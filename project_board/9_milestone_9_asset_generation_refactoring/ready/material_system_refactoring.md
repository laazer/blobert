# Material System Refactoring

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Decompose `materials/material_system.py` (896 LOC) from a god object into focused, single-responsibility modules. Extract texture handlers into a registry pattern, pull out material presets, separate feature zone logic, and isolate enemy material lookup. Enable independent testing and extension of each layer.

## Acceptance Criteria

- [ ] `system.py` (refactored): < 150 LOC, orchestration only (setup_materials, get_enemy_materials, apply_material_to_object)
- [ ] `presets.py` (new): Material finishes, color profiles, per-enemy defaults
- [ ] `texture_handlers.py` (new): Registry pattern for texture handlers (organic, gradient, stripes, spots)
- [ ] `feature_zones.py` (new): Feature zone override logic extracted from apply_feature_slot_overrides
- [ ] `material_lookup.py` (new): Enemy type → materials mapping logic
- [ ] All existing tests pass; expand to cover extracted modules
- [ ] Type hints added: dict[str, Material], remove Any types where possible
- [ ] No texture handler requires bpy context for definition (only for application)
- [ ] Backend routes use new imports without modification

## Dependencies

- Import standardization (ticket #1)
- Model registry layering (ticket #2): Optional but recommended before material refactoring

## Execution Plan

### Approach

1. Extract finish presets and color mappings → `presets.py`
2. Extract texture handler dispatch logic → `texture_handlers.py` (registry pattern)
3. Extract feature zone override math → `feature_zones.py`
4. Extract enemy material selection → `material_lookup.py`
5. Refactor `system.py` to use extracted modules
6. Add type hints: `dict[str, Material]`, Pydantic for payload validation
7. Update all internal imports
8. Expand test coverage to 85%+

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `system.py` | ~150 | Orchestration, setup, lookups | `setup_materials()`, `get_enemy_materials()`, `apply_material_to_object()` |
| `presets.py` | ~120 | Finish/color/theme data | `FINISHES`, `MaterialColors`, `get_preset_for_theme()` |
| `texture_handlers.py` | ~200 | Texture handler registry | `register_handler()`, `apply_texture()`, handlers dict |
| `feature_zones.py` | ~180 | Feature slot override logic | `apply_feature_slot_overrides()`, `apply_zone_texture_pattern_overrides()` |
| `material_lookup.py` | ~80 | Enemy → materials mapping | `get_materials_for_enemy_type()` |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `presets.py` (new) | Extract finish/color data | High |
| `texture_handlers.py` (new) | Extract handler registry | High |
| `feature_zones.py` (new) | Extract zone override logic | High |
| `material_lookup.py` (new) | Extract enemy lookup | High |
| `system.py` | Refactor to dispatch | High |
| `gradient_generator.py` | No change (keep as-is) | N/A |
| `stripes_texture.py` | No change (keep as-is) | N/A |
| Enemies builder files | Update imports | Medium |
| Test files | Expand coverage | Medium |

### Success Criteria

- All 5 modules < 200 LOC
- `pytest tests/materials/` passes with 85%+ coverage
- Texture handler registry testable without bpy
- Feature zone logic testable in isolation
- No functional changes to public API
- Material application still works end-to-end

## Notes

- 23 existing material tests provide safety net
- High coupling risk—tests critical before and after refactoring
- Texture handlers are good candidate for pytest parametrization
- Extract logic without touching gradient_generator.py (already good shape)
