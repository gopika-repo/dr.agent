"""
Technology Detector - Detect tech stack from repository files.

Analyzes requirements.txt, package.json, Gemfile, pyproject.toml, and
file extensions to categorize technologies into AI/ML, frameworks,
databases, DevOps, and testing categories.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Set


# Technology patterns mapped to categories
TECH_PATTERNS = {
    'ai_ml': [
        'opencv', 'cv2', 'tensorflow', 'torch', 'pytorch', 'keras',
        'sklearn', 'scikit-learn', 'numpy', 'scipy', 'pandas',
        'langchain', 'crewai', 'langgraph', 'transformers', 'huggingface',
        'llm', 'openai', 'anthropic', 'gemini', 'mistral',
        'yolo', 'detectron', 'rnn', 'lstm', 'gpt', 'bert',
        'spacy', 'nltk', 'gensim', 'xgboost', 'lightgbm',
        'ocr', 'tesseract', 'easyocr', 'paddleocr', 'multimodal'
    ],
    'frameworks': [
        'django', 'flask', 'fastapi', 'starlette', 'aiohttp',
        'react', 'vue', 'angular', 'svelte', 'nextjs', 'nuxt',
        'express', 'hapi', 'koa', 'nestjs',
        'spring', 'hibernate', 'tomcat',
        'rails', 'sinatra',
        'laravel', 'symfony',
        'gin', 'echo', 'chi',
        'rocket', 'actix', 'warp'
    ],
    'databases': [
        'postgresql', 'postgres', 'mysql', 'mariadb', 'sqlite',
        'mongodb', 'cassandra', 'couchdb', 'firebase',
        'redis', 'memcached', 'elasticache',
        'dynamodb', 'aurora', 'cloudspanner',
        'cockroachdb', 'elasticsearch', 'opensearch',
        'neo4j', 'graph', 'vector', 'qdrant', 'weaviate', 'pinecone'
    ],
    'devops': [
        'docker', 'dockerfile', 'docker-compose',
        'kubernetes', 'k8s', 'helm', 'istio',
        'terraform', 'cloudformation', 'ansible', 'puppet',
        'github-actions', 'gitlab-ci', 'jenkins', 'circleci', 'travis',
        'aws', 'azure', 'gcp', 'digitalocean',
        'nginx', 'apache', 'haproxy',
        'prometheus', 'grafana', 'datadog', 'newrelic',
        'ecs', 'lambda', 'fargate', 'appengine'
    ],
    'testing': [
        'pytest', 'unittest', 'nose', 'testng',
        'jest', 'mocha', 'jasmine', 'vitest',
        'rspec', 'minitest',
        'phpunit', 'cakephp',
        'testify', 'gtest',
        'selenium', 'playwright', 'cypress', 'puppeteer',
        'coverage', 'codecov', 'sonarqube', 'cobertura',
        'mock', 'faker', 'hypothesis'
    ]
}

# File extension to language mapping
EXTENSION_TO_LANG = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kotlin': 'kotlin',
    '.scala': 'scala',
    '.r': 'r',
    '.m': 'objective_c',
    '.html': 'html',
    '.css': 'css',
    '.sql': 'sql',
    '.sh': 'shell',
    '.bash': 'shell'
}


def detect_technologies(repo_path: str) -> Dict[str, List[str]]:
    """
    Detect technology stack from repository files.
    
    Analyzes:
    - requirements.txt (Python dependencies)
    - package.json (Node.js dependencies)
    - Gemfile (Ruby dependencies)
    - pyproject.toml (Python project config)
    - go.mod (Go dependencies)
    - Cargo.toml (Rust dependencies)
    - File extensions present in repository
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        Dictionary with categories as keys, lists of detected technologies as values:
        {
            'ai_ml': [...],
            'frameworks': [...],
            'databases': [...],
            'devops': [...],
            'testing': [...],
            'languages': [...]
        }
    """
    repo_root = Path(repo_path)
    detected_tech: Dict[str, Set[str]] = {
        'ai_ml': set(),
        'frameworks': set(),
        'databases': set(),
        'devops': set(),
        'testing': set(),
        'languages': set()
    }
    
    if not repo_root.exists():
        return {k: list(v) for k, v in detected_tech.items()}
    
    # Track file extensions found
    file_extensions: Set[str] = set()
    
    # Scan for dependency files and file extensions
    for root, dirs, files in os.walk(repo_root):
        # Skip common non-essential directories
        dirs[:] = [d for d in dirs if d not in {
            '.git', '.venv', 'venv', 'node_modules', '__pycache__',
            '.pytest_cache', 'dist', 'build', '.env'
        }]
        
        # Collect file extensions
        for file_name in files:
            ext = Path(file_name).suffix.lower()
            if ext in EXTENSION_TO_LANG:
                detected_tech['languages'].add(EXTENSION_TO_LANG[ext])
                file_extensions.add(ext)
        
        # Process dependency files
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            try:
                if file_name == 'requirements.txt':
                    _parse_requirements(file_path, detected_tech)
                
                elif file_name == 'package.json':
                    _parse_package_json(file_path, detected_tech)
                
                elif file_name == 'Gemfile':
                    _parse_gemfile(file_path, detected_tech)
                
                elif file_name == 'pyproject.toml':
                    _parse_pyproject_toml(file_path, detected_tech)
                
                elif file_name == 'go.mod':
                    _parse_go_mod(file_path, detected_tech)
                
                elif file_name == 'Cargo.toml':
                    _parse_cargo_toml(file_path, detected_tech)
                
                elif file_name == 'Gemfile.lock':
                    _parse_gemfile_lock(file_path, detected_tech)
                
                elif file_name == 'poetry.lock':
                    _parse_poetry_lock(file_path, detected_tech)
                
            except Exception:
                pass
    
    # Convert sets to lists and sort
    result = {}
    for category, techs in detected_tech.items():
        result[category] = sorted(list(techs))
    
    return result


def _parse_requirements(file_path: str, detected_tech: Dict) -> None:
    """Parse Python requirements.txt file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if not line or line.startswith('#'):
                    continue
                
                # Extract package name before version specifiers
                package = re.split(r'[<>=!]', line)[0].strip()
                package = package.replace('-', '_').replace('.', '_')
                
                # Match against patterns
                _match_tech_patterns(package, detected_tech)
    except Exception:
        pass


def _parse_package_json(file_path: str, detected_tech: Dict) -> None:
    """Parse Node.js package.json file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            for package in dependencies.keys():
                _match_tech_patterns(package.lower(), detected_tech)
    except Exception:
        pass


def _parse_gemfile(file_path: str, detected_tech: Dict) -> None:
    """Parse Ruby Gemfile."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if 'gem ' in line:
                    match = re.search(r"gem\s+['\"]([^'\"]+)['\"]", line)
                    if match:
                        _match_tech_patterns(match.group(1), detected_tech)
    except Exception:
        pass


def _parse_pyproject_toml(file_path: str, detected_tech: Dict) -> None:
    """Parse Python pyproject.toml file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            for line in content.split('\n'):
                if '=' in line and not line.strip().startswith('['):
                    package = line.split('=')[0].strip().strip('"\'')
                    _match_tech_patterns(package, detected_tech)
    except Exception:
        pass


def _parse_go_mod(file_path: str, detected_tech: Dict) -> None:
    """Parse Go go.mod file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith('require'):
                    parts = line.split()
                    if len(parts) > 1:
                        _match_tech_patterns(parts[1], detected_tech)
    except Exception:
        pass


def _parse_cargo_toml(file_path: str, detected_tech: Dict) -> None:
    """Parse Rust Cargo.toml file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            for line in content.split('\n'):
                if '=' in line and not line.strip().startswith('['):
                    package = line.split('=')[0].strip().strip('"\'')
                    _match_tech_patterns(package, detected_tech)
    except Exception:
        pass


def _parse_gemfile_lock(file_path: str, detected_tech: Dict) -> None:
    """Parse Ruby Gemfile.lock."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if '(' in line and not line.startswith('ruby') and not line.startswith('bundled'):
                    package = line.split('(')[0].strip()
                    _match_tech_patterns(package, detected_tech)
    except Exception:
        pass


def _parse_poetry_lock(file_path: str, detected_tech: Dict) -> None:
    """Parse Poetry poetry.lock file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith('name = '):
                    package = line.replace('name = ', '').strip().strip('"\'')
                    _match_tech_patterns(package, detected_tech)
    except Exception:
        pass


def _match_tech_patterns(package: str, detected_tech: Dict) -> None:
    """Match package against known technology patterns."""
    package = package.lower().replace('-', '_').replace('.', '_')
    
    for category, patterns in TECH_PATTERNS.items():
        for pattern in patterns:
            if package == pattern or pattern in package:
                detected_tech[category].add(pattern)
                return
