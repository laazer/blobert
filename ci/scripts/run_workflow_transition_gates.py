#!/usr/bin/env python3
"""
Mandatory workflow transition gates (M902-20 + M902-23).

Runs todo_validation_check then handoff_validation_check in **blocking** order.
Orchestrators (autopilot, feature) must call this after each finishing agent and
before advancing the ticket stage. No skip/opt-out flags on this entry point.

Break-glass (tests only): set BLOBERT_ALLOW_GATE_OPT_OUT=1 on individual gate
inputs when calling gate_runner directly — never in autopilot/feature flows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gates.handoff_validation_check import run as handoff_run
from gates.todo_validation_check import run as todo_run

DEFAULT_CHECKPOINTS_DIR = "project_board/checkpoints"

# Normative transition table (Requirement 17, 902_23_atomic_handoff_spec.md)
TRANSITIONS: dict[str, dict[str, str]] = {
    "planner_to_spec": {
        "expected_agent": "Planner Agent",
        "from_agent": "planner",
        "to_agent": "spec",
    },
    "spec_to_test_design": {
        "expected_agent": "Spec Agent",
        "from_agent": "spec",
        "to_agent": "test_designer",
    },
    "test_design_to_test_break": {
        "expected_agent": "Test Designer Agent",
        "from_agent": "test_designer",
        "to_agent": "test_breaker",
    },
    "test_break_to_implementation": {
        "expected_agent": "Test Breaker Agent",
        "from_agent": "test_breaker",
        "to_agent": "implementation",
    },
    "implementation_to_static_qa": {
        "expected_agent": "Implementation Agent",
        "from_agent": "implementation",
        "to_agent": "static_qa",
    },
    "static_qa_to_learning": {
        "expected_agent": "Static QA",
        "from_agent": "static_qa",
        "to_agent": "learning",
    },
    "learning_to_ac_gatekeeper": {
        "expected_agent": "Learning Agent",
        "from_agent": "learning",
        "to_agent": "ac_gatekeeper",
    },
}


def _normalize_ticket_id(ticket_id: str) -> str:
    from gates.todo_validation_check import _normalize_ticket_id as norm

    return norm(ticket_id)


def run_transition_gates(
    ticket_id: str,
    transition: str,
    *,
    checkpoints_dir: str = DEFAULT_CHECKPOINTS_DIR,
) -> tuple[int, dict[str, Any]]:
    """
    Run mandatory todo + handoff gates for a named transition.

    Returns (exit_code, summary) where exit_code is 0 only if both gates PASS.
    """
    if transition not in TRANSITIONS:
        return 2, {
            "error": f"unknown transition {transition!r}",
            "valid_transitions": sorted(TRANSITIONS),
        }

    row = TRANSITIONS[transition]
    normalized = _normalize_ticket_id(ticket_id)
    base_inputs: dict[str, Any] = {
        "ticket_id": normalized,
        "checkpoints_dir": checkpoints_dir,
        "mode": "blocking",
    }

    todo_result = todo_run(
        {
            **base_inputs,
            "expected_agent": row["expected_agent"],
            "upstream_agent": row["expected_agent"],
            "downstream_agent": row["to_agent"],
        }
    )
    handoff_result = handoff_run(
        {
            **base_inputs,
            "from_agent": row["from_agent"],
            "to_agent": row["to_agent"],
            "upstream_agent": row["from_agent"],
            "downstream_agent": row["to_agent"],
        }
    )

    summary = {
        "ticket_id": normalized,
        "transition": transition,
        "todo_validation_check": todo_result,
        "handoff_validation_check": handoff_result,
    }

    if todo_result.get("status") != "PASS":
        return 1, summary
    if handoff_result.get("status") != "PASS":
        return 1, summary
    return 0, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run mandatory todo + handoff gates for a workflow stage transition.",
    )
    parser.add_argument("--ticket-id", required=True, help="Ticket id (e.g. M902-23)")
    parser.add_argument(
        "--transition",
        required=True,
        choices=sorted(TRANSITIONS),
        help="Named transition (see agent_context/.../mandatory_workflow_gates_v1.md)",
    )
    parser.add_argument(
        "--checkpoints-dir",
        default=DEFAULT_CHECKPOINTS_DIR,
        help="Checkpoints root (default: project_board/checkpoints)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full gate results as JSON on stdout",
    )
    args = parser.parse_args(argv)

    code, summary = run_transition_gates(
        args.ticket_id,
        args.transition,
        checkpoints_dir=args.checkpoints_dir,
    )

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        todo = summary.get("todo_validation_check", {})
        handoff = summary.get("handoff_validation_check", {})
        if "error" in summary:
            print(summary["error"], file=sys.stderr)
            print("Valid transitions:", ", ".join(summary["valid_transitions"]), file=sys.stderr)
        else:
            print(f"transition={summary['transition']} ticket_id={summary['ticket_id']}")
            print(f"  todo_validation_check: {todo.get('status')} — {todo.get('message', '')}")
            print(
                f"  handoff_validation_check: {handoff.get('status')} — {handoff.get('message', '')}"
            )

    if code != 0:
        for gate_name in ("todo_validation_check", "handoff_validation_check"):
            result = summary.get(gate_name, {})
            if isinstance(result, dict) and result.get("status") == "FAIL":
                print(f"\n--- {gate_name} FAIL ---", file=sys.stderr)
                print(result.get("message", ""), file=sys.stderr)
                for hint in result.get("remediation_hints") or []:
                    print(f"  - {hint}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
