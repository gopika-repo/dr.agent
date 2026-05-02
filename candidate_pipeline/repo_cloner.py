"""
Repository Cloner - Clone GitHub repositories to local temp directories.

Uses subprocess to execute git clone commands with proper error handling
and cleanup. Extracted owner/repo from URL using regex patterns.
"""

import subprocess
import os
import tempfile
import shutil
import re
import stat
from pathlib import Path
from typing import Optional


def extract_owner_repo(repo_url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract owner and repo name from any GitHub URL format.
    
    Handles formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo
    - git@github.com:owner/repo.git
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo) or (None, None) if parsing fails
    """
    if not repo_url:
        return None, None
    
    url = repo_url.strip().rstrip('/')
    # Remove .git suffix
    url = re.sub(r'\.git$', '', url)
    
    # Match github.com/owner/repo or github.com:owner/repo patterns
    match = re.search(r'github\.com[/:]([^/]+)/([^/?#]+)', url)
    if match:
        return match.group(1), match.group(2)
    
    return None, None


def clone_repository(repo_url: str, temp_base_dir: Optional[str] = None) -> Optional[str]:
    """
    Clone a GitHub repository to a temporary local directory.
    
    Args:
        repo_url: GitHub repository URL
        temp_base_dir: Optional base directory for temp files. 
                      Defaults to system temp directory.
    
    Returns:
        Absolute path to cloned repository directory, or None if cloning fails
        
    Raises:
        ValueError: If repository URL is invalid or malformed
        RuntimeError: If git is not installed or cloning fails
    """
    owner, repo = extract_owner_repo(repo_url)
    if not owner or not repo:
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    # Create temp directory
    temp_base = temp_base_dir or tempfile.gettempdir()
    temp_dir = tempfile.mkdtemp(prefix=f"{repo}_", dir=temp_base)
    
    try:
        # Run git clone
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(
                f"Git clone failed for {repo_url}: {result.stderr}"
            )
        
        return temp_dir
        
    except FileNotFoundError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError("Git is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Git clone timed out for {repo_url}")
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Unexpected error during cloning: {str(e)}")


def cleanup_repository(repo_path: str) -> bool:
    """
    Clean up a cloned repository directory.
    
    Args:
        repo_path: Path to the repository directory to clean up
        
    Returns:
        True if cleanup succeeded, False otherwise
    """
    def _handle_remove_readonly(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            raise

    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, onerror=_handle_remove_readonly)
        return True
    except Exception as e:
        print(f"Warning: Failed to cleanup repository at {repo_path}: {e}")
        return False


# Compatibility aliases used by the hackathon pipeline and verification scripts.
clone_repo = clone_repository
cleanup_repo = cleanup_repository
