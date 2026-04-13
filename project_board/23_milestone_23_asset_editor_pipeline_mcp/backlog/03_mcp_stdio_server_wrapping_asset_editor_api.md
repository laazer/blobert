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

Implementation language: **TypeScript (Node)** or **Python** — match repo maintainability; if Python, align with `uv` project layout or document standalone `pip install -e` for the MCP package.

## Acceptance Criteria

- `README.md` next to the server lists dependencies, env vars, and a one-line run command.
- With backend up (`task editor` / `start.sh`), a developer can register the MCP in Cursor and invoke at least **health**, **files get**, **registry get**, and **run** (using a fast cmd in dev) successfully.
- Tool descriptions are written for **LLM** consumption (clear parameters, when to use draft `output_draft`, expected failure modes).

## Dependencies

- Ticket `02_backend_blocking_or_polled_run_endpoint.md` for blocking run tool
- Ticket `01` spec for exact tool names and shapes

## Workflow State

Stage: BACKLOG
