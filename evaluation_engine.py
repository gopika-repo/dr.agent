# models/evaluation_engine.py - REAL Evaluation Engine
import re
from typing import Dict, List, Optional, Any
import math
from pathlib import Path

class EvaluationEngine:
    def __init__(self, challenge: Dict):
        self.challenge = challenge
        self.challenge_id = challenge.get('_id', '')
        
    def evaluate(self, analysis_results: Dict) -> Dict:
        """REAL evaluation with complete calculations"""
        
        if self.challenge_id == 'challenge_023':
            return self._evaluate_challenge_023(analysis_results)
        elif self.challenge_id == 'challenge_024':
            return self._evaluate_challenge_024(analysis_results)
        elif self.challenge_id == 'challenge_025':
            return self._evaluate_challenge_025(analysis_results)
        elif self.challenge_id == 'challenge_026':
            return self._evaluate_challenge_026(analysis_results)
        elif self.challenge_id == 'challenge_027':
            return self._evaluate_challenge_027(analysis_results)
        else:
            return self._evaluate_general(analysis_results)
    
    def _evaluate_challenge_023(self, analysis: Dict) -> Dict:
        """Evaluate AI Agents Builder System"""
        score_breakdown = []
        total_score = 0
        
        # 1. Technical Implementation (60 points)
        tech_score = self._calculate_tech_score_023(analysis)
        tech_details = self._get_tech_details_023(analysis)
        score_breakdown.append({
            'category': 'Technical Implementation',
            'score': tech_score,
            'max': 60,
            'details': tech_details
        })
        total_score += tech_score
        
        # 2. Functionality & Results (25 points)
        func_score = self._calculate_func_score_023(analysis)
        func_details = self._get_func_details_023(analysis)
        score_breakdown.append({
            'category': 'Functionality & Results',
            'score': func_score,
            'max': 25,
            'details': func_details
        })
        total_score += func_score
        
        # 3. Innovation & Practicality (15 points)
        innov_score = self._calculate_innov_score_023(analysis)
        innov_details = self._get_innov_details_023(analysis)
        score_breakdown.append({
            'category': 'Innovation & Practicality',
            'score': innov_score,
            'max': 15,
            'details': innov_details
        })
        total_score += innov_score
        
        # Bonus Points (0-15)
        bonus_score = self._calculate_bonus_score(analysis)
        
        return {
            'score_breakdown': score_breakdown,
            'total_score': min(total_score, 100),
            'max_score': 100,
            'bonus_score': min(bonus_score, 15),
            'max_bonus': 15,
            'final_score': min(total_score, 100) + min(bonus_score, 15)
        }
    
    def _calculate_tech_score_023(self, analysis: Dict) -> int:
        """Calculate technical score for challenge 023"""
        score = 0
        
        # Check for CV libraries
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        cv_libs = ['opencv', 'pillow', 'torchvision', 'pytesseract', 'easyocr', 'paddleocr']
        found_cv = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in cv_libs))
        
        if found_cv >= 3:
            score += 15
        elif found_cv >= 2:
            score += 10
        elif found_cv >= 1:
            score += 5
        
        # Check for agent frameworks
        agent_libs = ['langchain', 'langgraph', 'crewai', 'autogen']
        found_agents = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in agent_libs))
        
        if found_agents >= 2:
            score += 15
        elif found_agents >= 1:
            score += 10
        
        # Check for system engineering
        structure = analysis.get('structure', {})
        key_dirs = structure.get('key_directories', {})
        
        if key_dirs.get('src') or key_dirs.get('app'):
            score += 10
        
        # Check for tests
        tests = analysis.get('tests', {})
        if tests.get('has_test_directory', False):
            score += 10
        
        # Check for Docker
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            score += 10
        
        return min(score, 60)
    
    def _calculate_func_score_023(self, analysis: Dict) -> int:
        """Calculate functionality score for challenge 023"""
        score = 0
        
        # Check documentation quality
        docs = analysis.get('documentation', {})
        if docs.get('has_setup_instructions', False):
            score += 5
        
        if docs.get('has_examples', False):
            score += 5
        
        if docs.get('has_api_docs', False):
            score += 5
        
        # Check for demo/example files
        all_files = self._get_all_files(analysis)
        demo_files = [f for f in all_files if 'demo' in f.lower() or 'example' in f.lower()]
        if len(demo_files) >= 2:
            score += 5
        
        # Check for validation
        test_files = len(analysis.get('tests', {}).get('test_files', []))
        if test_files >= 5:
            score += 5
        
        return min(score, 25)
    
    def _calculate_innov_score_023(self, analysis: Dict) -> int:
        """Calculate innovation score for challenge 023"""
        score = 0
        
        # Check for multi-modal indicators
        docs = analysis.get('documentation', {})
        readme_content = docs.get('readme_content', '').lower()
        
        multi_modal_terms = ['multi-modal', 'multimodal', 'cv+llm', 'computer vision', 'ocr', 'layout']
        multi_modal_count = sum(1 for term in multi_modal_terms if term in readme_content)
        
        if multi_modal_count >= 3:
            score += 8
        elif multi_modal_count >= 2:
            score += 5
        elif multi_modal_count >= 1:
            score += 3
        
        # Check for production readiness
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            score += 4
        
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci', False):
            score += 3
        
        return min(score, 15)
    
    # Similar methods for other challenges...
    def _evaluate_challenge_024(self, analysis: Dict) -> Dict:
        """Evaluate AI Healthcare Agent System"""
        score_breakdown = []
        total_score = 0
        
        # Technical Implementation (60)
        tech_score = self._calculate_tech_score_024(analysis)
        score_breakdown.append({
            'category': 'Technical Implementation',
            'score': tech_score,
            'max': 60
        })
        total_score += tech_score
        
        # Functionality & Results (25)
        func_score = self._calculate_func_score_024(analysis)
        score_breakdown.append({
            'category': 'Functionality & Results',
            'score': func_score,
            'max': 25
        })
        total_score += func_score
        
        # Innovation & Best Practices (15)
        innov_score = self._calculate_innov_score_024(analysis)
        score_breakdown.append({
            'category': 'Innovation & Best Practices',
            'score': innov_score,
            'max': 15
        })
        total_score += innov_score
        
        bonus_score = self._calculate_bonus_score(analysis)
        
        return {
            'score_breakdown': score_breakdown,
            'total_score': min(total_score, 100),
            'max_score': 100,
            'bonus_score': min(bonus_score, 15),
            'max_bonus': 15,
            'final_score': min(total_score, 100) + min(bonus_score, 15)
        }
    
    def _calculate_tech_score_024(self, analysis: Dict) -> int:
        """Calculate technical score for challenge 024"""
        score = 0
        
        # Check for RAG/AI libraries
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        rag_libs = ['langchain', 'llamaindex', 'chromadb', 'pinecone', 'faiss', 'qdrant']
        found_rag = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in rag_libs))
        
        if found_rag >= 3:
            score += 20
        elif found_rag >= 2:
            score += 15
        elif found_rag >= 1:
            score += 10
        
        # Check for agent frameworks
        agent_libs = ['langgraph', 'crewai', 'autogen']
        found_agents = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in agent_libs))
        
        if found_agents >= 2:
            score += 20
        elif found_agents >= 1:
            score += 15
        
        # Check for AWS/cloud
        cloud_patterns = ['boto3', 'aws', 'azure', 'google.cloud']
        found_cloud = sum(1 for dep in python_deps if any(pattern in dep.lower() for pattern in cloud_patterns))
        
        if found_cloud >= 2:
            score += 20
        elif found_cloud >= 1:
            score += 15
        
        return min(score, 60)
    
    # Methods for challenges 025-027...
    
    def _evaluate_challenge_025(self, analysis: Dict) -> Dict:
        """Evaluate Healthcare Analytics"""
        return self._evaluate_data_pipeline(analysis, "Healthcare Analytics")
    
    def _evaluate_challenge_026(self, analysis: Dict) -> Dict:
        """Evaluate AI Healthcare Platform"""
        return self._evaluate_full_stack(analysis, "AI Healthcare Platform")
    
    def _evaluate_challenge_027(self, analysis: Dict) -> Dict:
        """Evaluate Enterprise Platform"""
        return self._evaluate_enterprise(analysis, "Enterprise Platform")
    
    def _evaluate_data_pipeline(self, analysis: Dict, challenge_name: str) -> Dict:
        """Generic data pipeline evaluation"""
        score_breakdown = []
        total_score = 0
        
        # ETL/Data Pipeline (40)
        pipeline_score = self._calculate_pipeline_score(analysis)
        score_breakdown.append({
            'category': 'Data Pipeline',
            'score': pipeline_score,
            'max': 40
        })
        total_score += pipeline_score
        
        # Database Design (30)
        db_score = self._calculate_db_score(analysis)
        score_breakdown.append({
            'category': 'Database Design',
            'score': db_score,
            'max': 30
        })
        total_score += db_score
        
        # Deployment & Monitoring (30)
        deploy_score = self._calculate_deploy_score(analysis)
        score_breakdown.append({
            'category': 'Deployment & Monitoring',
            'score': deploy_score,
            'max': 30
        })
        total_score += deploy_score
        
        bonus_score = self._calculate_bonus_score(analysis)
        
        return {
            'score_breakdown': score_breakdown,
            'total_score': min(total_score, 100),
            'max_score': 100,
            'bonus_score': min(bonus_score, 15),
            'max_bonus': 15,
            'final_score': min(total_score, 100) + min(bonus_score, 15)
        }
    
    def _evaluate_full_stack(self, analysis: Dict, challenge_name: str) -> Dict:
        """Generic full-stack evaluation"""
        score_breakdown = []
        total_score = 0
        
        # Frontend (35)
        frontend_score = self._calculate_frontend_score(analysis)
        score_breakdown.append({
            'category': 'Frontend Development',
            'score': frontend_score,
            'max': 35
        })
        total_score += frontend_score
        
        # Backend (35)
        backend_score = self._calculate_backend_score(analysis)
        score_breakdown.append({
            'category': 'Backend Development',
            'score': backend_score,
            'max': 35
        })
        total_score += backend_score
        
        # AI/ML Integration (30)
        ai_score = self._calculate_ai_score(analysis)
        score_breakdown.append({
            'category': 'AI/ML Integration',
            'score': ai_score,
            'max': 30
        })
        total_score += ai_score
        
        bonus_score = self._calculate_bonus_score(analysis)
        
        return {
            'score_breakdown': score_breakdown,
            'total_score': min(total_score, 100),
            'max_score': 100,
            'bonus_score': min(bonus_score, 15),
            'max_bonus': 15,
            'final_score': min(total_score, 100) + min(bonus_score, 15)
        }
    
    def _evaluate_enterprise(self, analysis: Dict, challenge_name: str) -> Dict:
        """Generic enterprise platform evaluation"""
        score_breakdown = []
        total_score = 0
        
        # System Design (40)
        design_score = self._calculate_design_score(analysis)
        score_breakdown.append({
            'category': 'System Design',
            'score': design_score,
            'max': 40
        })
        total_score += design_score
        
        # Task Queue (40)
        queue_score = self._calculate_queue_score(analysis)
        score_breakdown.append({
            'category': 'Task Queue Implementation',
            'score': queue_score,
            'max': 40
        })
        total_score += queue_score
        
        # Monitoring (20)
        monitor_score = self._calculate_monitor_score(analysis)
        score_breakdown.append({
            'category': 'Monitoring & Scalability',
            'score': monitor_score,
            'max': 20
        })
        total_score += monitor_score
        
        bonus_score = self._calculate_bonus_score(analysis)
        
        return {
            'score_breakdown': score_breakdown,
            'total_score': min(total_score, 100),
            'max_score': 100,
            'bonus_score': min(bonus_score, 15),
            'max_bonus': 15,
            'final_score': min(total_score, 100) + min(bonus_score, 15)
        }
    
    def _evaluate_general(self, analysis: Dict) -> Dict:
        """General evaluation for unknown challenges"""
        base_score = self._calculate_base_score(analysis)
        
        return {
            'score_breakdown': [{
                'category': 'Overall Implementation',
                'score': base_score,
                'max': 100
            }],
            'total_score': base_score,
            'max_score': 100,
            'bonus_score': 0,
            'max_bonus': 0,
            'final_score': base_score
        }
    
    def _calculate_bonus_score(self, analysis: Dict) -> int:
        """Calculate bonus points (0-15)"""
        score = 0
        
        # Advanced features
        docs = analysis.get('documentation', {})
        readme_content = docs.get('readme_content', '').lower()
        
        advanced_terms = ['vector', 'embedding', 'retrieval', 'cache', 'optimization', 
                         'performance', 'monitoring', 'observability']
        
        advanced_count = sum(1 for term in advanced_terms if term in readme_content)
        if advanced_count >= 3:
            score += 5
        elif advanced_count >= 2:
            score += 3
        elif advanced_count >= 1:
            score += 1
        
        # Multi-stage Docker
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            dockerfile_path = docker.get('dockerfile_path', '')
            if dockerfile_path:
                try:
                    with open(dockerfile_path, 'r') as f:
                        content = f.read()
                        if content.count('FROM ') >= 2:
                            score += 3
                except:
                    pass
        
        # Comprehensive testing
        tests = analysis.get('tests', {})
        if len(tests.get('test_files', [])) >= 10:
            score += 4
        
        # CI/CD pipeline
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci', False):
            score += 3
        
        return min(score, 15)
    
    # Helper methods for specific calculations...
    def _calculate_pipeline_score(self, analysis: Dict) -> int:
        """Calculate data pipeline score"""
        score = 0
        
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        # ETL libraries
        etl_libs = ['pandas', 'pyspark', 'airflow', 'luigi', 'prefect', 'dagster']
        found_etl = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in etl_libs))
        
        if found_etl >= 3:
            score += 15
        elif found_etl >= 2:
            score += 10
        elif found_etl >= 1:
            score += 5
        
        # Database libraries
        db_libs = ['sqlalchemy', 'psycopg2', 'pymongo', 'redis']
        found_db = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in db_libs))
        
        if found_db >= 2:
            score += 15
        elif found_db >= 1:
            score += 10
        
        # Check for pipeline structure
        structure = analysis.get('structure', {})
        pipeline_dirs = ['etl', 'pipeline', 'data', 'ingestion']
        has_pipeline_dir = any(dir_name in structure.get('key_directories', {}) for dir_name in pipeline_dirs)
        
        if has_pipeline_dir:
            score += 10
        
        return min(score, 40)
    
    def _calculate_frontend_score(self, analysis: Dict) -> int:
        """Calculate frontend score"""
        score = 0
        
        files = analysis.get('files', {})
        
        # Frontend file counts
        frontend_files = files.get('javascript_count', 0) + files.get('typescript_count', 0) + \
                        files.get('html_count', 0) + files.get('css_count', 0)
        
        if frontend_files >= 20:
            score += 15
        elif frontend_files >= 10:
            score += 10
        elif frontend_files >= 5:
            score += 5
        
        # Check for frontend frameworks
        deps = analysis.get('dependencies', {})
        node_deps = deps.get('node', [])
        
        frontend_libs = ['react', 'vue', 'angular', 'next', 'svelte', 'tailwind']
        found_frontend = sum(1 for dep in node_deps if any(lib in dep.lower() for lib in frontend_libs))
        
        if found_frontend >= 3:
            score += 20
        elif found_frontend >= 2:
            score += 15
        elif found_frontend >= 1:
            score += 10
        
        return min(score, 35)
    
    # Additional calculation methods...
    def _calculate_backend_score(self, analysis: Dict) -> int:
        """Calculate backend score"""
        score = 0
        
        files = analysis.get('files', {})
        python_files = files.get('python_count', 0)
        
        if python_files >= 15:
            score += 10
        elif python_files >= 8:
            score += 7
        elif python_files >= 3:
            score += 4
        
        # Check for backend frameworks
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        backend_libs = ['django', 'flask', 'fastapi', 'express', 'koa']
        found_backend = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in backend_libs))
        
        if found_backend >= 2:
            score += 15
        elif found_backend >= 1:
            score += 10
        
        # Check for API structure
        structure = analysis.get('structure', {})
        api_dirs = ['api', 'routes', 'endpoints', 'controllers']
        has_api_dir = any(dir_name in structure.get('key_directories', {}) for dir_name in api_dirs)
        
        if has_api_dir:
            score += 10
        
        return min(score, 35)
    
    def _get_all_files(self, analysis: Dict) -> List[str]:
        """Extract all file paths from analysis"""
        all_files = []
        structure = analysis.get('structure', {})
        
        for dir_path, dir_info in structure.items():
            if isinstance(dir_info, dict) and 'files' in dir_info:
                files = dir_info['files']
                all_files.extend([f"{dir_path}/{f}" if dir_path != '/' else f for f in files])
        
        return all_files
    
    def _get_tech_details_023(self, analysis: Dict) -> List[str]:
        """Get technical details for challenge 023"""
        details = []
        
        deps = analysis.get('dependencies', {}).get('python', [])
        
        # CV libraries
        cv_libs = ['opencv', 'pillow', 'torchvision', 'pytesseract', 'easyocr']
        found_cv = [dep for dep in deps if any(lib in dep.lower() for lib in cv_libs)]
        if found_cv:
            details.append(f"Computer Vision: {', '.join(found_cv[:3])}")
        
        # Agent frameworks
        agent_libs = ['langchain', 'langgraph', 'crewai', 'autogen']
        found_agents = [dep for dep in deps if any(lib in dep.lower() for lib in agent_libs)]
        if found_agents:
            details.append(f"Agent Frameworks: {', '.join(found_agents[:3])}")
        
        return details
    
    def _get_func_details_023(self, analysis: Dict) -> List[str]:
        """Get functionality details for challenge 023"""
        details = []
        
        tests = analysis.get('tests', {})
        if tests.get('has_test_directory', False):
            details.append(f"Tests: {len(tests.get('test_files', []))} test files")
        
        docs = analysis.get('documentation', {})
        if docs.get('has_examples', False):
            details.append("Examples provided")
        
        return details
    
    def _get_innov_details_023(self, analysis: Dict) -> List[str]:
        """Get innovation details for challenge 023"""
        details = []
        
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            details.append("Docker configuration")
        
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci', False):
            details.append("CI/CD pipeline")
        
        return details
    
    def _calculate_base_score(self, analysis: Dict) -> int:
        """Calculate base score for general evaluation"""
        score = 0
        
        # Code structure
        structure = analysis.get('structure', {})
        key_dirs = structure.get('key_directories', {})
        
        if key_dirs.get('src') or key_dirs.get('app'):
            score += 20
        
        # Documentation
        docs = analysis.get('documentation', {})
        if docs.get('has_readme', False):
            score += 15
        
        if docs.get('has_setup_instructions', False):
            score += 10
        
        # Testing
        tests = analysis.get('tests', {})
        if tests.get('has_test_directory', False):
            score += 15
        
        # Dependencies
        deps = analysis.get('dependencies', {})
        if deps.get('python') or deps.get('node'):
            score += 20
        
        # Production readiness
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            score += 10
        
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci', False):
            score += 10
        
        return min(score, 100)
    
    # Additional calculation methods for other scores...
    def _calculate_db_score(self, analysis: Dict) -> int:
        """Calculate database design score"""
        score = 0
        
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        db_libs = ['sqlalchemy', 'psycopg2', 'pymongo', 'redis', 'sqlite']
        found_db = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in db_libs))
        
        if found_db >= 3:
            score += 15
        elif found_db >= 2:
            score += 10
        elif found_db >= 1:
            score += 5
        
        # Check for database structure
        structure = analysis.get('structure', {})
        db_dirs = ['models', 'schema', 'database', 'db']
        has_db_dir = any(dir_name in structure.get('key_directories', {}) for dir_name in db_dirs)
        
        if has_db_dir:
            score += 15
        
        return min(score, 30)
    
    def _calculate_deploy_score(self, analysis: Dict) -> int:
        """Calculate deployment score"""
        score = 0
        
        docker = analysis.get('docker', {})
        if docker.get('has_dockerfile', False):
            score += 10
        
        ci_cd = analysis.get('ci_cd', {})
        if ci_cd.get('has_ci', False):
            score += 10
        
        # Check for cloud/configuration
        configs = analysis.get('configs', {})
        if len(configs) >= 3:
            score += 10
        elif len(configs) >= 2:
            score += 7
        elif len(configs) >= 1:
            score += 5
        
        return min(score, 30)
    
    def _calculate_ai_score(self, analysis: Dict) -> int:
        """Calculate AI/ML integration score"""
        score = 0
        
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        ai_libs = ['tensorflow', 'torch', 'pytorch', 'scikit', 'transformers', 'openai', 'langchain']
        found_ai = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in ai_libs))
        
        if found_ai >= 3:
            score += 20
        elif found_ai >= 2:
            score += 15
        elif found_ai >= 1:
            score += 10
        
        # Check for AI/ML structure
        structure = analysis.get('structure', {})
        ai_dirs = ['models', 'ai', 'ml', 'predict']
        has_ai_dir = any(dir_name in structure.get('key_directories', {}) for dir_name in ai_dirs)
        
        if has_ai_dir:
            score += 10
        
        return min(score, 30)
    
    def _calculate_design_score(self, analysis: Dict) -> int:
        """Calculate system design score"""
        score = 0
        
        structure = analysis.get('structure', {})
        key_dirs = structure.get('key_directories', {})
        
        # Clean architecture
        if key_dirs.get('src') and key_dirs.get('tests'):
            score += 15
        
        # Modular structure
        dir_count = len([k for k in key_dirs.keys() if k != '/'])
        if dir_count >= 8:
            score += 15
        elif dir_count >= 5:
            score += 10
        elif dir_count >= 3:
            score += 5
        
        # Configuration management
        configs = analysis.get('configs', {})
        if len(configs) >= 3:
            score += 10
        
        return min(score, 40)
    
    def _calculate_queue_score(self, analysis: Dict) -> int:
        """Calculate task queue score"""
        score = 0
        
        deps = analysis.get('dependencies', {})
        python_deps = deps.get('python', [])
        
        # Queue libraries
        queue_libs = ['celery', 'redis', 'rq', 'dramatiq']
        found_queue = sum(1 for dep in python_deps if any(lib in dep.lower() for lib in queue_libs))
        
        if found_queue >= 2:
            score += 25
        elif found_queue >= 1:
            score += 15
        
        # Check for queue structure
        structure = analysis.get('structure', {})
        queue_dirs = ['tasks', 'workers', 'queue', 'jobs']
        has_queue_dir = any(dir_name in structure.get('key_directories', {}) for dir_name in queue_dirs)
        
        if has_queue_dir:
            score += 15
        
        return min(score, 40)
    
    def _calculate_monitor_score(self, analysis: Dict) -> int:
        """Calculate monitoring score"""
        score = 0
        
        # Check for monitoring/logging
        docs = analysis.get('documentation', {})
        readme_content = docs.get('readme_content', '').lower()
        
        monitoring_terms = ['monitoring', 'logging', 'metrics', 'observability', 'dashboard']
        monitoring_count = sum(1 for term in monitoring_terms if term in readme_content)
        
        if monitoring_count >= 3:
            score += 10
        elif monitoring_count >= 2:
            score += 7
        elif monitoring_count >= 1:
            score += 5
        
        # Check for error handling
        code_quality = analysis.get('code_quality', {})
        if code_quality.get('has_error_handling', False):
            score += 10
        
        return min(score, 20)