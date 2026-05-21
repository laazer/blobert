# Spec: M902-25 — Pydantic + Zod Dual Validation (Asset Editor API Pilot)

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/25_pydantic_zod_dual_validation.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-25_pydantic_zod_dual_validation.md`

**Agent:** Spec Agent

**Date:** 2026-05-21

**Status:** SPECIFICATION

**Revision:** 1

**Spec exit gate type:** `api` (read GET response contracts; runtime validation at HTTP boundaries)

---

## Executive Summary

Introduce **dual runtime validation** on three pilot GET endpoints: backend returns Pydantic `response_model` instances; frontend parses JSON with **Zod** via a shared **`api-client.ts`**. Manual mirror between Python and TypeScript until codegen is deferred. **Compile-time** types remain in `src/api.types.ts` (M902-24); **runtime** enforcement is Zod + Pydantic.

**In scope:** `GET /api/health`, `GET /api/registry/model`, `GET /api/meta/enemies`; backend `models/responses/`; frontend `schemas.ts`, `api-client.ts`, drift fixtures, user-safe Zod error UX; pilot component wiring; README sync checklist.

**Out of scope:** Remaining `JSONResponse` routes (~25); Pydantic→Zod codegen; deleting `src/types/index.ts`; migrating non-pilot `client.ts` functions; request-body validation changes on PATCH/POST routes.

**Prerequisites:** M902-24 complete (`api.types.ts`, `sync-api-types.sh`). FastAPI OpenAPI at `/openapi.json`. Vitest + backend pytest.

---

## Assumptions and Ambiguity Resolutions

| # | Topic | Resolution | Confidence |
|---|--------|------------|------------|
| A1 | Ticket AC “100% runtime coverage” | **Deferred** to follow-up ticket; this ticket delivers pattern + 3 pilots only. | High |
| A2 | Registry shape authority | Wire JSON matches `load_effective_manifest` / `validate_manifest` in `asset_generation/python/src/model_registry/schema.py`. Backend Pydantic models align with `blobert_asset_gen/api_schemas/manifest.py` field names. | High |
| A3 | JSON key casing | **snake_case** on the wire for all pilot responses. Zod schemas use snake_case keys. `client.ts` may map meta response to camelCase **after** Zod validation (compatibility layer). | High |
| A4 | Zod version | Pin **`zod@3.24.2`** exact in `dependencies` (runtime; used in bundle). | High |
| A5 | Strict unknown keys | Zod: **`.strict()`** on all pilot object schemas (fail-closed). Pydantic v2: `model_config = ConfigDict(extra="forbid")` on response models. | High |
| A6 | Backend model location | New modules under `asset_generation/web/backend/models/responses/`; may duplicate manifest nested types locally (no required import of `blobert_asset_gen` from web backend). | High |
| A7 | Invalid handler-internal data | If service returns dict that fails `ModelRegistryResponse.model_validate`, handler raises before HTTP 200 (500 or re-raise `ValueError` per existing registry error mapping). | High |
| A8 | HTTP error responses | **4xx/5xx bodies are not Zod-validated** in pilot; `api-client` throws `ApiHttpError` with status + body text only. | High |
| A9 | Drift tests | Shared JSON fixtures under `asset_generation/web/frontend/scripts/fixtures/dual_validation/`; pytest uses Pydantic `model_validate`; Vitest uses Zod `.parse`. | High |
| A10 | OpenAPI regen | After backend `response_model` lands, run `npm run sync-api-types` and commit `api.types.ts` + `openapi.cached.json`. | High |

---

## File Path Contract (Normative)

| Artifact | Path | Git policy |
|----------|------|------------|
| Spec (this document) | `project_board/specs/902_25_pydantic_zod_validation_spec.md` | Committed |
| Backend response models | `asset_generation/web/backend/models/responses/{health,registry,meta}.py` | Committed |
| Backend package init | `asset_generation/web/backend/models/__init__.py`, `models/responses/__init__.py` | Committed |
| Route edits | `main.py`, `routers/registry.py`, `routers/meta.py` | Committed |
| Zod schemas | `asset_generation/web/frontend/src/schemas.ts` | Committed |
| Validated client | `asset_generation/web/frontend/src/api-client.ts` | Committed |
| Health wrapper | `asset_generation/web/frontend/src/api/healthCheck.ts` | Re-export from api-client |
| Legacy client | `asset_generation/web/frontend/src/api/client.ts` | Pilot functions delegate; non-pilot unchanged |
| Drift fixtures | `asset_generation/web/frontend/scripts/fixtures/dual_validation/*.json` | Committed |
| Backend drift tests | `asset_generation/web/backend/tests/test_response_models_pilot.py` | Committed |
| Frontend drift tests | `asset_generation/web/frontend/src/schemas.pilot.test.ts` and/or `src/api-client.pilot.test.ts` | Committed |
| README addition | `asset_generation/web/frontend/README.md` § Dual validation | Committed |
| Compile-time types | `asset_generation/web/frontend/src/api.types.ts` | Regen when OpenAPI changes |

---

## HTTP API Contract — Endpoint Freeze

Pilot endpoints only. Full route inventory for follow-up is in **Requirement 12**.

| Method | URI | Handler (current) | Response model (new) | 200 JSON content-type |
|--------|-----|-------------------|----------------------|------------------------|
| GET | `/api/health` | `main.health` | `HealthResponse` | `application/json` |
| GET | `/api/registry/model` | `registry.get_model_registry` | `ModelRegistryResponse` | `application/json` |
| GET | `/api/meta/enemies` | `meta.get_enemies` | `MetaEnemiesResponse` | `application/json` |

**Unchanged for pilots:** Path prefixes, query params (none), auth (none), CORS, existing `HTTPException` status codes on registry/meta failure paths.

**OpenAPI:** After implementation, `/openapi.json` must expose component schemas for the three response models (not `unknown` for 200 bodies).

---

## Validation Precedence

### Backend (response construction)

| Order | Check | On failure |
|-------|--------|------------|
| 1 | Service / loader returns `dict` (registry) or constructs meta payload | Existing `HTTPException` / `map_exception_to_http` (unchanged) |
| 2 | `ResponseModel.model_validate(data)` or constructor with validated nested models | Uncaught `ValidationError` → FastAPI **500** (implementation must validate before return; tests assert no 200 with invalid model) |
| 3 | FastAPI `response_model` serialization | N/A on success path |
| 4 | Client receives JSON | — |

**Registry route:** Call `ModelRegistryResponse.model_validate(reg.load_effective_manifest(...))` (or equivalent) **before** returning; do not return raw dict through `JSONResponse`.

**Meta route:** Build `MetaEnemiesResponse(...)` explicitly for both `meta_backend: ok` and `fallback` branches.

**Health route:** Return `HealthResponse(status="ok")` instance.

### Frontend (response consumption)

| Order | Check | On failure |
|-------|--------|------------|
| 1 | `fetch(url)` network | Throw `Error` with message containing `network` or propagate (Vitest may mock) |
| 2 | `response.ok` | Throw `ApiHttpError` (status, optional body snippet); **no Zod parse** |
| 3 | `response.json()` | Throw `ApiHttpError` or `Error` `invalid JSON` if body not JSON object/array |
| 4 | `schema.parse(data)` (Zod strict) | Throw `ApiValidationError` with user-safe `message` + `cause: ZodError` for logging |
| 5 | Optional camelCase map (meta only) | TypeScript-only; must not widen validated fields |

### Cross-layer drift

| Order | Check | On failure |
|-------|--------|------------|
| 1 | Fixture JSON file exists | Test setup error |
| 2 | Pydantic `model_validate` (pytest) | Assertion / pytest failure |
| 3 | Zod `.parse` (Vitest) | Assertion failure |
| 4 | `api.types.ts` path types (manual / optional test) | Documented in README; not blocking drift test if OpenAPI still `unknown` until regen |

---

## Failure Taxonomy

### Backend HTTP (unchanged semantics for pilots)

| Condition | Status | Body shape | Zod on client? |
|-----------|--------|------------|----------------|
| Registry `ValueError` from loader | 500 | `{"detail": "<str>"}` | No |
| Registry `ImportError` | 503 | `{"detail": "registry unavailable: ..."}` | No |
| Meta ImportError (fallback path) | 200 | Valid `MetaEnemiesResponse` with `meta_backend: "fallback"` | Yes — must parse |
| Uncaught Pydantic `ValidationError` in handler | 500 | FastAPI default | No |
| Health success | 200 | `{"status":"ok"}` | Yes |

### Frontend error classes (new — normative)

| Class | When | `message` (user-facing) | Logged fields |
|-------|------|-------------------------|---------------|
| `ApiHttpError` | `!response.ok` | `The editor could not reach the server (HTTP <status>).` | `status`, `url`, first 200 chars of body |
| `ApiValidationError` | Zod `.parse` fails | `The server returned unexpected data. Try refreshing the page or restarting the asset editor.` | `url`, `zodError.issues` (structured), **not** shown in UI |
| Generic `Error` | JSON parse fail | `The server returned a response that could not be read.` | `url`, parse error |

**UI rule:** Components catch `ApiValidationError` and show `error.message` only (e.g. toast / inline banner). **Forbidden:** `JSON.stringify(zodError)`, `error.issues` in DOM, or raw stack in production UI.

**Console rule:** `console.error("[api-client]", url, zodError)` or equivalent **once** per failure in `api-client.ts`.

---

## Deferred Boundary Statement

- **Not in M902-25:** All non-pilot routes returning `JSONResponse`; PATCH/POST response `response_model`; Zod on request bodies; auto codegen Pydantic→Zod; removal of `src/types/index.ts`; changing meta Python introspection logic.
- **Follow-up:** Ticket “M902-25b” or M902-26 — roll `response_model` + Zod to remaining routes using pilot templates (see Requirement 12).
- **Ticket AC partial:** “All API response types use Pydantic” → satisfied for **3** routes only; AC gatekeeper documents deferral with spec § Requirement 12 table.

---

## Requirement 01: Backend Module Layout

### 1. Spec Summary

- **Description:** Create `asset_generation/web/backend/models/responses/` with three modules and re-exports.

```
models/
├── __init__.py
└── responses/
    ├── __init__.py   # HealthResponse, ModelRegistryResponse, MetaEnemiesResponse, nested types
    ├── health.py
    ├── registry.py   # VersionRowResponse, FamilyBlockResponse, PlayerActiveVisualResponse, ModelRegistryResponse
    └── meta.py       # EnemyMetaRowResponse, MetaEnemiesResponse, AnimatedBuildControlDef models
```

- **Constraints:** Routers import response types from `models.responses` only for pilot returns. Request models (`EnemyVersionPatch`, etc.) stay in `routers/registry.py` unless moved in a later ticket.
- **Assumptions:** Pydantic v2 (`BaseModel`, `Field`, `ConfigDict`).
- **Scope:** New files + `__init__.py` exports.

### 2. Acceptance Criteria

- **AC-01.1:** `from models.responses import HealthResponse, ModelRegistryResponse, MetaEnemiesResponse` succeeds.
- **AC-01.2:** Each public model has `Field(..., description=...)` on every field and a one-line class docstring.
- **AC-01.3:** All response models set `extra="forbid"`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Circular imports registry ↔ meta | Build break | Keep meta control-def models self-contained in `meta.py` |

### 4. Clarifying Questions

- None.

---

## Requirement 02: `GET /api/health` — `HealthResponse`

### 1. Spec Summary

- **Description:** Replace dict return with typed model.

**Pydantic (`models/responses/health.py`):**

```python
class HealthResponse(BaseModel):
    """Liveness probe for the asset editor API."""
    status: Literal["ok"] = Field(..., description="Health status; only ok is defined.")
```

**Route (`main.py`):**

```python
@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
```

- **Wire JSON (valid fixture `health.ok.json`):**

```json
{ "status": "ok" }
```

- **Invalid examples (must fail Pydantic + Zod):** `{"status":"healthy"}`, `{"status":1}`, `{"extra":true}`, `{}`.

### 2. Acceptance Criteria

- **AC-02.1:** TestClient GET `/api/health` → 200, body equals valid fixture.
- **AC-02.2:** OpenAPI 200 schema references `HealthResponse` after regen.
- **AC-02.3:** Zod `HealthResponseSchema.parse(valid)` succeeds; invalid fixtures throw.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 03: `GET /api/registry/model` — `ModelRegistryResponse`

### 1. Spec Summary

- **Description:** Model the MRVC manifest returned by `load_effective_manifest`. Align keys and constraints with `model_registry/schema.py` and `ManifestPydantic` in `blobert_asset_gen/api_schemas/manifest.py`.

**Nested models (`models/responses/registry.py`):**

| Model | Fields | Validators |
|-------|--------|------------|
| `VersionRowResponse` | `id`, `path`, `draft`, `in_use`, optional `name` | `id`/`path` non-empty stripped strings; `name` max 128 when present |
| `FamilyBlockResponse` | `versions: list[VersionRowResponse]`, optional `slots: list[str]` | `slots` entries non-empty if present |
| `PlayerActiveVisualResponse` | `path`, `draft` | `path` non-empty; used only inside nullable wrapper |
| `ModelRegistryResponse` | `schema_version`, `enemies`, `player`, `player_active_visual` | `schema_version >= 1`; `enemies` dict keys non-empty; `player_active_visual` null or `PlayerActiveVisualResponse` |

**Route (`registry.py`):**

```python
@router.get("/model", response_model=ModelRegistryResponse)
async def get_model_registry() -> ModelRegistryResponse:
    data = reg.load_effective_manifest(settings.python_root)
    return ModelRegistryResponse.model_validate(data)
```

- **Assumptions:** Service already returns manifest dict passing `validate_manifest`; response model is a typed view of that dict.

**Valid fixture `registry.minimal.ok.json` (committed):**

```json
{
  "schema_version": 1,
  "enemies": {
    "spider": {
      "versions": [
        {
          "id": "v001",
          "path": "animated_exports/spider_animated_00.glb",
          "draft": false,
          "in_use": true
        }
      ],
      "slots": ["v001"]
    }
  },
  "player": {
    "versions": [
      {
        "id": "p001",
        "path": "exports/blobert_default.glb",
        "draft": false,
        "in_use": true
      }
    ],
    "slots": ["p001"]
  },
  "player_active_visual": null
}
```

**Invalid fixtures (non-exhaustive; each must fail both validators):**

| File | Defect |
|------|--------|
| `registry.invalid.extra_top_key.json` | `"foo": 1` at root |
| `registry.invalid.schema_version.json` | `"schema_version": 0` |
| `registry.invalid.version_missing_draft.json` | version row missing `draft` |
| `registry.invalid.bad_path.json` | `path` not allowlisted prefix |
| `registry.invalid.pav_extra_key.json` | `player_active_visual: {"path":"exports/x.glb","draft":false,"extra":1}` |

### 2. Acceptance Criteria

- **AC-03.1:** TestClient GET with mocked `load_effective_manifest` returning minimal fixture → 200 JSON matches fixture.
- **AC-03.2:** `ModelRegistryResponse.model_validate(invalid)` raises `ValidationError` for each invalid fixture.
- **AC-03.3:** Zod `ModelRegistryResponseSchema` mirrors wire keys and passes/fails same fixtures.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large nested model | Review noise | Split nested classes per file section |
| Path allowlist only in Python service | Backend model may accept paths service already filtered | Optional `field_validator` on path prefixes matching allowlist |

### 4. Clarifying Questions

- None.

---

## Requirement 04: `GET /api/meta/enemies` — `MetaEnemiesResponse`

### 1. Spec Summary

- **Description:** Typed response for enemy catalog + build controls + backend status.

**Pydantic (`models/responses/meta.py`):**

| Model | Fields | Notes |
|-------|--------|-------|
| `EnemyMetaRowResponse` | `slug`, `label` | Both `min_length=1` |
| `AnimatedBuildControlDefResponse` | Discriminated by `type` | Mirror TS union: `int`, `select`, `float`, `str`, `select_str`, `bool` with required keys per variant (see `src/types/index.ts` `AnimatedBuildControlDef`) |
| `MetaEnemiesResponse` | `enemies`, `animated_build_controls`, `meta_backend`, optional `meta_error` | `meta_backend: Literal["ok","fallback"]`; `animated_build_controls: dict[str, list[AnimatedBuildControlDefResponse]]`; when `fallback`, `meta_error` required non-empty string |

**Route:** Return `MetaEnemiesResponse` model instances in both try and except ImportError branches (no raw dict in `JSONResponse`).

**Valid fixture `meta.ok.minimal.json`:**

```json
{
  "enemies": [{ "slug": "spider", "label": "Spider" }],
  "animated_build_controls": {},
  "meta_backend": "ok"
}
```

**Valid fixture `meta.fallback.ok.json`:**

```json
{
  "enemies": [{ "slug": "spider", "label": "Spider" }],
  "animated_build_controls": {},
  "meta_backend": "fallback",
  "meta_error": "ImportError: simulated"
}
```

**Invalid fixtures:** `meta_backend: "error"`, missing `slug`, `animated_build_controls` not object, control missing `type`, extra keys on row with `.strict()`.

- **Assumptions:** Pilot Zod does **not** accept legacy `enemies: string[]` wire format; if still needed, handle in `client.ts` pre-parse shim (out of Zod) — current backend emits objects only.

### 2. Acceptance Criteria

- **AC-04.1:** TestClient GET `/api/meta/enemies` (mocked Python imports) returns 200 matching ok or fallback fixture shape.
- **AC-04.2:** Pydantic and Zod reject invalid fixtures in drift suite.
- **AC-04.3:** `meta_error` omitted allowed only when `meta_backend` is `"ok"`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large control-def union | Schema duplication | Share `AnimatedBuildControlDefSchema` in Zod; single Pydantic discriminated union |

### 4. Clarifying Questions

- None.

---

## Requirement 05: Frontend Zod — `schemas.ts`

### 1. Spec Summary

- **Description:** Add `zod@3.24.2` to `package.json` `dependencies`. Create `src/schemas.ts` exporting schemas and `z.infer` types.

**Naming convention:** `*Schema` for Zod; exported types `HealthResponse`, `ModelRegistryResponse`, `MetaEnemiesResponse` (wire/snake_case fields).

**Rules:**

- All pilot object schemas use `.strict()`.
- Use `z.literal("ok")` for health status.
- Registry: nested objects mirror Requirement 03; `player_active_visual: z.union([z.null(), PlayerActiveVisualSchema])`.
- Meta: `meta_backend: z.enum(["ok", "fallback"])`, `meta_error: z.string().min(1).optional()` with `.refine()` or `superRefine` enforcing: if `meta_backend === "fallback"` then `meta_error` present.
- `AnimatedBuildControlDefSchema`: `z.discriminatedUnion("type", [...])` matching TS union arms.

- **Assumptions:** No `z.coerce.date` on pilot (no datetime fields).
- **Scope:** `schemas.ts` only for pilot types (+ shared sub-schemas).

### 2. Acceptance Criteria

- **AC-05.1:** `npm ls zod` shows `3.24.2`.
- **AC-05.2:** Drift tests import schemas and parse valid fixtures.
- **AC-05.3:** Invalid fixtures throw `ZodError` with `issues.length >= 1`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| TS union drift from Python | Runtime failures | Drift fixtures + OpenAPI regen |

### 4. Clarifying Questions

- None.

---

## Requirement 06: Frontend `api-client.ts`

### 1. Spec Summary

- **Description:** Central validated fetch layer.

**Exports (normative):**

```typescript
export class ApiHttpError extends Error { /* status, url */ }
export class ApiValidationError extends Error { /* user message; cause?: ZodError */ }

export async function validatedFetch<T>(
  url: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T>;

export async function getHealth(): Promise<HealthResponse>;
export async function getModelRegistry(): Promise<ModelRegistryResponse>;
export async function getMetaEnemies(): Promise<MetaEnemiesResponse>;
```

- **Base URL:** Paths `/api/health`, `/api/registry/model`, `/api/meta/enemies` (relative, same as existing `client.ts` `BASE = "/api"`).
- **Constraints:** No `as any` / `@ts-ignore` in this module.
- **Scope:** New file; update `healthCheck.ts` to re-export `getHealth` (or delegate).

### 2. Acceptance Criteria

- **AC-06.1:** Vitest mock `fetch` returning valid fixture → `getHealth()` resolves typed data.
- **AC-06.2:** Mock invalid JSON body → `getModelRegistry()` throws `ApiValidationError`.
- **AC-06.3:** Mock 503 → throws `ApiHttpError`, not `ApiValidationError`.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 07: Component Integration (Pilot)

### 1. Spec Summary

- **Description:** Wire validated client into real UI paths without migrating all of `client.ts`.

| Consumer | Change |
|----------|--------|
| Health indicator / any caller of `fetchHealth` | Use `getHealth` from `api-client` via `healthCheck.ts` re-export |
| `ModelRegistryPane.tsx` | `fetchModelRegistry` delegates to `getModelRegistry` from api-client (may keep export name in `client.ts`) |
| `useAppStore` or meta loader | `fetchEnemyPreviewMeta` calls `getMetaEnemies` then applies existing camelCase mapping to `EnemyPreviewMeta` |

- **Constraints:** Do not delete `src/types/index.ts` types in this ticket.
- **Scope:** At least one component path per pilot endpoint.

### 2. Acceptance Criteria

- **AC-07.1:** `ModelRegistryPane` loads registry via validated path (mock test or integration test).
- **AC-07.2:** Meta load path shows user-safe message when `ApiValidationError` injected in test.
- **AC-07.3:** `client.ts` pilot exports document `// M902-25: validated via api-client` above delegating functions.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Double fetch wrappers | Confusion | Single implementation in api-client |

### 4. Clarifying Questions

- None.

---

## Requirement 08: Manual Sync Policy

### 1. Spec Summary

- **Description:** Document manual mirror process in `asset_generation/web/frontend/README.md` (section **Dual validation (Pydantic + Zod)**).

**Checklist (normative steps when backend response shape changes):**

1. Update Pydantic models in `models/responses/`.
2. Update Zod schemas in `src/schemas.ts`.
3. Add/adjust drift fixtures under `scripts/fixtures/dual_validation/`.
4. Run backend pytest + `npm test` for pilot tests.
5. Run `npm run sync-api-types` and commit `api.types.ts` + `scripts/fixtures/openapi.cached.json`.
6. Do **not** edit `api.types.ts` by hand.

- **Deferred:** Script to generate Zod from Pydantic (explicitly out of scope).

### 2. Acceptance Criteria

- **AC-08.1:** README section contains the six-step checklist verbatim as numbered list.
- **AC-08.2:** README states Pydantic is source of truth on backend; Zod is manual mirror on frontend.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Human forgets Zod update | Silent drift | Drift tests in CI |

### 4. Clarifying Questions

- None.

---

## Requirement 09: Drift Tests (Shared Fixtures)

### 1. Spec Summary

- **Description:** Behavioral tests only — no assertions on markdown/ticket prose.

**Fixture directory:** `asset_generation/web/frontend/scripts/fixtures/dual_validation/`

| File | Used by |
|------|---------|
| `health.ok.json` | health |
| `registry.minimal.ok.json` | registry |
| `meta.ok.minimal.json`, `meta.fallback.ok.json` | meta |
| `registry.invalid.*.json`, `meta.invalid.*.json` | negative cases |

**Backend test file:** `asset_generation/web/backend/tests/test_response_models_pilot.py`

- Module docstring traces M902-25.
- Parametrize valid fixtures → `model_validate` + `model_dump(mode="json")` round-trip keys.
- Parametrize invalid fixtures → `pytest.raises(ValidationError)`.
- Optional TestClient tests with mocks for three GET routes.

**Frontend test file:** `asset_generation/web/frontend/src/schemas.pilot.test.ts` (or split api-client tests)

- Vitest: valid fixtures `.parse` ok; invalid throw.
- `api-client` tests with `vi.stubGlobal("fetch", ...)`.

### 2. Acceptance Criteria

- **AC-09.1:** At least **3** valid and **5** invalid fixture-driven assertions across Python + TS.
- **AC-09.2:** Tests pass without live backend (mocks/fixtures only).
- **AC-09.3:** No test reads `project_board/**/*.md`.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 10: OpenAPI Regeneration

### 1. Spec Summary

- **Description:** After backend implementation, run M902-24 sync pipeline so compile-time types reflect new schemas.

### 2. Acceptance Criteria

- **AC-10.1:** `paths["/api/health"]["get"]["responses"][200]` is no longer `unknown` after regen (typed `HealthResponse` or equivalent).
- **AC-10.2:** Same for `/api/registry/model` and `/api/meta/enemies` when OpenAPI documents components.
- **AC-10.3:** Checkpoint records sync command output or attestation.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAPI still generic if response_model missing | Zod remains runtime source of truth | AC-10 enforced in implementation QA |

### 4. Clarifying Questions

- None.

---

## Requirement 11: Test Designer — Adversarial Hints (Non-normative)

Test Breaker should extend beyond fixtures with:

- Extra JSON keys at every nesting level
- Wrong scalar types (`draft: "true"`, `schema_version: "1"`)
- Empty `enemies: {}` (valid) vs empty `versions: []` with missing required version fields
- `meta_backend: fallback` without `meta_error`
- Malformed JSON body, empty body, HTML error page with `ok` false
- Concurrent parallel `getModelRegistry` calls (deterministic mocks)

---

## Requirement 12: Follow-Up Backlog — Remaining `JSONResponse` Routes

Not implemented in M902-25. Use as checklist for follow-up ticket.

| File | Method | Route (prefix) | Notes |
|------|--------|----------------|-------|
| `registry.py` | GET | `/api/registry/model/load_existing/candidates` | |
| `registry.py` | POST | `/api/registry/model/load_existing/open` | |
| `registry.py` | PATCH | `/api/registry/model/enemies/{family}/versions/{version_id}` | returns manifest |
| `registry.py` | PATCH | `/api/registry/model/player_active_visual` | returns manifest |
| `registry.py` | GET | `/api/registry/model/enemies/{family}/slots` | |
| `registry.py` | POST | `/api/registry/model/enemies/{family}/sync_animated_exports` | |
| `registry.py` | PUT | `/api/registry/model/enemies/{family}/slots` | |
| `registry.py` | GET | `/api/registry/model/player/slots` | |
| `registry.py` | PUT | `/api/registry/model/player/slots` | |
| `registry.py` | POST | `/api/registry/model/player/sync_exports` | |
| `registry.py` | GET | `/api/registry/model/enemies/{family}/spawn_eligible` | |
| `registry.py` | DELETE | `/api/registry/model/enemies/{family}/versions/{version_id}` | destructive |
| `registry.py` | DELETE | `/api/registry/model/player_active_visual` | destructive |
| `files.py` | GET/PUT | `/api/files`, `/api/files/{path}` | |
| `assets.py` | GET | `/api/assets`, texture assets | |
| `meta.py` | GET | `/api/meta/animations` | |
| `run.py` | multiple | `/api/run/*` | |

**Count:** 3 pilot conversions of ~28 remaining JSONResponse return sites (exact count may vary; implementer updates table if router diff differs).

---

## Acceptance Criteria Mapping (Ticket → Spec)

| Ticket AC | Pilot? | Spec | Verification |
|-----------|--------|------|--------------|
| All API response types use Pydantic | Partial (3) | Req 02–04, 12 | `response_model` on 3 routes; table for rest |
| Audit routers / convert dict | Partial | Req 12, 01 | Spec table + 3 implementations |
| `response_model` on routes | Yes | Req 02–04 | Code review + OpenAPI |
| Pydantic annotations, validators, docstrings | Yes | Req 01–04 | Code review |
| Backend serialize + ValidationError | Yes | Req 03, 09 | pytest |
| Install Zod | Yes | Req 05 | `package.json` |
| `schemas.ts` + infer | Yes | Req 05 | Vitest |
| `api-client.ts` validated fetch | Yes | Req 06 | Vitest |
| Integrate components | Yes | Req 07 | Tests + grep delegation |
| Zod error UX | Yes | Failure Taxonomy, Req 06–07 | Vitest + UI test |
| Sync process documented | Yes | Req 08 | README |
| Auto-generate Zod | Deferred | Deferred Boundary | N/A |
| 3+ endpoints match / pass / fail | Yes | Req 09 | Drift + route tests |

---

## Risk & Ambiguity Analysis (Cross-Cutting)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Triple schema drift (Pydantic, Zod, OpenAPI) | Medium | Editor bugs | Drift fixtures + sync checklist |
| Strict Zod breaks backward-compatible extra keys | Low | User-visible errors | Intentional fail-closed |
| Meta control-def schema incomplete | Medium | Parse failures on real API | Use one real `animated_build_controls` snapshot fixture from recorded API or minimal spider defs in fixture |
| Registry model_validate on hot path | Low | Latency | Acceptable for editor GET |

---

## Clarifying Questions

- None — resolved in Assumptions A1–A10.

---

## Spec → Test Designer Handoff Notes

- Spec exit gate: `python ci/scripts/spec_completeness_check.py project_board/specs/902_25_pydantic_zod_validation_spec.md --type api`
- Orchestrator transition: `python ci/scripts/run_workflow_transition_gates.py --ticket-id M902-25 --transition spec_to_test_design`
- Prefer **fixture-driven** pytest/Vitest; mock `load_effective_manifest` and meta imports — no `python_root` disk dependency in unit tests.
- Module docstrings: trace **M902-25** (not ticket id in filenames).
