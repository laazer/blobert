# TICKET: 01_spec_asset_pipeline_mcp_and_agent_http_api

Title: Spec — Asset pipeline MCP tool catalog and agent-oriented HTTP API contract

## Description

Author a normative spec under `project_board/specs/` (stable filename, e.g. `asset_pipeline_mcp_spec.md`) that defines how **coding agents** interact with the asset generation loop **via MCP tools** backed by the **existing FastAPI** app (`asset_generation/web/backend`).

The spec must bridge:

- **M21** editor behavior (Monaco + SSE run stream) and **MRVC** (`project_board/specs/model_registry_draft_versions_spec.md`) — registry paths, allowlists, draft vs in-use semantics.
- **Gap:** SSE is human-friendly but agent-awkward; the spec must require a **completion-oriented** HTTP contract (see ticket `02_backend_blocking_or_polled_run_endpoint.md`) and document exact JSON shapes, status codes, and timeout behavior.

Include a **tool catalog** table: tool name, purpose, HTTP method/path (or internal note if tool batches multiple calls), required/optional parameters, success and error payloads, and idempotency notes where relevant.

## Acceptance Criteria

- Spec file exists at `project_board/specs/` with a clear **spec ID prefix** (e.g. APMCP) and traceability to this milestone README.
- **Security:** Threat model section — localhost binding, optional shared secret, no shell execution from MCP tools, path-jail rules delegated to existing routers.
- **MRVC alignment:** Explicit statement that MCP registry tools **must not** bypass `_ALLOWLIST_PREFIXES` or path normalization rules already enforced in `routers/registry.py`.
- **Run API:** Normative requirements for the agent run endpoint: parameters parity with `/api/run/stream` query params (`cmd`, `enemy`, `count`, `finish`, `hex_color`, `build_options`, `output_draft`, etc.) unless a deliberate subset is documented with rationale.
- Downstream tickets (`02`–`04`, `06`) can implement without reopening contract churn: tool list and HTTP shapes are frozen enough for implementation; ticket `06` skill must reference the final tool names from this spec.

## Dependencies

- M21 — existing routes: `routers/run.py`, `routers/registry.py`, `routers/files.py`, `routers/assets.py`
- MRVC spec — `project_board/specs/model_registry_draft_versions_spec.md`

## Workflow State

Stage: BACKLOG
