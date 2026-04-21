# Zone Geometry Extras Decomposition

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Decompose `enemies/zone_geometry_extras_attach.py` (718 LOC) monolith into 3-4 focused modules: geometry math (ellipsoid surface, normals), placement strategy (clustering, distribution), attachment handlers (per-enemy specifics), and a thin dispatcher. Extract testable math from untestable Blender context code.

## Acceptance Criteria

- [ ] `geometry_math.py` (new): Pure geometry utilities (ellipsoid surface, normal vectors, point sampling)
- [ ] `placement_strategy.py` (new): Placement algorithms (clustering, distribution, facing)
- [ ] `attachment.py` (new): Enemy-specific handlers (body extras, head extras, player extras)
- [ ] Dispatcher logic thin and readable
- [ ] All extracted math functions unit testable without bpy context
- [ ] All existing tests pass; test coverage improved (currently untestable)
- [ ] Geometry math functions fully type-hinted

## Dependencies

- Enemy builder template extraction (ticket #6): Optional but recommended for understanding rig context

## Execution Plan

### Approach

1. Extract ellipsoid and geometry math → `geometry_math.py`
2. Extract placement algorithms → `placement_strategy.py`
3. Organize per-enemy handlers → `attachment.py`
4. Keep dispatcher thin and readable
5. Write unit tests for geometry_math (pure functions, no bpy)
6. Test placement strategies with mocked geometry
7. Integration test full flow end-to-end

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `geometry_math.py` | ~100 | Ellipsoid surface, normals, point sampling | `ellipsoid_surface_points()`, `compute_normal()`, `sample_facing_direction()` |
| `placement_strategy.py` | ~150 | Clustering, distribution logic | `compute_placement_grid()`, `apply_clustering()`, `apply_distribution()` |
| `attachment.py` | ~250 | Enemy-specific attachment | `attach_to_body()`, `attach_to_head()`, per-enemy handlers |
| `__init__.py` | ~20 | Dispatcher, public API | `append_animated_enemy_zone_extras()` |

### Current Code Analysis

| Section | LOC | New Home | Testability |
|---------|-----|----------|------------|
| ellipsoid math (lines 38-54) | 17 | geometry_math.py | Fully testable (pure) |
| placement validation (lines 56-90) | 35 | placement_strategy.py | Testable with mocks |
| Main dispatch (lines 162-215) | 54 | attachment.py dispatch | N/A (dispatcher) |
| Body ellipsoid (lines 216-415) | 200 | attachment.py body_handler | Testable after extraction |
| Head ellipsoid (lines 416-640) | 225 | attachment.py head_handler | Testable after extraction |
| Player extras (lines 641-718) | 78 | attachment.py player_handler | Testable after extraction |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `geometry_math.py` (new) | Extract ellipsoid/normal math | High |
| `placement_strategy.py` (new) | Extract placement algorithms | High |
| `attachment.py` (new) | Organize per-enemy handlers | High |
| `__init__.py` (new) | Thin dispatcher + public API | High |
| `zone_geometry_extras_attach.py` | Delete (consolidate into above) | High |

### Success Criteria

- geometry_math functions 100% unit testable (no bpy context)
- placement_strategy 90%+ testable with mocked geometry
- Full integration tests validate end-to-end zone extras application
- All 5 enemies (spider, slug, imp, carapace_husk, claw_crawler) produce identical zone extras
- New module structure enables adding 6th enemy handler without touching geometry logic
- Type hints: geometry functions explicitly typed (no Variant, no Any)

## Testing Strategy

### Unit Tests (Pure Math)
- Test ellipsoid_surface_points() with known sphere
- Test normal computation with sample points
- Test placement grid generation and spacing

### Integration Tests
- Mock bpy, run full zone extras pipeline
- Compare GLB output before/after refactoring
- Validate zone extras placement on 5 known enemies

## Notes

- CRITICAL: Currently this code is untestable. Extract enables validation via tests.
- Ellipsoid math is solid; extraction is mechanical
- Placement logic has some heuristics—tests help document intended behavior
- Per-enemy handlers are boilerplate; good candidate for parametrized tests
- Future: Zone extras placement could be data-driven (placement spec format)
