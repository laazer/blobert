"""
Gate wrapper for semantic agent review (M902-14).

Reads semantic bundle from .semantic_reviews/<issue_id>.json, evaluates using agent,
and returns M902-01 gate success schema with agent-specific fields.

Spec: project_board/specs/902_14_agent_review_layer_spec.md
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ci.scripts.agents.semantic_reviewer import evaluate_bundle

logger = logging.getLogger(__name__)


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Gate runner function for M902-01 framework.

    Args:
        inputs: dict with optional keys:
            - bundle_path: explicit path to bundle JSON
            - issue_id: issue/PR ID for default bundle path
            - upstream_agent: prior agent name (e.g., "semantic_extraction_check")
            - downstream_agent: next agent name (e.g., "orchestrator")
            - mode: "shadow" or "blocking"
            - ticket_id: ticket identifier

    Returns:
        dict conforming to M902-01 gate success schema + agent fields
    """
    start_time = time.time()

    # Determine bundle path
    bundle_path = inputs.get("bundle_path")
    if not bundle_path:
        issue_id = inputs.get("issue_id", "unknown")
        bundle_path = f".semantic_reviews/{issue_id}.json"

    # Load bundle
    try:
        bundle_file = Path(bundle_path)
        if not bundle_file.exists():
            logger.error("Bundle file not found: %s", bundle_path)
            return _error_response(
                "Bundle not found",
                bundle_path,
                inputs,
                time.time() - start_time,
            )

        with open(bundle_file, "r") as f:
            bundle = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in bundle: %s", bundle_path)
        return _error_response(
            f"Invalid JSON: {str(e)}",
            bundle_path,
            inputs,
            time.time() - start_time,
        )
    except Exception as e:
        logger.error("Error loading bundle: %s", str(e))
        return _error_response(
            f"Error loading bundle: {str(e)}",
            bundle_path,
            inputs,
            time.time() - start_time,
        )

    # Evaluate bundle
    try:
        agent_result = evaluate_bundle(bundle)
    except Exception as e:
        logger.error("Agent evaluation error: %s", str(e))
        return _error_response(
            f"Agent evaluation failed: {str(e)}",
            bundle_path,
            inputs,
            time.time() - start_time,
        )

    # Transform to M902-01 gate schema
    duration_ms = int((time.time() - start_time) * 1000)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Build message
    message = f"Agent semantic review complete. Decision: {agent_result['decision']}. Confidence: {agent_result['confidence']}."
    if len(message) > 500:
        message = message[:497] + "..."

    # Build artifacts array
    artifacts = []
    if bundle_path:
        artifacts.append({
            "path": bundle_path,
            "sha256": "unknown",  # Would compute in production
        })

    # Build gate output
    gate_output = {
        "version": "1.0",
        "status": "PASS",  # Always PASS in shadow mode
        "gate": "agent_review_check",
        "timestamp": timestamp,
        "ticket_id": inputs.get("ticket_id", "unknown"),
        "upstream_agent": inputs.get("upstream_agent", "semantic_extraction_check"),
        "downstream_agent": inputs.get("downstream_agent", "orchestrator"),
        "message": message,
        "violations": agent_result.get("violations", []),
        "artifacts": artifacts,
        "duration_ms": duration_ms,
        "mode": inputs.get("mode", "shadow"),
        # Agent-specific fields
        "decision": agent_result["decision"],
        "confidence": agent_result["confidence"],
        "agent_decision_reasoning": agent_result["reasoning"],
    }

    logger.debug("Gate evaluation complete: %s", gate_output)

    return gate_output


def _error_response(
    message: str,
    bundle_path: str,
    inputs: dict[str, Any],
    duration_ms: float,
) -> dict[str, Any]:
    """Generate error response in M902-01 format."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "version": "1.0",
        "status": "PASS",  # Shadow mode: always PASS
        "gate": "agent_review_check",
        "timestamp": timestamp,
        "ticket_id": inputs.get("ticket_id", "unknown"),
        "upstream_agent": inputs.get("upstream_agent", "semantic_extraction_check"),
        "downstream_agent": inputs.get("downstream_agent", "orchestrator"),
        "message": f"Agent error: {message}",
        "violations": [],
        "artifacts": [{"path": bundle_path, "sha256": "unknown"}],
        "duration_ms": int(duration_ms * 1000),
        "mode": inputs.get("mode", "shadow"),
        "decision": "error",
        "confidence": 0.0,
        "agent_decision_reasoning": message,
    }
