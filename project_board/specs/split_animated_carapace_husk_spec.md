# Specification: split_animated_carapace_husk

## SCHS-1 Module layout

- New file: `asset_generation/python/src/enemies/animated_carapace_husk.py` containing `AnimatedCarapaceHusk` only (same behavior as pre-split).
- `animated_enemies.py` imports `AnimatedCarapaceHusk` from that module and keeps `'carapace_husk': AnimatedCarapaceHusk` in `AnimatedEnemyBuilder.ENEMY_CLASSES`.
- No circular imports: `animated_carapace_husk` must not import `animated_enemies`.

## SCHS-2 Public API

- Callers may continue to import `AnimatedCarapaceHusk` from `src.enemies.animated_enemies`.
- `AnimatedCarapaceHusk.__module__` must be `src.enemies.animated_carapace_husk` (class defined in dedicated module).

## SCHS-3 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.
- Structure docs (`PROJECT_STRUCTURE.md`, `docs/ARCHITECTURE_SUMMARY.md`) list `animated_carapace_husk.py` where the enemy tree is described.
