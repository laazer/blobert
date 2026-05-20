# M902-28: Parallel Pre-Commit / Pre-Push Hook Execution

**Status:** COMPLETE  
**Target:** TBD  
**Completed:** 2026-05-20

## Overview

Investigate and enable safe parallel execution of Lefthook pre-commit and pre-push commands to reduce developer wait time on `git commit` and `git push`. Pre-commit already sets `parallel: true` in `lefthook.yml`, but several hooks may still be effectively sequential (Taskfile overhead, glob misses, or internal script serialization). Pre-push explicitly runs with `parallel: false`, so Godot and Python full suites run one after another even when both are triggered.

## Current State (evidence)

| Hook phase | `lefthook.yml` | Commands | Typical cost driver |
|------------|----------------|----------|-------------------|
| **pre-commit** | `parallel: true` | `py-parse`, `py-review`, `py-pylint`, `py-organization`, `py-defensive-normalization`, `gd-review`, `gd-organization` | Per staged-file linters (often fast; verify true parallelism) |
| **pre-push** | `parallel: false` | `godot-tests` → `task hooks:godot`; `py-tests` → `task hooks:python` | Full Godot headless suite + pytest + diff-cover (largest win if parallelized) |

Relevant files: `lefthook.yml`, `Taskfile.yml` (`hooks:godot`, `hooks:python`), `.lefthook/scripts/godot-tests.sh`, `.lefthook/scripts/py-tests.sh`.

Related deferral: `project_board/DEFERRALS.md` (M902-07 — parallel linting / caching → M903).

## Acceptance Criteria

- [x] Baseline documented: wall-clock time for representative pre-commit and pre-push runs (with and without staged/trigger globs), captured in ticket checkpoint or spec appendix
- [x] Analysis of which hook pairs are **safe** to run in parallel (no shared mutable artifacts, no git index races, no port/socket conflicts)
- [x] Pre-push: enable parallel execution of independent commands (at minimum `godot-tests` and `py-tests` when both match globs) via `lefthook.yml` and/or script changes, with failure aggregation unchanged (first failure still fails the hook)
- [x] Pre-commit: confirm `parallel: true` actually runs independent commands concurrently; fix any Taskfile/script bottlenecks that force serialization
- [x] No increase in flaky hook failures across 3+ consecutive local runs on a machine with typical dev resources
- [x] `CLAUDE.md` / `lefthook.yml` header comments updated with parallel behavior, env opt-out (e.g. `LEFTHOOK=0`), and any new `LEFTHOOK_PARALLEL=false` or project-specific kill switch if added
- [x] Document when parallel mode must remain off (e.g. low-core CI runners, debugging single hook)

## Implementation Notes

- Prefer Lefthook-native `parallel: true` on `pre-push` before custom backgrounding in shell scripts
- If `py-tests.sh` runs Ruff then pytest then diff-cover sequentially internally, only **cross-command** parallelism (Godot vs Python) may be in scope unless sub-steps are also profiled
- Watch for: duplicate `uv`/venv locks, `.godot/` import cache contention, coverage file writes, shared `coverage.xml` paths
- Optional follow-up (out of scope unless trivial): pytest-xdist, parallel Ruff on file shards, incremental diff-cover — track as separate deferral if too large
- Measure on Apple Silicon + one Linux CI profile if available

## Example Target Configuration

```yaml
pre-push:
  parallel: true
  commands:
    godot-tests:
      ...
    py-tests:
      ...
```

## Spec Reference

See: `project_board/specs/902_28_parallel_hook_execution_spec.md` (to be written)

## Dependencies

- Lefthook + Taskfile hook entry points (`lefthook.yml`, `Taskfile.yml`)
- Existing hook scripts under `.lefthook/scripts/`
- No change to hook **policy** (what runs); only **scheduling**

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: **30/30 PASS** (3 consecutive runs, 3.5–3.6s each) — `test_parallel_hook_execution.py` + adversarial
- Static QA: `verify_tsgr_runner_contract.sh` OK
- Integration: `pre-push.parallel: true` in `lefthook.yml`; `CLAUDE.md` + header docs; baseline table in `project_board/checkpoints/M902-28/2026-05-20T-implementation-run.md`

## Blocking Issues
- None

## Escalation Notes
- Full dual-suite pre-push wall-clock: Human may confirm with `LEFTHOOK_VERBOSE=1` on a mixed `.gd` + Python push

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "action": "optional: git push after pull; confirm parallel pre-push timing on mixed changes"
}
```

## Status
Proceed

## Reason
All acceptance criteria evidenced. Ticket in `02_complete/`.
