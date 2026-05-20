# TODO Validation Gate — Agent Runbook (M902-20)

**Gate name:** `todo_validation_check`  
**When to run:** After an agent finishes work and before the orchestrator advances the ticket to the next stage (full autopilot wiring: M902-23).

## Invoke the gate

```bash
python ci/scripts/gate_runner.py todo_validation_check \
  --upstream-agent "Spec Agent" \
  --downstream-agent "Test Designer Agent" \
  --ticket-id M902-20 \
  --mode shadow \
  --input '{"ticket_id":"M902-20","expected_agent":"Spec Agent"}'
```

Replace agent names and `ticket_id` for your handoff. In blocking mode (M903+), exit code `1` on FAIL.

## Snapshot artifact

Agents must persist TodoWrite state to:

`project_board/checkpoints/<ticket_id>/todos-latest.json`

Schema: `schema_version` `"1.0"`, `ticket_id`, `agent` (envelope), `todos[]` with `id`, `content`, `status`, optional `activeForm`, optional per-todo `agent`.

## PASS

- No snapshot files → vacuous PASS (no todos tracked yet).
- Empty `todos` array → vacuous PASS.
- All todos **attributed** to `expected_agent` are `completed`, `pending`, or `cancelled`.

`pending` and `cancelled` are valid when work is deferred or abandoned; only `in_progress` blocks handoff.

## FAIL — fields to read

| Field | Use |
|-------|-----|
| `status` | Always `"FAIL"` |
| `message` | Human summary (task count, agent) |
| `incomplete_tasks[]` | Each row: `id`, `content`, `status`, `agent`, `activeForm` |
| `violations[]` | Audit rows; `rule` is usually `todo_incomplete` or `todo_artifact_invalid` |
| `remediation_hints[]` | Ordered steps to fix |

Prior-agent todos (`in_progress` but different `agent` attribution) do **not** appear in `incomplete_tasks` for the current agent.

## FAIL — remediation steps

1. Read `message` and each `incomplete_tasks[]` entry.
2. Finish the work or move the todo to `completed`, `pending`, or `cancelled` via TodoWrite.
3. Follow `remediation_hints` in order.
4. Write updated snapshot to `todos-latest.json` under the ticket checkpoint directory.
5. Re-run `todo_validation_check` with the same `ticket_id` and `expected_agent`.

Retry until PASS. Same snapshot bytes → same result (deterministic).

## Shadow vs blocking

Until M903 enforcement, shadow mode exits `0` even on FAIL. **Still remediate** before handoff; do not rely on exit code alone.

## Escalation

If FAIL persists after three remediation attempts with confirmed completed work, add a `Blocking Issues` entry on the ticket with the gate JSON path and route to Human.

## Example FAIL shape

```json
{
  "gate": "todo_validation_check",
  "status": "FAIL",
  "incomplete_tasks": [
    {
      "id": "t1",
      "content": "Implement user authentication",
      "status": "in_progress",
      "agent": "implementation"
    }
  ],
  "violations": [
    {
      "rule": "todo_incomplete",
      "message": "Todo t1 remains in_progress for agent implementation"
    }
  ],
  "remediation_hints": [
    "Complete or re-status each incomplete_tasks entry via TodoWrite",
    "Update project_board/checkpoints/<ticket_id>/todos-latest.json",
    "Re-run todo_validation_check with the same expected_agent"
  ]
}
```
