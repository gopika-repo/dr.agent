# utils/file_processor.py - Enhanced
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import yaml
import ast

class FileProcessor:
    @staticmethod
    def detect_file_type(file_path: Path) -> str:
        """Enhanced file type detection"""
        ext = file_path.suffix.lower()
        
        file_types = {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript',
            '.ts': 'typescript', '.tsx': 'typescript',
            '.html': 'html', '.htm': 'html',
            '.css': 'css', '.scss': 'css', '.less': 'css',
            '.json': 'json',
            '.yaml': 'yaml', '.yml': 'yaml',
            '.toml': 'toml',
            '.md': 'markdown',
            '.txt': 'text', '.log': 'text',
            '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp',
            '.go': 'go', '.rs': 'rust', '.rb': 'ruby',
            '.sql': 'sql',
            '.sh': 'shell', '.bash': 'shell',
            '.dockerfile': 'docker', 'dockerfile': 'docker',
            '.xml': 'xml', '.csv': 'csv'
        }
        
        return file_types.get(ext, 'other')
    
    @staticmethod
    def analyze_python_file(content: str) -> Dict:
        """Enhanced Python file analysis"""
        analysis = {
            'imports': [],
            'functions': [],
            'classes': [],
            'async_functions': [],
            'decorators': [],
            'has_error_handling': False,
            'has_logging': False,
            'has_type_hints': False,
            'has_docstrings': False,
            'line_count': len(content.split('\n')),
            'complexity_indicators': [],
            'dependency_patterns': []
        }
        
        try:
            # Try to parse with AST for better accuracy
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    names = ', '.join([alias.name for alias in node.names])
                    analysis['imports'].append(f"from {module} import {names}")
                
                # Functions
                elif isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    analysis['functions'].append(func_name)
                    
                    # Check if async
                    if getattr(node, 'is_async', False):
                        analysis['async_functions'].append(func_name)
                    
                    # Check for type hints
                    if node.returns:
                        analysis['has_type_hints'] = True
                    
                    # Check for decorators
                    if node.decorator_list:
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name):
                                analysis['decorators'].append(decorator.id)
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append(node.name)
                
                # Try/Except blocks
                elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                    analysis['has_error_handling'] = True
                
                # Logging calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['debug', 'info', 'warning', 'error', 'critical']:
                            analysis['has_logging'] = True
            
            # Check for docstrings
            if ast.get_docstring(tree):
                analysis['has_docstrings'] = True
            
            # Complexity indicators
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Complex conditions
                if line.count('and') + line.count('or') >= 3:
                    analysis['complexity_indicators'].append(f"Line {i+1}: Complex condition")
                
                # Deep nesting
                if line.startswith(('    ' * 4)):  # 4 levels deep
                    analysis['complexity_indicators'].append(f"Line {i+1}: Deep nesting")
                
                # Long line
                if len(line) > 120:
                    analysis['complexity_indicators'].append(f"Line {i+1}: Long line ({len(line)} chars)")
            
        except SyntaxError:
            # Fallback to regex parsing if AST fails
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                # Check imports
                if line.startswith('import ') or line.startswith('from '):
                    analysis['imports'].append(line)
                
                # Check functions
                if line.startswith('def '):
                    func_name = line.split('def ')[1].split('(')[0].strip()
                    analysis['functions'].append(func_name)
                
                # Check classes
                if line.startswith('class '):
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    analysis['classes'].append(class_name)
                
                # Check error handling
                if 'try:' in line or 'except ' in line or 'finally:' in line:
                    analysis['has_error_handling'] = True
                
                # Check logging
                if 'logging.' in line or 'logger.' in line or 'log.' in line:
                    analysis['has_logging'] = True
                
                # Check type hints
                if '->' in line or ': ' in line and 'def ' in line:
                    analysis['has_type_hints'] = True
        
        return analysis
    
    @staticmethod
    def analyze_javascript_file(content: str) -> Dict:
        """Analyze JavaScript/TypeScript file"""
        analysis = {
            'imports': [],
            'exports': [],
            'functions': [],
            'classes': [],
            'has_error_handling': False,
            'has_logging': False,
            'has_types': False,
            'line_count': len(content.split('\n'))
        }
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Imports
            if line.startswith('import '):
                analysis['imports'].append(line)
            
            # Exports
            if line.startswith('export '):
                analysis['exports'].append(line)
            
            # Functions
            if 'function ' in line or line.startswith('const ') and '=' in line and '=>' in line:
                # Extract function name
                if 'function ' in line:
                    parts = line.split('function ')
                    if len(parts) > 1:
                        func_name = parts[1].split('(')[0].strip()
                        analysis['functions'].append(func_name)
            
            # Classes
            if line.startswith('class '):
                class_name = line.split('class ')[1].split('{')[0].strip()
                analysis['classes'].append(class_name)
            
            # Error handling
            if 'try' in line or 'catch' in line or 'finally' in line:
                analysis['has_error_handling'] = True
            
            # Logging
            if 'console.' in line or 'logger.' in line:
                analysis['has_logging'] = True
            
            # TypeScript types
            if ': ' in line and ('string' in line or 'number' in line or 'boolean' in line or 
                               'any' in line or 'void' in line or 'interface' in line):
                analysis['has_types'] = True
        
        return analysis
    
    @staticmethod
    def extract_dependencies(content: str, file_type: str) -> List[str]:
        """Enhanced dependency extraction"""
        dependencies = []
        
        if file_type == 'python':
            # Look for import statements
            import_pattern = r'^(?:import|from)\s+([a-zA-Z0-9_\.]+)'
            matches = re.findall(import_pattern, content, re.MULTILINE)
            dependencies.extend(matches)
            
            # Look for pip install in comments (common in notebooks)
            pip_pattern = r'pip\s+(?:install|uninstall)\s+([a-zA-Z0-9_\-]+)'
            pip_matches = re.findall(pip_pattern, content, re.IGNORECASE)
            dependencies.extend(pip_matches)
            
        elif file_type == 'javascript':
            # Look for import/require statements
            import_pattern = r'(?:import|require)\s*\(?[\'"]([^"\']+)[\'"]\)?'
            matches = re.findall(import_pattern, content)
            dependencies.extend(matches)
            
        elif file_type == 'json':
            try:
                data = json.loads(content)
                if 'dependencies' in data:
                    dependencies.extend(list(data['dependencies'].keys()))
                if 'devDependencies' in data:
                    dependencies.extend(list(data['devDependencies'].keys()))
            except:
                pass
        
        elif file_type == 'yaml':
            try:
                data = yaml.safe_load(content)
                if data and 'dependencies' in data:
                    if isinstance(data['dependencies'], list):
                        dependencies.extend(data['dependencies'])
                    elif isinstance(data['dependencies'], dict):
                        dependencies.extend(list(data['dependencies'].keys()))
            except:
                pass
        
        elif file_type == 'toml':
            # Simple TOML parsing for dependencies
            lines = content.split('\n')
            in_deps = False
            for line in lines:
                line = line.strip()
                if line.startswith('[dependencies]'):
                    in_deps = True
                elif line.startswith('[') and in_deps:
                    in_deps = False
                elif in_deps and '=' in line and not line.startswith('#'):
                    dep = line.split('=')[0].strip()
                    dependencies.append(dep)
        
        # Filter out standard library and local imports
        filtered_deps = []
        for dep in dependencies:
            dep = dep.strip()
            if ('.' not in dep or dep.startswith('.')) and '/' not in dep:
                filtered_deps.append(dep)
        
        return list(set(filtered_deps))  # Remove duplicates
    
    @staticmethod
    def analyze_config_file(content: str, file_type: str) -> Dict:
        """Analyze configuration files"""
        analysis = {
            'parsed_successfully': False,
            'config_type': file_type,
            'sections': [],
            'key_count': 0,
            'has_secrets': False,
            'has_comments': False
        }
        
        try:
            if file_type == 'json':
                data = json.loads(content)
                analysis['parsed_successfully'] = True
                analysis['key_count'] = len(data)
                analysis['sections'] = list(data.keys())
            
            elif file_type == 'yaml':
                data = yaml.safe_load(content)
                if data:
                    analysis['parsed_successfully'] = True
                    if isinstance(data, dict):
                        analysis['key_count'] = len(data)
                        analysis['sections'] = list(data.keys())
            
            # Check for secrets
            secret_patterns = ['password', 'secret', 'key', 'token', 'auth']
            for pattern in secret_patterns:
                if pattern.lower() in content.lower():
                    analysis['has_secrets'] = True
                    break
            
            # Check for comments
            analysis['has_comments'] = '#' in content or '//' in content
            
        except:
            analysis['parsed_successfully'] = False
        
        return analysis
    
    @staticmethod
    def extract_code_patterns(content: str, patterns: List[str]) -> Dict[str, List[str]]:
        """Extract specific code patterns"""
        results = {}
        
        for pattern in patterns:
            regex = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
            matches = regex.findall(content)
            if matches:
                results[pattern] = matches[:10]  # Limit to 10 matches
        
        return results