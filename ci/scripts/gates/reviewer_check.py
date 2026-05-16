"""
Reviewer gate — TODO/FIXME scanning and suppression auditing (M902-06).

Specification: project_board/specs/902_06_reviewer_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md

Detects:
  - New TODO/FIXME/HACK/XXX/KLUDGE comments (prefixed '+' in git diff)
  - Suppressions without issue links (# noqa, # pylint, etc. without M\d{3}-\d{2} or GH-\d+ or https://)
  - Graceful fallback if git unavailable

JSON Output: matches M902-01 gate schema with violations[], remediation_hints[].
"""

from __future__ import annotations

import re
import subprocess
from typing import Any


def _run_git_diff(repo_path: str | None = None) -> tuple[str, bool]:
    """Run git diff --cached and return output.

    Returns:
        (diff_output, success) — if git fails, returns ("", False)
    """
    try:
        cmd = ["git", "diff", "--cached"]
        if repo_path:
            cmd.extend(["-C", repo_path])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return "", False
        return result.stdout, True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", False


def _parse_diff_lines(diff_output: str) -> list[tuple[str, int, str]]:
    """Parse git diff and extract new lines with file and line number.

    Returns:
        list of (file, line_number, line_text) tuples for lines starting with '+'
    """
    lines: list[tuple[str, int, str]] = []
    current_file = ""
    line_number = 0

    for line in diff_output.split("\n"):
        # Track current file
        if line.startswith("+++"):
            # Extract filename from +++ b/path/to/file
            current_file = line[6:] if len(line) > 6 else ""
            continue

        # Track line number from hunk header
        if line.startswith("@@"):
            # Parse @@ -old_start,old_count +new_start,new_count @@
            match = re.search(r"\+(\d+)", line)
            if match:
                line_number = int(match.group(1)) - 1

        # Extract new lines (prefixed with '+' but not '+++')
        if line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            content = line[1:]  # Remove the '+' prefix
            lines.append((current_file, line_number, content))

    return lines


def _detect_todo_keywords(text: str) -> list[tuple[str, int]]:
    """Detect TODO/FIXME/HACK/XXX/KLUDGE keywords (case-insensitive).

    Returns:
        list of (keyword, position_in_text) tuples
    """
    keywords = [
        "TODO",
        "FIXME",
        "HACK",
        "XXX",
        "KLUDGE",
    ]
    matches: list[tuple[str, int]] = []

    for keyword in keywords:
        # Case-insensitive search with word boundary
        pattern = rf"\b{keyword}\b"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append((keyword.upper(), match.start()))

    return matches


def _has_issue_link(text: str) -> bool:
    """Check if text contains an issue link (M\d{3}-\d{2}, GH-\d+, or https://)."""
    patterns = [
        r"M\d{3}-\d{2}",  # M902-03
        r"GH-\d+",  # GH-1234
        r"https?://",  # https://...
    ]
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def _detect_suppressions_without_links(text: str) -> bool:
    """Detect suppressions without issue links (# noqa, # pylint, etc.)."""
    suppression_patterns = [
        r"#\s*noqa",  # Python noqa
        r"#\s*pylint",  # Python pylint
        r"//\s*eslint-disable",  # JavaScript eslint
        r"//\s*ts-ignore",  # TypeScript ignore
        r"#\s*nosemgrep",  # Semgrep suppression
    ]

    for pattern in suppression_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Found a suppression, check if it has an issue link
            if not _has_issue_link(text):
                return True

    return False


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute reviewer gate.

    Inputs:
        - repo_path: str (optional), path to git repository

    Returns:
        dict matching M902-01 gate schema
    """
    repo_path = inputs.get("repo_path", None)

    # Get staged diff
    diff_output, git_success = _run_git_diff(repo_path)

    if not git_success:
        return {
            "status": "PASS",
            "gate": "reviewer_check",
            "violations": [],
            "remediation_hints": [],
            "message": "git not available or not a git repository; skipping TODO/FIXME scan",
        }

    # Parse diff to extract new lines
    new_lines = _parse_diff_lines(diff_output)

    violations: list[dict[str, Any]] = []
    remediation_hints: list[str] = []

    # Scan each new line for TODO/FIXME and suppressions
    for file, line_num, content in new_lines:
        # Check for TODO/FIXME keywords
        todo_matches = _detect_todo_keywords(content)
        for keyword, pos in todo_matches:
            violations.append(
                {
                    "file": file,
                    "line": line_num,
                    "rule": "new_todo_found",
                    "message": f"New {keyword} comment found: '{content.strip()}'",
                    "severity": "WARN",
                }
            )
            remediation_hints.append(
                f"Resolve {keyword} or document the issue ID: {file}:{line_num}"
            )

        # Check for suppressions without issue links
        if _detect_suppressions_without_links(content):
            violations.append(
                {
                    "file": file,
                    "line": line_num,
                    "rule": "suppression_without_issue",
                    "message": f"Suppression without issue link: '{content.strip()}'",
                    "severity": "WARN",
                }
            )
            remediation_hints.append(
                f"Add issue link (M###-##, GH-###, or https://...) to suppression: {file}:{line_num}"
            )

    status = "WARN" if violations else "PASS"

    return {
        "status": status,
        "gate": "reviewer_check",
        "violations": violations,
        "remediation_hints": remediation_hints,
        "message": (
            f"Found {len([v for v in violations if v['rule'] == 'new_todo_found'])} "
            f"TODO/FIXME comments and "
            f"{len([v for v in violations if v['rule'] == 'suppression_without_issue'])} "
            "suppressions without issue links in staged changes."
            if violations
            else "No new TODO/FIXME comments or suppression issues detected."
        ),
    }
