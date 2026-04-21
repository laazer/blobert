# Utility File Consolidation

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Reorganize the `utils/` directory (20+ files with unclear boundaries) into a clear, navigable structure. Consolidate constants, configuration, export utilities, and shared helpers into focused modules. Reduce cognitive overhead of finding things.

## Acceptance Criteria

- [ ] `config.py` (new): All constants and configuration values (EnemyTypes, AnimatedBuildOptions enums, etc.)
- [ ] `build_options.py` (refactored): Animated build options schema and validation (from Phase 2 ticket)
- [ ] `export.py` (new): Unified export naming, GLB validation, file I/O utilities
- [ ] `validation.py` (new): Shared validation helpers (not specific to build options or materials)
- [ ] `simple_viewer.py` (keep): Visualization utility (no changes)
- [ ] Orphaned utility files consolidated or deleted
- [ ] All imports updated; no dangling references
- [ ] All tests pass with new structure
- [ ] Type hints improved: no bare `dict`, use dict[str, T] or TypedDict

## Dependencies

- Import standardization (ticket #1)
- Animated build options consolidation (ticket #4): Parallel or after

## Execution Plan

### Approach

1. Audit current utils/ files and categorize by responsibility
2. Create `config.py` with all constants
3. Create `export.py` with export-related utilities
4. Create `validation.py` with shared validation helpers
5. Move `build_options.py` from Phase 2 into utils
6. Update all imports across codebase
7. Delete empty/orphaned files
8. Run full test suite

### Current Utils State & Consolidation Plan

| Current File(s) | New Location | LOC | Action |
|----------|---------------|-----|--------|
| constants.py | config.py | 150+ | Move, consolidate |
| enemy_slug_registry.py | config.py | 50+ | Merge |
| animated_build_options*.py | build_options.py | 1,669 | Phase 2 output |
| export_*.py (scattered) | export.py | 100+ | Consolidate |
| simple_viewer.py | simple_viewer.py | 150 | Keep as-is |
| materials.py (constants) | Keep separate | 187 | Keep (materials layer) |
| Other utility helpers | validation.py | TBD | Consolidate |

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `config.py` | ~200 | All project constants, enums, defaults | `EnemyTypes`, `ZoneTypes`, `MATERIAL_DEFAULTS`, etc. |
| `build_options.py` | ~900 | Build option schema and validation | From Phase 2 consolidation |
| `export.py` | ~150 | Export utilities, GLB naming, file I/O | `get_export_path()`, `validate_glb()`, `export_manifest_entry()` |
| `validation.py` | ~100 | Shared validation helpers | `validate_path()`, `validate_enum()`, etc. |

### File Changes Summary

| Action | Files | Priority |
|--------|-------|----------|
| Create | config.py, export.py, validation.py | High |
| Consolidate into | config.py (constants.py, enemy_slug_registry.py) | High |
| Move/Integrate | build_options.py from Phase 2 | High |
| Keep | simple_viewer.py, materials.py | N/A |
| Delete | Orphaned/empty files (post-audit) | High |
| Update imports | All builders, routers, pipeline code | High |

### Success Criteria

- `utils/` now has 6 focused modules instead of 20+ scattered files
- Each module < 250 LOC with clear responsibility
- All tests pass with new import structure
- IDE autocomplete works; imports discoverable
- No circular dependencies
- Type hints: dict → dict[str, T], enums used instead of string literals

## Notes

- Can run in parallel with Phase 2 refactorings
- High impact on code navigation and onboarding
- Enums reduce string literal bugs (type safety)
- Export consolidation unifies GLB naming conventions
