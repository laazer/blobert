# Spec: Audit Log Schema and Persistence Strategy

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/04_handoff_metadata_and_risk_escalation.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-15

**Status:** SPECIFICATION

---

## Overview

This document specifies the **audit log storage schema, format, location, event types, retention policy, and security constraints**. Audit logs enable forensic tracing of violations, escalations, and detector inputs/outputs for transparency and auditing.

---

## Location and Path Structure

**Base Directory:** `ci/artifacts/audit-logs/` (gitignored)

**Path Pattern:** `ci/artifacts/audit-logs/<gate-name>/<YYYY-MM-DD>/<ISO8601-timestamp>-<mode>.jsonl`

**Example Paths:**
- `ci/artifacts/audit-logs/static_analysis_check/2026-05-15/2026-05-15T10-30-00Z-shadow.jsonl`
- `ci/artifacts/audit-logs/spec_completeness/2026-05-15/2026-05-15T14-15-30Z-blocking.jsonl`
- `ci/artifacts/audit-logs/governance_check/2026-05-16/2026-05-16T09-00-00Z-shadow.jsonl`

**Granularity:**
- One file per gate per calendar day per mode (shadow vs blocking).
- Multiple runs on the same gate, same day, same mode → appended to same file (JSON Lines allows this).
- Different modes → separate files (shadow and blocking runs create distinct logs).

---

## Format: JSON Lines (RFC 7464)

Each line is a complete JSON object (no line breaks within objects).

**Example Log File:**
```
{"timestamp": "2026-05-15T10:30:00Z", "run_id": "abc-123-def", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "gate_started", "event_data": {"mode": "shadow", "upstream_agent": "Spec Agent", "downstream_agent": "Test Designer Agent"}}
{"timestamp": "2026-05-15T10:30:02Z", "run_id": "abc-123-def", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "tool_invoked", "event_data": {"tool_name": "ruff", "timeout_s": 30}}
{"timestamp": "2026-05-15T10:30:15Z", "run_id": "abc-123-def", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "tool_finished", "event_data": {"tool_name": "ruff", "exit_code": 1, "duration_ms": 13000}}
{"timestamp": "2026-05-15T10:30:16Z", "run_id": "abc-123-def", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "violation_added", "event_data": {"rule_id": "E501", "file": "asset_generation/python/src/model_registry/__init__.py", "line": 42, "severity": "WARN", "message": "Line too long (120 > 100 characters)"}}
{"timestamp": "2026-05-15T10:30:17Z", "run_id": "abc-123-def", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "escalation_triggered", "event_data": {"detector": "architecture_drift", "severity": "HIGH", "confidence": "MEDIUM", "details": "Violation count increased 25% from baseline (8 → 10)"}}
```

---

## Event Schema

### Top-Level Fields (All Events)

```python
{
    "timestamp": str,      # ISO 8601 format (e.g., "2026-05-15T10:30:00Z")
    "run_id": str,         # UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
    "gate_name": str,      # Gate identifier (e.g., "static_analysis_check")
    "ticket_id": str|null, # Ticket ID (e.g., "M902-02") or null
    "event_type": str,     # Enum value (see below)
    "event_data": dict     # Type-specific payload (see below)
}
```

### Event Types and Payloads

#### 1. gate_started

**When:** Gate execution begins.

**event_data:**
```python
{
    "mode": str,                    # "shadow" or "blocking"
    "upstream_agent": str,          # Agent name (e.g., "Spec Agent")
    "downstream_agent": str,        # Agent name (e.g., "Test Designer Agent")
    "ticket_id": str|null           # (optional, duplicate of top-level) 
}
```

**Example:**
```json
{
    "timestamp": "2026-05-15T10:30:00Z",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_name": "static_analysis_check",
    "ticket_id": "M902-02",
    "event_type": "gate_started",
    "event_data": {
        "mode": "shadow",
        "upstream_agent": "Spec Agent",
        "downstream_agent": "Test Designer Agent"
    }
}
```

---

#### 2. tool_invoked

**When:** A tool (ruff, mypy, semgrep, jscpd, etc.) is invoked.

**event_data:**
```python
{
    "tool_name": str,       # Tool identifier (e.g., "ruff", "mypy", "semgrep")
    "timeout_s": int|null   # Timeout in seconds, or null if no timeout
}
```

**Example:**
```json
{
    "timestamp": "2026-05-15T10:30:02Z",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_name": "static_analysis_check",
    "ticket_id": "M902-02",
    "event_type": "tool_invoked",
    "event_data": {
        "tool_name": "ruff",
        "timeout_s": 30
    }
}
```

---

#### 3. tool_finished

**When:** A tool completes execution.

**event_data:**
```python
{
    "tool_name": str,       # Tool identifier (e.g., "ruff")
    "exit_code": int,       # Exit code (0 = success, 1 = violations, 2 = error)
    "duration_ms": int      # Elapsed time in milliseconds
}
```

**Example:**
```json
{
    "timestamp": "2026-05-15T10:30:15Z",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_name": "static_analysis_check",
    "ticket_id": "M902-02",
    "event_type": "tool_finished",
    "event_data": {
        "tool_name": "ruff",
        "exit_code": 1,
        "duration_ms": 13000
    }
}
```

---

#### 4. violation_added

**When:** A rule violation is detected and added to the gate result.

**event_data:**
```python
{
    "rule_id": str,         # Rule identifier (e.g., "E501", "AR-01", "GV-06")
    "file": str,            # File path relative to repo root
    "line": int|null,       # Line number (1-indexed) or null if unknown
    "severity": str,        # One of: "CRITICAL", "ERROR", "WARN", "INFO"
    "message": str          # Human-readable violation description
}
```

**Example:**
```json
{
    "timestamp": "2026-05-15T10:30:16Z",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_name": "static_analysis_check",
    "ticket_id": "M902-02",
    "event_type": "violation_added",
    "event_data": {
        "rule_id": "E501",
        "file": "asset_generation/python/src/model_registry/__init__.py",
        "line": 42,
        "severity": "WARN",
        "message": "Line too long (120 > 100 characters)"
    }
}
```

---

#### 5. escalation_triggered

**When:** An escalation detector triggers (detector returns non-empty list).

**event_data:**
```python
{
    "detector": str,        # Detector name (e.g., "governance_file_modifications")
    "severity": str,        # One of: "CRITICAL", "HIGH", "MEDIUM", "LOW"
    "confidence": str,      # One of: "HIGH", "MEDIUM", "LOW"
    "details": str          # Explanation of escalation
}
```

**Example:**
```json
{
    "timestamp": "2026-05-15T10:30:17Z",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_name": "static_analysis_check",
    "ticket_id": "M902-02",
    "event_type": "escalation_triggered",
    "event_data": {
        "detector": "architecture_drift",
        "severity": "HIGH",
        "confidence": "MEDIUM",
        "details": "Violation count increased 25% from baseline (8 → 10)"
    }
}
```

---

#### 6. audit_error

**When:** An error occurs during audit logging (e.g., disk full, permission denied).

**event_data:**
```python
{
    "error_type": str,      # Error category (e.g., "disk_full", "permission_denied")
    "details": str          # Error details
}
```

**Example:**
```json
{
    "timestamp": "2026-05-15T10:35:00Z",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_name": "static_analysis_check",
    "ticket_id": "M902-02",
    "event_type": "audit_error",
    "event_data": {
        "error_type": "disk_full",
        "details": "Failed to write audit log: disk quota exceeded"
    }
}
```

---

## Complete Event Sequences (Examples)

### Sequence 1: Successful Static Analysis Run

```json
{"timestamp": "2026-05-15T10:30:00Z", "run_id": "run-001", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "gate_started", "event_data": {"mode": "shadow", "upstream_agent": "Implementation Agent", "downstream_agent": "Test Designer Agent"}}
{"timestamp": "2026-05-15T10:30:02Z", "run_id": "run-001", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "tool_invoked", "event_data": {"tool_name": "ruff", "timeout_s": 30}}
{"timestamp": "2026-05-15T10:30:12Z", "run_id": "run-001", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "tool_finished", "event_data": {"tool_name": "ruff", "exit_code": 0, "duration_ms": 10000}}
{"timestamp": "2026-05-15T10:30:13Z", "run_id": "run-001", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "tool_invoked", "event_data": {"tool_name": "mypy", "timeout_s": 60}}
{"timestamp": "2026-05-15T10:30:25Z", "run_id": "run-001", "gate_name": "static_analysis_check", "ticket_id": "M902-02", "event_type": "tool_finished", "event_data": {"tool_name": "mypy", "exit_code": 0, "duration_ms": 12000}}
```

**Result:** status = PASS (no violations)

---

### Sequence 2: Run with Violations and Escalation

```json
{"timestamp": "2026-05-15T14:15:00Z", "run_id": "run-002", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "gate_started", "event_data": {"mode": "blocking", "upstream_agent": "Test Designer Agent", "downstream_agent": "Implementation Agent"}}
{"timestamp": "2026-05-15T14:15:02Z", "run_id": "run-002", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "tool_invoked", "event_data": {"tool_name": "ruff", "timeout_s": 30}}
{"timestamp": "2026-05-15T14:15:10Z", "run_id": "run-002", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "tool_finished", "event_data": {"tool_name": "ruff", "exit_code": 1, "duration_ms": 8000}}
{"timestamp": "2026-05-15T14:15:11Z", "run_id": "run-002", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "violation_added", "event_data": {"rule_id": "E501", "file": "asset_generation/web/backend/routers/registry.py", "line": 87, "severity": "WARN", "message": "Line too long (115 > 100 characters)"}}
{"timestamp": "2026-05-15T14:15:12Z", "run_id": "run-002", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "violation_added", "event_data": {"rule_id": "AR-02", "file": "CLAUDE.md", "line": null, "severity": "ERROR", "message": "Architecture rule violation: CLAUDE.md modified with AR-02"}}
{"timestamp": "2026-05-15T14:15:13Z", "run_id": "run-002", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "escalation_triggered", "event_data": {"detector": "governance_file_modifications", "severity": "CRITICAL", "confidence": "HIGH", "details": "Governance file CLAUDE.md modified with architecture rule AR-02: Architecture rule violation detected in policy file"}}
```

**Result:** status = ESCALATE (governance file modified with AR rule)

---

### Sequence 3: Multi-Detector Escalation

```json
{"timestamp": "2026-05-15T16:45:00Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "gate_started", "event_data": {"mode": "shadow", "upstream_agent": "Spec Agent", "downstream_agent": "Test Designer Agent"}}
{"timestamp": "2026-05-15T16:45:05Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "tool_invoked", "event_data": {"tool_name": "sempreg", "timeout_s": 45}}
{"timestamp": "2026-05-15T16:45:20Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "tool_finished", "event_data": {"tool_name": "sempreg", "exit_code": 1, "duration_ms": 15000}}
{"timestamp": "2026-05-15T16:45:21Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "violation_added", "event_data": {"rule_id": "AR-01", "file": "asset_generation/python/src/model_registry/__init__.py", "line": 5, "severity": "ERROR", "message": "Domain module imports HTTP library: fastapi"}}
{"timestamp": "2026-05-15T16:45:22Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "violation_added", "event_data": {"rule_id": "AR-01", "file": "asset_generation/python/src/enemies/__init__.py", "line": 3, "severity": "ERROR", "message": "Domain module imports HTTP library: requests"}}
{"timestamp": "2026-05-15T16:45:23Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "violation_added", "event_data": {"rule_id": "GV-06", "file": "asset_generation/web/backend/routers/registry.py", "line": 142, "severity": "WARN", "message": "Suppression without issue link: # noqa: E501"}}
{"timestamp": "2026-05-15T16:45:24Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "escalation_triggered", "event_data": {"detector": "architecture_drift", "severity": "HIGH", "confidence": "HIGH", "details": "New architecture violations detected: AR-01, AR-01. These rules were not present in baseline."}}
{"timestamp": "2026-05-15T16:45:25Z", "run_id": "run-003", "gate_name": "static_analysis_check", "ticket_id": "M902-04", "event_type": "escalation_triggered", "event_data": {"detector": "suppression_abuse", "severity": "HIGH", "confidence": "HIGH", "details": "File asset_generation/web/backend/routers/registry.py (line 142) has GV-06 violation: Suppression without issue link: # noqa: E501"}}
```

**Result:** status = ESCALATE (two detectors triggered: drift + suppression abuse)

---

## Retention Policy

**Retention Period:** 30 days

**Cleanup Strategy:** Deferred to M903.

**M903 Rotation Options:**
- Daily log file truncation (keep only 30 most recent days).
- Automatic export to external logging service (e.g., CloudWatch, Datadog, Splunk).
- Optional gzip compression of old logs.

---

## Gitignore Policy

**File:** `.gitignore`

**Addition:**
```
ci/artifacts/audit-logs/
```

**Rationale:**
- Audit logs are runtime artifacts, not source code.
- Logs accumulate over time and should not be committed.
- Each developer has local audit logs for debugging; shared logs can be reviewed via CI artifacts.

---

## Security Constraints

### No Secrets in Logs

**Forbidden:**
- API keys, tokens, or passwords
- Private SSL certificates or secrets
- User credentials or session tokens
- File contents or source code excerpts

**Allowed:**
- File paths and line numbers
- Rule IDs and violation types
- Tool names and exit codes
- Agent names and ticket IDs
- Timestamps and run IDs

### Content Filtering (Validation in M903)

M903 will implement automated content filtering to:
- Redact common secret patterns (AWS keys, GitHub tokens, etc.).
- Validate log files for presence of known secrets before shipping.
- Alert on anomalous patterns (e.g., large base64 blobs, key-like strings).

---

## Queryability and Access

### Query Patterns (Grep/JQ Examples)

**Find all violations for a specific file:**
```bash
grep -h '"file": "asset_generation/web/backend/routers/registry.py"' ci/artifacts/audit-logs/**/*.jsonl | jq .
```

**Find all escalations across all runs:**
```bash
grep -h '"event_type": "escalation_triggered"' ci/artifacts/audit-logs/**/*.jsonl | jq .
```

**Find violations by rule_id across all dates:**
```bash
grep -h '"rule_id": "AR-01"' ci/artifacts/audit-logs/**/*.jsonl | jq .
```

**Count violations per tool:**
```bash
grep -h '"event_type": "tool_finished"' ci/artifacts/audit-logs/**/*.jsonl | jq -s 'group_by(.event_data.tool_name) | map({tool: .[0].event_data.tool_name, count: length})'
```

### M903 Query API

M903 will implement a dedicated query API for:
- Querying violations by rule_id, file, date range.
- Aggregating escalation statistics.
- Filtering by gate name, mode, ticket ID.
- Exporting as CSV/JSON for analysis.

---

## Error Handling and Robustness

### Audit Logging Failures

**If audit log writing fails (disk full, permission denied, etc.):**
1. Log error to stderr (not to audit log, to avoid recursion).
2. Continue gate execution (non-blocking; audit log is observability, not a gate blocker).
3. Emit `audit_error` event to indicate logging failure.
4. Gate result file is still produced (decoupled from audit log).

**Example Error Handling:**
```python
try:
    emit_event(event)
except IOError as e:
    # Log to stderr, continue execution
    print(f"ERROR: Failed to write audit log: {e}", file=sys.stderr)
    # Gate execution continues; result file is still produced
```

---

## File Permissions and Safety

**Audit Log File Permissions:** `0644` (readable by all, writable by owner)

**Audit Log Directory Permissions:** `0755` (traversable)

**Rationale:** Audit logs are non-sensitive operational artifacts; full team access is acceptable. Sensitive data is forbidden in logs (see Security Constraints).

---

## Sample Audit Log Files

Three complete audit log files are provided at `project_board/specs/902_04_audit_log_examples/`:

1. `static_analysis_check_2026-05-15_shadow.jsonl` — Successful run (no violations)
2. `static_analysis_check_2026-05-15_blocking.jsonl` — Run with violations and escalation
3. `governance_check_2026-05-15_shadow.jsonl` — Multi-detector escalation scenario

---

**End of Audit Log Specification**
