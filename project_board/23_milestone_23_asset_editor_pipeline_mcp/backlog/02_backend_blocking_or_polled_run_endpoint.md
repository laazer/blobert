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

## Workflow State

Stage: BACKLOG
