# Specification: split_animated_claw_crawler

## SACC-1 Module layout

- New file: `asset_generation/python/src/enemies/animated_claw_crawler.py` containing `AnimatedClawCrawler` only (same behavior as pre-split).
- `animated_enemies.py` imports `AnimatedClawCrawler` from that module and keeps `'claw_crawler': AnimatedClawCrawler` in `AnimatedEnemyBuilder.ENEMY_CLASSES`.
- No circular imports: `animated_claw_crawler` must not import `animated_enemies`.

## SACC-2 Public API

- Callers may continue to import `AnimatedClawCrawler` from `src.enemies.animated_enemies`.
- `AnimatedClawCrawler.__module__` must be `src.enemies.animated_claw_crawler` (class defined in dedicated module).

## SACC-3 Verification

- `cd asset_generation/python && uv run pytest tests/ -q` — full suite green.
- Structure docs (`PROJECT_STRUCTURE.md`, `docs/ARCHITECTURE_SUMMARY.md`) list `animated_claw_crawler.py` where the enemy tree is described.
