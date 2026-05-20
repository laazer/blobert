# M902-22: Early-Stop Detection

**Status:** PENDING  
**Target:** 2026-07-29

## Overview

Implement loop detection heuristics that identify when an agent is stuck (same error 3× in a row, no progress for N iterations) and gracefully break out or escalate. Prevents runaway loops that waste tokens. Inspired by smallcode's early-stop mechanism.

## Acceptance Criteria

- [ ] Detect repetition: same error message in last 3 agent iterations → escalate
- [ ] Detect stalls: same diff/modification in last 3 iterations → escalate
- [ ] Detect no-op changes: agent ran tools but no file changes → flag after 2 iterations
- [ ] Track iteration state: error messages, diffs, modifications per iteration
- [ ] Store state in checkpoint: `project_board/checkpoints/<ticket_id>/agent_iterations.json`
- [ ] Escalation path: when stuck, break agent loop and create structured handoff to different agent or human
- [ ] Logging: all stuck detections logged with evidence (iterations, diffs, errors)
- [ ] Tested with 5+ stuck scenarios:
  - [ ] Same compile error repeated → detect after 3 iterations
  - [ ] Test fails, agent runs same fix 3× → detect repetition
  - [ ] Agent makes no file changes for 2 iterations → flag
- [ ] Agent runbook: how to interpret escalation and restart
- [ ] Configuration: max iterations before escalation (default: 5)

## Implementation Notes

- Iteration tracking: append to checkpoint log after each agent call
- Compare last N iterations for pattern matching
- Store hash of diffs to detect identical changes
- Only activate on agent loops (not single calls)
- High confidence required before escalation (3+ confirmations)

## Example Iteration Log

```json
{
  "ticket_id": "M902-09",
  "agent": "implementation",
  "iterations": [
    {
      "iteration": 1,
      "error": "ruff: E501 line too long",
      "diff_hash": "abc123",
      "modified_files": ["src/main.py"]
    },
    {
      "iteration": 2,
      "error": "ruff: E501 line too long",
      "diff_hash": "abc123",
      "modified_files": ["src/main.py"]
    },
    {
      "iteration": 3,
      "error": "ruff: E501 line too long",
      "diff_hash": "abc123",
      "modified_files": ["src/main.py"],
      "escalation_triggered": true,
      "reason": "Same error 3 times, same diff"
    }
  ]
}
```

## Spec Reference

See: `project_board/specs/902_22_early_stop_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- Checkpoint logging infrastructure

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Red (behavioral + adversarial; `early_stop_tracker.py` not implemented)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent (Generalist) — `ci/scripts`

## Required Input Schema
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/22_early_stop_detection.md",
  "execution_plan_path": "project_board/execution_plans/M902-22_early_stop_detection.md",
  "spec_path": "project_board/specs/902_22_early_stop_spec.md",
  "test_modules": [
    "tests/ci/test_early_stop_detection.py",
    "tests/ci/test_early_stop_detection_adversarial.py"
  ],
  "implementation_targets": [
    "ci/scripts/early_stop_tracker.py",
    "ci/scripts/agent_invocation_middleware.py"
  ],
  "reference_modules": [
    "ci/scripts/context_budget_tracker.py"
  ]
}
```

## Status
Proceed

## Reason
Adversarial suite `tests/ci/test_early_stop_detection_adversarial.py` covers corrupt JSON, schema mismatch, huge errors, concurrent append, JSONL idempotency, one-byte diff hash sensitivity, whitespace vacuity, and middleware fail-safe paths. Implement `early_stop_tracker.py` + middleware hook until both test modules pass.
