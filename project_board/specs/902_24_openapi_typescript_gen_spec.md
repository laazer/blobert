# Spec: M902-24 — OpenAPI → TypeScript Generation (Asset Editor Frontend)

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/24_openapi_typescript_generation.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-24_openapi_typescript_generation.md`

**Agent:** Spec Agent

**Date:** 2026-05-21

**Status:** SPECIFICATION

**Revision:** 1

**Spec exit gate type:** `api` (tooling consumes FastAPI OpenAPI HTTP contract; mutation/read paths must remain type-stable)

---

## Executive Summary

Add **`openapi-typescript@7.13.0`** to the asset editor frontend (`asset_generation/web/frontend/`), a **`sync-api-types.sh`** pipeline that fetches the FastAPI OpenAPI document (or falls back to a committed cache), generates **`src/api.types.ts`**, and wire **`npm run sync-api-types`** plus **`predev`** so local dev starts with compile-time-safe API types. Document usage in **`asset_generation/web/frontend/README.md`** and demonstrate **`paths['/api/health']`** typing in one real module.

**In scope:** Dev dependency pin, shell sync script, fixture cache, generated types committed, `package.json` scripts, README, example health helper, behavioral tests (script exit codes + `tsc --noEmit`).

**Out of scope:** Replacing all manual types in `src/types/index.ts`; deleting legacy types; auto-run on `npm install`; new CI gate registry entries; migrating every `client.ts` endpoint in this ticket.

**Prerequisites:** FastAPI app at `asset_generation/web/backend/main.py` serves OpenAPI 3.x at `/openapi.json` (default). Node ≥18 per `package.json` `engines`. Vite proxy `/api` → `127.0.0.1:8000` unchanged.

---

## Assumptions and Ambiguity Resolutions

| # | Topic | Resolution | Confidence |
|---|--------|------------|------------|
| A1 | OpenAPI URL env var | **`BLOBERT_OPENAPI_URL`** only (no `OPENAPI_URL` alias). Default `http://127.0.0.1:8000/openapi.json`. | High |
| A2 | Cache path | **`asset_generation/web/frontend/scripts/fixtures/openapi.cached.json`** (committed). Updated on every successful live fetch. | High |
| A3 | Generated output | **`asset_generation/web/frontend/src/api.types.ts`** — committed; banner comment marks auto-generated. | High |
| A4 | `openapi-typescript` version | Pin **`7.13.0`** exact in `devDependencies` (lockfile updated in implementation). CLI: default flags only (`openapi-typescript <input> -o <output>`). | High |
| A5 | Dev server freshness | Add **`"predev": "npm run sync-api-types"`** so `npm run dev` refreshes types when backend is up; offline dev uses cache (see offline rules). | High |
| A6 | Example endpoint | **`GET /api/health`** — stable, minimal response `{"status":"ok"}` in `main.py`; example uses `paths['/api/health']`. | High |
| A7 | Legacy manual types | **`src/types/index.ts`** and existing `client.ts` imports remain; M902-24 adds parallel generated types only. | High |
| A8 | Fetch tooling | Script requires **`curl`** on PATH (macOS/Linux CI/dev). No `wget` fallback required. | High |
| A9 | Test realism | Tests use **fixture OpenAPI JSON** and mocked fetch — **no live backend** required in CI. | High |

---

## File Path Contract (Normative)

All paths are repo-relative unless noted. Working directory for script and npm scripts: **`asset_generation/web/frontend/`**.

| Artifact | Path | Git policy |
|----------|------|------------|
| Sync script | `asset_generation/web/frontend/scripts/sync-api-types.sh` | Committed, executable (`chmod +x`) |
| Cached OpenAPI | `asset_generation/web/frontend/scripts/fixtures/openapi.cached.json` | Committed; refresh on successful fetch |
| Generated types | `asset_generation/web/frontend/src/api.types.ts` | Committed; regen when backend routes change |
| Example consumer | `asset_generation/web/frontend/src/api/healthCheck.ts` | Committed (new) |
| Frontend README | `asset_generation/web/frontend/README.md` | Committed (create if absent) |
| Package manifest | `asset_generation/web/frontend/package.json` | Committed (`devDependencies`, `scripts`) |
| Backend OpenAPI source | `asset_generation/web/backend/main.py` (+ routers) | Read-only for this ticket |
| Behavioral tests | `asset_generation/web/frontend/scripts/sync-api-types.test.sh` **or** `tests/ci/test_openapi_typescript_sync.py` | Spec mandates **one** location; implementer picks; module docstring traces M902-24 |
| Spec (this document) | `project_board/specs/902_24_openapi_typescript_gen_spec.md` | Committed |

**Directories to create:** `scripts/`, `scripts/fixtures/`, `src/api/` (if missing).

---

## HTTP API Contract — Endpoint Freeze

Type generation must reflect the **live FastAPI OpenAPI document** at fetch time. The following endpoints are **frozen for M902-24 example and regression tests** (full `paths` map still generated from complete spec):

| Method | URI | Purpose | Example response shape (200) |
|--------|-----|---------|------------------------------|
| GET | `/api/health` | Liveness probe | `{ "status": "ok" }` (string literal) |
| GET | `/openapi.json` | OpenAPI document (not a `paths` entry in generated client types; fetch URL only) | OpenAPI 3.x JSON object |

**Full surface:** Generated `paths` must include **all** operations present in the cached/live OpenAPI document (registry, files, assets, meta, run routers, etc.). Tests may assert presence of **`/api/health`** and at least one registry path (e.g. **`/api/registry/model`**) as smoke keys — not an exhaustive path list in tests.

**Deferred boundary:** Changing backend route shapes is allowed in other tickets; this ticket only requires re-running `npm run sync-api-types` and committing updated `api.types.ts` + cache when routes change. No backend code changes in M902-24.

---

## Validation Precedence

When `sync-api-types.sh` can fail for multiple reasons, checks run in this order; **first fatal failure determines exit code**:

| Order | Check | On failure |
|-------|--------|------------|
| 1 | CWD is frontend package root (`package.json` exists) | Exit **2** |
| 2 | `curl` executable available | Exit **2** |
| 3 | `node` / `npx` available | Exit **2** |
| 4 | Live fetch attempted (unless `BLOBERT_SYNC_SKIP_FETCH=1` in tests) | See fetch branch |
| 5 | Spec input is valid JSON object with `"openapi"` key (3.x) | Exit **4** (cache) or **3** (no cache) |
| 6 | `npx openapi-typescript@7.13.0` generation | Exit **5** |
| 7 | Output file written and non-empty | Exit **5** |

**Fetch branch precedence:**

1. If live fetch succeeds (HTTP 200, body parses as JSON object) → write cache → generate → exit **0**.
2. If live fetch fails → if valid cache exists → stderr warning → generate from cache → exit **0**.
3. If live fetch fails → no cache or invalid cache → exit **3** (no cache) or **4** (invalid cache).

**TypeScript validation precedence (post-generation):**

1. `npx tsc --noEmit` in frontend root must pass including new `api.types.ts` and `healthCheck.ts`.
2. `npm run build` must pass (includes `tsc && vite build` per existing `package.json`).

---

## Failure Taxonomy

### `sync-api-types.sh` exit codes

| Code | Meaning | Stderr must include |
|------|---------|---------------------|
| **0** | Success: types generated from live spec and cache updated, **or** from valid cache after fetch failure (offline mode) | On cache fallback: substring `using cached OpenAPI` |
| **1** | Unexpected internal error (`set -e` trap, unhandled failure) | `unexpected error` or re-raised command |
| **2** | Usage / environment: missing `curl`, `node`, `npx`, or not in frontend directory | Which prerequisite failed |
| **3** | Fetch failed and **no** usable cache file | `fetch failed` and `no cache` |
| **4** | Cache file present but unreadable or not valid OpenAPI JSON | `invalid cache` |
| **5** | `openapi-typescript` failed or output missing/empty | `generation failed` |

### TypeScript / build failures (downstream)

| Symptom | Typical cause | Remediation (README) |
|---------|---------------|----------------------|
| `tsc` errors on `paths[...]` | Stale `api.types.ts` | Start backend, `npm run sync-api-types`, commit regen |
| Missing path key | Backend added route; types not synced | Same as above |
| `fetch failed` + exit 3 | No backend and no committed cache | Seed cache once with backend up, or copy fixture from repo |

---

## Requirement 01: `openapi-typescript` Dependency Pin

### 1. Spec Summary

- **Description:** Add dev dependency **`openapi-typescript`** version **`7.13.0`** (exact semver in `package.json`; lockfile updated).
- **Constraints:** Dev dependency only; no runtime import of `openapi-typescript` in app bundle.
- **Assumptions:** npm is package manager for frontend.
- **Scope:** `asset_generation/web/frontend/package.json` + lockfile.

### 2. Acceptance Criteria

- **AC-01.1:** `package.json` `devDependencies` contains `"openapi-typescript": "7.13.0"`.
- **AC-01.2:** `npm install` in frontend root installs CLI invocable as `npx openapi-typescript`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Major version drift | Breaking CLI flags | Exact pin; upgrade via follow-up ticket |

### 4. Clarifying Questions

- None.

---

## Requirement 02: `sync-api-types.sh` — Fetch, Cache, Generate

### 1. Spec Summary

- **Description:** Bash script at `scripts/sync-api-types.sh` implements fetch → validate → cache → generate pipeline.

- **Environment variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `BLOBERT_OPENAPI_URL` | `http://127.0.0.1:8000/openapi.json` | Live OpenAPI JSON URL |
| `BLOBERT_SYNC_SKIP_FETCH` | unset (fetch enabled) | When `1`, skip live fetch and use cache only (tests) |
| `BLOBERT_OPENAPI_CACHE` | `scripts/fixtures/openapi.cached.json` | Override cache path (tests only) |
| `BLOBERT_OPENAPI_OUTPUT` | `src/api.types.ts` | Override output path (tests only) |

- **Script requirements:**
  - `set -euo pipefail`
  - Resolve paths relative to script directory / frontend root per implementation (document in README)
  - **Fetch:** `curl --fail --show-error --silent --max-time 5` to `BLOBERT_OPENAPI_URL`
  - **Validate input:** JSON object with string `"openapi"` field matching `^3\.`
  - **Cache write:** On successful fetch, atomically write pretty-printed or minified JSON to cache path (implementation choice; must be valid JSON)
  - **Generate:** `npx openapi-typescript@7.13.0 "$SPEC_FILE" -o "$OUTPUT"` where `SPEC_FILE` is temp copy of live or cache JSON
  - **Banner:** Prepend generated file with comment block: `// AUTO-GENERATED by scripts/sync-api-types.sh — do not edit`
  - Exit codes per **Failure Taxonomy** table

- **Offline fallback rules (normative):**
  1. **Primary:** Live fetch succeeds → update `scripts/fixtures/openapi.cached.json` → generate → exit **0**.
  2. **Fallback:** Live fetch fails (connection refused, timeout, non-200, empty body) → if cache exists and validates as OpenAPI 3.x JSON → print warning to stderr → generate from cache → exit **0**.
  3. **Fail-closed:** Fetch fails and cache missing → exit **3**. Fetch fails and cache invalid → exit **4**.
  4. **Tests:** May set `BLOBERT_SYNC_SKIP_FETCH=1` to force cache-only path without network.

- **Assumptions:** Initial implementation seeds `openapi.cached.json` from one successful backend capture or minimal fixture that includes `/api/health` and OpenAPI 3.0.3 metadata.

- **Scope:** `scripts/sync-api-types.sh` only.

### 2. Acceptance Criteria

- **AC-02.1:** With backend running and reachable at default URL, script exits **0** and updates cache mtime/content.
- **AC-02.2:** With backend stopped and valid committed cache, script exits **0** and stderr contains `using cached OpenAPI`.
- **AC-02.3:** With backend stopped and cache removed, script exits **3**.
- **AC-02.4:** With corrupt cache (invalid JSON), script exits **4**.
- **AC-02.5:** With `openapi-typescript` forced to fail (test mock), script exits **5**.
- **AC-02.6:** Generated `src/api.types.ts` exports `paths` interface (and `components`, `operations` per openapi-typescript defaults).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stale cache merged to main | Wrong types until regen | README: regen after backend API changes |
| curl absent on Windows dev | Script exit 2 | Document macOS/Linux; WSL curl |

### 4. Clarifying Questions

- None.

---

## Requirement 03: `package.json` Scripts and Build Integration

### 1. Spec Summary

- **Description:** Wire npm scripts for manual and automatic sync before dev server.

- **Required scripts:**

```json
"sync-api-types": "bash scripts/sync-api-types.sh",
"predev": "npm run sync-api-types"
```

- **Constraints:** Do **not** add `postinstall` sync (manual + predev only).
- **Assumptions:** `npm run dev` remains entry for Vite.
- **Scope:** `package.json` scripts section.

### 2. Acceptance Criteria

- **AC-03.1:** `npm run sync-api-types` invokes bash script from frontend root and propagates exit code.
- **AC-03.2:** `npm run dev` runs sync first via `predev` (npm lifecycle).

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| predev slows dev when backend down | stderr warning only; still starts if cache valid | Offline rules |

### 4. Clarifying Questions

- None.

---

## Requirement 04: Generated Module Shape and Type Consumption

### 1. Spec Summary

- **Description:** `src/api.types.ts` is the single generated module. Consumers import:

```typescript
import type { paths, components, operations } from "./api.types";
```

- **Path accessor pattern (required in docs and example):**

```typescript
type HealthGet = paths["/api/health"]["get"];
type HealthOk = HealthGet["responses"][200]["content"]["application/json"];
```

- **Constraints:**
  - Keys are string literal path keys on `paths` (e.g. `"/api/health"`).
  - Do not re-export generated types from `src/types/index.ts` in M902-24.
- **Assumptions:** openapi-typescript 7.x default output matches project TS 5.5.
- **Scope:** Generated file + one example module.

### 2. Acceptance Criteria

- **AC-04.1:** `paths["/api/health"]` exists after generation against current backend spec.
- **AC-04.2:** `npx tsc --noEmit` passes with `strict` settings from `tsconfig.json`.
- **AC-04.3:** `npm run build` passes.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Deep indexed access errors | TS2589 | Example uses shallow aliases |

### 4. Clarifying Questions

- None.

---

## Requirement 05: Example Component — `paths['/api/health']`

### 1. Spec Summary

- **Description:** Add `src/api/healthCheck.ts` exporting:

```typescript
import type { paths } from "../api.types";

export type HealthResponse =
  paths["/api/health"]["get"]["responses"][200]["content"]["application/json"];

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json() as Promise<HealthResponse>;
}
```

- **Constraints:** No requirement to wire into UI in M902-24; module must compile and be importable.
- **Assumptions:** Vite dev proxy serves `/api/health` → backend.
- **Scope:** One new file only; no drive-by refactors in `client.ts`.

### 2. Acceptance Criteria

- **AC-05.1:** `healthCheck.ts` imports only from `api.types` for the response type.
- **AC-05.2:** `tsc --noEmit` includes `healthCheck.ts` without errors.
- **AC-05.3:** Type of `fetchHealth()` return is assignable to `{ status: string }` per backend.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend changes health schema | Compile break until sync | Document regen workflow |

### 4. Clarifying Questions

- None.

---

## Requirement 06: Frontend README Documentation

### 1. Spec Summary

- **Description:** Create or update `asset_generation/web/frontend/README.md` with sections:

1. **Syncing API types** — run `npm run sync-api-types` after backend route/schema changes; when backend is running vs offline cache.
2. **Environment** — `BLOBERT_OPENAPI_URL` override example.
3. **Example** — import `paths` / `healthCheck` snippet (abbreviated).
4. **Troubleshooting** — table: fetch failed + no cache (exit 3), invalid cache (4), generation failed (5), `tsc` errors after regen, stale cache warning text.

- **Assumptions:** English prose; link to root `README.md` optional one-liner only.
- **Scope:** Frontend README only.

### 2. Acceptance Criteria

- **AC-06.1:** README documents `npm run sync-api-types` and `predev` behavior.
- **AC-06.2:** README documents `BLOBERT_OPENAPI_URL` default `http://127.0.0.1:8000/openapi.json`.
- **AC-06.3:** README includes troubleshooting for backend-down + cache path `scripts/fixtures/openapi.cached.json`.

### 3. Risk & Ambiguity Analysis

- None material.

### 4. Clarifying Questions

- None.

---

## Requirement 07: Test Strategy (Behavioral)

### 1. Spec Summary

- **Description:** Executable tests verify script contract and TypeScript validity — **not** ticket markdown prose.

- **Minimum scenarios:**

| ID | Scenario | Expected |
|----|----------|----------|
| T1 | Valid cache, fetch skipped/fails | Exit **0**, `api.types.ts` exists |
| T2 | No cache, fetch fails | Exit **3** |
| T3 | Fetch succeeds (mock curl) | Exit **0**, cache written |
| T4 | Invalid cache JSON | Exit **4** |
| T5 | `npx tsc --noEmit` after generation | Exit **0** |
| T6 | `paths` contains `/api/health` key (grep or TS const) | Present |

- **Constraints:**
  - Use temp directories or env overrides (`BLOBERT_OPENAPI_CACHE`, `BLOBERT_OPENAPI_OUTPUT`) — do not mutate repo cache in tests without restore.
  - Module docstring references M902-24 and this spec path.
- **Assumptions:** Test Breaker adds adversarial cases (empty cache, OpenAPI 2.0, read-only dir, etc.) per execution plan Task 3.
- **Scope:** Tests only; implementation in Test Designer phase.

### 2. Acceptance Criteria

- **AC-07.1:** At least 5 behavioral cases T1–T5 (or equivalent) exist and fail before implementation.
- **AC-07.2:** No test asserts content of `24_openapi_typescript_generation.md`.

### 3. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| CI without curl | Tests mock script internals or skip fetch | Fixture-only path |

### 4. Clarifying Questions

- None.

---

## Acceptance Criteria Mapping

Maps ticket checkboxes → spec requirements → verification command/evidence.

| Ticket AC | Spec requirement | Verification evidence |
|-----------|------------------|------------------------|
| Install `openapi-typescript` | Req 01 | `package.json` devDependency `7.13.0`; `npm ls openapi-typescript` |
| Create `scripts/sync-api-types.sh` | Req 02 | File exists, executable; T1–T4 tests |
| Fetches from backend | Req 02 | T3 with mock/live; default `BLOBERT_OPENAPI_URL` |
| Generates `src/api.types.ts` | Req 02, 04 | File exists post-script; T5 `tsc` |
| Exit 0 success / non-zero failure | Req 02, Failure Taxonomy | T1–T4 exit code assertions |
| Path types + schemas exported | Req 04 | `paths`, `components` in generated file; T6 |
| Readable, usable in components | Req 04, 05 | `healthCheck.ts` compiles |
| No syntax errors (`tsc`) | Req 04 | `npx tsc --noEmit`; `npm run build` |
| `package.json` `sync-api-types` | Req 03 | Script entry present |
| Dev server up-to-date types | Req 03 | `predev` runs sync; README |
| README how-to + example + troubleshooting | Req 06 | `frontend/README.md` sections |
| Offline generation (cached spec) | Req 02 offline rules | T1 backend stopped; AC gate exit 0 + stderr |
| `tsc --noEmit` passes | Req 04, 07 T5 | CI/local command output |
| Manual API call uses generated type | Req 05 | `fetchHealth` return type from `paths['/api/health']` |

---

## Deferred Boundary Statement

- **Not in M902-24:** Migrating `src/api/client.ts` to generated types for registry/files/assets; `postinstall` hook; `gate_registry.json` entry; changing backend OpenAPI metadata; Windows-native curl-free script.
- **Follow-up:** Incremental replacement of `src/types/index.ts` duplicates per endpoint family.

---

## Risk & Ambiguity Analysis (Cross-Cutting)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Large generated file churn in PRs | Medium | Review noise | Commit policy documented; regen only when API changes |
| Cache/backend drift | Medium | Silent wrong types | stderr on cache fallback; README |
| openapi-typescript breaking change on pin bump | Low | Build break | Exact pin 7.13.0 |
| First-time clone without cache | Medium | Exit 3 until seed | Commit seeded `openapi.cached.json` in implementation |

---

## Clarifying Questions

- None — resolved in Assumptions A1–A9.

---

## Spec → Test Designer Handoff Notes

- Spec exit gate: `python ci/scripts/spec_completeness_check.py project_board/specs/902_24_openapi_typescript_gen_spec.md --type api`
- Orchestrator transition: `python ci/scripts/run_workflow_transition_gates.py --ticket-id M902-24 --transition spec_to_test_design`
- Prefer **bash + temp dir** tests colocated with script unless Python subprocess pattern is already standard in `tests/ci/` for npm projects.
