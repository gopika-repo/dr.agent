# evaluation_logic.py - REAL SCORING LOGIC
import re
import os
import json
from typing import Dict, List, Optional, Tuple
import math

class RealScoringEngine:
    """REAL scoring engine that actually analyzes code quality"""
    
    def __init__(self):
        self.tech_keywords = {
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'sklearn'],
            'frontend': ['react', 'vue', 'angular', 'nextjs', 'javascript', 'typescript', 'html', 'css', 'tailwind'],
            'backend': ['node', 'express', 'spring', 'laravel', 'ruby', 'php', 'java'],
            'database': ['postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'ai_ml': ['opencv', 'tesseract', 'langchain', 'transformers', 'huggingface', 'llm', 'ai', 'machine learning'],
            'devops': ['github actions', 'jenkins', 'gitlab', 'ci/cd', 'monitoring', 'logging']
        }
    
    def calculate_real_score(self, repo_content: str, challenge_id: str, tech_stack: List[str], difficulty: str = "intermediate") -> Dict:
        """Calculate REAL score based on actual analysis"""
        
        # Parse challenge requirements
        challenge_requirements = self._get_challenge_requirements(challenge_id)
        
        # Analyze code quality
        code_quality_score = self._analyze_code_quality(repo_content)
        
        # Check required technologies
        tech_match_score = self._check_tech_match(tech_stack, challenge_requirements['required_tech'])
        
        # Check completeness
        completeness_score = self._check_completeness(repo_content, challenge_requirements)
        
        # Check documentation
        documentation_score = self._check_documentation(repo_content)
        
        # Check production readiness
        production_score = self._check_production_readiness(repo_content)
        
        # Calculate base score (0-70)
        base_score = (
            code_quality_score * 0.25 +
            tech_match_score * 0.20 +
            completeness_score * 0.25 +
            documentation_score * 0.15 +
            production_score * 0.15
        )
        
        # Apply challenge-specific multipliers (Uses user-provided difficulty or ID fallback)
        multiplier = self._get_challenge_multiplier(challenge_id, difficulty)
        final_base_score = base_score * multiplier
        
        # Add bonus points (0-30)
        bonus_points = self._calculate_bonus_points(repo_content, challenge_requirements)
        
        # Total score (0-100)
        total_score = min(final_base_score + bonus_points, 100)
        
        return {
            'code_quality': round(code_quality_score, 1),
            'tech_match': round(tech_match_score, 1),
            'completeness': round(completeness_score, 1),
            'documentation': round(documentation_score, 1),
            'production': round(production_score, 1),
            'bonus': round(bonus_points, 1),
            'total': round(total_score, 1),
            'breakdown': {
                'base_score': round(final_base_score, 1),
                'bonus_score': round(bonus_points, 1),
                'multiplier': multiplier
            }
        }
    
    def _analyze_code_quality(self, content: str) -> float:
        """Analyze actual code quality"""
        score = 50  # Start at average
        
        # Check for imports (shows dependency management)
        import_pattern = r'(import|from|require|include)\s+\w'
        imports = len(re.findall(import_pattern, content, re.IGNORECASE))
        if imports > 20:
            score += 15
        elif imports > 10:
            score += 10
        elif imports > 5:
            score += 5
        
        # Check for functions/classes (structure)
        function_pattern = r'(def|function|class)\s+\w+'
        functions = len(re.findall(function_pattern, content, re.IGNORECASE))
        if functions > 30:
            score += 20
        elif functions > 15:
            score += 15
        elif functions > 5:
            score += 10
        
        # Check for error handling
        error_patterns = ['try:', 'except', 'catch', 'finally', 'throw', 'raise', 'error', 'exception']
        error_handling = sum(1 for pattern in error_patterns if pattern in content.lower())
        if error_handling > 10:
            score += 10
        elif error_handling > 5:
            score += 5
        
        # Check for comments/documentation in code
        comment_patterns = ['#', '//', '/*', '*/', '"""', "'''"]
        comments = sum(content.count(pattern) for pattern in comment_patterns)
        if comments > 50:
            score += 10
        elif comments > 20:
            score += 5
        
        # Check for test files
        test_patterns = ['test_', '_test.', 'spec.', '.test.']
        has_tests = any(pattern in content.lower() for pattern in test_patterns)
        if has_tests:
            score += 10
        
        # Check for configuration files
        config_patterns = ['requirements', 'package.json', 'dockerfile', 'docker-compose', 'config.', 'settings.']
        has_config = any(pattern in content.lower() for pattern in config_patterns)
        if has_config:
            score += 5
        
        return min(score, 100)
    
    def _check_tech_match(self, actual_tech: List[str], required_tech: List[str]) -> float:
        """Check how well actual tech stack matches requirements"""
        if not required_tech:
            return 80  # Default if no requirements specified
        
        actual_lower = [tech.lower() for tech in actual_tech]
        required_lower = [tech.lower() for tech in required_tech]
        
        matches = 0
        for req in required_lower:
            # Check for partial matches
            for act in actual_lower:
                if req in act or act in req:
                    matches += 1
                    break
        
        percentage = (matches / len(required_lower)) * 100
        return min(percentage, 100)
    
    def _check_completeness(self, content: str, requirements: Dict) -> float:
        """Check how complete the project is"""
        score = 60  # Start at average
        
        # Check for README
        if 'readme' in content.lower():
            score += 10
        
        # Check for main/app files
        main_patterns = ['main.', 'app.', 'index.', 'server.', 'run.', 'start.']
        has_main = any(pattern in content.lower() for pattern in main_patterns)
        if has_main:
            score += 10
        
        # Check for challenge-specific requirements
        challenge_type = requirements.get('type', '')
        if challenge_type == 'ai':
            # Check for AI/ML components
            ai_patterns = ['model', 'train', 'predict', 'tensor', 'pytorch', 'neural', 'llm', 'ai']
            ai_found = sum(1 for pattern in ai_patterns if pattern in content.lower())
            score += min(ai_found * 5, 20)
        elif challenge_type == 'web':
            # Check for web components
            web_patterns = ['html', 'css', 'javascript', 'api', 'endpoint', 'route']
            web_found = sum(1 for pattern in web_patterns if pattern in content.lower())
            score += min(web_found * 5, 20)
        elif challenge_type == 'data':
            # Check for data components
            data_patterns = ['data', 'process', 'etl', 'pipeline', 'database', 'query']
            data_found = sum(1 for pattern in data_patterns if pattern in content.lower())
            score += min(data_found * 5, 20)
        
        return min(score, 100)
    
    def _check_documentation(self, content: str) -> float:
        """Check documentation quality"""
        score = 50
        
        # Count README sections
        readme_sections = ['# ', '## ', '### ', 'installation', 'usage', 'examples', 'api', 'contributing']
        sections_found = sum(1 for section in readme_sections if section in content.lower())
        score += sections_found * 5
        
        # Check for inline documentation
        docstring_patterns = ['"""', "'''", '/*', '*/', '//']
        docstrings = sum(content.count(pattern) for pattern in docstring_patterns)
        if docstrings > 20:
            score += 20
        elif docstrings > 10:
            score += 10
        elif docstrings > 5:
            score += 5
        
        return min(score, 100)
    
    def _check_production_readiness(self, content: str) -> float:
        """Check production readiness"""
        score = 40
        
        # Check for Docker
        if 'docker' in content.lower():
            score += 20
        
        # Check for CI/CD
        ci_patterns = ['.github', 'gitlab', 'jenkins', 'travis', 'circle']
        if any(pattern in content.lower() for pattern in ci_patterns):
            score += 15
        
        # Check for configuration management
        config_patterns = ['.env', 'config.', 'settings.', 'environment']
        if any(pattern in content.lower() for pattern in config_patterns):
            score += 10
        
        # Check for error handling (already counted, but gives extra)
        if 'try:' in content or 'catch' in content or 'except' in content:
            score += 10
        
        # Check for logging
        if 'log' in content.lower() or 'logger' in content.lower():
            score += 5
        
        return min(score, 100)
    
    def _calculate_bonus_points(self, content: str, requirements: Dict) -> float:
        """Calculate bonus points for advanced features"""
        bonus = 0
        
        # Advanced AI/ML features
        if requirements.get('type') == 'ai':
            advanced_ai = ['transformer', 'huggingface', 'langchain', 'vector', 'embedding', 'rag']
            for feature in advanced_ai:
                if feature in content.lower():
                    bonus += 3
        
        # Advanced web features
        if requirements.get('type') == 'web':
            advanced_web = ['websocket', 'real-time', 'pwa', 'service worker', 'graphql']
            for feature in advanced_web:
                if feature in content.lower():
                    bonus += 3
        
        # Advanced data features
        if requirements.get('type') == 'data':
            advanced_data = ['streaming', 'real-time', 'airflow', 'spark', 'kafka']
            for feature in advanced_data:
                if feature in content.lower():
                    bonus += 3
        
        # General advanced features
        advanced_general = ['microservice', 'kubernetes', 'terraform', 'monitoring', 'observability', 'testing']
        for feature in advanced_general:
            if feature in content.lower():
                bonus += 2
        
        # Check for extensive testing
        test_files = content.lower().count('test_') + content.lower().count('_test')
        if test_files > 5:
            bonus += 5
        elif test_files > 2:
            bonus += 3
        
        return min(bonus, 30)
    
    def _get_challenge_requirements(self, challenge_id: str) -> Dict:
        """Get specific requirements for each challenge"""
        requirements = {
            'challenge_023': {
                'type': 'ai',
                'required_tech': ['python', 'opencv', 'llm', 'ocr', 'fastapi', 'docker'],
                'description': 'AI Agents with Computer Vision and LLMs'
            },
            'challenge_024': {
                'type': 'ai',
                'required_tech': ['python', 'rag', 'langchain', 'vector', 'ai agent', 'aws'],
                'description': 'Healthcare AI Agent System with RAG'
            },
            'challenge_025': {
                'type': 'data',
                'required_tech': ['python', 'etl', 'postgresql', 'aws', 'airflow', 'docker'],
                'description': 'Healthcare Data Pipeline'
            },
            'challenge_026': {
                'type': 'web',
                'required_tech': ['react', 'django', 'node', 'postgresql', 'docker', 'aws'],
                'description': 'Full-stack Healthcare Platform'
            },
            'challenge_027': {
                'type': 'web',
                'required_tech': ['react', 'django', 'celery', 'redis', 'docker', 'monitoring'],
                'description': 'Enterprise Platform with Task Queues'
            }
        }
        
        return requirements.get(challenge_id, {
            'type': 'general',
            'required_tech': [],
            'description': 'General Development Challenge'
        })
    
    def _get_challenge_multiplier(self, challenge_id: str, difficulty: str = "intermediate") -> float:
        """Get difficulty multiplier for each challenge. 
           User difficulty (beginner/intermediate/advanced) overrides if provided.
        """
        # First check the explicit difficulty tier
        tier_multipliers = {
            'beginner': 1.1,
            'intermediate': 0.95,
            'advanced': 0.8
        }
        
        if difficulty in tier_multipliers:
            return tier_multipliers[difficulty]

        # Fallback to challenge_id based multipliers
        multipliers = {
            'challenge_023': 1.0,  # Advanced - strict scoring
            'challenge_024': 1.0,  # Advanced - strict scoring
            'challenge_025': 0.9,  # Intermediate - slightly easier
            'challenge_026': 0.9,  # Intermediate - slightly easier
            'challenge_027': 0.9   # Intermediate - slightly easier
        }
        return multipliers.get(challenge_id, 1.0)
    
    def extract_tech_stack(self, content: str) -> List[str]:
        """Extract actual tech stack from repository content"""
        tech_stack = []
        content_lower = content.lower()
        
        # Check for programming languages
        if 'python' in content_lower or '.py' in content:
            tech_stack.append('Python')
        if 'javascript' in content_lower or '.js' in content or '.ts' in content:
            tech_stack.append('JavaScript/TypeScript')
        if 'react' in content_lower:
            tech_stack.append('React')
        if 'django' in content_lower:
            tech_stack.append('Django')
        if 'node' in content_lower:
            tech_stack.append('Node.js')
        
        # Check for databases
        if 'postgres' in content_lower or 'postgresql' in content_lower:
            tech_stack.append('PostgreSQL')
        if 'mongodb' in content_lower or 'mongo' in content_lower:
            tech_stack.append('MongoDB')
        if 'redis' in content_lower:
            tech_stack.append('Redis')
        
        # Check for AI/ML
        if 'tensorflow' in content_lower or 'tensor' in content_lower:
            tech_stack.append('TensorFlow')
        if 'pytorch' in content_lower or 'torch' in content_lower:
            tech_stack.append('PyTorch')
        if 'opencv' in content_lower:
            tech_stack.append('OpenCV')
        if 'langchain' in content_lower:
            tech_stack.append('LangChain')
        
        # Check for infrastructure
        if 'docker' in content_lower:
            tech_stack.append('Docker')
        if 'aws' in content_lower:
            tech_stack.append('AWS')
        if 'azure' in content_lower:
            tech_stack.append('Azure')
        if 'gcp' in content_lower or 'google cloud' in content_lower:
            tech_stack.append('Google Cloud')
        
        # Check for frameworks/tools
        if 'fastapi' in content_lower:
            tech_stack.append('FastAPI')
        if 'flask' in content_lower:
            tech_stack.append('Flask')
        if 'celery' in content_lower:
            tech_stack.append('Celery')
        if 'airflow' in content_lower:
            tech_stack.append('Airflow')
        if 'pandas' in content_lower:
            tech_stack.append('Pandas')
        if 'numpy' in content_lower:
            tech_stack.append('NumPy')
        
        # Remove duplicates and return
        return list(dict.fromkeys(tech_stack))  # Preserves order while removing duplicates