# Spec: M902-27 — API Contract Pre-Commit Hook (Asset Editor)

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/27_api_contract_precommit_hook.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-27_api_contract_precommit_hook.md`

**Agent:** Spec Agent

**Date:** 2026-05-21

**Status:** SPECIFICATION

**Revision:** 1

**Spec exit gate type:** `api` (pre-commit enforces FastAPI OpenAPI → TypeScript → contract-test alignment on backend surface changes)

---

## Executive Summary

Add a **Lefthook pre-commit** command `api-contract-check` that runs when staged files match **`asset_generation/web/backend/**/*.py`**. The hook executes a **frozen three-step pipeline**: (1) regenerate `src/api.types.ts` via M902-24 `sync-api-types.sh` (live OpenAPI fetch with **cache fallback**, **no backend auto-start**), (2) `npx tsc --noEmit` in the frontend package, (3) M902-26 contract pytest under `asset_generation/python/tests/api/`. Any step failure exits **1** and blocks the commit. Regenerated `api.types.ts` is included in the commit via **`stage: commit`**.

**In scope:** `.lefthook/scripts/api-contract-check.sh`, `lefthook.yml` registration, frozen stderr templates, failure runbook (Appendix C), `CLAUDE.md` hook section outline, CI tests in `tests/ci/test_api_contract_precommit_hook.py`, manual dry-run evidence protocol (Appendix D).

**Out of scope:** New npm/Python dependencies; duplicating `openapi-typescript` URL logic outside `sync-api-types.sh`; changing M902-26 test semantics; pre-push wiring (full suite stays `py-tests.sh`); backend process management; M902-28 parallel tuning beyond registering the new command under existing `pre-commit.parallel: true`.

**Prerequisites:** M902-24 COMPLETE (`sync-api-types.sh`, `openapi.cached.json`). M902-25 COMPLETE (pilot `response_model`). M902-26 COMPLETE (87 tests, `test_*_contract.py` + `test_api_contract_adversarial.py`). Lefthook installed; `uv sync --extra dev` in `asset_generation/python/`; `npm ci` in `asset_generation/web/frontend/`.

---

## Assumptions and Ambiguity Resolutions

| # | Topic | Resolution | Confidence |
|---|--------|------------|------------|
| A1 | Type regeneration authority | Step 1 **must** invoke `bash asset_generation/web/frontend/scripts/sync-api-types.sh` from repo root (or `npm run sync-api-types` with `cd` to frontend root). Ticket AC `npx openapi-typescript http://localhost:8000/...` is **illustrative only**. | High |
| A2 | Backend unreachable | Sync script cache fallback (exit **0**); hook **must not** start `uvicorn` / `task editor`. Hook stderr **must** include exact line `Backend not reachable; using cached OpenAPI spec` when cache fallback is used (see Req 02). | High |
| A3 | Contract test path | `cd asset_generation/python && uv run pytest tests/api/test_*_contract.py -v` — **not** repo-root `tests/api/`. Glob collects adversarial module `test_api_contract_adversarial.py`. | High |
| A4 | Lefthook glob | **Frozen:** `asset_generation/web/backend/**/*.py` (includes `main.py`, `core/`, routers, models — all affect OpenAPI). Ticket `routers/**/*.py` example is superseded. | High |
| A5 | Staged generated file | `stage: commit` on `api-contract-check` so passing hook auto-stages updated `api.types.ts`. Developer may need `git add` if hook fails mid-run. | High |
| A6 | Performance | Target wall-clock **&lt; 30s** on typical laptop (contract-only pytest, no diff-cover). No hard timeout in hook unless Test Breaker proves flake; optional `timeout` wrapper deferred. | High |
| A7 | Bypass | Document `LEFTHOOK=0 git commit`, `LEFTHOOK_EXCLUDE=api-contract-check git commit`, and `git commit --no-verify`; no new `BLOBERT_*` kill switch. | High |
| A8 | Env reuse | Reuse M902-24 vars: `BLOBERT_OPENAPI_URL`, `BLOBERT_OPENAPI_CACHE`, `BLOBERT_OPENAPI_OUTPUT`, `BLOBERT_SYNC_SKIP_FETCH` (tests only). | High |
| A9 | Test realism | CI tests mock subprocesses / use `BLOBERT_SYNC_SKIP_FETCH=1` — **no live backend** required. | High |

---

## File Path Contract (Normative)

| Artifact | Path | Git policy |
|----------|------|------------|
| Spec (this document) | `project_board/specs/902_27_api_contract_precommit_spec.md` | Committed |
| Hook script | `.lefthook/scripts/api-contract-check.sh` | Committed, executable |
| Lefthook config | `lefthook.yml` | Committed |
| Type sync (delegate) | `asset_generation/web/frontend/scripts/sync-api-types.sh` | Read-only (M902-24) |
| Generated types | `asset_generation/web/frontend/src/api.types.ts` | May change each hook run; `stage: commit` |
| OpenAPI cache | `asset_generation/web/frontend/scripts/fixtures/openapi.cached.json` | Updated when live fetch succeeds |
| Contract suite | `asset_generation/python/tests/api/test_*_contract.py` | Read-only (M902-26) |
| CI hook tests | `tests/ci/test_api_contract_precommit_hook.py` | Committed (create) |
| M902-24 test precedent | `tests/web_frontend/test_sync_api_types_script.py` | Read-only reference |
| Parallel hook tests | `tests/ci/test_parallel_hook_execution.py` | Extend or sibling assertions |
| Runbook (canonical) | Appendix C (this spec) | Committed |
| Runbook (cross-link) | `asset_generation/web/backend/AGENTS.md` § API contract pre-commit | Committed (extend) |
| CLAUDE.md section | `CLAUDE.md` § Hooks / pre-commit | Committed (extend) |
| Dry-run evidence | `project_board/checkpoints/M902-27/<run-id>-dry-run.md` | Committed at Integration/AC |

---

## HTTP API Contract — Protected Surface Freeze (Endpoint Freeze)

The hook does **not** add HTTP endpoints. It enforces alignment for the **existing FastAPI OpenAPI surface** consumed by M902-24/26 when **backend Python** under `asset_generation/web/backend/` changes.

| Authority | URI / artifact | Role in hook |
|-----------|----------------|--------------|
| Live OpenAPI (optional) | `GET http://127.0.0.1:8000/openapi.json` (override `BLOBERT_OPENAPI_URL`) | Step 1 fetch input when backend up |
| Cached OpenAPI (fallback) | `asset_generation/web/frontend/scripts/fixtures/openapi.cached.json` | Step 1 input when fetch fails |
| Generated TS contract | `asset_generation/web/frontend/src/api.types.ts` | Step 1 output; Step 2 input |
| Contract test authority | Live `app.openapi()` in pytest (M902-26) | Step 3 validates same surface |

**Protected path families** (non-exhaustive; full map = M902-26 endpoint table): `/api/health`, `/api/files/*`, `/api/registry/*`, `/api/run/*`, `/api/assets/*`, `/api/meta/*`. Any backend change that alters these operations in OpenAPI **must** pass all three hook steps before commit.

**OpenAPI document endpoint** (`/openapi.json`) is fetch-only for sync; not a `paths` entry in generated client types.

---

## Validation Precedence

### Hook pipeline (aggregate)

| Order | Step | Command (normative) | On failure |
|-------|------|---------------------|------------|
| 0 | Repo root resolution | `ROOT="$(cd "$(dirname "$0")/../.." && pwd)"` | Exit **1** — `api-contract-check: could not resolve repo root` |
| 1 | Type sync | `bash "$ROOT/asset_generation/web/frontend/scripts/sync-api-types.sh"` (cwd irrelevant; script `cd`s to frontend) | Exit **1** immediately; print Step 1 failure block (Req 03) |
| 2 | TypeScript check | `cd "$ROOT/asset_generation/web/frontend" && npx tsc --noEmit` | Exit **1**; passthrough `tsc` stderr; print Step 2 failure block |
| 3 | Contract tests | `cd "$ROOT/asset_generation/python" && uv run pytest tests/api/test_*_contract.py -v` | Exit **1**; passthrough pytest tail; print Step 3 failure block |
| — | Success | All steps exit **0** | Exit **0**; print success footer (Req 03) |

**Step 1 internal precedence** (owned by `sync-api-types.sh`, M902-24 — hook does not reorder):

1. Tooling (`curl`, `node`, `npx`, `package.json`) → sync exit **2**
2. Live fetch (unless `BLOBERT_SYNC_SKIP_FETCH=1`) → on fail, valid cache → exit **0** + cache stderr
3. No valid cache → sync exit **3** or **4** → hook exit **1**
4. `openapi-typescript` generation → sync exit **5** → hook exit **1**

**Cache fallback detection (hook):** After Step 1 exit **0**, if sync stderr contains substring `using cached OpenAPI spec`, hook **must** print to stderr exactly:

```text
Backend not reachable; using cached OpenAPI spec
```

(before Step 2 banner). Sync’s own line may remain; this line is **additive** and mandatory.

**Pre-step prerequisites (hook start):**

| Check | Message if missing | Exit |
|-------|-------------------|------|
| `uv` on PATH | `api-contract-check: uv not found. From asset_generation/python run: uv sync --extra dev` | **1** |
| Frontend `node_modules` | `api-contract-check: run npm ci in asset_generation/web/frontend` | **1** |
| `package.json` in frontend | Same as sync exit **2** | **1** |

Hook **must not** invoke `task editor`, `uvicorn`, or `start.sh` to start the backend.

### Lefthook trigger precedence

| Condition | Hook runs? |
|-----------|------------|
| Staged file matches `asset_generation/web/backend/**/*.py` | **Yes** |
| Only frontend / Godot / other paths staged | **No** (glob skip) |
| `LEFTHOOK=0` | **No** (all hooks) |
| `LEFTHOOK_EXCLUDE=api-contract-check` | **No** (this command) |
| `git commit --no-verify` | **No** |

---

## Failure Taxonomy

| Class | Step | Symptom | Hook exit | User-facing class label |
|-------|------|---------|-----------|-------------------------|
| F1 | 1 | Sync exit **2** (missing tools / package.json) | **1** | `SETUP` |
| F2 | 1 | Sync exit **3** (fetch failed, no cache) | **1** | `OPENAPI_UNAVAILABLE` |
| F3 | 1 | Sync exit **4** (invalid cache JSON) | **1** | `OPENAPI_CACHE_INVALID` |
| F4 | 1 | Sync exit **5** (generation failed) | **1** | `TYPEGEN_FAILED` |
| F5 | 1 | Cache fallback used | **0** (continue) | `CACHE_FALLBACK` (warning only) |
| F6 | 2 | `tsc` type errors | **1** | `TYPE_MISMATCH` |
| F7 | 2 | `tsc` missing / `node_modules` | **1** | `SETUP` |
| F8 | 3 | pytest failures | **1** | `CONTRACT_TEST_FAILED` |
| F9 | 3 | `uv` / venv missing | **1** | `SETUP` |
| F10 | — | Unexpected bash error (`set -euo pipefail`) | **1** | `HOOK_INTERNAL` |

**Status-code mapping (HTTP):** Not applicable at hook layer; contract tests assert HTTP status classes per M902-26. Hook failure is always **process exit 1** (no partial success commit).

---

## Deferred Boundary Statement

- **Not in M902-27:** Pre-push registration of `api-contract-check`; replacing `py-tests.sh`; auto-starting backend; changing `sync-api-types.sh` semantics; narrowing contract tests to routers-only; `Taskfile.yml` target unless Implementation finds parity gap (default: direct bash per ticket AC).
- **M902-28:** New command participates in `pre-commit.parallel: true` with existing linters; no serial `depends_on` unless Integration documents flake.
- **Follow-up:** Optional hard `timeout 30` wrapper; narrowing glob if false positives from `core/` config-only edits prove noisy.

---

## Requirement 01: Lefthook Registration (Frozen)

### 1. Spec Summary

- **Description:** Register `api-contract-check` under `pre-commit.commands` with frozen glob, run line, and `stage: commit`.

- **Constraints:** Do not alter other commands’ globs or `parallel` flag.

- **Assumptions:** Lefthook ≥ version used in repo today; `{staged_files}` not passed to script (hook uses full pipeline, not per-file lint).

- **Scope:** `lefthook.yml` only.

#### Frozen YAML fragment

```yaml
api-contract-check:
  name: API contract (OpenAPI sync, tsc, contract tests)
  glob: "asset_generation/web/backend/**/*.py"
  run: bash .lefthook/scripts/api-contract-check.sh
  stage: commit
```

**Header comment (add to `lefthook.yml` pre-commit block):** One line documenting trigger glob and three steps, pointing to Appendix C runbook path in this spec.

### 2. Acceptance Criteria

- **AC-01.1:** `lefthook.yml` contains command id exactly `api-contract-check`.
- **AC-01.2:** `glob` equals `asset_generation/web/backend/**/*.py` (byte-for-byte).
- **AC-01.3:** `run` equals `bash .lefthook/scripts/api-contract-check.sh`.
- **AC-01.4:** `stage: commit` present.
- **AC-01.5:** `tests/ci/test_api_contract_precommit_hook.py` asserts AC-01.1–AC-01.4 via YAML parse (same pattern as M902-28).

### 3. Risk & Ambiguity Analysis

- **R1:** Glob broader than ticket `routers/**` — intentional (R4); may run on `core/config.py` edits; acceptable.
- **R2:** `stage: commit` re-stages `api.types.ts` even when developer intended manual edit — generated file is auto-only per M902-24 banner.

### 4. Clarifying Questions

- None.

---

## Requirement 02: Hook Script — Three-Step Pipeline

### 1. Spec Summary

- **Description:** Implement `.lefthook/scripts/api-contract-check.sh` with `set -euo pipefail`, repo-root `ROOT`, three steps, frozen banners, exit **0** / **1** only.

- **Constraints:** No duplicated `openapi-typescript` invocation outside sync script. No backend start.

- **Assumptions:** Script invoked from repo root via Lefthook (consistent with `py-tests.sh` pattern).

- **Scope:** Hook script only.

#### Step commands (normative)

```bash
# Step 1
bash "${ROOT}/asset_generation/web/frontend/scripts/sync-api-types.sh"

# Step 2
cd "${ROOT}/asset_generation/web/frontend" && npx tsc --noEmit

# Step 3
cd "${ROOT}/asset_generation/python" && uv run pytest tests/api/test_*_contract.py -v
```

### 2. Acceptance Criteria

- **AC-02.1:** File exists, executable, starts with `set -euo pipefail`.
- **AC-02.2:** Steps run in order 1 → 2 → 3; any non-zero step aborts later steps.
- **AC-02.3:** Aggregate exit **0** only if all three steps exit **0**.
- **AC-02.4:** Aggregate exit **1** on any failure class F1–F10.
- **AC-02.5:** Cache fallback line printed per Validation Precedence when F5 applies.
- **AC-02.6:** Script does not contain `uvicorn`, `task editor`, or `start.sh` invocations (CI grep test).

### 3. Risk & Ambiguity Analysis

- **R1:** Regenerated `api.types.ts` dirty tree if commit fails at Step 2 — developer resets or fixes; runbook covers.
- **R2:** `uv run` cold start — first run may exceed 30s; acceptable for AC gatekeeper manual evidence.

### 4. Clarifying Questions

- None.

---

## Requirement 03: Stderr / Stdout Templates (Frozen)

### 1. Spec Summary

- **Description:** Human-readable console output **must** match templates below (allow variable paths/counts in bracketed placeholders).

- **Constraints:** Labels `[1/3]`, `[2/3]`, `[3/3]` fixed. Success checkmark `✓` and failure cross `✗` as shown (UTF-8).

- **Assumptions:** Terminal UTF-8 support (same as ticket example).

- **Scope:** Hook script stdout/stderr only; sync/pytest passthrough allowed between banners.

#### Opening banner (always)

```text
Running API contract check...
```

#### Step 1 — start

```text
[1/3] Regenerating TypeScript types from OpenAPI spec...
```

#### Step 1 — success

```text
  ✓ Generated: asset_generation/web/frontend/src/api.types.ts
```

#### Step 1 — failure (sync non-zero)

```text
  ✗ ERROR: OpenAPI type sync failed (exit <code>)
  Fix: Start backend (task editor) and re-run, or restore scripts/fixtures/openapi.cached.json
```

#### Step 2 — start

```text
[2/3] Type-checking frontend...
```

#### Step 2 — failure (`tsc` non-zero)

```text
  ✗ ERROR: TypeScript check failed
  Fix: Run `cd asset_generation/web/frontend && npx tsc --noEmit` and update frontend code or regenerate types
```

(Passthrough: full `tsc` stderr between start and failure footer.)

#### Step 3 — start

```text
[3/3] Running contract tests...
```

#### Step 3 — success

```text
  ✓ All contract tests passed (<N> tests)
```

(`<N>` = parsed from pytest summary line or counted exit 0 without parse — Implementation may use `pytest` last line; tests mock **≥1**.)

#### Step 3 — failure

```text
  ✗ ERROR: Contract tests failed
  Hint: Run `cd asset_generation/python && uv run pytest tests/api/test_*_contract.py -v` to debug
```

#### Final — failure (any step)

```text
❌ Commit blocked: <REASON>. Fix and retry.
```

`<REASON>` one of: `OpenAPI type sync failed` | `Type errors found` | `Contract tests failed` | `Setup error` (maps F1–F10).

#### Final — success

```text
✅ API contract check passed
```

### 2. Acceptance Criteria

- **AC-03.1:** CI test captures script output with mocked steps and asserts substrings `[1/3]`, `[2/3]`, `[3/3]`, and final success/failure lines.
- **AC-03.2:** `TYPE_MISMATCH` path includes `tsc` error text in captured output (fixture project or stubbed `tsc`).
- **AC-03.3:** `CONTRACT_TEST_FAILED` path includes Hint line verbatim.

### 3. Risk & Ambiguity Analysis

- Emoji in CI logs — acceptable; optional ASCII fallback **not** required unless Test Breaker finds encoding failure on Windows CI (none today).

### 4. Clarifying Questions

- None.

---

## Requirement 04: Parallel Safety (M902-28)

### 1. Spec Summary

- **Description:** `api-contract-check` runs under `pre-commit.parallel: true` alongside existing commands when multiple globs match.

- **Constraints:** Hook writes only `src/api.types.ts` and may update `scripts/fixtures/openapi.cached.json` on successful live fetch — not staged Python coverage artifacts.

- **Assumptions:** No concurrent hook mutates `api.types.ts` (true today).

- **Scope:** Read-only analysis + optional matrix row in Implementation PR notes.

#### Normative pair verdicts (add to M902-28-style reasoning)

| Pair | Verdict | Rationale |
|------|---------|-----------|
| `api-contract-check` ∥ `py-review` / `py-parse` / other `py-*` | **SAFE** | Linters read staged files; hook writes frontend artifacts |
| `api-contract-check` ∥ `gd-*` | **SAFE** | Disjoint globs |
| `api-contract-check` ∥ self | **N/A** | Single instance |

### 2. Acceptance Criteria

- **AC-04.1:** No new `parallel: false` on pre-commit.
- **AC-04.2:** Optional test: godot/py isolation patterns unchanged (no regression to M902-28 tests).

### 3. Risk & Ambiguity Analysis

- Concurrent `openapi.cached.json` write + read — low risk; same hook single process.

### 4. Clarifying Questions

- None.

---

## Requirement 05: Documentation — CLAUDE.md Section Outline

### 1. Spec Summary

- **Description:** Add subsection under existing **Hooks / Pre-commit** in `CLAUDE.md` with the following **mandatory bullets** (Implementation copies prose; Spec freezes outline only).

- **Scope:** `CLAUDE.md` only.

#### Required bullets (outline)

1. **Trigger:** `api-contract-check` runs on pre-commit when staged files match `asset_generation/web/backend/**/*.py`.
2. **Steps:** sync-api-types → `tsc --noEmit` → contract pytest (`tests/api/test_*_contract.py`).
3. **Backend optional:** If :8000 down, hook uses cached OpenAPI and prints warning; does not start backend.
4. **Fix type errors:** `cd asset_generation/web/frontend && npx tsc --noEmit`.
5. **Fix contract tests:** `cd asset_generation/python && uv run pytest tests/api/test_*_contract.py -v`.
6. **Bypass:** `LEFTHOOK=0`, `LEFTHOOK_EXCLUDE=api-contract-check`, or `--no-verify` — temporary only; must pass hook before merge.
7. **Prerequisites:** `uv sync --extra dev`, `npm ci` in frontend.
8. **Runbook:** Link to `project_board/specs/902_27_api_contract_precommit_spec.md` Appendix C and `asset_generation/web/backend/AGENTS.md`.

### 2. Acceptance Criteria

- **AC-05.1:** `CLAUDE.md` contains heading or bullet group identifiable as API contract pre-commit with all eight bullets.
- **AC-05.2:** No invented `BLOBERT_HOOKS_*` env vars.

### 3. Risk & Ambiguity Analysis

- None material.

### 4. Clarifying Questions

- None.

---

## Requirement 06: Test Strategy (Behavioral)

### 1. Spec Summary

- **Description:** Executable tests verify hook script and Lefthook config — **not** ticket markdown prose.

- **Assumptions:** Test Designer implements red tests before Implementation; Test Breaker extends per execution plan Task 3.

- **Scope:** `tests/ci/test_api_contract_precommit_hook.py` (primary); may reuse patterns from `tests/web_frontend/test_sync_api_types_script.py`.

#### Minimum scenarios

| ID | Scenario | Expected |
|----|----------|----------|
| H1 | Mock Step 1–3 success | Hook exit **0**; success footer |
| H2 | Mock sync failure | Exit **1**; Step 1 failure template |
| H3 | Mock `tsc` failure | Exit **1**; `TYPE_MISMATCH` reason |
| H4 | Mock pytest failure | Exit **1**; Hint line present |
| H5 | Sync success with cache fallback stderr | Exit **0**; exact warning line present |
| H6 | `lefthook.yml` registration | glob, run, `stage: commit` |
| H7 | Script forbids backend start | No `uvicorn` / `task editor` in script text |
| H8 | `BLOBERT_SYNC_SKIP_FETCH=1` in test env | Deterministic Step 1 without network |

**Constraints:**

- Module docstring cites M902-27 and this spec path.
- No test asserts content of `27_api_contract_precommit_hook.md`.
- Do not require live backend in CI.

### 2. Acceptance Criteria

- **AC-06.1:** ≥8 scenarios H1–H8 (or equivalent) exist and fail before implementation.
- **AC-06.2:** Tests use subprocess and/or mock — not documentation grep of spec file as sole assertion.

### 3. Risk & Ambiguity Analysis

| Risk | Mitigation |
|------|------------|
| Slow pytest in hook test | Mock `uv run pytest` for H1–H4 |
| Flaky network | H8 + cache fixtures |

### 4. Clarifying Questions

- None.

---

## Requirement 07: Manual Dry-Run Evidence (Frozen)

### 1. Spec Summary

- **Description:** After implementation, record manual evidence in `project_board/checkpoints/M902-27/<run-id>-dry-run.md` per ticket Testing AC.

- **Assumptions:** Local dev has frontend deps; Python venv via `uv`.

- **Scope:** Human/Integration checkpoint only — not CI pytest.

#### Required scenarios

| ID | Scenario | Expected commit outcome |
|----|----------|-------------------------|
| D1 | Add **required** field to a pilot response model + regenerate types without fixing frontend | `git commit` **blocked**; `tsc` failure (F6) |
| D2 | Change field type `string` → `integer` in OpenAPI-exposed model | Commit **blocked**; `tsc` failure |
| D3 | Remove field from model | Commit **blocked**; `tsc` failure |
| D4 | `git commit --no-verify` after D1 failure | Commit **succeeds**; document that hook did not run |
| D5 | Fix frontend + re-commit after D1 | Commit **succeeds**; hook exit **0** |

#### Evidence format (each scenario)

- Command(s) run (verbatim)
- Exit code of hook (`lefthook run pre-commit` or commit attempt)
- **Verbatim** stderr/stdout excerpt (≥10 lines or full output if shorter)
- `git status` snippet showing staged files
- Date, machine, `git rev-parse --short HEAD`

### 2. Acceptance Criteria

- **AC-07.1:** Checkpoint file exists with D1–D5 rows populated.
- **AC-07.2:** D1–D3 show hook exit **1** with `Type errors found` or `tsc` output.
- **AC-07.3:** D4 shows bypass succeeded.
- **AC-07.4:** D5 shows hook exit **0**.

### 3. Risk & Ambiguity Analysis

- Backend down during D1 — use cache fallback (F5); tsc may still fail if types changed vs frontend — acceptable.

### 4. Clarifying Questions

- None.

---

## Appendix C — Failure Runbook (Canonical)

### Type mismatch (`TYPE_MISMATCH` / `tsc` failed)

1. Run `cd asset_generation/web/frontend && npx tsc --noEmit`.
2. Fix frontend call sites to match `src/api.types.ts`, **or** revert backend OpenAPI change.
3. Re-run `npm run sync-api-types` if backend was up during fix.
4. `git add` frontend + generated types; commit again.

### Backend unreachable (`CACHE_FALLBACK`)

1. Warning is expected if `task editor` is not running.
2. Hook still runs `tsc` + contract tests against **cached** spec.
3. If types are stale vs your backend edits, start backend (`task editor`), run `npm run sync-api-types`, commit cache + `api.types.ts`.
4. Do **not** rely on cache-only for large router refactors without refreshing cache.

### OpenAPI unavailable (`OPENAPI_UNAVAILABLE` / exit 3)

1. Start backend **or** restore valid `scripts/fixtures/openapi.cached.json` from main.
2. Run `npm run sync-api-types` once successfully; commit cache.

### Contract test failed (`CONTRACT_TEST_FAILED`)

1. `cd asset_generation/python && uv run pytest tests/api/test_*_contract.py -v`.
2. See M902-26 runbook in `asset_generation/web/backend/AGENTS.md`.
3. Fix backend response shape or test mocks per failure.

### Setup errors (`SETUP`)

1. `cd asset_generation/python && uv sync --extra dev`
2. `cd asset_generation/web/frontend && npm ci`

### Bypass (temporary)

- `LEFTHOOK_EXCLUDE=api-contract-check git commit -m "..."`
- `LEFTHOOK=0 git commit ...`
- `git commit --no-verify`

**Policy:** Bypass must not land on shared main without follow-up PR that passes hook. CI pre-push `py-tests.sh` still runs broader suite.

---

## Appendix D — Developer Workflow (Normative)

1. Edit backend Python under `asset_generation/web/backend/`.
2. `git add` changed files.
3. `git commit` → Lefthook runs `api-contract-check` when glob matches.
4. Hook regenerates `api.types.ts` (may auto-stage via `stage: commit`).
5. If `tsc` fails → fix frontend → `git add` → retry commit.
6. If contract tests fail → fix per Appendix C → retry.

---

## Acceptance Criteria Mapping

| Ticket AC | Spec requirement | Verification |
|-----------|------------------|--------------|
| `.lefthook/scripts/api-contract-check.sh` | Req 02 | File + H1–H5 tests |
| Regenerate TS types | Req 02 Step 1, A1 | Delegates to sync script |
| `tsc --noEmit` | Req 02 Step 2 | H3, D1–D3 |
| Contract pytest | Req 02 Step 3, A3 | H4, pytest collect |
| `lefthook.yml` registration | Req 01 | H6 |
| Backend not running → cache + warning | Validation Precedence, Req 03, H5 | test + manual |
| Error output clarity | Req 03 | H1–H4 output assertions |
| Runbook | Appendix C, AC-05 | Path + AGENTS.md link |
| Bypass docs | Appendix C, Req 05 | CLAUDE.md |
| CLAUDE.md section | Req 05 | Review |
| Dry-run 3 scenarios | Req 07 D1–D3 | Checkpoint log |
| Bypass `--no-verify` | Req 07 D4 | Checkpoint log |
| Fix + retry | Req 07 D5 | Checkpoint log |
| Automated testing | Req 06 | `tests/ci/test_api_contract_precommit_hook.py` |

---

## Risk & Ambiguity Analysis (Cross-Cutting)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Large `api.types.ts` diff noise | High | Review fatigue | Document `stage: commit`; regen only when backend staged |
| Cache/backend drift | Medium | False green commit | Warning on F5; contract tests use live `app.openapi()` |
| Hook &gt; 30s | Medium | Dev friction | Contract-only pytest; no diff-cover |
| First-time clone missing deps | Medium | F1/F7/F9 | Setup messages; Appendix C |
| Contributor bypasses habitually | Low | Main drift | Policy in Appendix C; pre-push full suite |

---

## Clarifying Questions

- None — resolved in Assumptions A1–A9 and planning resolutions R1–R8.

---

## Spec → Test Designer Handoff Notes

- Spec exit gate: `python ci/scripts/spec_completeness_check.py project_board/specs/902_27_api_contract_precommit_spec.md --type api`
- Orchestrator transition: `python ci/scripts/run_workflow_transition_gates.py --ticket-id M902-27 --transition spec_to_test_design`
- Primary test module: `tests/ci/test_api_contract_precommit_hook.py`
- Reuse M902-24 subprocess patterns from `tests/web_frontend/test_sync_api_types_script.py` for sync mocking
- Contract test collection glob: `tests/api/test_*_contract.py` (includes adversarial module)
