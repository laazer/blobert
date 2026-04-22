# Registry Mutation Service Boundary

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Move registry mutation logic currently implemented in API route helpers into shared package service modules so business rules live in one domain/service layer.

Target overlap:
- `asset_generation/web/backend/routers/registry.py` (`_find_enemy_version`, `_apply_enemy_version_delete`, player-active delete flow)
- `blobert_asset_gen.services.registry` (or transitional `asset_generation/python/src/model_registry/service.py`)

## Acceptance Criteria

- [ ] Service layer provides public APIs for enemy-version delete and player-active-visual delete.
- [ ] API delete endpoints become thin transport wrappers (request validation + HTTP mapping only).
- [ ] Manifest save/validate behavior remains atomic and unchanged.
- [ ] Delete confirmation semantics (`confirm`, `confirm_text`, sole in-use guard) are preserved.
- [ ] Existing deletion tests pass; new tests cover service-level delete behavior.

## Dependencies

- Registry Path Policy Unification

## Execution Plan

1. Extract mutation helpers from router into service-layer functions.
2. Keep HTTP-specific concerns in API layer only.
3. Add/adjust service tests for delete guardrails.
4. Verify endpoint compatibility with current clients.
5. Run API registry tests and python model registry tests.

## Notes

- Do not change endpoint paths or payload contracts in this ticket.
