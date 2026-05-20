# Project: M902-28 Parallel Pre-Commit / Pre-Push Hook Execution

**Description:** Enable safe Lefthook parallel scheduling for pre-push (Godot + Python full suites) and verify true concurrency for pre-commit linters, without changing hook policy (what runs) or TSGR runner contracts.

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/28_parallel_hook_execution.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-28/2026-05-20T-planning-run.md`

---

## Executive Summary

**Objective:** Reduce wall-clock time on `git commit` and `git push` by running independent Lefthook commands concurrently where safe. Primary win: `pre-push` currently sets `parallel: false`, so `godot-tests` and `py-tests` run sequentially even when both globs match. Pre-commit already sets `parallel: true` but may be effectively serial due to Taskfile/glob behavior — verify and fix.

**Scope (in):** `lefthook.yml`, `Taskfile.yml` hook targets, `.lefthook/scripts/godot-tests.sh`, `.lefthook/scripts/py-tests.sh`, `CLAUDE.md` / `lefthook.yml` header docs, behavioral CI tests for scheduling contract and artifact isolation.

**Scope (out):** pytest-xdist, parallel Ruff shards, incremental diff-cover, M903 parallel gate audit (see `project_board/DEFERRALS.md` M902-07 → M903). Changing which hooks run or TSGR timeout/import policy.

**Prerequisites:** MAINT-TSGR complete (`ci/scripts/verify_tsgr_runner_contract.sh`, `ci/scripts/run_tests.sh`). No umbrella children.

**Estimated effort:** 5–7 agent runs (spec → tests → impl → integration timing → AC gatekeeper).

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Lefthook config | `lefthook.yml` | `pre-commit: parallel: true` (8 commands); `pre-push: parallel: false` (godot-tests, py-tests) |
| Taskfile hooks | `Taskfile.yml` | `hooks:godot` → `godot-tests.sh`; `hooks:python` → `py-tests.sh` |
| Godot pre-push | `.lefthook/scripts/godot-tests.sh` | `timeout 120` import + `timeout 300` `tests/run_tests.gd`; uses `bin/godot` |
| Python pre-push | `.lefthook/scripts/py-tests.sh` | Ruff → pytest → diff-cover; writes `asset_generation/python/coverage.xml` |
| Canonical CI suite | `ci/scripts/run_tests.sh` | **Sequential** Godot then Python (TSGR-1/3); must remain canonical; parallel is hook-only |
| TSGR static contract | `ci/scripts/verify_tsgr_runner_contract.sh` | Must stay green after changes |
| Deferral | `project_board/DEFERRALS.md` | M902-07 parallel linting/caching → M903 (distinct from this ticket) |

**Safety sketch (for Spec to freeze):**

| Pair | Shared mutable artifacts? | Preliminary safe? |
|------|---------------------------|-------------------|
| `godot-tests` ∥ `py-tests` | Godot: `.godot/` cache; Python: `coverage.xml`, `.venv` reads | **Likely yes** if import cache + coverage paths do not collide (no shared write target today) |
| pre-commit py-* ∥ gd-* | Staged-file reads only; separate processes | **Likely yes**; verify Taskfile does not global-lock |
| `py-tests` internal | Single `coverage.xml` | **Not in scope** for inner parallelism unless trivial |

---

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: safety matrix, baseline protocol, Lefthook contract, docs contract** | Spec Agent | Ticket AC; `lefthook.yml`; hook scripts; `verify_tsgr_runner_contract.sh`; `run_tests.sh`; DEFERRALS note | `project_board/specs/902_28_parallel_hook_execution_spec.md` with: (a) **baseline appendix template** — how to capture wall-clock for pre-commit / pre-push (with/without matching globs, sequential vs parallel), minimum 2 scenarios per phase, (b) **parallel safety matrix** per hook command pair (shared files, git index, ports, `.godot/`, `coverage.xml`, uv/venv locks), (c) **pre-push**: require `parallel: true` for `godot-tests` + `py-tests` when both triggered; failure aggregation = any non-zero fails hook (Lefthook default), (d) **pre-commit**: verification procedure for true concurrency (e.g. `lefthook run pre-commit` + timing/log evidence); list fixes if Taskfile/glob forces serialization, (e) **opt-out**: document `LEFTHOOK=0`; research and document Lefthook-native parallel disable (env or config) — add `BLOBERT_HOOKS_PARALLEL=0` or equivalent **only if** supported without forking Lefthook, (f) **when parallel off**: low-core CI, debugging single hook, suspected `.godot/` corruption, (g) **CI vs local**: `run_tests.sh` stays sequential; hooks may parallelize only on developer push, (h) **TSGR**: no change to import/test timeouts or DRY delegation. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_28_parallel_hook_execution_spec.md --type generic` before TEST_DESIGN. | None | Spec exit gate PASS; every AC bullet mapped; safety matrix signed off with fail-closed rules. | **A1:** `.godot/` import contention under parallel Godot+pytest — spec may require serial import phase or accept measured risk. **A2:** Lefthook parallel disable env may not exist — fallback is doc-only `parallel: false` edit for emergencies. |
| **2** | **Test design: scheduling contract + artifact isolation (behavioral)** | Test Designer | Spec Task 1 | `tests/ci/test_parallel_hook_execution.py` (stable name; docstring → M902-28 / spec): (1) parse `lefthook.yml` — `pre-push.parallel` is true, `pre-commit.parallel` is true, (2) `godot-tests` and `py-tests` commands still delegate to `task hooks:godot` / `task hooks:python` (no policy drift), (3) script path assertions — Godot script does not write under `asset_generation/python/`; py-tests `coverage.xml` under `PY_ROOT` only, (4) optional lightweight timing guard: mock/subprocess wrapper proving two hook stubs can run concurrently when spec defines test hook (if full Godot too heavy for CI, spec defines stub mode), (5) `verify_tsgr_runner_contract.sh` still referenced / not weakened by yaml change. No markdown prose assertions. | Task 1 | Tests red before Task 4; pytest collection OK. | CI may skip real Godot parallel timing — integration Task 6 owns 3+ real runs. |
| **3** | **Test break: contention and flake adversarial cases** | Test Breaker | Tests Task 2, spec | Expanded tests: concurrent py-tests coverage write simulation (if spec allows temp paths), yaml mutation guards (parallel false regression), missing `parallel` key, handoff_metadata `lefthook.yml` change classification unchanged, 4× pytest collection zero flakes. | Task 2 | +8 adversarial cases; determinism documented. | |
| **4** | **Implementation: enable parallel pre-push + pre-commit fixes** | Implementation Generalist | Spec; tests Tasks 2–3 | `lefthook.yml`: `pre-push.parallel: true`; pre-commit adjustments per spec only; script changes **only if** spec mandates (e.g. isolated coverage tmp). `bash ci/scripts/verify_tsgr_runner_contract.sh` PASS. Task 2–3 tests PASS. | Tasks 1–3 | Diff limited to scheduling/docs/scripts per spec; no hook policy removal. | **R1:** Flaky `.godot/` — rollback path in spec. **R2:** LEARNINGS.md TSGR comment-line ordering if touching runner scripts. |
| **5** | **Documentation: CLAUDE.md + lefthook header** | Implementation Generalist or Spec Agent | Spec § docs; implemented config | `CLAUDE.md` Hooks section: parallel pre-push behavior, `LEFTHOOK=0`, parallel kill-switch, when to disable; `lefthook.yml` header comments aligned. | Task 4 | Human-readable; matches spec. | |
| **6** | **Integration: baseline timings + 3+ stable hook runs** | Integration / Human-orchestrated | Tasks 4–5; local dev machine | Scoped log `project_board/checkpoints/M902-28/<run-id>-integration.md`: (a) baseline table (sequential vs parallel pre-push when both globs match), (b) **3+ consecutive** `lefthook run pre-push` (or real `git push` dry-run) passes with no new flakes, (c) pre-commit concurrency evidence per spec protocol. Ticket Validation Status → Integration: Passing with pointers. | Tasks 4–5 | AC baseline + flake AC satisfied with pasted timings (summary in log, not CHECKPOINTS body). | **R3:** Godot absent in CI agent env — Human/local runs required; failures verbatim per workflow. |
| **7** | **Static QA** | python-reviewer / Code Reviewer | Tasks 2–5 | `task hooks:py-review` on changed Python tests; `verify_tsgr_runner_contract.sh` PASS; no new bare except in scripts. | Tasks 4–5 | No blocking findings. | |
| **8** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Per-AC evidence matrix; targeted pytest; git clean + push before COMPLETE; `git mv` ticket to `02_complete/`. | Tasks 1–7 | All AC checkboxes evidenced; handoff metadata aware of `lefthook.yml` change. | COMPLETE blocked without push. |

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-28? | Notes |
|------------|----------------|-----------------|-------|
| MAINT-TSGR / runner contract | `project_board/maintenance/done/test_suite_green_and_runner_exit_codes.md` | No (satisfied) | Parallel hooks must not break TSGR static checks |
| M902-07 parallel linting (M903) | DEFERRED | No | Different surface (gate audit vs git hooks) |
| Lefthook installed locally | N/A | Soft | Integration Task 6 needs `lefthook` on PATH |
| Umbrella children | — | No | Not an umbrella ticket |

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| Baseline wall-clock documented | 1, 6 |
| Safe parallel pairs analysis | 1 |
| Pre-push parallel godot + py | 1, 4 |
| Pre-commit true parallelism verified/fixed | 1, 4, 6 |
| No flaky increase (3+ runs) | 6 |
| CLAUDE.md / lefthook header + opt-out | 1, 5 |
| When parallel must stay off | 1, 5 |

---

## Notes

- **Policy vs scheduling:** This ticket changes **when** hooks run, not **what** they run (globs, scripts, TSGR timeouts unchanged unless spec finds a safety-required exception).
- **Canonical CI:** `timeout 300 ci/scripts/run_tests.sh` remains the single sequential full suite; do not parallelize inside `run_tests.sh` without a new ticket.
- **Cross-command parallelism only:** `py-tests.sh` may keep Ruff → pytest → diff-cover sequential; primary win is Godot suite overlapping Python suite.
- **Checkpoint protocol:** Judgment ambiguities → `project_board/checkpoints/M902-28/`; index line only in `CHECKPOINTS.md`.
- **Test filenames:** No ticket id in module name (`test_parallel_hook_execution.py`).

---

## Next Steps

**Immediate:** Spec Agent — author `902_28_parallel_hook_execution_spec.md` and pass `spec_completeness_check.py --type generic`.

**Unblocks:** Faster local `git push` for mixed Godot+Python changes; foundation for M903 hook performance work without conflating deferrals.
