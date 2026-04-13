# Asset Pipeline MCP — Cursor & Claude Code setup

This guide enables the **Blobert asset pipeline** [Model Context Protocol](https://modelcontextprotocol.io/) server so agents can call the local asset editor API (`FastAPI` on port **8000**) via frozen tool names from **`project_board/specs/asset_pipeline_mcp_spec.md`** (APMCP).

**Package code:** `asset_generation/python/src/blobert_asset_pipeline_mcp/` (FastMCP + httpx).

## Prerequisites

1. **Editor API running** on `http://127.0.0.1:8000`:

   ```bash
   task editor
   # or
   bash asset_generation/web/start.sh
   ```

2. **Python env** (from repo root, with `direnv` or manual `uv` per `CLAUDE.md`):

   ```bash
   cd asset_generation/python && uv sync --extra mcp
   # or: uv sync --extra dev   # includes fastmcp
   ```

3. Smoke the API:

   ```bash
   curl -sS http://127.0.0.1:8000/api/health
   ```

## Security

- **Local-only by default.** The MCP process uses httpx against `127.0.0.1` — not browser CORS.
- **Do not** expose the asset editor to the public internet without TLS, authentication, and network isolation.
- Optional: set `BLOBERT_ASSET_API_TOKEN` in the MCP `env` if your deployment adds a matching `X-Blobert-Asset-Token` check on the backend.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BLOBERT_ASSET_API_BASE` | `http://127.0.0.1:8000` | Editor origin |
| `BLOBERT_ASSET_API_TOKEN` | unset | Optional auth header |
| `PYTHONPATH` | must include `src` | Import package `blobert_asset_pipeline_mcp` |

## Cursor

Official overview: [Cursor MCP documentation](https://docs.cursor.com/context/model-context-protocol).

Add a stdio server that runs from **`asset_generation/python`** with `PYTHONPATH=src`. Example fragment (merge into your Cursor MCP config; paths often support `${workspaceFolder}` when the workspace is the repo root):

```json
{
  "mcpServers": {
    "blobert-asset-pipeline": {
      "command": "uv",
      "args": ["run", "--extra", "mcp", "python", "-m", "blobert_asset_pipeline_mcp"],
      "cwd": "${workspaceFolder}/asset_generation/python",
      "env": {
        "PYTHONPATH": "src",
        "BLOBERT_ASSET_API_BASE": "http://127.0.0.1:8000"
      }
    }
  }
}
```

If `${workspaceFolder}` is not expanded, set `"cwd"` to the **absolute** path of `asset_generation/python` on your machine.

## Claude Code

This repo may already have a root **`.mcp.json`**. Merge a new entry (same `uv` invocation); use a **repo-relative** `cwd` from the project root:

```json
{
  "mcpServers": {
    "blobert-asset-pipeline": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--extra", "mcp", "python", "-m", "blobert_asset_pipeline_mcp"],
      "cwd": "asset_generation/python",
      "env": {
        "PYTHONPATH": "src",
        "BLOBERT_ASSET_API_BASE": "http://127.0.0.1:8000"
      }
    }
  }
}
```

Restart / reload the MCP session after editing.

## First successful tool call (acceptance check)

1. Start the editor (`task editor`).
2. Enable the MCP server in Cursor or Claude Code using the fragment above.
3. In the agent, invoke **`blobert_asset_pipeline_health`**.
4. Expect a JSON-shaped result with **`status_code`** `200` and **`data`** containing `"status": "ok"` (see `format_http_response` in the MCP package).

Alternative: **`blobert_asset_pipeline_files_read`** with a real path under the jail, e.g. a `.py` file under `src/` (e.g. `enemies/animated_spider.py` if present).

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| Connection refused / httpx error | Backend up? `curl http://127.0.0.1:8000/api/health` |
| `uv: command not found` | Shell PATH / `direnv` / run `which uv` from the same environment the MCP uses |
| `ModuleNotFoundError: blobert_asset_pipeline_mcp` | `cwd` must be `asset_generation/python` and `PYTHONPATH` must include `src` |
| HTTP **409** on run tools | Single-flight: another run is active — use **`blobert_asset_pipeline_run_status`** or **`blobert_asset_pipeline_run_kill`** |
| HTTP **504** on `run_complete` | Increase `max_wait_ms` or wait/poll status (see APMCP spec) |
| “CORS” in browser | Irrelevant for MCP (server-side httpx only) |

## Agent skill (ticket `06`)

Procedural guidance for agents lives under:

`asset_generation/resources/agent_skills/blobert-asset-pipeline-mcp/SKILL.md`

Bundled skills index: `asset_generation/resources/README.md`. Install by symlinking or copying the skill folder into your client’s skills directory (e.g. `.cursor/skills/` or your Claude Code skills path). Contract tests keep SKILL.md aligned with registered MCP tool names (`tests/specs/test_blobert_asset_pipeline_skill_contract.py`).

## Future work — GLB validation / preview (optional, M23-05)

**Not** part of M23 core closure. Possible follow-ups: run a **glTF validator** on an allowlisted export path and return structured issues; optional **single-frame render** or screenshot (Blender batch or headless Godot) if cost is acceptable. Dependencies: core MCP iteration complete (`01`–`04`, `06`), plus art/tech direction on pixels-in-the-loop.

Ticket: `project_board/23_milestone_23_asset_editor_pipeline_mcp/done/05_backlog_optional_glb_validation_or_preview_hooks.md`

## See also

- `asset_generation/python/src/blobert_asset_pipeline_mcp/README.md` — developer-focused package notes  
- `project_board/specs/asset_pipeline_mcp_spec.md` — normative tool catalog and HTTP contract  
