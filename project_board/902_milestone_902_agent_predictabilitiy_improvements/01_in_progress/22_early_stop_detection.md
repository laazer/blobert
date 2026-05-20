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
INTEGRATION

## Revision
6

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: `tests/ci/test_early_stop_detection.py` + `tests/ci/test_early_stop_detection_adversarial.py` — **45 passed** (gatekeeper re-run 2026-05-20; 0.36s). Coverage maps to AC: `repeated_error` (3× same error, incl. lint/compile-style `_SAME_ERROR`), `repeated_diff` (3× same `diff_hash` / “same fix”), no-op flag at 2× without escalate, `max_iterations` default 5 (T5 + env override), A-B-A-B non-trigger, missing artifact fail-safe, `on_early_stop` callback (T10), JSONL escalation events with evidence payloads
- Static QA: Ruff via `task hooks:py-review` on `ci/scripts/early_stop_tracker.py`, `ci/scripts/agent_invocation_middleware.py` — PASS
- Integration:
  - **Tracker:** `ci/scripts/early_stop_tracker.py` — `record_iteration`, `evaluate_early_stop`; persists `project_board/checkpoints/<ticket_id>/agent_iterations.json`; append-only `early_stop_events.jsonl` with iteration/diff/error evidence
  - **Middleware:** `_maybe_record_early_stop_iteration` in `agent_invocation_middleware.py` (loop_mode + `EARLY_STOP_DETECTION` opt-out); structured `EarlyStopResult` + optional `on_early_stop` break-loop handoff
  - **Runbook:** `project_board/checkpoints/M902-22/EARLY_STOP_RUNBOOK.md` (reason codes, restart, config table)
  - **Configuration:** defaults `EARLY_STOP_MAX_ITERATIONS=5`, error/diff thresholds 3, noop threshold 2 (documented in runbook + env parsing in tracker)
- Acceptance criteria coverage: all listed AC items evidenced by tests/integration above; nested “5+ stuck scenarios” satisfied via T2–T7 + adversarial corrupt/concurrent/JSONL paths (45 cases total)

## Blocking Issues
- **Git closure gate (mandatory):** M902-22 implementation artifacts are not committed (`ci/scripts/early_stop_tracker.py`, middleware hook, test modules, spec, execution plan, checkpoints/runbook). `git status` is dirty on `main`.
- **Git push gate (mandatory):** `main` is **24 commits ahead** of `origin/main`; push not verified. Stage `COMPLETE` and move to `02_complete/` deferred until commit + successful `git push`.

## Escalation Notes
- After commit/push, re-run Acceptance Criteria Gatekeeper to set `COMPLETE`, check AC boxes, and `git mv` ticket to `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/22_early_stop_detection.md`

---

# NEXT ACTION

## Next Responsible Agent
Human (or orchestrator commit handoff)

## Required Input Schema
```json
{
  "action": "commit_and_push",
  "paths": [
    "ci/scripts/early_stop_tracker.py",
    "ci/scripts/agent_invocation_middleware.py",
    "tests/ci/test_early_stop_detection.py",
    "tests/ci/test_early_stop_detection_adversarial.py",
    "project_board/specs/902_22_early_stop_spec.md",
    "project_board/execution_plans/M902-22_early_stop_detection.md",
    "project_board/checkpoints/M902-22/EARLY_STOP_RUNBOOK.md",
    "project_board/checkpoints/M902-22/"
  ],
  "suggested_commit_scope": "feat(ci): early-stop loop detection (M902-22)",
  "then": "re-invoke Acceptance Criteria Gatekeeper on this ticket path"
}
```

## Status
Blocked

## Reason
Behavioral and adversarial tests pass (45/45) and every acceptance criterion has objective coverage, but workflow_enforcement_v1 **Commit and Push BEFORE COMPLETE** is unmet: working tree dirty and branch unpushed. Commit all M902-22 artifacts, `git push`, then re-run gatekeeper for `COMPLETE` + `02_complete/` move and AC checkbox updates.
