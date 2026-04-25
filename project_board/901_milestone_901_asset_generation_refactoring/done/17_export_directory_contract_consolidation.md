# Export Directory Contract Consolidation

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Consolidate export directory constants and allowlist prefixes used across API and package service modules into one shared contract module.

Target overlap:
- `asset_generation/web/backend/routers/assets.py`
- `asset_generation/web/backend/routers/registry.py`
- `blobert_asset_gen.services.registry` (or transitional `model_registry/service.py`)
- `blobert_asset_gen.domain.constants` (or transitional constants module)

## Acceptance Criteria

- [ ] One canonical module defines export directory roots and allowlisted registry prefixes.
- [ ] API assets/registry routers import constants from canonical module.
- [ ] Python model registry validation imports same canonical constants.
- [ ] Hardcoded duplicate tuples/lists are removed from API routers.
- [ ] Existing assets and registry tests pass with no path behavior regression.

## Dependencies

- Registry Path Policy Unification
- Backend-Python Import Adapter

## Execution Plan

1. Create or designate canonical constants module for export roots.
2. Migrate API and service imports to canonical module.
3. Remove duplicate constant declarations.
4. Validate assets listing and registry path checks.
5. Run backend assets/registry and python registry tests.

## Notes

- Keep naming stable to avoid broad churn in existing tests.
