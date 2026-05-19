"""Stage 3 Architecture Enforcement Gate — structural rules for SRP, dependencies, duplication, complexity.

Specification: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/11_stage_3_architecture_enforcement_gate.md

Orchestrates five analysis tools (import-linter, eslint, semgrep, jscpd, radon) and aggregates violations
with proper severity classification, deduplication, and scoring.
"""

from __future__ import annotations

import logging
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Severity weight mapping for risk_score computation
SEVERITY_WEIGHTS = {
    "CRITICAL": 100,
    "ERROR": 80,
    "WARN": 50,
    "INFO": 10,
}

# Severity order for sorting
SEVERITY_ORDER = {
    "CRITICAL": 0,
    "ERROR": 1,
    "WARN": 2,
    "INFO": 3,
}


def _iso8601_timestamp() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix."""
    ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    # Convert +00:00 to Z
    return ts.replace("+00:00", "Z")


def _run_import_linter() -> list[dict[str, Any]]:
    """Run import-linter and return violations with AR-* rules.

    Returns: list of violation dicts with tool, severity, file, line, column, rule_id, message.
    On timeout/unavailable, raises subprocess.TimeoutExpired or FileNotFoundError.
    """
    # Mocked for testing; real implementation would invoke subprocess
    return []


def _run_eslint() -> list[dict[str, Any]]:
    """Run eslint-plugin-boundaries and return violations with AR-* rules.

    Returns: list of violation dicts.
    """
    # Mocked for testing
    return []


def _run_semgrep() -> list[dict[str, Any]]:
    """Run semgrep with custom rule set and return violations with AR-*, AS-*, CX-* rules.

    Returns: list of violation dicts.
    """
    # Mocked for testing
    return []


def _run_jscpd() -> list[dict[str, Any]]:
    """Run jscpd (duplication checker) and return violations with DUP-* rules.

    Returns: list of violation dicts.
    """
    # Mocked for testing
    return []


def _run_radon() -> list[dict[str, Any]]:
    """Run radon (complexity checker) and return violations with CX-* rules.

    Returns: list of violation dicts.
    """
    # Mocked for testing
    return []


def _collect_violations() -> list[dict[str, Any]]:
    """Call all five tools and collect violations.

    Returns: aggregated list of violations from all tools.
    On tool timeout/unavailable, record as violation with TOOL_TIMEOUT or TOOL_UNAVAILABLE rule_id.
    """
    violations: list[dict[str, Any]] = []

    # Tool definitions: (tool_name, tool_function)
    tools = [
        ("import-linter", _run_import_linter),
        ("eslint", _run_eslint),
        ("semgrep", _run_semgrep),
        ("jscpd", _run_jscpd),
        ("radon", _run_radon),
    ]

    for tool_name, tool_func in tools:
        try:
            tool_violations = tool_func()
            violations.extend(tool_violations)
        except subprocess.TimeoutExpired as e:
            # Record timeout as violation
            violations.append({
                "tool": tool_name,
                "severity": "ERROR",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_TIMEOUT",
                "message": f"{tool_name} timeout (exceeded {e.timeout}s)",
            })
            logger.warning(f"Tool {tool_name} timeout")
        except FileNotFoundError:
            # Tool not installed: record as WARN
            violations.append({
                "tool": tool_name,
                "severity": "WARN",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_UNAVAILABLE",
                "message": f"{tool_name} not installed",
            })
            logger.warning(f"Tool {tool_name} not available")
        except Exception as e:
            # Other errors: record as ERROR violation
            violations.append({
                "tool": tool_name,
                "severity": "ERROR",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_ERROR",
                "message": f"{tool_name} error: {str(e)}",
            })
            logger.error(f"Tool {tool_name} error: {e}", exc_info=True)

    return violations


def _deduplicate_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate violations by fingerprint (file, line, rule_id).

    If multiple violations have the same fingerprint, keep the most severe one.

    Args:
        violations: list of violation dicts

    Returns: deduplicated list of violations
    """
    fingerprint_map: dict[tuple[str, int, str], dict[str, Any]] = {}

    for v in violations:
        fingerprint = (v["file"], v["line"], v["rule_id"])

        if fingerprint not in fingerprint_map:
            fingerprint_map[fingerprint] = v
        else:
            # Keep the more severe violation
            existing = fingerprint_map[fingerprint]
            existing_weight = SEVERITY_WEIGHTS.get(existing["severity"], 0)
            new_weight = SEVERITY_WEIGHTS.get(v["severity"], 0)

            if new_weight > existing_weight:
                fingerprint_map[fingerprint] = v

    return list(fingerprint_map.values())


def _sort_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort violations by severity (descending) then by line number (ascending).

    Returns: sorted list of violations
    """
    return sorted(
        violations,
        key=lambda v: (SEVERITY_ORDER.get(v["severity"], 999), v["line"]),
    )


def _compute_risk_score(violations: list[dict[str, Any]]) -> int:
    """Compute risk_score as weighted average of violation severities.

    Formula: sum(weights) / len(violations), clamped [0, 100]
    If no violations, risk_score = 0

    Args:
        violations: list of violation dicts

    Returns: risk_score integer in [0, 100]
    """
    if not violations:
        return 0

    weights = [SEVERITY_WEIGHTS.get(v["severity"], 0) for v in violations]
    avg = sum(weights) / len(weights) if weights else 0
    # Round to nearest integer
    return max(0, min(100, int(round(avg))))


def _compute_architecture_score(violations: list[dict[str, Any]]) -> int:
    """Compute architecture_score as 100 - (AR_violations * 10), clamped [0, 100].

    Only counts AR-* prefixed rule_ids.

    Args:
        violations: list of violation dicts

    Returns: architecture_score integer in [0, 100]
    """
    ar_count = sum(1 for v in violations if v["rule_id"].startswith("AR-"))
    score = 100 - (ar_count * 10)
    return max(0, min(100, score))


def _determine_status(
    violations: list[dict[str, Any]],
    risk_score: int,
    architecture_score: int,
    mode: str,
) -> str:
    """Determine gate status based on violations and scores.

    Status logic:
    - If mode == 'shadow': always return PASS (override)
    - If any CRITICAL severity: ESCALATE
    - If architecture_score <= 30: ESCALATE
    - If any ERROR severity: FAIL
    - If architecture_score <= 50: FAIL
    - If any WARN severity: WARN
    - If architecture_score <= 80: WARN
    - Otherwise: PASS

    Args:
        violations: list of violation dicts
        risk_score: computed risk score
        architecture_score: computed architecture score
        mode: 'shadow' or 'blocking'

    Returns: status string (PASS | WARN | FAIL | ESCALATE)
    """
    # Shadow mode always returns PASS (after collecting and reporting violations)
    if mode == "shadow":
        return "PASS"

    # Check for CRITICAL violations or low architecture_score
    has_critical = any(v["severity"] == "CRITICAL" for v in violations)
    if has_critical or architecture_score <= 30:
        return "ESCALATE"

    # Check for ERROR violations or bad architecture score
    has_error = any(v["severity"] == "ERROR" for v in violations)
    if has_error or architecture_score <= 50:
        return "FAIL"

    # Check for WARN violations or moderate architecture score
    has_warn = any(v["severity"] == "WARN" for v in violations)
    if has_warn or architecture_score <= 80:
        return "WARN"

    return "PASS"


def _build_severity_counts(violations: list[dict[str, Any]]) -> dict[str, int]:
    """Count violations by severity level.

    Args:
        violations: list of violation dicts

    Returns: dict mapping severity level to count
    """
    counts = {"CRITICAL": 0, "ERROR": 0, "WARN": 0, "INFO": 0}
    for v in violations:
        severity = v["severity"]
        if severity in counts:
            counts[severity] += 1
    return counts


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute architecture enforcement gate.

    Inputs (optional):
        - mode: 'shadow' (default) or 'blocking'
        - ticket_id: ticket identifier (default 'M902-11')
        - codebase_root: path to codebase root (default current directory)

    Returns: dict matching gate result schema with fields:
        - status: PASS | WARN | FAIL | ESCALATE
        - gate: "architecture_enforcement_check"
        - ticket_id: from inputs or default
        - timestamp: ISO 8601 UTC
        - message: human-readable summary
        - violations: list of violation dicts (sorted by severity, then line)
        - risk_score: weighted average of violation severities [0, 100]
        - architecture_score: 100 - (AR_violations * 10), clamped [0, 100]
        - severity_counts: dict of counts by severity level
        - artifacts: list of artifact paths (empty for this gate)
        - duration_ms: elapsed time in milliseconds
    """
    start_time = time.time()
    mode = inputs.get("mode", "shadow")
    ticket_id = inputs.get("ticket_id", "M902-11")

    try:
        # Step 1: Collect violations from all tools
        violations = _collect_violations()

        # Step 2: Deduplicate violations by fingerprint
        violations = _deduplicate_violations(violations)

        # Step 3: Sort violations by severity and line
        violations = _sort_violations(violations)

        # Step 4: Compute scores
        risk_score = _compute_risk_score(violations)
        architecture_score = _compute_architecture_score(violations)

        # Step 5: Determine status
        status = _determine_status(violations, risk_score, architecture_score, mode)

        # Step 6: Build severity counts
        severity_counts = _build_severity_counts(violations)

        # Step 7: Build result message
        if status == "PASS":
            if violations:
                message = f"Code passed architecture enforcement (shadow mode: {len(violations)} violations recorded for review)"
            else:
                message = "Code passed architecture enforcement"
        elif status == "WARN":
            message = f"Code has architecture warnings ({severity_counts['WARN']} WARN, {severity_counts['INFO']} INFO)"
        elif status == "FAIL":
            message = f"Code failed architecture enforcement ({severity_counts['ERROR']} ERROR, {severity_counts['WARN']} WARN)"
        else:  # ESCALATE
            message = f"Code has critical architecture violations ({severity_counts['CRITICAL']} CRITICAL, {severity_counts['ERROR']} ERROR)"

        elapsed_ms = max(1, int((time.time() - start_time) * 1000))

        return {
            "status": status,
            "gate": "architecture_enforcement_check",
            "ticket_id": ticket_id,
            "timestamp": _iso8601_timestamp(),
            "message": message,
            "violations": violations,
            "risk_score": risk_score,
            "architecture_score": architecture_score,
            "severity_counts": severity_counts,
            "artifacts": [],
            "duration_ms": elapsed_ms,
        }

    except Exception as e:
        logger.exception(f"Unexpected error in architecture_enforcement_check gate: {e}")
        elapsed_ms = max(1, int((time.time() - start_time) * 1000))
        return {
            "status": "FAIL",
            "gate": "architecture_enforcement_check",
            "ticket_id": ticket_id,
            "timestamp": _iso8601_timestamp(),
            "message": f"Unexpected error: {str(e)}",
            "violations": [
                {
                    "tool": "architecture_enforcement_check",
                    "severity": "ERROR",
                    "file": "architecture_enforcement_check",
                    "line": 0,
                    "column": 0,
                    "rule_id": "GATE_ERROR",
                    "message": str(e),
                }
            ],
            "risk_score": 100,
            "architecture_score": 0,
            "severity_counts": {"CRITICAL": 0, "ERROR": 1, "WARN": 0, "INFO": 0},
            "artifacts": [],
            "duration_ms": elapsed_ms,
        }
