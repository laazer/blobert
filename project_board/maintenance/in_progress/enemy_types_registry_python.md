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

### REQ-ETRP-001 — Registry module
- **Path:** `asset_generation/python/src/utils/enemy_slug_registry.py`
- **Public symbols:** `ANIMATED_SLUGS: tuple[str, ...]`, `STATIC_SLUGS: tuple[str, ...]`
- **Values:** Byte-identical strings, same order as pre-change `EnemyTypes.get_animated()` then `EnemyTypes.get_static()` respectively (animated: adhesion_bug → … → carapace_husk; static: glue_drone → … → ferro_drone).

### REQ-ETRP-002 — Import DAG (no cycles)
- `enemy_slug_registry` **must not** import `constants` or any module that transitively imports `constants` at import time.
- `constants.EnemyTypes` **may** import `enemy_slug_registry` and use its tuples for `get_animated` / `get_static` / `get_all`.

### REQ-ETRP-003 — `EnemyTypes` compatibility
- Class attributes (`EnemyTypes.ADHESION_BUG`, …) remain the same string literals as before refactor.
- `get_animated()` returns `list(enemy_slug_registry.ANIMATED_SLUGS)` (or equivalent copy).
- `get_static()` returns `list(enemy_slug_registry.STATIC_SLUGS)`.
- `get_all()` returns `get_animated() + get_static()` (animated first, then static), matching prior behavior.

### REQ-ETRP-004 — Pytest contract
- Under `asset_generation/python/tests/`: frozen expected lists match registry tuples; class attributes asserted; `get_all() == get_animated() + get_static()`; **import-order** smoke in a **fresh subprocess** with `sys.path` like `main.py` (`import utils.constants` then `import utils.enemy_slug_registry`) succeeds.

### REQ-ETRP-005 — Adversarial (test-breaker)
- AST (or equivalent) assertion that `enemy_slug_registry.py` contains no import of `utils.constants`, `constants`, or `from utils import constants`.
- Assert `ANIMATED_SLUGS` and `STATIC_SLUGS` are disjoint sets.

### REQ-ETRP-006 — Package surface
- `src/utils/__init__.py` unchanged unless a future ticket explicitly exports the registry from `utils`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
4

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passed (gatekeeper re-run: `cd asset_generation/python && uv run pytest tests/ -q` — 386 passed, 221 subtests passed)
- Static QA: Passed (contract tests ETRP_*: frozen slugs match `enemy_slug_registry` and `EnemyTypes` class attributes; subprocess import-order smoke; AST guard — no registry import of `constants`)
- Integration: Partial — `smart_generation` imports `EnemyTypes` from `constants` (same slug source as CLI). `uv run python main.py list` (no Blender) fails mid-run: `KeyError: 'acid_spitter'` in `list_enemies()` because `animated_enemy_details` only keys three slugs while `EnemyTypes.get_animated()` has six; AC “main.py list commands … agree” is not operationally satisfied until list completes.

## Blocking Issues

- `main.py` `list` subcommand: extend `animated_enemy_details` (or safe fallback) for every slug in `EnemyTypes.get_animated()` so `python main.py list` finishes; then re-smoke with `uv run python main.py list`.

## Escalation Notes

- System `python` may be unavailable; use `uv run python` from `asset_generation/python`. There is no `python -m src.main`; entry point is `main.py` in package root.

---

# NEXT ACTION

## Next Responsible Agent
Implementation Generalist

## Required Input Schema
```json
{
  "ticket_path": "project_board/maintenance/in_progress/enemy_types_registry_python.md",
  "scope": "Fix list_enemies() KeyError for animated slugs missing from animated_enemy_details; verify uv run python main.py list exits 0; hand back to Acceptance Criteria Gatekeeper Agent for COMPLETE + move to maintenance/done/"
}
```

## Status
Proceed

## Reason

Slug identity and no-cycle requirements are evidenced by pytest; CLI list smoke fails before completion, so Stage cannot be COMPLETE until list output matches extended animated roster without crashing.
