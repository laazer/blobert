# Specification: split_animated_ember_imp

## SEI-1 Module layout

- New file: `asset_generation/python/src/enemies/animated_ember_imp.py` containing `AnimatedEmberImp` only (same behavior as pre-split).
- `animated_enemies.py` imports `AnimatedEmberImp` from that module and keeps `'ember_imp': AnimatedEmberImp` in `AnimatedEnemyBuilder.ENEMY_CLASSES`.
- No circular imports: `animated_ember_imp` must not import `animated_enemies`.

## SEI-2 Public API

- Callers may continue to import `AnimatedEmberImp` from `src.enemies.animated_enemies`.
- `AnimatedEmberImp.__module__` must be `src.enemies.animated_ember_imp` (class defined in dedicated module).

## SEI-3 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.
- Structure docs (`PROJECT_STRUCTURE.md`, `docs/ARCHITECTURE_SUMMARY.md`) list `animated_ember_imp.py` where the enemy tree is described.
