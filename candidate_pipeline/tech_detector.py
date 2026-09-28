"""
Technology Detector - repository technology and AI/agent capability detection.

The detector works only inside the path it receives.

So:

full_repo
    -> scans complete repository

agents_only
    -> scans only repo/agents

This detector uses dependency manifests, filenames, imports,
and bounded source-code content.

It does NOT use an LLM and does NOT hardcode evaluation scores.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Set


SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
    ".idea",
    ".vscode",
}


# Prevent extremely large files from being read just for tech detection.
MAX_SOURCE_FILE_BYTES = 256_000


# ---------------------------------------------------------------------
# Technology signatures
# ---------------------------------------------------------------------

TECH_SIGNATURES: Mapping[str, Mapping[str, Iterable[str]]] = {

    "ai_ml": {
        "openai": (
            "openai",
            "@ai-sdk/openai",
        ),

        "anthropic": (
            "anthropic",
            "@anthropic-ai/sdk",
            "claude",
        ),

        "gemini": (
            "google.generativeai",
            "google.genai",
            "@google/generative-ai",
            "gemini",
        ),

        "groq": (
            "groq",
            "groq-sdk",
        ),

        "mistral": (
            "mistralai",
            "@mistralai",
            "mistral",
        ),

        "transformers": (
            "transformers",
            "huggingface",
        ),

        "tensorflow": (
            "tensorflow",
        ),

        "pytorch": (
            "torch",
            "pytorch",
        ),

        "scikit-learn": (
            "sklearn",
            "scikit-learn",
        ),

        "opencv": (
            "opencv",
            "cv2",
        ),

        "llm": (
            "llm",
            "large language model",
            "chatcompletion",
            "generatecontent",
        ),

        "multimodal": (
            "multimodal",
            "vision model",
            "image_url",
            "image input",
        ),
    },


    "agent_frameworks": {

        "mastra": (
            "@mastra/",
            "from 'mastra",
            'from "mastra',
            "mastra.",
        ),

        "langchain": (
            "langchain",
            "@langchain/",
        ),

        "langgraph": (
            "langgraph",
            "@langchain/langgraph",
        ),

        "crewai": (
            "crewai",
            "crew ai",
        ),

        "autogen": (
            "autogen",
            "pyautogen",
            "microsoft/autogen",
        ),

        "semantic-kernel": (
            "semantic_kernel",
            "semantic-kernel",
            "@microsoft/semantic-kernel",
        ),

        "ai agents": (
            "agent(",
            "new agent",
            "createagent",
            "agent =",
            "agent:",
            "tool calling",
            "tool_call",
        ),
    },


    "rag": {

        "rag": (
            "retrieval augmented",
            "retrieval-augmented",
            "rag pipeline",
            "retriever",
            "retrieval",
        ),

        "embeddings": (
            "embedding",
            "embeddings",
            "embedmany",
            "embedquery",
        ),

        "vector search": (
            "vector search",
            "similarity search",
            "semantic search",
            "nearest neighbor",
        ),
    },


    "security_ai": {

        "enkrypt ai": (
            "enkrypt",
            "enkryptai",
            "enkrypt ai",
        ),

        "guardrails": (
            "guardrail",
            "prompt injection",
            "content filter",
            "input validation",
            "output validation",
        ),
    },


    "frameworks": {

        "fastapi": (
            "fastapi",
        ),

        "flask": (
            "flask",
        ),

        "django": (
            "django",
        ),

        "react": (
            "react-dom",
            "from 'react'",
            'from "react"',
            "from 'react/",
            'from "react/',
            "require('react')",
            'require("react")',
            "@types/react",
        ),

        "next.js": (
            "nextjs",
            "next.js",
            "from 'next/",
            'from "next/',
            "require('next",
            'require("next',
            "@next/",
        ),

        "vue": (
            "vue",
        ),

        "angular": (
            "@angular/",
            "angular",
        ),

        "svelte": (
            "svelte",
        ),

        "express": (
            "express",
        ),

        "nestjs": (
            "@nestjs/",
            "nestjs",
        ),
    },


    "databases": {

        "qdrant": (
            "qdrant",
            "@qdrant/js-client",
            "qdrant-client",
        ),

        "pinecone": (
            "pinecone",
        ),

        "weaviate": (
            "weaviate",
        ),

        "milvus": (
            "milvus",
            "pymilvus",
        ),

        "chroma": (
            "chromadb",
            "chroma",
        ),

        "faiss": (
            "faiss",
        ),

        "postgresql": (
            "postgresql",
            "postgres",
            "psycopg",
            "pgvector",
        ),

        "mongodb": (
            "mongodb",
            "pymongo",
            "mongoose",
        ),

        "redis": (
            "redis",
        ),

        "sqlite": (
            "sqlite",
        ),

        "mysql": (
            "mysql",
        ),

        "neo4j": (
            "neo4j",
        ),

        "turso": (
            "turso",
            "libsql",
        ),

        "vector db": (
            "vector database",
            "vector db",
            "vectorstore",
            "vector store",
        ),
    },


    "devops": {

        "docker": (
            "docker",
            "dockerfile",
            "docker-compose",
        ),

        "kubernetes": (
            "kubernetes",
            "k8s",
            "helm",
        ),

        "github-actions": (
            ".github/workflows",
            "github actions",
        ),

        "aws": (
            "boto3",
            "aws-sdk",
            "amazon web services",
        ),

        "azure": (
            "azure",
        ),

        "gcp": (
            "google-cloud",
            "gcp",
        ),

        "cloudflare": (
            "cloudflare",
            "wrangler",
        ),

        "vercel": (
            "vercel",
        ),
    },


    "testing": {

        "pytest": (
            "pytest",
        ),

        "unittest": (
            "unittest",
        ),

        "jest": (
            "jest",
        ),

        "vitest": (
            "vitest",
        ),

        "mocha": (
            "mocha",
        ),

        "playwright": (
            "playwright",
        ),

        "cypress": (
            "cypress",
        ),
    },
}


# ---------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------

EXTENSION_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
}


SOURCE_EXTENSIONS = set(EXTENSION_TO_LANG) | {
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".mjs",
    ".cjs",
}


DEPENDENCY_FILES = {
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "pipfile",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "gemfile",
    "gemfile.lock",
    "go.mod",
    "cargo.toml",
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _empty_detection() -> Dict[str, Set[str]]:
    """
    Create empty technology detection structure.
    """

    result: Dict[str, Set[str]] = {
        category: set()
        for category in TECH_SIGNATURES
    }

    result["languages"] = set()

    return result


def _normalise_text(value: str) -> str:
    """
    Normalize strings for case-insensitive matching.
    """

    return str(value).lower().replace("\\", "/")


def _record_matches(
    text: str,
    detected: MutableMapping[str, Set[str]],
) -> None:
    """
    Detect technology signatures inside text.
    """

    haystack = _normalise_text(text)

    for category, technologies in TECH_SIGNATURES.items():

        for canonical, indicators in technologies.items():

            if any(
                _normalise_text(indicator) in haystack
                for indicator in indicators
            ):
                detected[category].add(canonical)


def _safe_read(path: Path) -> str:
    """
    Safely read source/config files with a size limit.
    """

    try:

        if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
            return ""

        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    except (OSError, UnicodeError):
        return ""


def _scan_package_json(
    content: str,
    detected: MutableMapping[str, Set[str]],
) -> None:
    """
    Inspect package.json dependencies and scripts.
    """

    try:
        data = json.loads(content)

    except (TypeError, ValueError):

        _record_matches(
            content,
            detected,
        )

        return

    dependency_sections = (
        data.get("dependencies", {}),
        data.get("devDependencies", {}),
        data.get("peerDependencies", {}),
        data.get("optionalDependencies", {}),
    )

    for section in dependency_sections:

        if isinstance(section, dict):

            for package in section:

                package_name = str(package).strip().lower()

                # Exact package-name detection prevents false positives
                # such as "next" in normal prose or "ReAct" agent patterns.
                if package_name == "react":
                    detected["frameworks"].add("react")

                if package_name == "next":
                    detected["frameworks"].add("next.js")

                _record_matches(
                    package,
                    detected,
                )

    scripts = data.get(
        "scripts",
        {},
    )

    if isinstance(scripts, dict):

        _record_matches(
            " ".join(
                map(
                    str,
                    scripts.values(),
                )
            ),
            detected,
        )


def _scan_manifest(
    path: Path,
    content: str,
    detected: MutableMapping[str, Set[str]],
) -> None:
    """
    Inspect dependency manifest.
    """

    if path.name.lower() == "package.json":

        _scan_package_json(
            content,
            detected,
        )

    else:

        _record_matches(
            content,
            detected,
        )


# ---------------------------------------------------------------------
# Public detector
# ---------------------------------------------------------------------

def detect_technologies(
    repo_path: str,
) -> Dict[str, List[str]]:
    """
    Detect technologies implemented or referenced inside repo_path.

    IMPORTANT:

    This function ONLY scans the path that is provided to it.

    Therefore:

    full_repo:
        detect_technologies(repo_root)

    agents_only:
        detect_technologies(repo_root / "agents")

    This is important for Dr. Agent token and scope optimization.

    Returns:
        {
            "ai_ml": [...],
            "agent_frameworks": [...],
            "rag": [...],
            "security_ai": [...],
            "frameworks": [...],
            "databases": [...],
            "devops": [...],
            "testing": [...],
            "languages": [...]
        }
    """

    root = Path(repo_path)

    detected = _empty_detection()

    if not root.exists():

        return {
            key: []
            for key in detected
        }

    # ---------------------------------------------------------
    # Single-file evaluation support
    # ---------------------------------------------------------
    if root.is_file():

        filename = root.name
        lower_name = filename.lower()
        ext = root.suffix.lower()

        # Detect programming language from file extension.
        if ext in EXTENSION_TO_LANG:
            detected["languages"].add(
                EXTENSION_TO_LANG[ext]
            )

        # Filename itself may contain technology signals.
        _record_matches(
            filename,
            detected,
        )

        content = _safe_read(root)

        if content:

            # Dependency files such as package.json,
            # requirements.txt, pyproject.toml, etc.
            if lower_name in DEPENDENCY_FILES:

                _scan_manifest(
                    root,
                    content,
                    detected,
                )

            else:
                # Explicitly selected files should be inspected
                # even when they are documentation files such as README.md.
                _record_matches(
                    content,
                    detected,
                )

        return {
            key: sorted(values)
            for key, values in detected.items()
        }


    for current_root, dirs, files in os.walk(root):

        # Skip large/generated directories.
        dirs[:] = [
            directory
            for directory in dirs
            if directory.lower() not in SKIP_DIRS
        ]

        current = Path(current_root)


        # Folder names themselves may contain useful signals:
        #
        # agents/
        # rag/
        # qdrant/
        # workflows/
        #
        if current != root:

            relative_dir = (
                current
                .relative_to(root)
                .as_posix()
            )

            _record_matches(
                relative_dir,
                detected,
            )


        for filename in files:

            path = current / filename

            lower_name = filename.lower()

            ext = path.suffix.lower()


            # ---------------------------------------------------------
            # Programming language
            # ---------------------------------------------------------

            if ext in EXTENSION_TO_LANG:

                detected["languages"].add(
                    EXTENSION_TO_LANG[ext]
                )


            # ---------------------------------------------------------
            # Filename/path technology evidence
            # ---------------------------------------------------------

            try:

                relative_path = (
                    path
                    .relative_to(root)
                    .as_posix()
                )

            except ValueError:

                relative_path = str(path)


            _record_matches(
                relative_path,
                detected,
            )


            # ---------------------------------------------------------
            # Decide whether file content should be inspected
            # ---------------------------------------------------------

            should_read = (
                lower_name in DEPENDENCY_FILES
                or ext in SOURCE_EXTENSIONS
            )

            if not should_read:
                continue


            content = _safe_read(path)

            if not content:
                continue


            # ---------------------------------------------------------
            # Dependency manifests
            # ---------------------------------------------------------

            if lower_name in DEPENDENCY_FILES:

                _scan_manifest(
                    path,
                    content,
                    detected,
                )


            # ---------------------------------------------------------
            # Source code / documentation
            # ---------------------------------------------------------

            else:

                _record_matches(
                    content,
                    detected,
                )


    # Convert sets to deterministic sorted lists.
    return {
        category: sorted(values)
        for category, values in detected.items()
    }
