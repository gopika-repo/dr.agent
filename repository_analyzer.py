# models/repository_analyzer.py - Simplified Repository Analyzer
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import re

class RepositoryAnalyzer:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def analyze(self) -> Dict:
        """Complete repository analysis"""
        try:
            analysis = {
                'metadata': self._analyze_metadata(),
                'structure': self._analyze_structure(),
                'files': self._analyze_files(),
                'dependencies': self._analyze_dependencies(),
                'documentation': self._analyze_documentation(),
                'tests': self._analyze_tests(),
                'docker': self._analyze_docker(),
                'ci_cd': self._analyze_ci_cd(),
                'code_quality': self._analyze_code_quality(),
                'configs': self._analyze_configs()
            }
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_metadata(self) -> Dict:
        """Analyze repository metadata"""
        metadata = {
            'has_readme': False,
            'has_license': False,
            'has_gitignore': False,
            'has_test_directory': False,
            'has_dockerfile': False
        }
        
        # Check for key files
        for item in self.repo_path.iterdir():
            if item.is_file():
                name_lower = item.name.lower()
                if name_lower.startswith('readme'):
                    metadata['has_readme'] = True
                elif name_lower == 'license' or name_lower.startswith('license.'):
                    metadata['has_license'] = True
                elif name_lower == '.gitignore':
                    metadata['has_gitignore'] = True
                elif name_lower == 'dockerfile' or name_lower.startswith('dockerfile.'):
                    metadata['has_dockerfile'] = True
        
        # Check for test directory
        test_dirs = ['tests', 'test', '__tests__']
        for test_dir in test_dirs:
            if (self.repo_path / test_dir).exists():
                metadata['has_test_directory'] = True
                break
        
        return metadata
    
    def _analyze_structure(self) -> Dict:
        """Analyze directory structure"""
        structure = {
            'key_directories': {},
            'total_directories': 0
        }
        
        key_dirs = ['src', 'app', 'lib', 'core', 'api', 'routes', 'models', 
                   'tests', 'test', 'docs', 'documentation', 'docker', 
                   'deploy', 'config', 'configuration', 'data', 'etl']
        
        for dir_name in key_dirs:
            if (self.repo_path / dir_name).exists():
                structure['key_directories'][dir_name] = True
        
        # Count total directories (excluding hidden)
        dir_count = 0
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            dir_count += len(dirs)
        
        structure['total_directories'] = dir_count
        
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
            'markdown_count': 0
        }
        
        # Count files by type
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                ext = os.path.splitext(filename)[1].lower()
                
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
        
        return files
    
    def _analyze_dependencies(self) -> Dict:
        """Analyze dependencies from package files"""
        deps = {
            'python': [],
            'node': []
        }
        
        # Python dependencies
        req_files = ['requirements.txt', 'pyproject.toml', 'setup.py']
        for req_file in req_files:
            file_path = self.repo_path / req_file
            if file_path.exists():
                try:
                    if req_file == 'requirements.txt':
                        with open(file_path, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and not line.startswith('-'):
                                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
                                    if pkg and pkg not in deps['python']:
                                        deps['python'].append(pkg)
                except:
                    pass
        
        # Node dependencies
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    if 'dependencies' in data:
                        deps['node'].extend(list(data['dependencies'].keys()))
                    if 'devDependencies' in data:
                        deps['node'].extend(list(data['devDependencies'].keys()))
            except:
                pass
        
        return deps
    
    def _analyze_documentation(self) -> Dict:
        """Analyze documentation"""
        docs = {
            'has_readme': False,
            'has_setup_instructions': False,
            'has_examples': False,
            'has_api_docs': False,
            'readme_content': ''
        }
        
        # Find and read README
        readme_files = list(self.repo_path.glob('README*'))
        if readme_files:
            docs['has_readme'] = True
            readme_file = readme_files[0]
            
            try:
                with open(readme_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)  # First 5000 chars
                    docs['readme_content'] = content.lower()
                    
                    # Check for common sections
                    if any(term in content.lower() for term in ['install', 'setup', 'getting started']):
                        docs['has_setup_instructions'] = True
                    
                    if any(term in content.lower() for term in ['example', 'usage', 'demo']):
                        docs['has_examples'] = True
                    
                    if any(term in content.lower() for term in ['api', 'endpoint', 'rest', 'graphql']):
                        docs['has_api_docs'] = True
            except:
                pass
        
        return docs
    
    def _analyze_tests(self) -> Dict:
        """Analyze testing setup"""
        tests = {
            'has_test_directory': False,
            'test_files': []
        }
        
        # Find test directory
        test_dirs = ['tests', 'test', '__tests__']
        for test_dir in test_dirs:
            test_path = self.repo_path / test_dir
            if test_path.exists():
                tests['has_test_directory'] = True
                
                # Find test files
                test_patterns = ['*test*.py', '*spec*.js', '*test*.js', '*test*.ts']
                for pattern in test_patterns:
                    for test_file in test_path.rglob(pattern):
                        if test_file.is_file():
                            tests['test_files'].append(str(test_file.relative_to(self.repo_path)))
                break
        
        return tests
    
    def _analyze_docker(self) -> Dict:
        """Analyze Docker configuration"""
        docker = {
            'has_dockerfile': False,
            'dockerfile_path': '',
            'has_docker_compose': False
        }
        
        # Check for Dockerfile
        dockerfiles = list(self.repo_path.glob('Dockerfile*'))
        if dockerfiles:
            docker['has_dockerfile'] = True
            docker['dockerfile_path'] = str(dockerfiles[0].relative_to(self.repo_path))
        
        # Check for docker-compose
        compose_files = list(self.repo_path.glob('docker-compose*'))
        if compose_files:
            docker['has_docker_compose'] = True
        
        return docker
    
    def _analyze_ci_cd(self) -> Dict:
        """Analyze CI/CD configuration"""
        ci_cd = {
            'has_ci': False,
            'ci_files': []
        }
        
        # Check for CI files
        ci_patterns = ['.github/workflows/*.yml', '.github/workflows/*.yaml', 
                      '.gitlab-ci.yml', '.travis.yml', 'circle.yml']
        
        for pattern in ci_patterns:
            ci_files = list(self.repo_path.rglob(pattern))
            if ci_files:
                ci_cd['has_ci'] = True
                ci_cd['ci_files'].extend([
                    str(f.relative_to(self.repo_path)) for f in ci_files
                ])
        
        return ci_cd
    
    def _analyze_code_quality(self) -> Dict:
        """Analyze code quality indicators"""
        quality = {
            'has_linting': False,
            'has_error_handling': False,
            'has_comments': False
        }
        
        # Check for linting/config files
        linting_files = ['.flake8', '.pylintrc', '.eslintrc', '.prettierrc',
                        'pyproject.toml', 'setup.cfg', '.editorconfig']
        
        for file_name in linting_files:
            if (self.repo_path / file_name).exists():
                quality['has_linting'] = True
                break
        
        return quality
    
    def _analyze_configs(self) -> Dict:
        """Analyze configuration files"""
        configs = {}
        
        config_files = {
            '.env': self.repo_path / '.env',
            '.env.example': self.repo_path / '.env.example',
            'config.json': self.repo_path / 'config.json',
            'settings.py': self.repo_path / 'settings.py',
            'config.py': self.repo_path / 'config.py'
        }
        
        for name, path in config_files.items():
            if path.exists():
                configs[name] = {'exists': True, 'path': str(path.relative_to(self.repo_path))}
        
        return configs