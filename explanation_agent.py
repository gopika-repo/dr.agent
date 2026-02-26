# models/explanation_agent.py - Gemini AI Explanation Engine
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ExplanationEngine:
    def __init__(self, api_key: str):
        """Initialize with Gemini API key"""
        genai.configure(api_key=api_key)
        self.supported_models = [
            "gemini-2.0-flash",
            "gemini-2.0-pro",
            "gemini-2.5-pro",
            "gemini-2.5-flash"
        ]
    
    def analyze(self, analysis_results: Dict, evaluation_results: Dict, 
                challenge: Dict, model_name: str = "gemini-2.5-flash") -> Dict:
        """Generate detailed analysis using Gemini AI"""
        
        # Validate model
        if model_name not in self.supported_models:
            model_name = "gemini-2.5-flash"
        
        try:
            # Prepare prompt for Gemini
            prompt = self._create_analysis_prompt(analysis_results, evaluation_results, challenge)
            
            # Call Gemini
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 4000,
                }
            )
            
            # Handle multi-part responses properly
            if response.candidates and len(response.candidates) > 0:
                parts = response.candidates[0].content.parts
                response_text = "".join(part.text for part in parts if hasattr(part, 'text'))
            else:
                response_text = ""
            
            # Parse response
            return self._parse_gemini_response(response_text, evaluation_results)
            
        except Exception as e:
            # Fallback to rule-based analysis
            return self._analyze_rules_based(analysis_results, evaluation_results, challenge)
    
    def _create_analysis_prompt(self, analysis: Dict, evaluation: Dict, challenge: Dict) -> str:
        """Create detailed prompt for Gemini"""
        
        # Extract key information
        final_score = evaluation.get('final_score', 0)
        score_breakdown = evaluation.get('score_breakdown', [])
        
        # Repository information
        repo_info = self._extract_repo_info(analysis)
        
        # Create structured prompt
        prompt = f"""You are a senior technical hiring manager evaluating a GitHub repository for a coding challenge.

CHALLENGE: {challenge['title']}
{challenge['fullDescription']}

REPOSITORY ANALYSIS:
{json.dumps(repo_info, indent=2)}

EVALUATION RESULTS:
Final Score: {final_score}/115
Score Breakdown:
{chr(10).join([f"- {item.get('category', 'Unknown')}: {item.get('score', 0)}/{item.get('max', 100)}" for item in score_breakdown])}

YOUR TASK:
Based on the repository analysis and evaluation results, provide a comprehensive assessment in JSON format with the following structure:

1. STRENGTHS (3-5 items): Identify what is good about this repository. For each strength:
   - title: Brief title
   - evidence: Specific evidence from the analysis
   - impact: Why this is valuable

2. WEAKNESSES (3-5 items): Identify what needs improvement. For each weakness:
   - title: Brief title
   - evidence: Specific evidence from the analysis
   - impact: Why this matters

3. RECOMMENDATION: Provide hiring recommendation with:
   - type: One of ["Hire as Intern", "Consider for Internship", "Do Not Hire", "Strong Hire"]
   - justification: Detailed reasoning based on scores and analysis
   - suggested_improvements: What they need to work on

4. BENCHMARKS: Compare against industry standards:
   - intern_level: "Exceeds"/"Meets"/"Below" (benchmark: 60/115)
   - entry_level: "Exceeds"/"Meets"/"Below" (benchmark: 75/115)
   - strong_hire: "Exceeds"/"Meets"/"Below" (benchmark: 85/115)
   - exceptional: "Exceeds"/"Meets"/"Below" (benchmark: 90/115)
   - Include delta values (e.g., "+5" or "-10")

IMPORTANT:
- Be specific and evidence-based
- Focus on the challenge requirements
- Consider code quality, documentation, testing, and production readiness
- Provide actionable feedback

Return ONLY valid JSON in this exact structure:
{{
    "strengths": [
        {{
            "title": "string",
            "evidence": "string",
            "impact": "string"
        }}
    ],
    "weaknesses": [
        {{
            "title": "string",
            "evidence": "string",
            "impact": "string"
        }}
    ],
    "recommendation": {{
        "type": "string",
        "justification": "string",
        "suggested_improvements": "string"
    }},
    "benchmarks": {{
        "intern_level": "string",
        "entry_level": "string",
        "strong_hire": "string",
        "exceptional": "string",
        "intern_delta": "string",
        "entry_delta": "string",
        "strong_delta": "string",
        "exceptional_delta": "string"
    }}
}}
"""
        return prompt
    
    def _extract_repo_info(self, analysis: Dict) -> Dict:
        """Extract key repository information for the prompt"""
        repo_info = {
            'structure': {},
            'dependencies': {},
            'documentation': {},
            'testing': {},
            'code_quality': {},
            'production_readiness': {}
        }
        
        # Structure
        structure = analysis.get('structure', {})
        repo_info['structure'] = {
            'key_directories': structure.get('key_directories', {}),
            'total_directories': len(structure) - 1 if '/' in structure else len(structure)
        }
        
        # Dependencies
        deps = analysis.get('dependencies', {})
        repo_info['dependencies'] = {
            'python_count': len(deps.get('python', [])),
            'node_count': len(deps.get('node', [])),
            'top_python': deps.get('python', [])[:5],
            'top_node': deps.get('node', [])[:5]
        }
        
        # Documentation
        docs = analysis.get('documentation', {})
        repo_info['documentation'] = {
            'has_readme': docs.get('has_readme', False),
            'has_setup_instructions': docs.get('has_setup_instructions', False),
            'has_examples': docs.get('has_examples', False),
            'has_api_docs': docs.get('has_api_docs', False)
        }
        
        # Testing
        tests = analysis.get('tests', {})
        repo_info['testing'] = {
            'has_tests': tests.get('has_test_directory', False),
            'test_file_count': len(tests.get('test_files', []))
        }
        
        # Code Quality
        quality = analysis.get('code_quality', {})
        repo_info['code_quality'] = {
            'has_linting': quality.get('has_linting', False),
            'has_error_handling': quality.get('has_error_handling', False)
        }
        
        # Production Readiness
        repo_info['production_readiness'] = {
            'has_docker': analysis.get('docker', {}).get('has_dockerfile', False),
            'has_ci_cd': analysis.get('ci_cd', {}).get('has_ci', False)
        }
        
        return repo_info
    
    def _parse_gemini_response(self, response_text: str, evaluation: Dict) -> Dict:
        """Parse Gemini response and extract structured data"""
        try:
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate and enhance with evaluation data
                final_score = evaluation.get('final_score', 0)
                
                # Ensure benchmarks are calculated
                if 'benchmarks' not in result:
                    result['benchmarks'] = self._calculate_benchmarks(final_score)
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            # Return fallback
            return {
                'error': f"Failed to parse Gemini response: {str(e)}",
                'strengths': [],
                'weaknesses': [],
                'recommendation': {
                    'type': 'Manual Review Required',
                    'justification': 'AI analysis failed to parse',
                    'suggested_improvements': 'N/A'
                },
                'benchmarks': self._calculate_benchmarks(evaluation.get('final_score', 0))
            }
    
    def _calculate_benchmarks(self, final_score: int) -> Dict:
        """Calculate industry benchmarks"""
        benchmarks = {
            'intern_level': 60,
            'entry_level': 75,
            'strong_hire': 85,
            'exceptional': 90
        }
        
        result = {}
        
        for level, threshold in benchmarks.items():
            if final_score >= threshold + 5:
                result[level] = "Exceeds"
            elif final_score >= threshold:
                result[level] = "Meets"
            else:
                result[level] = "Below"
            
            # Calculate delta
            delta = final_score - threshold
            result[f"{level}_delta"] = f"+{delta}" if delta >= 0 else f"{delta}"
        
        return result
    
    def _analyze_rules_based(self, analysis: Dict, evaluation: Dict, challenge: Dict) -> Dict:
        """Fallback rule-based analysis"""
        
        final_score = evaluation.get('final_score', 0)
        
        # Basic strengths/weaknesses based on analysis
        strengths = []
        weaknesses = []
        
        # Check documentation
        docs = analysis.get('documentation', {})
        if docs.get('has_readme', False):
            strengths.append({
                'title': 'Good Documentation',
                'evidence': 'README file present with setup instructions',
                'impact': 'Makes the project accessible and well-documented'
            })
        else:
            weaknesses.append({
                'title': 'Missing Documentation',
                'evidence': 'No README file found',
                'impact': 'Project is difficult to understand and use'
            })
        
        # Check testing
        tests = analysis.get('tests', {})
        if tests.get('has_test_directory', False):
            strengths.append({
                'title': 'Test Suite Present',
                'evidence': f'{len(tests.get("test_files", []))} test files found',
                'impact': 'Demonstrates quality assurance mindset'
            })
        else:
            weaknesses.append({
                'title': 'Insufficient Testing',
                'evidence': 'No test directory or minimal test files',
                'impact': 'Reduces code reliability and maintainability'
            })
        
        # Check production readiness
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            strengths.append({
                'title': 'Containerization Ready',
                'evidence': 'Dockerfile present',
                'impact': 'Supports production deployment'
            })
        
        # Generate recommendation based on score
        if final_score >= 85:
            recommendation_type = "Strong Hire"
            justification = f"Excellent score of {final_score}/115. Demonstrates strong technical skills and understanding of challenge requirements."
        elif final_score >= 75:
            recommendation_type = "Hire as Intern"
            justification = f"Good score of {final_score}/115. Shows solid technical foundation suitable for internship."
        elif final_score >= 60:
            recommendation_type = "Consider for Internship"
            justification = f"Fair score of {final_score}/115. Has potential but needs improvement in key areas."
        else:
            recommendation_type = "Do Not Hire"
            justification = f"Score of {final_score}/115 is below minimum standards for internship."
        
        return {
            'strengths': strengths[:3],
            'weaknesses': weaknesses[:3],
            'recommendation': {
                'type': recommendation_type,
                'justification': justification,
                'suggested_improvements': 'Focus on documentation, testing, and production readiness.'
            },
            'benchmarks': self._calculate_benchmarks(final_score),
            'analysis_method': 'rule_based_fallback'
        }