# Early-Stop Detection Runbook (schema 1.0.0)

**Ticket:** M902-22 | **Spec:** `project_board/specs/902_22_early_stop_spec.md`

## 12.1 Read artifacts

1. Open `project_board/checkpoints/<ticket_id>/agent_iterations.json` — inspect `rollup` and the last three `iterations`.
2. Open `project_board/checkpoints/<ticket_id>/early_stop_events.jsonl` — the latest line is the authoritative escalate snapshot.

## 12.2 Reason codes

| Code | Meaning | Typical action |
|------|---------|----------------|
| `repeated_error` | Same lint/test error 3× | Human reviews error; fix root cause; new `loop_run_id` |
| `repeated_diff` | Same change attempted 3× | Switch approach or agent; Human review |
| `max_iterations` | Loop budget exhausted (default 5) | Human prioritizes remaining work or splits ticket |
| (no-op flag only) | Tools ran, no files changed 2× | Check tool permissions / targets; may continue until max iter |

## 12.3 Restart procedure

1. Resolve the underlying issue (error, approach, or environment).
2. Start a new implementation loop with a **new** `loop_run_id` (do not reuse an escalated loop id).
3. Optionally archive `agent_iterations.json` to `agent_iterations.<timestamp>.json` before reset.
4. Clear ticket `BLOCKED` only after Human or planner acknowledgment in Escalation Notes.
5. Set `EARLY_STOP_DETECTION=0` only for local debugging; never in CI autopilot.

## 12.4 When to retry same agent vs switch

- `repeated_error` / `repeated_diff` → prefer **Human** first; alternate implementation agent only if Human assigns a different strategy.
- `max_iterations` → planner may split the ticket; do not blindly retry.

## Configuration

| Env var | Default |
|---------|---------|
| `EARLY_STOP_DETECTION` | enabled (`!= "0"`) |
| `EARLY_STOP_MAX_ITERATIONS` | `5` |
| `EARLY_STOP_ERROR_THRESHOLD` | `3` |
| `EARLY_STOP_DIFF_THRESHOLD` | `3` |
| `EARLY_STOP_NOOP_THRESHOLD` | `2` |

## Orchestrator kwargs (implementation loops)

| Key | Required | Notes |
|-----|----------|-------|
| `ticket_id` | yes | Short tag (e.g. `M902-22`) |
| `agent_run_id` | yes | Per-iteration unique id |
| `loop_run_id` | yes | Stable for one loop; new on Human restart |
| `loop_mode` | yes | Must be boolean `True` |
| `iteration_context` | recommended | `error`, `modified_files`, `diff_hash`, `tools_invoked` |
| `on_early_stop` | recommended | Callback when `should_escalate` |
