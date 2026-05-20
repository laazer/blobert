# M902-20: TODO Validation Gates

**Status:** COMPLETE  
**Target:** 2026-07-15  
**Completed:** 2026-05-20

## Overview

Implement validation gates that ensure agents fully complete their task decomposition (TodoWrite) before handing off to downstream agents. Prevents silent handoff failures where an agent leaves tasks incomplete. Inspired by smallcode's atomic step validation.

## Acceptance Criteria

- [x] Gate function: `validate_todos(ticket_id: str, expected_agent: str) -> GateResult`
- [x] Validates that all tasks in TodoWrite list for the ticket moved from `in_progress` → `completed`
- [x] Detects incomplete tasks (still `in_progress` after agent finishes)
- [x] Blocks advancement if any task remains `in_progress`
- [x] Returns structured error with list of incomplete tasks and remediation (agent should finish them)
- [x] Integrated into gate registry as `todo_validation_check`
- [x] Tested with 5+ scenarios:
  - [x] All tasks completed → PASS
  - [x] One task incomplete → FAIL (list incomplete task)
  - [x] Multiple incomplete → FAIL (list all)
  - [x] No tasks present → PASS (vacuous)
  - [x] Empty todo list → PASS
- [x] Optional: Track task completion time to identify slow/stuck tasks
- [x] Runbook: How agents should interpret FAIL output and retry

## Implementation Notes

- Read TodoWrite checkpoint files from `project_board/checkpoints/<ticket_id>/`
- Each todo entry has `status`, `content`, `activeForm` fields
- Only validate tasks marked `in_progress` by current agent
- Do not penalize agents for tasks left by previous agents
- Gate runs at agent stage transitions (after agent completes, before next agent starts)

## Example Failure Output

```json
{
  "gate_name": "todo_validation_check",
  "status": "FAIL",
  "incomplete_tasks": [
    {
      "content": "Implement user authentication",
      "status": "in_progress",
      "agent": "implementation"
    },
    {
      "content": "Write authentication tests",
      "status": "in_progress",
      "agent": "test-designer"
    }
  ],
  "message": "2 tasks remain in_progress. Agent should complete or explicitly move to pending/deferred.",
  "remediation": "Run TodoWrite to move completed tasks to 'completed' status before handing off."
}
```

## Spec Reference

See: `project_board/specs/902_20_todo_validation_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- TodoWrite tool integration

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: **66/66 PASS** — `python -m pytest tests/ci/test_todo_validation_gate.py tests/ci/test_todo_validation_gate_adversarial.py -q`
- Static QA: Python review path confinement fix applied; NFR-3 repo/cwd anchor
- Integration: `todo_validation_check` in `gate_registry.json` (shadow); runbook at `project_board/checkpoints/M902-20/TODO_VALIDATION_RUNBOOK.md`
- Commits: `674c7cb` (feat), `5b909d9` (path hardening + runbook)
- Git push: Human reminder — branch ahead of origin

## Blocking Issues
- None

## Escalation Notes
- Orchestrator wiring at stage transitions deferred to M902-23 per spec

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "action": "git push origin main"
}
```

## Status
Proceed

## Reason
All acceptance criteria evidenced. Ticket in `02_complete/`. Push when ready.
