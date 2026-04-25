# Metadata Catalog Single Source

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Eliminate duplicate enemy metadata and animation catalog definitions by making package metadata modules the single source of truth for API meta routes.

Target overlap:
- `asset_generation/web/backend/routers/meta.py` (`_FALLBACK_SLUGS`, animation list)
- `blobert_asset_gen.domain.metadata.enemy_slug_registry` (or transitional utility module)
- `blobert_asset_gen.services.build_options` (or transitional utility module)

## Acceptance Criteria

- [ ] API meta route reads enemy slug/label catalog from package metadata module.
- [ ] Hardcoded fallback slug list is removed or generated from canonical source.
- [ ] Animation export names are sourced from one canonical module.
- [ ] `/api/meta/enemies` response shape remains backward compatible.
- [ ] Regression tests prevent stale fallback/canonical mismatch.

## Dependencies

- Backend-Python Import Adapter

## Execution Plan

1. Define canonical metadata export module for enemies + animations.
2. Refactor API meta router to consume canonical module.
3. Keep fallback mode but derive fallback payload from shared source.
4. Add parity tests for normal and fallback import-failure paths.
5. Run API meta tests and related python utility tests.

## Notes

- Preserve deterministic ordering of enemy entries for UI stability.
