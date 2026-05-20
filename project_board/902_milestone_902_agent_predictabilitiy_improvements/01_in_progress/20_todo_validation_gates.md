# M902-20: TODO Validation Gates

**Status:** PENDING  
**Target:** 2026-07-15

## Overview

Implement validation gates that ensure agents fully complete their task decomposition (TodoWrite) before handing off to downstream agents. Prevents silent handoff failures where an agent leaves tasks incomplete. Inspired by smallcode's atomic step validation.

## Acceptance Criteria

- [ ] Gate function: `validate_todos(ticket_id: str, expected_agent: str) -> GateResult`
- [ ] Validates that all tasks in TodoWrite list for the ticket moved from `in_progress` → `completed`
- [ ] Detects incomplete tasks (still `in_progress` after agent finishes)
- [ ] Blocks advancement if any task remains `in_progress`
- [ ] Returns structured error with list of incomplete tasks and remediation (agent should finish them)
- [ ] Integrated into gate registry as `todo_validation_check`
- [ ] Tested with 5+ scenarios:
  - [ ] All tasks completed → PASS
  - [ ] One task incomplete → FAIL (list incomplete task)
  - [ ] Multiple incomplete → FAIL (list all)
  - [ ] No tasks present → PASS (vacuous)
  - [ ] Empty todo list → PASS
- [ ] Optional: Track task completion time to identify slow/stuck tasks
- [ ] Runbook: How agents should interpret FAIL output and retry

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
INTEGRATION

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Green — `python -m pytest tests/ci/test_todo_validation_gate.py tests/ci/test_todo_validation_gate_adversarial.py -q` → **66 passed** (AC gatekeeper re-run 2026-05-20). Evidence: `validate_todos` API (`test_validate_todos_all_completed_passes`, `test_validate_todos_one_in_progress_fails`, `test_validate_todos_three_in_progress_sorted`, `test_validate_todos_no_artifacts_vacuous_pass`, `test_validate_todos_empty_todos_passes`); registry (`test_gate_registry_contains_todo_validation_check`); adversarial path/attribution/schema cases in `test_todo_validation_gate_adversarial.py`.
- Static QA: Not Run (CI gate module only; no Godot/asset_generation Python diff in scope).
- Integration: **Partial** — core gate + registry evidenced by tests; **runbook deliverable missing** (`project_board/checkpoints/M902-20/TODO_VALIDATION_RUNBOOK.md` per spec Req 10 / execution plan Task 8; ticket AC “Runbook”). Spec Req 10 summary exists in `project_board/specs/902_20_todo_validation_spec.md` but standalone agent-facing runbook not present; `todo_validation_check` not documented in milestone README gate reference.
- Optional timing AC: PASS — `_compute_timing_diagnostics` + adversarial slow-task tests.
- Git closure (workflow mandatory): **FAIL** — dirty working tree (`ci/scripts/gates/todo_validation_check.py`, both test modules, `project_board/LEARNINGS.md`); branch `main` **ahead of origin/main by 7 commits**, not pushed.

## Blocking Issues
- Work not committed/pushed. Dirty tree and unpushed commits block Stage COMPLETE per `workflow_enforcement_v1.md` (Commit and Push BEFORE COMPLETE Closure). Implementation Agent must commit M902-20 artifacts and push before re-gate.
- Runbook AC unmet: missing `project_board/checkpoints/M902-20/TODO_VALIDATION_RUNBOOK.md` (spec AC-10.1–10.3 / ticket AC “Runbook”). Route Documentation Agent or Integration Agent per execution plan Task 8.

## Escalation Notes
- Code ACs (validator, FAIL payload, registry, 5+ scenarios, optional timing) satisfied by pytest evidence. COMPLETE deferred for documentation + git hygiene only.

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent (Generalist)

## Required Input Schema
```json
{
  "actions": [
    "git add ci/scripts/gates/todo_validation_check.py tests/ci/test_todo_validation_gate.py tests/ci/test_todo_validation_gate_adversarial.py",
    "git commit with Conventional Commit for M902-20",
    "git push origin main"
  ],
  "then_route": "Documentation Agent or Integration Agent",
  "runbook_path": "project_board/checkpoints/M902-20/TODO_VALIDATION_RUNBOOK.md",
  "spec_runbook_ref": "project_board/specs/902_20_todo_validation_spec.md#requirement-10-agent-runbook--fail-interpretation-and-retry"
}
```

## Status
Blocked

## Reason
Gatekeeper re-verified 66/66 pytest PASS for code ACs; cannot set COMPLETE: (1) dirty/unpushed git, (2) runbook artifact missing per ticket AC and spec Req 10. After commit/push + runbook, re-invoke Acceptance Criteria Gatekeeper for COMPLETE and `git mv` to `02_complete/`.
