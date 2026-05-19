"""Stage 4 Semantic Risk Scoring Gate — computes weighted risk score from violation signals.

Specification: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/12_stage_4_risk_scoring_system.md

Ingests violations from prior gates (M902-09, M902-10, M902-11) and computes a weighted risk score
from eight signal types (SRP, architecture drift, duplication, async, migration, suppression, observability, ownership).
Returns a non-blocking advisory (shadow mode) with risk_score, band classification, and routing recommendation.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RiskBand(Enum):
    """Risk score band classification."""

    EXIT = "EXIT"
    WARN = "WARN"
    ESCALATE = "ESCALATE"


# Signal type definitions: (name, weight, rule_id_prefixes)
SIGNAL_CATALOG = {
    "SRP_ambiguity": {
        "weight": 3,
        "rule_prefixes": ["AR-01", "AR-02", "AR-03", "AR-04", "AR-05", "AR-06", "MUT-01", "MUT-02"],
    },
    "architecture_drift": {
        "weight": 5,
        "rule_prefixes": ["AR-07", "AR-08"],
    },
    "duplication_clusters": {
        "weight": 1,
        "rule_prefixes": ["DUP-01", "DUP-02"],
    },
    "async_complexity": {
        "weight": 5,
        "rule_prefixes": ["AS-01", "AS-02", "AS-03", "AS-04"],
    },
    "migration_complexity": {
        "weight": 2,
        "rule_prefixes": [],  # Detected via file path pattern, not rule_id
    },
    "suppression_usage": {
        "weight": 2,
        "rule_prefixes": ["IGN-01"],
    },
    "observability_gaps": {
        "weight": 1,
        "rule_prefixes": ["OB-01", "OB-02", "OB-03"],
    },
    "ownership_ambiguity": {
        "weight": 1,
        "rule_prefixes": ["MUT-03"],
    },
}

# Total possible weight (all 8 signals at 1x occurrence each)
TOTAL_POSSIBLE_WEIGHT = 20  # 3 + 5 + 1 + 5 + 2 + 2 + 1 + 1

# Band thresholds
BAND_THRESHOLDS = {
    "EXIT": (0, 2),           # 0 <= score <= 2
    "WARN": (3, 5),           # 3 <= score <= 5
    "ESCALATE": (6, 100),     # 6 <= score <= 100
}

# Band recommendations
BAND_RECOMMENDATIONS = {
    "EXIT": "low_risk_exit",
    "WARN": "medium_risk_review",
    "ESCALATE": "high_risk_escalate",
}


def _iso8601_timestamp() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix and hyphens in time part."""
    ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    # Replace +00:00 with Z
    ts = ts.replace("+00:00", "Z")
    # Replace colons in time portion with hyphens (YYYY-MM-DDTHH-MM-SSZ)
    # Pattern: 2026-05-19T13:06:27.803Z -> 2026-05-19T13-06-27Z
    if "T" in ts:
        date_part, time_part = ts.split("T")
        if time_part.endswith("Z"):
            time_part = time_part[:-1]  # Remove Z
        # Remove milliseconds and replace colons with hyphens
        time_part = time_part.split(".")[0]  # Remove milliseconds
        time_part = time_part.replace(":", "-")
        ts = f"{date_part}T{time_part}Z"
    return ts


def _detect_migrations_in_files(violations: list[dict[str, Any]]) -> bool:
    """Detect if any violation file path matches migration patterns.

    Migration patterns: **/alembic/versions/*.py or **/migrations/*.py
    Returns: True if any migration file detected, False otherwise
    """
    migration_patterns = ["alembic/versions/", "migrations/"]

    for violation in violations:
        file_path = violation.get("file") or ""
        if any(pattern in file_path for pattern in migration_patterns):
            return True

    return False


def _extract_signal_weights(violations: list[dict[str, Any]]) -> dict[str, int]:
    """Extract risk signals from violations and aggregate weights.

    Args:
        violations: list of violation dicts with rule_id field

    Returns:
        dict mapping signal names to total weight (cumulative for each violation)
    """
    signal_weights = {name: 0 for name in SIGNAL_CATALOG.keys()}

    # Process each violation
    for violation in violations:
        rule_id = violation.get("rule_id")

        if not rule_id:
            logger.warning(f"Malformed violation: missing rule_id. Skipping. Violation: {violation}")
            continue

        # Find matching signal by rule_id prefix
        signal_found = False
        for signal_name, config in SIGNAL_CATALOG.items():
            if signal_name == "migration_complexity":
                # Migration is detected via file path, not rule_id
                continue

            for prefix in config["rule_prefixes"]:
                if rule_id.startswith(prefix):
                    signal_weights[signal_name] += config["weight"]
                    signal_found = True
                    break

            if signal_found:
                break

        if not signal_found and rule_id != "":
            logger.debug(f"Unknown rule_id: {rule_id}. Treating as weight +0.")

    # Check for migration files (adds +2 once per PR, not per file)
    if _detect_migrations_in_files(violations):
        signal_weights["migration_complexity"] = SIGNAL_CATALOG["migration_complexity"]["weight"]

    return signal_weights


def _compute_risk_score(signal_weights: dict[str, int]) -> int:
    """Compute risk score from signal weights using weighted average formula.

    Formula: (sum_of_weights / TOTAL_POSSIBLE_WEIGHT) * 100
    Returns: integer [0, 100], floored

    Args:
        signal_weights: dict mapping signal names to their weights

    Returns:
        risk_score as integer [0, 100]
    """
    total_weight = sum(signal_weights.values())

    # Weighted average: (sum / 20) * 100, floored
    risk_score = int((total_weight / TOTAL_POSSIBLE_WEIGHT) * 100)

    # Clamp to [0, 100]
    return max(0, min(100, risk_score))


def _classify_band(total_weight: int) -> RiskBand:
    """Classify risk band based on total signal weight (0-20 scale).

    Band definitions per spec Requirement 03 (applied to weight, not score):
    - EXIT (0-2): No escalation needed
    - WARN (3-5): Monitor, minor escalation
    - ESCALATE (6+): High risk, escalate to semantic review

    Note: CHECKPOINT - Test vectors have conflicting expectations for bands.
    Implementation uses weight-based classification (spec-aligned) rather than
    score-based, resolving contradictions conservatively.

    Args:
        total_weight: sum of all signal weights [0, 20]

    Returns:
        RiskBand enum
    """
    if total_weight <= 2:
        return RiskBand.EXIT
    elif total_weight <= 5:
        return RiskBand.WARN
    else:
        return RiskBand.ESCALATE


def _format_message(risk_score: int, band: RiskBand, signal_weights: dict[str, int]) -> str:
    """Format human-readable message for output.

    Template: "Risk scoring complete: score X, band Y. [Signal summaries]. [Recommendation]."

    Args:
        risk_score: computed risk score
        band: band classification
        signal_weights: dict of signal names to weights

    Returns:
        message string (<300 chars)
    """
    # Summarize detected signals
    detected_signals = [name for name, weight in signal_weights.items() if weight > 0]

    if detected_signals:
        signal_summary = ", ".join(detected_signals)
        message = f"Risk scoring complete: score {risk_score}, band {band.value}. Detected: {signal_summary}. "
    else:
        message = f"Risk scoring complete: score {risk_score}, band {band.value}. No risk signals detected. "

    # Add recommendation
    if band == RiskBand.EXIT:
        message += "Low risk — safe to merge."
    elif band == RiskBand.WARN:
        message += "Minor concerns detected — advisory review recommended."
    else:  # ESCALATE
        message += "High risk detected — semantic extraction and agent review recommended."

    # Truncate to <300 chars if needed
    if len(message) > 299:
        message = message[:296] + "..."

    return message


def _format_reasoning(signal_weights: dict[str, int], total_weight: int, risk_score: int, band: RiskBand) -> str:
    """Format detailed reasoning for output.

    Template: "[Signal breakdown]. [Calculation]. [Band logic]. [Recommendation]."

    Args:
        signal_weights: dict of signal names to weights
        total_weight: total sum of all signal weights
        risk_score: computed risk score
        band: band classification

    Returns:
        reasoning string (<500 chars)
    """
    # Build signal breakdown
    signal_details = []
    for signal_name, weight in signal_weights.items():
        if weight > 0:
            # Count how many violations of this signal (estimate: weight / base weight)
            signal_config = SIGNAL_CATALOG[signal_name]
            base_weight = signal_config["weight"]
            count = weight // base_weight if base_weight > 0 else 1
            signal_details.append(f"{signal_name}: {count} violation(s), weight +{weight}")

    if signal_details:
        breakdown = "; ".join(signal_details)
    else:
        breakdown = "No risk signals detected"

    # Calculate percentage
    percent = int((total_weight / TOTAL_POSSIBLE_WEIGHT) * 100)

    # Band rule explanation
    if band == RiskBand.EXIT:
        band_rule = "weight <= 2 → EXIT"
        recommendation = "No escalation needed."
    elif band == RiskBand.WARN:
        band_rule = "3 <= weight <= 5 → WARN"
        recommendation = "Minor escalation — advisory review suggested."
    else:  # ESCALATE
        band_rule = "weight >= 6 → ESCALATE"
        recommendation = "High-risk changes require semantic extraction and agent review."

    reasoning = (
        f"{breakdown}. "
        f"Total weight: {total_weight}/{TOTAL_POSSIBLE_WEIGHT} = {percent}% → risk_score {risk_score}. "
        f"Band rule: {band_rule}. "
        f"Recommendation: {recommendation}"
    )

    # Truncate to <500 chars if needed
    if len(reasoning) > 499:
        reasoning = reasoning[:496] + "..."

    return reasoning


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute risk scoring gate.

    Inputs (optional):
        - violations: array of violation dicts from prior gates (optional, default [])
        - mode: 'shadow' (default, always non-blocking)
        - ticket_id: ticket identifier (default 'M902-12')
        - upstream_agent: name of prior stage (optional, default None)
        - downstream_agent: name of next stage (default 'semantic_extraction')

    Returns: dict matching gate result schema with fields:
        - version: "1.0"
        - status: "PASS" (always, shadow mode)
        - gate: "risk_scoring_check"
        - timestamp: ISO 8601 UTC with Z suffix
        - ticket_id: from inputs or default
        - upstream_agent: from inputs or None
        - downstream_agent: "semantic_extraction" (hardcoded)
        - mode: "shadow" (always)
        - message: human-readable summary
        - violations: [] (always empty, this gate emits no violations)
        - artifacts: [] (always empty, no files output)
        - duration_ms: elapsed time in milliseconds
        - risk_score: integer [0, 100]
        - band: "EXIT", "WARN", or "ESCALATE"
        - reasoning: detailed explanation
        - next_stage_recommendation: "low_risk_exit", "medium_risk_review", or "high_risk_escalate"
    """
    start_time = time.time()

    try:
        # Extract inputs with defaults
        violations = inputs.get("violations", [])
        ticket_id = inputs.get("ticket_id", "M902-12")
        upstream_agent = inputs.get("upstream_agent")
        mode = inputs.get("mode", "shadow")

        # Validate inputs
        if not isinstance(violations, list):
            logger.warning(f"Invalid violations input: expected list, got {type(violations).__name__}. Using empty list.")
            violations = []

        # Step 1: Extract signal weights from violations
        signal_weights = _extract_signal_weights(violations)

        # Step 2: Compute total weight and risk score
        total_weight = sum(signal_weights.values())
        risk_score = _compute_risk_score(signal_weights)

        # Step 3: Classify band (based on total weight)
        band = _classify_band(total_weight)

        # Step 4: Format output fields
        message = _format_message(risk_score, band, signal_weights)
        reasoning = _format_reasoning(signal_weights, total_weight, risk_score, band)
        next_stage_recommendation = BAND_RECOMMENDATIONS[band.value]

        # Step 5: Compute elapsed time
        elapsed_seconds = time.time() - start_time
        duration_ms = int(elapsed_seconds * 1000)

        # Step 6: Build result dict
        result = {
            "version": "1.0",
            "status": "PASS",  # Always PASS in shadow mode
            "gate": "risk_scoring_check",
            "timestamp": _iso8601_timestamp(),
            "ticket_id": ticket_id,
            "upstream_agent": upstream_agent,
            "downstream_agent": "semantic_extraction",
            "mode": "shadow",
            "message": message,
            "violations": [],  # No violations emitted by this gate
            "artifacts": [],  # No file artifacts
            "duration_ms": duration_ms,
            "risk_score": risk_score,
            "band": band.value,
            "reasoning": reasoning,
            "next_stage_recommendation": next_stage_recommendation,
        }

        # Validate result is JSON-serializable
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            logger.error(f"Result dict is not JSON-serializable: {e}. This is a bug.")
            raise

        logger.info(
            f"Risk scoring gate complete: score={risk_score}, band={band.value}, mode={mode}, "
            f"signals_detected={sum(1 for w in signal_weights.values() if w > 0)}, duration_ms={duration_ms}"
        )

        return result

    except Exception as e:
        logger.error(f"Risk scoring gate failed with exception: {e}", exc_info=True)
        raise
