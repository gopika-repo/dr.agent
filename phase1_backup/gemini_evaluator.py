"""Gemini evaluator for the candidate pipeline.

This module sends compact, structured repository-analysis evidence to Gemini and
parses the model response into a stable JSON shape. It intentionally does not
send raw repository contents; repository scanning/evidence selection belongs to
the analysis pipeline.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime
    genai = None

from config.settings import get_gemini_model


def evaluate_with_gemini(
    analysis_dict: Dict[str, Any],
    challenge_id: str,
    gemini_api_key: Optional[str] = None,
    max_file_samples: int = 5,
) -> Dict[str, Any]:
    """Evaluate an analyzed repository with Gemini.

    ``max_file_samples`` is retained for API compatibility. The current
    candidate pipeline sends summarized metrics/evidence rather than raw source
    files, so the value is not consumed here yet.
    """
    del max_file_samples

    if genai is None:
        return {
            "error": (
                "google-generativeai package not installed. "
                "Install the version declared in requirements.txt."
            )
        }

    api_key = (gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return {"error": "GEMINI_API_KEY is not configured."}

    try:
        model_name = get_gemini_model()
    except ValueError as exc:
        return {"error": str(exc)}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = _create_evaluation_prompt(analysis_dict, challenge_id)

        # google-generativeai==0.3.2 does not accept request_options as a field
        # on GenerateContentRequest in this call path. Keep only arguments that
        # are supported by the pinned SDK.
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 4000,
            },
        )

        response_text = _extract_response_text(response)
        if not response_text:
            return {"error": "Gemini API returned an empty response."}

        result = _parse_gemini_response(response_text, analysis_dict)

        # Capture token metadata when the installed SDK/model exposes it.
        usage = getattr(response, "usage_metadata", None)
        if usage is not None and isinstance(result, dict):
            result["usage"] = {
                "prompt_tokens": _safe_attr(usage, "prompt_token_count"),
                "output_tokens": _safe_attr(usage, "candidates_token_count"),
                "total_tokens": _safe_attr(usage, "total_token_count"),
            }

        return result
    except Exception as exc:
        return {"error": f"Gemini API error: {exc}"}


def _safe_attr(obj: Any, name: str) -> Optional[int]:
    value = getattr(obj, name, None)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _extract_response_text(response: Any) -> str:
    """Extract text from a google-generativeai response defensively."""
    try:
        text = getattr(response, "text", None)
        if text:
            return str(text).strip()
    except Exception:
        pass

    chunks = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            text = getattr(part, "text", None)
            if text:
                chunks.append(str(text))
    return "".join(chunks).strip()


def _create_evaluation_prompt(analysis_dict: Dict[str, Any], challenge_id: str) -> str:
    """Create a compact prompt using real analysis data."""
    scores = analysis_dict.get("scores", {}) or {}
    component_scores = scores.get("component_scores", {}) or analysis_dict.get("component_scores", {}) or {}
    category_scores = scores.get("category_scores", {}) or analysis_dict.get("category_scores", {}) or {}
    raw_category_scores = scores.get("raw_category_scores", {}) or {}
    score_metadata = scores.get("metadata", {}) or {}

    code_quality = analysis_dict.get("code_quality", {}) or {}
    technologies = analysis_dict.get("technologies", {}) or {}
    readme = analysis_dict.get("readme", {}) or {}
    commits = analysis_dict.get("commits", {}) or {}
    file_scan = analysis_dict.get("file_scanner", {}) or {}
    hackathon = analysis_dict.get("hackathon", {}) or {}

    title = hackathon.get("title") or challenge_id or "Coding Challenge"
    criteria_text = (
        hackathon.get("evaluation")
        or hackathon.get("eval_criteria")
        or analysis_dict.get("evaluation_criteria")
        or "Use the supplied challenge criteria and repository evidence."
    )
    required_tech = (
        hackathon.get("technologies")
        or hackathon.get("required_tech")
        or hackathon.get("skills")
        or []
    )
    if isinstance(required_tech, list):
        required_tech_text = ", ".join(str(item) for item in required_tech)
    else:
        required_tech_text = str(required_tech)

    payload = {
        "challenge_id": challenge_id,
        "title": title,
        "evaluation_criteria": criteria_text,
        "required_technologies": required_tech_text,
        "repository_metrics": {
            "total_files": file_scan.get("total_files"),
            "total_lines": file_scan.get("total_lines"),
            "key_directories": file_scan.get("key_directories", []),
            "has_cicd": file_scan.get("has_cicd"),
        },
        "code_quality": {
            "overall_quality_score": code_quality.get("overall_quality_score"),
            "error_handling_score": code_quality.get("error_handling_score"),
            "docstring_coverage": code_quality.get("docstring_coverage"),
            "type_hint_coverage": code_quality.get("type_hint_coverage"),
            "design_patterns": code_quality.get("design_patterns", []),
            "total_functions": code_quality.get("total_functions"),
            "total_classes": code_quality.get("total_classes"),
            "code_duplication_score": code_quality.get("code_duplication_score"),
        },
        "technologies": technologies,
        "documentation": {
            "exists": readme.get("exists"),
            "quality_score": readme.get("quality_score"),
            "sections_found": readme.get("sections_found", []),
            "word_count": readme.get("word_count"),
            "has_examples": readme.get("has_examples"),
            "has_installation": readme.get("has_installation"),
            "has_usage": readme.get("has_usage"),
        },
        "commits": {
            "total_commits": commits.get("total_commits"),
            "project_duration_days": commits.get("project_duration_days"),
            "commits_per_day": commits.get("commits_per_day"),
        },
        "scores": {
            "component_scores": component_scores,
            "raw_category_scores": raw_category_scores,
            "experience_adjusted_category_scores": category_scores,
            "overall_score": scores.get("overall_score", score_metadata.get("adjusted_score")),
            "metadata": {
                "experience_level": score_metadata.get("experience_level"),
                "criteria_source": score_metadata.get("criteria_source"),
                "max_score": score_metadata.get("max_score"),
            },
        },
    }

    compact_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)

    return f"""You are a senior technical evaluator reviewing a repository submission.

Use ONLY the supplied analysis evidence. Do not invent code, files, technologies, or behavior that are not present in the evidence.

ANALYSIS_EVIDENCE_JSON:
{compact_json}

Return ONLY valid JSON using exactly this top-level structure:
{{
  "strengths": [
    {{"title": "...", "evidence": "...", "impact": "..."}}
  ],
  "weaknesses": [
    {{"title": "...", "evidence": "...", "impact": "..."}}
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

The numerical score has already been calculated by deterministic code. Do not recalculate or overwrite it. Use it only as supporting context. Be specific and evidence-based."""


def _parse_gemini_response(response_text: str, analysis_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Gemini JSON while tolerating Markdown fences."""
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[len("```json") :]
        if text.endswith("```"):
            text = text[:-3]
    elif text.startswith("```"):
        text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
    text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Try extracting the outermost JSON object before using deterministic fallback.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                result = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return _generate_fallback_evaluation(analysis_dict)
        else:
            return _generate_fallback_evaluation(analysis_dict)

    if not isinstance(result, dict):
        return _generate_fallback_evaluation(analysis_dict)

    if not isinstance(result.get("strengths"), list):
        result["strengths"] = []
    if not isinstance(result.get("weaknesses"), list):
        result["weaknesses"] = []
    if not isinstance(result.get("recommendation"), dict):
        result["recommendation"] = {}
    if not isinstance(result.get("benchmarks"), dict):
        result["benchmarks"] = {}
    return result


def _generate_fallback_evaluation(analysis_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Create an evidence-based deterministic fallback when Gemini returns invalid JSON."""
    scores = analysis_dict.get("scores", {}) or {}
    components = scores.get("component_scores", {}) or analysis_dict.get("component_scores", {}) or {}
    overall = scores.get("overall_score")
    if overall is None:
        overall = (scores.get("metadata", {}) or {}).get("adjusted_score", 0)
    try:
        overall = float(overall or 0)
    except (TypeError, ValueError):
        overall = 0.0

    strengths = []
    weaknesses = []
    for name, value in components.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        label = name.replace("_", " ").title()
        if numeric >= 75:
            strengths.append({
                "title": f"Strong {label}",
                "evidence": f"{label} score: {numeric:.1f}/100",
                "impact": "This is one of the stronger measured areas in the repository analysis.",
            })
        elif numeric < 50:
            weaknesses.append({
                "title": f"Limited {label}",
                "evidence": f"{label} score: {numeric:.1f}/100",
                "impact": "This measured area needs improvement relative to the rest of the evaluation.",
            })

    if overall >= 85:
        recommendation = "Strong Hire"
    elif overall >= 70:
        recommendation = "Consider for Internship"
    elif overall >= 55:
        recommendation = "Hire as Intern"
    else:
        recommendation = "Do Not Hire"

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": {
            "type": recommendation,
            "justification": f"Deterministic pipeline score: {overall:.1f}/100. Gemini returned invalid JSON, so this fallback uses only measured pipeline results.",
            "suggested_improvements": "Review the lowest-scoring measured components and address the evidence reported by the deterministic analyzers.",
        },
        "benchmarks": {
            "intern_level": "Meets" if overall >= 60 else "Below",
            "entry_level": "Meets" if overall >= 75 else "Below",
            "strong_hire": "Meets" if overall >= 85 else "Below",
            "exceptional": "Meets" if overall >= 90 else "Below",
        },
        "_fallback": True,
    }
