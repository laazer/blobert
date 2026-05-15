#!/usr/bin/env python3
"""
Aggregation rules for M902-04 violation deduplication and severity merging.

Handles:
  - Deduplication: (file, line, rule_id) tuple matching
  - Severity merging: CRITICAL > ERROR > WARN > INFO
  - Tool priority ordering: ruff > mypy > bandit > ... (configurable)
  - Deterministic output ordering: sorted by (file, line)

Usage:
    aggregated = aggregate_violations(violations)
"""

from __future__ import annotations

from typing import Any

# Tool priority (higher = higher priority)
_TOOL_PRIORITY = {
    "ruff": 100,
    "mypy": 90,
    "bandit": 80,
    "vulture": 70,
    "semgrep": 60,
    "wemake-python-styleguide": 50,
    "eslint": 40,
    "gdformat": 30,
    "gdlint": 20,
    "jscpd": 10,
}

# Severity order
_SEVERITY_ORDER = {
    "CRITICAL": 4,
    "ERROR": 3,
    "WARN": 2,
    "INFO": 1,
}


def aggregate_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate violations from multiple tools.

    Deduplicates by (file, line, rule_id) tuple. When duplicates are found,
    retains the violation with highest severity. Tool priority is used as a
    tiebreaker.

    Args:
        violations: List of violation dicts from multiple tools

    Returns:
        List of deduplicated violations, sorted by (file, line)
    """
    if not violations:
        return []

    # Build deduplication map: (file, line, rule_id) -> violation
    seen = {}

    for violation in violations:
        file = violation.get("file", "unknown")
        line = violation.get("line", 0)
        rule_id = violation.get("rule_id", "unknown")
        severity = violation.get("severity", "INFO")
        tool = violation.get("tool", "unknown")

        key = (file, line, rule_id)

        if key not in seen:
            seen[key] = violation
        else:
            # Determine which to keep: higher severity wins
            existing = seen[key]
            existing_severity = existing.get("severity", "INFO")

            if _SEVERITY_ORDER.get(severity, 0) > _SEVERITY_ORDER.get(existing_severity, 0):
                # New violation has higher severity
                seen[key] = violation
            elif _SEVERITY_ORDER.get(severity, 0) == _SEVERITY_ORDER.get(existing_severity, 0):
                # Same severity: use tool priority as tiebreaker
                existing_tool = existing.get("tool", "unknown")
                new_priority = _TOOL_PRIORITY.get(tool, 0)
                existing_priority = _TOOL_PRIORITY.get(existing_tool, 0)

                if new_priority > existing_priority:
                    seen[key] = violation

    # Convert to list and sort by (file, line) for deterministic ordering
    result = list(seen.values())
    result.sort(
        key=lambda v: (v.get("file", "unknown"), v.get("line", 0))
    )

    return result
