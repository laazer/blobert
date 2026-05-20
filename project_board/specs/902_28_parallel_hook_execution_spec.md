# Spec: Parallel Pre-Commit / Pre-Push Hook Execution (M902-28)

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/28_parallel_hook_execution.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-28_parallel_hook_execution.md`

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

**Ticket type:** `generic`

---

## Executive Summary

This specification defines **scheduling-only** changes for Lefthook git hooks: enable and verify safe **parallel** execution of independent hook commands to reduce wall-clock time on `git commit` and `git push`, without changing **hook policy** (which commands run, globs, scripts, TSGR timeouts, or canonical CI ordering).

**Primary win:** `pre-push` currently sets `parallel: false` in `lefthook.yml`, so `godot-tests` and `py-tests` run sequentially when both globs match. **Secondary win:** confirm `pre-commit` with `parallel: true` actually runs independent staged-file linters concurrently; fix Taskfile/glob bottlenecks if evidence shows serialization.

**In scope:** `lefthook.yml`, `Taskfile.yml` hook targets (only if spec-mandated), `.lefthook/scripts/godot-tests.sh`, `.lefthook/scripts/py-tests.sh`, `CLAUDE.md` Hooks section, `lefthook.yml` header comments, behavioral CI tests per Requirement 10.

**Out of scope:** pytest-xdist, parallel Ruff shards, incremental diff-cover, inner parallelism inside `py-tests.sh` (Ruff → pytest → diff-cover stays sequential), parallelizing `ci/scripts/run_tests.sh`, M903 gate audit / M902-07 deferral work (`project_board/DEFERRALS.md`).

**Prerequisites (satisfied):** MAINT-TSGR (`ci/scripts/verify_tsgr_runner_contract.sh`, `ci/scripts/run_tests.sh`).

---

## Assumptions and Checkpoint Resolutions

| # | Ambiguity | Resolution (normative) | Confidence |
|---|-----------|------------------------|------------|
| A1 | `LEFTHOOK_PARALLEL` env var | **Not part of upstream Lefthook** (v1.x docs: parallel is config-only). Do **not** invent `BLOBERT_HOOKS_PARALLEL` unless a future Lefthook release documents an official env override. Opt-out uses `LEFTHOOK=0`, per-command `LEFTHOOK_EXCLUDE`, or temporary `parallel: false` in `lefthook.yml`. | High |
| A2 | `.godot/` import cache under parallel pre-push | Godot import + pytest are **approved parallel** with monitoring; Integration must run 3+ consecutive pre-push passes. If flakes correlate with concurrent import, rollback `pre-push.parallel` to `false` (Requirement 05). | Medium |
| A3 | `py-tests.sh` inner steps | Ruff, pytest, and diff-cover remain **sequential within** `py-tests.sh`; only **cross-command** parallelism (Godot vs Python) is required. | High |
| A4 | Canonical CI | `timeout 300 ci/scripts/run_tests.sh` remains **Godot then Python, sequential**; no change without a new ticket. | High |
| A5 | Hook policy | Globs, `run:` lines (`task hooks:godot`, `task hooks:python`, staged linters), TSGR timeouts in scripts unchanged unless a safety matrix row mandates a script change. | High |
| A6 | Baseline capture owner | Spec defines protocol; **Integration** (execution plan Task 6) records measured wall-clock in `project_board/checkpoints/M902-28/<run-id>-integration.md`. Spec appendix is the template only. | High |

---

## Deferred Boundary Statement

- **M902-07 / M903:** Parallel linting, caching, and gate-runner tool parallelism remain deferred (`project_board/DEFERRALS.md`). M902-28 covers **Lefthook developer hooks only**.
- **pytest-xdist / parallel Ruff / incremental diff-cover:** Separate tickets if pursued after baseline proves cross-command win insufficient.
- **CI agent environments without Godot:** Real timing and flake ACs are validated on a local dev machine (or Human); CI behavioral tests assert **config contract** only (Requirement 10).
- **Blog / post-commit / commit-msg hooks:** Unchanged; not part of parallel scheduling work.

---

## Requirement 01: Parallel Safety Matrix

### 1. Spec Summary

- **Description:** Every Lefthook command pair that may run concurrently must be classified **SAFE**, **UNSAFE**, or **N/A** with explicit shared-resource analysis. Implementation must not enable parallelism for any pair marked **UNSAFE**.

- **Constraints:** Fail-closed: if a pair is **UNKNOWN** after analysis, treat as **UNSAFE** until Integration evidence upgrades it.

- **Assumptions:** Repo root is the working directory for hooks; `direnv` may be inactive during hooks (Godot uses `bin/godot` per `godot-tests.sh`).

- **Scope:** `pre-push` command pairs; `pre-commit` command pairs among the eight commands in `lefthook.yml`.

#### Appendix B — Normative safety matrix (freeze)

| Pair | Commands | Shared mutable artifacts / contention | Git index / working tree | Ports / sockets | Verdict | Notes |
|------|----------|--------------------------------------|--------------------------|-----------------|---------|-------|
| P1 | `godot-tests` ∥ `py-tests` | Godot writes `.godot/` under repo root; Python writes `asset_generation/python/coverage.xml` only; both read `.venv` / uv env **read-mostly** | Both may read git for diff-cover (Python only); no `git write` in either script | None used | **SAFE** | Disjoint write paths; primary M902-28 win |
| P2 | `py-parse` ∥ `py-review` | Staged file reads; separate processes | Read-only staged paths via Lefthook | None | **SAFE** | |
| P3 | `py-parse` ∥ `py-pylint` | Same as P2 | Read-only | None | **SAFE** | |
| P4 | `py-parse` ∥ `py-organization` | Same | Read-only | None | **SAFE** | |
| P5 | `py-parse` ∥ `py-defensive-normalization` | Same | Read-only | None | **SAFE** | |
| P6 | `py-review` ∥ `py-pylint` | Same | Read-only | None | **SAFE** | |
| P7 | `py-review` ∥ `py-organization` | Same | Read-only | None | **SAFE** | |
| P8 | `py-review` ∥ `py-defensive-normalization` | Same | Read-only | None | **SAFE** | |
| P9 | `py-pylint` ∥ `py-organization` | Same | Read-only | None | **SAFE** | |
| P10 | `py-pylint` ∥ `py-defensive-normalization` | Same | Read-only | None | **SAFE** | |
| P11 | `py-organization` ∥ `py-defensive-normalization` | Same | Read-only | None | **SAFE** | |
| P12 | Any `py-*` ∥ `gd-review` | Python checks under `asset_generation/**`; GD checks `**/*.gd` — disjoint paths unless same file staged as both (impossible for one path) | Read-only | None | **SAFE** | |
| P13 | Any `py-*` ∥ `gd-organization` | Same as P12 | Read-only | None | **SAFE** | |
| P14 | `gd-review` ∥ `gd-organization` | Same staged `.gd` files possible — both read-only linters | Read-only | None | **SAFE** | |
| P15 | `godot-tests` internal | Single Godot process sequence in one script | N/A | N/A | **N/A** | Import then tests; not parallelized in M902-28 |
| P16 | `py-tests` internal | Single `coverage.xml` writer | N/A | N/A | **N/A** | Sequential Ruff → pytest → diff-cover |
| P17 | `godot-tests` ∥ any `pre-commit` command | Different hook phases — never co-scheduled | N/A | N/A | **N/A** | |

**Godot vs Python isolation (normative):**

- `godot-tests.sh` must **not** write under `asset_generation/python/` (including `coverage.xml`).
- `py-tests.sh` must write `coverage.xml` only at `$PY_ROOT/coverage.xml` (`asset_generation/python/coverage.xml`).
- Neither script must invoke `git commit`, `git add`, or modify the index.

### 2. Acceptance Criteria

- **AC-01.1:** Spec matrix (Appendix B) is complete for all `pre-push` and `pre-commit` command pairs listed in `lefthook.yml`.
- **AC-01.2:** Implementation enables `pre-push.parallel: true` only for pair P1 (and does not add parallelism for P15/P16).
- **AC-01.3:** Static tests (Requirement 10) assert Godot hook script does not reference `asset_generation/python/coverage.xml` write paths and Python hook keeps coverage under `PY_ROOT`.

### 3. Risk & Ambiguity Analysis

- **R1:** `.godot/` cache corruption or import races when Godot import overlaps heavy pytest I/O — monitor in Integration; rollback per Requirement 05.
- **R2:** `uv run` concurrent invocations — read-only on lockfile; acceptable per A2.
- **R3:** Staging overlapping paths — not possible for same path as both `.py` under `asset_generation` and `.gd` at repo root with distinct globs; no action.

### 4. Clarifying Questions

- None (A1–A6 resolved).

---

## Requirement 02: Baseline Measurement Protocol

### 1. Spec Summary

- **Description:** Before/after wall-clock evidence for hook phases must be captured using a fixed protocol so Integration and AC gatekeeper can compare sequential vs parallel scheduling.

- **Constraints:** Use `/usr/bin/time` or `time -p` (POSIX) wrapping the **entire** hook invocation; record real elapsed seconds. Machine metadata required.

- **Assumptions:** `lefthook` installed on PATH; repo has typical dev deps (Godot wrapper, Python `.venv` or `uv`).

- **Scope:** Local measurement; not required in CI pytest.

#### Minimum scenarios (≥2 per phase)

| ID | Phase | Trigger condition | Command |
|----|-------|-------------------|---------|
| B1 | pre-push | Both globs would match (mixed change) | `lefthook run pre-push` after staging or touching at least one `**/*.gd` and one `asset_generation/python/**/*.py` path in the last commit range, **or** use `git push --dry-run` if hooks fire on dry-run in local Lefthook version; if not, `lefthook run pre-push` only |
| B2 | pre-push | Godot-only glob match | `lefthook run pre-push` with only Godot-tracked files changed in the evaluated file set |
| B3 | pre-push | Python-only glob match | `lefthook run pre-push` with only `asset_generation/python/**/*.py` changed |
| B4 | pre-commit | Multiple py + gd staged | `lefthook run pre-commit` with ≥2 staged `asset_generation/**/*.py` and ≥1 staged `**/*.gd` |
| B5 | pre-commit | Python-only staged | `lefthook run pre-commit` with staged Python only (no `.gd`) |

**Sequential baseline (pre-push B1 only):** Record one run with `pre-push.parallel: false` (temporary local edit or pre-implementation checkout) before enabling parallel, labeled `mode=sequential`.

**Parallel target (pre-push B1):** Record ≥3 consecutive runs with `pre-push.parallel: true` after implementation, labeled `mode=parallel`; all must exit 0.

### 2. Acceptance Criteria

- **AC-02.1:** Integration checkpoint log contains a table with columns: `scenario_id`, `phase`, `mode`, `elapsed_sec`, `exit_code`, `date`, `machine`, `lefthook_version`, `git_rev`.
- **AC-02.2:** At least scenarios **B1** (sequential + parallel) and **B4** are present in the log.
- **AC-02.3:** B1 parallel shows `elapsed_sec` less than B1 sequential on the same machine, **or** log documents why not (e.g. Godot-only-dominated push) with measured numbers.

### 3. Risk & Ambiguity Analysis

- Cold-cache first run may skew timing — record run 2–4 for parallel stability, not run 1 only.
- Apple Silicon vs Linux CI — ticket AC allows one Linux profile **if available**; not blocking.

### 4. Clarifying Questions

- None.

---

## Requirement 03: Lefthook Parallel Contract

### 1. Spec Summary

- **Description:** Normative YAML scheduling contract for `lefthook.yml` and Taskfile delegation unchanged.

- **pre-push (required change):**

```yaml
pre-push:
  parallel: true
  commands:
    godot-tests:
      glob: "**/*.{gd,tscn,tres,gdshader}"
      run: task hooks:godot
    py-tests:
      glob: "asset_generation/python/**/*.py"
      run: task hooks:python
```

- **pre-commit (verify, fix only if spec evidence):** Must retain `parallel: true`. All eight commands unchanged in `run:` and `glob:` from current `lefthook.yml`.

- **Glob behavior:** Lefthook skips commands whose globs do not match the evaluated file set; parallel applies only among **triggered** commands.

- **Taskfile:** `hooks:godot` → `bash .lefthook/scripts/godot-tests.sh`; `hooks:python` → `bash .lefthook/scripts/py-tests.sh` — no substitution of direct script paths in `lefthook.yml`.

- **Assumptions:** Lefthook default scheduler runs triggered commands concurrently when `parallel: true`.

- **Scope:** `lefthook.yml` only for scheduling flag unless Requirement 01 mandates script isolation fix.

### 2. Acceptance Criteria

- **AC-03.1:** Parsed `lefthook.yml` has `pre-push.parallel` truthy and `pre-commit.parallel` truthy.
- **AC-03.2:** `godot-tests.run` equals `task hooks:godot` and `py-tests.run` equals `task hooks:python` (whitespace-tolerant parse).
- **AC-03.3:** Globs match ticket evidence table (Godot: `**/*.{gd,tscn,tres,gdshader}`; Python: `asset_generation/python/**/*.py`).
- **AC-03.4:** `bash ci/scripts/verify_tsgr_runner_contract.sh` exits 0 after implementation (TSGR timeouts and import policy unchanged in scripts).

### 3. Risk & Ambiguity Analysis

- Misconfigured YAML indentation breaks hooks — Test Designer adds regression parse tests.
- Taskfile global mutex — if discovered, document in Integration log; fix only if Task itself serializes (out of scope unless proven).

### 4. Clarifying Questions

- None.

---

## Requirement 04: Failure Aggregation (Unchanged Semantics)

### 1. Spec Summary

- **Description:** Hook phase fails if **any** triggered command exits non-zero. Lefthook default aggregation must remain: developers see failures from all concurrent commands where supported; the git operation aborts with non-zero hook exit.

- **Constraints:** Do not swallow subprocess failures; do not add `|| true` to hook scripts. Do not change `set -e` behavior in `.lefthook/scripts/*.sh`.

- **Assumptions:** Lefthook propagates the first/non-zero exit according to its version’s parallel job implementation (any failure ⇒ hook failure).

- **Scope:** `pre-push` and `pre-commit`.

### 2. Acceptance Criteria

- **AC-04.1:** With `parallel: true`, if `godot-tests` fails and `py-tests` succeeds, `lefthook run pre-push` exit code is non-zero.
- **AC-04.2:** If `py-tests` fails and `godot-tests` succeeds, exit code is non-zero.
- **AC-04.3:** stderr from failing command is present in hook output (manual or Integration spot-check once; Test Designer may stub commands for CI).

### 3. Risk & Ambiguity Analysis

- Interleaved logs may make debugging harder — document verbose flag in Requirement 05.

### 4. Clarifying Questions

- None.

---

## Requirement 05: Opt-Out and When Parallel Must Stay Off

### 1. Spec Summary

- **Description:** Document all supported ways to disable or bypass hooks and parallel scheduling.

#### Normative opt-out table

| Mechanism | Effect | Document in |
|-----------|--------|-------------|
| `LEFTHOOK=0` (or `LEFTHOOK=false`) | Disables Lefthook entirely for that git command | `lefthook.yml` header (existing), `CLAUDE.md` |
| `LEFTHOOK_EXCLUDE=<command_id>` | Skips named command(s); comma-separated per Lefthook docs | `CLAUDE.md` Hooks section |
| `git commit --no-verify` / `git push --no-verify` | Skips all git hooks (not Lefthook-specific) | `CLAUDE.md` (advisory) |
| Edit `lefthook.yml` → `parallel: false` | Disables concurrent scheduling for that phase | `CLAUDE.md` emergency rollback |
| `LEFTHOOK_VERBOSE=1` | More logging when debugging parallel failures | `CLAUDE.md` |

**Not supported (do not document as available):** `LEFTHOOK_PARALLEL=false` — no upstream env var in Lefthook 1.x configuration docs. **Do not add** `BLOBERT_HOOKS_PARALLEL` in M902-28.

#### When parallel must remain off

| Situation | Action |
|-----------|--------|
| Debugging a single failing hook | `LEFTHOOK_EXCLUDE` all but one command, or temporary `parallel: false` |
| Low-core / memory-constrained runner | Keep `parallel: false` locally or use `LEFTHOOK=0` for one-off pushes |
| Suspected `.godot/` corruption or flaky import after parallel enable | Roll back `pre-push.parallel` to `false`; file issue; cite Integration log |
| CI canonical suite | Always sequential via `run_tests.sh` — parallel hooks are **local push/commit only** |

- **Assumptions:** Developers read `CLAUDE.md` for hook ergonomics.

- **Scope:** Documentation + implementation default `pre-push.parallel: true` after M902-28 lands.

### 2. Acceptance Criteria

- **AC-05.1:** `CLAUDE.md` Hooks section lists `LEFTHOOK=0`, `LEFTHOOK_EXCLUDE`, `LEFTHOOK_VERBOSE`, and explicitly states **`LEFTHOOK_PARALLEL` is not a Lefthook feature**.
- **AC-05.2:** `lefthook.yml` header comment block matches AC-05.1 for skip/parallel rollback (minimum: `LEFTHOOK=0` preserved; add parallel note).
- **AC-05.3:** No new env var `BLOBERT_HOOKS_PARALLEL` in repo unless a later ticket cites upstream Lefthook release notes adding it.

### 3. Risk & Ambiguity Analysis

- Developers expecting env parallel toggle — mitigated by explicit negative documentation.

### 4. Clarifying Questions

- None.

---

## Requirement 06: Pre-Commit True Concurrency Verification

### 1. Spec Summary

- **Description:** Procedure to prove `pre-commit.parallel: true` results in overlapping execution of independent commands, not effective serialization via Taskfile or missed globs.

#### Verification procedure (Integration or implementer)

1. Stage ≥3 Python files under `asset_generation/python/` and ≥2 `.gd` files outside `tests/` (paths that match globs).
2. Run: `LEFTHOOK_VERBOSE=1 lefthook run pre-commit 2>&1 | tee /tmp/pre-commit-parallel.log`
3. **Pass evidence** if log timestamps or Lefthook verbose lines show multiple commands **started** before any single long-running command **finished**, **or** wall-clock for full pre-commit is materially less than sum of individual `task hooks:*` runs measured sequentially on same staged set (≥25% reduction acceptable).
4. If only one glob family matches, document **N/A concurrency** for that run (not a failure).

#### Fixes allowed if serialization proven

- Adjust Taskfile `deps` only if a hook target incorrectly serializes unrelated cmds.
- Do **not** remove `parallel: true` without ticket escalation.

- **Assumptions:** Pre-commit commands are short relative to pre-push.

- **Scope:** pre-commit phase only.

### 2. Acceptance Criteria

- **AC-06.1:** Integration log includes pre-commit verification outcome (`pass`, `n/a`, or `fail` with log excerpt).
- **AC-06.2:** If `fail`, implementation documents root cause and applies minimal Taskfile/`lefthook.yml` fix before COMPLETE.
- **AC-06.3:** `pre-commit.parallel` remains `true` in committed `lefthook.yml` after M902-28.

### 3. Risk & Ambiguity Analysis

- All commands fast → overlap hard to see in logs — use verbose mode and multi-file staging.

### 4. Clarifying Questions

- None.

---

## Requirement 07: CI Canonical Suite and TSGR (Unchanged)

### 1. Spec Summary

- **Description:** `ci/scripts/run_tests.sh` remains the single **sequential** combined suite: Godot import + tests, then `py-tests.sh`. Parallelism is **not** added to `run_tests.sh` in M902-28.

- **TSGR:** `godot-tests.sh` keeps `timeout 120` import and `timeout 300` `tests/run_tests.gd`; no `|| true` on import; no stderr discard on fail path.

- **Assumptions:** `verify_tsgr_runner_contract.sh` is run after hook changes.

- **Scope:** CI scripts read-only for parallelism; TSGR static contract must pass.

### 2. Acceptance Criteria

- **AC-07.1:** `run_tests.sh` still invokes Godot before bash `py-tests.sh` with no `&` backgrounding or parallel wrapper.
- **AC-07.2:** `bash ci/scripts/verify_tsgr_runner_contract.sh` exit 0 on implementation branch.
- **AC-07.3:** No reduction of TSGR timeout values in hook scripts without spec revision.

### 3. Risk & Ambiguity Analysis

- Accidental edit to `run_tests.sh` — Test Designer guards ordering in static test optional cross-check.

### 4. Clarifying Questions

- None.

---

## Requirement 08: Implementation Constraints

### 1. Spec Summary

- **Description:** Allowed file changes and forbidden policy drift.

**Allowed:**

- Set `pre-push.parallel: true` in `lefthook.yml`.
- `lefthook.yml` / `CLAUDE.md` comments.
- `Taskfile.yml` only to remove proven serialization between independent hook targets.
- Script changes **only** if Integration proves safety matrix violation (e.g. relocate `coverage.xml` to temp path) — requires spec amendment checkpoint before coding.

**Forbidden:**

- Removing or weakening globs/commands.
- Changing diff-cover threshold defaults.
- Parallelizing inside `py-tests.sh` without new ticket.
- Parallelizing `run_tests.sh` or frontend tests.

- **Assumptions:** Generalist implementation follows tests from Requirement 10.

- **Scope:** M902-28 implementation tasks 4–5 in execution plan.

### 2. Acceptance Criteria

- **AC-08.1:** `git diff` for M902-28 is limited to scheduling/docs/tests per Allowed list.
- **AC-08.2:** Handoff metadata classifiers for `lefthook.yml` remain valid (no silent policy change).

### 3. Risk & Ambiguity Analysis

- Scope creep into pytest-xdist — reject; defer.

### 4. Clarifying Questions

- None.

---

## Requirement 09: Flake Stability Acceptance

### 1. Spec Summary

- **Description:** After parallel pre-push is enabled, local stability must not regress versus pre-change baseline.

- **Constraints:** ≥3 consecutive `lefthook run pre-push` (scenario B1 file set) with exit code 0 on same machine without manual `.godot` deletion between runs.

- **Assumptions:** Machine has adequate RAM/CPU for two heavy suites (typical Apple Silicon dev laptop).

- **Scope:** Integration Task 6; not CI pytest.

### 2. Acceptance Criteria

- **AC-09.1:** Integration log documents run1, run2, run3 exit codes all 0.
- **AC-09.2:** No new intermittent failures not explained by environment (if failure occurs, verbatim stderr in checkpoint per workflow).

### 3. Risk & Ambiguity Analysis

- Godot headless flake — rollback `parallel: false` and BLOCKED until root cause.

### 4. Clarifying Questions

- None.

---

## Requirement 10: Test Designer Contract (Behavioral)

### 1. Spec Summary

- **Description:** Tests must assert **executable** scheduling and isolation contracts, not markdown prose.

- **Module:** `tests/ci/test_parallel_hook_execution.py` (docstring references M902-28 and this spec).

**Minimum test obligations:**

| ID | Behavior asserted |
|----|-------------------|
| T1 | YAML parse: `pre-push.parallel` is true post-implementation |
| T2 | YAML parse: `pre-commit.parallel` is true |
| T3 | Command delegation: `godot-tests` → `task hooks:godot`; `py-tests` → `task hooks:python` |
| T4 | Godot script does not write under `asset_generation/python/` |
| T5 | Python script references `coverage.xml` under `PY_ROOT` / `asset_generation/python` only |
| T6 | `verify_tsgr_runner_contract.sh` path exists and `run_tests.sh` still sequences Godot before Python (lightweight file read) |
| T7 | Optional: subprocess stub proving two hook stubs can overlap when spec stub mode defined — only if full Godot too heavy |

- **Assumptions:** Tests red before implementation (TDD).

- **Scope:** Test Designer + Test Breaker; no implementation in Spec stage.

### 2. Acceptance Criteria

- **AC-10.1:** Test module collects under project pytest config.
- **AC-10.2:** No assertion that reads ticket/spec markdown bodies as expected output.
- **AC-10.3:** Test Breaker adds adversarial YAML regression cases per execution plan Task 3.

### 3. Risk & Ambiguity Analysis

- Over-mocking Lefthook — prefer YAML + script path checks; timing tests optional/stub.

### 4. Clarifying Questions

- None.

---

## Appendix A: Baseline Measurement Log Template

Copy into `project_board/checkpoints/M902-28/<run-id>-integration.md`:

```markdown
## Hook timing baseline (M902-28)

| scenario_id | phase | mode | elapsed_sec | exit_code | date | machine | lefthook_version | git_rev |
|-------------|-------|------|---------------|-----------|------|---------|------------------|---------|
| B1 | pre-push | sequential | | | | | | |
| B1 | pre-push | parallel | | | | | | |
| B1 | pre-push | parallel | | | | | | |
| B1 | pre-push | parallel | | | | | | |
| B4 | pre-commit | parallel | | | | | | |

Notes:
- Command: `/usr/bin/time -p lefthook run <phase>`
- pre-commit concurrency evidence: pass / n/a / fail (see Requirement 06)
```

---

## Appendix B: Parallel Safety Matrix (Summary)

See Requirement 01 table. **Only pair P1** is newly enabled for cross-suite parallelism on pre-push. All pre-commit pairs among triggered commands are **SAFE** per read-only staged analysis.

---

## Ticket AC Traceability

| Ticket AC | Spec requirements |
|-----------|-------------------|
| Baseline wall-clock documented | Req 02, Appendix A |
| Safe parallel pairs analysis | Req 01, Appendix B |
| Pre-push parallel godot + py | Req 03, 01 (P1) |
| Pre-commit true parallelism | Req 06, 03 |
| No flaky increase (3+ runs) | Req 09 |
| CLAUDE.md / lefthook header + opt-out | Req 05 |
| When parallel must stay off | Req 05 |

---

## Spec Exit Gate

Run before TEST_DESIGN advance:

```bash
python ci/scripts/spec_completeness_check.py \
  project_board/specs/902_28_parallel_hook_execution_spec.md \
  --type generic
```

Expected: exit code **0** (`generic` has no extra mandatory sections).

---

## Handoff

- **Next agent:** Test Designer Agent
- **Next stage:** TEST_DESIGN
- **Deliverable:** `tests/ci/test_parallel_hook_execution.py` per Requirement 10
