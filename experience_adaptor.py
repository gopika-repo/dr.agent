"""Experience-aware score adaptation for 0-100 evaluation outputs."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple


class ExperienceScoreAdapter:
    """Adapt already-normalized (0-100) evaluation scores by experience level.

    This adapter is used by the legacy/GitHubAnalyzerAgent flow. The local
    ``candidate_pipeline.scoring`` flow applies its own weighted-point adjustment
    and must not be passed through this adapter a second time.
    """

    def __init__(self) -> None:
        self.experience_configs = {
            "1st_year": {"multiplier": 1.15, "expectation_base": 55, "excellent_threshold": 75, "penalty_factor": 0.3, "reward_factor": 1.2, "description": "1st Year Student - Basic understanding expected"},
            "2nd_year": {"multiplier": 1.10, "expectation_base": 60, "excellent_threshold": 78, "penalty_factor": 0.4, "reward_factor": 1.1, "description": "2nd Year Student - Growing proficiency"},
            "3rd_year": {"multiplier": 1.05, "expectation_base": 65, "excellent_threshold": 80, "penalty_factor": 0.5, "reward_factor": 1.0, "description": "3rd Year Student - Solid fundamentals"},
            "4th_year": {"multiplier": 1.00, "expectation_base": 70, "excellent_threshold": 83, "penalty_factor": 0.6, "reward_factor": 0.9, "description": "Final Year Student - Near-graduate level"},
            "fresher": {"multiplier": 0.95, "expectation_base": 68, "excellent_threshold": 80, "penalty_factor": 0.7, "reward_factor": 0.8, "description": "Recent Graduate - Entry-level professional"},
            "experienced_0_2": {"multiplier": 0.85, "expectation_base": 75, "excellent_threshold": 86, "penalty_factor": 0.8, "reward_factor": 0.7, "description": "1-2 Years Experience - Junior professional"},
            "senior": {"multiplier": 0.75, "expectation_base": 82, "excellent_threshold": 92, "penalty_factor": 0.9, "reward_factor": 0.6, "description": "3+ Years Experience - Senior professional"},
            "industry": {"multiplier": 0.88, "expectation_base": 75, "excellent_threshold": 88, "penalty_factor": 0.8, "reward_factor": 0.8, "description": "Industry Ready - Professional standard assessment"},
            "beginner": {"multiplier": 1.10, "expectation_base": 55, "excellent_threshold": 75, "penalty_factor": 0.3, "reward_factor": 1.2, "description": "Beginner - Focus on basic implementation"},
            "intermediate": {"multiplier": 0.95, "expectation_base": 70, "excellent_threshold": 82, "penalty_factor": 0.6, "reward_factor": 0.9, "description": "Intermediate - Solid logic and features"},
            "advanced": {"multiplier": 0.80, "expectation_base": 85, "excellent_threshold": 92, "penalty_factor": 0.9, "reward_factor": 0.7, "description": "Advanced - High scale/quality standards"},
        }
        self.industry_benchmarks = {
            "1st_year": {"min": 40, "good": 60, "excellent": 75},
            "2nd_year": {"min": 45, "good": 65, "excellent": 80},
            "3rd_year": {"min": 50, "good": 70, "excellent": 82},
            "4th_year": {"min": 55, "good": 75, "excellent": 85},
            "fresher": {"min": 50, "good": 68, "excellent": 80},
            "experienced_0_2": {"min": 60, "good": 78, "excellent": 88},
            "senior": {"min": 70, "good": 85, "excellent": 95},
            "industry": {"min": 65, "good": 78, "excellent": 90},
            "beginner": {"min": 40, "good": 60, "excellent": 80},
            "intermediate": {"min": 60, "good": 75, "excellent": 85},
            "advanced": {"min": 75, "good": 85, "excellent": 95},
        }

    def adapt_scores(self, evaluation: dict, experience_level: str) -> dict:
        """Adapt a legacy evaluation whose category scores are on a 0-100 scale."""
        level = experience_level if experience_level in self.experience_configs else "fresher"
        config = self.experience_configs[level]
        benchmark = self.industry_benchmarks[level]
        adapted = copy.deepcopy(evaluation or {})

        category_scores = self._extract_category_scores(evaluation or {})
        adjustments: List[Dict[str, Any]] = []
        adjusted_values: List[float] = []
        raw_values: List[float] = []

        for category, raw_score in category_scores.items():
            raw_score = max(0.0, min(100.0, float(raw_score)))
            adjusted_score, details = self._apply_experience_adjustment(raw_score, config)
            self._set_category_score(adapted, category, adjusted_score, raw_score, details["explanation"])
            raw_values.append(raw_score)
            adjusted_values.append(adjusted_score)
            adjustments.append({
                "category": category.replace("_", " ").title(),
                "original": round(raw_score, 1),
                "adjusted": round(adjusted_score, 1),
                "difference": round(adjusted_score - raw_score, 1),
                "expected": details["expected"],
                "gap": details["gap"],
                "explanation": details["explanation"],
            })

        original_overall = self._extract_existing_overall(evaluation)
        if original_overall is None and raw_values:
            original_overall = sum(raw_values) / len(raw_values)
        if original_overall is None:
            original_overall = 0.0

        if adjusted_values:
            overall_score = sum(adjusted_values) / len(adjusted_values)
        elif original_overall > 0:
            overall_score, _ = self._apply_experience_adjustment(original_overall, config)
        else:
            overall_score = 0.0

        adapted["original_overall"] = round(original_overall, 1)
        adapted["overall_score"] = round(overall_score, 1)
        adapted["experience_context"] = {
            "level": level,
            "multiplier": config["multiplier"],
            "expectation_base": config["expectation_base"],
            "excellent_threshold": config["excellent_threshold"],
            "penalty_factor": config["penalty_factor"],
            "reward_factor": config["reward_factor"],
            "description": config["description"],
            "benchmark_min": benchmark["min"],
            "benchmark_good": benchmark["good"],
            "benchmark_excellent": benchmark["excellent"],
        }
        adapted["score_adjustments"] = adjustments
        adapted["experience_feedback"] = self._generate_experience_feedback(adapted, level, config, benchmark, adjustments)
        adapted["hiring_recommendation"] = self.get_actionable_recommendation(adapted["overall_score"], level)
        return adapted

    def get_actionable_recommendation(self, score: float, experience_level: str) -> str:
        """Return the frontend recommendation for an already-final 0-100 score."""
        level = experience_level if experience_level in self.industry_benchmarks else "fresher"
        benchmark = self.industry_benchmarks[level]
        is_student = "year" in level or "student" in level
        score = float(score or 0)
        if score >= benchmark["excellent"]:
            return "Exceptional – Direct Interview"
        if score >= benchmark["good"]:
            return "Strong Internship Hire" if is_student else "Strong Hire"
        if score >= benchmark["min"]:
            return "Average – Potential Hire"
        return "Below Benchmark – Needs Improvement"

    # Backward-compatible alias for any existing direct calls.
    def _get_actionable_recommendation(self, score: float, level: str, benchmark: Optional[dict] = None) -> str:
        del benchmark
        return self.get_actionable_recommendation(score, level)

    def _apply_experience_adjustment(self, raw_score: float, config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Adjust a normalized 0-100 score.

        The calculation intentionally stays on the same 0-100 scale. It is not
        valid for weighted category points such as 11/25; those are handled by
        candidate_pipeline.scoring before reaching this adapter.
        """
        multiplier = float(config["multiplier"])
        base_score = raw_score * multiplier
        expectation = float(config["expectation_base"])
        gap = base_score - expectation

        if gap < 0:
            adjustment = gap * float(config["penalty_factor"])
            adjusted = base_score + adjustment
            action = "Penalty"
            factor = config["penalty_factor"]
        else:
            # A reward_factor below 1 is still stricter than the raw gap, while
            # a factor above 1 is more lenient for junior levels.
            rewarded_gap = gap * float(config["reward_factor"])
            adjusted = expectation + rewarded_gap
            adjustment = adjusted - base_score
            action = "Expectation adjustment"
            factor = config["reward_factor"]

        adjusted = max(0.0, min(100.0, adjusted))
        explanation = (
            f"Raw score: {raw_score:.1f}/100 → Base (×{multiplier}): {base_score:.1f}/100 → "
            f"Expectation: {expectation:.1f}/100 → Gap: {gap:+.1f} → "
            f"{action} (×{factor}): {adjustment:+.1f} → Final: {adjusted:.1f}/100"
        )
        return adjusted, {
            "expected": expectation,
            "gap": round(gap, 1),
            "adjustment": round(adjustment, 1),
            "explanation": explanation,
        }

    def _extract_existing_overall(self, evaluation: dict) -> Optional[float]:
        candidates = [evaluation.get("overall"), evaluation.get("overall_score"), evaluation.get("score")]
        report = evaluation.get("report") if isinstance(evaluation.get("report"), dict) else {}
        hidevs = report.get("hidevs_score") if isinstance(report.get("hidevs_score"), dict) else {}
        candidates.append(hidevs.get("score"))
        for value in candidates:
            try:
                if value is not None:
                    return max(0.0, min(100.0, float(value)))
            except (TypeError, ValueError):
                continue
        return None

    def _extract_category_scores(self, evaluation: dict) -> Dict[str, float]:
        category_scores: Dict[str, float] = {}
        scores = evaluation.get("scores")
        if isinstance(scores, dict):
            for category, data in scores.items():
                try:
                    value = data.get("score") if isinstance(data, dict) else data
                    category_scores[str(category)] = float(value)
                except (TypeError, ValueError, AttributeError):
                    continue

        report = evaluation.get("report") if isinstance(evaluation.get("report"), dict) else {}
        criteria = report.get("evaluation_criteria")
        if not category_scores and isinstance(criteria, list):
            for criterion in criteria:
                if not isinstance(criterion, dict):
                    continue
                name = criterion.get("criterion_name")
                value = criterion.get("score")
                if name is None or value is None:
                    continue
                try:
                    category_scores[str(name).lower().replace(" ", "_")] = float(value)
                except (TypeError, ValueError):
                    pass

        hidevs = report.get("hidevs_score") if isinstance(report.get("hidevs_score"), dict) else {}
        breakdown = hidevs.get("breakdown")
        if not category_scores and isinstance(breakdown, dict):
            for category, value in breakdown.items():
                try:
                    category_scores[str(category)] = float(value)
                except (TypeError, ValueError):
                    continue

        if not category_scores:
            overall = self._extract_existing_overall(evaluation)
            if overall is not None and overall > 0:
                category_scores = {
                    "technical_implementation": overall,
                    "functionality_results": overall,
                    "innovation_practices": overall,
                }
        return category_scores

    def _set_category_score(self, adapted: dict, category: str, score: float, original: float, explanation: str) -> None:
        adjusted = adapted.setdefault("adjusted_scores", {})
        adjusted[category] = {
            "score": round(score, 1),
            "original": round(original, 1),
            "difference": round(score - original, 1),
            "explanation": explanation,
        }
        scores = adapted.get("scores")
        if isinstance(scores, dict) and category in scores:
            if isinstance(scores[category], dict):
                scores[category]["score"] = round(score, 1)
                scores[category]["original_score"] = round(original, 1)
            else:
                scores[category] = {"score": round(score, 1), "original_score": round(original, 1)}

    def _generate_experience_feedback(
        self,
        adapted: dict,
        experience_level: str,
        config: Dict[str, Any],
        benchmark: Dict[str, Any],
        adjustments: List[Dict[str, Any]],
    ) -> str:
        overall = float(adapted.get("overall_score", 0) or 0)
        original = float(adapted.get("original_overall", overall) or 0)
        if overall >= benchmark["excellent"]:
            performance, recommendation = "EXCELLENT", "Strong hire - Exceptional for this level"
        elif overall >= benchmark["good"]:
            performance, recommendation = "GOOD", "Hire - Meets or exceeds expectations"
        elif overall >= benchmark["min"]:
            performance, recommendation = "SATISFACTORY", "Consider - Meets minimum requirements"
        else:
            performance, recommendation = "NEEDS IMPROVEMENT", "Further development needed"

        lines = [
            f"## Experience-Aware Assessment: {experience_level.replace('_', ' ').title()}",
            "",
            f"**Raw Score:** {original:.1f}/100",
            f"**Experience-Adjusted Score:** {overall:.1f}/100",
            f"**Net Adjustment:** {overall - original:+.1f} points",
            f"**Performance Rating:** {performance}",
            "",
            "### Category-wise Breakdown:",
        ]
        for item in adjustments:
            lines.append(
                f"- **{item['category']}**: {item['original']:.1f} → {item['adjusted']:.1f} "
                f"({item['difference']:+.1f}); expectation gap {item['gap']:+.1f}"
            )
        lines.extend([
            "",
            "### Benchmarks:",
            f"- Minimum acceptable: {benchmark['min']}/100",
            f"- Good: {benchmark['good']}/100",
            f"- Excellent: {benchmark['excellent']}/100",
            "",
            f"### Recommendation: {recommendation}",
        ])
        return "\n".join(lines)
