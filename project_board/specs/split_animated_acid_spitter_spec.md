# Specification: split_animated_acid_spitter

## SAAS-1 Module layout

- New file: `asset_generation/python/src/enemies/animated_acid_spitter.py` containing `AnimatedAcidSpitter` only (same behavior as pre-split).
- `animated_enemies.py` imports `AnimatedAcidSpitter` from that module and keeps `'acid_spitter': AnimatedAcidSpitter` in `AnimatedEnemyBuilder.ENEMY_CLASSES`.
- No circular imports: `animated_acid_spitter` must not import `animated_enemies`.

## SAAS-2 Public API

- Callers may continue to import `AnimatedAcidSpitter` from `src.enemies.animated_enemies`.
- `AnimatedAcidSpitter.__module__` must be `src.enemies.animated_acid_spitter` (class defined in dedicated module).

## SAAS-3 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.
- Structure docs (`PROJECT_STRUCTURE.md`, `docs/ARCHITECTURE_SUMMARY.md`) list `animated_acid_spitter.py` where the enemy tree is described.
