"""
Gemini evaluator for Dr. Agent.

This evaluator receives:
- deterministic repository metrics
- detected technologies
- bounded selected code evidence
- already-calculated scores

It does NOT scan the repository itself.

That is important because the evaluation scope is chosen before this stage:

full_repo
    -> complete repository analysis path

agents_only
    -> repo/agents analysis path

Gemini receives only selected evidence from that already-approved path.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config.settings import get_gemini_model


def evaluate_with_gemini(
    analysis_dict: Dict[str, Any],
    challenge_id: str,
    gemini_api_key: Optional[str] = None,
    max_file_samples: int = 8,
) -> Dict[str, Any]:
    """
    Generate the qualitative Dr. Agent report.

    Numerical scoring is performed elsewhere.
    Gemini receives the deterministic scores only as supporting context.

    Token-related metadata is also returned when available.
    """

    if genai is None:
        return {
            "error": "google-generativeai package not installed."
        }

    api_key = (
        gemini_api_key
        or os.getenv("GEMINI_API_KEY")
        or ""
    ).strip()

    if not api_key:
        return {
            "error": "GEMINI_API_KEY is not configured."
        }

    try:
        model_name = get_gemini_model()

    except ValueError as exc:
        return {
            "error": str(exc)
        }

    try:
        genai.configure(
            api_key=api_key
        )

        model = genai.GenerativeModel(
            model_name
        )

        prompt = _create_evaluation_prompt(
            analysis_dict,
            challenge_id,
            max_file_samples,
        )

        # -------------------------------------------------------------
        # Prompt/token metrics BEFORE generation
        # -------------------------------------------------------------

        code_evidence = (
            analysis_dict.get("code_evidence", {})
            or {}
        )

        evidence_files = (
            code_evidence.get("files", [])
            or []
        )[:max_file_samples]

        selected_evidence_characters = sum(
            len(
                str(
                    item.get(
                        "content",
                        "",
                    )
                )
            )
            for item in evidence_files
            if isinstance(item, dict)
        )

        prompt_metrics: Dict[str, Any] = {
            "prompt_characters": len(prompt),

            # Approximation only.
            # Exact Gemini token count is added below when supported.
            "estimated_prompt_tokens": max(
                1,
                round(
                    len(prompt) / 4
                ),
            ),

            "selected_evidence_files": len(
                evidence_files
            ),

            "selected_evidence_characters":
                selected_evidence_characters,
        }

        # -------------------------------------------------------------
        # Ask Gemini SDK for exact input token count when supported
        # -------------------------------------------------------------

        try:

            counted = model.count_tokens(
                prompt
            )

            exact_input_tokens = getattr(
                counted,
                "total_tokens",
                None,
            )

            if exact_input_tokens is not None:

                prompt_metrics[
                    "input_tokens_before_generation"
                ] = int(
                    exact_input_tokens
                )

        except Exception:
            # Some older SDK/model combinations may not support
            # count_tokens(). The labelled estimate remains available.
            pass

        # -------------------------------------------------------------
        # Gemini generation
        # -------------------------------------------------------------

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 40,

                # Lower than the old 4000-output-token allowance.
                # This keeps qualitative evaluation more predictable.
                "max_output_tokens": 3000,
            },
        )

        response_text = _extract_response_text(
            response
        )

        if not response_text:

            return {
                "error":
                    "Gemini API returned an empty response.",

                "token_metrics":
                    prompt_metrics,
            }

        # Count Gemini output tokens.
        try:
            output_count = model.count_tokens(response_text)

            output_tokens = getattr(
                output_count,
                "total_tokens",
                None,
            )

            if output_tokens is not None:
                prompt_metrics["output_tokens_counted"] = int(
                    output_tokens
                )

                input_tokens = prompt_metrics.get(
                    "input_tokens_before_generation"
                )

                if input_tokens is not None:
                    prompt_metrics["total_tokens_counted"] = (
                        int(input_tokens)
                        + int(output_tokens)
                    )

        except Exception:
            pass

        result = _parse_gemini_response(
            response_text,
            analysis_dict,
        )

        # ---------------------------------------------------------
        # JSON repair pass
        #
        # If Gemini returns useful content but malformed JSON,
        # make ONE small second request asking Gemini only to repair
        # the JSON syntax. No repository re-analysis is performed.
        # ---------------------------------------------------------

        json_repair_attempted = False
        json_repair_successful = False

        if (
            isinstance(result, dict)
            and result.get("_fallback")
        ):
            json_repair_attempted = True

            repair_prompt = f"""
You are a JSON formatter.

The text below was intended to be valid JSON but contains formatting
or syntax errors.

Repair ONLY the JSON syntax.

Rules:
- Do not add new facts.
- Do not remove factual content.
- Do not explain anything.
- Do not use Markdown fences.
- Return ONLY one valid JSON object.
- Preserve this required top-level structure:

{{
  "strengths": [],
  "weaknesses": [],
  "recommendation": {{
    "type": "",
    "justification": "",
    "suggested_improvements": ""
  }},
  "benchmarks": {{
    "intern_level": "",
    "entry_level": "",
    "strong_hire": "",
    "exceptional": ""
  }}
}}

BROKEN_JSON:
{response_text}
""".strip()

            try:
                # Record repair-request token size when supported.
                try:
                    repair_count = model.count_tokens(
                        repair_prompt
                    )

                    repair_tokens = getattr(
                        repair_count,
                        "total_tokens",
                        None,
                    )

                    if repair_tokens is not None:
                        prompt_metrics[
                            "json_repair_input_tokens"
                        ] = int(
                            repair_tokens
                        )

                except Exception:
                    pass

                repair_response = model.generate_content(
                    repair_prompt,
                    generation_config={
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "top_k": 1,
                        "max_output_tokens": 3000,
                    },
                )

                repaired_text = _extract_response_text(
                    repair_response
                )

                if repaired_text:

                    # Count repair response tokens.
                    try:
                        repair_output_count = model.count_tokens(
                            repaired_text
                        )

                        repair_output_tokens = getattr(
                            repair_output_count,
                            "total_tokens",
                            None,
                        )

                        if repair_output_tokens is not None:
                            prompt_metrics[
                                "json_repair_output_tokens"
                            ] = int(repair_output_tokens)

                    except Exception:
                        pass

                    repaired_result = _parse_gemini_response(
                        repaired_text,
                        analysis_dict,
                    )

                    if (
                        isinstance(repaired_result, dict)
                        and not repaired_result.get("_fallback")
                    ):
                        result = repaired_result
                        json_repair_successful = True

            except Exception:
                # The deterministic fallback from the first parsing
                # attempt remains available if repair also fails.
                pass

        # Recalculate total usage across the main call and
        # optional JSON-repair call.
        main_input = prompt_metrics.get(
            "input_tokens_before_generation",
            0,
        ) or 0

        main_output = prompt_metrics.get(
            "output_tokens_counted",
            0,
        ) or 0

        repair_input = prompt_metrics.get(
            "json_repair_input_tokens",
            0,
        ) or 0

        repair_output = prompt_metrics.get(
            "json_repair_output_tokens",
            0,
        ) or 0

        prompt_metrics[
            "total_tokens_counted"
        ] = (
            int(main_input)
            + int(main_output)
            + int(repair_input)
            + int(repair_output)
        )

        prompt_metrics[
            "json_repair_attempted"
        ] = json_repair_attempted

        prompt_metrics[
            "json_repair_successful"
        ] = json_repair_successful

        # Always include local prompt measurements.
        result["token_metrics"] = (
            prompt_metrics
        )

        # -------------------------------------------------------------
        # Actual Gemini usage metadata when available
        # -------------------------------------------------------------

        usage = getattr(
            response,
            "usage_metadata",
            None,
        )

        if usage is not None:

            result["usage"] = {
                "prompt_tokens":
                    _safe_attr(
                        usage,
                        "prompt_token_count",
                    ),

                "output_tokens":
                    _safe_attr(
                        usage,
                        "candidates_token_count",
                    ),

                "total_tokens":
                    _safe_attr(
                        usage,
                        "total_token_count",
                    ),
            }

        return result

    except Exception as exc:

        return {
            "error":
                f"Gemini API error: {exc}"
        }


def _safe_attr(
    obj: Any,
    name: str,
) -> Optional[int]:
    """
    Safely convert Gemini usage metadata into integers.
    """

    value = getattr(
        obj,
        name,
        None,
    )

    try:

        return (
            int(value)
            if value is not None
            else None
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def _extract_response_text(
    response: Any,
) -> str:
    """
    Extract text from Gemini response defensively.
    """

    try:

        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            return str(
                text
            ).strip()

    except Exception:
        pass


    chunks = []


    for candidate in (
        getattr(
            response,
            "candidates",
            [],
        )
        or []
    ):

        content = getattr(
            candidate,
            "content",
            None,
        )

        for part in (
            getattr(
                content,
                "parts",
                [],
            )
            or []
        ):

            text = getattr(
                part,
                "text",
                None,
            )

            if text:

                chunks.append(
                    str(text)
                )


    return "".join(
        chunks
    ).strip()


def _compact_evidence(
    analysis_dict: Dict[str, Any],
    max_file_samples: int,
) -> Dict[str, Any]:
    """
    Build bounded code evidence for Gemini.

    Only evidence already selected locally is used.
    Gemini never walks the repository.
    """

    evidence = (
        analysis_dict.get(
            "code_evidence",
            {},
        )
        or {}
    )

    compact_files = []


    for item in (
        evidence.get(
            "files",
            [],
        )
        or []
    )[:max_file_samples]:

        if not isinstance(
            item,
            dict,
        ):
            continue


        compact_files.append(
            {
                "path":
                    item.get(
                        "path"
                    ),

                "relevance_score":
                    item.get(
                        "relevance_score"
                    ),

                "matched_terms":
                    item.get(
                        "matched_terms",
                        [],
                    ),

                "content":
                    item.get(
                        "content",
                        "",
                    ),
            }
        )


    return {
        "selected_files":
            len(
                compact_files
            ),

        "candidate_files":
            evidence.get(
                "candidate_files"
            ),

        "total_chars":
            sum(
                len(
                    str(
                        item.get(
                            "content",
                            "",
                        )
                    )
                )
                for item in compact_files
            ),

        "files":
            compact_files,
    }


def _create_evaluation_prompt(
    analysis_dict: Dict[str, Any],
    challenge_id: str,
    max_file_samples: int,
) -> str:
    """
    Create compact Gemini prompt from deterministic analysis + evidence.
    """

    scores = (
        analysis_dict.get(
            "scores",
            {},
        )
        or {}
    )

    component_scores = (
        scores.get(
            "component_scores",
            {},
        )
        or {}
    )

    category_scores = (
        scores.get(
            "category_scores",
            {},
        )
        or {}
    )

    raw_category_scores = (
        scores.get(
            "raw_category_scores",
            {},
        )
        or {}
    )

    score_metadata = (
        scores.get(
            "metadata",
            {},
        )
        or {}
    )


    code_quality = (
        analysis_dict.get(
            "code_quality",
            {},
        )
        or {}
    )

    technologies = (
        analysis_dict.get(
            "technologies",
            {},
        )
        or {}
    )

    readme = (
        analysis_dict.get(
            "readme",
            {},
        )
        or {}
    )

    commits = (
        analysis_dict.get(
            "commits",
            {},
        )
        or {}
    )

    file_scan = (
        analysis_dict.get(
            "file_scanner",
            {},
        )
        or {}
    )

    hackathon = (
        analysis_dict.get(
            "hackathon",
            {},
        )
        or {}
    )


    title = (
        hackathon.get(
            "title"
        )
        or challenge_id
        or "Coding Challenge"
    )


    criteria_text = (
        hackathon.get(
            "evaluation"
        )
        or hackathon.get(
            "eval_criteria"
        )
        or analysis_dict.get(
            "evaluation_criteria"
        )
        or (
            "Use the supplied challenge criteria "
            "and repository evidence."
        )
    )


    required_tech = (
        hackathon.get(
            "technologies"
        )
        or hackathon.get(
            "required_tech"
        )
        or hackathon.get(
            "skills"
        )
        or []
    )


    if isinstance(
        required_tech,
        list,
    ):

        required_tech_text = ", ".join(
            str(item)
            for item in required_tech
        )

    else:

        required_tech_text = str(
            required_tech
        )


    payload = {

        "challenge_id":
            challenge_id,

        "title":
            title,

        "evaluation_scope":
            analysis_dict.get(
                "evaluation_scope",
                "full_repo",
            ),

        "target_folder":
            analysis_dict.get(
                "target_folder"
            ),

        "evaluation_criteria":
            criteria_text,

        "required_technologies":
            required_tech_text,


        "repository_metrics": {

            "total_files":
                file_scan.get(
                    "total_files"
                ),

            "total_lines":
                file_scan.get(
                    "total_lines"
                ),

            "key_directories":
                file_scan.get(
                    "key_directories",
                    [],
                ),

            "has_cicd":
                file_scan.get(
                    "has_cicd"
                ),
        },


        "technologies":
            technologies,


        "code_quality": {

            "overall_quality_score":
                code_quality.get(
                    "overall_quality_score"
                ),

            "error_handling_score":
                code_quality.get(
                    "error_handling_score"
                ),

            "docstring_coverage":
                code_quality.get(
                    "docstring_coverage"
                ),

            "type_hint_coverage":
                code_quality.get(
                    "type_hint_coverage"
                ),

            "design_patterns":
                code_quality.get(
                    "design_patterns",
                    [],
                ),

            "total_functions":
                code_quality.get(
                    "total_functions"
                ),

            "total_classes":
                code_quality.get(
                    "total_classes"
                ),

            "code_duplication_score":
                code_quality.get(
                    "code_duplication_score"
                ),
        },


        "documentation": {

            "exists":
                readme.get(
                    "exists"
                ),

            "quality_score":
                readme.get(
                    "quality_score"
                ),

            "has_examples":
                readme.get(
                    "has_examples"
                ),

            "has_installation":
                readme.get(
                    "has_installation"
                ),

            "has_usage":
                readme.get(
                    "has_usage"
                ),
        },


        "commits": {

            "total_commits":
                commits.get(
                    "total_commits"
                ),

            "project_duration_days":
                commits.get(
                    "project_duration_days"
                ),

            "commits_per_day":
                commits.get(
                    "commits_per_day"
                ),
        },


        "scores": {

            "component_scores":
                component_scores,

            "raw_category_scores":
                raw_category_scores,

            "experience_adjusted_category_scores":
                category_scores,

            "overall_score":
                scores.get(
                    "overall_score",
                    score_metadata.get(
                        "adjusted_score"
                    ),
                ),

            "experience_level":
                score_metadata.get(
                    "experience_level"
                ),
        },


        "selected_code_evidence":
            _compact_evidence(
                analysis_dict,
                max_file_samples,
            ),
    }


    compact_json = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
        default=str,
    )


    return f"""
You are a senior technical evaluator reviewing a repository submission.

Use ONLY the supplied evidence.

Never claim a technology or implementation exists unless it appears in:
1. detected technologies, or
2. selected code evidence.

Distinguish repository-level metadata such as README/commits from code
evidence inside the selected evaluation scope.

ANALYSIS_EVIDENCE_JSON:
{compact_json}

Return ONLY valid JSON using exactly this top-level structure:

{{
  "strengths": [
    {{
      "title": "...",
      "evidence": "...",
      "impact": "..."
    }}
  ],

  "weaknesses": [
    {{
      "title": "...",
      "evidence": "...",
      "impact": "..."
    }}
  ],

  "recommendation": {{
    "type": "Strong Hire | Consider for Internship | Hire as Intern | Do Not Hire",
    "justification": "...",
    "suggested_improvements": "..."
  }},

  "benchmarks": {{
    "intern_level": "Exceeds | Meets | Below",
    "entry_level": "Exceeds | Meets | Below",
    "strong_hire": "Exceeds | Meets | Below",
    "exceptional": "Exceeds | Meets | Below"
  }}
}}

The numerical score has already been calculated by deterministic code.

Do NOT recalculate or overwrite that score.

For integration claims such as:
- Mastra
- Qdrant
- Enkrypt AI
- RAG
- agents
- tools
- embeddings
- workflows

reference the supplied detected technology or file path whenever possible.
""".strip()


def _parse_gemini_response(
    response_text: str,
    analysis_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Parse Gemini JSON while tolerating Markdown fences.
    """

    text = response_text.strip()


    if text.startswith(
        "```json"
    ):

        text = text[
            len("```json"):
        ]

        if text.endswith(
            "```"
        ):

            text = text[
                :-3
            ]


    elif text.startswith(
        "```"
    ):

        text = text[
            3:
        ]

        if text.endswith(
            "```"
        ):

            text = text[
                :-3
            ]


    text = text.strip()


    try:

        result = json.loads(
            text
        )


    except json.JSONDecodeError:

        start = text.find(
            "{"
        )

        end = text.rfind(
            "}"
        )


        if (
            start != -1
            and end > start
        ):

            try:

                result = json.loads(
                    text[
                        start:
                        end + 1
                    ]
                )

            except json.JSONDecodeError:

                return _generate_fallback_evaluation(
                    analysis_dict
                )

        else:

            return _generate_fallback_evaluation(
                analysis_dict
            )


    if not isinstance(
        result,
        dict,
    ):

        return _generate_fallback_evaluation(
            analysis_dict
        )


    if not isinstance(
        result.get(
            "strengths"
        ),
        list,
    ):

        result[
            "strengths"
        ] = []


    if not isinstance(
        result.get(
            "weaknesses"
        ),
        list,
    ):

        result[
            "weaknesses"
        ] = []


    if not isinstance(
        result.get(
            "recommendation"
        ),
        dict,
    ):

        result[
            "recommendation"
        ] = {}


    if not isinstance(
        result.get(
            "benchmarks"
        ),
        dict,
    ):

        result[
            "benchmarks"
        ] = {}


    return result


def _generate_fallback_evaluation(
    analysis_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic fallback when Gemini returns invalid JSON.

    This does NOT fabricate repository facts.
    It uses only already-calculated component scores.
    """

    scores = (
        analysis_dict.get(
            "scores",
            {},
        )
        or {}
    )


    components = (
        scores.get(
            "component_scores",
            {},
        )
        or {}
    )


    overall = scores.get(
        "overall_score"
    )


    if overall is None:

        overall = (
            scores.get(
                "metadata",
                {},
            )
            or {}
        ).get(
            "adjusted_score",
            0,
        )


    try:

        overall = float(
            overall
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        overall = 0.0


    strengths = []

    weaknesses = []


    for name, value in components.items():

        try:

            numeric = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            continue


        label = (
            name
            .replace(
                "_",
                " ",
            )
            .title()
        )


        if numeric >= 75:

            strengths.append(
                {
                    "title":
                        f"Strong {label}",

                    "evidence":
                        f"{label} score: "
                        f"{numeric:.1f}/100",

                    "impact":
                        (
                            "This is one of the stronger "
                            "measured areas in the "
                            "repository analysis."
                        ),
                }
            )


        elif numeric < 50:

            weaknesses.append(
                {
                    "title":
                        f"Limited {label}",

                    "evidence":
                        f"{label} score: "
                        f"{numeric:.1f}/100",

                    "impact":
                        (
                            "This measured area needs "
                            "improvement relative to "
                            "the rest of the evaluation."
                        ),
                }
            )


    recommendation = (

        "Strong Hire"
        if overall >= 85

        else "Consider for Internship"
        if overall >= 70

        else "Hire as Intern"
        if overall >= 55

        else "Do Not Hire"
    )


    return {

        "strengths":
            strengths,

        "weaknesses":
            weaknesses,

        "recommendation": {

            "type":
                recommendation,

            "justification":
                (
                    "Deterministic pipeline score: "
                    f"{overall:.1f}/100. "
                    "Gemini returned invalid JSON, "
                    "so this fallback uses only "
                    "measured pipeline results."
                ),

            "suggested_improvements":
                (
                    "Review the lowest-scoring measured "
                    "components and selected code evidence."
                ),
        },

        "benchmarks": {

            "intern_level":
                (
                    "Meets"
                    if overall >= 60
                    else "Below"
                ),

            "entry_level":
                (
                    "Meets"
                    if overall >= 75
                    else "Below"
                ),

            "strong_hire":
                (
                    "Meets"
                    if overall >= 85
                    else "Below"
                ),

            "exceptional":
                (
                    "Meets"
                    if overall >= 90
                    else "Below"
                ),
        },

        "_fallback":
            True,
    }
