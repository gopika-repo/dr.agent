# utils/github_client.py - GitHub API Client
import requests
from typing import Dict, Optional, List, Any
import base64
import time

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
        
        self.base_url = 'https://api.github.com'
        self.rate_limit_remaining = 60
        self.rate_limit_reset = 0
    
    def check_repo_access(self, repo_url: str) -> bool:
        """Check if repository is accessible"""
        try:
            # Extract owner/repo from URL
            parts = repo_url.strip('/').split('/')
            
            # Find github.com index
            for i, part in enumerate(parts):
                if 'github.com' in part:
                    github_index = i
                    break
            else:
                return False
            
            if len(parts) <= github_index + 2:
                return False
            
            owner = parts[github_index + 1]
            repo = parts[github_index + 2].replace('.git', '')
            
            # Make API call
            url = f'{self.base_url}/repos/{owner}/{repo}'
            response = requests.get(url, headers=self.headers)
            
            return response.status_code == 200
            
        except Exception as e:
            return False
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict:
        """Get repository languages statistics"""
        url = f'{self.base_url}/repos/{owner}/{repo}/languages'
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return {}