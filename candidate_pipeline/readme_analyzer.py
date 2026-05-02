"""
README Analyzer - Analyze README quality and completeness.

Checks for README existence, quality score (0-10 scale), sections present,
word count, and key sections (examples, installation, usage).
"""

import os
import re
from pathlib import Path
from typing import Dict, List


# README file name variations
README_FILENAMES = ['README.md', 'readme.md', 'README.rst', 'readme.rst', 'README.txt', 'readme.txt']

# Key sections to look for
KEY_SECTIONS = [
    ('installation', ['install', 'setup', 'getting started', 'prerequisites', 'requirements']),
    ('usage', ['usage', 'how to use', 'quickstart', 'quick start', 'examples', 'tutorial']),
    ('features', ['features', 'capabilities', 'what can it do']),
    ('api', ['api', 'endpoints', 'reference', 'documentation']),
    ('contributing', ['contribute', 'contributing', 'development', 'dev setup']),
    ('license', ['license', 'licensing']),
    ('examples', ['example', 'examples', 'sample', 'demo', 'demo code']),
    ('configuration', ['config', 'configuration', 'customize', 'settings'])
]


def analyze_readme(repo_path: str) -> Dict:
    """
    Analyze README quality in repository.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary containing README analysis:
        {
            'exists': bool,
            'quality_score': float (0-10),
            'sections_found': List[str],
            'word_count': int,
            'has_examples': bool,
            'has_installation': bool,
            'has_usage': bool,
            'has_badges': bool,
            'has_images': bool,
            'has_toc': bool,
            'filename': str (if exists)
        }
    """
    repo_root = Path(repo_path)
    
    result = {
        'exists': False,
        'quality_score': 0.0,
        'sections_found': [],
        'word_count': 0,
        'has_examples': False,
        'has_installation': False,
        'has_usage': False,
        'has_badges': False,
        'has_images': False,
        'has_toc': False,
        'filename': None,
        'headers': []
    }
    
    if not repo_root.exists():
        return result
    
    # Search for README file
    readme_path = None
    for readme_name in README_FILENAMES:
        candidate = repo_root / readme_name
        if candidate.exists():
            readme_path = candidate
            result['filename'] = readme_name
            break
    
    if not readme_path:
        return result
    
    try:
        with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result['exists'] = True
        
        # Basic metrics
        result['word_count'] = len(content.split())
        
        # Check for badges
        result['has_badges'] = '[![' in content or '[badge]' in content.lower()
        
        # Check for images
        result['has_images'] = bool(re.search(r'!\[.*?\]\(.*?\)', content))
        
        # Check for table of contents
        result['has_toc'] = bool(re.search(r'#{1,6}\s+(?:Table of Contents|Contents|TOC)', content, re.IGNORECASE))
        
        # Extract headers
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        result['headers'] = [h.strip() for h in headers]
        
        # Check for key sections
        content_lower = content.lower()
        for section, keywords in KEY_SECTIONS:
            for keyword in keywords:
                if keyword in content_lower:
                    if section not in result['sections_found']:
                        result['sections_found'].append(section)
                    break
        
        # Set specific flags
        result['has_examples'] = 'example' in result['sections_found']
        result['has_installation'] = 'installation' in result['sections_found']
        result['has_usage'] = 'usage' in result['sections_found']
        
        # Calculate quality score (0-10)
        quality_score = _calculate_quality_score(
            content=content,
            word_count=result['word_count'],
            has_headers=len(headers) > 0,
            has_badges=result['has_badges'],
            has_images=result['has_images'],
            has_toc=result['has_toc'],
            sections_found=result['sections_found']
        )
        
        result['quality_score'] = round(quality_score, 1)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def _calculate_quality_score(content: str, word_count: int, has_headers: bool,
                             has_badges: bool, has_images: bool, has_toc: bool,
                             sections_found: List[str]) -> float:
    """
    Calculate README quality score (0-10).
    
    Scoring criteria:
    - Word count: 50-200 words = 1 point
    - Headers/structure: 2+ headers = 1 point
    - Key sections: 3+ sections = 1 point, 5+ sections = 2 points
    - Examples: 1 point
    - Installation/Setup: 1 point
    - Usage: 1 point
    - Images: 1 point
    - Badges/Status: 1 point
    - Table of contents: 1 point
    - Code formatting: 1 point
    """
    score = 0.0
    
    # Word count (50-500 is good)
    if 50 <= word_count <= 500:
        score += 1
    elif 30 <= word_count < 50:
        score += 0.5
    elif word_count > 500:
        score += 0.8
    
    # Headers/structure
    if has_headers:
        score += 1
    
    # Key sections
    if len(sections_found) >= 5:
        score += 2
    elif len(sections_found) >= 3:
        score += 1
    elif len(sections_found) >= 1:
        score += 0.5
    
    # Specific important sections
    if 'examples' in sections_found or 'example' in sections_found:
        score += 0.5
    
    if 'installation' in sections_found:
        score += 0.5
    
    if 'usage' in sections_found:
        score += 0.5
    
    # Media
    if has_images:
        score += 0.5
    
    # Badges
    if has_badges:
        score += 0.5
    
    # Table of contents
    if has_toc:
        score += 0.5
    
    # Code formatting
    if '```' in content or '`' in content:
        score += 0.5
    
    # Links/references
    if re.search(r'\[.*?\]\(.*?\)', content):
        score += 0.3
    
    return min(score, 10.0)
