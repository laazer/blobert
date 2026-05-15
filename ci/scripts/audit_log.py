#!/usr/bin/env python3
"""
Audit event logging module for M902-04 Handoff Metadata & Risk Escalation.

Provides functions to emit structured audit events in JSON Lines format to
`ci/artifacts/audit-logs/`. All writes are append-only and thread-safe.

Event Types:
  - gate_started: Gate execution begins
  - tool_invoked: A tool (ruff, mypy, etc.) is invoked
  - tool_finished: A tool completes execution
  - violation_added: A rule violation is detected
  - escalation_triggered: An escalation detector triggers
  - audit_error: An error occurs during audit logging

No secrets are stored in logs. Errors are logged to stderr, not to audit logs
(to avoid recursion).

Usage:
    import audit_log
    audit_log.emit_gate_started("run-001", "static_analysis_check", "M902-04", "shadow", "Spec Agent", "Test Designer")
    audit_log.emit_tool_invoked("run-001", "ruff", 60)
    audit_log.emit_violation_added("run-001", "E501", "test.py", 42, "WARN", "Line too long")
    audit_log.emit_escalation_triggered("run-001", "governance_file_modifications", "CRITICAL", "HIGH")
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AUDIT_LOG_BASE = Path("ci/artifacts/audit-logs")


def _emit_event(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    event_type: str,
    event_data: dict[str, Any],
    mode: str = "shadow"
) -> None:
    """Internal function to emit an audit event to the log file.

    Args:
        run_id: Unique run identifier (UUID or correlation ID)
        gate_name: Name of the gate (e.g., "static_analysis_check")
        ticket_id: Ticket ID (e.g., "M902-04") or None
        event_type: Event type (gate_started, tool_invoked, etc.)
        event_data: Event-specific payload dict
        mode: Execution mode ("shadow" or "blocking")

    On error: logs to stderr and continues (non-blocking).
    """
    try:
        # Build path: ci/artifacts/audit-logs/<gate-name>/<YYYY-MM-DD>/<timestamp>-<mode>.jsonl
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        timestamp_str = now.strftime("%Y-%m-%dT%H-%M-%SZ")
        filename = f"{timestamp_str}-{mode}.jsonl"

        log_path = _AUDIT_LOG_BASE / gate_name / date_str / filename

        # Auto-create directory hierarchy
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Build event object
        event = {
            "timestamp": now.isoformat(),
            "run_id": run_id,
            "gate_name": gate_name,
            "ticket_id": ticket_id,
            "event_type": event_type,
            "event_data": event_data
        }

        # Append to file (JSON Lines format: one JSON object per line)
        with log_path.open("a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    except (OSError, IOError) as e:
        # Log error to stderr but do not block gate execution
        print(f"ERROR: Failed to write audit log: {e}", file=sys.stderr)


def emit_gate_started(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    mode: str,
    upstream_agent: str,
    downstream_agent: str
) -> None:
    """Emit gate_started event when gate execution begins.

    Args:
        run_id: Unique run identifier
        gate_name: Name of the gate
        ticket_id: Ticket ID or None
        mode: "shadow" or "blocking"
        upstream_agent: Name of upstream agent
        downstream_agent: Name of downstream agent
    """
    _emit_event(
        run_id,
        gate_name,
        ticket_id,
        "gate_started",
        {
            "mode": mode,
            "upstream_agent": upstream_agent,
            "downstream_agent": downstream_agent
        },
        mode
    )


def emit_tool_invoked(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    tool_name: str,
    timeout_s: int | None,
    mode: str = "shadow"
) -> None:
    """Emit tool_invoked event when a tool (ruff, mypy, etc.) is invoked.

    Args:
        run_id: Unique run identifier
        gate_name: Name of the gate
        ticket_id: Ticket ID or None
        tool_name: Name of the tool
        timeout_s: Timeout in seconds or None
        mode: Execution mode
    """
    _emit_event(
        run_id,
        gate_name,
        ticket_id,
        "tool_invoked",
        {
            "tool_name": tool_name,
            "timeout_s": timeout_s
        },
        mode
    )


def emit_tool_finished(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    tool_name: str,
    exit_code: int,
    duration_ms: int,
    mode: str = "shadow"
) -> None:
    """Emit tool_finished event when a tool completes execution.

    Args:
        run_id: Unique run identifier
        gate_name: Name of the gate
        ticket_id: Ticket ID or None
        tool_name: Name of the tool
        exit_code: Exit code from tool
        duration_ms: Elapsed time in milliseconds
        mode: Execution mode
    """
    _emit_event(
        run_id,
        gate_name,
        ticket_id,
        "tool_finished",
        {
            "tool_name": tool_name,
            "exit_code": exit_code,
            "duration_ms": duration_ms
        },
        mode
    )


def emit_violation_added(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    rule_id: str,
    file: str,
    line: int | None,
    severity: str,
    message: str,
    mode: str = "shadow"
) -> None:
    """Emit violation_added event when a rule violation is detected.

    Args:
        run_id: Unique run identifier
        gate_name: Name of the gate
        ticket_id: Ticket ID or None
        rule_id: Rule identifier (e.g., "E501", "AR-01")
        file: File path relative to repo root
        line: Line number (1-indexed) or None
        severity: Severity level (CRITICAL, ERROR, WARN, INFO)
        message: Human-readable violation description
        mode: Execution mode
    """
    _emit_event(
        run_id,
        gate_name,
        ticket_id,
        "violation_added",
        {
            "rule_id": rule_id,
            "file": file,
            "line": line,
            "severity": severity,
            "message": message
        },
        mode
    )


def emit_escalation_triggered(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    detector: str,
    severity: str,
    confidence: str,
    details: str,
    mode: str = "shadow"
) -> None:
    """Emit escalation_triggered event when a detector triggers.

    Args:
        run_id: Unique run identifier
        gate_name: Name of the gate
        ticket_id: Ticket ID or None
        detector: Detector name (e.g., "governance_file_modifications")
        severity: Escalation severity (CRITICAL, HIGH, MEDIUM, LOW)
        confidence: Confidence level (HIGH, MEDIUM, LOW)
        details: Explanation of escalation trigger
        mode: Execution mode
    """
    _emit_event(
        run_id,
        gate_name,
        ticket_id,
        "escalation_triggered",
        {
            "detector": detector,
            "severity": severity,
            "confidence": confidence,
            "details": details
        },
        mode
    )


def emit_audit_error(
    run_id: str,
    gate_name: str,
    ticket_id: str | None,
    error_type: str,
    details: str,
    mode: str = "shadow"
) -> None:
    """Emit audit_error event when audit logging fails.

    Args:
        run_id: Unique run identifier
        gate_name: Name of the gate
        ticket_id: Ticket ID or None
        error_type: Error category (e.g., "disk_full", "permission_denied")
        details: Error details
        mode: Execution mode
    """
    _emit_event(
        run_id,
        gate_name,
        ticket_id,
        "audit_error",
        {
            "error_type": error_type,
            "details": details
        },
        mode
    )


def get_audit_log_references(
    gate_name: str,
    date: str,
    mode: str,
    lines: list[int] | None = None
) -> list[str]:
    """Get audit log entry references for a given gate/date/mode.

    Args:
        gate_name: Name of the gate
        date: Date string (YYYY-MM-DD)
        mode: Execution mode (shadow or blocking)
        lines: Optional list of line numbers to reference. If None, returns path only.

    Returns:
        List of audit log references (format: "ci/artifacts/audit-logs/<gate>/<date>/<timestamp>-<mode>.jsonl:line-N")
    """
    # Find the most recent log file for this gate/date/mode
    log_dir = _AUDIT_LOG_BASE / gate_name / date
    if not log_dir.exists():
        return []

    # Find files matching the pattern
    matching_files = list(log_dir.glob(f"*-{mode}.jsonl"))
    if not matching_files:
        return []

    # Use the most recent file
    most_recent = max(matching_files, key=lambda p: p.stat().st_mtime)
    rel_path = most_recent.relative_to(Path.cwd())

    if lines is None:
        return [str(rel_path)]

    return [f"{str(rel_path)}:line-{line}" for line in lines]
