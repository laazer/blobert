# Execution Plan: M902-25 Pydantic + Zod Dual Validation

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/25_pydantic_zod_dual_validation.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-21  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-25/` (`todos-latest.json`, `handoff-latest.yaml`)

---

## Executive Summary

**Objective:** Introduce dual runtime validation at API boundaries: Pydantic `response_model` on the backend and Zod `.parse()` on the frontend. Pilot on three endpoints to prove the pattern, then document manual sync until auto-generation is deferred to a follow-up ticket.

**Phased scope (this ticket):**

| Layer | Deliverable | Pilot endpoints |
|-------|-------------|-----------------|
| Backend | `asset_generation/web/backend/models/responses/` modules; routes return Pydantic models via `response_model` | `GET /api/health`, `GET /api/registry/model`, `GET /api/meta/enemies` |
| Frontend | `src/schemas.ts` (Zod), `src/api-client.ts` (validated fetch); wire pilot calls | Same three; migrate from compile-time-only `api.types.ts` / `src/types` for these paths |
| Sync | Manual mirror contract + drift tests; regen OpenAPI after backend model changes | Cross-check Zod vs Pydantic fixtures; `sync-api-types` refresh updates `api.types.ts` for compile-time parity |

**Out of scope (follow-up ticket):** Remaining ~25 JSONResponse endpoints across `registry.py`, `run.py`, `files.py`, `assets.py`, `meta.py` (animations). Ticket AC “100% runtime coverage” is **deferred** — this ticket delivers the pattern + 3-endpoint pilot with explicit follow-up enumeration in spec.

**Prerequisites:** M902-24 COMPLETE (`src/api.types.ts`, `scripts/sync-api-types.sh`, `healthCheck.ts` pilot). FastAPI OpenAPI at `/openapi.json`. Vitest + pytest CI present.

**Estimated Effort:** 8–10 agent runs (see table below).

---

## Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | Pilot endpoint contracts, model module layout, Zod mirror rules, sync/drift test contract; `--type api` |
| Test design | Test Designer | 1 | Backend pytest (response_model + invalid payload → 422/500); frontend Vitest (Zod pass/fail + api-client); fixture JSON per pilot |
| Test break | Test Breaker | 1 | Adversarial: extra fields, wrong types, null vs missing, nested registry drift, HTTP error paths |
| Implementation | Implementation Agent (Backend) | 1–2 | `models/responses/*`; refactor 3 routes off JSONResponse; OpenAPI regen triggers |
| Implementation | Implementation Agent (Frontend) | 1–2 | `zod` dep; `schemas.ts`; `api-client.ts`; migrate health + registry model + meta enemies from `client.ts` / `healthCheck.ts` |
| Static QA | Code Reviewer | 1 | `npm run build`, `npm test`, backend pytest, ruff on touched `.py` |
| AC gatekeeper | AC Gatekeeper | 1 | AC matrix; 3-endpoint smoke; git commit/push before COMPLETE |

**Total:** 8–10 runs

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-25? | Notes |
|------------|----------------|-----------------|-------|
| **M902-24** OpenAPI → TypeScript Generation | `02_complete/24_openapi_typescript_generation.md` | **No** (satisfied) | `api.types.ts` informs Zod field names/types; `healthCheck.ts` is first consumer to upgrade to Zod |
| FastAPI backend + OpenAPI | `asset_generation/web/backend/` | **No** (satisfied) | Most routes still `JSONResponse`; pilot converts 3 |
| Frontend Vite + React + TS | `asset_generation/web/frontend/` | **No** (satisfied) | No `zod` yet; `client.ts` uses manual `src/types` |
| M902-23 Handoff / todo gates | `02_complete/` | **No** | Orchestrator runs `run_workflow_transition_gates.py --transition planning_to_specification` |
| `zod` npm package | External | Soft | Pin major in spec; lockfile update in frontend implementation |

**Umbrella:** No.

**Cycles / WARN:** Ticket AC mentions “100% runtime coverage” — **WARN:** plan scopes pilot (3 endpoints) only; spec must enumerate remaining endpoints as follow-up backlog to avoid scope creep in one run.

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Ticket AC | `.../01_in_progress/25_pydantic_zod_dual_validation.md` | Source requirements |
| Spec stub pointer | `project_board/specs/902_25_pydantic_zod_validation_spec.md` | **Absent** — Spec Agent creates in Task 1 |
| Health route (dict return) | `asset_generation/web/backend/main.py` | `return {"status": "ok"}` — no `response_model` |
| Registry model GET (dict return) | `asset_generation/web/backend/routers/registry.py` | `get_model_registry()` → `JSONResponse(data)` |
| Meta enemies GET (dict return) | `asset_generation/web/backend/routers/meta.py` | `get_enemies()` → `JSONResponse({...})` |
| Inline request models | `registry.py`, `files.py`, `assets.py` | Request bodies use Pydantic; responses do not |
| Manual frontend types | `asset_generation/web/frontend/src/types/index.ts` | `ModelRegistryPayload`, `EnemyPreviewMeta` — coexist during pilot |
| OpenAPI generated types | `asset_generation/web/frontend/src/api.types.ts` | Compile-time reference for Zod field alignment |
| M902-24 health pilot | `asset_generation/web/frontend/src/api/healthCheck.ts` | Uses `paths["/api/health"]` — upgrade to Zod parse |
| API client (unvalidated fetch) | `asset_generation/web/frontend/src/api/client.ts` | `fetchModelRegistry()`, `fetchAnimatedEnemyMeta()` — pilot migration targets |
| Backend AGENTS.md | `asset_generation/web/backend/AGENTS.md` | Documents `models/` layer — currently empty on disk |

**Gap:** No `backend/models/responses/`, no `schemas.ts`, no `api-client.ts`, no `zod` dependency.

---

## Pilot Endpoint Contracts (Planning Defaults)

Spec Agent may refine shapes; defaults below match current runtime JSON.

### 1. `GET /api/health` (`main.py`)

- **Backend model:** `HealthResponse(status: Literal["ok"])`
- **Frontend schema:** `HealthResponseSchema = z.object({ status: z.literal("ok") })`
- **Consumer today:** `healthCheck.ts` → move to `api-client.ts` or re-export

### 2. `GET /api/registry/model` (`registry.py`)

- **Backend model:** Nested `ModelRegistryResponse` matching MRVC manifest (`schema_version`, `enemies`, optional `player`, `player_active_visual`)
- **Field validators:** `schema_version` int ≥ 1; version `id`/`path` non-empty; `player_active_visual` null or object
- **Frontend schema:** Mirror nested structure; map snake_case JSON keys (`player_active_visual`) — Zod uses same keys as wire format
- **Consumer today:** `client.ts::fetchModelRegistry()` → `ModelRegistryPayload` from `src/types`

### 3. `GET /api/meta/enemies` (`meta.py`)

- **Backend model:** `MetaEnemiesResponse(enemies, animated_build_controls, meta_backend, optional meta_error)`
- **Field validators:** `enemies[].slug`/`label` non-empty; `meta_backend` enum `ok|fallback`
- **Frontend schema:** Discriminated union or optional fields for fallback path; `animated_build_controls` as record of control-def arrays (align with existing `AnimatedBuildControlDef` manual type shape)
- **Consumer today:** `client.ts` meta fetch → `EnemyPreviewMeta`

**OpenAPI regen:** After backend `response_model` lands, run `npm run sync-api-types` and commit updated `api.types.ts` + cache so compile-time and runtime layers stay aligned.

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: dual-validation architecture, pilot contracts, sync policy** | Spec Agent | Ticket AC; spec path `902_25_pydantic_zod_validation_spec.md`; `main.py`, `registry.py`, `meta.py`; `client.ts`, `healthCheck.ts`, `api.types.ts`, `types/index.ts`; M902-24 spec for OpenAPI workflow | `project_board/specs/902_25_pydantic_zod_validation_spec.md` with: (a) **backend module layout**: `asset_generation/web/backend/models/responses/{health,registry,meta}.py` + `__init__.py` re-exports; routers import response models only (request models may stay colocated or move per spec), (b) **per-pilot Pydantic contract**: field list, validators, docstrings, example JSON fixtures (valid + invalid), (c) **route refactor rules**: replace `JSONResponse(dict)` with model instance + `response_model=`; error paths unchanged (HTTPException), (d) **frontend layout**: `src/schemas.ts` (Zod + `z.infer` types), `src/api-client.ts` (generic `validatedFetch<T>(url, schema)` + pilot functions), (e) **Zod mirror rules**: wire-format key names, coercion policy (`z.coerce.date` only where backend emits ISO strings — likely N/A for pilot), strict vs strip unknown fields (recommend `.strict()` or `z.object({...}).strict()` for fail-closed), (f) **error handling contract**: Zod failures → log structured error + throw `ApiValidationError` with user-safe message; no raw Zod dump in UI, (g) **sync policy**: manual mirror checklist; when backend model changes → update Zod + fixture tests + run `sync-api-types`; defer Pydantic→Zod codegen, (h) **drift tests**: shared fixture JSON files under `asset_generation/web/frontend/scripts/fixtures/` or `tests/` validated by both pytest (Pydantic model_validate) and Vitest (Zod parse), (i) **migration scope**: which `client.ts` functions move to `api-client.ts` vs re-export; keep non-pilot endpoints on legacy fetch until follow-up, (j) **follow-up backlog table**: all remaining JSONResponse routes by file, (k) AC traceability + OpenAPI regen step. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_25_pydantic_zod_validation_spec.md --type api` before TEST_DESIGN. | None | Spec exit gate PASS; 3 pilot contracts frozen; follow-up enumeration complete. | **A1:** Registry manifest shape is dynamic — spec must reference `load_effective_manifest` sample or checked-in fixture. **A2:** Meta `animated_build_controls` is deeply nested — spec may allow `z.record(z.array(AnimatedBuildControlDefSchema))` with shared sub-schema. **A3:** Do not delete `src/types/index.ts` in pilot — incremental migration. |
| **2** | **Test design: backend response_model + frontend Zod** | Test Designer | Spec (Task 1) | Backend: `tests/web_backend/test_response_models_pilot.py` (or colocated per spec) — valid fixture serializes; invalid fixture raises ValidationError; TestClient GET returns 200 + schema-conformant JSON for 3 routes (mock registry service where needed). Frontend: Vitest for `schemas.ts` + `api-client.ts` — parse success, parse failure throws typed error, fetch mock returns validated data. Shared fixtures committed. Module docstrings trace M902-25. **No** markdown/ticket prose assertions. | Task 1 | Tests red before implementation. | **R1:** Registry tests need fixture manifest — use minimal JSON from spec, not live python_root. |
| **3** | **Test break: adversarial validation** | Test Breaker | Tests (Task 2), spec | Cases: extra JSON keys, wrong scalar types, empty enemies map, null vs omitted optional, registry version missing `draft`, meta fallback missing `meta_error`, HTTP 500 still unvalidated (document), concurrent fetch, malformed JSON body, schema strictness bypass attempts. 4 consecutive runs zero flakes. | Task 2 | +8 cases; determinism. | |
| **4** | **Implementation (Backend): response models + route refactor** | Implementation Agent (Backend) | Spec; tests (Tasks 2–3) | Create `models/responses/` modules; add `HealthResponse`, registry manifest models, meta enemies models with Field validators + docstrings; update `main.py`, `registry.py` (`get_model_registry`), `meta.py` (`get_enemies`) to `response_model=`; remove JSONResponse returns for pilot routes; run backend tests PASS; regen OpenAPI snapshot instructions in checkpoint. | Tasks 1–3 | 3 routes return Pydantic-serialized JSON; OpenAPI schemas populated for pilot paths. | **R2:** Large registry model — keep nested types readable; avoid circular imports. |
| **5** | **Implementation (Frontend): Zod schemas + validated api-client** | Implementation Agent (Frontend) | Spec; Task 4 OpenAPI; tests | `npm install zod`; `src/schemas.ts`; `src/api-client.ts`; migrate `fetchHealth`, `fetchModelRegistry`, meta enemies fetch to validated client; update `healthCheck.ts` to re-export from api-client or deprecate; user-facing error handling per spec; `npm run sync-api-types` + commit `api.types.ts` if backend OpenAPI changed. All frontend tests PASS. | Tasks 1–3, 4 | Zod parse on success path for 3 endpoints; components receive inferred types. | **R3:** camelCase vs snake_case — wire format stays snake_case; no silent remapping unless spec defines transform layer. |
| **6** | **Implementation: component integration + sync docs** | Implementation Agent (Frontend) | Spec § sync; Task 5 | Wire at least one component path per pilot (e.g. registry pane uses validated registry fetch; health indicator uses validated health); add short section to `asset_generation/web/frontend/README.md` on dual validation + manual sync checklist (no new top-level doc file unless spec requires). Drift tests PASS. | Task 5 | AC: components use api-client for pilot; sync process documented. | Avoid drive-by migration of all `client.ts` exports. |
| **7** | **Static QA** | Code Reviewer | Tasks 4–6 | `npm run build`, `npm test`, backend pytest subset, ruff on changed Python; no `as any` / `@ts-ignore` on pilot paths. | Task 6 | No blocking findings. | |
| **8** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Evidence matrix mapping pilot AC → files + tests + commands; verify 3 endpoints valid/invalid validation; note deferred full-coverage follow-up; git commit/push before COMPLETE; `git mv` ticket to `02_complete/`. | Tasks 1–7 | Pilot AC satisfied; follow-up backlog linked in spec. | COMPLETE blocked without push per workflow. |

---

## Acceptance Criteria Traceability (Planning — Pilot Scope)

| AC (ticket) | Pilot scope? | Task owner |
|-------------|--------------|------------|
| All API response types use Pydantic | **Partial** — 3 pilot routes | 1, 4 |
| Audit routers / convert dict returns | **Partial** — audit in spec Task 1 (j); implement 3 | 1, 4 |
| `response_model` on routes | 3 pilots | 4 |
| Pydantic: annotations, validators, docstrings | 3 pilots | 1, 4 |
| Backend tested: serialize + ValidationError | 3 pilots | 2, 4 |
| Install Zod | Yes | 5 |
| `schemas.ts` with infer types | 3 pilots | 1, 5 |
| `api-client.ts` validated fetch | 3 pilots | 1, 5 |
| Integrate into components | 3 pilots | 6 |
| Zod error handling + user message | Yes | 1, 5, 6 |
| Sync process documented | Yes | 1, 6 |
| Auto-generate Zod from Pydantic | Deferred | 1 (document) |
| Tested 3+ endpoints match / pass / fail | Yes | 2, 3, 7, 8 |

---

## Backend Module Layout (Planning Default)

```
asset_generation/web/backend/models/
├── __init__.py
└── responses/
    ├── __init__.py      # re-export HealthResponse, ModelRegistryResponse, MetaEnemiesResponse
    ├── health.py
    ├── registry.py      # nested version/player models
    └── meta.py
```

Routers: thin handlers call services, construct response model, return instance (FastAPI serializes).

---

## Frontend Module Layout (Planning Default)

```
asset_generation/web/frontend/src/
├── schemas.ts           # Zod schemas + z.infer types for pilot (+ shared sub-schemas)
├── api-client.ts        # validatedFetch + getHealth / getModelRegistry / getMetaEnemies
├── api/
│   ├── healthCheck.ts   # re-export or thin wrapper → api-client (backward compat)
│   └── client.ts        # legacy fetch; pilot functions delegate or deprecate with comment
└── api.types.ts         # compile-time (M902-24); regen after backend OpenAPI change
```

---

## Notes

- **Spec type `api`:** Pilot endpoints are read-heavy GET contracts; spec exit gate enforces API sections.
- **M902-24 relationship:** `api.types.ts` remains compile-time layer; Zod adds runtime layer. Both should agree on pilot shapes — drift tests are the enforcement mechanism until codegen exists.
- **Test realism:** Assert JSON round-trip and parse behavior, not ticket markdown wording.
- **Handoff gates:** Planner writes `todos-latest.json` + `handoff-latest.yaml`; orchestrator runs `run_workflow_transition_gates.py --ticket-id M902-25 --transition planning_to_specification` before Spec Agent.
- **Follow-up ticket (recommended):** “M902-25b” or M902-26 — roll `response_model` + Zod to remaining JSONResponse routes using pilot templates.
- **Commit policy:** Implementation agents commit per handoff; generated `api.types.ts` updated when backend OpenAPI changes.

---

## Next Steps

**Immediate:** Spec Agent — author `project_board/specs/902_25_pydantic_zod_validation_spec.md` per Task 1, including registry manifest fixture and follow-up route inventory.

**Unblocks:** Runtime safety at API boundaries; reduces silent schema drift between Python pipeline manifest and React editor.
