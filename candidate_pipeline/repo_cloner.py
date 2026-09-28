"""
Repository Cloner - Clone GitHub repositories to local temp directories.
"""

import os
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Optional


def _normalize_repo_url(repo_url: str) -> str:
    """
    Clean repository URL before validation and cloning.
    """

    repo_url = (repo_url or "").strip()

    if not repo_url:
        raise ValueError("GitHub repository URL cannot be empty.")

    return repo_url


def extract_owner_repo(
    repo_url: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Extract GitHub owner and repository name.

    Supports:
    https://github.com/owner/repo
    https://github.com/owner/repo.git
    git@github.com:owner/repo.git
    """

    try:
        repo_url = _normalize_repo_url(repo_url)
    except ValueError:
        return None, None

    url = repo_url.rstrip("/")

    url = re.sub(
        r"\.git$",
        "",
        url,
        flags=re.IGNORECASE,
    )

    match = re.search(
        r"github\.com[/:]([^/\s]+)/([^/?#\s]+)",
        url,
        flags=re.IGNORECASE,
    )

    if not match:
        return None, None

    owner = match.group(1).strip()
    repo = match.group(2).strip()

    if not owner or not repo:
        return None, None

    return owner, repo


def clone_repository(
    repo_url: str,
    temp_base_dir: Optional[str] = None,
) -> str:
    """
    Clone GitHub repository into temporary directory.

    Uses shallow cloning because source analysis does not require
    the entire git history.

    Full commit history should be obtained using GitHub API.
    """

    # Important:
    # Strip accidental spaces before passing URL to git.
    repo_url = _normalize_repo_url(repo_url)

    owner, repo = extract_owner_repo(repo_url)

    if not owner or not repo:
        raise ValueError(
            f"Invalid GitHub repository URL: {repo_url}"
        )

    temp_base = temp_base_dir or tempfile.gettempdir()

    os.makedirs(
        temp_base,
        exist_ok=True,
    )

    temp_dir = tempfile.mkdtemp(
        prefix=f"{repo}_",
        dir=temp_base,
    )

    try:
        command = [
            "git",
            "clone",
            "--depth",
            "1",
            repo_url,
            temp_dir,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.returncode != 0:
            error_message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Unknown git clone error"
            )

            shutil.rmtree(
                temp_dir,
                ignore_errors=True,
            )

            raise RuntimeError(
                f"Git clone failed for {repo_url}: "
                f"{error_message}"
            )

        if not os.path.isdir(temp_dir):
            raise RuntimeError(
                "Git clone reported success but repository "
                "directory was not created."
            )

        return os.path.abspath(temp_dir)

    except FileNotFoundError as exc:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )

        raise RuntimeError(
            "Git is not installed or is not available in PATH."
        ) from exc

    except subprocess.TimeoutExpired as exc:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )

        raise RuntimeError(
            f"Git clone timed out after 60 seconds for {repo_url}"
        ) from exc

    except Exception:

        if os.path.exists(temp_dir):
            shutil.rmtree(
                temp_dir,
                ignore_errors=True,
            )

        raise


def cleanup_repository(
    repo_path: str,
) -> bool:
    """
    Remove cloned temporary repository.
    """

    if not repo_path:
        return True

    def _handle_remove_readonly(
        func,
        path,
        exc_info,
    ):
        os.chmod(
            path,
            stat.S_IWRITE,
        )

        func(path)

    try:

        if os.path.exists(repo_path):

            shutil.rmtree(
                repo_path,
                onerror=_handle_remove_readonly,
            )

        return True

    except Exception as exc:

        print(
            f"Warning: Failed to cleanup repository "
            f"at {repo_path}: {exc}"
        )

        return False


# Backward compatibility
clone_repo = clone_repository
cleanup_repo = cleanup_repository
