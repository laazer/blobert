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
SPECIFICATION

## Revision
2

## Last Updated By
Planner Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Spec Agent

## Required Input Schema
```json
{
  "execution_plan": "project_board/execution_plans/M902-28_parallel_hook_execution.md",
  "spec_output": "project_board/specs/902_28_parallel_hook_execution_spec.md",
  "ticket_type": "generic"
}
```

## Status
Proceed

## Reason
Planning complete. Execution plan and checkpoint logged. Spec Agent owns safety matrix, baseline protocol, and Lefthook parallel contract before TEST_DESIGN.
