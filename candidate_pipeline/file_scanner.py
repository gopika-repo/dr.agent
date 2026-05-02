"""
File Scanner - Analyze repository structure, file counts, and CI/CD presence.

Walks directory tree to extract metrics: total files, lines of code,
key directories (src, tests, config, etc.), and CI/CD platform detection.
"""

import os
from pathlib import Path
from typing import Dict, List, Set


# Standard directory patterns to identify as "key directories"
KEY_DIRECTORY_PATTERNS = {
    'src': ['src', 'source', 'lib', 'app', 'application'],
    'tests': ['test', 'tests', 'spec', 'specs', '__tests__'],
    'config': ['config', 'conf', 'settings', 'etc'],
    'docs': ['doc', 'docs', 'documentation'],
    'build': ['build', 'dist', 'out', 'bin'],
    'scripts': ['script', 'scripts', 'bin', 'tools'],
    'data': ['data', 'dataset', 'datasets', 'assets'],
    'ml_models': ['models', 'ml', 'ai', 'ml_models', 'pretrained']
}

# CI/CD file patterns
CICD_PATTERNS = {
    'github_actions': '.github/workflows',
    'gitlab_ci': '.gitlab-ci.yml',
    'circleci': '.circleci/config.yml',
    'jenkins': 'Jenkinsfile',
    'travis': '.travis.yml',
    'azure_pipelines': 'azure-pipelines.yml',
    'github_workflow': '.github/workflows'
}

# Code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs',
    '.go', '.rs', '.rb', '.php', '.swift', '.kotlin', '.scala',
    '.sh', '.bash', '.sql', '.r', '.m', '.h', '.hpp'
}


def scan_repository(repo_path: str) -> Dict:
    """
    Scan a repository to extract structure and metrics.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary containing:
        - total_files: int - Total file count
        - total_lines: int - Total lines of code
        - key_directories: List[str] - Identified important directories
        - has_cicd: bool - Whether CI/CD platform detected
        - cicd_platforms: List[str] - Detected CI/CD platforms
        - file_tree: Dict - Distribution of files by type
        - largest_files: List[tuple] - Top 5 largest files
    """
    repo_root = Path(repo_path)
    
    if not repo_root.exists():
        return {
            'total_files': 0,
            'total_lines': 0,
            'key_directories': [],
            'has_cicd': False,
            'cicd_platforms': [],
            'file_tree': {},
            'largest_files': [],
            'error': f'Repository path does not exist: {repo_path}'
        }
    
    total_files = 0
    total_lines = 0
    identified_dirs: Set[str] = set()
    file_extensions: Dict[str, int] = {}
    cicd_platforms: List[str] = []
    file_sizes: List[tuple[str, int]] = []
    
    # Directories to skip
    skip_dirs = {
        '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
        '.env', '.github', 'dist', 'build', '.egg-info', '.tox', '.mypy_cache'
    }
    
    try:
        for root, dirs, files in os.walk(repo_root):
            # Filter out directories to skip
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            # Check for key directories
            for dir_name in dirs:
                for category, patterns in KEY_DIRECTORY_PATTERNS.items():
                    if dir_name.lower() in patterns:
                        identified_dirs.add(category)
                        break
            
            # Check for CI/CD files in current directory
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                for cicd_name, cicd_path in CICD_PATTERNS.items():
                    if cicd_path.replace('/', os.sep) in file_path:
                        if cicd_name not in cicd_platforms:
                            cicd_platforms.append(cicd_name)
            
            # Process files
            for file_name in files:
                total_files += 1
                file_path = os.path.join(root, file_name)
                
                # Get file extension
                ext = Path(file_name).suffix.lower()
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
                # Count lines for code files
                if ext in CODE_EXTENSIONS:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                            file_sizes.append((file_name, lines))
                    except Exception:
                        pass
    
    except Exception as e:
        # Return partial results if walk fails
        pass
    
    # Sort files by size and get top 5
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    largest_files = [(name, size) for name, size in file_sizes[:5]]
    
    return {
        'total_files': total_files,
        'total_lines': total_lines,
        'key_directories': sorted(list(identified_dirs)),
        'has_cicd': len(cicd_platforms) > 0,
        'cicd_platforms': cicd_platforms,
        'file_tree': file_extensions,
        'largest_files': largest_files,
        'repository_path': str(repo_root)
    }
