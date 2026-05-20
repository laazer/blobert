# Atomic Handoff Checkpoint Runbook (schema 1.0)

**Ticket:** M902-23 | **Spec:** `project_board/specs/902_23_atomic_handoff_spec.md`

## Before every stage handoff

1. Finish agent work for the current stage.
2. Run `todo_validation_check` (M902-20) for the finishing agent.
3. Write `project_board/checkpoints/<ticket_id>/handoff-latest.yaml` using the frozen catalog for your pair (see spec Req 05–11).
4. Run `handoff_validation_check` with matching `from_agent` / `to_agent`.
5. Only advance the ticket when both gates PASS (blocking mode) or log shadow FAIL for human review.

## Artifact location

- Primary: `project_board/checkpoints/<ticket_id>/handoff-latest.yaml`
- History (optional): `handoff-<run-id>.yaml`
- Fallback: fenced ` ```yaml handoff ` block in checkpoint `.md` files

## Valid pairs

| From | To |
|------|-----|
| planner | spec |
| spec | test_designer |
| test_designer | test_breaker |
| test_breaker | implementation |
| implementation | static_qa |
| static_qa | learning |
| learning | ac_gatekeeper |

## Reason codes

| Rule | Meaning |
|------|---------|
| `handoff_item_missing` | Required item incomplete or absent |
| `handoff_blocked` | Required item blocked — do not proceed |
| `handoff_evidence_missing` | Complete without evidence or path missing |
| `handoff_pair_mismatch` | YAML pair ≠ gate inputs |
| `handoff_artifact_missing` | No handoff file found |
| `handoff_artifact_invalid` | Parse/schema error |
| `handoff_counter_mismatch` | Counter fields ≠ computed |
| `path_traversal` | Unsafe ticket_id or symlink escape |

## CLI

```bash
python ci/scripts/gate_runner.py handoff_validation_check \
  --input '{"ticket_id":"M902-23","from_agent":"spec","to_agent":"test_designer"}' \
  --mode shadow
```

Set `handoff_optional: true` only in shadow rollout when artifact not yet written.
