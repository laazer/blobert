# Shared Manifest Schema Contract

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Introduce shared typed schema models for registry manifest and API payloads so API transport models and domain validation stop drifting.

Target overlap:
- `asset_generation/web/backend/routers/registry.py` Pydantic request/response models
- `blobert_asset_gen.services.registry` (or transitional `model_registry/service.py`) typed manifest rules

## Acceptance Criteria

- [ ] Shared schema module introduced for registry manifest and key payloads.
- [ ] API route models and service validation reference shared typed definitions where feasible.
- [ ] `dict[str, Any]` usage in cross-boundary contracts is reduced.
- [ ] Existing API response shapes remain backward compatible.
- [ ] Contract tests cover schema parity between backend and service.

## Dependencies

- Model Registry Layering
- Registry Mutation Service Boundary

## Execution Plan

1. Define shared schema models (TypedDict and/or Pydantic) in model registry package.
2. Migrate service contract boundaries to typed models.
3. Migrate API request/response models to shared contracts incrementally.
4. Add parity tests for schema compatibility and migration behavior.
5. Run API registry tests plus python spec/contract tests.

## Notes

- This ticket should be scoped to contract parity, not endpoint redesign.
