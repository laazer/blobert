# Backend-Python Import Adapter

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Replace per-router `sys.path` mutation and repeated Blender-stub bootstrap with a single adapter module. This creates one reliable boundary for importing asset-generation services during the transition to a unified `blobert_asset_gen` package architecture.

Target duplication:
- `asset_generation/web/backend/routers/registry.py`
- `asset_generation/web/backend/routers/meta.py`
- `asset_generation/web/backend/routers/assets.py`

## Acceptance Criteria

- [ ] New adapter module centralizes Python root path injection and Blender stub initialization.
- [ ] Routers stop mutating `sys.path` directly.
- [ ] Registry/meta/assets routes import Python modules through adapter only.
- [ ] Adapter exposes package-root resolution abstraction that can switch from `asset_generation/python/src` to `asset_generation/python/blobert_asset_gen` without router changes.
- [ ] Existing backend tests pass without route behavior regressions.
- [ ] Adapter has focused tests for import/bootstrap behavior in test environment.

## Dependencies

- None (recommended first ticket for follow-on consolidation work).

## Execution Plan

1. Create `backend/services/python_bridge.py` (or equivalent) for import/bootstrap.
2. Move `ensure_blender_stubs` and canonical path setup logic into bridge.
3. Replace router-local setup calls with bridge API.
4. Add bridge configuration point for current/future package root resolution.
5. Add regression tests for import failures and startup behavior.
6. Run backend and relevant python integration tests.

## Notes

- Keep public API endpoints unchanged.
- This ticket is the migration seam for package convergence; all follow-on tickets should consume bridge APIs rather than hardcoding import roots.
