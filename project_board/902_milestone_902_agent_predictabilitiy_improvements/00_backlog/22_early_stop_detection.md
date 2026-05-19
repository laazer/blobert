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
