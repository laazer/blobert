# M902-22: Early-Stop Detection

**Status:** COMPLETE  
**Target:** 2026-07-29

## Overview

Implement loop detection heuristics that identify when an agent is stuck (same error 3× in a row, no progress for N iterations) and gracefully break out or escalate. Prevents runaway loops that waste tokens. Inspired by smallcode's early-stop mechanism.

## Acceptance Criteria

- [x] Detect repetition: same error message in last 3 agent iterations → escalate
- [x] Detect stalls: same diff/modification in last 3 iterations → escalate
- [x] Detect no-op changes: agent ran tools but no file changes → flag after 2 iterations
- [x] Track iteration state: error messages, diffs, modifications per iteration
- [x] Store state in checkpoint: `project_board/checkpoints/<ticket_id>/agent_iterations.json`
- [x] Escalation path: when stuck, break agent loop and create structured handoff to different agent or human
- [x] Logging: all stuck detections logged with evidence (iterations, diffs, errors)
- [x] Tested with 5+ stuck scenarios:
  - [x] Same compile error repeated → detect after 3 iterations
  - [x] Test fails, agent runs same fix 3× → detect repetition
  - [x] Agent makes no file changes for 2 iterations → flag
- [x] Agent runbook: how to interpret escalation and restart
- [x] Configuration: max iterations before escalation (default: 5)

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
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: `tests/ci/test_early_stop_detection.py` + `tests/ci/test_early_stop_detection_adversarial.py` — **45 passed** (2026-05-20)
- Static QA: Ruff `task hooks:py-review` on tracker + middleware — PASS
- Integration: `ci/scripts/early_stop_tracker.py`, `_maybe_record_early_stop_iteration` in middleware, `EARLY_STOP_RUNBOOK.md`
- Git: `3182237` feat(ci): early-stop loop detection and escalation (M902-22)

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "action": "push",
  "note": "main is ahead of origin; push when ready"
}
```

## Status
Proceed

## Reason
All acceptance criteria evidenced; commit `3182237` on main. Push branch to remote when ready.
