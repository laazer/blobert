# Execution Plan: M902-27 API Contract Pre-Commit Hook

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/27_api_contract_precommit_hook.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-21  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-27/` (`todos-latest.json`, `handoff-latest.yaml`)

---

## Executive Summary

**Objective:** Add a Lefthook pre-commit command that, when backend API surface changes are staged, (1) regenerates `src/api.types.ts` via the M902-24 sync pipeline (live OpenAPI with cached fallback), (2) runs `tsc --noEmit` on the frontend, and (3) runs the M902-26 OpenAPI contract pytest suite — blocking the commit on any failure.

**Scope:**

| Layer | Deliverable |
|-------|-------------|
| Hook script | `.lefthook/scripts/api-contract-check.sh` — three steps, exit 0/1, structured stderr |
| Lefthook | `pre-commit.commands.api-contract-check` with backend glob + `stage: commit` |
| Type sync | Delegate to `asset_generation/web/frontend/scripts/sync-api-types.sh` (not duplicate `npx openapi-typescript` URL logic) |
| Contract tests | `cd asset_generation/python && uv run pytest tests/api/test_*_contract.py -v` (87 tests today) |
| Docs | Runbook (spec path); `CLAUDE.md` hook section; `lefthook.yml` header comment |
| Verification | CI tests for script + lefthook registration; manual dry-run matrix per ticket AC |

**Out of scope:** New npm/Python dependencies; replacing M902-24 script; changing contract test semantics (M902-26); pre-push wiring (stays on `py-tests.sh` full suite); M902-28 parallel tuning (already `parallel: true` on pre-commit).

**Prerequisites:** M902-24, M902-25, M902-26 in `02_complete/`; Lefthook installed; `uv` + frontend `node_modules` on PATH for dev machines.

**Estimated Effort:** 7–9 agent runs (see table below).

---

## Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | Freeze glob, step contracts, stderr templates, spec exit `--type api` |
| Test design | Test Designer | 1 | Shell + `tests/ci/` lefthook config tests; mocked backend/curl |
| Test break | Test Breaker | 1 | Backend down, dirty `api.types.ts`, partial failures, timeout |
| Implementation | Implementation Agent (Generalist) | 1–2 | Script, lefthook, CLAUDE.md, runbook |
| Static QA | Code Reviewer | 1 | Shellcheck, pytest CI module, manual dry-run evidence |
| Learning | Learning Agent | 1 | LEARNINGS.md entry |
| AC gatekeeper | AC Gatekeeper | 1 | AC matrix; commit/push before COMPLETE |

**Total:** 7–9 runs

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-27? | Notes |
|------------|----------------|-----------------|-------|
| **M902-24** OpenAPI → TypeScript | `02_complete/24_openapi_typescript_generation.md` | **No** (satisfied) | `sync-api-types.sh`, `openapi.cached.json`, `src/api.types.ts` |
| **M902-25** Pydantic + Zod pilot | `02_complete/25_pydantic_zod_dual_validation.md` | **No** (satisfied) | Richer OpenAPI for pilot routes |
| **M902-26** API contract testing | `02_complete/26_api_contract_testing.md` | **No** (satisfied) | 87 tests under `asset_generation/python/tests/api/` |
| **M902-28** Parallel hooks | `02_complete/28_parallel_hook_execution.md` | **No** (satisfied) | `pre-commit.parallel: true` — new hook runs concurrently when glob matches |
| Lefthook | `lefthook.yml` | **No** (satisfied) | Eight pre-commit commands today |
| Spec stub | `project_board/specs/902_27_api_contract_precommit_spec.md` | Soft | **Absent** — Spec Agent creates in Task 1 |

**Umbrella:** No.

**Cycles / WARN:** None.

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Ticket AC | `.../01_in_progress/27_api_contract_precommit_hook.md` | Source requirements |
| Sync pipeline (reuse) | `asset_generation/web/frontend/scripts/sync-api-types.sh` | Step 1 authority; cache fallback + exit codes 3–5 |
| Generated types | `asset_generation/web/frontend/src/api.types.ts` | May change on hook run → `stage: commit` |
| Contract suite | `asset_generation/python/tests/api/test_*_contract.py` | 87 collected tests |
| Contract runbook | `asset_generation/web/backend/AGENTS.md` (M902-26) | Cross-link from hook runbook |
| Lefthook pattern | `lefthook.yml`, `.lefthook/scripts/py-tests.sh` | `set -e`, repo-root `ROOT`, `uv run pytest` |
| Parallel hook tests | `tests/ci/test_parallel_hook_execution.py` | Extend or sibling module for `api-contract-check` |
| M902-24 frontend tests | `tests/web_frontend/test_sync_api_types_script.py` | Precedent for bash hook testing |

**Gaps:** No `api-contract-check.sh`; no lefthook entry; spec file missing.

---

## Planning Resolutions (Spec Agent Must Freeze)

| # | Topic | Decision | Rationale |
|---|--------|----------|-----------|
| R1 | Type regeneration | Call `bash asset_generation/web/frontend/scripts/sync-api-types.sh` from repo root (or `npm run sync-api-types` from frontend root) | M902-24 already implements fetch/cache/validate; ticket AC `npx openapi-typescript http://localhost:8000/...` is illustrative only |
| R2 | Backend unreachable | Warning to stderr; continue with cache-backed types; still run `tsc` + contract tests | Matches ticket Error Handling AC |
| R3 | Pytest path | `asset_generation/python/tests/api/`, not repo-root `tests/api/` | M902-26 layout; 87 tests verified via `pytest --collect-only` |
| R4 | Lefthook glob | **Recommend** `asset_generation/web/backend/**/*.py` (user/orchestrator context) vs ticket example `routers/**/*.py` only | `main.py`, `core/`, and schema modules affect OpenAPI; spec picks one with AC traceability |
| R5 | Staged generated file | Use `stage: commit` on hook command | Regenerated `api.types.ts` included in commit when hook passes |
| R6 | Performance | Contract tests only (not full `py-tests.sh` / diff-cover) on pre-commit | Keeps hook &lt; 30s; full suite remains pre-push |
| R7 | Bypass | Document `LEFTHOOK=0` / `git commit --no-verify`; no new env kill switch unless spec requires | Aligns with existing lefthook header |
| R8 | Spec type | `api` for `spec_completeness_check.py` | Hook enforces API contract surface |

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: hook pipeline, glob, messages, runbook** | Spec Agent | Ticket AC; M902-24 script; M902-26 spec/runbook; `lefthook.yml`; `902_27_api_contract_precommit_spec.md` (create) | `project_board/specs/902_27_api_contract_precommit_spec.md` with: (a) **three-step contract** — sync → `cd frontend && npx tsc --noEmit` → `uv run pytest tests/api/test_*_contract.py` from `asset_generation/python`, (b) **exit codes** per step and aggregate exit 1, (c) **stderr templates** matching ticket example (step labels `[1/3]`…, tsc errors passthrough, pytest hint), (d) **glob + trigger** frozen (R4), (e) **env vars** — reuse `BLOBERT_OPENAPI_*` from M902-24 where applicable, (f) **failure runbook** — type mismatch / backend down / contract fail / bypass, (g) **CLAUDE.md section** outline, (h) **test plan** — `tests/ci/test_api_contract_precommit_hook.py` + optional shell test with mocked curl; no prose-only tests, (i) AC traceability table. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_27_api_contract_precommit_spec.md --type api` before TEST_DESIGN. | None | Spec exit gate PASS; R1–R8 unambiguous. | **A1:** Hook does not start backend — cache-only path must always be testable. **A2:** `tsc` requires `node_modules` — spec documents `npm ci` prerequisite. |
| **2** | **Test design: script behavior + lefthook registration** | Test Designer | Spec (Task 1) | Red tests: (1) `api-contract-check.sh` exits 0 when sync mocked + `tsc` + pytest succeed, (2) exits 1 when `tsc` fails (fixture TS project or stub), (3) exits 1 when pytest fails, (4) sync warning on fetch failure but cache valid (reuse M902-24 fixture patterns), (5) `lefthook.yml` contains `api-contract-check` with spec glob and `stage: commit`, (6) command run string points at `.lefthook/scripts/api-contract-check.sh`. Under `tests/ci/` and/or `tests/web_frontend/` per spec. Module docstring traces M902-27. | Task 1 | Tests fail before implementation. | **R1:** CI has no live backend — mock sync or `BLOBERT_SYNC_SKIP_FETCH=1`. |
| **3** | **Test break: adversarial hook paths** | Test Breaker | Tests (Task 2), spec | Cases: empty cache + fetch fail (sync exit 3), invalid cache, missing `uv`/venv, missing `node_modules`, hook run from wrong cwd, parallel pre-commit race (read-only), timeout &gt; 30s guard optional, `LEFTHOOK=0` not invoked in test. 3 consecutive green runs. | Task 2 | +6 cases; deterministic. | |
| **4** | **Implementation: hook script + lefthook + docs** | Implementation Agent (Generalist) | Spec; tests (Tasks 2–3) | `.lefthook/scripts/api-contract-check.sh` executable (`set -euo pipefail`); `lefthook.yml` registration; `CLAUDE.md` section; runbook in spec-indicated path; optional `Taskfile.yml` `hooks:api-contract` delegate (only if spec requires — default: direct bash per AC). All Task 3 tests PASS. | Tasks 1–3 | AC: script steps, lefthook glob, error handling, bypass documented. | **R2:** Regenerated `api.types.ts` may create large diffs — developer must re-`git add`. **R3:** First-time contributors without `uv sync` see clear error. |
| **5** | **Manual dry-run matrix (evidence for AC)** | Implementation Agent (Generalist) or AC Gatekeeper | Task 4 output | Checkpoint log with three scenarios: add required field (tsc fail), type change (tsc fail), remove field (tsc fail); bypass `--no-verify` succeeds; fix + retry succeeds. Commands + exit codes in `project_board/checkpoints/M902-27/2026-05-21T-dry-run.md`. | Task 4 | Ticket Testing AC satisfied with verbatim output. | Requires local backend or cache-only path per spec. |
| **6** | **Static QA** | Code Reviewer | Tasks 4–5 | `tests/ci/test_api_contract*.py` PASS; shellcheck on new script; no duplicate openapi-typescript logic outside sync script. | Task 5 | No blocking findings. | |
| **7** | **Learning** | Learning Agent | Static QA pass | `project_board/LEARNINGS.md` entry: hook vs pre-push split, cache fallback ops, bypass policy. | Task 6 | Entry merged. | |
| **8** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Evidence matrix per checkbox; `run_workflow_transition_gates.py` history green; git commit/push; ticket → `02_complete/`. | Tasks 1–7 | All AC satisfied. | COMPLETE blocked without push. |

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| `.lefthook/scripts/api-contract-check.sh` (3 steps, exit 0/1) | 1, 4 |
| Regenerate TS types (via sync script, not raw npx URL only) | 1, 4 |
| `tsc --noEmit` | 1, 4 |
| Contract pytest | 1, 4 |
| `lefthook.yml` registration + backend glob | 1, 4 |
| Backend not running → cache + warning | 1, 2, 4 |
| Error output clarity | 1, 4 |
| Runbook + bypass docs | 1, 4 |
| CLAUDE.md | 1, 4 |
| Dry-run / 3 scenarios / bypass | 5, 8 |
| Testing (automated) | 2, 3, 6 |

---

## Notes

- **Orchestrator:** After planner handoff, run `python ci/scripts/run_workflow_transition_gates.py --ticket-id M902-27 --transition planner_to_spec` before Spec Agent.
- **Commit policy:** Planner commits plan + checkpoint artifacts only (no implementation).
- **M902-28:** New hook participates in existing `pre-commit.parallel: true`; no serial dependency on py-review unless spec adds ordering (default: none).
- **Contract test scope:** `test_*_contract.py` includes adversarial module — spec confirms inclusion vs `test_api_contract_adversarial.py` naming.
- **Checkpoint log:** Spec Agent may append `project_board/checkpoints/M902-27/2026-05-21T-spec-run.md` for glob/error-template ambiguities.

---

## Tasks (Summary Table)

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Specification | Spec Agent | Ticket; M902-24/26 artifacts | `902_27_api_contract_precommit_spec.md` | — | Spec exit PASS | See Task 1 above |
| 2 | Test design | Test Designer | Spec | Red CI/shell tests | 1 | Fails pre-impl | Mock backend |
| 3 | Test break | Test Breaker | Tests | Adversarial cases | 2 | Deterministic | |
| 4 | Implementation | Implementation Agent (Generalist) | Spec; tests | Script + lefthook + docs | 1–3 | AC script/lefthook | uv/node prereqs |
| 5 | Dry-run evidence | Generalist / AC Gatekeeper | Impl | Checkpoint dry-run log | 4 | Manual AC | |
| 6 | Static QA | Code Reviewer | 4–5 | PASS review | 5 | Clean | |
| 7 | Learning | Learning Agent | 6 | LEARNINGS.md | 6 | Entry | |
| 8 | AC gatekeeper | AC Gatekeeper | All | COMPLETE + done/ | 1–7 | All AC | Push required |
