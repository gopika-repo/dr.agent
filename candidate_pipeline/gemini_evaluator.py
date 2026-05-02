"""
Gemini Evaluator - Call Google Generative AI for structured evaluation.

Sends full analysis dict and sampled file contents to Gemini API,
returns structured JSON with strengths, weaknesses, recommendations,
and benchmark comparisons.
"""

import os
import json
from typing import Dict, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None


# Default model (supports fallback to other models if needed)
DEFAULT_MODEL = "gemini-2.0-flash"
SUPPORTED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "gemini-2.5-pro",
    "gemini-2.5-flash"
]


def evaluate_with_gemini(
    analysis_dict: Dict,
    challenge_id: str,
    gemini_api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
    max_file_samples: int = 5
) -> Dict:
    """
    Evaluate repository analysis using Google Generative AI (Gemini).
    
    Args:
        analysis_dict: Full analysis dictionary from all scanners containing:
            - component_scores
            - category_scores
            - code_quality results
            - tech_detector results
            - readme_analyzer results
            - commits results
        challenge_id: Challenge identifier (e.g., 'challenge_023')
        gemini_api_key: Optional Gemini API key. If not provided, reads from
                       environment variable GEMINI_API_KEY
        model_name: Gemini model to use (default: gemini-2.0-flash)
        max_file_samples: Maximum number of files to include in prompt
        
    Returns:
        Dictionary with Gemini evaluation:
        {
            'strengths': [
                {'title': str, 'evidence': str, 'impact': str}
            ],
            'weaknesses': [
                {'title': str, 'evidence': str, 'impact': str}
            ],
            'recommendation': {
                'type': str,
                'justification': str,
                'suggested_improvements': str
            },
            'benchmarks': {
                'intern_level': str,
                'entry_level': str,
                'strong_hire': str,
                'exceptional': str
            },
            'error': str (if evaluation failed)
        }
    """
    
    # Check if google.generativeai is available
    if genai is None:
        return {
            'error': 'google-generativeai package not installed. Install with: pip install google-generativeai'
        }
    
    # Get API key from parameter or environment
    api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {
            'error': 'GEMINI_API_KEY not provided and not set in environment variables'
        }
    
    # Validate model
    if model_name not in SUPPORTED_MODELS:
        model_name = DEFAULT_MODEL
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Prepare prompt
        prompt = _create_evaluation_prompt(analysis_dict, challenge_id)
        
        # Call Gemini
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,  # Deterministic
                'top_p': 0.9,
                'top_k': 40,
                'max_output_tokens': 4000,
            },
            request_options={
                'timeout': 60,
            }
        )
        
        # Extract response text
        response_text = ''
        if response.candidates and len(response.candidates) > 0:
            parts = response.candidates[0].content.parts
            response_text = "".join(
                part.text for part in parts if hasattr(part, 'text')
            )
        
        if not response_text:
            return {'error': 'Gemini API returned empty response'}
        
        # Parse response
        return _parse_gemini_response(response_text, analysis_dict)
        
    except Exception as e:
        return {'error': f'Gemini API error: {str(e)}'}


def _create_evaluation_prompt(analysis_dict: Dict, challenge_id: str) -> str:
    """Create detailed prompt for Gemini evaluation."""
    
    # Extract key information
    component_scores = analysis_dict.get('component_scores', {})
    category_scores = analysis_dict.get('category_scores', {})
    code_quality = analysis_dict.get('code_quality', {})
    technologies = analysis_dict.get('technologies', {})
    readme = analysis_dict.get('readme', {})
    commits = analysis_dict.get('commits', {})
    file_scan = analysis_dict.get('file_scanner', {})
    
    # Challenge descriptions
    challenge_descriptions = {
        'challenge_023': 'AI Agents Builder System - Build an AI-powered system using multi-modal capabilities, LLMs, and agent frameworks',
        'challenge_024': 'AI Healthcare Agent System - Develop healthcare-focused AI agents with RAG capabilities and vector databases',
        'challenge_025': 'Healthcare Analytics - Create ETL pipelines for healthcare data processing and analytics',
        'challenge_026': 'AI Healthcare Platform - Build a full-stack platform combining React frontend, Django backend, and AI/ML',
        'challenge_027': 'Enterprise Platform - Develop an enterprise-grade platform with React, Django, PostgreSQL, and task queues'
    }
    
    challenge_desc = challenge_descriptions.get(
        challenge_id,
        'Coding Challenge - Build a solution meeting specified requirements'
    )
    
    # Build prompt
    prompt = f"""You are an expert technical hiring manager evaluating a GitHub repository submission for a coding challenge.

CHALLENGE: {challenge_id}
{challenge_desc}

REPOSITORY ANALYSIS SUMMARY:
=========================================

METRICS:
- Total Files: {file_scan.get('total_files', 'N/A')}
- Total Lines of Code: {file_scan.get('total_lines', 'N/A')}
- Commits: {commits.get('total_commits', 'N/A')} (over {commits.get('project_duration_days', 'N/A')} days)
- Key Directories: {', '.join(file_scan.get('key_directories', [])) or 'None identified'}

CODE QUALITY METRICS:
- Overall Quality Score: {code_quality.get('overall_quality_score', 'N/A')}/100
- Error Handling: {code_quality.get('error_handling_score', 'N/A')}%
- Documentation Coverage: {code_quality.get('docstring_coverage', 'N/A')}%
- Type Hints: {code_quality.get('type_hint_coverage', 'N/A')}%
- Design Patterns: {', '.join(code_quality.get('design_patterns', [])) or 'None identified'}
- Functions: {code_quality.get('total_functions', 'N/A')}
- Classes: {code_quality.get('total_classes', 'N/A')}

TECHNOLOGY STACK:
- AI/ML: {', '.join(technologies.get('ai_ml', [])) or 'None'}
- Frameworks: {', '.join(technologies.get('frameworks', [])) or 'None'}
- Databases: {', '.join(technologies.get('databases', [])) or 'None'}
- DevOps: {', '.join(technologies.get('devops', [])) or 'None'}
- Testing: {', '.join(technologies.get('testing', [])) or 'None'}

README ANALYSIS:
- Exists: {readme.get('exists', False)}
- Quality Score: {readme.get('quality_score', 'N/A')}/10
- Sections: {', '.join(readme.get('sections_found', [])) or 'None'}
- Word Count: {readme.get('word_count', 0)}
- Has Examples: {readme.get('has_examples', False)}
- Has Installation: {readme.get('has_installation', False)}

SCORING BREAKDOWN:
- Code Quality Component: {component_scores.get('code_quality', 'N/A')}/100
- Tech Stack Match: {component_scores.get('tech_match', 'N/A')}/100
- Completeness: {component_scores.get('completeness', 'N/A')}/100
- Documentation: {component_scores.get('documentation', 'N/A')}/100
- Architecture: {component_scores.get('architecture', 'N/A')}/100

YOUR TASK:
Based on this analysis, provide a comprehensive technical evaluation in valid JSON format.

IMPORTANT REQUIREMENTS:
1. MUST return ONLY valid JSON, no other text before or after
2. MUST include all required fields exactly as specified below
3. Strengths/weaknesses should be specific and evidence-based
4. Recommendation should consider the challenge requirements
5. Benchmark comparisons should be realistic

RETURN THIS EXACT JSON STRUCTURE (fill in all fields):
{{
    "strengths": [
        {{
            "title": "Clear title of strength (e.g., 'Excellent Error Handling')",
            "evidence": "Specific evidence from analysis (e.g., 'Error handling score: 92%, with try-catch blocks in critical sections')",
            "impact": "Why this matters for the challenge (e.g., 'Ensures robust, production-ready code')"
        }}
    ],
    "weaknesses": [
        {{
            "title": "Clear title of weakness (e.g., 'Limited Testing Infrastructure')",
            "evidence": "Specific evidence from analysis (e.g., 'No test files found, documentation coverage only 15%')",
            "impact": "Why this matters (e.g., 'Increases risk of bugs in production')"
        }}
    ],
    "recommendation": {{
        "type": "Choose ONE: 'Hire as Intern' / 'Consider for Internship' / 'Do Not Hire' / 'Strong Hire'",
        "justification": "Detailed reasoning based on scores and challenge fit (2-3 sentences)",
        "suggested_improvements": "Top 3 specific improvements needed (as comma-separated list)"
    }},
    "benchmarks": {{
        "intern_level": "Choose: 'Exceeds' / 'Meets' / 'Below' (benchmark: 60/100)",
        "entry_level": "Choose: 'Exceeds' / 'Meets' / 'Below' (benchmark: 75/100)",
        "strong_hire": "Choose: 'Exceeds' / 'Meets' / 'Below' (benchmark: 85/100)",
        "exceptional": "Choose: 'Exceeds' / 'Meets' / 'Below' (benchmark: 90/100)"
    }}
}}

Be fair, specific, and constructive in your evaluation."""
    
    return prompt


def _parse_gemini_response(response_text: str, analysis_dict: Dict) -> Dict:
    """
    Parse Gemini's JSON response.
    
    Args:
        response_text: Raw response text from Gemini
        analysis_dict: Original analysis dict (for fallback)
        
    Returns:
        Parsed evaluation dict
    """
    try:
        # Try to extract JSON from response
        # Sometimes Gemini wraps JSON in markdown code blocks
        if '```json' in response_text:
            json_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_text = response_text.split('```')[1].split('```')[0].strip()
        else:
            json_text = response_text
        
        # Parse JSON
        result = json.loads(json_text)
        
        # Validate structure
        required_keys = ['strengths', 'weaknesses', 'recommendation', 'benchmarks']
        for key in required_keys:
            if key not in result:
                result[key] = {}
        
        return result
        
    except json.JSONDecodeError:
        # Return structured fallback response
        return _generate_fallback_evaluation(analysis_dict)
    except Exception as e:
        return {'error': f'Failed to parse Gemini response: {str(e)}'}


def _generate_fallback_evaluation(analysis_dict: Dict) -> Dict:
    """
    Generate a fallback evaluation based on analysis scores.
    
    Used when Gemini API fails or returns unparseable response.
    """
    component_scores = analysis_dict.get('component_scores', {})
    code_quality = analysis_dict.get('code_quality', {})
    
    overall_quality = component_scores.get('code_quality', 50)
    
    strengths = []
    weaknesses = []
    
    # Generate strengths based on scores
    if component_scores.get('code_quality', 0) > 70:
        strengths.append({
            'title': 'Strong Code Quality',
            'evidence': f'Code quality score: {component_scores.get("code_quality", 0)}/100',
            'impact': 'Indicates well-structured, maintainable codebase'
        })
    
    if component_scores.get('documentation', 0) > 70:
        strengths.append({
            'title': 'Excellent Documentation',
            'evidence': f'Documentation score: {component_scores.get("documentation", 0)}/100',
            'impact': 'Makes code understandable and maintainable'
        })
    
    if component_scores.get('tech_match', 0) > 80:
        strengths.append({
            'title': 'Strong Technology Alignment',
            'evidence': f'Tech match score: {component_scores.get("tech_match", 0)}/100',
            'impact': 'Uses appropriate technologies for the challenge'
        })
    
    # Generate weaknesses
    if component_scores.get('testing', 0) < 50:
        weaknesses.append({
            'title': 'Limited Testing Coverage',
            'evidence': f'Testing proxy score: {component_scores.get("testing", 0)}/100',
            'impact': 'May have undetected bugs'
        })
    
    if component_scores.get('documentation', 0) < 40:
        weaknesses.append({
            'title': 'Insufficient Documentation',
            'evidence': f'Documentation score: {component_scores.get("documentation", 0)}/100',
            'impact': 'Difficult for others to understand and maintain'
        })
    
    # Recommendation based on overall score
    if overall_quality > 85:
        rec_type = 'Strong Hire'
        justification = 'Repository demonstrates strong technical execution with excellent code quality and design.'
    elif overall_quality > 75:
        rec_type = 'Consider for Internship'
        justification = 'Repository shows solid implementation with room for improvement in testing and documentation.'
    elif overall_quality > 60:
        rec_type = 'Hire as Intern'
        justification = 'Repository demonstrates basic competence with clear areas for growth.'
    else:
        rec_type = 'Do Not Hire'
        justification = 'Repository does not meet minimum technical standards for the role.'
    
    return {
        'strengths': strengths or [{'title': 'Code Present', 'evidence': 'Repository has code', 'impact': 'Shows effort'}],
        'weaknesses': weaknesses or [{'title': 'Areas for Improvement', 'evidence': 'Code quality below average', 'impact': 'Needs enhancement'}],
        'recommendation': {
            'type': rec_type,
            'justification': justification,
            'suggested_improvements': 'Improve documentation, add tests, refactor complex functions'
        },
        'benchmarks': {
            'intern_level': 'Meets' if overall_quality > 60 else 'Below',
            'entry_level': 'Exceeds' if overall_quality > 85 else 'Meets' if overall_quality > 75 else 'Below',
            'strong_hire': 'Exceeds' if overall_quality > 90 else 'Meets' if overall_quality > 85 else 'Below',
            'exceptional': 'Below'
        },
        '_fallback': True
    }
