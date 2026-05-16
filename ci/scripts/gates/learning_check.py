"""
Learning gate — forbidden phrase detection in checkpoint outputs (M902-06).

Specification: project_board/specs/902_06_learning_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/06_per_stage_gate_improvements.md

Detects:
  - Forbidden phrases in learning output files (hack, temporary, XXX, KLUDGE, etc.)
  - Reads policy from YAML config file
  - Scans all .md files under project_board/checkpoints/

JSON Output: matches M902-01 gate schema with violations[], remediation_hints[].
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _load_policy(policy_file: str | None) -> dict[str, Any]:
    """Load forbidden phrase policy from YAML file.

    Returns default policy if file missing or invalid.
    """
    default_policy = {
        "forbidden_phrases": [
            {"phrase": "hack", "case_sensitive": False, "whole_word": True},
            {"phrase": "temporary", "case_sensitive": False, "whole_word": True},
            {"phrase": "XXX", "case_sensitive": True, "whole_word": True},
            {"phrase": "KLUDGE", "case_sensitive": False, "whole_word": True},
            {"phrase": "workaround", "case_sensitive": False, "whole_word": True},
        ]
    }

    if not policy_file:
        return default_policy

    policy_path = Path(policy_file)
    if not policy_path.exists():
        return default_policy

    try:
        if yaml is None:
            return default_policy
        content = policy_path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(content)
        if isinstance(loaded, dict) and "forbidden_phrases" in loaded:
            return loaded
        return default_policy
    except (OSError, yaml.YAMLError):
        # Invalid YAML or read error; use defaults
        return default_policy


def _enumerate_learning_files(
    checkpoints_dir: Path,
) -> list[Path]:
    """Find all learning output .md files under checkpoints directory.

    Excludes CHECKPOINTS.md, README.md, and files under /specs/.
    """
    if not checkpoints_dir.exists():
        return []

    files: list[Path] = []
    for md_file in checkpoints_dir.rglob("*.md"):
        # Exclude index/spec files
        if md_file.name in ["CHECKPOINTS.md", "README.md"]:
            continue
        if "/specs/" in str(md_file):
            continue
        files.append(md_file)

    return files


def _extract_content_after_frontmatter(text: str) -> str:
    """Skip YAML frontmatter (lines between --- markers at start)."""
    lines = text.split("\n")
    if not lines or not lines[0].startswith("---"):
        return text

    # Find closing ---
    for i in range(1, len(lines)):
        if lines[i].startswith("---"):
            return "\n".join(lines[i + 1 :])

    return text


def _match_phrase(text: str, phrase_config: dict[str, Any]) -> list[tuple[int, str]]:
    """Find all matches of a phrase in text.

    Returns:
        list of (line_number, context) tuples
    """
    phrase = phrase_config.get("phrase", "")
    case_sensitive = phrase_config.get("case_sensitive", False)
    whole_word = phrase_config.get("whole_word", True)

    if not phrase:
        return []

    if whole_word:
        if case_sensitive:
            pattern = rf"\b{re.escape(phrase)}\b"
        else:
            pattern = rf"\b{re.escape(phrase)}\b"
            text = text
    else:
        if case_sensitive:
            pattern = re.escape(phrase)
        else:
            pattern = re.escape(phrase)

    matches: list[tuple[int, str]] = []
    regex_flags = 0 if case_sensitive else re.IGNORECASE

    for line_num, line in enumerate(text.split("\n"), start=1):
        if re.search(pattern, line, flags=regex_flags):
            matches.append((line_num, line.strip()))

    return matches


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute learning gate.

    Inputs:
        - checkpoints_dir: str, path to project_board/checkpoints
        - policy_file: str (optional), path to policy YAML file

    Returns:
        dict matching M902-01 gate schema
    """
    checkpoints_dir_str = inputs.get("checkpoints_dir", "project_board/checkpoints")
    policy_file = inputs.get("policy_file", "project_board/902_06_learning_gate_policy.yml")

    checkpoints_dir = Path(checkpoints_dir_str)
    policy = _load_policy(policy_file)

    # Enumerate learning files
    learning_files = _enumerate_learning_files(checkpoints_dir)

    violations: list[dict[str, Any]] = []
    remediation_hints: list[str] = []

    # Scan each learning file
    for file_path in learning_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            violations.append(
                {
                    "file": str(file_path),
                    "line": 0,
                    "rule": "file_read_error",
                    "message": f"Failed to read learning file: {e}",
                    "severity": "WARN",
                }
            )
            continue

        # Skip YAML frontmatter
        content = _extract_content_after_frontmatter(content)

        # Truncate large files
        max_size = 10 * 1024 * 1024
        if len(content) > max_size:
            content = content[:max_size]

        # Check each forbidden phrase
        for phrase_config in policy.get("forbidden_phrases", []):
            matches = _match_phrase(content, phrase_config)
            for line_num, context in matches:
                violations.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "rule": "forbidden_phrase_found",
                        "message": f"Forbidden phrase '{phrase_config.get('phrase')}' found: '{context}'",
                        "severity": "ERROR",
                    }
                )
                remediation_hints.append(
                    f"Remove or rephrase the forbidden phrase in {file_path}:{line_num}"
                )

    status = "FAIL" if violations else "PASS"

    return {
        "status": status,
        "gate": "learning_check",
        "violations": violations,
        "remediation_hints": remediation_hints,
        "message": (
            f"Found {len(violations)} forbidden phrases in {len(learning_files)} learning files"
            if violations
            else f"No forbidden phrases found in {len(learning_files)} learning files"
        ),
    }
