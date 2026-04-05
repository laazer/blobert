# Specification: animated_enemy_registry_cleanup

## AERC-1 Package layout

- New package directory: `asset_generation/python/src/enemies/animated/`.
- New module `asset_generation/python/src/enemies/animated/registry.py` contains `AnimatedEnemyBuilder` with `ENEMY_CLASSES` mapping identical in keys and class objects to the pre-change registry (same six string keys; values are the classes from `animated_<slug>.py` modules).
- `asset_generation/python/src/enemies/animated/__init__.py` re-exports `AnimatedEnemyBuilder` and all six concrete animated enemy classes so consumers may use `from src.enemies.animated import AnimatedEnemyBuilder, AnimatedAcidSpitter, ...`.
- Delete `asset_generation/python/src/enemies/animated_enemies.py` after migration (no long-term shim).

## AERC-2 Import graph

- `animated_<slug>.py` modules must not import `animated.registry` or `animated` package (preserves acyclic graph: registry imports leaf modules only).
- `src/enemies/__init__.py` imports `AnimatedEnemyBuilder` from `.animated` (not `animated_enemies`).

## AERC-3 In-repo migration

- Update every Python reference under `asset_generation/python/` that imported from `src.enemies.animated_enemies` or `.animated_enemies` to the new path (`src.enemies.animated` or relative equivalent).
- Update `tests/enemies/conftest.py` docstring to name `src.enemies.animated` as the import entry point for stubbed Blender deps.
- Update `PROJECT_STRUCTURE.md` and `docs/ARCHITECTURE_SUMMARY.md` so the enemies tree documents `animated/` (registry + package) and does not present `animated_enemies.py` as the primary factory location.

## AERC-4 Behavior and CLI

- `AnimatedEnemyBuilder.create_enemy` and `get_available_types()` semantics unchanged.
- `main.py` and `generator.py` continue to drive animated enemy generation; `EnemyTypes` / CLI listing of animated types remains correct for all six types.

## AERC-5 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.

## AERC-6 Risk

- External out-of-repo scripts importing `src.enemies.animated_enemies` would break; in-repo scope only.
