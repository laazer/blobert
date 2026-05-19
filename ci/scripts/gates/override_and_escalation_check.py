"""M902-15 Override & Escalation System Gate.

Validates code suppressions (# blobert-ignore-next-line) for proper justification,
expiration, and escalates repeated/architecture/security bypasses for human review.

Produces audit log and escalation violations.

Spec: project_board/specs/902_15_override_escalation_spec.md v1.0 FROZEN
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/15_stage_7_override_and_escalation_system.md
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional, TypedDict


# ---------------------------------------------------------------------------
# TypedDict Definitions (Fixed-Schema Structures)
# ---------------------------------------------------------------------------


class ParsedSuppression(TypedDict):
    """Parsed suppression comment metadata.

    Fields extracted from the # blobert-ignore-next-line comment.
    """

    reason: str
    ticket: str
    until_date: Optional[str]


class SuppressionFileRecord(TypedDict):
    """Intermediate suppression record found in file scan.

    Contains file location, line number, and parsed metadata from comment.
    """

    file: str
    line: int
    parsed: ParsedSuppression
    rule_id: Optional[str]


class SuppressionRecord(TypedDict):
    """Audit log suppression record (fixed-schema).

    Complete record with validation results and escalation details.
    """

    file: str
    line: int
    rule_id: Optional[str]
    reason: str
    ticket: str
    expiration_date: Optional[str]
    first_seen: str
    repeat_count: int
    escalation_reasons: list[str]
    validation_errors: Optional[list[str]]


class AuditLogEntry(TypedDict):
    """Audit log JSON root structure."""

    version: str
    timestamp: str
    total_suppressions: int
    total_escalations: int
    total_files_scanned: int
    suppressions: list[SuppressionRecord]


class GateViolation(TypedDict):
    """Gate output violation record (M902-01 schema)."""

    file: str
    line: int
    rule: str
    message: str
    severity: str


class GateResult(TypedDict):
    """Gate result conforming to M902-01 schema."""

    version: str
    status: str
    gate: str
    upstream_agent: str
    downstream_agent: str
    ticket_id: str
    timestamp: str
    duration_ms: int
    message: str
    artifacts: list[dict[str, str]]
    violations: list[GateViolation]
    mode: str


# Suppression syntax regex from spec AC-01.1
SUPPRESSION_REGEX = re.compile(
    r'^\s*#\s+blobert-ignore-next-line:\s*reason="([^"]{10,200})",\s*ticket="([A-Z0-9\-]{3,20})"'
    r'(,\s*until="(\d{4}-\d{2}-\d{2})")?$',
    re.IGNORECASE,
)

# High-risk rule prefixes (AC-03.2)
HIGH_RISK_PREFIXES = ("AR-", "SE-", "AS-", "EXH-")

# Escalation reason enums (AC-05.5)
ESCALATION_REASON_REPEATED = "REPEATED_SUPPRESSION"
ESCALATION_REASON_HIGH_RISK = "HIGH_RISK_RULE"
ESCALATION_REASON_VALIDATION_ERROR = "VALIDATION_ERROR"
ESCALATION_REASON_EXPIRED = "EXPIRED"

# 50-line window for repeated suppression detection (AC-03.1)
REPEATED_SUPPRESSION_WINDOW = 50
REPEATED_SUPPRESSION_THRESHOLD = 3


def _get_changed_files(inputs: dict[str, Any], repo_root: str = ".") -> list[str]:
    """Get changed files from input or git diff.

    Args:
        inputs: Gate input dict
        repo_root: Repository root directory

    Returns:
        List of changed file paths (relative to repo root)
    """
    if "changed_files" in inputs and inputs["changed_files"]:
        return inputs["changed_files"]

    # Try git diff
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return []


def _read_file_lines(file_path: str) -> list[str]:
    """Read file and return lines.

    Args:
        file_path: Path to file

    Returns:
        List of lines (without newlines)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def _validate_reason(reason: str) -> tuple[bool, Optional[str]]:
    """Validate reason field.

    Args:
        reason: Reason text

    Returns:
        (is_valid, error_message)
    """
    if not reason or not reason.strip():
        return False, "Reason is empty"

    if len(reason) < 10:
        return False, f"Reason too short: {len(reason)} chars < 10 min"

    if len(reason) > 200:
        return False, f"Reason too long: {len(reason)} chars > 200 max"

    return True, None


def _validate_ticket(ticket: str) -> tuple[bool, Optional[str]]:
    """Validate ticket field format.

    Args:
        ticket: Ticket ID

    Returns:
        (is_valid, error_message)
    """
    pattern = r"^[A-Z0-9\-]{3,20}$"
    if not re.match(pattern, ticket):
        return False, f"Ticket format invalid: {ticket}"
    return True, None


def _validate_expiration(until_date_str: str) -> tuple[bool, Optional[str], Optional[bool]]:
    """Validate and check expiration date.

    Args:
        until_date_str: Expiration date in YYYY-MM-DD format

    Returns:
        (is_valid_format, error_message, is_expired)
    """
    if not until_date_str:
        return True, None, None

    # Validate format
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(date_pattern, until_date_str):
        return False, f"Invalid date format: {until_date_str} (expected YYYY-MM-DD)", None

    # Parse and compare
    try:
        until_date = datetime.datetime.strptime(until_date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        is_expired = until_date < today
        return True, None, is_expired
    except ValueError:
        return False, f"Invalid date value: {until_date_str}", None


def _get_current_timestamp_iso() -> str:
    """Get current timestamp in ISO 8601 UTC format.

    Returns:
        Timestamp string in format YYYY-MM-DDTHH-MM-SSZ
    """
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")


def _parse_suppression(
    comment: str,
) -> tuple[bool, Optional[ParsedSuppression]]:
    """Parse suppression comment.

    Args:
        comment: Comment line text

    Returns:
        (is_valid, parsed_dict)
    """
    match = SUPPRESSION_REGEX.match(comment)
    if not match:
        return False, None

    reason = match.group(1)
    ticket = match.group(2)
    until_date = match.group(4)

    return True, ParsedSuppression(
        reason=reason,
        ticket=ticket,
        until_date=until_date,
    )


def _find_suppressions_in_file(
    file_path: str,
) -> list[SuppressionFileRecord]:
    """Find all suppressions in a file.

    Args:
        file_path: Path to file to scan

    Returns:
        List of suppression records with file, line, and parsed metadata
    """
    lines = _read_file_lines(file_path)
    suppressions: list[SuppressionFileRecord] = []

    for i, line in enumerate(lines):
        is_valid, parsed = _parse_suppression(line)
        if is_valid and parsed:
            suppressions.append(SuppressionFileRecord(
                file=file_path,
                line=i + 1,  # 1-indexed
                parsed=parsed,
                rule_id=None,
            ))

    return suppressions


def _classify_high_risk(rule_id: Optional[str]) -> bool:
    """Check if rule_id is high-risk.

    Args:
        rule_id: Rule ID from violations

    Returns:
        True if high-risk prefix
    """
    if not rule_id:
        return False
    return any(rule_id.startswith(prefix) for prefix in HIGH_RISK_PREFIXES)


def _count_repeated_in_window(
    suppressions: list[SuppressionFileRecord],
    rule_id: Optional[str],
    file_path: str,
    target_line: int,
) -> int:
    """Count repetitions of a rule in a 50-line window.

    Args:
        suppressions: All suppressions for the file
        rule_id: Rule ID to count
        file_path: File path
        target_line: Target line for the suppression

    Returns:
        Count of suppressions in window
    """
    window_start = max(1, target_line - REPEATED_SUPPRESSION_WINDOW)
    window_end = target_line + REPEATED_SUPPRESSION_WINDOW

    count = 0
    for sup in suppressions:
        if (sup["file"] == file_path and
            sup["rule_id"] == rule_id and
            window_start <= sup["line"] <= window_end):
            count += 1

    return count


def _build_suppression_record(
    suppression: SuppressionFileRecord,
    violations: list[dict[str, Any]],
    all_suppressions: list[SuppressionFileRecord],
) -> SuppressionRecord:
    """Build a suppression record for the audit log.

    Args:
        suppression: Suppression with file, line, parsed metadata
        violations: Violations array from upstream (JSON boundary, remains dict[str, Any])
        all_suppressions: All suppressions found (for repeat counting)

    Returns:
        Audit log suppression record
    """
    file_path = suppression["file"]
    line = suppression["line"]
    parsed = suppression["parsed"]

    reason = parsed["reason"]
    ticket = parsed["ticket"]
    until_date = parsed["until_date"]

    # Find rule_id from violations (match by file/line)
    rule_id = None
    for v in violations:
        if v.get("file") == file_path and v.get("line") == line + 1:  # Suppression on line N suppresses line N+1
            rule_id = v.get("rule_id")
            break

    # Validate metadata
    validation_errors: list[str] = []

    is_valid_reason, reason_error = _validate_reason(reason)
    if not is_valid_reason and reason_error:
        validation_errors.append(reason_error)

    is_valid_ticket, ticket_error = _validate_ticket(ticket)
    if not is_valid_ticket and ticket_error:
        validation_errors.append(ticket_error)

    is_valid_expiration, expiration_error, is_expired = _validate_expiration(until_date)
    if not is_valid_expiration and expiration_error:
        validation_errors.append(expiration_error)

    # Detect escalations
    escalation_reasons: list[str] = []

    # Validation error escalation
    if validation_errors:
        escalation_reasons.append(ESCALATION_REASON_VALIDATION_ERROR)

    # Expiration escalation
    if is_valid_expiration and is_expired:
        escalation_reasons.append(ESCALATION_REASON_EXPIRED)

    # High-risk rule escalation
    if _classify_high_risk(rule_id):
        escalation_reasons.append(ESCALATION_REASON_HIGH_RISK)

    # Repeated suppression escalation
    repeat_count = _count_repeated_in_window(all_suppressions, rule_id, file_path, line)
    if repeat_count >= REPEATED_SUPPRESSION_THRESHOLD:
        escalation_reasons.append(ESCALATION_REASON_REPEATED)

    # Deduplicate escalation reasons
    escalation_reasons = list(set(escalation_reasons))
    escalation_reasons.sort()  # For determinism

    record: SuppressionRecord = SuppressionRecord(
        file=file_path,
        line=line,
        rule_id=rule_id,
        reason=reason,
        ticket=ticket,
        expiration_date=until_date,
        first_seen=_get_current_timestamp_iso(),
        repeat_count=repeat_count,
        escalation_reasons=escalation_reasons,
        validation_errors=validation_errors if validation_errors else None,
    )

    return record


def _sort_suppressions(suppressions: list[SuppressionRecord]) -> list[SuppressionRecord]:
    """Sort suppressions by file path then line number for determinism.

    Args:
        suppressions: List of suppression records

    Returns:
        Sorted list
    """
    return sorted(suppressions, key=lambda s: (s["file"], s["line"]))


def run(inputs: dict[str, Any]) -> GateResult:
    """Gate entry point.

    Args:
        inputs: Gate input dict with optional changed_files, violations, etc.
                (JSON boundary, remains dict[str, Any])

    Returns:
        Gate result dict conforming to M902-01 schema
    """
    start_time = time.time()

    # Extract inputs
    changed_files = _get_changed_files(inputs)
    violations: list[dict[str, Any]] = inputs.get("violations", [])
    issue_id = inputs.get("issue_id", "M902-15")
    ticket_id = inputs.get("ticket_id", "M902-15")
    upstream_agent = inputs.get("upstream_agent", "Agent Review")
    downstream_agent = inputs.get("downstream_agent", "Override Check")
    mode = inputs.get("mode", "shadow")

    # Scan changed files for suppressions
    all_suppressions: list[SuppressionFileRecord] = []
    scanned_files: set[str] = set()

    for file_path in changed_files:
        scanned_files.add(file_path)
        file_suppressions = _find_suppressions_in_file(file_path)

        # Add rule_id field for repeat counting
        for sup in file_suppressions:
            # Find rule_id from violations
            rule_id = None
            for v in violations:
                if v.get("file") == file_path and v.get("line") == sup["line"] + 1:
                    rule_id = v.get("rule_id")
                    break
            sup["rule_id"] = rule_id

        all_suppressions.extend(file_suppressions)

    # Build audit log
    audit_log_suppressions: list[SuppressionRecord] = []
    total_escalations = 0

    for suppression in all_suppressions:
        record = _build_suppression_record(suppression, violations, all_suppressions)
        audit_log_suppressions.append(record)

        if record["escalation_reasons"]:
            total_escalations += 1

    # Sort suppressions for determinism
    audit_log_suppressions = _sort_suppressions(audit_log_suppressions)

    # Build audit log JSON
    audit_log: AuditLogEntry = AuditLogEntry(
        version="1.0",
        timestamp=_get_current_timestamp_iso(),
        total_suppressions=len(audit_log_suppressions),
        total_escalations=total_escalations,
        total_files_scanned=len(scanned_files),
        suppressions=audit_log_suppressions,
    )

    # Write audit log artifact
    audit_log_path = "ci/scripts/gates/override_audit_log.json"
    try:
        Path(audit_log_path).parent.mkdir(parents=True, exist_ok=True)
        audit_log_json = json.dumps(audit_log, indent=2)
        Path(audit_log_path).write_text(audit_log_json)
        audit_log_sha256 = hashlib.sha256(audit_log_json.encode()).hexdigest()
    except (OSError, IOError):
        # If we can't write artifact, compute SHA256 in-memory
        audit_log_json = json.dumps(audit_log)
        audit_log_sha256 = hashlib.sha256(audit_log_json.encode()).hexdigest()

    duration_ms = int((time.time() - start_time) * 1000)
    timestamp = _get_current_timestamp_iso()

    # Build violations array for escalations
    violations_out: list[GateViolation] = []
    for record in audit_log_suppressions:
        if record["escalation_reasons"]:
            violations_out.append(GateViolation(
                file=record["file"],
                line=record["line"],
                rule="SUPPRESSION_ESCALATION",
                message=f"Suppression escalated: {', '.join(record['escalation_reasons'])}",
                severity="WARN",
            ))

    # Determine status
    status = "WARN" if total_escalations > 0 else "PASS"

    message = f"Suppression validation complete. {total_escalations} escalation(s) detected."

    # Build gate result
    result: GateResult = GateResult(
        version="1.0",
        status=status,
        gate="override_and_escalation_check",
        upstream_agent=upstream_agent,
        downstream_agent=downstream_agent,
        ticket_id=ticket_id,
        timestamp=timestamp,
        duration_ms=duration_ms,
        message=message,
        artifacts=[
            {
                "path": audit_log_path,
                "sha256": audit_log_sha256,
            }
        ],
        violations=violations_out,
        mode=mode,
    )

    return result
