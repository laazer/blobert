"""Formatting check gate — auto-formats staged code and re-stages if changes detected.

Specification: project_board/specs/902_10_formatting_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md

Formatter execution order: black → ruff format → prettier → gdformat.
If any formatter modified files, re-stages them and returns PASS with message.
If no changes, returns PASS with "already formatted" message.
On formatter error or git error, returns FAIL with violations.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Formatter configurations
FORMATTERS = [
    {
        "name": "black",
        "cmd": ["black"],
        "extensions": [".py"],
    },
    {
        "name": "ruff_format",
        "cmd": ["ruff", "format"],
        "extensions": [".py"],
    },
    {
        "name": "prettier",
        "cmd": ["prettier", "--write"],
        "extensions": [".ts", ".tsx", ".js", ".jsx"],
    },
    {
        "name": "gdformat",
        "cmd": ["gdformat"],
        "extensions": [".gd"],
    },
]


def _iso8601_timestamp() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix."""
    ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    # Convert +00:00 to Z
    return ts.replace("+00:00", "Z")


def _get_staged_files(repo: Path) -> tuple[list[str], dict[str, Any] | None]:
    """Get list of staged files via git diff --cached --name-only.

    Returns: (file_list, error_dict_or_none)
    If error, returns ([], error_dict) with FAIL status.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            msg = f"git diff failed: {result.stderr}"
            logger.error(msg)
            error = {
                "file": "git",
                "line": 0,
                "rule": "git_failed",
                "message": msg,
            }
            return [], error

        files = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        return files, None

    except (OSError, subprocess.TimeoutExpired) as e:
        msg = f"git error: {str(e)}"
        logger.error(msg)
        error = {
            "file": "git",
            "line": 0,
            "rule": "git_failed",
            "message": msg,
        }
        return [], error


def _filter_files_by_extensions(files: list[str], extensions: list[str]) -> list[str]:
    """Filter files by extension."""
    return [f for f in files if any(f.endswith(ext) for ext in extensions)]


def _detect_formatting_changes(repo: Path, files: list[str]) -> tuple[list[str], dict[str, Any] | None]:
    """Detect which files were modified by formatting.

    Uses git diff to compare working tree against index (staged state).
    Returns: (list of changed files, error_dict_or_none)
    """
    changed_files = []

    try:
        # Run git diff (working tree vs index)
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        # Parse changed files from output
        # NOTE: git diff returns returncode 0 with non-empty output when there are changes,
        # and returncode 1 when there are no changes. We check the output directly.
        diff_output = result.stdout
        if diff_output.strip():
            for line in diff_output.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Handle diff output format (lines starting with --- or +++)
                # Example: "--- a/test.py" or "+++ b/test.py" → extract "test.py"
                if line.startswith("---") or line.startswith("+++"):
                    # Format: "--- a/path/to/file" → extract path after "a/" or "b/"
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        path = parts[1]
                        # Remove "a/" or "b/" prefix
                        if path.startswith("a/"):
                            path = path[2:]
                        elif path.startswith("b/"):
                            path = path[2:]
                        if path in files:
                            changed_files.append(path)
                else:
                    # Direct filename format (from --name-only)
                    if line in files:
                        changed_files.append(line)

            # Deduplicate while preserving order
            seen = set()
            unique_files = []
            for f in changed_files:
                if f not in seen:
                    seen.add(f)
                    unique_files.append(f)
            changed_files = unique_files

        return changed_files, None

    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Error detecting changes via git diff: {e}")
        # Non-fatal; assume no changes
        return [], None


def _run_formatter(
    formatter_name: str,
    cmd: list[str],
    files: list[str],
    repo: Path,
) -> tuple[bool, str | None]:
    """Run a single formatter on files.

    Returns: (success: bool, error_message: str | None)
    """
    if not files:
        logger.info(f"No files to format with {formatter_name}")
        return True, None

    try:
        # Build full command
        full_cmd = cmd + files

        # Run formatter with timeout
        result = subprocess.run(
            full_cmd,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            error_msg = f"{formatter_name} exited with code {result.returncode}: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

        logger.info(f"Formatter {formatter_name} completed successfully")
        return True, None

    except subprocess.TimeoutExpired:
        error_msg = f"{formatter_name} timeout (exceeded 30s)"
        logger.error(error_msg)
        return False, error_msg
    except (OSError, ValueError) as e:
        error_msg = f"{formatter_name} error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def _git_add_files(repo: Path, files: list[str]) -> tuple[bool, str | None]:
    """Re-stage files via git add.

    Returns: (success: bool, error_message: str | None)
    """
    if not files:
        return True, None

    try:
        result = subprocess.run(
            ["git", "add"] + files,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            error_msg = f"git add failed: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

        logger.info(f"Re-staged {len(files)} files")
        return True, None

    except (OSError, subprocess.TimeoutExpired) as e:
        error_msg = f"git add error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def _format_message(
    formatters_applied: list[str],
    formatters_unavailable: list[str],
    formatting_changed: bool,
) -> str:
    """Format output message based on what happened."""
    applied_str = ", ".join(formatters_applied)

    if formatting_changed:
        if formatters_unavailable:
            unavailable_str = ", ".join(formatters_unavailable)
            return f"Formatted code with {applied_str} ({unavailable_str} skipped—not installed). Re-staged for review."
        else:
            return f"Formatted code with {applied_str}. Re-staged for review."
    else:
        # No changes
        if formatters_unavailable:
            unavailable_str = "; ".join(formatters_unavailable)
            return f"Code is already formatted ({applied_str}; {unavailable_str} not installed)."
        else:
            return f"Code is already formatted ({applied_str})."


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute formatting check gate.

    Inputs: ticket_id (optional, defaults to "M902-10")
    Returns: dict matching gate result schema with fields:
      - status: "PASS" or "FAIL"
      - gate: "formatting_check"
      - timestamp: ISO 8601 UTC
      - ticket_id: from inputs or default
      - message: human-readable summary
      - artifacts: list of re-staged files (empty if no changes)
      - duration_ms: elapsed time
      - formatting_changed: bool (optional)
      - formatters_applied: list of formatters run (optional)
      - violations: list of violation dicts (on FAIL)
    """
    start_time = time.time()
    ticket_id = inputs.get("ticket_id", "M902-10")
    repo = Path.cwd()

    violations: list[dict[str, Any]] = []
    formatters_applied: list[str] = []
    formatters_unavailable: list[str] = []
    formatting_changed = False
    artifacts: list[str] = []

    try:
        # Step 1: Get staged files
        staged_files, git_error = _get_staged_files(repo)
        if git_error:
            elapsed_ms = max(1, int((time.time() - start_time) * 1000))
            violations.append(git_error)
            return {
                "status": "FAIL",
                "gate": "formatting_check",
                "timestamp": _iso8601_timestamp(),
                "ticket_id": ticket_id,
                "message": f"Git failed: {git_error['message']}. See violations for details.",
                "artifacts": [],
                "violations": violations,
                "duration_ms": elapsed_ms,
            }

        # If no staged files, return early
        if not staged_files:
            elapsed_ms = max(1, int((time.time() - start_time) * 1000))
            return {
                "status": "PASS",
                "gate": "formatting_check",
                "timestamp": _iso8601_timestamp(),
                "ticket_id": ticket_id,
                "message": "Code is already formatted (black, ruff format, prettier, gdformat).",
                "artifacts": [],
                "formatting_changed": False,
                "formatters_applied": [],
                "duration_ms": elapsed_ms,
            }

        # Step 2: Run formatters in sequence (formatters modify working tree)
        for formatter_config in FORMATTERS:
            formatter_name = formatter_config["name"]
            cmd = formatter_config["cmd"]
            extensions = formatter_config["extensions"]

            # Filter files by extension
            files_to_format = _filter_files_by_extensions(staged_files, extensions)

            # Run formatter
            if files_to_format:
                success, error_msg = _run_formatter(
                    formatter_name,
                    cmd,
                    files_to_format,
                    repo,
                )
                if not success:
                    # Check if this is a "not found" error (formatter not installed)
                    if "not found" in (error_msg or "").lower() or "no such file" in (error_msg or "").lower():
                        # Gracefully degrade if formatter is not installed
                        logger.warning(f"Formatter {formatter_name} not installed; skipping")
                        formatters_unavailable.append(formatter_name)
                        violations.append({
                            "file": formatter_name,
                            "line": 0,
                            "rule": "formatter_unavailable",
                            "message": f"{formatter_name} not installed",
                        })
                        continue
                    else:
                        # Formatter error is a hard failure
                        elapsed_ms = max(1, int((time.time() - start_time) * 1000))
                        # Determine error type for violation rule
                        error_rule = "timeout" if "timeout" in (error_msg or "").lower() else "subprocess_error"
                        violations.append({
                            "file": formatter_name,
                            "line": 0,
                            "rule": error_rule,
                            "message": error_msg or f"{formatter_name} failed",
                        })
                        return {
                            "status": "FAIL",
                            "gate": "formatting_check",
                            "timestamp": _iso8601_timestamp(),
                            "ticket_id": ticket_id,
                            "message": f"Formatting failed: {error_msg}. See violations for details.",
                            "artifacts": [],
                            "violations": violations,
                            "duration_ms": elapsed_ms,
                        }

            formatters_applied.append(formatter_name)

        # Step 3: Detect changes (using git diff to find working tree changes)
        changed_files, _ = _detect_formatting_changes(repo, staged_files)
        formatting_changed = len(changed_files) > 0

        # Step 4: Re-stage if changes detected
        if formatting_changed:
            success, error_msg = _git_add_files(repo, changed_files)
            if not success:
                elapsed_ms = max(1, int((time.time() - start_time) * 1000))
                violations.append({
                    "file": "git",
                    "line": 0,
                    "rule": "git_failed",
                    "message": error_msg or "git add failed",
                })
                return {
                    "status": "FAIL",
                    "gate": "formatting_check",
                    "timestamp": _iso8601_timestamp(),
                    "ticket_id": ticket_id,
                    "message": f"Git failed: {error_msg}. See violations for details.",
                    "artifacts": [],
                    "violations": violations,
                    "duration_ms": elapsed_ms,
                }

            artifacts = changed_files

        # Step 5: Build success result
        message = _format_message(formatters_applied, formatters_unavailable, formatting_changed)
        elapsed_ms = max(1, int((time.time() - start_time) * 1000))

        result = {
            "status": "PASS",
            "gate": "formatting_check",
            "timestamp": _iso8601_timestamp(),
            "ticket_id": ticket_id,
            "message": message,
            "artifacts": artifacts,
            "formatting_changed": formatting_changed,
            "formatters_applied": formatters_applied,
            "duration_ms": elapsed_ms,
        }

        # Include violations if any WARN-level violations were recorded
        if violations:
            result["violations"] = violations

        return result

    except Exception as e:
        logger.exception(f"Unexpected error in formatting_check gate: {e}")
        elapsed_ms = max(1, int((time.time() - start_time) * 1000))
        return {
            "status": "FAIL",
            "gate": "formatting_check",
            "timestamp": _iso8601_timestamp(),
            "ticket_id": ticket_id,
            "message": f"Unexpected error: {str(e)}",
            "artifacts": [],
            "violations": [
                {
                    "file": "formatting_check",
                    "line": 0,
                    "rule": "subprocess_error",
                    "message": str(e),
                }
            ],
            "duration_ms": elapsed_ms,
        }
