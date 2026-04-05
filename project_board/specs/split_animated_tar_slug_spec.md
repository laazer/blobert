# Specification: split_animated_tar_slug

## STS-1 Module layout

- New file: `asset_generation/python/src/enemies/animated_tar_slug.py` containing `AnimatedTarSlug` only (same behavior as pre-split).
- `animated_enemies.py` imports `AnimatedTarSlug` from that module and keeps `'tar_slug': AnimatedTarSlug` in `AnimatedEnemyBuilder.ENEMY_CLASSES`.
- No circular imports: `animated_tar_slug` must not import `animated_enemies`.

## STS-2 Public API

- Callers may continue to import `AnimatedTarSlug` from `src.enemies.animated_enemies`.
- `AnimatedTarSlug.__module__` must be `src.enemies.animated_tar_slug` (class defined in dedicated module).

## STS-3 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.
- Structure docs (`PROJECT_STRUCTURE.md`, `docs/ARCHITECTURE_SUMMARY.md`) list `animated_tar_slug.py` where the enemy tree is described.
