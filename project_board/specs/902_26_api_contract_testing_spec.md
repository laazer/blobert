# Spec: M902-26 — API Contract Testing (Asset Editor Backend)

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/26_api_contract_testing.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-26_api_contract_testing.md`

**Agent:** Spec Agent

**Date:** 2026-05-21

**Status:** SPECIFICATION

**Revision:** 1

**Spec exit gate type:** `api` (mutation-heavy registry/files/run routes; normative error and request-body contracts)

---

## Executive Summary

Add a **pytest + `jsonschema`** contract suite under `asset_generation/python/tests/api/` that exercises every public HTTP handler in `asset_generation/web/backend/routers/` plus `GET /api/health`. Each endpoint gets at least one **happy-path** and one **error-path** test. Response bodies are validated against JSON Schemas derived from the **live FastAPI OpenAPI document** (`app.openapi()`), with optional cross-check against the M902-24 committed cache `asset_generation/web/frontend/scripts/fixtures/openapi.cached.json`. Non-JSON routes (GLB, texture binaries) and **SSE** `/api/run/stream` use header/status and event-shape contracts defined here.

**In scope:** Shared OpenAPI→JSON Schema harness (`conftest.py` + `openapi_contract.py`), per-router test modules, direct `jsonschema` dev dependency, module docstrings + runbook section, CI via existing `ci/scripts/run_tests.sh` → `.lefthook/scripts/py-tests.sh`.

**Out of scope:** Frontend Zod contract tests (M902-25); regenerating TypeScript types (M902-24) except when implementation discovers live/cache drift; deleting or weakening `asset_generation/python/tests/web/test_registry_api.py` or `asset_generation/web/backend/tests/*`; business-logic assertions beyond schema-reasonable value checks.

**Prerequisites:** M902-24 COMPLETE (OpenAPI cache + `sync-api-types`). M902-25 COMPLETE (Pydantic `response_model` on three pilot GETs). FastAPI app importable from `asset_generation/python` dev extras (`fastapi`, `httpx`, `sse-starlette`).

---

## Assumptions and Ambiguity Resolutions

| # | Topic | Resolution | Confidence |
|---|--------|------------|------------|
| A1 | Test root path | All contract tests live under **`asset_generation/python/tests/api/`** (not repo-root `tests/api/`). Ticket AC name `test_registry_contract.py` is illustrative; normative layout is per-router modules below. | High |
| A2 | Schema authority order | **(1)** Live `app.openapi()` at pytest session start; **(2)** cache file for drift/staleness tests only. Hand-written schemas from ticket examples are **forbidden** as normative sources. | High |
| A3 | OpenAPI cache staleness | Committed `openapi.cached.json` may lag live app after M902-25; implementation MUST NOT fail solely because cache has `{}` for pilot routes. One adversarial test may assert live vs cache path keys match after regen. | High |
| A4 | `additionalProperties` strictness | **Tier A** (pilot + explicit Pydantic `response_model` / request bodies in OpenAPI): enforce `additionalProperties: false` when present in resolved schema. **Tier B** (legacy `JSONResponse`, empty OpenAPI `{}`): validate status, `Content-Type: application/json`, and minimal structural anchors (see Req 03). | High |
| A5 | Destructive DELETE | Registry DELETE endpoints have **no** confirmation UX; use **`api`** type only (not full destructive template). Error contract is standard FastAPI `detail`. | High |
| A6 | Run router side effects | Contract tests **mock** `process_manager` / subprocess for `/api/run/*` where needed; assert JSON/SSE shapes only, not pipeline exit codes from real Blender. | High |
| A7 | Registry filesystem | Use tmp `python_root` fixture pattern from `tests/web/test_registry_api.py` (`monkeypatch` `settings.python_root`). | High |
| A8 | Pre-commit | Lefthook pre-push inclusion is **recommended, not mandatory**; canonical gate is `py-tests.sh` via `run_tests.sh`. | High |
| A9 | `jsonschema` version | Pin **`jsonschema>=4.23,<5`** in `[project.optional-dependencies].dev` (exact pin in lockfile at implementation). | High |

---

## File Path Contract (Normative)

| Artifact | Path | Git policy |
|----------|------|------------|
| Spec (this document) | `project_board/specs/902_26_api_contract_testing_spec.md` | Committed |
| OpenAPI cache (read-only in tests) | `asset_generation/web/frontend/scripts/fixtures/openapi.cached.json` | Committed; regen via `npm run sync-api-types` when routes change |
| Live OpenAPI URL (reference) | `http://127.0.0.1:8000/openapi.json` | Not required in CI |
| Harness module | `asset_generation/python/tests/api/openapi_contract.py` | Committed |
| Shared fixtures | `asset_generation/python/tests/api/conftest.py` | Committed |
| Registry contracts | `asset_generation/python/tests/api/test_registry_contract.py` | Committed |
| Files contracts | `asset_generation/python/tests/api/test_files_contract.py` | Committed |
| Run contracts | `asset_generation/python/tests/api/test_run_contract.py` | Committed |
| Assets contracts | `asset_generation/python/tests/api/test_assets_contract.py` | Committed |
| Meta contracts | `asset_generation/python/tests/api/test_meta_contract.py` | Committed |
| Health contract | `asset_generation/python/tests/api/test_health_contract.py` | Committed |
| Runbook | `asset_generation/web/backend/AGENTS.md` § API contract tests | Committed (extend existing file) |
| Dev dependency | `asset_generation/python/pyproject.toml` `[project.optional-dependencies].dev` | Add `jsonschema` |
| ASGI precedent | `asset_generation/python/tests/web/test_registry_api.py` | Read-only reference |

---

## HTTP API Contract — Endpoint Freeze

All paths are prefixed as mounted in `main.py` (routers register under `/api/...`). **28 handlers** + app health = **29 contract targets**.

| # | Method | URI | Router | Response tier | Contract class |
|---|--------|-----|--------|---------------|----------------|
| 1 | GET | `/api/health` | `main.py` | A | JSON schema (OpenAPI `HealthResponse`) |
| 2 | GET | `/api/files` | `files.py` | B | JSON list tree |
| 3 | GET | `/api/files/{file_path}` | `files.py` | B | JSON `{path, content}` |
| 4 | PUT | `/api/files/{file_path}` | `files.py` | B | JSON + mutation body `FileWrite` |
| 5 | GET | `/api/registry/model/load_existing/candidates` | `registry.py` | B | JSON |
| 6 | POST | `/api/registry/model/load_existing/open` | `registry.py` | B | JSON + `LoadExistingOpenRequest` |
| 7 | GET | `/api/registry/model` | `registry.py` | A | `ModelRegistryResponse` |
| 8 | PATCH | `/api/registry/model/enemies/{family}/versions/{version_id}` | `registry.py` | B | JSON + `EnemyVersionPatch` |
| 9 | PATCH | `/api/registry/model/player_active_visual` | `registry.py` | B | JSON + body model |
| 10 | GET | `/api/registry/model/enemies/{family}/slots` | `registry.py` | B | JSON |
| 11 | POST | `/api/registry/model/enemies/{family}/sync_animated_exports` | `registry.py` | B | JSON |
| 12 | PUT | `/api/registry/model/enemies/{family}/slots` | `registry.py` | B | JSON + `EnemySlotsPut` |
| 13 | GET | `/api/registry/model/player/slots` | `registry.py` | B | JSON |
| 14 | PUT | `/api/registry/model/player/slots` | `registry.py` | B | JSON + body model |
| 15 | POST | `/api/registry/model/player/sync_player_exports` | `registry.py` | B | JSON |
| 16 | GET | `/api/registry/model/spawn_eligible/{family}` | `registry.py` | B | JSON |
| 17 | DELETE | `/api/registry/model/enemies/{family}/versions/{version_id}` | `registry.py` | B | JSON |
| 18 | DELETE | `/api/registry/model/player_active_visual` | `registry.py` | B | JSON |
| 19 | GET | `/api/run/stream` | `run.py` | SSE | Event contract (Req 08) |
| 20 | GET | `/api/run/complete` | `run.py` | B | JSON |
| 21 | POST | `/api/run/kill` | `run.py` | B | JSON |
| 22 | GET | `/api/run/status` | `run.py` | B | JSON |
| 23 | GET | `/api/assets` | `assets.py` | B | JSON |
| 24 | GET | `/api/assets/textures` | `assets.py` | B | JSON |
| 25 | GET | `/api/assets/textures/file/{file_path}` | `assets.py` | Binary | PNG bytes (Req 09) |
| 26 | GET | `/api/assets/{asset_path}` | `assets.py` | Binary | GLB/octet-stream (Req 09) |
| 27 | GET | `/api/meta/enemies` | `meta.py` | A | `MetaEnemiesResponse` |
| 28 | GET | `/api/meta/animations` | `meta.py` | B | JSON |

**Deferred boundary:** Migrating all routes to Tier A Pydantic models is a follow-up ticket. M902-26 enforces drift detection on current OpenAPI surface; tightening Tier B to full component schemas happens when models land.

---

## Validation Precedence

### OpenAPI schema resolution (harness)

| Order | Step | On failure |
|-------|------|------------|
| 1 | Load live spec: `spec = app.openapi()` | pytest session error (import/bootstrap) |
| 2 | Normalize path template: `/api/registry/model/enemies/{family}/versions/{version_id}` | KeyError → explicit test skip with message `operation not in OpenAPI` |
| 3 | Select `paths[path][method].responses[str(status)]` | Missing response → test asserts documented alternate status or `pytest.fail` |
| 4 | Resolve `content['application/json'].schema` including `$ref`, `allOf`, `anyOf`, `nullable` | Unresolvable ref → harness raises `OpenAPIResolutionError` |
| 5 | Apply Tier A/B policy (Req 03) | `jsonschema.ValidationError` fails test |
| 6 | Optional reasonable-value formats (`uuid`, `date-time`, `minLength: 1`) | ValidationError |

### HTTP request → response (per test)

| Order | Check | On failure |
|-------|--------|------------|
| 1 | Build request (query/body/path) per endpoint matrix | Setup error |
| 2 | `httpx.AsyncClient` + `ASGITransport(app=app)` | Transport error |
| 3 | Assert **expected status** (normative for that case) | `assert response.status_code == expected` |
| 4 | If JSON contract class: `response.json()` parseable | Fail if non-JSON body |
| 5 | `validate_response(response, method, path, status)` | `jsonschema.ValidationError` |
| 6 | If Tier A: assert no extra top-level keys vs schema (`additionalProperties: false`) | ValidationError |
| 7 | If binary/SSE class: Req 08/09 assertions only | — |

### Mutation request validation (client → server)

| Order | Check | On failure |
|-------|--------|------------|
| 1 | OpenAPI `requestBody` schema for operation | N/A for GET/DELETE without body |
| 2 | Send intentionally invalid body (malformed JSON, missing field, wrong type) | Expect **422** + `HTTPValidationError` unless matrix says **400** |
| 3 | Validate error body against error schema (Req 05) | ValidationError |

### CI execution

| Order | Command | On failure |
|-------|---------|------------|
| 1 | `cd asset_generation/python && uv run pytest tests/api/ -q` | Non-zero exit blocks merge |
| 2 | `timeout 300 ci/scripts/run_tests.sh` (includes py-tests) | Non-zero exit |

---

## Failure Taxonomy

### Success response status classes

| Class | Codes | Body |
|-------|-------|------|
| OK JSON | 200, 201 | `application/json` matching OpenAPI response schema (Tier A/B) |
| OK binary | 200 | `Content-Type` per route (`image/png`, `model/gltf-binary` or `application/octet-stream`) |
| OK SSE | 200 | `text/event-stream` per Req 08 |

### Error response status classes (normative)

| Code | When | JSON body schema | `detail` shape |
|------|------|------------------|----------------|
| **400** | Malformed domain payload, path guard, unknown run `cmd` (complete/kill), mixed load_existing identity | `ErrorDetail` | string |
| **403** | Path outside allowed dirs (files/assets) | `ErrorDetail` | string |
| **404** | Missing file, registry target, asset, `src/` root | `ErrorDetail` | string |
| **409** | Run already active (`/api/run/complete`) | `ErrorDetail` + optional extra keys allowed if in OpenAPI | object or string |
| **422** | FastAPI/Pydantic request validation | `HTTPValidationError` | `detail: ValidationError[]` |
| **500** | Registry manifest invalid, unhandled server error | `ErrorDetail` | string |
| **503** | Registry `ImportError` / unavailable | `ErrorDetail` | string |

### Error body JSON Schema anchors (from OpenAPI components)

```yaml
ErrorDetail:
  type: object
  required: [detail]
  properties:
    detail: { oneOf: [string, object, array] }
  additionalProperties: true   # FastAPI may add keys (e.g. run_id on 409)

HTTPValidationError:
  type: object
  required: [detail]
  properties:
    detail:
      type: array
      items: { $ref: '#/components/schemas/ValidationError' }
```

**Normative rule:** Every error-path contract test MUST assert `detail` key exists. For **422**, additionally validate against resolved `HTTPValidationError` schema from live OpenAPI. For **400/404/403/500/503**, validate `ErrorDetail` minimal anchor OR full response schema if OpenAPI documents that status for the operation.

### Harness failures (non-HTTP)

| Symptom | Meaning |
|---------|---------|
| `OpenAPIResolutionError` | Missing path/method/status or broken `$ref` |
| Live/cache path set mismatch | Staleness — regen `openapi.cached.json` |
| `jsonschema.ValidationError` | Contract drift |

---

## Mutation Request Schema Contracts

Normative request bodies for **POST / PUT / PATCH** (OpenAPI `requestBody.content.application/json.schema`). Tests MUST trigger validation failures against these shapes.

| Method | URI | OpenAPI / Pydantic model | Required fields (happy path) | Invalid-body triggers (error path) |
|--------|-----|--------------------------|------------------------------|-------------------------------------|
| PUT | `/api/files/{file_path}` | `FileWrite` | `content` (string) | `{}` → 422; `{"content": 1}` → 422 |
| POST | `/api/registry/model/load_existing/open` | `LoadExistingOpenRequest` | `kind` + identity per kind | mixed identity+path → **400**; missing `kind` → 422 |
| PATCH | `/api/registry/model/enemies/{family}/versions/{version_id}` | `EnemyVersionPatch` | ≥1 patch field | `{}` → **400** `provide at least one field` |
| PATCH | `/api/registry/model/player_active_visual` | body model in OpenAPI | per schema | empty patch → 400 |
| PUT | `/api/registry/model/enemies/{family}/slots` | `EnemySlotsPut` | `version_ids` array | wrong type → 422 |
| PUT | `/api/registry/model/player/slots` | player slots model | per schema | wrong type → 422 |
| POST | `/api/run/kill` | none or empty | — | N/A (no body) |

**Malformed JSON transport:** Send `Content-Type: application/json` with body `not-json{` → **422** `HTTPValidationError` (FastAPI parser).

**Extra request fields:** When OpenAPI model uses `extra="forbid"` (Pydantic v2), unknown keys → **422**. When handler accepts loose dict, spec documents **fail-open** (extra keys ignored) only if live OpenAPI does not list `additionalProperties: false`.

---

## Error Response Schema Contracts

### Global schemas (all routers)

| Schema | HTTP statuses | Validation |
|--------|---------------|------------|
| `HTTPValidationError` | 422 | Full schema from OpenAPI |
| `ErrorDetail` (`{detail: ...}`) | 400, 403, 404, 409, 500, 503 | `detail` required; type matches taxonomy row |

### Per-router error triggers (minimum one per endpoint)

| URI | Method | Error case | Expected status | Error schema |
|-----|--------|------------|-----------------|--------------|
| `/api/files/{file_path}` | GET | path `../../../etc/passwd` or nonexistent | 403 or 404 | ErrorDetail |
| `/api/files/{file_path}` | PUT | invalid body | 422 | HTTPValidationError |
| `/api/registry/model/load_existing/open` | POST | `{"kind":"enemy"}` only | 400 | ErrorDetail |
| `/api/registry/model/enemies/{family}/versions/{version_id}` | PATCH | empty body | 400 | ErrorDetail |
| `/api/registry/model/enemies/nope/versions/x` | DELETE | unknown family/version | 404 | ErrorDetail |
| `/api/run/complete` | GET | `cmd=not_a_command` | 400 | ErrorDetail |
| `/api/run/complete` | GET | `cmd=animated` while process running (mock) | 409 | ErrorDetail |
| `/api/assets/{asset_path}` | GET | path outside exports | 403 | ErrorDetail |
| `/api/assets/textures/file/{file_path}` | GET | missing texture | 404 | ErrorDetail |
| `/api/meta/enemies` | GET | mock ImportError (optional) | 503 or 200 fallback | per handler — document in test |

**Consistent `detail` rule (ticket AC):** All sampled error responses across routers MUST include `detail` key. String details MUST be non-empty for 400/404/403 unless OpenAPI documents empty string (none today).

---

## Requirement 01: OpenAPI Harness and Schema Authority

### 1. Spec Summary

- **Description:** Implement `load_live_spec()`, `load_cached_spec()`, `resolve_response_schema(spec, method, path, status_code)`, `resolve_request_schema(...)`, `validate_response(response, *, method, path, expected_status)`.
- **Constraints:** Use `jsonschema.Draft202012Validator` (or draft matching OpenAPI 3.1). Resolve `$ref` under `#/components/schemas/`. No network in default tests.
- **Assumptions:** `from main import app` after `sys.path` bootstrap identical to `test_registry_api.py`.
- **Scope:** `tests/api/openapi_contract.py`, `conftest.py`.

### 2. Acceptance Criteria

- **AC-01.1:** Session fixture loads live OpenAPI once; exposes resolver to tests.
- **AC-01.2:** Resolver returns dict suitable for `jsonschema.validate(instance, schema)`.
- **AC-01.3:** Supports `$ref`, inline schemas, `allOf` merge (single merged dict for validation).
- **AC-01.4:** `validate_response` asserts status before schema check.
- **AC-01.5:** Module docstring links to `openapi.cached.json` and `npm run sync-api-types`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Empty `{}` schemas in stale cache | False confidence | Live spec authoritative (A2) |
| `allOf` with conflicting properties | Validator errors | Harness merges conservatively; checkpoint if impossible |

### 4. Clarifying Questions

- None.

---

## Requirement 02: Tier A / Tier B Response Strictness

### 1. Spec Summary

- **Description:** **Tier A** — full JSON Schema validation + forbid extra properties when schema declares it. **Tier B** — status + JSON parse + required anchor keys from spec table or non-empty dict/list.
- **Constraints:** Do not duplicate M902-25 Pydantic/Zod drift tests; complement them with OpenAPI-derived schemas.
- **Assumptions:** Pilot routes resolve to component schemas in **live** OpenAPI post-M902-25.
- **Scope:** Harness policy flags per endpoint freeze table.

### 2. Acceptance Criteria

- **AC-02.1:** Tier A endpoints: `GET /api/health`, `GET /api/registry/model`, `GET /api/meta/enemies` validate against resolved `HealthResponse`, `ModelRegistryResponse`, `MetaEnemiesResponse`.
- **AC-02.2:** Tier A: `schema_version` integer ≥ 1 on registry; `status` literal `ok` on health.
- **AC-02.3:** Tier B: at minimum `assert isinstance(body, dict)` and `len(body) > 0` for 200 responses unless documented empty object allowed.
- **AC-02.4:** Where OpenAPI lists `additionalProperties: false`, extra keys in response fail validation.

### 3. Risk & Ambiguity Analysis

Legacy routes may never gain strict schemas; Tier B remains until follow-up.

### 4. Clarifying Questions

- None.

---

## Requirement 03: ASGI Client and Fixtures

### 1. Spec Summary

- **Description:** `conftest.py` provides `async_client`, `python_root` tmp fixture, optional `registry_manifest` seed, `mock_process_manager` for run routes.
- **Constraints:** `pytest-asyncio` auto mode; skip module if `pydantic_core` import fails (same as `test_registry_api.py`).
- **Assumptions:** No live server on port 8000 required.
- **Scope:** `tests/api/conftest.py`.

### 2. Acceptance Criteria

- **AC-03.1:** Client uses `httpx.AsyncClient` + `ASGITransport`.
- **AC-03.2:** `python_root` monkeypatches `core.config.settings.python_root`.
- **AC-03.3:** Run tests patch `process_manager.is_running` / `start` / `stream_output` where needed for deterministic SSE/complete.

### 3. Risk & Ambiguity Analysis

Flaky timing on stream tests if mocks incomplete.

### 4. Clarifying Questions

- None.

---

## Requirement 04: Registry Contract Tests

### 1. Spec Summary

- **Description:** `test_registry_contract.py` covers rows 5–18 in endpoint freeze; happy + error per handler.
- **Constraints:** Reuse patterns from `test_registry_api.py` for PATCH/DELETE happy paths.
- **Scope:** Registry router only.

### 2. Acceptance Criteria

- **AC-04.1:** Every registry endpoint has ≥1 happy and ≥1 error test.
- **AC-04.2:** `POST load_existing/open` tests 400 mixed-identity and 422 missing fields.
- **AC-04.3:** `GET model` happy path validates Tier A schema; optional uuid/format on known id fields when schema provides `format: uuid`.
- **AC-04.4:** DELETE unknown version returns 404 + `detail`.

### 3. Risk & Ambiguity Analysis

Filesystem-dependent routes need seeded `model_registry.json` for deterministic 200s.

### 4. Clarifying Questions

- None.

---

## Requirement 05: Files Contract Tests

### 1. Spec Summary

- **Description:** `test_files_contract.py` for list/read/write under tmp `python_root/src`.
- **Scope:** `files.py`.

### 2. Acceptance Criteria

- **AC-05.1:** Happy: list returns `tree` array; read returns `path` + `content`; write returns `saved: true`.
- **AC-05.2:** Error: read missing file → 404; write invalid body → 422 HTTPValidationError.
- **AC-05.3:** Path traversal attempt → 403 or 404 per handler.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 06: Run Contract Tests (JSON + SSE)

### 1. Spec Summary

- **Description:** `test_run_contract.py` for status, kill, complete, stream.
- **Scope:** `run.py`.

### 2. Acceptance Criteria

- **AC-06.1:** `GET /api/run/status` happy → 200 JSON with keys per OpenAPI or Tier B anchors (`running`, `run_id` or documented equivalents).
- **AC-06.2:** `GET /api/run/complete?cmd=invalid` → 400 + `detail`.
- **AC-06.3:** `POST /api/run/kill` when not running → documented status (200 or 404/409 per OpenAPI); test locks expected code in assertion.

### 3. Risk & Ambiguity Analysis

Without mocks, complete may spawn real subprocess — MUST mock.

### 4. Clarifying Questions

- None.

---

## Requirement 07: Assets Contract Tests (JSON + Binary)

### 1. Spec Summary

- **Description:** `test_assets_contract.py` — JSON list endpoints + binary contracts.
- **Scope:** `assets.py`.

### 2. Acceptance Criteria

- **AC-07.1:** `GET /api/assets` and `/api/assets/textures` happy → 200 JSON Tier B.
- **AC-07.2:** `GET /api/assets/{asset_path}` with missing export → 404; assert no `application/json` body required.
- **AC-07.3:** Binary success: assert `status == 200` and `Content-Type` contains `octet-stream` or `gltf`; body length `> 0` when fixture file exists.
- **AC-07.4:** Texture file 404 → ErrorDetail.

### 3. Risk & Ambiguity Analysis

GLB fixtures may be heavy; use minimal temp file under `python_root` exports.

### 4. Clarifying Questions

- None.

---

## Requirement 08: SSE Contract — `/api/run/stream`

### 1. Spec Summary

- **Description:** SSE endpoint uses **alternate contract** (not `jsonschema` on full response body).
- **Constraints:** Mock `_run_stream` generator or process_manager for deterministic events.
- **Assumptions:** `sse-starlette` yields `text/event-stream`.
- **Scope:** `test_run_contract.py`.

### 2. Acceptance Criteria

- **AC-08.1:** Happy (mocked short stream): status **200**; `Content-Type` contains `text/event-stream`.
- **AC-08.2:** Parse SSE `data:` lines as JSON; at least one event of type `log`, `done`, or `error` per implementation.
- **AC-08.3:** `event: done` → data object with `exit_code` (int).
- **AC-08.4:** `event: error` with `cmd=invalid_cmd` → data object with `exit_code` and `message` (string).
- **AC-08.5:** `event: log` → data object with `line` (string) and `run_id` when logs emitted.

**Normative event data schemas (documentation authority until OpenAPI adopts them):**

```json
{"exit_code": 0, "output_file": "<optional string>"}
{"exit_code": -1, "message": "<non-empty string>"}
{"line": "<string>", "run_id": "<string>"}
```

### 3. Risk & Ambiguity Analysis

Real pipeline streams are non-deterministic; mocks mandatory.

### 4. Clarifying Questions

- None.

---

## Requirement 09: Meta and Health Contract Tests

### 1. Spec Summary

- **Description:** `test_health_contract.py` (single endpoint); `test_meta_contract.py` for enemies + animations.
- **Scope:** `main.py`, `meta.py`.

### 2. Acceptance Criteria

- **AC-09.1:** Health 200 Tier A `{status: "ok"}`.
- **AC-09.2:** Meta enemies Tier A; assert `meta_backend` enum/key present per `MetaEnemiesResponse`.
- **AC-09.3:** Meta animations happy Tier B; error path if feasible (e.g. mock loader failure → 500).

### 3. Risk & Ambiguity Analysis

Meta imports Python modules; may skip on import failure with explicit pytest skip only when dev extras missing (not on contract failure).

### 4. Clarifying Questions

- None.

---

## Requirement 10: CI Integration and Dependencies

### 1. Spec Summary

- **Description:** Wire suite into canonical Python CI; add `jsonschema` dev dependency.
- **Constraints:** `py-tests.sh` runs `pytest tests/` — new `tests/api/` picked up automatically.
- **Scope:** `pyproject.toml`, evidence in checkpoint.

### 2. Acceptance Criteria

- **AC-10.1:** `jsonschema` in dev optional dependencies.
- **AC-10.2:** `uv run pytest tests/api/ -q` exits 0 after implementation.
- **AC-10.3:** `timeout 300 ci/scripts/run_tests.sh` includes contract tests (log excerpt in checkpoint).
- **AC-10.4:** Failure blocks merge (existing CI policy).

### 3. Risk & Ambiguity Analysis

diff-cover omits `tests/` from src threshold — no conflict expected.

### 4. Clarifying Questions

- None.

---

## Requirement 11: Documentation and Runbook

### 1. Spec Summary

- **Description:** Module docstring in `tests/api/__init__.py` or `conftest.py`; runbook section in backend `AGENTS.md`.
- **Scope:** Docs only; no new top-level README unless absent.

### 2. Acceptance Criteria

- **AC-11.1:** Docstring explains contract vs unit tests and points to OpenAPI authority.
- **AC-11.2:** Runbook steps: (1) add route in backend, (2) run `npm run sync-api-types`, (3) add happy+error tests, (4) run `uv run pytest tests/api/ -q`.
- **AC-11.3:** Link to `project_board/specs/902_26_api_contract_testing_spec.md` and M902-24/25 specs.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 12: Overlap Policy vs Existing Tests

### 1. Spec Summary

- **Description:** Contract tests assert **OpenAPI shapes**; existing tests assert **behavior** (disk writes, spawn eligibility logic).
- **Scope:** Relationship only.

### 2. Acceptance Criteria

- **AC-12.1:** Do not delete or weaken `tests/web/test_registry_api.py`.
- **AC-12.2:** Do not duplicate long behavioral chains in contract modules.
- **AC-12.3:** `backend/tests/test_response_models_pilot.py` remains complementary.

### 3. Risk & Ambiguity Analysis

Duplication if both assert same PATCH outcome — acceptable if contract test is schema-only.

### 4. Clarifying Questions

- None.

---

## Test Strategy (Test Designer)

| Layer | Approach |
|-------|----------|
| Harness unit | Minimal tests for `$ref` resolver with fixture OpenAPI fragment in `tests/api/test_openapi_contract_resolver.py` (optional, if not covered by integration) |
| Per endpoint | One test function per happy + one per error minimum; name pattern `test_<operation>_<happy|error>_contract` |
| Markers | None required; asyncio for all HTTP |
| Forbidden | Asserting markdown/ticket prose; snapshot of full OpenAPI in every test |
| Adversarial (Test Breaker) | Extra keys on Tier A response; stale cache vs live; unicode path segments; malformed JSON POST; concurrent PATCH |

**Red state before implementation:** Tests written to call harness; harness raises `NotImplementedError` or missing module until Implementation Agent completes Req 01.

---

## Acceptance Criteria Mapping (Ticket → Spec)

| Ticket AC | Spec | Verification |
|-----------|------|--------------|
| Contract tests under `tests/api/` | Req 01–09 paths | `tests/api/*.py` exist |
| All public endpoints happy + error | Endpoint freeze + Req 04–09 | pytest collection count ≥ 58 tests (2×29 min) |
| Status + JSON shape + no extra fields | Req 02, Failure taxonomy | jsonschema pass |
| Reasonable values | Req 02 AC-02.2, format validators | uuid/status checks |
| pytest + jsonschema + OpenAPI | Req 01, 10 | imports and live spec |
| Error 400/422 detail | Error Response Schema + Req 04–06 | error tests |
| Comment + runbook + link | Req 11 | file content |
| CI `run_tests.sh` | Req 10 | CI log |
| Pre-commit optional | A8 | documented |
| Baseline pass + deviations | Implementation checkpoint | `known_deviations` list |

---

## Deferred Boundary Statement

- **Not in M902-26:** Frontend contract tests; OpenAPI codegen for tests; confirming DELETE with body; replacing Tier B with Tier A for all routes; lefthook mandatory hook; `gate_registry.json` entry.
- **Follow-up:** Regenerate `openapi.cached.json` when live app OpenAPI changes; expand Pydantic `response_model` coverage.

---

## Risk & Ambiguity Analysis (Cross-Cutting)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Stale cached OpenAPI | High | Wrong Tier A expectations | Live authority (A2) |
| SSE flakiness | Medium | CI noise | Mocks (Req 03, 08) |
| Binary test size | Low | Slow CI | Minimal temp GLB |
| OpenAPI `{}` for legacy routes | High | Weaker contracts | Tier B anchors; tighten in follow-up |

---

## Clarifying Questions

- None — resolved in Assumptions A1–A9.

---

## Spec → Test Designer Handoff Notes

- Spec exit gate: `python ci/scripts/spec_completeness_check.py project_board/specs/902_26_api_contract_testing_spec.md --type api`
- Orchestrator transition: `python ci/scripts/run_workflow_transition_gates.py --ticket-id M902-26 --transition spec_to_test_design`
- Write failing tests first; cite requirement IDs in module docstrings (M902-26).
- Endpoint matrix and error triggers are normative for case selection.
