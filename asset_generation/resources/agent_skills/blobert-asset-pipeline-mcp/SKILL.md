---
name: blobert-asset-pipeline-mcp
description: Use the Blobert Asset Pipeline MCP tools against the local FastAPI editor (port 8000). Covers prerequisites, MRVC-safe workflows (edit jailed Python, run pipeline, registry), tool selection vs raw HTTP, and single-flight run semantics. Normative parameters and HTTP mapping live in project_board/specs/asset_pipeline_mcp_spec.md.
argument-hint: Optional — skill is context for when MCP is enabled; no required user arguments.
---

# Blobert asset pipeline MCP

## Prerequisites

1. **Editor API running** on the machine where the MCP process executes: `task editor` or `bash asset_generation/web/start.sh` (default `http://127.0.0.1:8000`).
2. **MCP server** configured per `asset_generation/mcp/README.md` (`cwd` = `asset_generation/python`, `PYTHONPATH` includes `src`, `uv run --extra mcp python -m blobert_asset_pipeline_mcp`).
3. Optional: `BLOBERT_ASSET_API_BASE` / `BLOBERT_ASSET_API_TOKEN` if not using defaults (see APMCP spec §Configuration).

Always start with **`blobert_asset_pipeline_health`** before assuming the stack is up.

## Safety

- **Localhost posture:** These tools call the editor API over HTTP; do not ask operators to expose that API to the internet.
- **Path jail:** File tools only touch allowlisted pipeline sources (MRVC); do not try to bypass with raw paths outside the jail.
- **Single-flight runs:** Only one pipeline run at a time. If **`blobert_asset_pipeline_run_complete`** returns **409**, call **`blobert_asset_pipeline_run_status`** or **`blobert_asset_pipeline_run_kill`** before retrying. On **504** + `timed_out`, increase `max_wait_ms` or poll status and read partial logs per APMCP-RUN.

## When to use MCP vs curl

- **Prefer MCP tools** whenever the client has the asset-pipeline MCP enabled — consistent error shapes and no manual URL/header assembly.
- **Fallback to documented HTTP** only if MCP is unavailable; use the same paths and query/body shapes as in `project_board/specs/asset_pipeline_mcp_spec.md` (APMCP).

## Typical workflow

1. **`blobert_asset_pipeline_health`** — confirm API reachability.
2. **Discover / edit code**
   - **`blobert_asset_pipeline_files_list`** — see editable `.py` tree under the jail.
   - **`blobert_asset_pipeline_files_read`** / **`blobert_asset_pipeline_files_write`** — change procedural sources (e.g. under `src/enemies/`).
3. **Run generation**
   - **`blobert_asset_pipeline_run_complete`** with `cmd` and optional `enemy`, `count`, `build_options`, `output_draft`, `max_wait_ms`, etc. Prefer completion JSON over SSE (`/api/run/stream` is for humans).
   - Interpret **`exit_code`**, log tail, and HTTP status (**400** / **409** / **504**) per APMCP failure taxonomy.
4. **Registry (MRVC)**
   - **`blobert_asset_pipeline_registry_get`** — full manifest after runs or edits.
   - Use patch/put/sync/delete tools as needed; destructive calls require the confirmation bodies described in the spec and backend OpenAPI.
   - **`blobert_asset_pipeline_registry_load_existing_candidates`** / **`blobert_asset_pipeline_registry_load_existing_open`** when importing existing exports.
5. **Assets**
   - **`blobert_asset_pipeline_assets_list`** / **`blobert_asset_pipeline_assets_get`** to inspect GLB/JSON exports when validating output paths.
6. **Metadata**
   - **`blobert_asset_pipeline_meta_enemies`** — enemy metadata parity with the web UI (optional tool; 500 if backend import fails).

## Tool selection (intent → tool)

| Intent | Tool |
|--------|------|
| Is the API up? | `blobert_asset_pipeline_health` |
| Run pipeline to completion (agent path) | `blobert_asset_pipeline_run_complete` |
| Is a run still going? | `blobert_asset_pipeline_run_status` |
| Stop run | `blobert_asset_pipeline_run_kill` |
| Read / mutate registry | `blobert_asset_pipeline_registry_*` (see frozen list below) |
| List / read / write jailed `.py` | `blobert_asset_pipeline_files_list`, `files_read`, `files_write` |
| List / fetch export assets | `blobert_asset_pipeline_assets_list`, `assets_get` |
| Enemy meta JSON | `blobert_asset_pipeline_meta_enemies` |

## Frozen MCP tool names (must match APMCP §MCP tool catalog)

Use these exact strings when invoking tools (copy from here or from the spec):

- `blobert_asset_pipeline_health`
- `blobert_asset_pipeline_run_complete`
- `blobert_asset_pipeline_run_status`
- `blobert_asset_pipeline_run_kill`
- `blobert_asset_pipeline_registry_get`
- `blobert_asset_pipeline_registry_patch_enemy_version`
- `blobert_asset_pipeline_registry_patch_player_active`
- `blobert_asset_pipeline_registry_load_existing_candidates`
- `blobert_asset_pipeline_registry_load_existing_open`
- `blobert_asset_pipeline_registry_put_enemy_slots`
- `blobert_asset_pipeline_registry_put_player_slots`
- `blobert_asset_pipeline_registry_sync_animated_exports`
- `blobert_asset_pipeline_registry_sync_player_exports`
- `blobert_asset_pipeline_registry_spawn_eligible`
- `blobert_asset_pipeline_registry_delete_enemy_version`
- `blobert_asset_pipeline_registry_delete_player_active`
- `blobert_asset_pipeline_files_list`
- `blobert_asset_pipeline_files_read`
- `blobert_asset_pipeline_files_write`
- `blobert_asset_pipeline_assets_list`
- `blobert_asset_pipeline_assets_get`
- `blobert_asset_pipeline_meta_enemies`

## Normative references (not duplicated here)

- **`project_board/specs/asset_pipeline_mcp_spec.md`** — HTTP mapping, query parameters, error codes, MRVC rules, log caps.
- **`asset_generation/mcp/README.md`** — Cursor/Claude MCP install, env, troubleshooting.
- **Package:** `asset_generation/python/src/blobert_asset_pipeline_mcp/`
