# TICKET: enemy_types_registry_python

Title: Optional — tidy `EnemyTypes` / slug registry in asset generation (Python)

## Description

`asset_generation/python/src/utils/constants.py` aggregates every enemy slug in `EnemyTypes` with `get_animated()` / `get_static()`. If maintaining slugs in one class becomes noisy after per-file animated builders land, introduce a small registry module (or per-slug constant files) that `EnemyTypes` re-exports, without changing external string values.

## Acceptance Criteria

- Slug strings remain identical (no rename of GLB families or CLI flags).
- No circular imports; `main.py` list commands and smart generation still agree on type lists.

## Dependencies

- None required; optionally after `animated_enemy_registry_cleanup`

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce executable spec: registry module API, import DAG (registry → no `constants`), string freeze | Spec Agent | This ticket; `asset_generation/python/src/utils/constants.py` (`EnemyTypes`); `main.py` / `smart_generation.py` grep for `EnemyTypes` | `## Specification` filled (or link) with module path (`enemy_slug_registry.py` or approved alias), tuple/list definitions, how `EnemyTypes` re-exports | — | Spec names every public symbol; explicitly forbids circular imports; slugs byte-identical to current values | Assumes no new enemy types land before impl; if they do, replan snapshot |
| 2 | Add pytest snapshot/contract: `get_animated` / `get_static` / `get_all` and order; class attributes match literals | Test Designer Agent | Spec + current `EnemyTypes` behavior | New tests under `asset_generation/python/tests/` (e.g. `utils/test_enemy_slug_registry_contract.py`) with frozen `list`/`tuple` expected values copied from pre-refactor snapshot | 1 | `pytest` fails on intentional slug drift; passes on green main after task 4 | Snapshot must match spec order (animated then static composition for `get_all`) |
| 3 | Stress tests: duplicates, type of return values, disjoint static/animated | Test Breaker Agent | Tests from task 2 | Extended adversarial cases where gaps exist | 2 | No redundant breakage vs existing `test_animated_enemy_classes*.py`; or explicit consolidation noted in spec | Overlap with existing `TestEnemyTypesConstants` — avoid duplicate maintenance per spec |
| 4 | Implement `enemy_slug_registry.py` (tuples or immutable sequences + accessors); refactor `EnemyTypes` to re-export same strings; `get_*` delegate or compose | Implementation Generalist | Spec; green tests from 2–3 | New module; slim `EnemyTypes` in `constants.py`; `utils/__init__.py` unchanged unless spec exports registry | 1, 2 | All `asset_generation/python` pytest green; `python -c` import `utils.constants` then `utils.enemy_slug_registry` with no `ImportError`/cycle | Registry must not import `constants` or any module that imports `constants` at load time |
| 5 | Static QA: import graph, formatting, dead code | Static QA Agent | Diff from task 4 | Notes or fixes per project norms | 4 | No circular import (verify with importlib or documented trace) | — |
| 6 | Integration smoke: CLI list paths still use same strings | Integration Agent (or Generalist) | `main.py` subcommands that list `EnemyTypes.get_animated()` / `get_all()` | Logged command output or scripted assert | 4, 5 | Behavior matches pre-refactor string sets for list/help | Requires Blender path only if subcommand spawns Blender; prefer code-path test without Blender if available |

---

## Specification

*(Spec Agent populates or links.)*

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
  "ticket_path": "project_board/maintenance/in_progress/enemy_types_registry_python.md",
  "checkpoint_log": "project_board/checkpoints/MAINT-ETRP/run-2026-04-05-autopilot.md",
  "scope": "enemy_slug_registry module + EnemyTypes re-export; no slug renames"
}
```

## Status
Proceed

## Reason

Planning complete. Spec Agent must author Revision 2 specification: single registry module for slug sequences, `EnemyTypes` compatibility surface, import DAG, and pytest snapshot contract alignment.
