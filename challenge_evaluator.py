# challenge_evaluator.py - CHALLENGE-SPECIFIC EVALUATION
from typing import Dict, List, Any
import re

class ChallengeEvaluator:
    """Evaluate repositories against specific challenge criteria"""
    
    def __init__(self, challenge_data: Dict):
        self.challenge = challenge_data
        self.challenge_id = challenge_data.get('_id', '')
    
    def evaluate(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """Evaluate against challenge-specific criteria"""
        
        evaluators = {
            'challenge_023': self._evaluate_challenge_023,
            'challenge_024': self._evaluate_challenge_024,
            'challenge_025': self._evaluate_challenge_025,
            'challenge_026': self._evaluate_challenge_026,
            'challenge_027': self._evaluate_challenge_027
        }
        
        evaluator = evaluators.get(self.challenge_id, self._evaluate_general)
        return evaluator(metrics, adjusted_scores)
    
    def _evaluate_challenge_023(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """AI Agents Builder System - Multi-Modal Document Intelligence"""
        
        # Extract relevant metrics
        component_scores = adjusted_scores.get('component_scores', {})
        raw_metrics = adjusted_scores.get('raw_metrics', {})
        
        # A. Multi-Modal Implementation (60 points)
        computer_vision_score = (
            raw_metrics.get('ai_ml_indicators', 0) * 0.4 +
            raw_metrics.get('type_safety', 0) * 0.2 +
            component_scores.get('code_quality', 0) * 0.4
        ) * 0.2  # 20 points max
        
        multi_agent_score = (
            raw_metrics.get('async_patterns', 0) * 0.3 +
            component_scores.get('architecture', 0) * 0.4 +
            raw_metrics.get('dependency_density', 0) * 0.3
        ) * 0.2  # 20 points max
        
        system_engineering_score = (
            component_scores.get('code_quality', 0) * 0.3 +
            component_scores.get('architecture', 0) * 0.3 +
            raw_metrics.get('file_size_entropy', 0) * 0.2 +
            raw_metrics.get('documentation_ratio', 0) * 0.2
        ) * 0.2  # 20 points max
        
        multi_modal_total = computer_vision_score + multi_agent_score + system_engineering_score
        
        # B. Functionality & Results (25 points)
        accuracy_score = (
            raw_metrics.get('test_coverage', 0) * 0.3 +
            raw_metrics.get('error_handling_density', 0) * 0.4 +
            component_scores.get('testing', 0) * 0.3
        ) * 0.15  # 15 points max
        
        confidence_demo_score = (
            raw_metrics.get('documentation_ratio', 0) * 0.5 +
            raw_metrics.get('logging_sophistication', 0) * 0.5
        ) * 0.1  # 10 points max
        
        functionality_total = accuracy_score + confidence_demo_score
        
        # C. Innovation & Practicality (15 points)
        creative_solutions = (
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('security_patterns', 0) * 0.3
        ) * 0.08  # 8 points max
        
        production_readiness = (
            raw_metrics.get('database_interaction', 0) * 0.2 +
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.3 +
            raw_metrics.get('async_patterns', 0) * 0.2
        ) * 0.07  # 7 points max
        
        innovation_total = creative_solutions + production_readiness
        
        # Calculate total (max 100)
        total_score = multi_modal_total + functionality_total + innovation_total
        
        return {
            'challenge_id': self.challenge_id,
            'scores': {
                'multi_modal_implementation': {
                    'computer_vision_quality': round(computer_vision_score, 1),
                    'multi_agent_system': round(multi_agent_score, 1),
                    'system_engineering': round(system_engineering_score, 1),
                    'total': round(multi_modal_total, 1),
                    'max': 60
                },
                'functionality_results': {
                    'accuracy': round(accuracy_score, 1),
                    'confidence_demo': round(confidence_demo_score, 1),
                    'total': round(functionality_total, 1),
                    'max': 25
                },
                'innovation_practicality': {
                    'creative_solutions': round(creative_solutions, 1),
                    'production_readiness': round(production_readiness, 1),
                    'total': round(innovation_total, 1),
                    'max': 15
                }
            },
            'total_score': round(total_score, 1),
            'max_score': 100
        }
    
    def _evaluate_challenge_024(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """AI Healthcare Agent System - RAG + Agents"""
        
        component_scores = adjusted_scores.get('component_scores', {})
        raw_metrics = adjusted_scores.get('raw_metrics', {})
        
        # A. Technical Implementation (60 points)
        rag_pipeline_quality = (
            raw_metrics.get('database_interaction', 0) * 0.4 +
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            component_scores.get('architecture', 0) * 0.3
        ) * 0.2  # 20 points max
        
        agent_development = (
            raw_metrics.get('async_patterns', 0) * 0.4 +
            component_scores.get('code_quality', 0) * 0.3 +
            raw_metrics.get('error_handling_density', 0) * 0.3
        ) * 0.2  # 20 points max
        
        evaluation_framework = (
            raw_metrics.get('test_coverage', 0) * 0.6 +
            raw_metrics.get('logging_sophistication', 0) * 0.4
        ) * 0.1  # 10 points max
        
        deployment_infrastructure = (
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('database_interaction', 0) * 0.3
        ) * 0.1  # 10 points max
        
        technical_total = rag_pipeline_quality + agent_development + evaluation_framework + deployment_infrastructure
        
        # B. Functionality & Results (25 points)
        system_performance = (
            raw_metrics.get('performance_patterns', 0) * 0.5 +
            raw_metrics.get('error_handling_density', 0) * 0.3 +
            raw_metrics.get('logging_sophistication', 0) * 0.2
        ) * 0.15  # 15 points max
        
        demo_documentation = (
            raw_metrics.get('documentation_ratio', 0) * 0.7 +
            raw_metrics.get('type_safety', 0) * 0.3
        ) * 0.1  # 10 points max
        
        functionality_total = system_performance + demo_documentation
        
        # C. Innovation & Best Practices (15 points)
        creative_solutions = (
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            raw_metrics.get('async_patterns', 0) * 0.4 +
            raw_metrics.get('dependency_density', 0) * 0.3
        ) * 0.08  # 8 points max
        
        production_readiness = (
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('test_coverage', 0) * 0.3
        ) * 0.07  # 7 points max
        
        innovation_total = creative_solutions + production_readiness
        
        total_score = technical_total + functionality_total + innovation_total
        
        return {
            'challenge_id': self.challenge_id,
            'scores': {
                'technical_implementation': {
                    'rag_pipeline_quality': round(rag_pipeline_quality, 1),
                    'agent_development': round(agent_development, 1),
                    'evaluation_framework': round(evaluation_framework, 1),
                    'deployment_infrastructure': round(deployment_infrastructure, 1),
                    'total': round(technical_total, 1),
                    'max': 60
                },
                'functionality_results': {
                    'system_performance': round(system_performance, 1),
                    'demo_documentation': round(demo_documentation, 1),
                    'total': round(functionality_total, 1),
                    'max': 25
                },
                'innovation_practices': {
                    'creative_solutions': round(creative_solutions, 1),
                    'production_readiness': round(production_readiness, 1),
                    'total': round(innovation_total, 1),
                    'max': 15
                }
            },
            'total_score': round(total_score, 1),
            'max_score': 100
        }
    
    def _evaluate_challenge_025(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """Healthcare Supply Chain Analytics - Data Pipeline"""
        
        component_scores = adjusted_scores.get('component_scores', {})
        raw_metrics = adjusted_scores.get('raw_metrics', {})
        
        # A. Technical Implementation (60 points)
        etl_pipeline_quality = (
            raw_metrics.get('database_interaction', 0) * 0.4 +
            component_scores.get('architecture', 0) * 0.3 +
            raw_metrics.get('dependency_density', 0) * 0.3
        ) * 0.2  # 20 points max
        
        database_design = (
            raw_metrics.get('database_interaction', 0) * 0.6 +
            raw_metrics.get('type_safety', 0) * 0.2 +
            raw_metrics.get('file_size_entropy', 0) * 0.2
        ) * 0.15  # 15 points max
        
        pipeline_architecture = (
            component_scores.get('architecture', 0) * 0.4 +
            raw_metrics.get('error_handling_density', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.3
        ) * 0.15  # 15 points max
        
        cloud_deployment = (
            raw_metrics.get('security_patterns', 0) * 0.4 +
            raw_metrics.get('performance_patterns', 0) * 0.3 +
            raw_metrics.get('logging_sophistication', 0) * 0.3
        ) * 0.1  # 10 points max
        
        technical_total = etl_pipeline_quality + database_design + pipeline_architecture + cloud_deployment
        
        # B. Functionality & Results (25 points)
        data_processing_accuracy = (
            raw_metrics.get('test_coverage', 0) * 0.4 +
            raw_metrics.get('error_handling_density', 0) * 0.4 +
            raw_metrics.get('logging_sophistication', 0) * 0.2
        ) * 0.15  # 15 points max
        
        demo_documentation = (
            raw_metrics.get('documentation_ratio', 0) * 0.7 +
            component_scores.get('documentation', 0) * 0.3
        ) * 0.1  # 10 points max
        
        functionality_total = data_processing_accuracy + demo_documentation
        
        # C. Innovation & Best Practices (15 points)
        creative_solutions = (
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            raw_metrics.get('async_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4
        ) * 0.08  # 8 points max
        
        production_readiness = (
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('error_handling_density', 0) * 0.3
        ) * 0.07  # 7 points max
        
        innovation_total = creative_solutions + production_readiness
        
        total_score = technical_total + functionality_total + innovation_total
        
        return {
            'challenge_id': self.challenge_id,
            'scores': {
                'technical_implementation': {
                    'etl_pipeline_quality': round(etl_pipeline_quality, 1),
                    'database_design': round(database_design, 1),
                    'pipeline_architecture': round(pipeline_architecture, 1),
                    'cloud_deployment': round(cloud_deployment, 1),
                    'total': round(technical_total, 1),
                    'max': 60
                },
                'functionality_results': {
                    'data_processing_accuracy': round(data_processing_accuracy, 1),
                    'demo_documentation': round(demo_documentation, 1),
                    'total': round(functionality_total, 1),
                    'max': 25
                },
                'innovation_practices': {
                    'creative_solutions': round(creative_solutions, 1),
                    'production_readiness': round(production_readiness, 1),
                    'total': round(innovation_total, 1),
                    'max': 15
                }
            },
            'total_score': round(total_score, 1),
            'max_score': 100
        }
    
    def _evaluate_challenge_026(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """AI-Powered Healthcare Supply Chain Platform - Full Stack + AI"""
        
        component_scores = adjusted_scores.get('component_scores', {})
        raw_metrics = adjusted_scores.get('raw_metrics', {})
        
        # A. Technical Implementation (60 points)
        frontend_development = (
            raw_metrics.get('file_size_entropy', 0) * 0.3 +
            component_scores.get('architecture', 0) * 0.3 +
            raw_metrics.get('api_design_quality', 0) * 0.4
        ) * 0.2  # 20 points max
        
        backend_development = (
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            raw_metrics.get('database_interaction', 0) * 0.3 +
            raw_metrics.get('security_patterns', 0) * 0.4
        ) * 0.15  # 15 points max
        
        ai_ml_integration = (
            raw_metrics.get('type_safety', 0) * 0.2 +
            raw_metrics.get('async_patterns', 0) * 0.3 +
            component_scores.get('code_quality', 0) * 0.5
        ) * 0.15  # 15 points max
        
        deployment_infrastructure = (
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('logging_sophistication', 0) * 0.3
        ) * 0.1  # 10 points max
        
        technical_total = frontend_development + backend_development + ai_ml_integration + deployment_infrastructure
        
        # B. Functionality & Results (25 points)
        system_performance = (
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('error_handling_density', 0) * 0.3 +
            raw_metrics.get('async_patterns', 0) * 0.3
        ) * 0.15  # 15 points max
        
        demo_documentation = (
            raw_metrics.get('documentation_ratio', 0) * 0.7 +
            component_scores.get('documentation', 0) * 0.3
        ) * 0.1  # 10 points max
        
        functionality_total = system_performance + demo_documentation
        
        # C. Innovation & Best Practices (15 points)
        creative_solutions = (
            raw_metrics.get('api_design_quality', 0) * 0.4 +
            raw_metrics.get('async_patterns', 0) * 0.3 +
            raw_metrics.get('dependency_density', 0) * 0.3
        ) * 0.08  # 8 points max
        
        production_readiness = (
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('test_coverage', 0) * 0.3
        ) * 0.07  # 7 points max
        
        innovation_total = creative_solutions + production_readiness
        
        total_score = technical_total + functionality_total + innovation_total
        
        return {
            'challenge_id': self.challenge_id,
            'scores': {
                'technical_implementation': {
                    'frontend_development': round(frontend_development, 1),
                    'backend_development': round(backend_development, 1),
                    'ai_ml_integration': round(ai_ml_integration, 1),
                    'deployment_infrastructure': round(deployment_infrastructure, 1),
                    'total': round(technical_total, 1),
                    'max': 60
                },
                'functionality_results': {
                    'system_performance': round(system_performance, 1),
                    'demo_documentation': round(demo_documentation, 1),
                    'total': round(functionality_total, 1),
                    'max': 25
                },
                'innovation_practices': {
                    'creative_solutions': round(creative_solutions, 1),
                    'production_readiness': round(production_readiness, 1),
                    'total': round(innovation_total, 1),
                    'max': 15
                }
            },
            'total_score': round(total_score, 1),
            'max_score': 100
        }
    
    def _evaluate_challenge_027(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """Enterprise Healthcare Inventory Management - Full Stack + Task Queues"""
        
        component_scores = adjusted_scores.get('component_scores', {})
        raw_metrics = adjusted_scores.get('raw_metrics', {})
        
        # A. Technical Implementation (60 points)
        frontend_development = (
            raw_metrics.get('file_size_entropy', 0) * 0.3 +
            component_scores.get('architecture', 0) * 0.3 +
            raw_metrics.get('api_design_quality', 0) * 0.4
        ) * 0.2  # 20 points max
        
        backend_development = (
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            raw_metrics.get('database_interaction', 0) * 0.3 +
            raw_metrics.get('security_patterns', 0) * 0.4
        ) * 0.15  # 15 points max
        
        database_design = (
            raw_metrics.get('database_interaction', 0) * 0.5 +
            raw_metrics.get('type_safety', 0) * 0.2 +
            component_scores.get('architecture', 0) * 0.3
        ) * 0.1  # 10 points max
        
        task_queue_implementation = (
            raw_metrics.get('async_patterns', 0) * 0.5 +
            raw_metrics.get('performance_patterns', 0) * 0.3 +
            raw_metrics.get('error_handling_density', 0) * 0.2
        ) * 0.1  # 10 points max
        
        deployment_infrastructure = (
            raw_metrics.get('security_patterns', 0) * 0.4 +
            raw_metrics.get('performance_patterns', 0) * 0.3 +
            raw_metrics.get('logging_sophistication', 0) * 0.3
        ) * 0.05  # 5 points max
        
        technical_total = frontend_development + backend_development + database_design + task_queue_implementation + deployment_infrastructure
        
        # B. Functionality & Results (25 points)
        system_performance = (
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('async_patterns', 0) * 0.3 +
            raw_metrics.get('error_handling_density', 0) * 0.3
        ) * 0.15  # 15 points max
        
        demo_documentation = (
            raw_metrics.get('documentation_ratio', 0) * 0.7 +
            component_scores.get('documentation', 0) * 0.3
        ) * 0.1  # 10 points max
        
        functionality_total = system_performance + demo_documentation
        
        # C. Innovation & Best Practices (15 points)
        creative_solutions = (
            raw_metrics.get('api_design_quality', 0) * 0.3 +
            raw_metrics.get('async_patterns', 0) * 0.4 +
            raw_metrics.get('dependency_density', 0) * 0.3
        ) * 0.08  # 8 points max
        
        production_readiness = (
            raw_metrics.get('security_patterns', 0) * 0.3 +
            raw_metrics.get('performance_patterns', 0) * 0.4 +
            raw_metrics.get('test_coverage', 0) * 0.3
        ) * 0.07  # 7 points max
        
        innovation_total = creative_solutions + production_readiness
        
        total_score = technical_total + functionality_total + innovation_total
        
        return {
            'challenge_id': self.challenge_id,
            'scores': {
                'technical_implementation': {
                    'frontend_development': round(frontend_development, 1),
                    'backend_development': round(backend_development, 1),
                    'database_design': round(database_design, 1),
                    'task_queue_implementation': round(task_queue_implementation, 1),
                    'deployment_infrastructure': round(deployment_infrastructure, 1),
                    'total': round(technical_total, 1),
                    'max': 60
                },
                'functionality_results': {
                    'system_performance': round(system_performance, 1),
                    'demo_documentation': round(demo_documentation, 1),
                    'total': round(functionality_total, 1),
                    'max': 25
                },
                'innovation_practices': {
                    'creative_solutions': round(creative_solutions, 1),
                    'production_readiness': round(production_readiness, 1),
                    'total': round(innovation_total, 1),
                    'max': 15
                }
            },
            'total_score': round(total_score, 1),
            'max_score': 100
        }
    
    def _evaluate_general(self, metrics: Dict, adjusted_scores: Dict) -> Dict:
        """General evaluation for unknown challenges"""
        
        component_scores = adjusted_scores.get('component_scores', {})
        
        total_score = sum(component_scores.values()) / len(component_scores)
        
        return {
            'challenge_id': self.challenge_id,
            'scores': {
                'overall': {
                    'code_quality': round(component_scores.get('code_quality', 0), 1),
                    'architecture': round(component_scores.get('architecture', 0), 1),
                    'documentation': round(component_scores.get('documentation', 0), 1),
                    'testing': round(component_scores.get('testing', 0), 1),
                    'production_readiness': round(component_scores.get('production_readiness', 0), 1),
                    'api_design': round(component_scores.get('api_design', 0), 1),
                    'total': round(total_score, 1),
                    'max': 100
                }
            },
            'total_score': round(total_score, 1),
            'max_score': 100
        }