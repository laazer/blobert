# Spec: Escalation Detector Framework and Interface

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/04_handoff_metadata_and_risk_escalation.md`

**Milestone:** 902 — Agent Predictability Improvements

**Agent:** Spec Agent

**Date:** 2026-05-15

**Status:** SPECIFICATION

---

## Overview

This document defines the **escalation detector framework** — the interface, calling convention, and high-level specifications for all 5 escalation detectors. MVP scope includes full specifications for detectors 1–3 with placeholder stubs for 4–5.

---

## Detector Interface (Frozen)

All detectors implement the same function signature:

```python
def detect_X(
    gate_result: dict,
    baseline: dict | None,
    audit_log: list[dict]
) -> list[EscalationReason]
```

Where:
- `gate_result`: The aggregated gate output dict containing `violations`, `warnings`, `status`, etc.
- `baseline`: Optional baseline snapshot (dict) for comparison; None on first run.
- `audit_log`: List of audit event dicts from prior runs (queryable by event_type, rule_id, file).
- **Return:** List of `EscalationReason` dicts (empty list if no escalation triggered).

### EscalationReason Type

```python
EscalationReason = {
    "detector": str,  # e.g., "governance_file_modifications"
    "severity": str,  # One of: "CRITICAL", "HIGH", "MEDIUM", "LOW"
    "details": str,   # Human-readable explanation (1-3 sentences)
    "confidence": str,  # One of: "HIGH", "MEDIUM", "LOW"
    "recommendation": str  # Actionable next steps
}
```

---

## Detector Specifications

### Detector 1: Governance File Modifications (Full Specification)

**Function Name:** `detect_governance_file_modifications(gate_result, baseline, audit_log) -> list[EscalationReason]`

**Scope:** Governance file modifications with architecture rule violations.

**Monitored Files:**
- `CLAUDE.md`
- `Taskfile.yml`
- `lefthook.yml`
- `project_board/CHECKPOINTS.md`
- `.gitignore`

**Detection Logic:**
1. Iterate over violations in `gate_result["violations"]`.
2. For each violation, check: `violation["file"]` in monitored_files AND `violation["rule_id"]` in ["AR-01", "AR-02", "AR-03", "AR-04", "AR-05", "AR-06"].
3. If both conditions true, create EscalationReason and append to results.

**EscalationReason Structure:**
```python
{
    "detector": "governance_file_modifications",
    "severity": "CRITICAL",
    "details": f"Governance file {violation['file']} modified with architecture rule {violation['rule_id']}: {violation['message']}",
    "confidence": "HIGH",
    "recommendation": "Design review required before merge. Verify that governance file changes are intentional and do not violate architecture principles."
}
```

**Confidence Level:** HIGH (violations are deterministic; files are well-known).

**Severity:** CRITICAL (governance files are sensitivity-critical).

**Example Scenarios:**
1. CLAUDE.md modified with AR-01 violation → escalate (CRITICAL severity, HIGH confidence).
2. Taskfile.yml modified with no AR violations → no escalation.
3. Taskfile.yml modified with EX-01 violation (non-AR governance) → no escalation.

---

### Detector 2: Architecture Drift (Full Specification)

**Function Name:** `detect_architecture_drift(gate_result, baseline, audit_log) -> list[EscalationReason]`

**Scope:** Violation count increase and new architecture rule violations.

**Baseline Source:** `project_board/902_04_baseline_violations.json` (immutable snapshot).

**Baseline File Format:**
```json
{
  "AR-01": 0,
  "AR-02": 0,
  "E501": 5,
  "mypy-error": 2,
  "...": "..."
}
```

**Detection Algorithm:**
1. If baseline is None or baseline file missing, return empty list (graceful fallback; no baseline, no drift).
2. Count violations by rule_id in current `gate_result["violations"]`.
3. Count violations by rule_id in baseline dict.
4. Calculate `total_current = sum(counts.values())` and `total_baseline = sum(baseline.values())`.
5. If `total_baseline > 0`, calculate `drift_pct = (total_current - total_baseline) / total_baseline * 100`; else `drift_pct = 0`.
6. Check for new AR violations: `new_ar_rules = [rule_id for rule_id in current_counts if rule_id in ["AR-01"..AR-06"] and rule_id not in baseline]`.
7. ESCALATE if `drift_pct > 20` OR `len(new_ar_rules) > 0`.

**EscalationReason Structure:**
```python
if drift_pct > 20:
    reason = {
        "detector": "architecture_drift",
        "severity": "HIGH",
        "details": f"Violation count increased {drift_pct:.1f}% from baseline ({total_baseline} → {total_current}). Violations may indicate architectural degradation.",
        "confidence": "MEDIUM",
        "recommendation": "Review architecture changes. Consider refactoring to reduce violation count. If increase is intentional, update baseline in M903."
    }
elif new_ar_rules:
    reason = {
        "detector": "architecture_drift",
        "severity": "HIGH",
        "details": f"New architecture violations detected: {', '.join(new_ar_rules)}. These rules were not present in baseline.",
        "confidence": "HIGH",
        "recommendation": "Fix new architecture violations before merge. These indicate structural violations of layer boundaries or dependency rules."
    }
```

**Confidence Level:** MEDIUM for percentage-based drift (heuristic, tunable); HIGH for new AR rules (deterministic).

**Severity:** HIGH.

**Thresholds (Tunable in M903):**
- Drift threshold: 20% (conservative; can lower in M903).
- New AR rule detection: any AR-* rule not in baseline triggers escalation.

**Example Scenarios:**
1. Baseline: 5 violations, Current: 6 violations (20% drift, at threshold) → no escalation.
2. Baseline: 5 violations, Current: 7 violations (40% drift) → escalate.
3. Baseline: no AR-01, Current: AR-01 present → escalate (new AR rule).

---

### Detector 3: Suppression Abuse (Full Specification)

**Function Name:** `detect_suppression_abuse(gate_result, baseline, audit_log) -> list[EscalationReason]`

**Scope:** GV-06 violations (suppression integrity issues).

**Detection Logic:**
1. Filter violations with `rule_id == "GV-06"` from `gate_result["violations"]`.
2. For each GV-06 violation, extract file and line number.
3. **Current violation check:** If GV-06 present, create EscalationReason with HIGH confidence.
4. **Recurring abuse check:** Query audit_log for prior runs. Group events by (file, rule_id="GV-06"). Count consecutive recent runs (last 5) containing same (file, GV-06) pair. If found in 5+ consecutive runs, create separate EscalationReason with MEDIUM confidence.

**Current Violation EscalationReason:**
```python
{
    "detector": "suppression_abuse",
    "severity": "HIGH",
    "details": f"File {violation['file']} (line {violation['line'] or 'unknown'}) has GV-06 violation: {violation['message']}. Suppressions must have issue links.",
    "confidence": "HIGH",
    "recommendation": "Add issue link (# issue: <ticket-id>) to the suppression comment, or remove the suppression and fix the underlying rule violation."
}
```

**Recurring Abuse EscalationReason:**
```python
{
    "detector": "suppression_abuse",
    "severity": "HIGH",
    "details": f"File {file} has recurring GV-06 violation across 5+ consecutive recent runs. Suppression abuse is chronic.",
    "confidence": "MEDIUM",
    "recommendation": "Investigate root cause. Either fix the underlying rule violation or create a ticket with explicit justification for the suppression."
}
```

**Confidence Levels:**
- HIGH for current violations (GV-06 is deterministic from M902-03).
- MEDIUM for recurring (based on audit log query; acceptable if <5 runs exist).

**Severity:** HIGH (suppression abuse erodes governance integrity).

**GV-06 Source:** M902-03 governance_check.py output (COMPLETE ticket provides these violations).

**Example Scenarios:**
1. GV-06 violation with issue link in prior line (detected by M902-03) → no escalation.
2. GV-06 violation without link (detected by M902-03) → escalate (current, HIGH confidence).
3. GV-06 in file X detected in last 5 consecutive runs → escalate (recurring, MEDIUM confidence).

---

### Detector 4: Security-Sensitive Paths (Placeholder Stub)

**Function Name:** `detect_security_sensitive_paths(gate_result, baseline, audit_log) -> list[EscalationReason]`

**Status:** PLACEHOLDER (M903)

**Implementation (MVP):**
```python
def detect_security_sensitive_paths(gate_result, baseline, audit_log):
    # Placeholder: No security rule set available in MVP.
    # Security detector will be implemented in M903 when rules are finalized.
    return []  # No false escalations.
```

**M903 Implementation Notes:**
- Sensitive paths to monitor: `/scripts/`, `/ci/`, `/deployment/`, others TBD.
- Rules to detect: secrets (API keys, tokens), unsafe operations in sensitive locations.
- Requires: semprep custom rules (security-specific), bandit extensions.
- Deferred: M903 ticket TBD.

---

### Detector 5: Repeated Failures (Placeholder Stub)

**Function Name:** `detect_repeated_failures(gate_result, baseline, audit_log) -> list[EscalationReason]`

**Status:** PLACEHOLDER (audit log infrastructure dependency; full impl in Task 7 of Implementation phase)

**Specification (Task 7):**

See `902_04_repeated_failures_detector_spec.md` (created in Requirement 07 of main spec).

**Implementation (MVP):**
```python
def detect_repeated_failures(gate_result, baseline, audit_log):
    # Placeholder: Audit log infrastructure not yet built (Task 10 in Implementation).
    # Will query audit logs for (rule_id, file) pairs across recent runs.
    # MVP: return empty list (no escalation).
    if not audit_log:
        return []  # No audit log data available.
    # TODO: Implement recurring violation detection in Task 7.
    return []
```

---

## Detector Execution Order

Detectors are called **sequentially** post-aggregation in gate_runner (Task 11):

1. `detect_governance_file_modifications(gate_result, baseline, audit_log)`
2. `detect_architecture_drift(gate_result, baseline, audit_log)`
3. `detect_suppression_abuse(gate_result, baseline, audit_log)`
4. `detect_security_sensitive_paths(gate_result, baseline, audit_log)` (stub in MVP)
5. `detect_repeated_failures(gate_result, baseline, audit_log)` (stub in MVP)

All results are collected into `gate_result["escalation_reasons"]` list. If any detector returns non-empty list, `gate_result["status"]` is set to `"ESCALATE"`.

---

## Summary: MVP Scope

| Detector | Status | Confidence | Severity | Implemented |
|----------|--------|-----------|----------|-------------|
| Governance File Modifications | Full Spec | HIGH | CRITICAL | Task 4 |
| Architecture Drift | Full Spec | MEDIUM | HIGH | Task 5 |
| Suppression Abuse | Full Spec | HIGH/MEDIUM | HIGH | Task 6 |
| Security Paths | Placeholder | — | — | M903 |
| Repeated Failures | Placeholder | — | — | Task 7 (Impl), M903 (full) |

---

**End of Detector Framework Specification**
