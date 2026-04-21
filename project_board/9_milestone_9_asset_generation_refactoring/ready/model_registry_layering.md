# Model Registry Layering

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Decompose `model_registry/service.py` (684 LOC) from a god object into 4 focused, layered modules. Separate concerns: schema validation, file I/O, version migrations, and business logic. Enable each layer to be tested and modified independently.

## Acceptance Criteria

- [ ] `schema.py` (new): Contains all TypedDict definitions, validation constants, and `validate_manifest()` function
- [ ] `store.py` (new): Handles manifest file I/O (load, save); no validation logic
- [ ] `migrations.py` (new): Handles version migration logic and `normalize_*` functions
- [ ] `service.py` (refactored): Business logic layer using schema, store, and migrations; public API unchanged
- [ ] All existing tests pass; test coverage maintained or improved
- [ ] Type hints added: dict → dict[str, T], Pydantic models for API payloads
- [ ] No circular dependencies between modules
- [ ] Backend routes (`routers/registry.py`) work without modification

## Dependencies

- Import standardization (tickets #1): Must standardize imports first

## Execution Plan

### Approach

1. Extract TypedDict definitions and validation logic → `schema.py`
2. Extract file I/O (manifest load/save) → `store.py`
3. Extract migration/normalization helpers → `migrations.py`
4. Refactor `service.py` to delegate to the three new modules
5. Add Pydantic models for FastAPI request/response payloads
6. Update all internal imports to use new modules
7. Run full test suite and backend integration tests

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `schema.py` | ~150 | TypedDict, enums, validation rules | `validate_manifest()`, `EnemyVersion`, `RegistryFamily` |
| `store.py` | ~100 | Load/save manifest.json, create backups | `load_manifest()`, `save_manifest()` |
| `migrations.py` | ~120 | Version normalization, field migration | `normalize_registry_family_block()`, `normalize_version_entry()` |
| `service.py` | ~200 | Business logic, public API | `load_effective_manifest()`, `spawn_eligible_paths()`, `register_version()` |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `schema.py` (new) | Create validation layer | High |
| `store.py` (new) | Create I/O layer | High |
| `migrations.py` (new) | Create migration layer | High |
| `service.py` | Refactor to use new modules | High |
| `routers/registry.py` | Update service imports (no logic change) | Medium |

### Success Criteria

- All 4 modules < 200 LOC
- `pytest tests/` passes with no failures
- Backend integration tests pass
- Type coverage improved (dict[str, T] used throughout)
- No functional changes to public API

## Notes

- High test coverage (5 existing tests) makes this safe to refactor
- Clear separation enables future schema evolution
- Pydantic models improve API documentation and validation
