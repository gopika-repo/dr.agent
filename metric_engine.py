# metric_engine.py - COMPLETE METRIC-BASED SCORING ENGINE
import ast
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import re
from collections import Counter

class CodeMetricsCalculator:
    """Calculate real code metrics from repository content"""
    
    def calculate_all_metrics(self, repo_path: str, file_contents: Dict[str, str]) -> Dict:
        """Calculate all metrics for a repository"""
        metrics = {
            'cyclomatic_complexity': self._calculate_cyclomatic_complexity(file_contents),
            'code_duplication': self._calculate_code_duplication(file_contents),
            'dependency_density': self._calculate_dependency_density(file_contents),
            'test_coverage': self._calculate_test_coverage(file_contents),
            'documentation_ratio': self._calculate_documentation_ratio(file_contents),
            'error_handling_density': self._calculate_error_handling_density(file_contents),
            'logging_sophistication': self._calculate_logging_sophistication(file_contents),
            'file_size_entropy': self._calculate_file_size_entropy(file_contents),
            'architecture_modularity': self._calculate_architecture_modularity(file_contents),
            'type_safety': self._calculate_type_safety(file_contents),
            'api_design_quality': self._calculate_api_design_quality(file_contents),
            'async_patterns': self._calculate_async_patterns(file_contents),
            'database_interaction': self._calculate_database_interaction(file_contents),
            'security_patterns': self._calculate_security_patterns(file_contents),
            'performance_patterns': self._calculate_performance_patterns(file_contents)
        }
        
        # Calculate component scores (0-100 scale)
        component_scores = self._calculate_component_scores(metrics, file_contents)
        
        return {
            'raw_metrics': metrics,
            'component_scores': component_scores,
            'overall_raw_score': sum(component_scores.values()) / len(component_scores)
        }
    
    def _calculate_cyclomatic_complexity(self, files: Dict[str, str]) -> float:
        """Calculate average cyclomatic complexity"""
        complexities = []
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            complexity = 1  # Base complexity
                            
                            # Count decision points
                            for subnode in ast.walk(node):
                                if isinstance(subnode, (ast.If, ast.While, ast.For)):
                                    complexity += 1
                                elif isinstance(subnode, ast.BoolOp):
                                    complexity += len(subnode.values) - 1
                                elif isinstance(subnode, (ast.ExceptHandler, ast.With)):
                                    complexity += 1
                            
                            complexities.append(complexity)
                except:
                    continue
        
        if not complexities:
            return 0
        
        avg_complexity = sum(complexities) / len(complexities)
        # Normalize: lower complexity is better (target < 10)
        return max(0, 100 - (avg_complexity * 5))
    
    def _calculate_code_duplication(self, files: Dict[str, str]) -> float:
        """Calculate code duplication percentage"""
        # Simple fingerprinting for duplication detection
        fingerprints = {}
        duplicates = 0
        total_lines = 0
        
        for file_path, content in files.items():
            if file_path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                lines = content.split('\n')
                total_lines += len(lines)
                
                # Create fingerprints for each 5-line block
                for i in range(len(lines) - 4):
                    block = '\n'.join(lines[i:i+5])
                    # Remove whitespace for comparison
                    fingerprint = re.sub(r'\s+', '', block)
                    
                    if len(fingerprint) > 20:  # Only consider substantial blocks
                        if fingerprint in fingerprints:
                            duplicates += 5
                        else:
                            fingerprints[fingerprint] = file_path
        
        if total_lines == 0:
            return 100
        
        duplication_ratio = (duplicates / total_lines) * 100
        # Lower duplication is better
        return max(0, 100 - (duplication_ratio * 2))
    
    def _calculate_dependency_density(self, files: Dict[str, str]) -> float:
        """Calculate dependency graph density"""
        imports = []
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                # Find imports
                import_lines = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
                imports.extend(import_lines)
            elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                # Find requires/imports
                import_lines = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]', content)
                imports.extend(import_lines)
        
        # Count unique imports vs total imports
        if not imports:
            return 50
        
        unique_ratio = len(set(imports)) / len(imports)
        # Healthy projects have some reuse but not too much
        return min(100, unique_ratio * 100)
    
    def _calculate_test_coverage(self, files: Dict[str, str]) -> float:
        """Approximate test coverage"""
        test_files = []
        code_files = []
        
        for file_path in files.keys():
            if 'test' in file_path.lower() or 'spec' in file_path.lower():
                test_files.append(file_path)
            elif file_path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                if not any(x in file_path.lower() for x in ['test', 'spec', 'node_modules', 'venv']):
                    code_files.append(file_path)
        
        # Calculate test ratio
        if not code_files:
            return 50
        
        test_ratio = len(test_files) / len(code_files)
        
        # Check for test content quality
        test_content_score = 0
        for test_file in test_files[:5]:  # Sample first 5 test files
            if test_file in files:
                content = files[test_file]
                assertions = len(re.findall(r'assert|expect|should', content, re.IGNORECASE))
                if assertions > 0:
                    test_content_score += min(20, assertions)
        
        # Combine ratio and quality
        base_score = min(100, test_ratio * 200)  # 50% test ratio gives 100
        quality_bonus = min(20, test_content_score / len(test_files)) if test_files else 0
        
        return min(100, base_score + quality_bonus)
    
    def _calculate_documentation_ratio(self, files: Dict[str, str]) -> float:
        """Calculate documentation to code ratio"""
        doc_lines = 0
        code_lines = 0
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                lines = content.split('\n')
                code_lines += len(lines)
                
                # Count docstrings
                in_docstring = False
                for line in lines:
                    if '"""' in line or "'''" in line:
                        in_docstring = not in_docstring
                        doc_lines += 1
                    elif in_docstring:
                        doc_lines += 1
                    elif line.strip().startswith('#'):
                        doc_lines += 1
            elif file_path.lower().endswith(('readme.md', 'readme.txt')):
                doc_lines += len(content.split('\n')) * 2  # Weight READMEs higher
        
        if code_lines == 0:
            return 50
        
        ratio = (doc_lines / code_lines) * 100
        # Good documentation is 15-30% of code
        if ratio < 5:
            return 20
        elif ratio < 10:
            return 50
        elif ratio < 20:
            return 80
        elif ratio < 30:
            return 90
        else:
            return 100
    
    def _calculate_error_handling_density(self, files: Dict[str, str]) -> float:
        """Calculate error handling density"""
        total_ops = 0
        error_handlers = 0
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    operations = 0
                    handlers = 0
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Call, ast.Assign, ast.Attribute)):
                            operations += 1
                        elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                            handlers += 1
                    
                    total_ops += operations
                    error_handlers += handlers
                except:
                    continue
            elif file_path.endswith(('.js', '.ts')):
                # Simple JS error handling detection
                handlers = len(re.findall(r'try|catch|finally', content, re.IGNORECASE))
                operations = len(re.findall(r'function|=>|return|\.\w+\(', content))
                
                total_ops += operations
                error_handlers += handlers
        
        if total_ops == 0:
            return 50
        
        density = (error_handlers / total_ops) * 100
        # Good error handling density is 5-15%
        return min(100, density * 5)
    
    def _calculate_logging_sophistication(self, files: Dict[str, str]) -> float:
        """Calculate logging sophistication score"""
        score = 0
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                # Check for logging imports
                if 'import logging' in content or 'from logging' in content:
                    score += 10
                
                # Check for different log levels
                levels = 0
                if 'logging.debug' in content: levels += 1
                if 'logging.info' in content: levels += 1
                if 'logging.warning' in content: levels += 1
                if 'logging.error' in content: levels += 1
                if 'logging.critical' in content: levels += 1
                
                score += levels * 5
                
                # Check for structured logging
                if 'extra=' in content or 'exc_info=' in content:
                    score += 15
                
                # Check for log configuration
                if 'logging.basicConfig' in content or 'logging.config' in content:
                    score += 10
            
            elif file_path.endswith(('.js', '.ts')):
                if 'console.log' in content: score += 2
                if 'console.error' in content: score += 2
                if 'console.warn' in content: score += 2
                if 'console.info' in content: score += 2
                if 'console.debug' in content: score += 2
                
                # Check for logging libraries
                if 'winston' in content or 'pino' in content or 'bunyan' in content:
                    score += 15
        
        return min(100, score)
    
    def _calculate_file_size_entropy(self, files: Dict[str, str]) -> float:
        """Calculate file size distribution entropy"""
        sizes = []
        
        for file_path, content in files.items():
            if file_path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                sizes.append(len(content.split('\n')))
        
        if not sizes:
            return 50
        
        # Calculate entropy of size distribution
        # Smaller files are better for maintainability
        avg_size = sum(sizes) / len(sizes)
        max_size = max(sizes)
        
        # Penalize very large files
        large_file_penalty = 0
        for size in sizes:
            if size > 500:
                large_file_penalty += (size - 500) / 100
        
        # Calculate size consistency
        variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
        std_dev = math.sqrt(variance)
        
        # Good if files are reasonably sized and consistent
        consistency_score = 100 - min(100, std_dev / 10)
        size_score = 100 - min(100, large_file_penalty)
        
        return (consistency_score + size_score) / 2
    
    def _calculate_architecture_modularity(self, files: Dict[str, str]) -> float:
        """Calculate architecture modularity index"""
        modules = set()
        imports_between = 0
        
        # Group files into modules (by directory)
        for file_path in files.keys():
            parts = Path(file_path).parts
            if len(parts) > 1:
                module = parts[0]
                modules.add(module)
        
        # Count cross-module imports
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                # Find imports
                imports = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
                
                file_module = Path(file_path).parts[0] if Path(file_path).parts else 'root'
                
                for imp in imports:
                    # Check if import is from different module
                    for module in modules:
                        if imp.startswith(module) and module != file_module:
                            imports_between += 1
        
        if not modules:
            return 50
        
        # High modularity: few cross-module imports
        max_allowed = len(modules) * 5
        if imports_between > max_allowed:
            return max(0, 100 - ((imports_between - max_allowed) * 2))
        else:
            return 100
    
    def _calculate_type_safety(self, files: Dict[str, str]) -> float:
        """Calculate type safety score"""
        score = 0
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                # Check for type hints
                type_hints = len(re.findall(r':\s*\w+\s*=', content))  # Variable hints
                type_hints += len(re.findall(r'->\s*\w+', content))    # Return hints
                
                if type_hints > 0:
                    score += min(20, type_hints)
                
                # Check for type checking
                if 'mypy' in content or 'typing' in content:
                    score += 10
            
            elif file_path.endswith(('.ts', '.tsx')):
                score += 50  # TypeScript is type-safe by default
            elif file_path.endswith('.js'):
                # Check for JSDoc
                jsdoc = len(re.findall(r'@\w+', content))
                score += min(20, jsdoc)
        
        return min(100, score)
    
    def _calculate_api_design_quality(self, files: Dict[str, str]) -> float:
        """Calculate API design quality"""
        score = 0
        
        api_files = [f for f in files.keys() if 'api' in f.lower() or 'route' in f.lower()]
        
        for api_file in api_files[:5]:  # Sample first 5
            if api_file in files:
                content = files[api_file]
                
                # Check for HTTP methods
                methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
                found_methods = sum(1 for m in methods if m in content)
                score += found_methods * 5
                
                # Check for status codes
                status_codes = len(re.findall(r'status|code|HTTP_\w+', content))
                score += min(10, status_codes)
                
                # Check for validation
                if 'validate' in content.lower() or 'schema' in content.lower():
                    score += 10
                
                # Check for error responses
                if 'error' in content.lower() and 'return' in content.lower():
                    score += 10
        
        return min(100, score)
    
    def _calculate_async_patterns(self, files: Dict[str, str]) -> float:
        """Calculate async pattern usage score"""
        score = 0
        
        for file_path, content in files.items():
            if file_path.endswith('.py'):
                # Check for async/await
                if 'async def' in content:
                    score += 10
                if 'await' in content:
                    score += 5
                
                # Check for asyncio
                if 'asyncio' in content:
                    score += 10
            
            elif file_path.endswith(('.js', '.ts')):
                if 'async' in content and 'function' in content:
                    score += 10
                if 'await' in content:
                    score += 5
                if 'Promise' in content:
                    score += 10
        
        return min(100, score)
    
    def _calculate_database_interaction(self, files: Dict[str, str]) -> float:
        """Calculate database interaction quality"""
        score = 0
        
        db_files = [f for f in files.keys() if 'model' in f.lower() or 'db' in f.lower() or 'database' in f.lower()]
        
        for db_file in db_files[:5]:
            if db_file in files:
                content = files[db_file]
                
                # Check for ORM usage
                if 'sqlalchemy' in content or 'django.db' in content or 'mongoose' in content:
                    score += 20
                
                # Check for connection management
                if 'connect' in content and 'close' in content:
                    score += 15
                
                # Check for query optimization
                if 'select_related' in content or 'prefetch_related' in content or 'index' in content:
                    score += 15
                
                # Check for migrations
                if 'migration' in content.lower():
                    score += 10
        
        return min(100, score)
    
    def _calculate_security_patterns(self, files: Dict[str, str]) -> float:
        """Calculate security pattern score"""
        score = 0
        
        for file_path, content in files.items():
            # Check for security headers
            if 'helmet' in content or 'cors' in content:
                score += 10
            
            # Check for authentication
            if 'authenticat' in content.lower() or 'login' in content.lower():
                score += 10
            
            # Check for password hashing
            if 'bcrypt' in content or 'hash' in content or 'argon2' in content:
                score += 15
            
            # Check for JWT
            if 'jwt' in content.lower() or 'json web token' in content.lower():
                score += 10
            
            # Check for input validation
            if 'sanitize' in content or 'validate' in content:
                score += 10
            
            # Check for SQL injection prevention
            if 'escape' in content or 'parameterized' in content:
                score += 15
            
            # Check for environment variables
            if 'os.environ' in content or 'process.env' in content:
                score += 5
        
        return min(100, score)
    
    def _calculate_performance_patterns(self, files: Dict[str, str]) -> float:
        """Calculate performance pattern score"""
        score = 0
        
        for file_path, content in files.items():
            # Check for caching
            if 'cache' in content.lower():
                score += 10
            
            # Check for connection pooling
            if 'pool' in content.lower():
                score += 10
            
            # Check for lazy loading
            if 'lazy' in content.lower():
                score += 5
            
            # Check for pagination
            if 'paginate' in content.lower() or 'limit' in content.lower() and 'offset' in content.lower():
                score += 10
            
            # Check for batch processing
            if 'batch' in content.lower():
                score += 5
            
            # Check for indexing
            if 'index' in content.lower() and 'create' in content.lower():
                score += 10
        
        return min(100, score)
    
    def _calculate_component_scores(self, metrics: Dict, files: Dict[str, str]) -> Dict[str, float]:
        """Calculate component scores (0-100) for different evaluation areas"""
        
        # Map metrics to component scores based on challenge criteria
        component_scores = {
            'code_quality': (
                metrics['cyclomatic_complexity'] * 0.3 +
                metrics['code_duplication'] * 0.2 +
                metrics['error_handling_density'] * 0.25 +
                metrics['logging_sophistication'] * 0.25
            ),
            
            'architecture': (
                metrics['architecture_modularity'] * 0.4 +
                metrics['dependency_density'] * 0.3 +
                metrics['file_size_entropy'] * 0.3
            ),
            
            'documentation': (
                metrics['documentation_ratio'] * 0.7 +
                metrics['type_safety'] * 0.3
            ),
            
            'testing': metrics['test_coverage'],
            
            'production_readiness': (
                metrics['security_patterns'] * 0.3 +
                metrics['performance_patterns'] * 0.3 +
                metrics['database_interaction'] * 0.2 +
                metrics['async_patterns'] * 0.2
            ),
            
            'api_design': metrics['api_design_quality']
        }
        
        return component_scores


class ExpectationModel:
    """Model expectations per experience level per metric"""
    
    def __init__(self):
        # Define expected scores for each metric by experience level (0-100)
        self.expected_metrics = {
            '1st_year': {
                'cyclomatic_complexity': 60,
                'code_duplication': 60,
                'dependency_density': 50,
                'test_coverage': 30,
                'documentation_ratio': 40,
                'error_handling_density': 40,
                'logging_sophistication': 30,
                'file_size_entropy': 50,
                'architecture_modularity': 40,
                'type_safety': 30,
                'api_design_quality': 30,
                'async_patterns': 20,
                'database_interaction': 30,
                'security_patterns': 30,
                'performance_patterns': 30
            },
            '2nd_year': {
                'cyclomatic_complexity': 65,
                'code_duplication': 65,
                'dependency_density': 55,
                'test_coverage': 40,
                'documentation_ratio': 45,
                'error_handling_density': 45,
                'logging_sophistication': 40,
                'file_size_entropy': 55,
                'architecture_modularity': 45,
                'type_safety': 40,
                'api_design_quality': 40,
                'async_patterns': 30,
                'database_interaction': 40,
                'security_patterns': 40,
                'performance_patterns': 40
            },
            '3rd_year': {
                'cyclomatic_complexity': 70,
                'code_duplication': 70,
                'dependency_density': 60,
                'test_coverage': 50,
                'documentation_ratio': 55,
                'error_handling_density': 55,
                'logging_sophistication': 50,
                'file_size_entropy': 65,
                'architecture_modularity': 55,
                'type_safety': 50,
                'api_design_quality': 50,
                'async_patterns': 40,
                'database_interaction': 50,
                'security_patterns': 50,
                'performance_patterns': 50
            },
            '4th_year': {
                'cyclomatic_complexity': 75,
                'code_duplication': 75,
                'dependency_density': 65,
                'test_coverage': 60,
                'documentation_ratio': 65,
                'error_handling_density': 65,
                'logging_sophistication': 60,
                'file_size_entropy': 75,
                'architecture_modularity': 65,
                'type_safety': 60,
                'api_design_quality': 60,
                'async_patterns': 50,
                'database_interaction': 60,
                'security_patterns': 60,
                'performance_patterns': 60
            },
            'fresher': {
                'cyclomatic_complexity': 68,
                'code_duplication': 68,
                'dependency_density': 58,
                'test_coverage': 45,
                'documentation_ratio': 50,
                'error_handling_density': 50,
                'logging_sophistication': 45,
                'file_size_entropy': 60,
                'architecture_modularity': 50,
                'type_safety': 45,
                'api_design_quality': 45,
                'async_patterns': 35,
                'database_interaction': 45,
                'security_patterns': 45,
                'performance_patterns': 45
            },
            'experienced_0_2': {
                'cyclomatic_complexity': 80,
                'code_duplication': 80,
                'dependency_density': 75,
                'test_coverage': 70,
                'documentation_ratio': 75,
                'error_handling_density': 75,
                'logging_sophistication': 70,
                'file_size_entropy': 85,
                'architecture_modularity': 75,
                'type_safety': 70,
                'api_design_quality': 70,
                'async_patterns': 60,
                'database_interaction': 70,
                'security_patterns': 70,
                'performance_patterns': 70
            },
            'senior': {
                'cyclomatic_complexity': 85,
                'code_duplication': 85,
                'dependency_density': 80,
                'test_coverage': 80,
                'documentation_ratio': 85,
                'error_handling_density': 85,
                'logging_sophistication': 80,
                'file_size_entropy': 90,
                'architecture_modularity': 85,
                'type_safety': 80,
                'api_design_quality': 80,
                'async_patterns': 70,
                'database_interaction': 80,
                'security_patterns': 80,
                'performance_patterns': 80
            }
        }
        
        # Penalty and reward weights (strictness increases with experience)
        self.penalty_weights = {
            '1st_year': 0.5,
            '2nd_year': 0.6,
            '3rd_year': 0.7,
            '4th_year': 0.8,
            'fresher': 0.65,
            'experienced_0_2': 0.9,
            'senior': 1.0
        }
        
        self.reward_weights = {
            '1st_year': 1.5,
            '2nd_year': 1.3,
            '3rd_year': 1.1,
            '4th_year': 1.0,
            'fresher': 1.2,
            'experienced_0_2': 0.9,
            'senior': 0.8
        }
    
    def adjust_scores(self, raw_metrics: Dict[str, float], experience_level: str) -> Dict:
        """
        Adjust scores based on experience expectations
        adjusted = actual - max(0, expected - actual) * penalty + max(0, actual - expected) * reward
        """
        
        expected = self.expected_metrics.get(experience_level, self.expected_metrics['fresher'])
        penalty_weight = self.penalty_weights.get(experience_level, 0.7)
        reward_weight = self.reward_weights.get(experience_level, 1.0)
        
        adjusted_metrics = {}
        gaps = {}
        
        for metric, actual in raw_metrics.items():
            exp = expected.get(metric, 50)
            
            # Calculate gap
            if actual < exp:
                # Below expectation: penalty
                gap = exp - actual
                penalty = gap * penalty_weight
                adjusted = actual - penalty
                gaps[metric] = {
                    'expected': exp,
                    'actual': actual,
                    'gap': -gap,
                    'adjustment': -penalty,
                    'type': 'penalty'
                }
            else:
                # Above expectation: reward
                gap = actual - exp
                reward = gap * reward_weight
                adjusted = actual + reward
                gaps[metric] = {
                    'expected': exp,
                    'actual': actual,
                    'gap': gap,
                    'adjustment': reward,
                    'type': 'reward'
                }
            
            adjusted_metrics[metric] = max(0, min(100, adjusted))
        
        # Calculate component scores from adjusted metrics
        adjusted_components = {
            'code_quality': (
                adjusted_metrics['cyclomatic_complexity'] * 0.3 +
                adjusted_metrics['code_duplication'] * 0.2 +
                adjusted_metrics['error_handling_density'] * 0.25 +
                adjusted_metrics['logging_sophistication'] * 0.25
            ),
            'architecture': (
                adjusted_metrics['architecture_modularity'] * 0.4 +
                adjusted_metrics['dependency_density'] * 0.3 +
                adjusted_metrics['file_size_entropy'] * 0.3
            ),
            'documentation': (
                adjusted_metrics['documentation_ratio'] * 0.7 +
                adjusted_metrics['type_safety'] * 0.3
            ),
            'testing': adjusted_metrics['test_coverage'],
            'production_readiness': (
                adjusted_metrics['security_patterns'] * 0.3 +
                adjusted_metrics['performance_patterns'] * 0.3 +
                adjusted_metrics['database_interaction'] * 0.2 +
                adjusted_metrics['async_patterns'] * 0.2
            ),
            'api_design': adjusted_metrics['api_design_quality']
        }
        
        overall_score = sum(adjusted_components.values()) / len(adjusted_components)
        
        return {
            'raw_metrics': raw_metrics,
            'expected_metrics': expected,
            'adjusted_metrics': adjusted_metrics,
            'gaps': gaps,
            'component_scores': adjusted_components,
            'overall_score': overall_score,
            'experience_level': experience_level,
            'penalty_weight': penalty_weight,
            'reward_weight': reward_weight
        }