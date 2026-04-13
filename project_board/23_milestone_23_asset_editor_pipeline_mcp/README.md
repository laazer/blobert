# Epic: Milestone 23 – Asset Editor Pipeline MCP (Agent Model Iteration)

**Goal:** Give coding agents a **stable, tool-shaped interface** over the existing **Blobert Asset Editor API** (`asset_generation/web/backend`, FastAPI on `:8000`) so they can **edit generator source**, **run Blender exports**, **read logs and exit status**, and **read/update `model_registry.json`** without ad-hoc shell or brittle SSE parsing — enabling faster draft → preview → registry loops.

## Scope

- **Contract first:** Normative mapping from MCP tool names → HTTP routes, payloads, errors, and timeouts; alignment with MRVC (`model_registry_draft_versions_spec.md`) and existing allowlists.
- **Backend gap fix:** Today `/api/run/stream` is SSE-oriented; agents need a **single completion result** (exit code, aggregated log tail, guessed `output_file` path) with a **bounded wait** or a small **poll** model, without removing the streaming endpoint the UI uses.
- **MCP server:** A separate **stdio MCP** process (repo-local package) that calls `http://127.0.0.1:8000` only — no arbitrary shell from tools. Tools wrap: health, run-to-completion, registry read/patch (as already exposed), files read/write under existing path jail, optional assets list / GLB metadata if needed for iteration.
- **Security & ops:** Localhost-only default; optional shared-secret header; document threat model (same class as “local dev API”).
- **Documentation:** How to run `task editor` / `start.sh`, enable MCP in Cursor/Claude, and minimum smoke checks.
- **Agent skill:** A repo-local skill under `asset_generation/resources/` so agents consistently use the MCP tools and iteration loop (ticket `06`).

## Out of Scope (this milestone)

- In-engine Godot preview or headless render turntables (optional follow-up ticket).
- Replacing the React editor or changing MRVC semantics.
- **Milestone 22** (game control MCP) — different surface (runtime playtest vs asset pipeline).

## Dependencies

- **M21** — Asset editor backend/frontend and `/api/run`, `/api/registry`, `/api/files`, `/api/assets` must remain the integration point.
- Blender + `asset_generation/python` pipeline functional per `CLAUDE.md`.

## Exit Criteria

With the asset editor stack running locally, an agent using the new MCP can: (1) **read/write** a allowed `.py` file under `asset_generation/python/src/`, (2) **trigger** an `animated` or `player` generation with draft/output options and receive **structured success/failure** including output path hints, (3) **read** registry state and **apply** an allowed registry mutation the UI could also perform, (4) follow **documented** setup in-repo, (5) load the **skill** from `asset_generation/resources/` for procedural guidance aligned with the spec.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting validation
- `done/` – Verified, merged

## Tickets (planned)

| Order | Ticket | Role |
|------|--------|------|
| 1 | `01_spec_asset_pipeline_mcp_and_agent_http_api.md` | Spec + tool catalog + security notes |
| 2 | `02_backend_blocking_or_polled_run_endpoint.md` | Agent-friendly run completion + pytest coverage |
| 3 | `03_mcp_stdio_server_wrapping_asset_editor_api.md` | Implement MCP tools calling FastAPI |
| 4 | `04_documentation_cursor_and_claude_mcp_setup.md` | Operator docs + example config |
| 5 | `05_backlog_optional_glb_validation_or_preview_hooks.md` | Stretch — deferred (see ticket + `asset_generation/mcp/README.md` §Future work) |
| 6 | `06_agent_skill_blobert_asset_pipeline_mcp.md` | Agent skill under `asset_generation/resources/` |
