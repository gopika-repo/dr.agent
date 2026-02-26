# models/experience_evaluator.py
"""
EXPERIENCE-AWARE EVALUATION ENGINE - FIXED VERSION
Proper scoring where higher experience gets stricter grading
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import statistics

class ExperienceAwareEvaluator:
    def __init__(self):
        # Industry benchmarks for each experience level
        self.experience_benchmarks = {
            "1st_year": {
                "score_range": "95-100",  # Most lenient
                "expected_score": 60,
                "multiplier": 1.0,        # No penalty
                "strictness": 0.3,        # Least strict
                "penalty_weight": 0.5,    # Low penalties
                "reward_weight": 1.5      # High rewards
            },
            "2nd_year": {
                "score_range": "90-95",
                "expected_score": 65,
                "multiplier": 0.95,       # Slight penalty
                "strictness": 0.4,
                "penalty_weight": 0.6,
                "reward_weight": 1.3
            },
            "3rd_year": {
                "score_range": "80-85",
                "expected_score": 70,
                "multiplier": 0.90,       # Moderate penalty
                "strictness": 0.5,
                "penalty_weight": 0.7,
                "reward_weight": 1.1
            },
            "4th_year": {
                "score_range": "75-80",
                "expected_score": 75,
                "multiplier": 0.85,       # Significant penalty
                "strictness": 0.6,
                "penalty_weight": 0.8,
                "reward_weight": 1.0
            },
            "fresher": {
                "score_range": "70-75",
                "expected_score": 68,
                "multiplier": 0.92,       # Recent grad penalty
                "strictness": 0.55,
                "penalty_weight": 0.75,
                "reward_weight": 1.2
            },
            "experienced_0_2": {
                "score_range": "65-70",
                "expected_score": 78,
                "multiplier": 0.80,       # Experienced penalty
                "strictness": 0.7,
                "penalty_weight": 0.9,
                "reward_weight": 0.9
            },
            "senior": {
                "score_range": "60-65",   # Most strict
                "expected_score": 85,
                "multiplier": 0.75,       # Senior penalty (strictest)
                "strictness": 0.8,
                "penalty_weight": 1.0,    # Full penalties
                "reward_weight": 0.8      # Low rewards
            },
            "industry": {
                "score_range": "70-90",
                "expected_score": 75,
                "multiplier": 0.88,
                "strictness": 0.7,
                "penalty_weight": 0.85,
                "reward_weight": 0.9
            }
        }
        
        # Industry expectations for each level
        self.industry_expectations = {
            "1st_year": [
                "Basic understanding of programming concepts",
                "Ability to write simple working code",
                "Familiarity with version control",
                "Understanding of basic algorithms"
            ],
            "2nd_year": [
                "Good grasp of data structures",
                "Ability to work with APIs",
                "Basic understanding of databases",
                "Simple project implementation"
            ],
            "3rd_year": [
                "Good software design principles",
                "Ability to work in teams",
                "Understanding of testing",
                "Moderate complexity projects"
            ],
            "4th_year": [
                "Production-ready code quality",
                "Good architecture decisions",
                "Understanding of deployment",
                "Complex project implementation"
            ],
            "fresher": [
                "Industry-standard coding practices",
                "Ability to work independently",
                "Good problem-solving skills",
                "Ready for entry-level position"
            ],
            "experienced_0_2": [
                "Professional code quality",
                "Good system design",
                "Understanding of scalability",
                "Team collaboration skills"
            ],
            "senior": [
                "Enterprise architecture",
                "Leadership in technical decisions",
                "Advanced system design",
                "Mentorship capabilities"
            ],
            "industry": [
                "Production-ready code quality",
                "Standard professional practices",
                "Clear documentation and tests",
                "Ready for immediate industry deployment"
            ]
        }
    
    def evaluate_with_experience(self, repo_content: str, code_analysis: Dict, 
                               experience_level: str, challenge_id: str) -> Dict:
        """
        Evaluate repository with experience context
        Higher experience = Stricter grading = Lower scores for same quality
        
        Returns comprehensive evaluation with proper calculation breakdown
        """
        
        # Get experience configuration
        exp_config = self.experience_benchmarks.get(experience_level, 
                                                   self.experience_benchmarks["fresher"])
        
        # Step 1: Calculate RAW technical score (0-100)
        raw_score = self._calculate_raw_technical_score(code_analysis, challenge_id)
        
        # Step 2: Apply experience adjustments
        adjusted_score, breakdown = self._apply_experience_adjustments(
            raw_score, exp_config, experience_level, code_analysis, challenge_id
        )
        
        # Step 3: Calculate performance metrics
        expected_score = exp_config["expected_score"]
        performance_gap = adjusted_score - expected_score
        score_range = exp_config["score_range"]
        
        # Step 4: Determine hiring decision
        hiring_decision = self._determine_hiring_decision(
            adjusted_score, performance_gap, experience_level
        )
        
        # Step 5: Generate detailed feedback
        feedback = self._generate_detailed_feedback(
            raw_score, adjusted_score, exp_config, experience_level,
            performance_gap, hiring_decision, code_analysis, breakdown
        )
        
        # Step 6: Prepare final result
        return {
            "experience_level": experience_level,
            "score_range": score_range,
            "calculation_steps": self._get_calculation_steps(breakdown),
            
            # Scores
            "raw_technical_score": round(raw_score, 1),
            "final_adjusted_score": round(adjusted_score, 1),
            "industry_expected": expected_score,
            "performance_gap": round(performance_gap, 1),
            
            # Decisions
            "hiring_decision": hiring_decision,
            "recommendation": self._get_recommendation(adjusted_score, experience_level),
            
            # Details
            "feedback": feedback,
            "industry_expectations": self.industry_expectations.get(experience_level, []),
            "score_breakdown": breakdown,
            "evidence_summary": self._generate_evidence_summary(code_analysis)
        }
    
    def _calculate_raw_technical_score(self, code_analysis: Dict, challenge_id: str) -> float:
        """Calculate raw technical score from code analysis (0-100)"""
        
        # Each category contributes to total score
        category_scores = {}
        
        # 1. Code Quality (25 points max)
        code_quality_score = self._calculate_code_quality_score(code_analysis)
        category_scores["code_quality"] = min(code_quality_score, 25)
        
        # 2. Architecture & Structure (20 points max)
        architecture_score = self._calculate_architecture_score(code_analysis)
        category_scores["architecture"] = min(architecture_score, 20)
        
        # 3. Documentation (15 points max)
        documentation_score = self._calculate_documentation_score(code_analysis)
        category_scores["documentation"] = min(documentation_score, 15)
        
        # 4. Testing (15 points max)
        testing_score = self._calculate_testing_score(code_analysis)
        category_scores["testing"] = min(testing_score, 15)
        
        # 5. Production Readiness (15 points max)
        production_score = self._calculate_production_score(code_analysis)
        category_scores["production"] = min(production_score, 15)
        
        # 6. Challenge Specific (10 points max)
        challenge_score = self._calculate_challenge_score(code_analysis, challenge_id)
        category_scores["challenge_specific"] = min(challenge_score, 10)
        
        # Calculate total raw score (max 100)
        total_score = sum(category_scores.values())
        return min(total_score, 100)
    
    def _calculate_code_quality_score(self, code_analysis: Dict) -> float:
        """Calculate code quality score (0-25)"""
        score = 0
        
        # Check Python metrics
        quality = code_analysis.get("code_quality", {})
        if "python_metrics" in quality:
            py_metrics = quality["python_metrics"]
            
            # Functions and classes (0-8 points)
            functions = len(py_metrics.get("functions", []))
            classes = len(py_metrics.get("classes", []))
            if functions >= 10 and classes >= 3:
                score += 8
            elif functions >= 5 and classes >= 2:
                score += 5
            elif functions >= 2:
                score += 3
            
            # Type hints and docstrings (0-5 points)
            if py_metrics.get("has_type_hints", False):
                score += 2
            if py_metrics.get("has_docstrings", False):
                score += 2
            if py_metrics.get("has_decorators", False):
                score += 1
        
        # Error handling and logging (0-7 points)
        overall = quality.get("overall", {})
        if overall.get("has_error_handling", False):
            score += 4
        if overall.get("has_logging", False):
            score += 2
        if overall.get("has_comments", False):
            score += 1
        
        # Code patterns (0-5 points)
        patterns = code_analysis.get("code_patterns_found", {})
        if patterns.get("error_handling"):
            score += 3
        if patterns.get("logging"):
            score += 2
        
        return min(score, 25)
    
    def _calculate_architecture_score(self, code_analysis: Dict) -> float:
        """Calculate architecture score (0-20)"""
        score = 0
        
        structure = code_analysis.get("structure", {})
        
        # Directory structure (0-8 points)
        key_dirs = structure.get("key_directories", {})
        if key_dirs.get("src") or key_dirs.get("app"):
            score += 4
        if key_dirs.get("tests") or key_dirs.get("test"):
            score += 2
        if key_dirs.get("config") or key_dirs.get("configuration"):
            score += 1
        if key_dirs.get("docs") or key_dirs.get("documentation"):
            score += 1
        
        # File organization (0-6 points)
        files = code_analysis.get("files", {})
        if files.get("code_file_details"):
            code_files = len(files["code_file_details"])
            if code_files >= 10:
                score += 4
            elif code_files >= 5:
                score += 2
            elif code_files >= 2:
                score += 1
            
            # Check for largest files
            largest_files = files.get("largest_files", [])
            if largest_files and all(f['size_kb'] < 100 for f in largest_files[:3]):
                score += 2
        
        # Architecture patterns (0-6 points)
        patterns = structure.get("architecture_patterns", [])
        if patterns:
            score += min(len(patterns) * 2, 6)
        
        return min(score, 20)
    
    def _calculate_documentation_score(self, code_analysis: Dict) -> float:
        """Calculate documentation score (0-15)"""
        score = 0
        
        docs = code_analysis.get("documentation", {})
        readme = docs.get("readme", {})
        
        # README quality (0-8 points)
        if readme.get("exists", False):
            score += 3
            
            quality = readme.get("quality_score", 0)
            score += min(quality, 5)  # Max 5 points for quality
            
            sections = readme.get("sections", {})
            if sections.get("installation"):
                score += 1
            if sections.get("usage"):
                score += 1
        
        # API and architecture docs (0-4 points)
        if docs.get("api_docs", {}).get("exists", False):
            score += 2
        if docs.get("architecture_docs", {}).get("exists", False):
            score += 2
        
        # Examples (0-3 points)
        if docs.get("examples", {}).get("exists", False):
            score += 3
        
        return min(score, 15)
    
    def _calculate_testing_score(self, code_analysis: Dict) -> float:
        """Calculate testing score (0-15)"""
        score = 0
        
        testing = code_analysis.get("testing", {})
        
        # Test presence (0-5 points)
        if testing.get("has_tests", False):
            score += 3
            
            test_files = len(testing.get("test_files", []))
            if test_files >= 5:
                score += 2
            elif test_files >= 2:
                score += 1
        
        # Test frameworks (0-4 points)
        frameworks = len(testing.get("test_frameworks", []))
        score += min(frameworks * 2, 4)
        
        # Test structure and coverage (0-6 points)
        if testing.get("test_directory_structure", False):
            score += 2
        if testing.get("coverage", False):
            score += 2
        
        # Test patterns found
        patterns = code_analysis.get("code_patterns_found", {}).get("testing", [])
        if patterns:
            score += min(len(patterns) * 2, 2)
        
        return min(score, 15)
    
    def _calculate_production_score(self, code_analysis: Dict) -> float:
        """Calculate production readiness score (0-15)"""
        score = 0
        
        # Docker (0-6 points)
        docker = code_analysis.get("docker", {})
        if docker.get("has_dockerfile", False):
            score += 3
            
            analysis = docker.get("dockerfile_analysis", {})
            if analysis.get("multi_stage", False):
                score += 1
            if analysis.get("has_healthcheck", False):
                score += 1
            if analysis.get("has_optimizations", False):
                score += 1
        
        if docker.get("has_docker_compose", False):
            score += 1
        
        # CI/CD (0-4 points)
        ci_cd = code_analysis.get("ci_cd", {})
        if ci_cd.get("has_ci", False):
            score += 2
            if len(ci_cd.get("ci_files", [])) >= 2:
                score += 1
            if len(ci_cd.get("ci_platforms", [])) >= 2:
                score += 1
        
        # Configuration files (0-5 points)
        key_files = code_analysis.get("key_files_content", {})
        if key_files.get("config_files"):
            score += 2
        if key_files.get("requirements"):
            score += 2
        if key_files.get(".env", "") or ".env" in str(key_files.get("config_files", {})):
            score += 1
        
        return min(score, 15)
    
    def _calculate_challenge_score(self, code_analysis: Dict, challenge_id: str) -> float:
        """Calculate challenge-specific score (0-10)"""
        score = 0
        
        challenge_specific = code_analysis.get("challenge_specific", {})
        
        if challenge_id == "challenge_023":  # AI Agents
            ai_ml = challenge_specific.get("ai_ml_indicators", {})
            if ai_ml.get("has_ai_ml", False):
                score += 4
                libs = len(ai_ml.get("libraries", []))
                score += min(libs, 3)
            if ai_ml.get("model_files"):
                score += 2
            if ai_ml.get("notebooks"):
                score += 1
        
        elif challenge_id == "challenge_024":  # Healthcare AI
            ai_ml = challenge_specific.get("ai_ml_indicators", {})
            web = challenge_specific.get("web_app_indicators", {})
            
            if ai_ml.get("has_ai_ml", False):
                score += 3
            if web.get("has_web_app", False):
                score += 3
            if ai_ml.get("has_ai_ml", False) and web.get("has_web_app", False):
                score += 4
        
        elif challenge_id == "challenge_025":  # Data Pipeline
            data = challenge_specific.get("data_pipeline_indicators", {})
            if data.get("has_data_pipeline", False):
                score += 6
                etl_files = len(data.get("etl_files", []))
                score += min(etl_files, 4)
        
        elif challenge_id in ["challenge_026", "challenge_027"]:  # Web Apps
            web = challenge_specific.get("web_app_indicators", {})
            if web.get("has_web_app", False):
                score += 5
                frameworks = len(web.get("frameworks", []))
                score += min(frameworks, 3)
                if web.get("static_files") and web.get("templates"):
                    score += 2
        
        return min(score, 10)
    
    def _apply_experience_adjustments(self, raw_score: float, exp_config: Dict, 
                                    experience_level: str, code_analysis: Dict, 
                                    challenge_id: str) -> tuple:
        """Apply experience adjustments - Higher experience = Stricter grading"""
        
        breakdown = {
            "raw_score": raw_score,
            "multiplier_applied": exp_config["multiplier"],
            "penalties": 0,
            "rewards": 0,
            "adjustment_details": []
        }
        
        # Step 1: Apply experience multiplier
        adjusted = raw_score * exp_config["multiplier"]
        breakdown["adjustment_details"].append({
            "step": "Experience Multiplier",
            "value": f"{exp_config['multiplier']}x",
            "calculation": f"{raw_score} × {exp_config['multiplier']} = {adjusted:.1f}"
        })
        
        # Step 2: Apply penalties based on missing expectations
        penalties = self._calculate_penalties(code_analysis, experience_level, challenge_id)
        adjusted -= penalties
        breakdown["penalties"] = penalties
        
        if penalties > 0:
            breakdown["adjustment_details"].append({
                "step": "Experience Penalties",
                "value": f"-{penalties:.1f}",
                "calculation": f"Missing features expected at {experience_level} level"
            })
        
        # Step 3: Apply rewards for exceeding expectations
        rewards = self._calculate_rewards(code_analysis, experience_level, challenge_id)
        adjusted += rewards
        breakdown["rewards"] = rewards
        
        if rewards > 0:
            breakdown["adjustment_details"].append({
                "step": "Experience Rewards",
                "value": f"+{rewards:.1f}",
                "calculation": "Exceeding expectations for experience level"
            })
        
        # Step 4: Ensure score is within bounds
        adjusted = max(0, min(adjusted, 100))
        breakdown["final_score"] = adjusted
        
        return adjusted, breakdown
    
    def _calculate_penalties(self, code_analysis: Dict, experience_level: str, 
                            challenge_id: str) -> float:
        """Calculate penalties based on missing expectations"""
        penalties = 0
        
        # Higher experience = higher penalties for missing features
        if experience_level in ["senior", "experienced_0_2"]:
            # Enterprise expectations
            if not code_analysis.get("docker", {}).get("has_dockerfile", False):
                penalties += 5
            if not code_analysis.get("testing", {}).get("has_tests", False):
                penalties += 8
            if not code_analysis.get("ci_cd", {}).get("has_ci", False):
                penalties += 3
            if code_analysis.get("documentation", {}).get("readme", {}).get("quality_score", 0) < 7:
                penalties += 4
        
        elif experience_level in ["3rd_year", "4th_year"]:
            # Intermediate expectations
            if not code_analysis.get("testing", {}).get("has_tests", False):
                penalties += 5
            if not code_analysis.get("docker", {}).get("has_dockerfile", False):
                penalties += 3
            if code_analysis.get("documentation", {}).get("readme", {}).get("quality_score", 0) < 5:
                penalties += 3
        
        elif experience_level in ["1st_year", "2nd_year"]:
            # Junior expectations (minimal penalties)
            if not code_analysis.get("documentation", {}).get("readme", {}).get("exists", False):
                penalties += 2
        
        # Challenge-specific penalties
        penalties += self._calculate_challenge_penalties(code_analysis, challenge_id, experience_level)
        
        return penalties
    
    def _calculate_challenge_penalties(self, code_analysis: Dict, challenge_id: str, 
                                      experience_level: str) -> float:
        """Calculate challenge-specific penalties"""
        penalties = 0
        
        challenge_specific = code_analysis.get("challenge_specific", {})
        
        if challenge_id == "challenge_023":  # AI Agents
            if not challenge_specific.get("ai_ml_indicators", {}).get("has_ai_ml", False):
                if experience_level in ["senior", "experienced_0_2"]:
                    penalties += 10
                elif experience_level in ["3rd_year", "4th_year"]:
                    penalties += 7
                else:
                    penalties += 3
        
        elif challenge_id == "challenge_024":  # Healthcare AI
            if not challenge_specific.get("ai_ml_indicators", {}).get("has_ai_ml", False):
                if experience_level in ["senior", "experienced_0_2"]:
                    penalties += 8
                elif experience_level in ["3rd_year", "4th_year"]:
                    penalties += 5
        
        return penalties
    
    def _calculate_rewards(self, code_analysis: Dict, experience_level: str, 
                          challenge_id: str) -> float:
        """Calculate rewards for exceeding expectations"""
        rewards = 0
        
        # Lower experience = higher rewards for good work
        if experience_level in ["1st_year", "2nd_year", "fresher"]:
            if code_analysis.get("testing", {}).get("has_tests", False):
                rewards += 3
            if code_analysis.get("docker", {}).get("has_dockerfile", False):
                rewards += 2
            if code_analysis.get("ci_cd", {}).get("has_ci", False):
                rewards += 2
        
        # Excellent documentation for any level
        if code_analysis.get("documentation", {}).get("readme", {}).get("quality_score", 0) >= 8:
            rewards += 2
        
        # Good architecture for higher levels
        if experience_level in ["3rd_year", "4th_year", "experienced_0_2"]:
            structure = code_analysis.get("structure", {})
            if structure.get("key_directories", {}).get("tests") and \
               structure.get("key_directories", {}).get("src"):
                rewards += 2
        
        return rewards
    
    def _determine_hiring_decision(self, adjusted_score: float, performance_gap: float, 
                                  experience_level: str) -> str:
        """Determine hiring decision with proper experience considerations"""
        
        # Get expected score for this level
        exp_config = self.experience_benchmarks.get(experience_level, 
                                                   self.experience_benchmarks["fresher"])
        expected_score = exp_config["expected_score"]
        
        # Different criteria for different experience levels
        if experience_level in ["senior", "industry", "experienced_0_2"]:
            if adjusted_score >= expected_score + 10:
                return "Strong Hire"
            elif adjusted_score >= expected_score:
                return "Hire"
            elif adjusted_score >= expected_score - 10:
                return "Borderline"
            else:
                return "Reject"
        
        elif experience_level in ["3rd_year", "4th_year"]:
            if adjusted_score >= expected_score + 15:
                return "Strong Hire"
            elif adjusted_score >= expected_score + 5:
                return "Hire"
            elif adjusted_score >= expected_score - 5:
                return "Borderline"
            else:
                return "Reject"
        
        else:  # 1st_year, 2nd_year, fresher
            if adjusted_score >= expected_score + 20:
                return "Strong Hire"
            elif adjusted_score >= expected_score + 10:
                return "Hire"
            elif adjusted_score >= expected_score:
                return "Borderline"
            else:
                return "Reject"
    
    def _get_recommendation(self, score: float, experience_level: str) -> str:
        """Get specific recommendation based on score and experience"""
        
        exp_config = self.experience_benchmarks.get(experience_level, 
                                                   self.experience_benchmarks["fresher"])
        expected = exp_config["expected_score"]
        
        if score >= expected + 15:
            return "✅ Exceptional candidate - Strongly recommend hiring"
        elif score >= expected + 5:
            return "👍 Good candidate - Recommend hiring"
        elif score >= expected:
            return "🤔 Average candidate - Consider for appropriate role"
        elif score >= expected - 10:
            return "⚠️ Below average - Consider for junior position or internship"
        else:
            return "❌ Not suitable - Needs significant improvement"
    
    def _get_calculation_steps(self, breakdown: Dict) -> List[str]:
        """Get calculation steps for display"""
        steps = []
        
        steps.append(f"1. Raw Technical Score: {breakdown.get('raw_score', 0):.1f}/100")
        
        for detail in breakdown.get("adjustment_details", []):
            steps.append(f"2. {detail['step']}: {detail['value']}")
            steps.append(f"   → {detail['calculation']}")
        
        steps.append(f"3. Final Adjusted Score: {breakdown.get('final_score', 0):.1f}/100")
        
        return steps
    
    def _generate_detailed_feedback(self, raw_score: float, adjusted_score: float,
                                  exp_config: Dict, experience_level: str,
                                  performance_gap: float, hiring_decision: str,
                                  code_analysis: Dict, breakdown: Dict) -> str:
        """Generate detailed feedback with calculation breakdown"""
        
        feedback_parts = []
        
        # Header
        feedback_parts.append(f"## 🎓 EXPERIENCE-AWARE EVALUATION")
        feedback_parts.append(f"**Experience Level:** {experience_level.replace('_', ' ').title()}")
        feedback_parts.append(f"**Expected Score Range:** {exp_config['score_range']}")
        feedback_parts.append(f"**Industry Benchmark:** {exp_config['expected_score']}/100")
        
        # Score Summary
        feedback_parts.append("")
        feedback_parts.append("### 📊 SCORE SUMMARY")
        feedback_parts.append(f"- **Raw Technical Score:** {raw_score:.1f}/100")
        feedback_parts.append(f"- **Final Adjusted Score:** {adjusted_score:.1f}/100")
        feedback_parts.append(f"- **Performance Gap:** {'+' if performance_gap >= 0 else ''}{performance_gap:.1f}")
        feedback_parts.append(f"- **Hiring Decision:** {hiring_decision}")
        
        # Calculation Steps
        feedback_parts.append("")
        feedback_parts.append("### 🧮 CALCULATION STEPS")
        for step in self._get_calculation_steps(breakdown):
            feedback_parts.append(f"- {step}")
        
        # Evidence Summary
        feedback_parts.append("")
        feedback_parts.append("### 🔍 EVIDENCE SUMMARY")
        
        stats = code_analysis.get("stats", {})
        if stats.get("file_count", 0) > 0:
            feedback_parts.append(f"- **Files Analyzed:** {stats['file_count']} files")
        
        quality = code_analysis.get("code_quality", {})
        if "python_metrics" in quality:
            py_metrics = quality["python_metrics"]
            functions = py_metrics.get("functions", 0)
            classes = py_metrics.get("classes", 0)
            feedback_parts.append(f"- **Code Structure:** {functions} functions, {classes} classes")
        
        testing = code_analysis.get("testing", {})
        if testing.get("has_tests", False):
            test_files = len(testing.get("test_files", []))
            feedback_parts.append(f"- **Testing:** {test_files} test files found")
        else:
            feedback_parts.append("- **Testing:** No test files found")
        
        docker = code_analysis.get("docker", {})
        if docker.get("has_dockerfile", False):
            feedback_parts.append("- **Deployment:** Docker configuration found")
        
        # Experience-Specific Assessment
        feedback_parts.append("")
        feedback_parts.append("### 🎯 EXPERIENCE-RELATED ASSESSMENT")
        
        if performance_gap > 10:
            feedback_parts.append(f"✅ **EXCEEDS EXPECTATIONS:** For a {experience_level.replace('_', ' ')} developer, this is excellent work.")
        elif performance_gap >= 0:
            feedback_parts.append(f"✓ **MEETS EXPECTATIONS:** Good work for a {experience_level.replace('_', ' ')} developer.")
        elif performance_gap >= -10:
            feedback_parts.append(f"⚠️ **BELOW EXPECTATIONS:** Needs improvement for a {experience_level.replace('_', ' ')} developer.")
        else:
            feedback_parts.append(f"❌ **SIGNIFICANTLY BELOW EXPECTATIONS:** Does not meet standards for {experience_level.replace('_', ' ')} developer.")
        
        # Recommendations
        feedback_parts.append("")
        feedback_parts.append("### 📝 RECOMMENDATIONS")
        
        if experience_level in ["1st_year", "2nd_year"]:
            feedback_parts.append("**For Junior Developers:**")
            feedback_parts.append("- Focus on clean, well-documented code")
            feedback_parts.append("- Practice writing tests")
            feedback_parts.append("- Learn basic deployment concepts")
        
        elif experience_level in ["3rd_year", "4th_year"]:
            feedback_parts.append("**For Intermediate Developers:**")
            feedback_parts.append("- Implement comprehensive testing")
            feedback_parts.append("- Work on system design skills")
            feedback_parts.append("- Learn CI/CD and deployment best practices")
        
        else:  # experienced_0_2, senior
            feedback_parts.append("**For Experienced Developers:**")
            feedback_parts.append("- Focus on enterprise architecture")
            feedback_parts.append("- Implement monitoring and observability")
            feedback_parts.append("- Consider scalability and security")
        
        return "\n".join(feedback_parts)
    
    def _generate_evidence_summary(self, code_analysis: Dict) -> Dict:
        """Generate summary of evidence found"""
        summary = {
            "file_count": code_analysis.get("stats", {}).get("file_count", 0),
            "code_files": code_analysis.get("stats", {}).get("code_files", 0),
            "lines_of_code": code_analysis.get("stats", {}).get("line_count", 0),
            "has_tests": code_analysis.get("testing", {}).get("has_tests", False),
            "has_docker": code_analysis.get("docker", {}).get("has_dockerfile", False),
            "has_ci_cd": code_analysis.get("ci_cd", {}).get("has_ci", False),
            "documentation_quality": code_analysis.get("documentation", {}).get("readme", {}).get("quality_score", 0),
            "error_handling_found": code_analysis.get("code_quality", {}).get("overall", {}).get("has_error_handling", False),
            "architecture_score": self._calculate_architecture_score(code_analysis)
        }
        return summary