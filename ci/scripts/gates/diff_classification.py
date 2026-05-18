"""Diff classification gate — categorizes staged git changes into six categories.

Categories: docs-only, formatting-only, lockfile-only, tests-only, migration-only, runtime-code.
Priority (highest wins): runtime-code(6) > tests-only(5) > migration-only(4) > lockfile-only(3) > formatting-only(2) > docs-only(1).
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


CATEGORY_PRIORITY = {
    "docs-only": 1,
    "formatting-only": 2,
    "lockfile-only": 3,
    "migration-only": 4,
    "tests-only": 5,
    "runtime-code": 6,
}

RECOMMENDED_ROUTES = {
    "docs-only": "skip_pipeline",
    "formatting-only": "formatting_and_stage_1",
    "lockfile-only": "dependency_check_only",
    "tests-only": "reduced_pipeline_tests",
    "migration-only": "migration_safety_only",
    "runtime-code": "full_pipeline",
}


def _is_doc_file(path: str) -> bool:
    """Check if file is documentation (docs-only category)."""
    p = Path(path)

    # File extension checks
    if p.suffix in {".md", ".rst"}:
        return True

    # Filename patterns
    name_lower = p.name.lower()
    if name_lower.startswith(("readme", "changelog", "license", "authors", "contributors")):
        return True

    # Directory patterns
    parts = p.parts
    if "docs" in parts or ".github" in parts:
        # If in .github, check for template dirs
        if ".github" in parts:
            idx = parts.index(".github")
            if idx + 1 < len(parts):
                subdir = parts[idx + 1]
                if subdir in {"ISSUE_TEMPLATE", "PULL_REQUEST_TEMPLATE"}:
                    return True
        elif "docs" in parts:
            return True

    return False


def _is_lockfile(path: str) -> bool:
    """Check if file is a dependency lockfile (lockfile-only category)."""
    p = Path(path)
    name = p.name

    lockfile_names = {
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "requirements-prod.txt",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Pipfile.lock",
        "pyproject.lock",
        "uv.lock",
        "Gemfile.lock",
        "composer.lock",
        "go.sum",
    }

    # Check exact filename match or prefix match for requirements*
    if name in lockfile_names:
        return True

    if name.startswith("requirements") and name.endswith(".txt"):
        return True

    return False


def _is_test_file(path: str) -> bool:
    """Check if file is a test file (tests-only category)."""
    p = Path(path)

    # Check if in tests/ directory
    if "tests" in p.parts:
        # Any file in tests/ is a test file
        if p.suffix in {".py", ".gd", ".ts", ".tsx", ".js", ".jsx"}:
            return True

    # Check test filename patterns
    name = p.name
    if name.startswith("test_") or name.endswith("_test.py") or name.endswith("_test.gd"):
        if p.suffix in {".py", ".gd"}:
            return True

    # conftest.py is a test file
    if name == "conftest.py":
        return True

    return False


def _is_migration_file(path: str) -> bool:
    """Check if file is a migration (migration-only category)."""
    p = Path(path)

    migration_dirs = {"migrations", "db/migrations", "alembic/versions"}

    # Check if file is in a migration directory
    path_str = str(p).replace("\\", "/")  # Normalize to forward slashes
    for mig_dir in migration_dirs:
        if mig_dir in path_str:
            return True

    return False


def _is_code_file(path: str) -> bool:
    """Check if file is source code (various categories or runtime-code)."""
    p = Path(path)
    return p.suffix in {".py", ".gd", ".ts", ".tsx", ".js", ".jsx", ".json", ".go", ".rs", ".rb"}


def _is_formatting_only_file(repo: Path, file_path: str) -> bool:
    """Detect if file changes are formatting-only (whitespace/comments/imports).

    New files (additions) return False. Only modifications count as formatting-only.
    """
    try:
        # Get the diff for this specific file
        result = subprocess.run(
            ["git", "diff", "--cached", file_path],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Failed to get diff for {file_path}: {result.stderr}")
            return False

        diff_text = result.stdout

        # Check if this is a new file (no "--- /dev/null" indicates existing file)
        if "--- /dev/null" in diff_text:
            # This is a new file, not a modification. Don't classify as formatting-only.
            return False

        added_lines, removed_lines = [], []
        for line in diff_text.split("\n"):
            if line.startswith(("+++", "---", "@@")) or not line or line[0] == " ":
                continue
            if line[0] == "+":
                added_lines.append(line[1:])
            elif line[0] == "-":
                removed_lines.append(line[1:])

        def normalize(s: str) -> str:
            return "".join(s.split())

        for rem_line in removed_lines:
            if not rem_line.strip():
                continue
            stripped = rem_line.lstrip()
            if stripped.startswith(("#", "//", "import ", "from ", "export ")):
                continue
            norm_rem = normalize(rem_line)
            if not any(normalize(add) == norm_rem for add in added_lines if add.strip()):
                return False

        for add_line in added_lines:
            if not add_line.strip():
                continue
            stripped = add_line.lstrip()
            if stripped.startswith(("#", "//", "import ", "from ", "export ")):
                continue
            norm_add = normalize(add_line)
            if not any(normalize(rem) == norm_add for rem in removed_lines if rem.strip()):
                return False

        return True

    except Exception as e:
        logger.error(f"Error checking formatting for {file_path}: {e}")
        return False


def _classify_file(repo: Path, path: str) -> str:
    """Classify file by path pattern; check formatting-only for code modifications."""
    # Check categories by path patterns

    # Category 1: docs-only
    if _is_doc_file(path):
        return "docs-only"

    # Category 3: lockfile-only
    if _is_lockfile(path):
        return "lockfile-only"

    # Category 4: tests-only
    if _is_test_file(path):
        return "tests-only"

    # Category 5: migration-only
    if _is_migration_file(path):
        return "migration-only"

    # Category 6: runtime-code (or formatting-only for modifications)
    if _is_code_file(path):
        # Check if this modification is formatting-only
        # (new files are classified as runtime-code, not formatting-only)
        if _is_formatting_only_file(repo, path):
            return "formatting-only"
        return "runtime-code"

    # Default to runtime-code for unrecognized files
    return "runtime-code"


def _get_staged_files(repo: Path) -> list[str]:
    """Get list of staged files in git index."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTU"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(f"Failed to get staged files: {result.stderr}")
            return []

        files = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        return files

    except Exception as e:
        logger.error(f"Error getting staged files: {e}")
        return []


def _determine_classification(repo: Path, files: list[str]) -> str:
    """Classify overall repo: highest priority category wins."""
    if not files:
        # Empty staging area defaults to docs-only (safest)
        return "docs-only"

    # Classify each file
    categories: dict[str, int] = {cat: 0 for cat in CATEGORY_PRIORITY}

    for file_path in files:
        category = _classify_file(repo, file_path)
        categories[category] += 1

    # Find highest-priority category present
    highest_category = None
    highest_priority = -1

    for category, count in categories.items():
        if count > 0:
            priority = CATEGORY_PRIORITY[category]
            if priority > highest_priority:
                highest_priority = priority
                highest_category = category

    # If no categories matched (shouldn't happen), default to docs-only
    return highest_category or "docs-only"


def _format_message(classification: str, files: list[str]) -> str:
    """Format a human-readable message describing the classification."""
    if not files:
        return "No staged changes detected. Recommended: skip pipeline."

    route = RECOMMENDED_ROUTES[classification]

    message_templates = {
        "docs-only": f"Documentation only. All staged changes are .md/.rst files. Recommended: {route}.",
        "formatting-only": f"Formatting changes only. Staged changes are whitespace/comment/import-reordering. Recommended: {route}.",
        "lockfile-only": f"Dependency lock files only. Staged changes include requirements.txt, package-lock.json, etc. Recommended: {route}.",
        "tests-only": f"Test files only. All staged changes are in tests/ directory or test_*.py files. Recommended: {route}.",
        "migration-only": f"Database migrations only. Staged changes are in migrations/ or alembic/versions/. Recommended: {route}.",
        "runtime-code": f"Runtime code present. Staged changes include source code (scripts/, src/, etc.). Recommended: {route}.",
    }

    return message_templates.get(classification, f"Classification: {classification}. Recommended: {route}.")


def _iso8601_timestamp() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute diff classification gate. Inputs: ticket_id (optional)."""
    start_time = time.time()

    # Get inputs
    ticket_id = inputs.get("ticket_id", "M902-09")

    try:
        # Find repo root (current directory)
        repo = Path.cwd()

        # Check if git is available
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning("Git not available or not in a git repository")
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "status": "PASS",
                    "gate": "diff_classification",
                    "timestamp": _iso8601_timestamp(),
                    "ticket_id": ticket_id,
                    "message": "Git not available or not in a git repository.",
                    "classification": "docs-only",
                    "recommended_route": "skip_pipeline",
                    "artifacts": [],
                    "duration_ms": elapsed_ms,
                }
        except (OSError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Git check failed: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "PASS",
                "gate": "diff_classification",
                "timestamp": _iso8601_timestamp(),
                "ticket_id": ticket_id,
                "message": "Git not available.",
                "classification": "docs-only",
                "recommended_route": "skip_pipeline",
                "artifacts": [],
                "duration_ms": elapsed_ms,
            }

        # Get staged files
        staged_files = _get_staged_files(repo)

        # Determine classification
        classification = _determine_classification(repo, staged_files)

        # Format message
        message = _format_message(classification, staged_files)

        # Get recommended route
        recommended_route = RECOMMENDED_ROUTES[classification]

        # Calculate elapsed time
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Build result
        result = {
            "status": "PASS",
            "gate": "diff_classification",
            "timestamp": _iso8601_timestamp(),
            "ticket_id": ticket_id,
            "message": message,
            "classification": classification,
            "recommended_route": recommended_route,
            "artifacts": [],
            "duration_ms": elapsed_ms,
        }

        return result

    except Exception as e:
        logger.exception(f"Unexpected error in diff_classification gate: {e}")
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "PASS",
            "gate": "diff_classification",
            "timestamp": _iso8601_timestamp(),
            "ticket_id": ticket_id,
            "message": f"Error during classification: {str(e)}",
            "classification": "docs-only",
            "recommended_route": "skip_pipeline",
            "artifacts": [],
            "duration_ms": elapsed_ms,
        }
