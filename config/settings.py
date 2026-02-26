# config/settings.py
import os
from typing import Dict

class Settings:
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    GITHUB_API_URL = 'https://api.github.com'
    
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Application Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_EXTENSIONS = [
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss',
        '.json', '.yaml', '.yml', '.toml', '.md', '.txt', '.ini', '.cfg',
        '.dockerfile', 'docker-compose.yml', 'docker-compose.yaml'
    ]
    
    # Evaluation Configuration
    SCORE_WEIGHTS = {
        'challenge_023': {
            'multi_modal_implementation': 0.60,
            'functionality_results': 0.25,
            'innovation_practicality': 0.15
        },
        'challenge_024': {
            'technical_implementation': 0.60,
            'functionality_results': 0.25,
            'innovation_best_practices': 0.15
        }
    }
    
    # Industry Standards
    INDUSTRY_BENCHMARKS = {
        'intern_level': 60,
        'entry_level': 75,
        'strong_hire': 85,
        'exceptional': 90
    }