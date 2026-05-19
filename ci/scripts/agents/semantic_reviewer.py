"""
Stage 6 agent for semantic review of code bundles.

Ticket: M902-14
Spec: project_board/specs/902_14_agent_review_layer_spec.md

Evaluates bundles on 8 signals:
- S1: SRP correctness
- S2: Abstraction justification
- S3: Hierarchy correctness
- S4: Ownership clarity
- S5: Observability completeness
- S6: Async safety (CRITICAL)
- S7: Exception handling
- S8: Suppression justification

Returns JSON with decision (approve/warn/reject), confidence [0.0-1.0], reasoning, violations, and evaluated_signals.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

# Rule ID prefixes mapping to signals
RULE_ID_MAPPING = {
    "AR": "srp_correctness",  # AR-01 to AR-06
    "AS": "async_safety",  # AS-01 to AS-04
    "OB": "observability_completeness",  # OB-01 to OB-03
    "EXH": "exception_handling",  # EXH-01 to EXH-04
}

# Signal definitions (S1-S8)
SIGNAL_DEFINITIONS = [
    {"id": "S1", "name": "srp_correctness", "type": "moderate"},
    {"id": "S2", "name": "abstraction_justification", "type": "moderate"},
    {"id": "S3", "name": "hierarchy_correctness", "type": "critical"},
    {"id": "S4", "name": "ownership_clarity", "type": "low"},
    {"id": "S5", "name": "observability_completeness", "type": "low"},
    {"id": "S6", "name": "async_safety", "type": "critical"},
    {"id": "S7", "name": "exception_handling", "type": "moderate"},
    {"id": "S8", "name": "suppression_justification", "type": "moderate"},
]

# Severity order for sorting
SEVERITY_ORDER = {"CRITICAL": 0, "ERROR": 1, "WARN": 2, "INFO": 3}


# ============================================================================
# Signal Evaluation Functions
# ============================================================================


def evaluate_signal_1_srp(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S1: SRP correctness via violations_summary (AR-01–AR-06).

    Returns: (violation_present, confidence, reasoning)
    """
    violations_summary = bundle.get("violations_summary", {})
    violations = violations_summary.get("violations", [])

    for violation in violations:
        try:
            rule_id = violation.get("rule_id", "")
            if rule_id.startswith("AR-"):
                return (True, 0.9, "SRP violations detected in code structure")
        except (TypeError, AttributeError):
            logger.warning("Malformed violation in SRP check: %s", violation)
            continue

    return (False, 0.9, "No SRP violations detected")


def evaluate_signal_2_abstraction(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S2: Abstraction justification via code_hunks and import_graph.

    Returns: (violation_present, confidence, reasoning)
    """
    code_hunks = bundle.get("code_hunks", [])

    # Check for abstract class patterns without concrete implementations
    for hunk in code_hunks:
        try:
            content = hunk.get("content", "")
            # Pattern: ABC or abstractmethod without concrete subclasses
            if re.search(r"(from abc import|abstractmethod)", content):
                # Simple heuristic: if abstract found, check if it has practical use
                # For now, flag as potential violation (conservative)
                return (True, 0.7, "Abstract base class or interface found; justification unclear")
        except (TypeError, AttributeError):
            logger.warning("Malformed code hunk in abstraction check")
            continue

    return (False, 0.9, "Abstraction properly justified")


def evaluate_signal_3_hierarchy(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S3: Hierarchy correctness via import_graph cycles.

    Returns: (violation_present, confidence, reasoning)
    """
    import_graph = bundle.get("import_graph", {})
    cycles_detected = import_graph.get("cycles_detected", False)

    if cycles_detected:
        return (True, 0.95, "Circular imports detected in dependency graph")

    return (False, 0.95, "No circular imports; hierarchy correct")


def evaluate_signal_4_ownership(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S4: Ownership clarity via ownership.assignments.

    Returns: (violation_present, confidence, reasoning)
    """
    ownership = bundle.get("ownership", {})
    assignments = ownership.get("assignments", {})
    source = ownership.get("source", "UNKNOWN")

    # Check if all files have owners
    if not assignments:
        # Empty assignments → degrade gracefully
        logger.warning("No ownership assignments found")
        return (True, 0.6, "Ownership assignments missing or empty")

    # Check for missing owners in changed files (heuristic based on code_hunks)
    code_hunks = bundle.get("code_hunks", [])
    for hunk in code_hunks:
        try:
            file = hunk.get("file", "")
            if file and file not in assignments:
                return (True, 0.7, f"File {file} missing owner assignment")
        except (TypeError, AttributeError):
            continue

    # Lower confidence if source is heuristic
    confidence = 0.85 if source == "CODEOWNERS" else 0.7
    return (False, confidence, "Ownership clearly assigned")


def evaluate_signal_5_observability(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S5: Observability completeness via violations_summary (OB-01–OB-03).

    Returns: (violation_present, confidence, reasoning)
    """
    violations_summary = bundle.get("violations_summary", {})
    violations = violations_summary.get("violations", [])

    for violation in violations:
        try:
            rule_id = violation.get("rule_id", "")
            if rule_id.startswith("OB-"):
                return (True, 0.8, "Observability gaps detected (logging/audit events)")
        except (TypeError, AttributeError):
            logger.warning("Malformed violation in observability check")
            continue

    return (False, 0.9, "Observability requirements met")


def evaluate_signal_6_async(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S6: Async safety via violations_summary (AS-01–AS-04). CRITICAL signal.

    Returns: (violation_present, confidence, reasoning)
    """
    violations_summary = bundle.get("violations_summary", {})
    violations = violations_summary.get("violations", [])

    for violation in violations:
        try:
            rule_id = violation.get("rule_id", "")
            if rule_id.startswith("AS-"):
                return (True, 0.95, "Async safety violations detected (blocking I/O or unsafe task handling)")
        except (TypeError, AttributeError):
            logger.warning("Malformed violation in async check")
            continue

    return (False, 0.95, "Async safety verified")


def evaluate_signal_7_exception(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S7: Exception handling via violations_summary (EXH-01–EXH-04).

    Returns: (violation_present, confidence, reasoning)
    """
    violations_summary = bundle.get("violations_summary", {})
    violations = violations_summary.get("violations", [])

    for violation in violations:
        try:
            rule_id = violation.get("rule_id", "")
            if rule_id.startswith("EXH-"):
                return (True, 0.85, "Exception handling violations detected (bare except or silent failures)")
        except (TypeError, AttributeError):
            logger.warning("Malformed violation in exception check")
            continue

    return (False, 0.9, "Exception handling proper")


def evaluate_signal_8_suppression(bundle: dict[str, Any]) -> tuple[bool, float, str]:
    """S8: Suppression justification via code_hunks blobert-ignore patterns.

    Returns: (violation_present, confidence, reasoning)
    """
    code_hunks = bundle.get("code_hunks", [])

    for hunk in code_hunks:
        try:
            content = hunk.get("content", "")
            # Find blobert-ignore patterns
            if "blobert-ignore" in content:
                # Check if followed by justification (reason + ticket reference)
                # Pattern: blobert-ignore followed by comment with reason and issue reference
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "blobert-ignore" in line:
                        # Check next lines for reason and ticket
                        has_reason = False
                        has_ticket = False
                        for j in range(i + 1, min(i + 4, len(lines))):
                            next_line = lines[j].lower()
                            if "reason:" in next_line or "ticket:" in next_line:
                                has_reason = True
                            if "ticket:" in next_line or re.search(r"#|M\d+|issue", next_line):
                                has_ticket = True

                        if not (has_reason and has_ticket):
                            return (True, 0.8, "Suppression comment lacks justification (reason + ticket reference)")
        except (TypeError, AttributeError):
            logger.warning("Malformed code hunk in suppression check")
            continue

    return (False, 0.9, "Suppressions properly justified")


# ============================================================================
# Decision Logic
# ============================================================================


def evaluate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate a semantic bundle and return approval/warn/reject decision.

    Args:
        bundle: M902-13 semantic extraction bundle (v1.0 schema)

    Returns:
        dict with keys:
            - decision: "approve" | "warn" | "reject"
            - confidence: float [0.0, 1.0], rounded to 2 decimals
            - reasoning: str (1-3 sentences, max 500 chars)
            - violations: array of violation objects
            - evaluated_signals: array of signal evaluation metadata
    """
    logger.debug("Evaluating bundle: %s", bundle.get("issue_id", "unknown"))

    # Validate bundle schema (log WARNING if invalid, continue)
    if not isinstance(bundle, dict):
        logger.warning("Bundle is not a dict; treating as empty")
        bundle = {}

    required_fields = ["code_hunks", "import_graph", "ownership", "violations_summary"]
    for field in required_fields:
        if field not in bundle:
            logger.warning("Bundle missing field: %s", field)

    # Evaluate all 8 signals
    signal_results = []

    # S1: SRP
    s1_violation, s1_confidence, s1_reasoning = evaluate_signal_1_srp(bundle)
    signal_results.append({
        "signal_id": "S1",
        "signal_name": "srp_correctness",
        "violation_present": s1_violation,
        "confidence": round(s1_confidence, 2),
        "reasoning": s1_reasoning,
    })

    # S2: Abstraction
    s2_violation, s2_confidence, s2_reasoning = evaluate_signal_2_abstraction(bundle)
    signal_results.append({
        "signal_id": "S2",
        "signal_name": "abstraction_justification",
        "violation_present": s2_violation,
        "confidence": round(s2_confidence, 2),
        "reasoning": s2_reasoning,
    })

    # S3: Hierarchy
    s3_violation, s3_confidence, s3_reasoning = evaluate_signal_3_hierarchy(bundle)
    signal_results.append({
        "signal_id": "S3",
        "signal_name": "hierarchy_correctness",
        "violation_present": s3_violation,
        "confidence": round(s3_confidence, 2),
        "reasoning": s3_reasoning,
    })

    # S4: Ownership
    s4_violation, s4_confidence, s4_reasoning = evaluate_signal_4_ownership(bundle)
    signal_results.append({
        "signal_id": "S4",
        "signal_name": "ownership_clarity",
        "violation_present": s4_violation,
        "confidence": round(s4_confidence, 2),
        "reasoning": s4_reasoning,
    })

    # S5: Observability
    s5_violation, s5_confidence, s5_reasoning = evaluate_signal_5_observability(bundle)
    signal_results.append({
        "signal_id": "S5",
        "signal_name": "observability_completeness",
        "violation_present": s5_violation,
        "confidence": round(s5_confidence, 2),
        "reasoning": s5_reasoning,
    })

    # S6: Async (CRITICAL)
    s6_violation, s6_confidence, s6_reasoning = evaluate_signal_6_async(bundle)
    signal_results.append({
        "signal_id": "S6",
        "signal_name": "async_safety",
        "violation_present": s6_violation,
        "confidence": round(s6_confidence, 2),
        "reasoning": s6_reasoning,
    })

    # S7: Exception
    s7_violation, s7_confidence, s7_reasoning = evaluate_signal_7_exception(bundle)
    signal_results.append({
        "signal_id": "S7",
        "signal_name": "exception_handling",
        "violation_present": s7_violation,
        "confidence": round(s7_confidence, 2),
        "reasoning": s7_reasoning,
    })

    # S8: Suppression
    s8_violation, s8_confidence, s8_reasoning = evaluate_signal_8_suppression(bundle)
    signal_results.append({
        "signal_id": "S8",
        "signal_name": "suppression_justification",
        "violation_present": s8_violation,
        "confidence": round(s8_confidence, 2),
        "reasoning": s8_reasoning,
    })

    # Determine decision using priority cascade
    # CRITICAL signals: S6 (async), S3 (hierarchy if cycles)
    if s6_violation:
        decision = "reject"
        confidence_base = 0.95
        confidence_penalty = 0.25
    elif s3_violation:  # Circular imports are critical
        decision = "reject"
        confidence_base = 0.95
        confidence_penalty = 0.25
    else:
        # Count moderate violations
        moderate_violations = sum([s1_violation, s2_violation, s7_violation, s8_violation])

        if moderate_violations >= 2:
            decision = "warn"
            confidence_base = 0.75
            confidence_penalty = 0.10 * moderate_violations
        elif s4_violation or s5_violation:  # LOW signals
            decision = "warn"
            confidence_base = 0.75
            confidence_penalty = 0.05 * (s4_violation + s5_violation)
        else:
            decision = "approve"
            confidence_base = 0.75
            confidence_penalty = 0

    # Add ownership bonus if clear
    ownership_bonus = 0.05 if not s4_violation else 0

    # Calculate final confidence
    confidence = confidence_base - confidence_penalty + ownership_bonus
    confidence = max(0.0, min(1.0, confidence))  # Clamp to [0.0, 1.0]
    confidence = round(confidence, 2)

    # Compose reasoning
    if decision == "approve":
        reasoning = "Bundle passes semantic review. No critical signals detected; ownership is clear."
    elif decision == "warn":
        issues = []
        if s1_violation:
            issues.append("SRP violations")
        if s2_violation:
            issues.append("abstraction concerns")
        if s7_violation:
            issues.append("exception handling gaps")
        if s8_violation:
            issues.append("unjustified suppressions")
        if s4_violation:
            issues.append("ownership ambiguity")
        if s5_violation:
            issues.append("observability gaps")
        reasoning = f"Bundle has concerns: {', '.join(issues)}. Review recommended."
    else:  # reject
        if s6_violation:
            reasoning = "Bundle requires redesign. Async safety violations detected; blocking I/O must be refactored."
        elif s3_violation:
            reasoning = "Bundle requires redesign. Circular imports detected; dependency structure must be reorganized."
        else:
            reasoning = "Bundle requires fixes before proceeding."

    # Clamp reasoning to 500 chars
    if len(reasoning) > 500:
        reasoning = reasoning[:497] + "..."

    # Extract violations that match evaluated signals
    violations_array = []
    violations_summary = bundle.get("violations_summary", {})
    violations_list = violations_summary.get("violations", [])

    for violation in violations_list:
        try:
            rule_id = violation.get("rule_id", "")
            severity = violation.get("severity", "INFO")

            # Map rule_id to signal
            signal_name = None
            for prefix, name in RULE_ID_MAPPING.items():
                if rule_id.startswith(prefix):
                    signal_name = name
                    break

            # Include if violation affects decision
            if signal_name:
                violations_array.append({
                    "rule_id": rule_id,
                    "severity": severity,
                    "message": violation.get("message", ""),
                    "file": violation.get("file", ""),
                    "line": violation.get("line"),
                    "signal": signal_name,
                })
        except (TypeError, AttributeError):
            logger.warning("Malformed violation; skipping: %s", violation)
            continue

    # Sort violations by severity
    violations_array.sort(key=lambda v: SEVERITY_ORDER.get(v.get("severity", "INFO"), 99))

    # Build output
    output = {
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "violations": violations_array,
        "evaluated_signals": signal_results,
    }

    # Ensure deterministic JSON output (sorted keys)
    # This is validated by json.dumps(output, sort_keys=True) == json.dumps(output2, sort_keys=True)

    logger.debug("Bundle evaluation complete: decision=%s, confidence=%s", decision, confidence)

    return output
