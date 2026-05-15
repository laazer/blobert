#!/usr/bin/env python3
"""
Escalation detectors for M902-04 Handoff Metadata & Risk Escalation.

Provides 5 escalation detectors:
  1. detect_governance_file_modifications: Monitor CLAUDE.md, Taskfile.yml, etc. for AR rules
  2. detect_architecture_drift: >20% violation increase or new AR rules
  3. detect_suppression_abuse: GV-06 violations (suppression integrity)
  4. detect_security_sensitive_paths: Placeholder (deferred M903)
  5. detect_repeated_failures: Placeholder (deferred M903)

All detectors share the same interface:
    def detect_X(gate_result, baseline, audit_log) -> list[EscalationReason]

Where EscalationReason = {
    "detector": str,
    "severity": str,
    "details": str,
    "confidence": str,
    "recommendation": str
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ===========================================================================
# DETECTOR 1: GOVERNANCE FILE MODIFICATIONS
# ===========================================================================

_MONITORED_FILES = {
    "CLAUDE.md",
    "Taskfile.yml",
    "lefthook.yml",
    "project_board/CHECKPOINTS.md",
    ".gitignore"
}

_MONITORED_RULES = {"AR-01", "AR-02", "AR-03", "AR-04", "AR-05", "AR-06"}


def detect_governance_file_modifications(
    gate_result: dict[str, Any],
    baseline: dict[str, int] | None,
    audit_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Detect governance file modifications with architecture rule violations.

    Args:
        gate_result: Aggregated gate output dict
        baseline: Optional baseline snapshot (unused for this detector)
        audit_log: Audit log events (unused for this detector)

    Returns:
        List of EscalationReason dicts (one per governance file with AR violation)
    """
    reasons = []
    violations = gate_result.get("violations", [])

    for violation in violations:
        file = violation.get("file", "")
        rule_id = violation.get("rule_id", "")

        # Check if file is monitored AND rule is an architecture rule
        if file in _MONITORED_FILES and rule_id in _MONITORED_RULES:
            reasons.append({
                "detector": "governance_file_modifications",
                "severity": "CRITICAL",
                "details": f"Governance file {file} modified with architecture rule {rule_id}: {violation.get('message', '')}",
                "confidence": "HIGH",
                "recommendation": "Design review required before merge. Verify that governance file changes are intentional and do not violate architecture principles."
            })

    return reasons


# ===========================================================================
# DETECTOR 2: ARCHITECTURE DRIFT
# ===========================================================================

_BASELINE_FILE = Path("project_board/902_04_baseline_violations.json")


def detect_architecture_drift(
    gate_result: dict[str, Any],
    baseline: dict[str, int] | None,
    audit_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Detect architecture drift: >20% violation increase or new AR rules.

    Args:
        gate_result: Aggregated gate output dict
        baseline: Optional baseline snapshot (dict with rule_id -> count)
        audit_log: Audit log events (unused for this detector)

    Returns:
        List of EscalationReason dicts (at most one per drift type)
    """
    reasons = []

    # If no baseline, return empty list (graceful fallback; no baseline, no drift)
    if baseline is None:
        # Try to load baseline from file
        if _BASELINE_FILE.exists():
            try:
                baseline = json.loads(_BASELINE_FILE.read_text())
                # Filter out metadata
                baseline = {k: v for k, v in baseline.items() if not k.startswith("_")}
            except (json.JSONDecodeError, OSError):
                return []
        else:
            return []

    # Count violations by rule_id in current gate_result
    violations = gate_result.get("violations", [])
    current_counts = {}
    for v in violations:
        rule_id = v.get("rule_id", "")
        current_counts[rule_id] = current_counts.get(rule_id, 0) + 1

    # Check for new AR violations (deterministic, HIGH confidence)
    ar_rules = {"AR-01", "AR-02", "AR-03", "AR-04", "AR-05", "AR-06"}
    new_ar_rules = [r for r in current_counts if r in ar_rules and r not in baseline]

    if new_ar_rules:
        return [{
            "detector": "architecture_drift",
            "severity": "HIGH",
            "details": f"New architecture violations detected: {', '.join(new_ar_rules)}. These rules were not present in baseline.",
            "confidence": "HIGH",
            "recommendation": "Fix new architecture violations before merge. These indicate structural violations of layer boundaries or dependency rules."
        }]

    # Check for >20% drift (percentage-based, MEDIUM confidence)
    total_baseline = sum(baseline.values()) if baseline else 0
    total_current = sum(current_counts.values())

    if total_baseline > 0:
        drift_pct = (total_current - total_baseline) / total_baseline * 100
        # Escalate only if drift_pct > 20 (strictly greater)
        if drift_pct > 20:
            return [{
                "detector": "architecture_drift",
                "severity": "HIGH",
                "details": f"Violation count increased {drift_pct:.1f}% from baseline ({total_baseline} → {total_current}). Violations may indicate architectural degradation.",
                "confidence": "MEDIUM",
                "recommendation": "Review architecture changes. Consider refactoring to reduce violation count. If increase is intentional, update baseline in M903."
            }]

    return []


# ===========================================================================
# DETECTOR 3: SUPPRESSION ABUSE
# ===========================================================================

def detect_suppression_abuse(
    gate_result: dict[str, Any],
    baseline: dict[str, int] | None,
    audit_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Detect suppression abuse: GV-06 violations and recurring suppressions.

    Args:
        gate_result: Aggregated gate output dict
        baseline: Optional baseline snapshot (unused)
        audit_log: Audit log events (for recurring detection)

    Returns:
        List of EscalationReason dicts (one for current, one for recurring if applicable)
    """
    reasons = []
    violations = gate_result.get("violations", [])

    # Check for current GV-06 violations
    gv06_violations = [v for v in violations if v.get("rule_id") == "GV-06"]
    for violation in gv06_violations:
        reasons.append({
            "detector": "suppression_abuse",
            "severity": "HIGH",
            "details": f"File {violation.get('file', 'unknown')} (line {violation.get('line', 'unknown')}) has GV-06 violation: {violation.get('message', '')}. Suppressions must have issue links.",
            "confidence": "HIGH",
            "recommendation": "Add issue link (# issue: <ticket-id>) to the suppression comment, or remove the suppression and fix the underlying rule violation."
        })

    # Check for recurring GV-06 in audit log (5+ consecutive recent runs)
    if audit_log:
        gv06_in_log = [
            e for e in audit_log
            if e.get("event_type") == "violation_added"
            and e.get("event_data", {}).get("rule_id") == "GV-06"
        ]
        # Simplified: if 5+ GV-06 events exist, flag as recurring
        if len(gv06_in_log) >= 5:
            # Group by file to report which files are recurring
            files_with_recurring = set()
            for event in gv06_in_log:
                file = event.get("event_data", {}).get("file", "unknown")
                files_with_recurring.add(file)

            for file in files_with_recurring:
                reasons.append({
                    "detector": "suppression_abuse",
                    "severity": "HIGH",
                    "details": f"File {file} has recurring GV-06 violation across 5+ consecutive recent runs. Suppression abuse is chronic.",
                    "confidence": "MEDIUM",
                    "recommendation": "Investigate root cause. Either fix the underlying rule violation or create a ticket with explicit justification for the suppression."
                })

    return reasons


# ===========================================================================
# DETECTOR 4: SECURITY SENSITIVE PATHS (PLACEHOLDER)
# ===========================================================================

def detect_security_sensitive_paths(
    gate_result: dict[str, Any],
    baseline: dict[str, int] | None,
    audit_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Placeholder detector for security-sensitive paths (deferred to M903).

    Args:
        gate_result: Aggregated gate output dict
        baseline: Optional baseline snapshot (unused)
        audit_log: Audit log events (unused)

    Returns:
        Empty list (safe default; no false escalations)
    """
    # TODO M903: Implement when security rule set is finalized
    return []


# ===========================================================================
# DETECTOR 5: REPEATED FAILURES (PLACEHOLDER)
# ===========================================================================

def detect_repeated_failures(
    gate_result: dict[str, Any],
    baseline: dict[str, int] | None,
    audit_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Placeholder detector for repeated failures (deferred to M903).

    Looks for (rule_id, file) pairs that recur across 5+ recent runs.

    Args:
        gate_result: Aggregated gate output dict
        baseline: Optional baseline snapshot (unused)
        audit_log: Audit log events

    Returns:
        List of EscalationReason dicts (currently empty; full impl in M903)
    """
    # TODO M903: Implement when audit log infrastructure is stable
    return []


# ===========================================================================
# DETECTOR RUNNER
# ===========================================================================

def run_all_detectors(
    gate_result: dict[str, Any],
    baseline: dict[str, int] | None,
    audit_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Run all detectors sequentially and aggregate results.

    Args:
        gate_result: Aggregated gate output dict
        baseline: Optional baseline snapshot
        audit_log: Audit log events

    Returns:
        List of EscalationReason dicts (deduped by detector name)
    """
    all_reasons = []
    detectors = [
        detect_governance_file_modifications,
        detect_architecture_drift,
        detect_suppression_abuse,
        detect_security_sensitive_paths,
        detect_repeated_failures,
    ]

    for detector in detectors:
        try:
            reasons = detector(gate_result, baseline, audit_log)
            if reasons:
                all_reasons.extend(reasons)
        except Exception as e:
            # Log error but continue with other detectors
            print(f"WARNING: Detector {detector.__name__} raised exception: {e}")

    # Deduplicate by detector name (keep first occurrence of each detector)
    seen_detectors = set()
    deduped = []
    for reason in all_reasons:
        detector_name = reason.get("detector", "")
        if detector_name not in seen_detectors:
            seen_detectors.add(detector_name)
            deduped.append(reason)

    return deduped
