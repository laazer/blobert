# Registry Path Policy Unification

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Consolidate all registry path normalization and allowlist enforcement into shared package service modules so API routes do not carry a second security policy implementation.

Target overlap:
- `asset_generation/web/backend/routers/registry.py` (`_normalize_registry_relative_glb_path`)
- `blobert_asset_gen.services.registry` (or transitional `asset_generation/python/src/model_registry/service.py`) allowlist/validation logic

## Acceptance Criteria

- [ ] Path canonicalization/validation API is exposed from package service layer.
- [ ] API registry router delegates path checks to shared service API.
- [ ] Duplicated allowlist prefixes are removed from router.
- [ ] Traversal, encoding, extension, and forbidden path class tests pass through shared policy.
- [ ] No behavioral regression in existing registry endpoints.

## Dependencies

- Backend-Python Import Adapter

## Execution Plan

1. Define canonical registry path validation function in service layer.
2. Migrate API route calls to service API for all path-entry endpoints.
3. Remove router-local path normalization helpers/constants.
4. Expand adversarial tests for malformed encoded paths.
5. Run registry API and service test suites.

## Notes

- Treat this as a security ticket; preserve fail-closed behavior.
