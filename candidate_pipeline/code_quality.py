"""
Code Quality Analyzer - Analyze code quality metrics.

Uses AST parsing for Python, regex analysis for other languages.
Extracts: error handling, docstrings, type hints, design patterns,
comment ratio, function/class counts, and complexity metrics.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import Counter


# Design patterns to detect
PATTERN_KEYWORDS = {
    'factory': ['factory', 'create_', 'builder'],
    'singleton': ['singleton', 'instance', 'get_instance'],
    'observer': ['observer', 'listener', 'subscribe', 'notify'],
    'decorator': ['@decorator', 'decorator', 'wrapper'],
    'strategy': ['strategy', 'algorithm', 'select_strategy'],
    'adapter': ['adapter', 'convert', 'transform'],
    'mvc': ['model', 'view', 'controller'],
    'repository': ['repository', 'repository_pattern', 'data_access']
}


def analyze_code_quality(repo_path: str) -> Dict:
    """
    Analyze code quality across repository.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary containing quality metrics:
        {
            'error_handling_score': float (0-100),
            'docstring_coverage': float (0-100),
            'type_hint_coverage': float (0-100),
            'design_patterns': List[str],
            'comment_ratio': float,
            'total_functions': int,
            'total_classes': int,
            'code_duplication_score': float (0-100),
            'overall_quality_score': float (0-100)
        }
    """
    repo_root = Path(repo_path)
    
    if not repo_root.exists():
        return {
            'error_handling_score': 0,
            'docstring_coverage': 0,
            'type_hint_coverage': 0,
            'design_patterns': [],
            'comment_ratio': 0,
            'total_functions': 0,
            'total_classes': 0,
            'code_duplication_score': 0,
            'overall_quality_score': 0,
            'error': f'Repository path does not exist: {repo_path}'
        }
    
    metrics = {
        'total_functions': 0,
        'total_classes': 0,
        'functions_with_docstrings': 0,
        'functions_with_type_hints': 0,
        'classes_with_docstrings': 0,
        'error_handling_instances': 0,
        'comment_lines': 0,
        'code_lines': 0,
        'detected_patterns': set(),
        'duplicate_fingerprints': Counter()
    }
    
    file_contents = []
    
    # Walk repository and analyze Python/JS/TS files
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {
            '.git', '.venv', 'venv', 'node_modules', '__pycache__',
            'dist', 'build'
        }]
        
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            if file_name.endswith('.py'):
                _analyze_python_file(file_path, metrics, file_contents)
            elif file_name.endswith(('.js', '.ts', '.jsx', '.tsx')):
                _analyze_js_file(file_path, metrics, file_contents)
            elif file_name.endswith(('.java', '.cpp', '.c', '.cs', '.go', '.rs')):
                _analyze_generic_file(file_path, metrics)
    
    # Calculate scores
    error_handling_score = _calculate_error_handling_score(metrics)
    docstring_coverage = _calculate_docstring_coverage(metrics)
    type_hint_coverage = _calculate_type_hint_coverage(metrics)
    comment_ratio = _calculate_comment_ratio(metrics)
    duplication_score = _calculate_duplication_score(metrics)
    
    # Overall quality score
    overall_score = (
        error_handling_score * 0.25 +
        docstring_coverage * 0.25 +
        type_hint_coverage * 0.20 +
        (100 - duplication_score) * 0.20 +
        comment_ratio * 0.10
    )
    
    return {
        'error_handling_score': round(error_handling_score, 1),
        'docstring_coverage': round(docstring_coverage, 1),
        'type_hint_coverage': round(type_hint_coverage, 1),
        'design_patterns': sorted(list(metrics['detected_patterns'])),
        'comment_ratio': round(comment_ratio, 1),
        'total_functions': metrics['total_functions'],
        'total_classes': metrics['total_classes'],
        'code_duplication_score': round(duplication_score, 1),
        'overall_quality_score': round(overall_score, 1)
    }


def _analyze_python_file(file_path: str, metrics: Dict, file_contents: List[str]) -> None:
    """Analyze Python file using AST parsing."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        file_contents.append(content)
        
        # Count lines and comments
        lines = content.split('\n')
        metrics['code_lines'] += len(lines)
        metrics['comment_lines'] += sum(1 for line in lines if line.strip().startswith('#'))
        
        # Walk AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics['total_functions'] += 1
                
                # Check for docstring
                if ast.get_docstring(node):
                    metrics['functions_with_docstrings'] += 1
                
                # Check for type hints
                if node.returns or any(arg.annotation for arg in node.args.args):
                    metrics['functions_with_type_hints'] += 1
                
                # Check for error handling in function
                for child in ast.walk(node):
                    if isinstance(child, (ast.Try, ast.ExceptHandler)):
                        metrics['error_handling_instances'] += 1
                        break
            
            elif isinstance(node, ast.ClassDef):
                metrics['total_classes'] += 1
                
                # Check for docstring
                if ast.get_docstring(node):
                    metrics['classes_with_docstrings'] += 1
            
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                metrics['error_handling_instances'] += 1
        
        # Detect design patterns
        content_lower = content.lower()
        for pattern, keywords in PATTERN_KEYWORDS.items():
            if any(keyword in content_lower for keyword in keywords):
                metrics['detected_patterns'].add(pattern)
        
        # Simple duplication detection
        _detect_duplication(content, metrics)
        
    except Exception:
        pass


def _analyze_js_file(file_path: str, metrics: Dict, file_contents: List[str]) -> None:
    """Analyze JavaScript/TypeScript file using regex."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_contents.append(content)
        
        # Count lines and comments
        lines = content.split('\n')
        metrics['code_lines'] += len(lines)
        metrics['comment_lines'] += len(re.findall(r'//.*$|/\*.*?\*/', content, re.MULTILINE))
        
        # Count functions
        function_count = len(re.findall(r'(?:function|async\s+function|\(\s*\)\s*=>|function\*)', content))
        metrics['total_functions'] += function_count
        
        # Count classes
        class_count = len(re.findall(r'class\s+\w+', content))
        metrics['total_classes'] += class_count
        
        # Check for JSDoc/comments
        docstring_count = len(re.findall(r'/\*\*.*?\*/', content, re.DOTALL))
        metrics['functions_with_docstrings'] += docstring_count
        
        # Check for TypeScript type hints
        type_hint_count = len(re.findall(r':\s*(?:string|number|boolean|any|unknown|Type|Interface)', content))
        metrics['functions_with_type_hints'] += min(type_hint_count // 5, function_count)
        
        # Check for error handling
        try_count = len(re.findall(r'try\s*{|catch\s*\(|finally\s*{', content))
        metrics['error_handling_instances'] += try_count
        
        # Detect design patterns
        content_lower = content.lower()
        for pattern, keywords in PATTERN_KEYWORDS.items():
            if any(keyword in content_lower for keyword in keywords):
                metrics['detected_patterns'].add(pattern)
        
        _detect_duplication(content, metrics)
        
    except Exception:
        pass


def _analyze_generic_file(file_path: str, metrics: Dict) -> None:
    """Analyze generic code files (Java, C++, etc.)."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        metrics['code_lines'] += len(lines)
        metrics['comment_lines'] += sum(
            1 for line in lines 
            if re.match(r'\s*//|/\*|\*/', line.strip())
        )
        
        # Count functions and classes
        metrics['total_functions'] += len(re.findall(r'\bfunction\b|\bdef\b|\w+\s*\(', content))
        metrics['total_classes'] += len(re.findall(r'\bclass\b|\bstruct\b|\binterface\b', content))
        
        # Check for error handling
        metrics['error_handling_instances'] += len(re.findall(r'try\s*{|catch|finally', content))
        
    except Exception:
        pass


def _detect_duplication(content: str, metrics: Dict) -> None:
    """Simple duplication detection using line fingerprinting."""
    lines = content.split('\n')
    for i in range(len(lines) - 2):
        # Create fingerprint of 3-line blocks
        block = '\n'.join(lines[i:i+3])
        fingerprint = re.sub(r'\s+', '', block)
        if len(fingerprint) > 20:
            metrics['duplicate_fingerprints'][fingerprint] += 1


def _calculate_error_handling_score(metrics: Dict) -> float:
    """Calculate error handling score (0-100)."""
    if metrics['total_functions'] == 0:
        return 50
    
    ratio = min(
        (metrics['error_handling_instances'] / max(metrics['total_functions'], 1)) * 100,
        100
    )
    return 40 + (ratio * 0.6)  # Baseline 40, up to 100


def _calculate_docstring_coverage(metrics: Dict) -> float:
    """Calculate docstring coverage (0-100)."""
    total_documented = metrics['functions_with_docstrings'] + metrics['classes_with_docstrings']
    total_items = max(metrics['total_functions'] + metrics['total_classes'], 1)
    return (total_documented / total_items) * 100


def _calculate_type_hint_coverage(metrics: Dict) -> float:
    """Calculate type hint coverage (0-100)."""
    if metrics['total_functions'] == 0:
        return 0
    return (metrics['functions_with_type_hints'] / metrics['total_functions']) * 100


def _calculate_comment_ratio(metrics: Dict) -> float:
    """Calculate comment to code ratio (0-100)."""
    total_lines = metrics['code_lines'] + metrics['comment_lines']
    if total_lines == 0:
        return 50
    
    ratio = (metrics['comment_lines'] / total_lines) * 100
    # Good ratio is 10-30%
    if ratio < 5:
        return 20
    elif ratio < 10:
        return 50
    elif ratio < 20:
        return 80
    elif ratio < 30:
        return 95
    else:
        return 80  # Too many comments might indicate over-commenting


def _calculate_duplication_score(metrics: Dict) -> float:
    """Calculate code duplication score (0-100, lower is better)."""
    if not metrics['duplicate_fingerprints']:
        return 0
    
    duplicated_blocks = sum(1 for count in metrics['duplicate_fingerprints'].values() if count > 1)
    total_blocks = len(metrics['duplicate_fingerprints'])
    
    if total_blocks == 0:
        return 0
    
    duplication_ratio = (duplicated_blocks / total_blocks) * 100
    # Scale: 0% duplication = score 0, 50% duplication = score 50
    return min(duplication_ratio, 100)
