# Execution Plan: M902-26 API Contract Testing

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/26_api_contract_testing.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-21  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-26/` (`todos-latest.json`, `handoff-latest.yaml`)

---

## Executive Summary

**Objective:** Add pytest + `jsonschema` contract tests for every public route under `asset_generation/web/backend/routers/` (plus `GET /api/health`), using the FastAPI OpenAPI document as the single source of truth for response shapes. Wire the suite into the canonical Python CI path (`ci/scripts/run_tests.sh` → `.lefthook/scripts/py-tests.sh`) so API drift fails before merge.

**Scope:**

| Layer | Deliverable |
|-------|-------------|
| Schema authority | OpenAPI 3.x from `app.openapi()` or committed snapshot `asset_generation/web/frontend/scripts/openapi.cached.json` (M902-24) |
| Test harness | Shared loader: path + method + status → JSON Schema from `components.responses` / `paths.*.responses` |
| Contract tests | Per-router modules under `asset_generation/python/tests/api/` (ticket AC name; **not** repo-root `tests/api/`) |
| Validation | `jsonschema.validate(instance, schema)` on success and documented error bodies (`HTTPValidationError`, `detail` string/object) |
| CI | `jsonschema` direct dev dependency in `asset_generation/python/pyproject.toml`; suite picked up by existing `pytest tests/` |
| Docs | Module docstring + runbook section (spec chooses: extend `asset_generation/web/backend/AGENTS.md` or frontend README — **no** new top-level doc unless spec requires) |

**Out of scope:** Frontend Zod contract tests (M902-25); regenerating TypeScript types (M902-24); replacing existing behavioral/delegation tests in `asset_generation/web/backend/tests/` or `asset_generation/python/tests/web/` — contract tests **add** OpenAPI enforcement, do not delete service-boundary tests.

**Prerequisites:** M902-24 COMPLETE (OpenAPI snapshot + `sync-api-types`). M902-25 COMPLETE (Pydantic `response_model` on 3 pilot GETs). FastAPI app importable from `asset_generation/python` dev extras.

**Estimated Effort:** 9–11 agent runs (see table below).

---

## Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | Endpoint inventory, OpenAPI→JSON Schema extraction rules, error schema, SSE `/api/run/stream` contract, CI path; `--type api` |
| Test design | Test Designer | 1–2 | Harness + happy/error cases per route; mocks for filesystem/registry/python_root |
| Test break | Test Breaker | 1 | Extra fields, wrong status, stale OpenAPI, malformed bodies, unicode paths |
| Implementation | Implementation Agent (Backend) | 2–3 | Harness, `jsonschema` dep, all router modules, baseline pass |
| Static QA | Code Reviewer | 1 | `uv run pytest tests/api/ -q`, ruff on new modules |
| AC gatekeeper | AC Gatekeeper | 1 | AC matrix; known deviations in checkpoint; commit/push before COMPLETE |

**Total:** 9–11 runs

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-26? | Notes |
|------------|----------------|-----------------|-------|
| **M902-24** OpenAPI → TypeScript | `02_complete/24_openapi_typescript_generation.md` | **No** (satisfied) | Cached `openapi.cached.json`; regen when routes change |
| **M902-25** Pydantic + Zod pilot | `02_complete/25_pydantic_zod_dual_validation.md` | **No** (satisfied) | 3 routes have richer OpenAPI `components`; remaining routes still dict/JSONResponse |
| FastAPI backend + routers | `asset_generation/web/backend/` | **No** (satisfied) | 5 router modules + `main.py` health |
| Python CI pytest | `asset_generation/python/tests/` | **No** (satisfied) | `tests/web/test_registry_api.py` precedent for ASGI client |
| `jsonschema` package | Transitive in lockfile | Soft | Spec pins direct `dev` extra for stable import |
| M902-23 Handoff / todo gates | `02_complete/` | **No** | Orchestrator: `run_workflow_transition_gates.py --transition planner_to_spec` |

**Umbrella:** No.

**Cycles / WARN:** Ticket AC path `tests/api/test_registry_contract.py` is ambiguous vs repo layout — resolved to `asset_generation/python/tests/api/` (see checkpoint M902-26 planning).

---

## Public Endpoint Inventory (Planning — Spec Agent Refines)

Routes below are **public** HTTP handlers in `routers/` + app-level health. Spec must assign happy-path fixture/mocks and error-path triggers per route.

| # | Method | Path | Router file | Notes |
|---|--------|------|-------------|-------|
| 1 | GET | `/api/health` | `main.py` | `response_model=HealthResponse` (M902-25) |
| 2 | GET | `/api/files` | `files.py` | List |
| 3 | GET | `/api/files/{file_path}` | `files.py` | Read |
| 4 | PUT | `/api/files/{file_path}` | `files.py` | Write; 400/403/404 errors |
| 5 | GET | `/api/registry/model/load_existing/candidates` | `registry.py` | Query params |
| 6 | POST | `/api/registry/model/load_existing/open` | `registry.py` | Body validation → 422 |
| 7 | GET | `/api/registry/model` | `registry.py` | `response_model` (M902-25) |
| 8 | PATCH | `/api/registry/model/enemies/{family}/versions/{version_id}` | `registry.py` | Body |
| 9 | PATCH | `/api/registry/model/player_active_visual` | `registry.py` | Body |
| 10 | GET | `/api/registry/model/enemies/{family}/slots` | `registry.py` | |
| 11 | POST | `/api/registry/model/enemies/{family}/sync_animated_exports` | `registry.py` | Side effect; contract on JSON body only |
| 12 | PUT | `/api/registry/model/enemies/{family}/slots` | `registry.py` | Body |
| 13 | GET | `/api/registry/model/player/slots` | `registry.py` | |
| 14 | PUT | `/api/registry/model/player/slots` | `registry.py` | Body |
| 15 | POST | `/api/registry/model/player/sync_player_exports` | `registry.py` | |
| 16 | GET | `/api/registry/model/spawn_eligible/{family}` | `registry.py` | |
| 17 | DELETE | `/api/registry/model/enemies/{family}/versions/{version_id}` | `registry.py` | Destructive — spec uses destructive template sections only if AC requires confirmation contract (likely N/A: registry version delete) |
| 18 | DELETE | `/api/registry/model/player_active_visual` | `registry.py` | |
| 19 | GET | `/api/run/stream` | `run.py` | **SSE** — spec defines event JSON schema or documents exemption with alternate assertion |
| 20 | GET | `/api/run/complete` | `run.py` | Long-poll / completion JSON |
| 21 | POST | `/api/run/kill` | `run.py` | |
| 22 | GET | `/api/run/status` | `run.py` | |
| 23 | GET | `/api/assets` | `assets.py` | List |
| 24 | GET | `/api/assets/textures` | `assets.py` | |
| 25 | GET | `/api/assets/textures/file/{file_path}` | `assets.py` | Binary vs JSON — contract may scope to JSON/list endpoints only |
| 26 | GET | `/api/assets/{asset_path}` | `assets.py` | GLB octet-stream — validate headers + status, not JSON schema |
| 27 | GET | `/api/meta/enemies` | `meta.py` | `response_model` (M902-25) |
| 28 | GET | `/api/meta/animations` | `meta.py` | |

**Count:** 28 handlers (27 under routers + health).

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Ticket AC | `.../01_in_progress/26_api_contract_testing.md` | Source requirements |
| Spec stub pointer | `project_board/specs/902_26_api_contract_testing_spec.md` | **Absent** — Spec Agent creates Task 1 |
| OpenAPI cache | `asset_generation/web/frontend/scripts/openapi.cached.json` | Offline schema source |
| OpenAPI sync | `asset_generation/web/frontend/scripts/sync-api-types.sh` | Regen when backend changes |
| ASGI test precedent | `asset_generation/python/tests/web/test_registry_api.py` | `httpx` + `ASGITransport` + `python_root` fixture |
| Backend local tests | `asset_generation/web/backend/tests/*.py` | Behavioral tests; keep separate from contract suite |
| Pilot response tests | `asset_generation/web/backend/tests/test_response_models_pilot.py` | Pydantic drift — complement, not replace OpenAPI jsonschema |
| CI entry | `ci/scripts/run_tests.sh` | Godot + `py-tests.sh` (Python only today) |
| LEARNINGS | `project_board/LEARNINGS.md` (M902 web tests) | Prefer `asset_generation/python/tests/web/` or `tests/api/` for CI |

**Gap:** No `tests/api/`, no OpenAPI→jsonschema harness, no direct `jsonschema` dev dependency.

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: OpenAPI contract architecture** | Spec Agent | Ticket AC; execution plan; all `routers/*.py`, `main.py`; `openapi.cached.json`; M902-24/25 specs; `test_registry_api.py`, `test_response_models_pilot.py` | `project_board/specs/902_26_api_contract_testing_spec.md` with: (a) **schema authority**: load order (`app.openapi()` in tests vs cached file hash pin), (b) **JSON Schema extraction**: map `(method, path, status)` → schema ref resolution (`$ref`, `allOf`, nullable), (c) **strictness**: `additionalProperties: false` policy for responses where OpenAPI allows, (d) **error contracts**: 400/404/422/503 bodies — FastAPI `HTTPValidationError`, `detail` string vs list, (e) **per-endpoint table**: happy + error case, required mocks (`python_root`, export dirs, registry fixture), (f) **non-JSON routes**: assets GLB, files binary — header/status contract only, (g) **SSE** `/api/run/stream`: event shape or scoped exemption with rationale, (h) **test layout**: `asset_generation/python/tests/api/test_{files,registry,run,assets,meta}_contract.py` + `conftest.py` shared client/fixtures, (i) **overlap policy** vs existing `tests/web/` and `backend/tests/`, (j) **reasonable value checks**: uuid format, non-empty strings — jsonschema `format` + optional custom validators, (k) **CI**: confirm `py-tests.sh` coverage; optional lefthook hook spec, (l) **runbook**: steps to add contract test when adding a route + when to run `npm run sync-api-types`, (m) AC traceability. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_26_api_contract_testing_spec.md --type api`. | None | Spec exit gate PASS; endpoint table complete; SSE/binary resolved. | **A1:** OpenAPI may omit strict `additionalProperties` on legacy dict routes — spec documents fail-open vs tighten. **A2:** Ticket example hand-written `REGISTRY_SCHEMA` is illustrative only — normative source is OpenAPI. **A3:** Destructive registry DELETE — use `api` type, not full destructive template unless confirmation UX exists. |
| **2** | **Test design: contract harness + router modules** | Test Designer | Spec (Task 1) | `tests/api/conftest.py` (OpenAPI loader, `validate_response`, httpx client); per-router test modules with happy + ≥1 error per endpoint; module docstrings cite M902-26; **no** markdown assertions. Tests fail before harness exists. | Task 1 | Red suite; inventory matches spec table. | **R1:** Flaky registry state — use tmp `python_root` like `test_registry_api.py`. **R2:** Run router may need process mocks. |
| **3** | **Test break: adversarial contracts** | Test Breaker | Tests (Task 2), spec | Cases: response with extra keys (if strict), wrong Content-Type, stale cached OpenAPI vs live app, invalid uuid path params, malformed JSON POST, empty body, unicode in paths, concurrent registry PATCH; 4 consecutive green runs after impl. | Task 2 | +8 cases; deterministic. | |
| **4** | **Implementation: harness, dependency, baseline green** | Implementation Agent (Backend) | Spec; tests (Tasks 2–3) | Add `jsonschema` to `[project.optional-dependencies].dev`; implement OpenAPI resolver; fill tests until `cd asset_generation/python && uv run pytest tests/api/ -q` PASS; document known deviations in checkpoint; regen `openapi.cached.json` if spec requires after OpenAPI changes. | Tasks 1–3 | All AC endpoints covered; baseline pass logged. | **R3:** Binary/SSE endpoints may need narrower assertions. **R4:** diff-cover on new tests — mostly non-`src/` paths; confirm omit rules. |
| **5** | **CI integration verification** | Implementation Agent (Backend) | Task 4 | Evidence that `timeout 300 ci/scripts/run_tests.sh` runs contract tests (via py-tests); optional: lefthook pre-push note in spec/runbook only if spec mandates. Update runbook section per spec. | Task 4 | Full CI script includes new tests; failure blocks merge in practice. | **A4:** `run_tests.sh` does not invoke `backend/tests/` separately — contract tests **must** live under `asset_generation/python/tests/`. |
| **6** | **Static QA** | Code Reviewer | Tasks 4–5 | `uv run pytest tests/api/ -q`; ruff on new files; no empty except; no prose-only tests. | Task 5 | Clean report. | |
| **7** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | AC matrix; checkpoint lists any known schema deviations; commit/push; `git mv` ticket to `02_complete/`. | Tasks 1–6 | All AC satisfied or documented deviations with follow-up; git push before COMPLETE. | |

---

## Acceptance Criteria Traceability (Planning)

| AC (ticket) | Task owner |
|-------------|------------|
| Contract test file(s) under `tests/api/` | 1 (path), 2, 4 — resolved to `asset_generation/python/tests/api/` |
| All public router endpoints: happy + error | 1, 2, 4 |
| Status code + JSON shape + no extra fields + reasonable values | 1, 2, 4 |
| pytest + jsonschema + OpenAPI source | 1, 4 |
| Error cases 400/422 consistent `detail` | 1, 2, 4 |
| Comment + runbook + OpenAPI link | 1, 5 |
| CI via `run_tests.sh` | 5 |
| Pre-commit optional | 1 (spec decides) |
| Baseline pass + deviations in checkpoint | 4, 7 |

---

## OpenAPI Harness (Planning Default)

```python
# tests/api/openapi_contract.py (name per spec)
# - load_spec() -> dict from app.openapi() or cached JSON
# - response_schema(method, path, status_code) -> dict
# - validate_response(response, *, expected_status) -> None  # raises jsonschema.ValidationError
```

**Regeneration contract:** When a route's Pydantic model or response dict changes, developer runs backend tests + `npm run sync-api-types` so OpenAPI cache and TS types stay aligned; contract tests fail if only one layer updated.

---

## Notes

- **Spec type `api`:** Mutation-heavy registry/files routes; error body contracts required.
- **M902-25 relationship:** Pilot routes already in OpenAPI with full schemas — contract tests should derive schemas from spec, not duplicate hand-written dicts from ticket example.
- **Test realism:** Assert HTTP + `jsonschema.validate`, not ticket markdown.
- **Handoff gates:** Planner artifacts in `project_board/checkpoints/M902-26/`; orchestrator runs `run_workflow_transition_gates.py --ticket-id M902-26 --transition planner_to_spec`.
- **Commit policy:** Implementation agents commit per handoff; planner commits plan + checkpoint + ticket state.

---

## Next Steps

**Immediate:** Spec Agent — author `project_board/specs/902_26_api_contract_testing_spec.md` per Task 1, including SSE/binary endpoint policy and full endpoint error matrix.

**Unblocks:** CI-enforced API drift detection across asset editor backend surface.
