# Spec: Asset pipeline MCP tool catalog and agent-oriented HTTP API

**Ticket:** `project_board/23_milestone_23_asset_editor_pipeline_mcp/done/01_spec_asset_pipeline_mcp_and_agent_http_api.md`  
**Milestone:** `project_board/23_milestone_23_asset_editor_pipeline_mcp/README.md` (Milestone 23 — Asset Editor Pipeline MCP)  
**Spec path (stable):** `project_board/specs/asset_pipeline_mcp_spec.md`  
**Spec ID prefix:** APMCP  
**Date:** 2026-04-13  
**Last Updated By:** Spec revision (FastMCP stack for ticket `03`)

---

## Overview

This document is the **normative contract** for how **coding agents** interact with the Blobert **asset generation loop** through:

1. **MCP tools** (stdio server in ticket `03`) that perform **HTTP-only** calls to the existing **FastAPI** app (`asset_generation/web/backend`, default `http://127.0.0.1:8000`).
2. An **agent-oriented run completion** HTTP surface (implemented in ticket `02`) that complements the **SSE** endpoint `/api/run/stream` used by the M21 editor.

**Design goals**

- **Completion-oriented** responses: one JSON object with `exit_code`, bounded log text, and `output_file` hint when successful — no mandatory SSE parsing for agents.
- **Parity** with the editor: same validation, allowlists, path jail, and `process_manager` single-flight rules as today’s routers.
- **Frozen tool names** for downstream tickets `02`–`04`, `06` (MCP implementation, docs, agent skill).

**MCP server implementation (ticket `03`)**

When the in-repo server is implemented in **Python**, it **MUST** use **[FastMCP](https://github.com/PrefectHQ/fastmcp)** (`fastmcp` on PyPI): stdio transport (default), `@mcp.tool` functions that call `httpx` (or equivalent) against `BLOBERT_ASSET_API_BASE`, and no shell tools. This matches the repo’s **`uv`** workflow, avoids hand-rolled JSON-RPC, and keeps tool schemas aligned with type hints. A TypeScript MCP server remains **out of scope** for milestone 23 unless a future ticket explicitly revises ADR-APMCP-003.

**Related specifications**

| Spec ID | Path | Relationship |
|--------|------|----------------|
| MRVC | `project_board/specs/model_registry_draft_versions_spec.md` | Registry paths, draft vs in-use, allowlist roots — **MCP registry tools MUST NOT weaken or bypass** FastAPI checks that enforce MRVC. |
| ARGLB | `project_board/specs/assets_router_and_glb_viewer_spec.md` | List/serve asset roots under `python_root`; MCP `assets_*` tools map here. |

**Out of scope**

- Godot runtime / game control MCP (milestone 22).
- Replacing the React editor or MRVC semantics.
- Arbitrary shell execution from MCP tools.

---

## Traceability (ticket acceptance criteria)

| Ticket AC | Spec coverage |
|-----------|----------------|
| Spec under `project_board/specs/` with **APMCP** prefix | This document |
| **Security** threat model | §Threat model |
| MRVC alignment / no bypass of `_ALLOWLIST_PREFIXES` and normalization | §MRVC and registry path enforcement |
| **Run API** parity with `/api/run/stream` query params | §APMCP-RUN — Agent run completion API, §Endpoint freeze |
| Downstream `02`–`04`, `06` implement without contract churn | §MCP tool catalog (frozen names), §Downstream tickets |

---

## Threat model

**Trust boundaries**

- **Operator machine:** Human runs `task editor` / `asset_generation/web/start.sh`; FastAPI binds per deployment config (default local dev: localhost).
- **Agent + MCP process:** Assumed same user session as the operator; MCP server MUST call **only** the configured base URL (e.g. `127.0.0.1:8000`) and MUST NOT expose tools that execute shell commands or open arbitrary URLs.

**Assets**

- **model_registry.json** and exported GLBs under `asset_generation/python/` — integrity and allowlist enforcement are security-relevant for supply-chain and path traversal.

**Threats and mitigations**

| Threat | Mitigation |
|--------|------------|
| Exposing the API beyond localhost in dev | Bind to loopback by default; document that LAN exposure requires explicit operator choice and network controls. |
| Unauthenticated agent on shared machine | Optional **shared secret** header (implementation in backend + MCP; name e.g. `BLOBERT_ASSET_API_TOKEN` / `X-Blobert-Asset-Token`) — when set, all mutating or sensitive routes SHOULD require it; exact routes in ticket `02`/`03`. |
| **Shell injection** via MCP | **Forbidden:** no `run_terminal_cmd`-style tools in the asset-pipeline MCP. Run jobs only through **`/api/run/*`** (subprocess construction stays inside `routers/run.py`). |
| **Path traversal** or registry escape | **Delegated** to existing routers: `routers/files.py` + `core/path_guard.resolve_src_path` for `.py` under `python_root/src`; `routers/registry.py` `_normalize_registry_relative_glb_path` + `_ALLOWLIST_PREFIXES`; `routers/assets.py` export dir allowlist. MCP tools MUST NOT rewrite paths client-side to skip these checks. |
| **SSE parsing bugs** in agents | Agents SHOULD use **`blobert_asset_pipeline_run_complete`** → completion HTTP API, not SSE, for run results. |

**Residual risk**

- Any operator who disables path checks or runs an outdated backend bypasses this spec; compliance is **tested at the HTTP layer** in milestone tickets.

---

## MRVC and registry path enforcement

**Normative rule (APMCP-REG-1):** Any MCP tool that reads or mutates the visual registry MUST use the **published** `/api/registry/*` endpoints. Implementations MUST NOT:

- Write `model_registry.json` directly from the MCP process.
- Accept GLB paths that would be rejected by `routers/registry.py` (including `_ALLOWLIST_PREFIXES` at lines 20–25 and `_normalize_registry_relative_glb_path` in the same module).

**Alignment with MRVC:** Tool behavior MUST respect MRVC-3 allowlist roots (`animated_exports/`, `exports/`, `player_exports/`, `level_exports/`), traversal bans, and `.glb` extension rules as enforced by the backend today.

---

## Endpoint freeze

**Existing routes (authoritative as of spec date)** — MCP tools wrap these without semantic change.

| Method | URI | Purpose |
|--------|-----|---------|
| GET | `/api/health` | Liveness |
| GET | `/api/run/stream` | **Human/editor:** SSE log stream + `done` / `error` events (retained; not agent-primary) |
| POST | `/api/run/kill` | Kill current subprocess |
| GET | `/api/run/status` | `{ is_running, run_id }` |
| GET | `/api/files` | List `.py` tree under `python_root/src` |
| GET | `/api/files/{path}` | Read jailed source file |
| PUT | `/api/files/{path}` | Write jailed source file |
| GET | `/api/assets` | List GLB/JSON assets under export dirs (+ `draft/` subtrees) |
| GET | `/api/assets/{path}` | Serve asset file |
| GET+ | `/api/registry/...` | Registry read/patch/delete/sync/slots/load_existing/spawn_eligible (full set in tool catalog) |
| GET | `/api/meta/enemies` | Enemy metadata / build hints (optional for agents) |

**Frozen agent completion run route (ticket `02`)**

| Method | URI | Purpose |
|--------|-----|---------|
| GET | `/api/run/complete` | **Agent-primary:** start run (or join wait), return **one JSON** result when finished or on timeout/poll handoff per APMCP-RUN |

*Note:* If ticket `02` chooses `POST /api/run/complete` for implementation convenience, update this table and bump spec **Last Updated** — until then, **`GET`** is the normative contract for query-param parity with `/api/run/stream`.

---

## Validation precedence

Applies to **run completion** (`/api/run/complete`) and reiterates ordering for tools that touch runs:

| Order | Check | Typical HTTP outcome |
|-------|--------|----------------------|
| 1 | HTTP method + route registered | 404 if not found |
| 2 | `cmd` ∈ allowed set (`animated`, `player`, `level`, `smart`, `stats`, `test`) | 400 JSON body if unknown cmd |
| 3 | `process_manager` single-flight: no second run while one is active | **409 Conflict** with JSON `{"detail", "run_id"}` (frozen; 429 not used for this case) |
| 4 | Query/body parameter validation (types, mutual constraints) | 422 or 400 per FastAPI |
| 5 | Subprocess start failures | **200** with `exit_code: -1`, `message`, null `run_id` (matches SSE error shape) |
| 6 | Max wait exceeded while subprocess still running | **504** with partial `log_text`, `timed_out: true`, `run_id`; subprocess continues draining in the background until exit (stdout back-pressure avoided) |

Registry and files endpoints keep their **existing** FastAPI validation order (path normalization before business logic); MCP tools MUST NOT reorder checks client-side.

---

## Failure taxonomy

| Status | Meaning | Examples |
|--------|---------|----------|
| 200 | Success (HTTP OK); run completion MAY embed `exit_code != 0` in JSON | Run finished with Blender error |
| 202 | Accepted — async / poll continuation | Max wait exceeded, body includes `run_id` |
| 400 | Malformed query/body | Unknown `cmd`, invalid parameter |
| 403 | Forbidden path class | Registry path outside allowlist |
| 404 | Missing resource | File not under jail, missing GLB |
| 409 | Conflict | Run already active (completion endpoint start) |
| 429 | Conflict / rate-like guard | Alternative to 409 for single-flight (pick one) |
| 422 | Unprocessable entity | Pydantic validation |
| 500 | Unexpected server error | Uncaught exception |
| 504 | Gateway timeout | Server-side max wait exceeded without 202 handoff |

---

## APMCP-RUN — Agent run completion API

**APMCP-RUN-1 — Query parameter parity**

`/api/run/complete` MUST accept the **same query parameters** as `GET /api/run/stream` (see `asset_generation/web/backend/routers/run.py`, `run_stream` query parameters):

- `cmd` (required)
- `enemy` (optional)
- `count` (optional)
- `description` (optional)
- `difficulty` (optional)
- `finish` (optional)
- `hex_color` (optional)
- `build_options` (optional string; forwarded as `BLOBERT_BUILD_OPTIONS_JSON` in subprocess env)
- `output_draft` (optional bool; forwarded as draft export subdir semantics)
- `replace_variant_index` (optional int 0–99; pins `BLOBERT_EXPORT_START_INDEX` so the run overwrites that variant instead of allocating the next free index — UI “Regenerate”)

**No deliberate subset** unless a revision of this spec documents rationale and updates contract tests.

**APMCP-RUN-2 — Behavioral parity**

Command construction, `PYTHONPATH`, `BLOBERT_EXPORT_START_INDEX`, `BLOBERT_EXPORT_USE_DRAFT_SUBDIR`, and post-run registry sync for `animated` MUST match `_run_stream` behavior in `routers/run.py` (ticket `02` shares implementation helpers; no duplicate divergent logic).

**APMCP-RUN-3 — Response body (success path)**

JSON object including at minimum:

- `exit_code`: integer (or `null` when **504** timeout response before process exit)
- `log_text`: string — stdout/stderr aggregate **bounded** by **262_144** UTF-8 bytes (`Settings.run_complete_max_log_bytes`); if over limit, response uses a **tail-only** truncation with prefix `…` + `[log truncated — tail only]`
- `output_file`: string or null — same relative path semantics as SSE `done` event (`_guess_output_file` logic); null when `exit_code != 0`
- `run_id`: string or null — correlation id; always set when the subprocess was started (including 504 timeout responses)

**APMCP-RUN-4 — SSE preservation**

`/api/run/stream` MUST remain available and behaviorally unchanged for the M21 UI. Automated coverage targets `/api/run/complete`; operators should still smoke an `animated` run via the editor locally after backend changes.

**APMCP-RUN-5 — Timeouts**

- Query parameter **`max_wait_ms`** (optional, ≥ 1): wall-clock wait for the subprocess to finish; defaults to `Settings.run_complete_default_max_wait_ms` (1 hour). Values are clamped to `Settings.run_complete_absolute_max_wait_ms`.
- When exceeded: **504** per §Validation precedence row 6 (no 202 poll handoff in v1).

**APMCP-RUN-6 — Idempotency**

Starting a run is **not idempotent** (side effects: exports, registry sync). Re-POST/duplicate GET with same params may create additional variants; agents SHOULD use explicit `count` and draft flags. `GET /api/run/status` and `POST /api/run/kill` are read/control helpers (kill is side-effecting; not idempotent).

---

## MCP tool catalog

**Naming:** Tools below are **normative** for ticket `03` (MCP server) and **MUST** be referenced by ticket `06` (agent skill). Parameter columns describe the MCP tool surface; HTTP mapping shows the underlying call.

| MCP tool name | Purpose | HTTP method + path | Required parameters | Optional parameters | Success shape (summary) | Error / notes | Idempotency |
|---------------|---------|--------------------|----------------------|----------------------|-------------------------|---------------|-------------|
| `blobert_asset_pipeline_health` | Verify API up | GET `/api/health` | none | none | `{ "status": "ok" }` | Connection errors from MCP | Safe / repeatable |
| `blobert_asset_pipeline_run_complete` | Run pipeline to completion | GET `/api/run/complete` | `cmd` | `enemy`, `count`, `description`, `difficulty`, `finish`, `hex_color`, `build_options`, `output_draft`, `max_wait_ms` | APMCP-RUN-3 body | **409** if run already active; **504** + `timed_out` if `max_wait_ms` exceeded; **400** unknown `cmd` | **Not** idempotent |
| `blobert_asset_pipeline_run_status` | Poll run state | GET `/api/run/status` | none | none | `{ is_running, run_id }` | n/a | Read-only |
| `blobert_asset_pipeline_run_kill` | Stop current run | POST `/api/run/kill` | none | none | `{ killed, message }` | n/a | Side effect |
| `blobert_asset_pipeline_registry_get` | Read full manifest | GET `/api/registry/model` | none | none | Registry JSON | 500 parse errors | Read-only |
| `blobert_asset_pipeline_registry_patch_enemy_version` | Patch enemy version row | PATCH `/api/registry/model/enemies/{family}/versions/{version_id}` | `family`, `version_id`, body fields per OpenAPI | none | Updated registry fragment | 403 path; 404 missing | Mutating |
| `blobert_asset_pipeline_registry_patch_player_active` | Set/patch player active visual | PATCH `/api/registry/model/player_active_visual` | body per OpenAPI | none | Updated fragment | 403 / validation | Mutating |
| `blobert_asset_pipeline_registry_load_existing_candidates` | List load-existing candidates | GET `/api/registry/model/load_existing/candidates` | none | query per OpenAPI | Candidate list JSON | 403 | Read-only |
| `blobert_asset_pipeline_registry_load_existing_open` | Open existing into registry | POST `/api/registry/model/load_existing/open` | body per OpenAPI | none | Result JSON | 403 / 404 | Mutating |
| `blobert_asset_pipeline_registry_put_enemy_slots` | Replace enemy slot ordering | PUT `/api/registry/model/enemies/{family}/slots` | `family`, body | none | Slots JSON | 403 | Mutating |
| `blobert_asset_pipeline_registry_put_player_slots` | Replace player slots | PUT `/api/registry/model/player/slots` | body | none | Slots JSON | 403 | Mutating |
| `blobert_asset_pipeline_registry_sync_animated_exports` | Scan disk → registry for family | POST `/api/registry/model/enemies/{family}/sync_animated_exports` | `family` | none | Sync result | 403 | Side effect |
| `blobert_asset_pipeline_registry_sync_player_exports` | Scan player exports | POST `/api/registry/model/player/sync_player_exports` | none | none | Sync result | 403 | Side effect |
| `blobert_asset_pipeline_registry_spawn_eligible` | Query spawn-eligible paths | GET `/api/registry/model/spawn_eligible/{family}` | `family` | none | Paths JSON | 404 / empty | Read-only |
| `blobert_asset_pipeline_registry_delete_enemy_version` | Delete enemy version | DELETE `/api/registry/model/enemies/{family}/versions/{version_id}` | `family`, `version_id`, confirmation body | none | Per MRVC delete matrix | 403/404/409 | Destructive |
| `blobert_asset_pipeline_registry_delete_player_active` | Clear player active | DELETE `/api/registry/model/player_active_visual` | body per OpenAPI | none | Result | 403 | Destructive |
| `blobert_asset_pipeline_files_list` | List editable `.py` tree | GET `/api/files` | none | none | `{ tree: [...] }` | 404 if no src | Read-only |
| `blobert_asset_pipeline_files_read` | Read one source file | GET `/api/files/{path}` | `path` | none | `{ path, content }` | 404 | Read-only |
| `blobert_asset_pipeline_files_write` | Write one source file | PUT `/api/files/{path}` | `path`, `content` | none | `{ path, saved }` | 404 parent / jail | Mutating |
| `blobert_asset_pipeline_assets_list` | List export assets | GET `/api/assets` | none | none | `{ assets: [...] }` | n/a | Read-only |
| `blobert_asset_pipeline_assets_get` | Fetch GLB/JSON bytes | GET `/api/assets/{path}` | `path` | none | Binary / JSON | 404 | Read-only |
| `blobert_asset_pipeline_meta_enemies` *(optional)* | Enemy metadata for UI parity | GET `/api/meta/enemies` | none | none | JSON metadata | import errors → 500 | Read-only |

**SSE escape hatch:** `blobert_asset_pipeline_run_stream_subscribe` is **not** required; agents MUST prefer `blobert_asset_pipeline_run_complete`. If a future ticket adds SSE subscription as an optional tool, it MUST be named distinctly and documented as non-normative for automation.

---

## Configuration (MCP server and agents)

| Variable | Meaning | Default |
|----------|---------|---------|
| `BLOBERT_ASSET_API_BASE` | Origin for HTTP calls | `http://127.0.0.1:8000` |
| `BLOBERT_ASSET_API_TOKEN` | Optional shared secret | unset |

---

## Downstream tickets

| Ticket | Responsibility |
|--------|----------------|
| `02_backend_blocking_or_polled_run_endpoint.md` | Implement `/api/run/complete` per APMCP-RUN; pytest coverage; OpenAPI |
| `03_mcp_stdio_server_wrapping_asset_editor_api.md` | Implement tools in §MCP tool catalog using **FastMCP** (Python + stdio) |
| `04_documentation_cursor_and_claude_mcp_setup.md` | Operator docs + MCP config examples |
| `05_backlog_optional_glb_validation_or_preview_hooks.md` | Stretch — optional tools |
| `06_agent_skill_blobert_asset_pipeline_mcp.md` | Skill references **frozen tool names** in this spec |

---

## Architecture Decision Records

### ADR-APMCP-001 — HTTP-only MCP, no parallel registry client

- **Decision:** MCP tools are thin HTTP clients; no second registry writer.
- **Rationale:** Single validation path preserves MRVC guarantees and reduces desync bugs.

### ADR-APMCP-002 — Completion endpoint vs SSE

- **Decision:** Agents use `/api/run/complete`; humans keep `/api/run/stream`.
- **Rationale:** SSE is awkward for LLM clients; completion JSON is testable and log-friendly.

### ADR-APMCP-003 — FastMCP for the stdio MCP process

- **Decision:** The asset-pipeline MCP server (ticket `03`) is implemented in Python with **FastMCP**, dependencies managed via **`uv`** (same ecosystem as `asset_generation/python`), stdio transport for Cursor/Claude.
- **Rationale:** Less protocol boilerplate than raw MCP SDK usage; async-friendly tools with `httpx`; widely documented; keeps one language for HTTP client + MCP wrapper.
- **Rejected alternative:** Ad-hoc stdio JSON-RPC or a separate Node MCP package — higher maintenance and duplicated HTTP client patterns for this repo.

---

## Requirement APMCP-1 — Contract stability

### 1. Spec summary

Tool names and HTTP mappings in §MCP tool catalog are **frozen** for milestone 23 unless this file is revised with **Date** and **Last Updated By** and downstream tickets are revalidated.

### 2. Acceptance criteria

- **APMCP-1.1:** Ticket `06` skill lists the same tool names as §MCP tool catalog for required flows.
- **APMCP-1.2:** Ticket `03` implements at minimum: health, run_complete, run_status, registry_get, files_read, files_write per milestone AC.
