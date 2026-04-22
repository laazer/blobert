# Backend Registry Service Extraction and Router Thinning

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Refactor `asset_generation/web/backend/routers/registry.py` into a thin transport layer backed by explicit package service objects. Move manifest mutation/query workflows out of route handlers and into shared service modules.

## Acceptance Criteria

- [ ] Registry router no longer contains direct domain mutation helpers.
- [ ] Query and mutation workflows live in package service module(s).
- [ ] Router responsibilities are limited to request validation, response mapping, and status codes.
- [ ] Existing registry endpoint behavior remains backward compatible.
- [ ] Registry API tests pass unchanged or with minimal transport-only updates.

## Dependencies

- Backend-Python Import Adapter
- Registry Mutation Service Boundary

## Execution Plan

1. Introduce `blobert_asset_gen.services.registry_query` and `blobert_asset_gen.services.registry_mutation` (or transitional equivalents).
2. Move route-local helper logic into services.
3. Keep HTTP mapping in router only.
4. Add focused unit tests for service-layer operations.
5. Run full registry backend tests.
