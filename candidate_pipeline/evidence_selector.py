"""
Code Evidence Selector.

Selects a small set of important source files from the already-selected
evaluation path.

IMPORTANT:

If Dr. Agent is running in:

    full_repo
        -> repo root is passed here

    agents_only
        -> repo/agents is passed here

Therefore this module never changes evaluation scope itself.
It only selects evidence from the path supplied by api.py.

Purpose:
- Reduce Gemini input size
- Avoid sending unnecessary source code
- Keep evidence relevant to AI/agent implementation
- Make token usage predictable
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------

MAX_EVIDENCE_FILES = 8

MAX_CHARS_PER_FILE = 2200

MAX_TOTAL_CHARS = 12000

MAX_FILE_SIZE_BYTES = 300_000


# ---------------------------------------------------------------------
# Directories that should never be used as code evidence
# ---------------------------------------------------------------------

SKIP_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".next",
    "dist",
    "build",
    "coverage",
    ".pytest_cache",
    ".idea",
    ".vscode",
    ".turbo",
}


# ---------------------------------------------------------------------
# File types worth examining
# ---------------------------------------------------------------------

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".cs",
}


CONFIG_FILENAMES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "docker-compose.yml",
    "docker-compose.yaml",
}


# ---------------------------------------------------------------------
# Terms indicating useful AI / agent evidence
# ---------------------------------------------------------------------

HIGH_VALUE_TERMS = {
    "agent": 10,
    "mastra": 10,
    "enkrypt": 10,

    "rag": 9,
    "retriever": 9,
    "retrieval": 8,

    "qdrant": 9,
    "pinecone": 9,
    "weaviate": 9,
    "milvus": 9,

    "embedding": 8,
    "vector": 8,

    "workflow": 8,
    "orchestr": 8,

    "tool": 7,
    "function_call": 7,
    "tool_call": 7,

    "prompt": 6,

    "openai": 6,
    "anthropic": 6,
    "gemini": 6,
    "groq": 6,

    "guardrail": 7,
    "prompt injection": 7,

    "memory": 6,

    "llm": 5,

    "semantic": 5,
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _safe_read(path: Path) -> str:
    """
    Safely read a text/source file.
    """

    try:

        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return ""

        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    except (OSError, UnicodeError):
        return ""


def _calculate_relevance(
    relative_path: str,
    content: str,
) -> Tuple[int, List[str]]:
    """
    Calculate how relevant a file is for AI/agent evaluation.

    Returns:
        score
        matched terms
    """

    searchable = (
        relative_path.lower()
        + "\n"
        + content.lower()
    )

    score = 0

    matched_terms: List[str] = []


    for term, weight in HIGH_VALUE_TERMS.items():

        if term in searchable:

            score += weight

            matched_terms.append(term)


    # Give actual implementation files a slight preference.
    extension = Path(relative_path).suffix.lower()

    if extension in SOURCE_EXTENSIONS:
        score += 2


    # Important common entry-point filenames.
    filename = Path(relative_path).name.lower()

    if filename in {
        "agent.py",
        "agents.py",
        "main_agent.py",
        "workflow.py",
        "tools.py",
        "rag.py",
        "retriever.py",
        "main.ts",
        "agent.ts",
        "workflow.ts",
        "tools.ts",
    }:
        score += 5


    # Dependency manifests may prove real framework usage.
    if filename in CONFIG_FILENAMES:
        score += 3


    return score, matched_terms


def _collect_candidates(
    analysis_path: str,
) -> List[Dict]:
    """
    Find candidate evidence files inside analysis_path.
    """

    root = Path(analysis_path)

    candidates: List[Dict] = []


    if not root.exists():
        return candidates

    # ---------------------------------------------------------
    # Single-file evaluation support
    # ---------------------------------------------------------
    if root.is_file():

        filename = root.name
        extension = root.suffix.lower()
        lower_name = filename.lower()

        content = _safe_read(root)

        if not content:
            return candidates

        # For an explicitly selected file, allow text/documentation
        # files such as README.md as evidence too.
        relative_path = filename

        score, matched_terms = _calculate_relevance(
            relative_path,
            content,
        )

        candidates.append(
            {
                "path": relative_path,
                "absolute_path": str(root),
                "score": max(score, 1),
                "matched_terms": matched_terms,
                "content": content,
            }
        )

        return candidates


    for current_root, dirs, files in os.walk(root):

        dirs[:] = [
            directory
            for directory in dirs
            if directory.lower() not in SKIP_DIRECTORIES
        ]


        current_path = Path(current_root)


        for filename in files:

            path = current_path / filename

            extension = path.suffix.lower()

            lower_name = filename.lower()


            if (
                extension not in SOURCE_EXTENSIONS
                and lower_name not in CONFIG_FILENAMES
            ):
                continue


            content = _safe_read(path)

            if not content:
                continue


            try:

                relative_path = (
                    path
                    .relative_to(root)
                    .as_posix()
                )

            except ValueError:

                relative_path = path.name


            score, matched_terms = _calculate_relevance(
                relative_path,
                content,
            )


            # Ignore unrelated files.
            if score <= 2:
                continue


            candidates.append(
                {
                    "path": relative_path,
                    "absolute_path": str(path),
                    "score": score,
                    "matched_terms": matched_terms,
                    "content": content,
                }
            )


    candidates.sort(
        key=lambda item: (
            item["score"],
            len(item["matched_terms"]),
        ),
        reverse=True,
    )


    return candidates


# ---------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------

def select_code_evidence(
    analysis_path: str,
    max_files: int = MAX_EVIDENCE_FILES,
    max_chars_per_file: int = MAX_CHARS_PER_FILE,
    max_total_chars: int = MAX_TOTAL_CHARS,
) -> Dict:
    """
    Select bounded source-code evidence for Gemini.

    The selector only looks inside analysis_path.

    Returns a dictionary containing selected files and metrics.
    """

    candidates = _collect_candidates(
        analysis_path
    )


    selected_files: List[Dict] = []

    total_chars = 0


    for candidate in candidates:

        if len(selected_files) >= max_files:
            break


        remaining_chars = (
            max_total_chars
            - total_chars
        )


        if remaining_chars <= 0:
            break


        allowed_chars = min(
            max_chars_per_file,
            remaining_chars,
        )


        snippet = candidate["content"][
            :allowed_chars
        ]


        if not snippet.strip():
            continue


        selected_files.append(
            {
                "path": candidate["path"],
                "relevance_score": candidate["score"],
                "matched_terms": candidate["matched_terms"],
                "characters": len(snippet),
                "content": snippet,
            }
        )


        total_chars += len(snippet)


    return {
        "files": selected_files,

        "candidate_files": len(candidates),

        "selected_files": len(selected_files),

        "total_chars": total_chars,

        "limits": {
            "max_files": max_files,
            "max_chars_per_file": max_chars_per_file,
            "max_total_chars": max_total_chars,
        },
    }


# Backward-compatible / convenient alias.
select_evidence = select_code_evidence
