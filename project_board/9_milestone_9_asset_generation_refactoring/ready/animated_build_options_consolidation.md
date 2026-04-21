# Animated Build Options Consolidation

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Consolidate 7 scattered `animated_build_options*.py` files (1,669 LOC total) into 2 cohesive, focused modules. Clarify the separation between schema definitions, validation rules, and parsing logic. This is CRITICAL for adding new enemies without sprawl.

## Acceptance Criteria

- [ ] `schema.py` (new): All control definitions, zones, feature defs consolidated (TypedDict-based)
- [ ] `validate.py` (new): All validation rules and normalization logic
- [ ] Original 7 files deleted (including satellite `_appendage_defs`, `_mesh_controls`, etc.)
- [ ] Public API preserved: `options_for_enemy()`, `get_control_definitions()`, validation functions
- [ ] All existing tests pass; test coverage maintained
- [ ] Adding a new enemy now requires < 150 LOC changes (down from 250+)
- [ ] No circular imports between schema and validate modules
- [ ] Type hints added: dict[str, Any] → dict[str, ControlValue], TypedDict for specific structures

## Dependencies

- Import standardization (ticket #1)
- Model registry layering (ticket #2): Optional

## Execution Plan

### Approach

1. Create `schema.py` with unified control definitions (appendage defs, mesh controls, zone texture, feature defs)
2. Create `validate.py` with all validation and normalization logic
3. Extract per-enemy configuration presets into a data structure (not scattered in functions)
4. Update `options_for_enemy()` to use new modules
5. Delete 6 satellite files
6. Update all builder imports
7. Run full test suite

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `schema.py` | ~700 | Control defs, zone textures, feature defs, presets | `get_control_definitions()`, `CONTROL_SCHEMA`, `ZONE_TEXTURE_PATTERNS`, enemy presets |
| `validate.py` | ~200 | Validation rules, normalization, range checks | `validate_build_options()`, `normalize_controls()` |
| `__init__.py` | ~20 | Re-exports, public API | `options_for_enemy()`, `validate_build_options()` |

### Files to Consolidate

| File | LOC | Consolidate Into |
|------|-----|------------------|
| `animated_build_options.py` | 912 | schema.py + validate.py |
| `animated_build_options_appendage_defs.py` | 288 | schema.py |
| `animated_build_options_mesh_controls.py` | 145 | schema.py |
| `animated_build_options_validate.py` | 113 | validate.py |
| `animated_build_options_zone_texture.py` | 32 | schema.py |
| `animated_build_options_spider_eye.py` | 69 | schema.py (per-enemy specifics) |
| `animated_build_options_part_feature_defs.py` | 110 | schema.py |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `schema.py` (new) | Consolidate all defs | High |
| `validate.py` (new) | Consolidate validation | High |
| `__init__.py` (new) | Public API re-exports | High |
| 7 old files | Delete | High |
| All builder files | Update imports from `utils.animated_build_options*` → `utils.build_options` | High |
| Test files | Update imports | Medium |

### Success Criteria

- 2 modules with clear responsibility
- Adding new enemy: copy control preset, add to schema, no scattered file changes
- `pytest tests/utils/test_animated_build_options*.py` all pass
- All enemies continue to work (no functional changes)
- Type hints: dict[str, ControlValue] used throughout
- Git diff shows only consolidation, no logic changes

## Notes

- CRITICAL blocker for new enemies; address early
- High test coverage (12 dedicated tests) provides safety
- Untangle spider-eye-specific logic (move to spider builder, not build options)
- Clear ownership per control type prevents future sprawl
