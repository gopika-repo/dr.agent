"""
Commit Analyzer - Analyze repository commit history using GitPython.

Extracts: total commits, project duration in days, first/last commit dates,
and commit frequency metrics.
"""

from datetime import datetime
import gc
from typing import Dict, Optional
from git import Repo
from git.exc import InvalidGitRepositoryError


def analyze_commits(repo_path: str) -> Dict:
    """
    Analyze commit history of a repository.
    
    Uses GitPython to extract commit statistics:
    - Total number of commits
    - Project duration (days between first and last commit)
    - First and last commit dates
    - Commits per day average
    
    Args:
        repo_path: Path to repository root (must be a valid git repository)
        
    Returns:
        Dictionary containing commit analysis:
        {
            'total_commits': int,
            'project_duration_days': int,
            'first_commit_date': str (ISO format),
            'last_commit_date': str (ISO format),
            'commits_per_day': float,
            'has_git_history': bool,
            'error': str (if any)
        }
    """
    result = {
        'total_commits': 0,
        'project_duration_days': 0,
        'first_commit_date': None,
        'last_commit_date': None,
        'commits_per_day': 0.0,
        'has_git_history': False,
        'error': None
    }
    
    try:
        # Initialize git repository
        git_repo = Repo(repo_path)
        result['has_git_history'] = True
        
        # Get all commits
        try:
            commits = list(git_repo.iter_commits())
        except Exception as e:
            # If default branch iteration fails, try common alternatives
            commits = []
            for ref in ['HEAD', 'main', 'master', 'develop']:
                try:
                    commits = list(git_repo.iter_commits(ref))
                    if commits:
                        break
                except Exception:
                    continue
        
        if not commits:
            result['error'] = 'No commits found in repository'
            return result
        
        result['total_commits'] = len(commits)
        
        # Get first and last commits
        last_commit = commits[0]  # Most recent
        first_commit = commits[-1]  # Oldest
        
        last_date = datetime.fromtimestamp(last_commit.committed_date)
        first_date = datetime.fromtimestamp(first_commit.committed_date)
        
        result['last_commit_date'] = last_date.isoformat()
        result['first_commit_date'] = first_date.isoformat()
        
        # Calculate duration
        duration = (last_date - first_date).days
        result['project_duration_days'] = max(duration, 1)  # Avoid division by zero
        
        # Calculate commits per day
        if result['project_duration_days'] > 0:
            result['commits_per_day'] = round(
                result['total_commits'] / result['project_duration_days'],
                2
            )
        
        try:
            git_repo.git.clear_cache()
        except Exception:
            pass
        
    except InvalidGitRepositoryError:
        result['error'] = f'Not a valid git repository: {repo_path}'
    except Exception as e:
        result['error'] = f'Error analyzing commits: {str(e)}'
    finally:
        try:
            del git_repo
        except Exception:
            pass
        gc.collect()
    
    return result
