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
