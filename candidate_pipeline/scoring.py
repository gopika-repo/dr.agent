"""Deterministic scoring engine for challenge and hackathon evaluation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

HACKATHON_CRITERIA = {
    "hackathon_general": {
        "code_quality": 25,
        "innovation": 25,
        "completeness": 25,
        "documentation": 15,
        "presentation": 10,
        "bonus_max": 10,
        "required_tech": [],
        "bonus_tech": [],
    }
}

CHALLENGE_CRITERIA = {
    "challenge_023": {
        "multi_modal_implementation": 60,
        "functionality_results": 25,
        "innovation_practicality": 15,
        "bonus_max": 15,
        "required_tech": ["python", "opencv", "llm", "ocr", "multi-modal"],
        "bonus_tech": ["langgraph", "crewai", "fastapi", "qdrant", "yolo"],
    },
    "challenge_024": {
        "technical_implementation": 60,
        "functionality_results": 25,
        "innovation_practices": 15,
        "bonus_max": 15,
        "required_tech": ["python", "rag", "ai agents", "vector db", "aws"],
        "bonus_tech": ["langchain", "langgraph", "crewai", "docker", "fastapi"],
    },
    "challenge_025": {
        "technical_implementation": 60,
        "functionality_results": 25,
        "innovation_practices": 15,
        "bonus_max": 15,
        "required_tech": ["python", "etl", "postgresql", "aws"],
        "bonus_tech": ["airflow", "docker", "pyspark", "redis"],
    },
    "challenge_026": {
        "technical_implementation": 60,
        "functionality_results": 25,
        "innovation_practices": 15,
        "bonus_max": 15,
        "required_tech": ["react", "django", "postgresql", "ai/ml"],
        "bonus_tech": ["next.js", "docker", "aws", "celery", "redis"],
    },
    "challenge_027": {
        "technical_implementation": 60,
        "functionality_results": 25,
        "innovation_practices": 15,
        "bonus_max": 15,
        "required_tech": ["react", "django", "postgresql", "task queue"],
        "bonus_tech": ["next.js", "celery", "redis", "docker", "aws"],
    },
}

EXPERIENCE_CONFIGS = {
    "1st_year": {"multiplier": 1.15, "expectation_base": 55, "excellent_threshold": 75},
    "2nd_year": {"multiplier": 1.10, "expectation_base": 60, "excellent_threshold": 78},
    "3rd_year": {"multiplier": 1.05, "expectation_base": 65, "excellent_threshold": 80},
    "4th_year": {"multiplier": 1.00, "expectation_base": 70, "excellent_threshold": 83},
    "fresher": {"multiplier": 0.95, "expectation_base": 68, "excellent_threshold": 80},
    "experienced_0_2": {"multiplier": 0.85, "expectation_base": 75, "excellent_threshold": 86},
    "senior": {"multiplier": 0.75, "expectation_base": 82, "excellent_threshold": 92},
    "industry": {"multiplier": 0.88, "expectation_base": 75, "excellent_threshold": 88},
    "beginner": {"multiplier": 1.10, "expectation_base": 55, "excellent_threshold": 75},
    "intermediate": {"multiplier": 0.95, "expectation_base": 70, "excellent_threshold": 82},
    "advanced": {"multiplier": 0.80, "expectation_base": 85, "excellent_threshold": 92},
}

SPECIAL_CRITERIA_KEYS = {"bonus_max", "required_tech", "bonus_tech"}


def calculate_scores(
    analysis_dict: Dict[str, Any],
    challenge_id: Optional[str] = None,
    experience_level: str = "intermediate",
    hackathon_id: Optional[str] = None,
    hackathon_db_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, Any]]:
    """Calculate deterministic component and weighted category scores.

    Category values are weighted points (for example 18/25), not percentages.
    Experience adjustment is applied exactly once here for this local pipeline.
    """
    criteria, criteria_source = _resolve_criteria(challenge_id, hackathon_id, hackathon_db_data)
    scoring_id = challenge_id or hackathon_id or "generic"

    file_scan = analysis_dict.get("file_scanner", {}) or {}
    tech_stack = analysis_dict.get("technologies", {}) or {}
    code_quality = analysis_dict.get("code_quality", {}) or {}
    readme = analysis_dict.get("readme", {}) or {}
    commits = analysis_dict.get("commits", {}) or {}

    component_scores = {
        "code_quality": _num(code_quality.get("overall_quality_score"), 50),
        "tech_match": _calculate_tech_match(tech_stack, criteria),
        "completeness": _calculate_completeness(file_scan, code_quality),
        "documentation": _num(readme.get("quality_score"), 0) * 10,
        "activity": _calculate_activity_score(commits),
        "architecture": _calculate_architecture_score(file_scan, code_quality),
        "testing": (
            _num(code_quality.get("docstring_coverage"), 0) * 0.5
            + _num(code_quality.get("type_hint_coverage"), 0) * 0.5
        ),
    }
    component_scores = {key: round(_clamp(value), 3) for key, value in component_scores.items()}

    raw_category_scores = _map_to_challenge_categories(component_scores, criteria, challenge_id)
    adjusted_scores, adjustment_details = apply_experience_adjustment(
        raw_category_scores, experience_level, criteria
    )

    category_weights = _category_weights(criteria)
    max_score = sum(category_weights.values()) or 100.0
    base_total = sum(raw_category_scores.values())
    adjusted_total = sum(adjusted_scores.values())

    # Convert totals to a canonical 0-100 score even if DB weights do not sum to 100.
    base_percentage = (base_total / max_score) * 100 if max_score else 0.0
    adjusted_percentage = (adjusted_total / max_score) * 100 if max_score else 0.0

    metadata = {
        "scoring_id": scoring_id,
        "criteria_source": criteria_source,
        "challenge_id": challenge_id,
        "hackathon_id": hackathon_id,
        "experience_level": experience_level,
        "experience_multiplier": adjustment_details["multiplier"],
        "base_score": round(base_percentage, 3),
        "adjusted_score": round(_clamp(adjusted_percentage), 3),
        "base_weighted_points": round(base_total, 3),
        "adjusted_weighted_points": round(adjusted_total, 3),
        "max_score": round(max_score, 3),
        "category_weights": category_weights,
        "raw_category_scores": raw_category_scores,
        "adjustment_details": adjustment_details,
    }
    return component_scores, adjusted_scores, metadata


def _resolve_criteria(
    challenge_id: Optional[str],
    hackathon_id: Optional[str],
    hackathon_db_data: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], str]:
    if challenge_id and challenge_id in CHALLENGE_CRITERIA:
        return dict(CHALLENGE_CRITERIA[challenge_id]), "challenge"
    if hackathon_id and hackathon_id in HACKATHON_CRITERIA:
        return dict(HACKATHON_CRITERIA[hackathon_id]), "hackathon_hardcoded"
    if hackathon_db_data:
        try:
            return _build_criteria_from_db(hackathon_db_data), "hackathon_dynamic"
        except (TypeError, ValueError, KeyError):
            pass
    return dict(HACKATHON_CRITERIA["hackathon_general"]), "fallback_default"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _normalise_tech(value: str) -> str:
    text = re.sub(r"[^a-z0-9+#.]+", " ", str(value).lower()).strip()
    aliases = {
        "vector database": "vector db",
        "vector databases": "vector db",
        "ai agent": "ai agents",
        "large language model": "llm",
        "large language models": "llm",
        "typescript": "typescript",
        "javascript": "javascript",
    }
    return aliases.get(text, text)


def _flatten_detected_technologies(tech_stack: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    for tech_list in tech_stack.values():
        if isinstance(tech_list, str):
            values.extend(part.strip() for part in tech_list.split(",") if part.strip())
        elif isinstance(tech_list, Iterable) and not isinstance(tech_list, (dict, bytes)):
            values.extend(str(item) for item in tech_list if item)
    return values


def _tech_matches(required: str, detected: str) -> bool:
    req = _normalise_tech(required)
    det = _normalise_tech(detected)
    if not req or not det:
        return False
    if req == det or req in det or det in req:
        return True

    token_aliases = {
        "vector db": {"qdrant", "pinecone", "weaviate", "milvus", "chroma", "faiss"},
        "llm": {"openai", "gemini", "anthropic", "claude", "llama", "mistral", "groq"},
        "ai/ml": {"openai", "gemini", "anthropic", "tensorflow", "pytorch", "sklearn"},
    }
    return det in token_aliases.get(req, set())


def _calculate_tech_match(tech_stack: Dict[str, Any], criteria: Dict[str, Any]) -> float:
    required = [str(item) for item in criteria.get("required_tech", []) if str(item).strip()]
    detected = _flatten_detected_technologies(tech_stack)
    if not required:
        return 75.0

    matches = sum(1 for req in required if any(_tech_matches(req, det) for det in detected))
    match_percentage = (matches / len(required)) * 100.0

    bonus = [str(item) for item in criteria.get("bonus_tech", []) if str(item).strip()]
    bonus_matches = sum(1 for req in bonus if any(_tech_matches(req, det) for det in detected))
    bonus_points = min(bonus_matches * 2.5, 10.0)
    return _clamp(match_percentage + bonus_points)


def _calculate_completeness(file_scan: Dict[str, Any], code_quality: Dict[str, Any]) -> float:
    score = 50.0
    total_files = int(_num(file_scan.get("total_files"), 0))
    if total_files > 50:
        score += 20
    elif total_files > 20:
        score += 15
    elif total_files > 10:
        score += 10

    total_lines = int(_num(file_scan.get("total_lines"), 0))
    if total_lines > 1000:
        score += 15
    elif total_lines > 500:
        score += 10
    elif total_lines > 100:
        score += 5

    key_dirs = {str(item).lower() for item in file_scan.get("key_directories", []) or []}
    if "tests" in key_dirs or "test" in key_dirs:
        score += 10
    if "docs" in key_dirs or "documentation" in key_dirs:
        score += 5
    if _num(code_quality.get("total_functions"), 0) > 20:
        score += 5
    return _clamp(score)


def _calculate_activity_score(commits: Dict[str, Any]) -> float:
    score = 50.0
    total_commits = _num(commits.get("total_commits"), 0)
    if total_commits > 50:
        score += 25
    elif total_commits > 20:
        score += 15
    elif total_commits > 5:
        score += 10

    duration_days = _num(commits.get("project_duration_days"), 1)
    if duration_days > 90:
        score += 15
    elif duration_days > 30:
        score += 10
    elif duration_days > 7:
        score += 5

    commits_per_day = _num(commits.get("commits_per_day"), 0)
    if commits_per_day > 0.5:
        score += 10
    elif commits_per_day > 0.2:
        score += 5
    return _clamp(score)


def _calculate_architecture_score(file_scan: Dict[str, Any], code_quality: Dict[str, Any]) -> float:
    score = 50.0
    key_dirs = file_scan.get("key_directories", []) or []
    score += min(len(key_dirs) * 5, 25)
    patterns = code_quality.get("design_patterns", []) or []
    score += min(len(patterns) * 5, 25)
    return _clamp(score)


def _as_tech_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _build_criteria_from_db(hackathon_db_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(hackathon_db_data, dict) or not hackathon_db_data:
        raise ValueError("hackathon_db_data must be a non-empty dictionary")

    required_tech = _as_tech_list(
        hackathon_db_data.get("technologies")
        or hackathon_db_data.get("required_tech")
        or hackathon_db_data.get("skills")
    )
    bonus_tech = _as_tech_list(hackathon_db_data.get("bonusTech") or hackathon_db_data.get("bonus_tech"))
    evaluation = hackathon_db_data.get("evaluation") or hackathon_db_data.get("eval_criteria") or ""
    weights = _parse_evaluation_criteria(evaluation)

    if not weights:
        weights = {"code_quality": 25.0, "innovation": 25.0, "completeness": 25.0, "documentation": 15.0, "presentation": 10.0}

    criteria: Dict[str, Any] = {
        "bonus_max": 10,
        "required_tech": required_tech,
        "bonus_tech": bonus_tech,
    }
    criteria.update(weights)
    return criteria


def _slugify_category(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value or "criterion"


def _parse_evaluation_criteria(evaluation: Any) -> Dict[str, float]:
    """Parse JSON or human-readable weighted criteria into ``{slug: weight}``."""
    if isinstance(evaluation, dict):
        return {str(k): float(v) for k, v in evaluation.items() if isinstance(v, (int, float)) and float(v) > 0}
    if not isinstance(evaluation, str) or not evaluation.strip():
        return {}

    text = evaluation.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            result = {str(k): float(v) for k, v in parsed.items() if isinstance(v, (int, float)) and float(v) > 0}
            if result:
                return result
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Example: "Mastra Integration Depth (25%), Qdrant Integration Quality (20%)"
    result: Dict[str, float] = {}
    for label, number in re.findall(r"([^,;]+?)\s*\(\s*(\d+(?:\.\d+)?)\s*%\s*\)", text):
        result[_slugify_category(label)] = float(number)
    if result:
        return result

    # Example: "Code Quality: 25%, Innovation: 25%"
    for label, number in re.findall(r"([^,;:]+?)\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?", text):
        result[_slugify_category(label)] = float(number)
    if result:
        return result

    # If no explicit weights exist, treat comma/semicolon separated labels equally.
    labels = [_slugify_category(item) for item in re.split(r"[,;]", text) if item.strip()]
    labels = [label for label in labels if label]
    if 1 < len(labels) <= 12:
        weight = 100.0 / len(labels)
        return {label: weight for label in labels}
    return {}


def _category_weights(criteria: Dict[str, Any]) -> Dict[str, float]:
    return {
        key: float(value)
        for key, value in criteria.items()
        if key not in SPECIAL_CRITERIA_KEYS and isinstance(value, (int, float)) and float(value) > 0
    }


def _map_to_challenge_categories(
    component_scores: Dict[str, float],
    criteria: Dict[str, Any],
    challenge_id: Optional[str],
) -> Dict[str, float]:
    del challenge_id
    weights = _category_weights(criteria)
    category_scores: Dict[str, float] = {}
    for category, weight in weights.items():
        percentage = _score_category(category, component_scores)
        category_scores[category] = round((percentage / 100.0) * weight, 3)
    return category_scores


def _score_category(category_name: str, components: Dict[str, float]) -> float:
    """Map an arbitrary criterion to measured components without fake evidence."""
    name = category_name.lower()

    # Ordered rules: specific semantic groups before generic "quality".
    if any(word in name for word in ("innovation", "novel", "impact", "practical")):
        return 0.6 * components.get("architecture", 50) + 0.4 * components.get("completeness", 50)
    if any(word in name for word in ("documentation", "readme", "docs", "presentation")):
        return components.get("documentation", 50)
    if any(word in name for word in ("test", "coverage")) and not any(word in name for word in ("technology", "tech")):
        return components.get("testing", 50)
    if any(word in name for word in ("activity", "commit", "maturity", "progress")):
        return components.get("activity", 50)
    if any(word in name for word in ("architecture", "design", "structure")):
        return components.get("architecture", 50)
    if any(word in name for word in ("integration", "technology", "technologies", "tech_stack", "stack")):
        return 0.65 * components.get("tech_match", 50) + 0.35 * components.get("code_quality", 50)
    if any(word in name for word in ("output", "functionality", "feature", "complete", "results")):
        return 0.65 * components.get("completeness", 50) + 0.35 * components.get("code_quality", 50)
    if any(word in name for word in ("implementation", "technical", "code", "quality")):
        return 0.7 * components.get("code_quality", 50) + 0.3 * components.get("architecture", 50)
    return components.get("code_quality", 50)


def _match_category_to_component(category_name: str, available_components: Dict[str, float]) -> str:
    """Backward-compatible helper retained for external imports."""
    name = category_name.lower()
    if name in available_components:
        return name
    if any(word in name for word in ("doc", "readme", "presentation")):
        return "documentation"
    if any(word in name for word in ("activity", "commit", "progress", "maturity")):
        return "activity"
    if any(word in name for word in ("test", "coverage")):
        return "testing"
    if any(word in name for word in ("innovation", "novel", "design", "architecture", "structure", "impact")):
        return "architecture"
    if any(word in name for word in ("complete", "functionality", "feature", "output")):
        return "completeness"
    if any(word in name for word in ("integration", "technology", "stack")):
        return "tech_match"
    return "code_quality"


def apply_experience_adjustment(
    category_scores: Dict[str, float],
    experience_level: str,
    criteria: Dict[str, Any],
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """Adjust weighted category points once while preserving each category maximum."""
    config = EXPERIENCE_CONFIGS.get(experience_level, EXPERIENCE_CONFIGS["intermediate"])
    multiplier = float(config["multiplier"])
    weights = _category_weights(criteria)

    adjusted: Dict[str, float] = {}
    per_category: Dict[str, Any] = {}
    for category, raw_points in category_scores.items():
        max_points = float(weights.get(category, 100.0))
        value = max(0.0, min(float(raw_points) * multiplier, max_points))
        adjusted[category] = round(value, 3)
        raw_pct = (float(raw_points) / max_points) * 100 if max_points else 0.0
        adjusted_pct = (value / max_points) * 100 if max_points else 0.0
        per_category[category] = {
            "raw_points": round(float(raw_points), 3),
            "adjusted_points": round(value, 3),
            "max_points": round(max_points, 3),
            "raw_percentage": round(raw_pct, 3),
            "adjusted_percentage": round(adjusted_pct, 3),
        }

    details = {
        "multiplier": multiplier,
        "expectation_base": config["expectation_base"],
        "excellent_threshold": config["excellent_threshold"],
        "per_category": per_category,
    }
    return adjusted, details
