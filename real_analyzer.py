# real_analyzer.py - REAL CALCULATIONS BASED ON CHALLENGE CRITERIA
import os
import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

class RealRepositoryAnalyzer:
    """
    Analyzes GitHub repositories and calculates REAL scores based on:
    1. Actual file analysis
    2. Code quality metrics
    3. Technology stack matching
    4. Challenge-specific criteria
    
    NO MOCK DATA - All calculations are based on actual repository content
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        
        # Challenge-specific criteria weights (from JSON)
        self.challenge_criteria = {
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
    
    def calculate_real_scores(self, challenge_id: str = 'challenge_023') -> Dict:
        """
        Calculate REAL scores based on actual repository analysis
        Returns breakdown of scores for each category
        """
        
        # Get challenge criteria
        criteria = self.challenge_criteria.get(challenge_id, self.challenge_criteria['challenge_023'])
        
        # Perform deep analysis
        analysis = self.analyze_deep()
        
        # Calculate individual component scores
        scores = {
            'code_quality': self._calculate_code_quality_score(analysis),
            'tech_stack_match': self._calculate_tech_match_score(analysis, criteria),
            'completeness': self._calculate_completeness_score(analysis),
            'documentation': self._calculate_documentation_score(analysis),
            'production_readiness': self._calculate_production_score(analysis),
            'innovation': self._calculate_innovation_score(analysis),
            'bonus': self._calculate_bonus_score(analysis, criteria)
        }
        
        # Calculate category scores based on challenge criteria
        category_scores = self._map_to_challenge_categories(scores, criteria, challenge_id)
        
        return {
            'component_scores': scores,
            'category_scores': category_scores,
            'analysis': analysis
        }
    
    def _calculate_code_quality_score(self, analysis: Dict) -> float:
        """
        Calculate code quality score (0-100) based on:
        - Error handling
        - Code organization
        - Testing
        - Documentation
        """
        score = 0.0
        max_score = 100.0
        
        # Error handling (25 points)
        if analysis.get('code_quality', {}).get('overall', {}).get('has_error_handling'):
            score += 25
        
        # Code organization (25 points)
        structure = analysis.get('structure', {})
        if len(structure.get('key_directories', {})) >= 3:
            score += 25
        elif len(structure.get('key_directories', {})) >= 2:
            score += 15
        elif len(structure.get('key_directories', {})) >= 1:
            score += 10
        
        # Testing (25 points)
        testing = analysis.get('testing', {})
        if testing.get('has_tests'):
            score += 10
            if testing.get('test_directory_structure'):
                score += 10
            if len(testing.get('test_frameworks', [])) > 0:
                score += 5
        
        # Documentation (25 points)
        docs = analysis.get('documentation', {})
        if docs.get('readme', {}).get('exists'):
            readme_score = docs['readme'].get('quality_score', 0)
            score += min(25, readme_score * 4)  # Scale 0-6 to 0-25
        
        return min(score, max_score)
    
    def _calculate_tech_match_score(self, analysis: Dict, criteria: Dict) -> float:
        """
        Calculate technology stack match score (0-100)
        """
        required_tech = criteria.get('required_tech', [])
        bonus_tech = criteria.get('bonus_tech', [])
        
        # Get detected technologies
        detected_tech = self._extract_technologies(analysis)
        
        # Calculate required tech match
        required_matches = 0
        for tech in required_tech:
            if self._tech_present(tech, detected_tech):
                required_matches += 1
        
        # Calculate bonus tech match
        bonus_matches = 0
        for tech in bonus_tech:
            if self._tech_present(tech, detected_tech):
                bonus_matches += 1
        
        # Score calculation
        required_score = (required_matches / len(required_tech)) * 70 if required_tech else 0
        bonus_score = (bonus_matches / len(bonus_tech)) * 30 if bonus_tech else 0
        
        return min(required_score + bonus_score, 100.0)
    
    def _calculate_completeness_score(self, analysis: Dict) -> float:
        """
        Calculate project completeness score (0-100)
        """
        score = 0.0
        
        # File count (20 points)
        file_count = analysis.get('metadata', {}).get('total_files', 0)
        if file_count >= 20:
            score += 20
        elif file_count >= 10:
            score += 15
        elif file_count >= 5:
            score += 10
        
        # Code files (20 points)
        files_data = analysis.get('files', {})
        code_files = (files_data.get('python_count', 0) + 
                     files_data.get('javascript_count', 0) + 
                     files_data.get('typescript_count', 0))
        if code_files >= 10:
            score += 20
        elif code_files >= 5:
            score += 15
        elif code_files >= 3:
            score += 10
        
        # Lines of code (20 points)
        total_lines = analysis.get('metadata', {}).get('total_lines', 0)
        if total_lines >= 1000:
            score += 20
        elif total_lines >= 500:
            score += 15
        elif total_lines >= 200:
            score += 10
        
        # Key components (20 points)
        deps = analysis.get('dependencies', {})
        if len(deps.get('python', {}).get('packages', [])) >= 5:
            score += 10
        if len(deps.get('javascript', {}).get('packages', [])) >= 5:
            score += 10
        
        # Challenge specific features (20 points)
        challenge_specific = analysis.get('challenge_specific', {})
        if challenge_specific.get('ai_ml_indicators', {}).get('has_ai_ml'):
            score += 10
        if challenge_specific.get('web_app_indicators', {}).get('has_web_app'):
            score += 5
        if challenge_specific.get('data_pipeline_indicators', {}).get('has_data_pipeline'):
            score += 5
        
        return min(score, 100.0)
    
    def _calculate_documentation_score(self, analysis: Dict) -> float:
        """
        Calculate documentation quality score (0-100)
        """
        score = 0.0
        docs = analysis.get('documentation', {})
        
        # README existence (30 points)
        if docs.get('readme', {}).get('exists'):
            score += 30
            
            # README quality (40 points)
            readme_sections = docs['readme'].get('sections', {})
            section_score = 0
            for section, exists in readme_sections.items():
                if exists:
                    section_score += 6.67  # 40 points / 6 sections
            score += min(section_score, 40)
        
        # Code comments (15 points)
        if analysis.get('code_quality', {}).get('overall', {}).get('has_comments'):
            score += 15
        
        # API docs (15 points)
        if docs.get('api_docs', {}).get('exists'):
            score += 15
        
        return min(score, 100.0)
    
    def _calculate_production_score(self, analysis: Dict) -> float:
        """
        Calculate production readiness score (0-100)
        """
        score = 0.0
        
        # Docker (25 points)
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile'):
            score += 15
        if docker.get('has_docker_compose'):
            score += 10
        
        # CI/CD (25 points)
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci'):
            score += 25
        
        # Environment config (15 points)
        metadata = analysis.get('metadata', {})
        if metadata.get('has_gitignore'):
            score += 10
        
        # Dependencies management (20 points)
        deps = analysis.get('dependencies', {})
        if len(deps.get('python', {}).get('files_found', [])) > 0:
            score += 10
        if len(deps.get('javascript', {}).get('files_found', [])) > 0:
            score += 10
        
        # Testing (15 points)
        testing = analysis.get('testing', {})
        if testing.get('has_tests'):
            score += 10
        if testing.get('coverage'):
            score += 5
        
        return min(score, 100.0)
    
    def _calculate_innovation_score(self, analysis: Dict) -> float:
        """
        Calculate innovation score (0-100)
        """
        score = 50.0  # Base score
        
        # Advanced technologies (25 points)
        challenge_specific = analysis.get('challenge_specific', {})
        ai_libs = challenge_specific.get('ai_ml_indicators', {}).get('libraries', [])
        if len(ai_libs) >= 3:
            score += 25
        elif len(ai_libs) >= 2:
            score += 15
        elif len(ai_libs) >= 1:
            score += 10
        
        # Code complexity (15 points)
        code_quality = analysis.get('code_quality', {})
        python_metrics = code_quality.get('python_metrics', {})
        if len(python_metrics.get('classes', [])) >= 3:
            score += 10
        if len(python_metrics.get('functions', [])) >= 5:
            score += 5
        
        # Architecture patterns (10 points)
        structure = analysis.get('structure', {})
        patterns = structure.get('architecture_patterns', [])
        score += min(len(patterns) * 2.5, 10)
        
        return min(score, 100.0)
    
    def _calculate_bonus_score(self, analysis: Dict, criteria: Dict) -> float:
        """
        Calculate bonus points (0-15)
        """
        bonus = 0.0
        max_bonus = criteria.get('bonus_max', 15)
        
        # Advanced features (5 points)
        challenge_specific = analysis.get('challenge_specific', {})
        if challenge_specific.get('ai_ml_indicators', {}).get('has_ai_ml'):
            bonus += 2
        if challenge_specific.get('web_app_indicators', {}).get('has_web_app'):
            bonus += 2
        if challenge_specific.get('data_pipeline_indicators', {}).get('has_data_pipeline'):
            bonus += 1
        
        # Technical excellence (5 points)
        testing = analysis.get('testing', {})
        if testing.get('has_tests') and testing.get('test_directory_structure'):
            bonus += 2
        if testing.get('coverage'):
            bonus += 1
        
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci'):
            bonus += 2
        
        # Innovation (5 points)
        ai_libs = challenge_specific.get('ai_ml_indicators', {}).get('libraries', [])
        if len(ai_libs) >= 3:
            bonus += 3
        elif len(ai_libs) >= 2:
            bonus += 2
        
        docker = analysis.get('docker', {})
        if docker.get('has_docker_compose'):
            bonus += 2
        
        return min(bonus, max_bonus)
    
    def _map_to_challenge_categories(self, scores: Dict, criteria: Dict, challenge_id: str) -> Dict:
        """
        Map component scores to challenge-specific categories
        """
        
        if challenge_id == 'challenge_023':
            # AI Agents Builder System
            return {
                'multi_modal_implementation': {
                    'score': (scores['tech_stack_match'] * 0.4 + 
                             scores['code_quality'] * 0.35 + 
                             scores['completeness'] * 0.25),
                    'max': 60,
                    'breakdown': {
                        'cv_quality': scores['tech_stack_match'] * 0.33,
                        'multi_agent_system': scores['code_quality'] * 0.33,
                        'system_engineering': scores['completeness'] * 0.33
                    }
                },
                'functionality_results': {
                    'score': (scores['completeness'] * 0.6 + 
                             scores['documentation'] * 0.4),
                    'max': 25,
                    'breakdown': {
                        'accuracy': scores['completeness'] * 0.6,
                        'demo': scores['documentation'] * 0.4
                    }
                },
                'innovation_practicality': {
                    'score': (scores['innovation'] * 0.53 + 
                             scores['production_readiness'] * 0.47),
                    'max': 15,
                    'breakdown': {
                        'creative_solutions': scores['innovation'] * 0.53,
                        'production_ready': scores['production_readiness'] * 0.47
                    }
                },
                'bonus': {
                    'score': scores['bonus'],
                    'max': 15
                }
            }
        
        elif challenge_id == 'challenge_024':
            # AI Healthcare Agent System
            return {
                'technical_implementation': {
                    'score': (scores['tech_stack_match'] * 0.33 + 
                             scores['code_quality'] * 0.33 + 
                             scores['production_readiness'] * 0.34),
                    'max': 60,
                    'breakdown': {
                        'rag_pipeline': scores['tech_stack_match'] * 0.33,
                        'ai_agents': scores['code_quality'] * 0.33,
                        'deployment': scores['production_readiness'] * 0.17,
                        'evaluation': scores['completeness'] * 0.17
                    }
                },
                'functionality_results': {
                    'score': (scores['completeness'] * 0.6 + 
                             scores['documentation'] * 0.4),
                    'max': 25
                },
                'innovation_practices': {
                    'score': (scores['innovation'] * 0.53 + 
                             scores['production_readiness'] * 0.47),
                    'max': 15
                },
                'bonus': {
                    'score': scores['bonus'],
                    'max': 15
                }
            }
        
        elif challenge_id == 'challenge_025':
            # Healthcare Analytics
            return {
                'technical_implementation': {
                    'score': (scores['tech_stack_match'] * 0.33 + 
                             scores['code_quality'] * 0.25 + 
                             scores['completeness'] * 0.25 +
                             scores['production_readiness'] * 0.17),
                    'max': 60,
                    'breakdown': {
                        'etl_pipeline': scores['tech_stack_match'] * 0.33,
                        'database_design': scores['code_quality'] * 0.25,
                        'pipeline_architecture': scores['completeness'] * 0.25,
                        'cloud_deployment': scores['production_readiness'] * 0.17
                    }
                },
                'functionality_results': {
                    'score': (scores['completeness'] * 0.6 + 
                             scores['documentation'] * 0.4),
                    'max': 25
                },
                'innovation_practices': {
                    'score': (scores['innovation'] * 0.53 + 
                             scores['production_readiness'] * 0.47),
                    'max': 15
                },
                'bonus': {
                    'score': scores['bonus'],
                    'max': 15
                }
            }
        
        elif challenge_id in ['challenge_026', 'challenge_027']:
            # Full Stack Challenges
            return {
                'technical_implementation': {
                    'score': (scores['code_quality'] * 0.33 + 
                             scores['tech_stack_match'] * 0.25 + 
                             scores['completeness'] * 0.25 +
                             scores['production_readiness'] * 0.17),
                    'max': 60,
                    'breakdown': {
                        'frontend': scores['code_quality'] * 0.33,
                        'backend': scores['tech_stack_match'] * 0.25,
                        'database': scores['completeness'] * 0.17,
                        'deployment': scores['production_readiness'] * 0.17
                    }
                },
                'functionality_results': {
                    'score': (scores['completeness'] * 0.6 + 
                             scores['documentation'] * 0.4),
                    'max': 25
                },
                'innovation_practices': {
                    'score': (scores['innovation'] * 0.53 + 
                             scores['production_readiness'] * 0.47),
                    'max': 15
                },
                'bonus': {
                    'score': scores['bonus'],
                    'max': 15
                }
            }
        
        else:
            # Default mapping
            return {
                'technical_implementation': {
                    'score': (scores['code_quality'] + scores['tech_stack_match']) / 2,
                    'max': 60
                },
                'functionality_results': {
                    'score': (scores['completeness'] + scores['documentation']) / 2,
                    'max': 25
                },
                'innovation_practices': {
                    'score': (scores['innovation'] + scores['production_readiness']) / 2,
                    'max': 15
                },
                'bonus': {
                    'score': scores['bonus'],
                    'max': 15
                }
            }
    
    def _extract_technologies(self, analysis: Dict) -> Set[str]:
        """Extract all detected technologies from analysis"""
        technologies = set()
        
        # From dependencies
        deps = analysis.get('dependencies', {})
        for pkg in deps.get('python', {}).get('packages', []):
            technologies.add(pkg.lower())
        for pkg in deps.get('javascript', {}).get('packages', []):
            technologies.add(pkg.lower())
        
        # From code imports
        code_quality = analysis.get('code_quality', {})
        python_metrics = code_quality.get('python_metrics', {})
        for imp in python_metrics.get('imports', []):
            technologies.add(imp.lower().split('.')[0])
        
        js_metrics = code_quality.get('javascript_metrics', {})
        for imp in js_metrics.get('imports', []):
            technologies.add(imp.lower())
        
        # From challenge-specific indicators
        challenge_specific = analysis.get('challenge_specific', {})
        for lib in challenge_specific.get('ai_ml_indicators', {}).get('libraries', []):
            technologies.add(lib.lower())
        
        return technologies
    
    def _tech_present(self, tech: str, detected: Set[str]) -> bool:
        """Check if technology is present in detected set"""
        tech_lower = tech.lower()
        
        # Direct match
        if tech_lower in detected:
            return True
        
        # Partial match for common aliases
        tech_aliases = {
            'llm': ['openai', 'anthropic', 'gemini', 'langchain', 'transformers'],
            'opencv': ['cv2', 'opencv'],
            'rag': ['langchain', 'llamaindex'],
            'vector db': ['qdrant', 'chroma', 'pinecone', 'weaviate', 'faiss'],
            'ai agents': ['langgraph', 'crewai', 'autogen'],
            'task queue': ['celery', 'bull', 'redis'],
            'ocr': ['tesseract', 'easyocr', 'pytesseract', 'paddleocr'],
            'multi-modal': ['multimodal', 'gpt-4v', 'claude', 'gemini']
        }
        
        if tech_lower in tech_aliases:
            return any(alias in detected for alias in tech_aliases[tech_lower])
        
        # Check for partial matches
        for detected_tech in detected:
            if tech_lower in detected_tech or detected_tech in tech_lower:
                return True
        
        return False
    
    def analyze_deep(self) -> Dict:
        """DEEP analysis - reads files, understands code, extracts REAL data"""
        try:
            return {
                'metadata': self._analyze_metadata(),
                'structure': self._analyze_structure(),
                'files': self._analyze_files(),
                'code_quality': self._analyze_code_quality(),
                'dependencies': self._analyze_dependencies(),
                'documentation': self._analyze_documentation(),
                'testing': self._analyze_testing(),
                'docker': self._analyze_docker(),
                'ci_cd': self._analyze_ci_cd(),
                'challenge_specific': self._analyze_challenge_specific(),
                'key_files_content': self._extract_key_files(),
                'stats': self._calculate_stats(),
                'code_patterns_found': self._analyze_code_patterns()
            }
        except Exception as e:
            return {'error': f"Deep analysis error: {str(e)}"}
    
    def _analyze_metadata(self) -> Dict:
        """Extract repository metadata"""
        metadata = {
            'has_readme': False,
            'has_license': False,
            'has_gitignore': False,
            'has_test_directory': False,
            'has_dockerfile': False,
            'total_files': 0,
            'total_lines': 0,
            'repo_size_mb': 0
        }
        
        # Count files and lines
        total_files = 0
        total_lines = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                total_files += 1
                
                # Count lines for code files
                if file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines += len(f.readlines())
                    except:
                        continue
        
        metadata['total_files'] = total_files
        metadata['total_lines'] = total_lines
        
        # Check for key files
        for item in self.repo_path.iterdir():
            if item.is_file():
                name_lower = item.name.lower()
                if name_lower.startswith('readme'):
                    metadata['has_readme'] = True
                elif 'license' in name_lower:
                    metadata['has_license'] = True
                elif name_lower == '.gitignore':
                    metadata['has_gitignore'] = True
                elif 'dockerfile' in name_lower:
                    metadata['has_dockerfile'] = True
        
        # Check for test directory
        test_dirs = ['tests', 'test', '__tests__']
        for test_dir in test_dirs:
            if (self.repo_path / test_dir).exists():
                metadata['has_test_directory'] = True
                break
        
        # Calculate repo size
        total_size = 0
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                file_path = Path(root) / file
                try:
                    total_size += file_path.stat().st_size
                except:
                    continue
        
        metadata['repo_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return metadata
    
    def _analyze_structure(self) -> Dict:
        """Analyze directory structure"""
        structure = {
            'key_directories': {},
            'architecture_patterns': []
        }
        
        key_dirs = ['src', 'app', 'lib', 'core', 'api', 'routes', 'models', 
                   'tests', 'test', 'docs', 'documentation', 'docker', 
                   'deploy', 'config', 'configuration', 'data', 'etl']
        
        for dir_name in key_dirs:
            if (self.repo_path / dir_name).exists():
                structure['key_directories'][dir_name] = True
        
        # Detect architecture patterns
        if 'src' in structure['key_directories']:
            structure['architecture_patterns'].append('src-based')
        if 'app' in structure['key_directories']:
            structure['architecture_patterns'].append('app-based')
        if 'tests' in structure['key_directories'] or 'test' in structure['key_directories']:
            structure['architecture_patterns'].append('test-separated')
        if 'config' in structure['key_directories'] or 'configuration' in structure['key_directories']:
            structure['architecture_patterns'].append('config-separated')
        
        return structure
    
    def _analyze_files(self) -> Dict:
        """Analyze file types and counts"""
        files = {
            'python_count': 0,
            'javascript_count': 0,
            'typescript_count': 0,
            'html_count': 0,
            'css_count': 0,
            'json_count': 0,
            'yaml_count': 0,
            'markdown_count': 0,
            'largest_files': [],
            'code_file_details': []
        }
        
        # Count files by type
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                ext = file_path.suffix.lower()
                
                if ext == '.py':
                    files['python_count'] += 1
                elif ext in ['.js', '.jsx']:
                    files['javascript_count'] += 1
                elif ext in ['.ts', '.tsx']:
                    files['typescript_count'] += 1
                elif ext == '.html':
                    files['html_count'] += 1
                elif ext in ['.css', '.scss', '.less']:
                    files['css_count'] += 1
                elif ext == '.json':
                    files['json_count'] += 1
                elif ext in ['.yaml', '.yml']:
                    files['yaml_count'] += 1
                elif ext == '.md':
                    files['markdown_count'] += 1
                
                # Get file stats for code files
                if ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c']:
                    try:
                        size = file_path.stat().st_size
                        if size < 1024 * 1024:  # Less than 1MB
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                lines = len(content.split('\n'))
                                
                                files['code_file_details'].append({
                                    'path': str(file_path.relative_to(self.repo_path)),
                                    'size_kb': round(size / 1024, 2),
                                    'lines': lines,
                                    'has_content': len(content.strip()) > 50
                                })
                                
                                if size > 1024:  # Larger than 1KB
                                    files['largest_files'].append({
                                        'path': str(file_path.relative_to(self.repo_path)),
                                        'size_kb': round(size / 1024, 2),
                                        'lines': lines
                                    })
                    except:
                        continue
        
        # Sort largest files
        files['largest_files'] = sorted(files['largest_files'], 
                                      key=lambda x: x['size_kb'], 
                                      reverse=True)[:10]
        
        # Limit code file details
        files['code_file_details'] = files['code_file_details'][:20]
        
        return files
    
    def _analyze_code_quality(self) -> Dict:
        """Analyze code quality with AST parsing"""
        quality = {
            'python_metrics': {},
            'javascript_metrics': {},
            'overall': {
                'has_error_handling': False,
                'has_logging': False,
                'has_comments': False,
                'has_docstrings': False,
                'complexity_indicators': []
            }
        }
        
        # Analyze Python files
        python_files = list(self.repo_path.rglob('*.py'))
        if python_files:
            quality['python_metrics'] = self._analyze_python_files(python_files[:10])
        
        # Analyze JavaScript files
        js_files = list(self.repo_path.rglob('*.js')) + list(self.repo_path.rglob('*.jsx'))
        if js_files:
            quality['javascript_metrics'] = self._analyze_javascript_files(js_files[:5])
        
        # Check for patterns in all code files
        code_files = list(self.repo_path.rglob('*.py')) + list(self.repo_path.rglob('*.js')) + \
                    list(self.repo_path.rglob('*.jsx')) + list(self.repo_path.rglob('*.ts')) + \
                    list(self.repo_path.rglob('*.tsx'))
        
        for file_path in code_files[:15]:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check for error handling
                    if 'try:' in content or 'except' in content or 'catch' in content:
                        quality['overall']['has_error_handling'] = True
                    
                    # Check for logging
                    if 'log' in content.lower() or 'console.' in content:
                        quality['overall']['has_logging'] = True
                    
                    # Check for comments
                    if '#' in content or '//' in content or '/*' in content:
                        quality['overall']['has_comments'] = True
                    
                    # Check for complexity
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if len(line.strip()) > 100:
                            quality['overall']['complexity_indicators'].append({
                                'file': str(file_path.relative_to(self.repo_path)),
                                'line': i + 1,
                                'issue': 'Long line (>100 chars)'
                            })
            except:
                continue
        
        # Limit complexity indicators
        quality['overall']['complexity_indicators'] = quality['overall']['complexity_indicators'][:10]
        
        return quality
    
    def _analyze_python_files(self, python_files: List[Path]) -> Dict:
        """Analyze Python files with AST"""
        metrics = {
            'total_files': len(python_files),
            'imports': [],
            'functions': [],
            'classes': [],
            'has_type_hints': False,
            'has_docstrings': False,
            'has_decorators': False
        }
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try AST parsing
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                metrics['imports'].append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ''
                            for alias in node.names:
                                metrics['imports'].append(f"{module}.{alias.name}")
                        
                        elif isinstance(node, ast.FunctionDef):
                            func_info = {
                                'name': node.name,
                                'has_docstring': bool(ast.get_docstring(node)),
                                'has_type_hints': bool(node.returns)
                            }
                            metrics['functions'].append(func_info)
                            
                            if func_info['has_docstring']:
                                metrics['has_docstrings'] = True
                            if func_info['has_type_hints']:
                                metrics['has_type_hints'] = True
                            if node.decorator_list:
                                metrics['has_decorators'] = True
                        
                        elif isinstance(node, ast.ClassDef):
                            class_info = {
                                'name': node.name,
                                'has_docstring': bool(ast.get_docstring(node))
                            }
                            metrics['classes'].append(class_info)
                
                except SyntaxError:
                    # Fallback to regex
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            parts = line.strip().split()
                            if len(parts) > 1:
                                metrics['imports'].append(parts[1].split('.')[0])
                        elif line.strip().startswith('def '):
                            metrics['functions'].append({'name': line.strip().split()[1].split('(')[0]})
                        elif line.strip().startswith('class '):
                            metrics['classes'].append({'name': line.strip().split()[1].split('(')[0]})
            
            except:
                continue
        
        # Remove duplicates
        metrics['imports'] = list(set(metrics['imports']))
        
        return metrics
    
    def _analyze_javascript_files(self, js_files: List[Path]) -> Dict:
        """Analyze JavaScript files"""
        metrics = {
            'total_files': len(js_files),
            'imports': [],
            'functions': [],
            'classes': [],
            'has_typescript': False
        }
        
        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for TypeScript
                if js_file.suffix in ['.ts', '.tsx']:
                    metrics['has_typescript'] = True
                
                # Extract imports
                import_pattern = r'(import|require)\s*\(?[\'"]([^"\']+)[\'"]\)?'
                imports = re.findall(import_pattern, content)
                for imp in imports:
                    metrics['imports'].append(imp[1])
                
                # Extract functions
                function_pattern = r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
                functions = re.findall(function_pattern, content)
                metrics['functions'].extend(functions)
                
                # Extract classes
                class_pattern = r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*'
                classes = re.findall(class_pattern, content)
                metrics['classes'].extend(classes)
            
            except:
                continue
        
        # Remove duplicates
        metrics['imports'] = list(set(metrics['imports']))
        metrics['functions'] = list(set(metrics['functions']))
        metrics['classes'] = list(set(metrics['classes']))
        
        return metrics
    
    def _analyze_dependencies(self) -> Dict:
        """Analyze dependencies"""
        deps = {
            'python': {'packages': [], 'files_found': []},
            'javascript': {'packages': [], 'files_found': []},
            'docker': {'images': [], 'files_found': []}
        }
        
        # Python dependencies
        req_files = ['requirements.txt', 'pyproject.toml', 'setup.py']
        for req_file in req_files:
            file_path = self.repo_path / req_file
            if file_path.exists():
                deps['python']['files_found'].append(req_file)
                try:
                    if req_file == 'requirements.txt':
                        with open(file_path, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and not line.startswith('-'):
                                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
                                    if pkg and pkg not in deps['python']['packages']:
                                        deps['python']['packages'].append(pkg)
                except:
                    pass
        
        # JavaScript dependencies
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            deps['javascript']['files_found'].append('package.json')
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    if 'dependencies' in data:
                        deps['javascript']['packages'].extend(list(data['dependencies'].keys()))
                    if 'devDependencies' in data:
                        deps['javascript']['packages'].extend(list(data['devDependencies'].keys()))
            except:
                pass
        
        # Docker dependencies
        dockerfile = self.repo_path / 'Dockerfile'
        if dockerfile.exists():
            deps['docker']['files_found'].append('Dockerfile')
            try:
                with open(dockerfile, 'r') as f:
                    for line in f:
                        if line.strip().upper().startswith('FROM '):
                            image = line[5:].strip().split()[0]
                            if image and image not in deps['docker']['images']:
                                deps['docker']['images'].append(image)
            except:
                pass
        
        return deps
    
    def _analyze_documentation(self) -> Dict:
        """Analyze documentation"""
        docs = {
            'readme': {'exists': False, 'sections': {}, 'quality_score': 0},
            'api_docs': {'exists': False, 'files': []},
            'architecture_docs': {'exists': False, 'files': []}
        }
        
        # Find README
        readme_files = list(self.repo_path.glob('README*'))
        if readme_files:
            readme_file = readme_files[0]
            docs['readme']['exists'] = True
            
            try:
                with open(readme_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check sections
                sections = {
                    'installation': ['install', 'setup', 'getting started'],
                    'usage': ['usage', 'example', 'demo'],
                    'api': ['api', 'endpoint', 'rest', 'graphql'],
                    'configuration': ['config', 'setting', 'environment'],
                    'testing': ['test', 'testing'],
                    'deployment': ['deploy', 'docker', 'production']
                }
                
                content_lower = content.lower()
                found_sections = {}
                for section, keywords in sections.items():
                    found_sections[section] = any(keyword in content_lower for keyword in keywords)
                
                docs['readme']['sections'] = found_sections
                
                # Calculate quality score
                score = 0
                for section in ['installation', 'usage', 'api', 'configuration', 'testing', 'deployment']:
                    if found_sections.get(section):
                        score += 1
                docs['readme']['quality_score'] = min(score, 6)
            
            except:
                pass
        
        return docs
    
    def _analyze_testing(self) -> Dict:
        """Analyze testing"""
        testing = {
            'has_tests': False,
            'test_files': [],
            'test_frameworks': set(),
            'coverage': False,
            'test_directory_structure': False
        }
        
        # Find test directory
        test_dirs = ['tests', 'test', '__tests__']
        for test_dir in test_dirs:
            if (self.repo_path / test_dir).exists():
                testing['has_tests'] = True
                testing['test_directory_structure'] = True
                
                # Find test files
                for pattern in ['*.py', '*.js', '*.ts']:
                    test_files = list((self.repo_path / test_dir).rglob(pattern))
                    for test_file in test_files:
                        if 'test' in test_file.name.lower() or 'spec' in test_file.name.lower():
                            testing['test_files'].append(str(test_file.relative_to(self.repo_path)))
                break
        
        # Also look for test files in root
        if not testing['has_tests']:
            for pattern in ['*test*.py', '*spec*.js', '*test*.js']:
                test_files = list(self.repo_path.rglob(pattern))
                for test_file in test_files:
                    if 'test' in test_file.name.lower() or 'spec' in test_file.name.lower():
                        testing['test_files'].append(str(test_file.relative_to(self.repo_path)))
                        testing['has_tests'] = True
        
        # Check for coverage files
        coverage_files = ['.coverage', 'coverage.xml', 'coverage.json']
        for file_name in coverage_files:
            if (self.repo_path / file_name).exists():
                testing['coverage'] = True
                break
        
        # Detect test frameworks from file content
        for test_file in testing['test_files'][:5]:
            try:
                with open(self.repo_path / test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'pytest' in content:
                        testing['test_frameworks'].add('pytest')
                    if 'unittest' in content:
                        testing['test_frameworks'].add('unittest')
                    if 'jest' in content:
                        testing['test_frameworks'].add('jest')
                    if 'mocha' in content:
                        testing['test_frameworks'].add('mocha')
            except:
                continue
        
        testing['test_frameworks'] = list(testing['test_frameworks'])
        
        return testing
    
    def _analyze_docker(self) -> Dict:
        """Analyze Docker configuration"""
        docker = {
            'has_dockerfile': False,
            'has_docker_compose': False
        }
        
        # Check for Dockerfile
        dockerfiles = list(self.repo_path.glob('Dockerfile*'))
        if dockerfiles:
            docker['has_dockerfile'] = True
        
        # Check for docker-compose
        compose_files = list(self.repo_path.glob('docker-compose*'))
        if compose_files:
            docker['has_docker_compose'] = True
        
        return docker
    
    def _analyze_ci_cd(self) -> Dict:
        """Analyze CI/CD configuration"""
        ci_cd = {
            'has_ci': False,
            'ci_files': [],
            'ci_platforms': set()
        }
        
        # Check for CI files
        ci_patterns = ['.github/workflows/*.yml', '.github/workflows/*.yaml', 
                      '.gitlab-ci.yml', '.travis.yml']
        
        for pattern in ci_patterns:
            ci_files = list(self.repo_path.rglob(pattern))
            if ci_files:
                ci_cd['has_ci'] = True
                ci_cd['ci_files'].extend([
                    str(f.relative_to(self.repo_path)) for f in ci_files
                ])
                
                for ci_file in ci_files:
                    rel_path = str(ci_file.relative_to(self.repo_path))
                    if 'github' in rel_path:
                        ci_cd['ci_platforms'].add('GitHub Actions')
                    elif 'gitlab' in rel_path:
                        ci_cd['ci_platforms'].add('GitLab CI')
                    elif 'travis' in rel_path:
                        ci_cd['ci_platforms'].add('Travis CI')
        
        ci_cd['ci_platforms'] = list(ci_cd['ci_platforms'])
        
        return ci_cd
    
    def _analyze_challenge_specific(self) -> Dict:
        """Analyze challenge-specific indicators"""
        challenge_specific = {
            'ai_ml_indicators': {
                'has_ai_ml': False,
                'libraries': []
            },
            'web_app_indicators': {
                'has_web_app': False
            },
            'data_pipeline_indicators': {
                'has_data_pipeline': False
            }
        }
        
        # Check for AI/ML libraries in Python files
        ai_ml_libraries = ['tensorflow', 'torch', 'pytorch', 'transformers', 'langchain', 
                          'opencv', 'pytesseract', 'easyocr', 'yolo', 'openai', 'anthropic', 
                          'gemini', 'crewai', 'langgraph', 'autogen']
        
        python_files = list(self.repo_path.rglob('*.py'))
        for py_file in python_files[:5]:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    for lib in ai_ml_libraries:
                        if lib in content:
                            challenge_specific['ai_ml_indicators']['has_ai_ml'] = True
                            if lib not in challenge_specific['ai_ml_indicators']['libraries']:
                                challenge_specific['ai_ml_indicators']['libraries'].append(lib)
            except:
                continue
        
        # Check for web app indicators
        web_files = list(self.repo_path.rglob('*.html')) + list(self.repo_path.rglob('*.js')) + \
                   list(self.repo_path.rglob('*.jsx'))
        if web_files:
            challenge_specific['web_app_indicators']['has_web_app'] = True
        
        # Check for data pipeline indicators
        data_files = list(self.repo_path.rglob('*.sql')) + list(self.repo_path.rglob('*etl*')) + \
                    list(self.repo_path.rglob('*pipeline*'))
        if data_files:
            challenge_specific['data_pipeline_indicators']['has_data_pipeline'] = True
        
        return challenge_specific
    
    def _extract_key_files(self) -> Dict:
        """Extract content from key files"""
        key_files = {
            'readme': '',
            'requirements': '',
            'dockerfile': '',
            'main_app': ''
        }
        
        # Read README
        readme_files = list(self.repo_path.glob('README*'))
        if readme_files:
            try:
                with open(readme_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    key_files['readme'] = f.read(2000)
            except:
                pass
        
        # Read requirements
        req_files = ['requirements.txt', 'package.json']
        for file_name in req_files:
            file_path = self.repo_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        key_files['requirements'] += f"\n=== {file_name} ===\n" + f.read(1000)
                except:
                    pass
        
        # Read Dockerfile
        dockerfile = self.repo_path / 'Dockerfile'
        if dockerfile.exists():
            try:
                with open(dockerfile, 'r') as f:
                    key_files['dockerfile'] = f.read(1000)
            except:
                pass
        
        # Find main application file
        main_patterns = ['main.py', 'app.py', 'index.js', 'server.js']
        for pattern in main_patterns:
            main_files = list(self.repo_path.rglob(pattern))
            if main_files:
                try:
                    with open(main_files[0], 'r', encoding='utf-8') as f:
                        key_files['main_app'] = f.read(2000)
                    break
                except:
                    continue
        
        return key_files
    
    def _calculate_stats(self) -> Dict:
        """Calculate repository statistics"""
        stats = {
            'file_count': 0,
            'line_count': 0,
            'code_files': 0,
            'comment_lines': 0,
            'blank_lines': 0
        }
        
        code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c'}
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                stats['file_count'] += 1
                
                # Count lines for code files
                if file_path.suffix in code_extensions:
                    stats['code_files'] += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            stats['line_count'] += len(lines)
                            
                            for line in lines:
                                line_stripped = line.strip()
                                if not line_stripped:
                                    stats['blank_lines'] += 1
                                elif line_stripped.startswith('#') or line_stripped.startswith('//'):
                                    stats['comment_lines'] += 1
                    except:
                        continue
        
        return stats
    
    def _analyze_code_patterns(self) -> Dict:
        """Analyze code patterns"""
        patterns_found = {
            'error_handling': [],
            'logging': [],
            'testing': []
        }
        
        code_files = list(self.repo_path.rglob('*.py')) + list(self.repo_path.rglob('*.js')) + \
                    list(self.repo_path.rglob('*.ts'))
        
        for file_path in code_files[:10]:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    rel_path = str(file_path.relative_to(self.repo_path))
                    
                    # Error handling patterns
                    if 'try:' in content or 'except' in content or 'catch' in content:
                        patterns_found['error_handling'].append({
                            'file': rel_path,
                            'count': content.count('try:') + content.count('except') + content.count('catch')
                        })
                    
                    # Logging patterns
                    if 'log' in content.lower() or 'console.' in content:
                        patterns_found['logging'].append({
                            'file': rel_path,
                            'count': content.lower().count('log')
                        })
                    
                    # Testing patterns
                    if 'test' in content.lower() or 'assert' in content:
                        patterns_found['testing'].append({
                            'file': rel_path,
                            'count': content.lower().count('test') + content.count('assert')
                        })
                        
            except:
                continue
        
        return patterns_found