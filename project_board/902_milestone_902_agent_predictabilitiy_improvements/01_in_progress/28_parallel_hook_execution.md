# M902-28: Parallel Pre-Commit / Pre-Push Hook Execution

**Status:** IN PROGRESS  
**Target:** TBD

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

- [ ] Baseline documented: wall-clock time for representative pre-commit and pre-push runs (with and without staged/trigger globs), captured in ticket checkpoint or spec appendix
- [ ] Analysis of which hook pairs are **safe** to run in parallel (no shared mutable artifacts, no git index races, no port/socket conflicts)
- [ ] Pre-push: enable parallel execution of independent commands (at minimum `godot-tests` and `py-tests` when both match globs) via `lefthook.yml` and/or script changes, with failure aggregation unchanged (first failure still fails the hook)
- [ ] Pre-commit: confirm `parallel: true` actually runs independent commands concurrently; fix any Taskfile/script bottlenecks that force serialization
- [ ] No increase in flaky hook failures across 3+ consecutive local runs on a machine with typical dev resources
- [ ] `CLAUDE.md` / `lefthook.yml` header comments updated with parallel behavior, env opt-out (e.g. `LEFTHOOK=0`), and any new `LEFTHOOK_PARALLEL=false` or project-specific kill switch if added
- [ ] Document when parallel mode must remain off (e.g. low-core CI runners, debugging single hook)

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
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: 29/30 PASS (1 expected red: `test_pre_push_parallel_enabled` until `pre-push.parallel: true`)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent (Generalist)

## Required Input Schema
```json
{
  "spec": "project_board/specs/902_28_parallel_hook_execution_spec.md",
  "execution_plan": "project_board/execution_plans/M902-28_parallel_hook_execution.md",
  "test_modules": [
    "tests/ci/test_parallel_hook_execution.py",
    "tests/ci/test_parallel_hook_execution_adversarial.py"
  ],
  "checkpoint": "project_board/checkpoints/M902-28/2026-05-20T-test-break-run.md"
}
```

## Status
Proceed

## Reason
Behavioral + adversarial suites (30 tests, 19 adversarial). Expected red until `pre-push.parallel: true` in `lefthook.yml`. Then `bash ci/scripts/verify_tsgr_runner_contract.sh` and CLAUDE.md/header docs per Req 05.
