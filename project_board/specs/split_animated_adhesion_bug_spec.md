# Specification: split_animated_adhesion_bug

## SAAB-1 Module layout

- New file: `asset_generation/python/src/enemies/animated_adhesion_bug.py` containing `AnimatedAdhesionBug` only (same behavior as pre-split).
- `animated_enemies.py` imports `AnimatedAdhesionBug` from that module and keeps `'adhesion_bug': AnimatedAdhesionBug` in `AnimatedEnemyBuilder.ENEMY_CLASSES`.
- No circular imports: `animated_adhesion_bug` must not import `animated_enemies`.

## SAAB-2 Public API

- Callers may continue to import `AnimatedAdhesionBug` from `src.enemies.animated_enemies`.
- `AnimatedAdhesionBug.__module__` must be `src.enemies.animated_adhesion_bug` (class defined in dedicated module).

## SAAB-3 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.
- Structure docs mention `animated_adhesion_bug.py` where the animated enemy module tree is described.
