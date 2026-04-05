# MAINT-ETRP — Autopilot run 2026-04-05

## Scope
Enemy slug registry module + `EnemyTypes` delegation; pytest contract + adversarial AST/disjoint checks.

## Outcomes
- Added `asset_generation/python/src/utils/enemy_slug_registry.py` with `ANIMATED_SLUGS` / `STATIC_SLUGS` (no `constants` import).
- Refactored `EnemyTypes.get_*` to `list(registry tuples)`; class string attributes unchanged.
- New tests: `tests/utils/test_enemy_slug_registry_contract.py` (frozen lists, attributes, `get_all` concat, subprocess import-order, AST import ban, disjoint sets).
- `uv run pytest tests/ -q`: **386 passed** (221 subtests).

## Assumption made
- Integration smoke (CLI list commands) left for gatekeeper / follow-up per ticket task 6; contract tests cover string sets and main-style import path.

## Confidence
High — full suite green; subprocess isolates `utils.*` import graph from pytest’s `src.utils` loading.
