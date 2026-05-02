"""
Scoring Engine - Calculate challenge-specific scores with experience adjustments.

Contains HACKATHON_CRITERIA and CHALLENGE_CRITERIA dictionaries,
and implements calculate_scores() function that applies component scoring,
challenge-specific mappings, and experience-level adjustments.
"""

from typing import Dict, Tuple

# Hackathon-style evaluation criteria (generic)
HACKATHON_CRITERIA = {
    'hackathon_general': {
        'code_quality': 25,
        'innovation': 25,
        'completeness': 25,
        'documentation': 15,
        'presentation': 10,
        'bonus_max': 10,
        'required_tech': [],
        'bonus_tech': []
    }
}

# Challenge-specific criteria (matches competition-analyser real_analyzer.py)
CHALLENGE_CRITERIA = {
    'challenge_023': {  # AI Agents Builder System
        'multi_modal_implementation': 60,
        'functionality_results': 25,
        'innovation_practicality': 15,
        'bonus_max': 15,
        'required_tech': ['python', 'opencv', 'llm', 'ocr', 'multi-modal'],
        'bonus_tech': ['langgraph', 'crewai', 'fastapi', 'qdrant', 'yolo']
    },
    'challenge_024': {  # AI Healthcare Agent System
        'technical_implementation': 60,
        'functionality_results': 25,
        'innovation_practices': 15,
        'bonus_max': 15,
        'required_tech': ['python', 'rag', 'ai agents', 'vector db', 'aws'],
        'bonus_tech': ['langchain', 'langgraph', 'crewai', 'docker', 'fastapi']
    },
    'challenge_025': {  # Healthcare Analytics
        'technical_implementation': 60,
        'functionality_results': 25,
        'innovation_practices': 15,
        'bonus_max': 15,
        'required_tech': ['python', 'etl', 'postgresql', 'aws'],
        'bonus_tech': ['airflow', 'docker', 'pyspark', 'redis']
    },
    'challenge_026': {  # AI Healthcare Platform
        'technical_implementation': 60,
        'functionality_results': 25,
        'innovation_practices': 15,
        'bonus_max': 15,
        'required_tech': ['react', 'django', 'postgresql', 'ai/ml'],
        'bonus_tech': ['next.js', 'docker', 'aws', 'celery', 'redis']
    },
    'challenge_027': {  # Enterprise Platform
        'technical_implementation': 60,
        'functionality_results': 25,
        'innovation_practices': 15,
        'bonus_max': 15,
        'required_tech': ['react', 'django', 'postgresql', 'task queue'],
        'bonus_tech': ['next.js', 'celery', 'redis', 'docker', 'aws']
    }
}

# Experience level configurations (from experience_adaptor.py)
EXPERIENCE_CONFIGS = {
    '1st_year': {
        'multiplier': 1.15,
        'expectation_base': 55,
        'excellent_threshold': 75,
    },
    '2nd_year': {
        'multiplier': 1.10,
        'expectation_base': 60,
        'excellent_threshold': 78,
    },
    '3rd_year': {
        'multiplier': 1.05,
        'expectation_base': 65,
        'excellent_threshold': 80,
    },
    '4th_year': {
        'multiplier': 1.00,
        'expectation_base': 70,
        'excellent_threshold': 83,
    },
    'fresher': {
        'multiplier': 0.95,
        'expectation_base': 68,
        'excellent_threshold': 80,
    },
    'experienced_0_2': {
        'multiplier': 0.85,
        'expectation_base': 75,
        'excellent_threshold': 86,
    },
    'senior': {
        'multiplier': 0.75,
        'expectation_base': 82,
        'excellent_threshold': 92,
    },
    'industry': {
        'multiplier': 0.88,
        'expectation_base': 75,
        'excellent_threshold': 88,
    },
    'beginner': {
        'multiplier': 1.10,
        'expectation_base': 55,
        'excellent_threshold': 75,
    },
    'intermediate': {
        'multiplier': 0.95,
        'expectation_base': 70,
        'excellent_threshold': 82,
    },
    'advanced': {
        'multiplier': 0.80,
        'expectation_base': 85,
        'excellent_threshold': 92,
    }
}


def calculate_scores(
    analysis_dict: Dict,
    challenge_id: str = None,
    experience_level: str = 'intermediate',
    hackathon_id: str = None,
    hackathon_db_data: Dict = None
) -> Tuple[Dict, Dict, Dict]:
    """
    Calculate component and category scores for a repository.
    
    Supports both hardcoded challenge criteria and dynamic hackathon criteria from MongoDB.
    
    Args:
        analysis_dict: Full analysis dictionary from all scanners containing:
            - file_scanner_results
            - tech_detector_results
            - code_quality_results
            - readme_analyzer_results
            - commit_analyzer_results
        challenge_id: Challenge identifier (e.g., 'challenge_023') - optional, preferred for predefined challenges
        experience_level: Experience level for adjustment (default: 'intermediate')
        hackathon_id: Hackathon identifier (e.g., 'memory-over-models-2025') - optional
        hackathon_db_data: Hackathon data from MongoDB with keys:
            - technologies: List[str] of required technologies
            - evaluation: str description or criteria JSON
            - bonusTech: List[str] of bonus technologies (optional)
            Falls back to hardcoded HACKATHON_CRITERIA if not provided
        
    Returns:
        Tuple of (component_scores, category_scores, metadata)
        - component_scores: Dict with individual metric scores (0-100)
        - category_scores: Dict with challenge-specific category scores
        - metadata: Dict with adjustment details
    """
    
    # Determine which criteria to use
    criteria = None
    criteria_source = None
    
    # 1. First check if challenge_id matches a predefined challenge
    if challenge_id and challenge_id in CHALLENGE_CRITERIA:
        criteria = CHALLENGE_CRITERIA[challenge_id]
        criteria_source = 'challenge'
    
    # 2. Check if hackathon_id matches hardcoded hackathon criteria
    elif hackathon_id and hackathon_id in HACKATHON_CRITERIA:
        criteria = HACKATHON_CRITERIA[hackathon_id]
        criteria_source = 'hackathon_hardcoded'
    
    # 3. Try to build criteria from MongoDB hackathon_db_data
    elif hackathon_db_data:
        try:
            criteria = _build_criteria_from_db(hackathon_db_data)
            criteria_source = 'hackathon_dynamic'
        except Exception as e:
            # Fall back to generic if parsing fails
            criteria = HACKATHON_CRITERIA.get('hackathon_general', {
                'code_quality': 25,
                'innovation': 25,
                'completeness': 25,
                'documentation': 15,
                'presentation': 10,
                'bonus_max': 10,
                'required_tech': [],
                'bonus_tech': []
            })
            criteria_source = 'fallback_generic'
    
    # 4. Fall back to generic criteria
    else:
        criteria = HACKATHON_CRITERIA.get('hackathon_general', {
            'code_quality': 25,
            'innovation': 25,
            'completeness': 25,
            'documentation': 15,
            'presentation': 10,
            'bonus_max': 10,
            'required_tech': [],
            'bonus_tech': []
        })
        criteria_source = 'fallback_default'
    
    # Use challenge_id if provided, else hackathon_id, else generic
    scoring_id = challenge_id or hackathon_id or 'generic'
    
    # Extract sub-analyses from analysis_dict
    file_scan = analysis_dict.get('file_scanner', {})
    tech_stack = analysis_dict.get('technologies', {})
    code_quality = analysis_dict.get('code_quality', {})
    readme = analysis_dict.get('readme', {})
    commits = analysis_dict.get('commits', {})
    
    # Calculate component scores
    component_scores = {
        'code_quality': code_quality.get('overall_quality_score', 50),
        'tech_match': _calculate_tech_match(tech_stack, criteria),
        'completeness': _calculate_completeness(file_scan, code_quality),
        'documentation': readme.get('quality_score', 0) * 10,  # Scale 0-10 to 0-100
        'activity': _calculate_activity_score(commits),
        'architecture': _calculate_architecture_score(file_scan, code_quality),
        'testing': code_quality.get('docstring_coverage', 0) * 0.5 +  # Proxy for testing
                   code_quality.get('type_hint_coverage', 0) * 0.5
    }
    
    # Normalize component scores to 0-100
    for key in component_scores:
        component_scores[key] = min(max(component_scores[key], 0), 100)
    
    # Calculate category scores based on challenge criteria
    category_scores = _map_to_challenge_categories(
        component_scores,
        criteria,
        challenge_id
    )
    
    # Apply experience-level adjustment
    adjusted_scores, adjustments = apply_experience_adjustment(
        category_scores,
        experience_level,
        criteria
    )
    
    # Calculate final score
    base_total = sum(category_scores.values())
    adjusted_total = sum(adjusted_scores.values())
    
    metadata = {
        'scoring_id': scoring_id,
        'criteria_source': criteria_source,
        'challenge_id': challenge_id,
        'hackathon_id': hackathon_id,
        'experience_level': experience_level,
        'experience_multiplier': EXPERIENCE_CONFIGS.get(experience_level, {}).get('multiplier', 1.0),
        'base_score': base_total,
        'adjusted_score': adjusted_total,
        'adjustment_details': adjustments
    }
    
    return component_scores, adjusted_scores, metadata


def _calculate_tech_match(tech_stack: Dict, criteria: Dict) -> float:
    """Calculate technology stack match score (0-100)."""
    if not criteria.get('required_tech'):
        return 75
    
    required_tech = set(t.lower() for t in criteria.get('required_tech', []))
    detected_tech = set()
    
    # Flatten all detected technologies
    for tech_list in tech_stack.values():
        for tech in tech_list:
            detected_tech.add(tech.lower())
    
    # Calculate match percentage
    matches = 0
    for req in required_tech:
        # Check for exact match or partial match
        for det in detected_tech:
            if req in det or det in req:
                matches += 1
                break
    
    if not required_tech:
        return 75
    
    match_percentage = (matches / len(required_tech)) * 100
    
    # Add bonus for exceeding technologies
    bonus_tech = set(t.lower() for t in criteria.get('bonus_tech', []))
    bonus_matches = len(detected_tech & bonus_tech)
    bonus_score = min(bonus_matches * 5, 15)  # Max 15 points bonus
    
    return min(match_percentage + (bonus_score / 2), 100)


def _calculate_completeness(file_scan: Dict, code_quality: Dict) -> float:
    """Calculate project completeness score (0-100)."""
    score = 50
    
    # File count indicates scope
    total_files = file_scan.get('total_files', 0)
    if total_files > 50:
        score += 20
    elif total_files > 20:
        score += 15
    elif total_files > 10:
        score += 10
    
    # Code lines indicate implementation depth
    total_lines = file_scan.get('total_lines', 0)
    if total_lines > 1000:
        score += 15
    elif total_lines > 500:
        score += 10
    elif total_lines > 100:
        score += 5
    
    # Has tests/docs indicates maturity
    key_dirs = file_scan.get('key_directories', [])
    if 'tests' in key_dirs:
        score += 10
    if 'docs' in key_dirs:
        score += 5
    
    # Code quality indicates functionality
    if code_quality.get('total_functions', 0) > 20:
        score += 5
    
    return min(score, 100)


def _calculate_activity_score(commits: Dict) -> float:
    """Calculate project activity/maturity score (0-100)."""
    score = 50
    
    total_commits = commits.get('total_commits', 0)
    if total_commits > 50:
        score += 25
    elif total_commits > 20:
        score += 15
    elif total_commits > 5:
        score += 10
    
    duration_days = commits.get('project_duration_days', 1)
    if duration_days > 90:
        score += 15
    elif duration_days > 30:
        score += 10
    elif duration_days > 7:
        score += 5
    
    commits_per_day = commits.get('commits_per_day', 0)
    if commits_per_day > 0.5:
        score += 10
    elif commits_per_day > 0.2:
        score += 5
    
    return min(score, 100)


def _calculate_architecture_score(file_scan: Dict, code_quality: Dict) -> float:
    """Calculate project architecture score (0-100)."""
    score = 50
    
    key_dirs = file_scan.get('key_directories', [])
    score += len(key_dirs) * 5  # Points for organized directories
    
    patterns = code_quality.get('design_patterns', [])
    if patterns:
        score += min(len(patterns) * 5, 25)
    
    total_classes = code_quality.get('total_classes', 0)
    if total_classes > 10:
        score += 15
    elif total_classes > 5:
        score += 10
    
    return min(score, 100)


def _build_criteria_from_db(hackathon_db_data: Dict) -> Dict:
    """
    Build criteria dictionary from MongoDB hackathon data.
    
    Args:
        hackathon_db_data: Dictionary from MongoDB with keys:
            - technologies: List[str] of required technologies
            - evaluation: str description or JSON with criteria
            - bonusTech: List[str] of bonus technologies (optional)
            
    Returns:
        Criteria dictionary compatible with scoring functions
        
    Raises:
        ValueError: If required fields are missing
    """
    if not hackathon_db_data:
        raise ValueError("hackathon_db_data cannot be None")
    
    # Extract required fields
    required_tech = hackathon_db_data.get('technologies', [])
    if isinstance(required_tech, str):
        required_tech = [t.strip() for t in required_tech.split(',')]
    elif not isinstance(required_tech, list):
        required_tech = []
    
    bonus_tech = hackathon_db_data.get('bonusTech', [])
    if isinstance(bonus_tech, str):
        bonus_tech = [t.strip() for t in bonus_tech.split(',')]
    elif not isinstance(bonus_tech, list):
        bonus_tech = []
    
    # Parse evaluation string to extract weights/criteria
    evaluation_str = hackathon_db_data.get('evaluation', '')
    weights = _parse_evaluation_criteria(evaluation_str)
    
    # Build criteria dictionary
    criteria = {
        'bonus_max': 10,
        'required_tech': required_tech,
        'bonus_tech': bonus_tech
    }
    
    # Add parsed weights/criteria
    criteria.update(weights)
    
    # Ensure there are category weights
    if not any(isinstance(v, (int, float)) for k, v in criteria.items() if k not in ['bonus_max', 'required_tech', 'bonus_tech']):
        # Fallback to equal weights if no numeric criteria found
        default_categories = ['code_quality', 'innovation', 'completeness', 'documentation']
        weight_per_category = 100 / len(default_categories)
        for category in default_categories:
            criteria[category] = weight_per_category
    
    return criteria


def _parse_evaluation_criteria(evaluation_str: str) -> Dict:
    """
    Parse evaluation string to extract category weights.
    
    Supports formats:
    - JSON: '{"code_quality": 30, "innovation": 25, ...}'
    - Key-value pairs: 'code_quality: 30, innovation: 25, ...'
    - Simple categories: 'code_quality, innovation, completeness'
    
    Args:
        evaluation_str: String description from MongoDB
        
    Returns:
        Dictionary with category names as keys and weights as values
        If parsing fails, returns empty dict (fallback to equal weights)
    """
    if not evaluation_str or not isinstance(evaluation_str, str):
        return {}
    
    import json
    import re
    
    # Try JSON parsing first
    try:
        data = json.loads(evaluation_str)
        if isinstance(data, dict):
            # Extract only numeric values
            return {k: v for k, v in data.items() if isinstance(v, (int, float))}
    except json.JSONDecodeError:
        pass
    
    # Try key-value pairs with colons
    weights = {}
    try:
        # Pattern: "category_name: weight, another_category: weight"
        pairs = evaluation_str.split(',')
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                try:
                    weight = float(value.strip())
                    weights[key] = weight
                except ValueError:
                    pass
        
        if weights:
            return weights
    except Exception:
        pass
    
    # Try to extract key-value patterns with regex
    try:
        # Pattern: "category_name: 30"
        pattern = r'(\w+(?:_\w+)*)\s*[:=]\s*(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, evaluation_str)
        
        if matches:
            for key, value in matches:
                weights[key.lower()] = float(value)
        
        if weights:
            return weights
    except Exception:
        pass
    
    # Try simple word extraction (e.g., "code quality, innovation, completeness")
    try:
        # Split by commas or "and"
        categories = re.split(r',\s+|and\s+', evaluation_str.lower())
        
        # Clean up category names
        cleaned = []
        for cat in categories:
            # Remove quotes, parentheses, etc.
            cat = re.sub(r'[^\w\s]', '', cat).strip().replace(' ', '_')
            if cat and len(cat) > 2:  # Only keep meaningful words
                cleaned.append(cat)
        
        if cleaned:
            # Equal weights for all categories
            weight = 100 / len(cleaned)
            return {cat: weight for cat in cleaned}
    except Exception:
        pass
    
    # Return empty dict as fallback (will use default weights)
    return {}


def _map_to_challenge_categories(
    component_scores: Dict,
    criteria: Dict,
    challenge_id: str
) -> Dict:
    """
    Map component scores to challenge-specific categories.
    
    Supports both predefined challenge criteria and dynamically built hackathon criteria.
    """
    category_scores = {}
    
    # Get category names and weights from criteria (excluding special keys)
    special_keys = {'bonus_max', 'required_tech', 'bonus_tech'}
    category_items = {k: v for k, v in criteria.items() 
                      if isinstance(v, (int, float)) and k not in special_keys}
    
    if not category_items:
        # No numeric categories found - shouldn't happen but handle gracefully
        return {}
    
    total_weight = sum(category_items.values())
    if total_weight == 0:
        total_weight = 100
    
    # Map each category to a component score
    for category_name, weight in category_items.items():
        component_key = _match_category_to_component(category_name, component_scores)
        base_score = component_scores.get(component_key, 50)
        weighted_score = (base_score / 100) * weight
        category_scores[category_name] = weighted_score
    
    return category_scores


def _match_category_to_component(category_name: str, available_components: Dict) -> str:
    """
    Match a category name to the most appropriate component score.
    
    Args:
        category_name: Name of the criterion/category
        available_components: Dict of available component scores
        
    Returns:
        Component key to use for scoring
    """
    category_lower = category_name.lower()
    
    # Direct component matches
    if category_lower in available_components:
        return category_lower
    
    # Keyword-based matching
    if any(word in category_lower for word in ['quality', 'code', 'implementation', 'technical']):
        return 'code_quality'
    elif any(word in category_lower for word in ['innovation', 'creative', 'novel']):
        return 'architecture'
    elif any(word in category_lower for word in ['complete', 'functionality', 'feature']):
        return 'completeness'
    elif any(word in category_lower for word in ['doc', 'readme', 'description']):
        return 'documentation'
    elif any(word in category_lower for word in ['activity', 'commit', 'progress', 'maturity']):
        return 'activity'
    elif any(word in category_lower for word in ['test', 'coverage', 'quality']):
        return 'testing'
    elif any(word in category_lower for word in ['design', 'architecture', 'structure']):
        return 'architecture'
    
    # Default fallback to code_quality
    return 'code_quality'


def apply_experience_adjustment(
    category_scores: Dict,
    experience_level: str,
    criteria: Dict
) -> Tuple[Dict, Dict]:
    """
    Apply experience-level adjustment to scores.
    
    Higher experience = stricter grading (multiplier < 1)
    Lower experience = more lenient (multiplier > 1)
    
    Args:
        category_scores: Dict of category scores
        experience_level: Experience level identifier
        criteria: Challenge criteria dict
        
    Returns:
        Tuple of (adjusted_scores, adjustment_details)
    """
    config = EXPERIENCE_CONFIGS.get(experience_level, EXPERIENCE_CONFIGS['intermediate'])
    multiplier = config['multiplier']
    
    adjusted_scores = {}
    for category, score in category_scores.items():
        adjusted = score * multiplier
        adjusted_scores[category] = min(adjusted, 100)
    
    adjustments = {
        'multiplier': multiplier,
        'expectation_base': config['expectation_base'],
        'excellent_threshold': config['excellent_threshold']
    }
    
    return adjusted_scores, adjustments
