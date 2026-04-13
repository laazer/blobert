# TICKET: 03_mcp_stdio_server_wrapping_asset_editor_api

Title: MCP server — stdio tools calling the Blobert Asset Editor API

## Description

Add a **small MCP server package** in-repo (path chosen during implementation; e.g. `asset_generation/mcp/asset_pipeline/` or `tools/mcp_blobert_asset_pipeline/`) that:

- Uses **stdio transport** (Cursor/Claude compatible).
- Reads **`BLOBERT_ASSET_API_BASE`** (or similar) defaulting to `http://127.0.0.1:8000`.
- Implements tools that map 1:1 to the ticket `01` catalog, minimally:
  - **Health** — `GET /api/health`
  - **Run generate (blocking)** — new completion endpoint from ticket `02` (`animated` / `player` / other allowed cmds as spec’d)
  - **Run status** — `GET /api/run/status` if still useful for poll-based design
  - **Registry** — read manifest + targeted mutations already exposed under `/api/registry/*`
  - **Files** — read/write `.py` under the existing path jail (`/api/files/...`)
  - **Assets** (optional) — list or fetch metadata if needed for iteration; align with `routers/assets.py`
- **No** arbitrary shell execution tools. **No** direct filesystem access outside HTTP API semantics.

**Implementation stack:** **Python** with **[FastMCP](https://github.com/PrefectHQ/fastmcp)** (`pip install fastmcp` / `uv add fastmcp`), **stdio** transport (FastMCP default), tools implemented as async functions using **`httpx.AsyncClient`** against `BLOBERT_ASSET_API_BASE`. Add the package under e.g. `asset_generation/python/` (new optional dependency group or sibling package) or `asset_generation/mcp/` per `project_board/specs/asset_pipeline_mcp_spec.md` ADR-APMCP-003. **TypeScript/Node MCP is out of scope** for this ticket unless the spec is revised.

## Acceptance Criteria

- `README.md` next to the server lists dependencies, env vars, and a one-line run command.
- With backend up (`task editor` / `start.sh`), a developer can register the MCP in Cursor and invoke at least **health**, **files get**, **registry get**, and **run** (using a fast cmd in dev) successfully.
- Tool descriptions are written for **LLM** consumption (clear parameters, when to use draft `output_draft`, expected failure modes).

## Dependencies

- Ticket `02_backend_blocking_or_polled_run_endpoint.md` for blocking run tool
- Ticket `01` spec for exact tool names and shapes

## Execution Plan

1. Add `fastmcp` optional extra `mcp` + dev pin; extend pytest `pythonpath` with `src`.
2. Implement `src/blobert_asset_pipeline_mcp/` (`http_util.py`, `server.py`, `__main__.py`) mapping APMCP tool names → httpx calls.
3. README with env vars and `PYTHONPATH=src uv run --extra mcp python -m blobert_asset_pipeline_mcp`.
4. Unit tests for encoding/response formatting and `list_tools` name coverage.

## Specification

- **APMCP:** `project_board/specs/asset_pipeline_mcp_spec.md` §MCP tool catalog

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

7

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `uv run pytest tests/blobert_asset_pipeline_mcp/ -v` (7 passed); full `uv run pytest tests/` 933 passed; FastMCP `list_tools` covers frozen APMCP names.
- Static QA: Passing — `ruff check src/blobert_asset_pipeline_mcp tests/blobert_asset_pipeline_mcp`
- Integration: Manual — with `task editor` running, `PYTHONPATH=src uv run --extra mcp python -m blobert_asset_pipeline_mcp` in another shell; Cursor MCP config is ticket `04`. Smoke: health, `registry_get`, `files_read`, `run_complete` (`cmd=stats`, `enemy=spider`, low `max_wait_ms`).

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

MCP server implemented; ticket `04` documents Cursor/Claude registration fragments.
