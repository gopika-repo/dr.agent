# experience_adaptor.py - PROPER EXPERIENCE-AWARE SCORING
import json
from typing import Dict, Tuple, List

class ExperienceScoreAdapter:
    """
    Adapts scores based on experience level using mathematical formulas
    
    Key Principle: Higher experience = Higher expectations = Stricter grading
    
    Formula: adjusted_score = raw_score * difficulty_multiplier + experience_bonus
    
    Where:
    - difficulty_multiplier < 1 for higher experience (makes scoring stricter)
    - difficulty_multiplier > 1 for lower experience (more lenient)
    - experience_bonus adjusts based on performance relative to expectations
    """
    
    def __init__(self):
        # Experience level configurations
        self.experience_configs = {
            '1st_year': {
                'multiplier': 1.15,  # More lenient grading
                'expectation_base': 55,
                'excellent_threshold': 75,
                'penalty_factor': 0.3,
                'reward_factor': 1.2,
                'description': '1st Year Student - Basic understanding expected'
            },
            '2nd_year': {
                'multiplier': 1.10,
                'expectation_base': 60,
                'excellent_threshold': 78,
                'penalty_factor': 0.4,
                'reward_factor': 1.1,
                'description': '2nd Year Student - Growing proficiency'
            },
            '3rd_year': {
                'multiplier': 1.05,
                'expectation_base': 65,
                'excellent_threshold': 80,
                'penalty_factor': 0.5,
                'reward_factor': 1.0,
                'description': '3rd Year Student - Solid fundamentals'
            },
            '4th_year': {
                'multiplier': 1.00,  # Neutral - expected to be graduate-ready
                'expectation_base': 70,
                'excellent_threshold': 83,
                'penalty_factor': 0.6,
                'reward_factor': 0.9,
                'description': 'Final Year Student - Near-graduate level'
            },
            'fresher': {
                'multiplier': 0.95,  # Slightly stricter than students
                'expectation_base': 68,
                'excellent_threshold': 80,
                'penalty_factor': 0.7,
                'reward_factor': 0.8,
                'description': 'Recent Graduate - Entry-level professional'
            },
            'experienced_0_2': {
                'multiplier': 0.85,  # Stricter grading
                'expectation_base': 75,
                'excellent_threshold': 86,
                'penalty_factor': 0.8,
                'reward_factor': 0.7,
                'description': '1-2 Years Experience - Junior professional'
            },
            'senior': {
                'multiplier': 0.75,  # Very strict grading
                'expectation_base': 82,
                'excellent_threshold': 92,
                'penalty_factor': 0.9,
                'reward_factor': 0.6,
                'description': '3+ Years Experience - Senior professional'
            },
            'industry': {
                'multiplier': 0.88,  # Industry-standard readiness
                'expectation_base': 75,
                'excellent_threshold': 88,
                'penalty_factor': 0.8,
                'reward_factor': 0.8,
                'description': 'Industry Ready - Professional standard assessment'
            },
            'beginner': {
                'multiplier': 1.10, 
                'expectation_base': 55,
                'excellent_threshold': 75,
                'penalty_factor': 0.3,
                'reward_factor': 1.2,
                'description': 'Beginner - Focus on basic implementation'
            },
            'intermediate': {
                'multiplier': 0.95,
                'expectation_base': 70,
                'excellent_threshold': 82,
                'penalty_factor': 0.6,
                'reward_factor': 0.9,
                'description': 'Intermediate - Solid logic and features'
            },
            'advanced': {
                'multiplier': 0.80,
                'expectation_base': 85,
                'excellent_threshold': 92,
                'penalty_factor': 0.9,
                'reward_factor': 0.7,
                'description': 'Advanced - High scale/quality standards'
            }
        }
        
        # Industry benchmarks for each level
        self.industry_benchmarks = {
            '1st_year': {'min': 40, 'good': 60, 'excellent': 75},
            '2nd_year': {'min': 45, 'good': 65, 'excellent': 80},
            '3rd_year': {'min': 50, 'good': 70, 'excellent': 82},
            '4th_year': {'min': 55, 'good': 75, 'excellent': 85},
            'fresher': {'min': 50, 'good': 68, 'excellent': 80},
            'experienced_0_2': {'min': 60, 'good': 78, 'excellent': 88},
            'senior': {'min': 70, 'good': 85, 'excellent': 95},
            'industry': {'min': 65, 'good': 78, 'excellent': 90},
            'beginner': {'min': 40, 'good': 60, 'excellent': 80},
            'intermediate': {'min': 60, 'good': 75, 'excellent': 85},
            'advanced': {'min': 75, 'good': 85, 'excellent': 95}
        }
    
    def adapt_scores(self, gemini_evaluation: dict, experience_level: str) -> dict:
        """
        Adapt Gemini's evaluation scores based on experience level
        
        Process:
        1. Extract raw scores from Gemini evaluation
        2. Apply experience-based multiplier
        3. Adjust based on expectations
        4. Calculate final scores
        """
        
        # Get experience configuration
        config = self.experience_configs.get(experience_level, self.experience_configs['fresher'])
        benchmark = self.industry_benchmarks.get(experience_level, self.industry_benchmarks['fresher'])
        
        # Make a deep copy to avoid modifying original
        adapted = json.loads(json.dumps(gemini_evaluation))
        
        # Extract category scores from Gemini evaluation
        category_scores = self._extract_category_scores(gemini_evaluation)
        
        # Track adjustments
        adjustments = []
        total_raw = 0
        total_adjusted = 0
        category_count = 0
        
        # Adapt each category
        for category, raw_score in category_scores.items():
            # Apply experience-based adjustment
            adjusted_score, adjustment_details = self._apply_experience_adjustment(
                raw_score=raw_score,
                category=category,
                config=config,
                benchmark=benchmark,
                experience_level=experience_level
            )
            
            # Store adjusted score
            self._set_category_score(adapted, category, adjusted_score, raw_score, adjustment_details['explanation'])
            
            total_raw += raw_score
            total_adjusted += adjusted_score
            category_count += 1
            
            adjustments.append({
                'category': category.replace('_', ' ').title(),
                'original': round(raw_score, 1),
                'adjusted': round(adjusted_score, 1),
                'difference': round(adjusted_score - raw_score, 1),
                'expected': adjustment_details['expected'],
                'gap': adjustment_details['gap'],
                'explanation': adjustment_details['explanation']
            })
        
        # Calculate overall scores
        if category_count > 0:
            adapted['original_overall'] = round(total_raw / category_count, 1)
            adapted['overall_score'] = round(total_adjusted / category_count, 1)
        else:
            adapted['original_overall'] = 0
            adapted['overall_score'] = 0
        
        # Add experience context
        adapted['experience_context'] = {
            'level': experience_level,
            'multiplier': config['multiplier'],
            'expectation_base': config['expectation_base'],
            'excellent_threshold': config['excellent_threshold'],
            'penalty_factor': config['penalty_factor'],
            'reward_factor': config['reward_factor'],
            'description': config['description'],
            'benchmark_min': benchmark['min'],
            'benchmark_good': benchmark['good'],
            'benchmark_excellent': benchmark['excellent']
        }
        
        adapted['score_adjustments'] = adjustments
        
        # Add experience-aware feedback
        adapted['experience_feedback'] = self._generate_experience_feedback(
            adapted, experience_level, config, benchmark, adjustments
        )
        
        # Add actionable hiring recommendation field for frontend use
        adapted['hiring_recommendation'] = self._get_actionable_recommendation(
            adapted.get('overall_score', 0), experience_level, benchmark
        )
        
        return adapted

    def _get_actionable_recommendation(self, score: float, level: str, benchmark: dict) -> str:
        """Get clear, actionable outcomes based on score and level"""
        is_student = any(x in level for x in ['year', 'student'])
        
        if score >= benchmark['excellent']:
            return "Exceptional – Direct Interview"
        elif score >= benchmark['good']:
            if is_student:
                return "Strong Internship Hire"
            return "Strong Hire"
        elif score >= benchmark['min']:
            return "Average – Potential Hire"
        else:
            return "Below Benchmark – Needs Improvement"
    
    def _apply_experience_adjustment(self, raw_score: float, category: str, 
                                    config: Dict, benchmark: Dict, 
                                    experience_level: str) -> Tuple[float, Dict]:
        """
        Apply experience-based adjustment to a single category score
        
        Formula:
        1. Apply base multiplier: base_score = raw_score * multiplier
        2. Calculate gap from expectation: gap = base_score - expectation
        3. Apply penalty/reward: 
           - If below expectation: penalty = gap * penalty_factor
           - If above expectation: reward = gap * reward_factor
        4. Final score = base_score + penalty/reward
        """
        
        # Step 1: Apply base multiplier
        multiplier = config['multiplier']
        base_score = raw_score * multiplier
        
        # Step 2: Determine expectation for this category
        expectation = config['expectation_base']
        
        # Step 3: Calculate gap
        gap = base_score - expectation
        
        # Step 4: Apply penalty or reward
        if gap < 0:
            # Below expectation - apply penalty
            penalty_factor = config['penalty_factor']
            adjustment = gap * penalty_factor  # Negative value
            adjusted_score = base_score + adjustment
            
            explanation = (
                f"Raw score: {raw_score:.1f} → Base (×{multiplier}): {base_score:.1f} → "
                f"Below expectation ({expectation}) by {abs(gap):.1f} → "
                f"Penalty (×{penalty_factor}): {adjustment:.1f} → "
                f"Final: {adjusted_score:.1f}"
            )
        else:
            # Above expectation - apply reward
            reward_factor = config['reward_factor']
            adjustment = gap * (reward_factor - 1)  # Can be positive or negative
            adjusted_score = base_score + adjustment
            
            explanation = (
                f"Raw score: {raw_score:.1f} → Base (×{multiplier}): {base_score:.1f} → "
                f"Above expectation ({expectation}) by {gap:.1f} → "
                f"Reward (×{reward_factor}): {adjustment:+.1f} → "
                f"Final: {adjusted_score:.1f}"
            )
        
        # Ensure score is within bounds
        adjusted_score = max(0, min(100, adjusted_score))
        
        return adjusted_score, {
            'expected': expectation,
            'gap': round(gap, 1),
            'adjustment': round(adjustment, 1),
            'explanation': explanation
        }
    
    def _extract_category_scores(self, evaluation: dict) -> Dict[str, float]:
        """Extract category scores from Gemini evaluation"""
        category_scores = {}
        
        # Try different possible structures
        
        # Structure 1: Direct scores object
        if 'scores' in evaluation and isinstance(evaluation['scores'], dict):
            for category, data in evaluation['scores'].items():
                if isinstance(data, dict) and 'score' in data:
                    category_scores[category] = float(data['score'])
                elif isinstance(data, (int, float)):
                    category_scores[category] = float(data)
        
        # Structure 2: Report with evaluation_criteria
        elif 'report' in evaluation and 'evaluation_criteria' in evaluation['report']:
            for criterion in evaluation['report']['evaluation_criteria']:
                if 'criterion_name' in criterion and 'score' in criterion:
                    category = criterion['criterion_name'].lower().replace(' ', '_')
                    category_scores[category] = float(criterion['score'])
        
        # Structure 3: HiDevs score breakdown
        elif 'report' in evaluation and 'hidevs_score' in evaluation['report']:
            hidevs = evaluation['report']['hidevs_score']
            if 'breakdown' in hidevs:
                for category, score in hidevs['breakdown'].items():
                    if isinstance(score, (int, float)):
                        category_scores[category] = float(score)
        
        # If no categories found, try to infer from overall score
        if not category_scores:
            overall = 0
            if 'overall' in evaluation:
                overall = float(evaluation['overall'])
            elif 'score' in evaluation:
                overall = float(evaluation['score'])
            elif 'report' in evaluation and 'hidevs_score' in evaluation['report']:
                overall = float(evaluation['report']['hidevs_score'].get('score', 0))
            
            if overall > 0:
                # Create default categories with the overall score
                category_scores = {
                    'technical_implementation': overall,
                    'functionality_results': overall,
                    'innovation_practices': overall
                }
        
        return category_scores
    
    def _set_category_score(self, adapted: dict, category: str, score: float, 
                           original: float, explanation: str):
        """Set a category score in the adapted evaluation"""
        
        # Create adjusted_scores structure if it doesn't exist
        if 'adjusted_scores' not in adapted:
            adapted['adjusted_scores'] = {}
        
        adapted['adjusted_scores'][category] = {
            'score': round(score, 1),
            'original': round(original, 1),
            'difference': round(score - original, 1),
            'explanation': explanation
        }
        
        # Also update in original structure if it exists
        if 'scores' in adapted and isinstance(adapted['scores'], dict):
            if category in adapted['scores']:
                if isinstance(adapted['scores'][category], dict):
                    adapted['scores'][category]['score'] = round(score, 1)
                    adapted['scores'][category]['original_score'] = round(original, 1)
                else:
                    adapted['scores'][category] = {
                        'score': round(score, 1),
                        'original_score': round(original, 1)
                    }
    
    def _generate_experience_feedback(self, adapted: dict, experience_level: str,
                                     config: Dict, benchmark: Dict, 
                                     adjustments: List[Dict]) -> str:
        """Generate experience-aware feedback"""
        
        overall = adapted.get('overall_score', 0)
        original = adapted.get('original_overall', overall)
        
        # Determine performance relative to benchmarks
        if overall >= benchmark['excellent']:
            performance = "EXCELLENT"
            emoji = "🏆"
            recommendation = "Strong hire - Exceptional for this level"
        elif overall >= benchmark['good']:
            performance = "GOOD"
            emoji = "👍"
            recommendation = "Hire - Meets or exceeds expectations"
        elif overall >= benchmark['min']:
            performance = "SATISFACTORY"
            emoji = "✓"
            recommendation = "Consider - Meets minimum requirements"
        else:
            performance = "NEEDS IMPROVEMENT"
            emoji = "📚"
            recommendation = "Further development needed"
        
        # Calculate total adjustment
        total_adjustment = overall - original
        
        feedback_lines = [
            f"## {emoji} Experience-Aware Assessment: {experience_level.replace('_', ' ').title()}",
            "",
            f"**Raw Gemini Score:** {original:.1f}/100",
            f"**Experience-Adjusted Score:** {overall:.1f}/100",
            f"**Net Adjustment:** {total_adjustment:+.1f} points",
            f"**Performance Rating:** {performance}",
            "",
            "### Adjustment Process:",
            "",
            f"For {experience_level.replace('_', ' ')} candidates:",
            f"- Base multiplier: {config['multiplier']} ({'more lenient' if config['multiplier'] > 1 else 'stricter'} than standard)",
            f"- Expected baseline: {config['expectation_base']}/100",
            f"- Excellent threshold: {config['excellent_threshold']}/100",
            f"- Penalty factor: {config['penalty_factor']} (applied when below expectations)",
            f"- Reward factor: {config['reward_factor']} (applied when above expectations)",
            "",
            "### Category-wise Breakdown:",
            ""
        ]
        
        # Add category adjustments
        for adj in adjustments:
            symbol = "⬆️" if adj['difference'] > 0 else "⬇️" if adj['difference'] < 0 else "➡️"
            feedback_lines.append(
                f"- {symbol} **{adj['category']}**: {adj['original']:.1f} → {adj['adjusted']:.1f} "
                f"({adj['difference']:+.1f}) - Gap from expectation: {adj['gap']:+.1f}"
            )
        
        feedback_lines.extend([
            "",
            "### Industry Benchmarks:",
            f"- Minimum acceptable: {benchmark['min']}/100",
            f"- Good performance: {benchmark['good']}/100",
            f"- Excellent performance: {benchmark['excellent']}/100",
            "",
            f"### Recommendation: {recommendation}"
        ])
        
        return "\n".join(feedback_lines)