# Execution Plan: M902-24 OpenAPI → TypeScript Generation

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/24_openapi_typescript_generation.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-21  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-24/` (`todos-latest.json`, `handoff-latest.yaml`)

---

## Executive Summary

**Objective:** Add `openapi-typescript` to the asset editor frontend, generate strongly typed `src/api.types.ts` from the FastAPI OpenAPI document, support offline regeneration via a cached spec snapshot, wire `npm run sync-api-types`, document usage in a frontend README, and demonstrate one real component import.

**Scope:**
- Dev dependency: `openapi-typescript` in `asset_generation/web/frontend/package.json`
- Shell script: `asset_generation/web/frontend/scripts/sync-api-types.sh` (fetch → generate → exit codes)
- Cached spec: committed fallback when `http://localhost:8000/openapi.json` is unreachable
- Generated output: `asset_generation/web/frontend/src/api.types.ts` (committed; valid under `tsc --noEmit`)
- Optional thin helper: typed `fetch` wrapper or path-key helper in `src/api/` (only if spec mandates; default: import types only)
- Example usage in one existing component (e.g. registry pane or `src/api/client.ts` for a single endpoint)
- README: `asset_generation/web/frontend/README.md` (sync workflow, troubleshooting)

**Prerequisites:** FastAPI backend exposes OpenAPI at `/openapi.json` (default). Node ≥18 frontend (`package.json` engines). Vite proxy `/api` → `:8000` already configured.

**Estimated Effort:** 6–8 agent runs (see table below).

---

## Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | Freeze paths, cache policy, type consumption pattern, spec exit `--type api` |
| Test design | Test Designer | 1 | Shell + `tsc` behavioral tests; Vitest only if spec requires component-level contract |
| Test break | Test Breaker | 1 | Adversarial: corrupt cache, partial fetch, stale spec, wrong OpenAPI version |
| Implementation | Implementation Agent (Frontend) | 2 | Task A: script + deps + generated file + cache; Task B: README + example import |
| Static QA | Code Reviewer / frontend lint | 1 | `npm run build`, eslint on touched TS, script shellcheck if used elsewhere |
| AC gatekeeper | AC Gatekeeper | 1 | Map AC → evidence; manual smoke with backend up/down |

**Total:** 6–8 runs

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-24? | Notes |
|------------|----------------|-----------------|-------|
| M902-01 Validation Gate Framework | `02_complete/` | **No** (optional) | No new gate module required unless spec expands; workflow transition gates use handoff/todo artifacts only |
| FastAPI backend + OpenAPI | `asset_generation/web/backend/` (runtime) | **No** (satisfied at dev time) | `main.py` FastAPI app; OpenAPI 3.x at `/openapi.json` |
| Node frontend (Vite + React + TS) | `asset_generation/web/frontend/` | **No** (satisfied) | `tsc` in build script; Vitest present; no `openapi-typescript` yet |
| M902-23 Handoff / todo gates | `02_complete/` or in_progress | **No** | Orchestrator runs `run_workflow_transition_gates.py`; this ticket produces planner handoff artifacts |
| `openapi-typescript` npm package | External | Soft | Pin version in spec; lockfile update in implementation |

**Umbrella:** No.

**Cycles / WARN:** None. M902-01 is informational only for this ticket.

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Ticket AC | `.../01_in_progress/24_openapi_typescript_generation.md` | Source requirements |
| Spec stub pointer | `project_board/specs/902_24_openapi_typescript_gen_spec.md` | **Absent** — Spec Agent creates in Task 1 |
| API client (manual types) | `asset_generation/web/frontend/src/api/client.ts` | Primary integration point; imports from `../types` today |
| Manual types | `asset_generation/web/frontend/src/types/index.ts` | Coexistence strategy: generated types for OpenAPI paths; legacy types until migrated |
| Vite proxy | `asset_generation/web/frontend/vite.config.ts` | Dev `/api` → `127.0.0.1:8000` |
| Backend registry routes | `asset_generation/web/backend/routers/registry.py` | Rich OpenAPI surface for realistic generated types |
| Root README | `README.md` | Optional one-line link; primary doc is frontend README per AC |

**Gap:** No `scripts/` dir, no `api.types.ts`, no `openapi-typescript` dep, no frontend README.

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: sync pipeline, cache, types consumption** | Spec Agent | Ticket AC; ticket spec path `902_24_openapi_typescript_gen_spec.md`; `client.ts`; FastAPI OpenAPI URL; `openapi-typescript` CLI docs | `project_board/specs/902_24_openapi_typescript_gen_spec.md` with: (a) **fetch contract**: primary URL `http://127.0.0.1:8000/openapi.json` (and env override `OPENAPI_URL`), timeout, curl/wget requirements, (b) **cache contract**: repo-relative path e.g. `scripts/openapi.cached.json` — update on successful fetch; on fetch failure use cache if present else exit non-zero with stderr message, (c) **generation**: `npx openapi-typescript <spec> -o src/api.types.ts` flags (default config), (d) **git policy**: commit `api.types.ts` + cached spec; regen when backend routes change, (e) **type usage pattern**: import `paths`, `components`, `operations` from generated module; example for `GET /api/registry/model` response typing, (f) **build integration**: when to run `sync-api-types` (`predev` / manual only — spec picks one; ticket suggests dev server “up-to-date” → recommend `predev` + documented manual sync), (g) **README sections**: run after backend change, troubleshooting (backend down, stale cache, tsc errors), (h) **test contract**: shell tests invoke script with mocked curl; `npm run build` or `tsc --noEmit` validates output; no prose-only tests, (i) AC traceability table. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_24_openapi_typescript_gen_spec.md --type api` before TEST_DESIGN. | None | Spec exit gate PASS; cache fallback unambiguous; example endpoint chosen. | **A1:** Pin `openapi-typescript` major version. **A2:** Generated `paths` keys use literal path strings — document accessor pattern (`paths['/api/registry/model']`). **A3:** Do not delete `src/types/index.ts` in M902-24 — incremental adoption only. |
| **2** | **Test design: script + TypeScript validity** | Test Designer | Spec (Task 1) | Tests under `asset_generation/web/frontend/` or `tests/` per spec: (1) `sync-api-types.sh` exit 0 when cache valid and fetch mocked/skipped, (2) exit non-zero when no cache and fetch fails, (3) exit 0 when fetch succeeds writes cache + output, (4) generated `src/api.types.ts` exists and `tsc --noEmit` passes, (5) optional: assert `paths` contains `/api/registry` or spec-chosen path key. Prefer Node/vitest or bash with `tmp_path`-style isolated dirs — **no** assertions on ticket markdown. Module docstring traces M902-24. | Task 1 | Tests fail before implementation (red). | **R1:** CI may not have backend — tests must use fixture OpenAPI JSON only. |
| **3** | **Test break: adversarial cache and spec corruption** | Test Breaker | Tests (Task 2), spec | Cases: empty cache file, invalid JSON cache, OpenAPI 2.0 stub, huge spec, read-only output dir, partial write, wrong `OPENAPI_URL`, concurrent runs, missing `node_modules`. 4 consecutive runs zero flakes. | Task 2 | +8 cases; determinism. | |
| **4** | **Implementation: deps, script, cache, generated types** | Implementation Agent (Frontend) | Spec; tests (Tasks 2–3) | `npm install -D openapi-typescript`; `scripts/sync-api-types.sh` executable; `scripts/openapi.cached.json` (initial snapshot from backend or hand-crafted minimal fixture matching backend); `src/api.types.ts` generated; `package.json` script `"sync-api-types": "bash scripts/sync-api-types.sh"`; optional `"predev": "npm run sync-api-types"` per spec. All Task 3 tests PASS. | Tasks 1–3 | AC: install, script, exit codes, offline cache path, tsc clean. | **R2:** First run needs one successful capture to seed cache — document in README. |
| **5** | **Implementation: README + example component** | Implementation Agent (Frontend) | Spec; Task 4 output | `asset_generation/web/frontend/README.md` with sync, troubleshooting, example import; update **one** component (spec names file — default `src/api/client.ts` or `ModelRegistryPane.tsx`) to use generated type for one API call (compile-time typed response or `paths` operation). Manual smoke: typed fetch against running backend optional in AC gatekeeper. | Task 4 | AC: docs + example + manual API call pattern evidenced. | Avoid drive-by refactors across all endpoints. |
| **6** | **Static QA** | Code Reviewer | Tasks 4–5 | `npm run build` and `npm test` PASS; eslint on changed TS; shell script uses `set -euo pipefail`. | Task 5 | No blocking findings. | |
| **7** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Evidence matrix: each checkbox → file + test + command output; verify offline sync (backend stopped) + `tsc --noEmit`; git commit/push before COMPLETE; `git mv` ticket to `02_complete/`. | Tasks 1–6 | All AC satisfied. | COMPLETE blocked without push per workflow. |

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| Install `openapi-typescript` | 4 |
| `scripts/sync-api-types.sh` | 1, 4 |
| Generates `src/api.types.ts` | 1, 4 |
| Path + schema exports, readable, tsc valid | 1, 4, 6 |
| `package.json` `sync-api-types` | 4 |
| Dev server up-to-date types | 1, 4 (`predev` or documented workflow) |
| README + example + troubleshooting | 1, 5 |
| Offline generation (cached spec) | 1, 2, 4 |
| `tsc --noEmit` / build passes | 2, 4, 6 |
| Manual API call uses generated type | 5, 7 |

---

## Notes

- **Spec type `api`:** Mutation/read endpoints documented; spec exit gate enforces API sections even though deliverable is frontend tooling.
- **M902-01:** Optional — no `gate_registry.json` entry unless spec adds `openapi_types_check` (default: omit).
- **Commit policy:** Planner assumes **commit** generated `api.types.ts` and `openapi.cached.json` so CI and offline dev work without live backend.
- **Test location:** Prefer colocated `scripts/sync-api-types.test.sh` or Vitest spawning script — Spec Agent chooses one pattern in Task 1.
- **Handoff gates:** Planner writes `todos-latest.json` + `handoff-latest.yaml`; orchestrator runs `run_workflow_transition_gates.py --ticket-id M902-24 --transition planning_to_specification` before Spec Agent.
- **Checkpoint log:** Spec Agent should add `project_board/checkpoints/M902-24/2026-05-21T-planning-run.md` with ambiguity resolutions (optional; not blocking handoff).

---

## Next Steps

**Immediate:** Spec Agent — author `project_board/specs/902_24_openapi_typescript_gen_spec.md` per Task 1.

**Unblocks:** Stronger compile-time safety for asset editor API evolution; reduces manual duplication in `src/types/index.ts` over follow-up tickets.
