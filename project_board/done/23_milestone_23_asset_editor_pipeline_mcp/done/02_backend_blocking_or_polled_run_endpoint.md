# TICKET: 02_backend_blocking_or_polled_run_endpoint

Title: Backend — Agent-oriented run completion API (non-SSE)

## Description

Add an HTTP API on the asset editor backend that lets an **automated client** run the same Blender/Python jobs as `/api/run/stream` but obtain a **single JSON result** when the subprocess finishes: at minimum `exit_code`, a **bounded text log** (full stdout/stderr or tail with max bytes — document choice), and when successful the same **output path hint** logic already used in `_guess_output_file` / `done` events in `routers/run.py`.

**Constraints:**

- Do **not** remove or break the existing SSE stream used by the frontend.
- Respect `process_manager` single-flight semantics: if a job is already running, return a clear **409 or 429**-class response with a machine-readable body (document in spec).
- Configurable **server-side max wait** (query or settings) with predictable behavior when exceeded (e.g. return `202` + `run_id` + poll URL, or `504` — pick one approach in implementation and spec).

Reuse existing command-building and env var logic (`BLOBERT_EXPORT_START_INDEX`, `BLOBERT_EXPORT_USE_DRAFT_SUBDIR`, `BLOBERT_BUILD_OPTIONS_JSON`) so agent runs match UI runs.

## Acceptance Criteria

- New route documented in OpenAPI/FastAPI and in the milestone spec (`01`).
- Automated tests in `asset_generation/web/backend/tests/` cover: happy path with a **fast** command (e.g. `stats` or `test` if sufficiently quick in CI), validation errors for unknown `cmd`, and conflict when a run is already active (mock or sequential test design as appropriate).
- Manual or documented note: one `animated` run locally still works from the existing UI SSE flow unchanged.

## Dependencies

- Ticket `01_spec_asset_pipeline_mcp_and_agent_http_api.md` (spec should merge first or in same PR with tight coordination)

## Execution Plan

1. Extract `_prepare_run_environment` from `_run_stream` so SSE and `/complete` share env/command/start_index logic.
2. Implement `GET /api/run/complete` with `max_wait_ms`, bounded `log_text`, 400/409/504/200 shapes per APMCP; add `Settings` knobs.
3. Add `tests/test_run_complete_router.py` (httpx AsyncClient + stub `process_manager`).
4. Revise `project_board/specs/asset_pipeline_mcp_spec.md` to freeze 409, 504, log cap, `max_wait_ms`.
5. Extend APMCP contract tests under `asset_generation/python/tests/specs/`.

## Specification

- **APMCP:** `project_board/specs/asset_pipeline_mcp_spec.md` (APMCP-RUN, §Validation precedence)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

6

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `uv run --project asset_generation/python --extra dev python -m pytest asset_generation/web/backend/tests/test_run_complete_router.py -q` (5 passed); full `asset_generation/web/backend/tests/` 123 passed; APMCP contract tests 27 passed.
- Static QA: Passing — `python ci/scripts/spec_completeness_check.py project_board/specs/asset_pipeline_mcp_spec.md --type api` (exit 0)
- Integration: Manual — APMCP-RUN-4 documents operator smoke of M21 SSE + `animated` after backend changes; not automated in this ticket.

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
{}
```

## Status

Proceed

## Reason

`/api/run/complete` implemented; ticket `03` can wire MCP `blobert_asset_pipeline_run_complete`.
