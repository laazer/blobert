# Blender Utilities Split

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Split the jumbled `core/blender_utils.py` (628 LOC) into 3 focused modules organized by responsibility: primitives (sphere, cylinder, cone, box), creature parts (eye, mouth, tail), and mesh operations (smoothing, weight painting, normals). Improve code discoverability and clarity.

## Acceptance Criteria

- [ ] `primitives.py` (new): Primitive creators (create_sphere, create_cylinder, create_cone, create_box)
- [ ] `creature_parts.py` (new): Creature-specific builders (create_eye_mesh, create_mouth_mesh, create_tail_mesh, create_pupil_mesh)
- [ ] `mesh_ops.py` (new): Mesh transformations (apply_smooth_shading, set_vertex_weight_painted_group, detect_body_scale_from_mesh, etc.)
- [ ] `blender_utils.py` (refactored): Lightweight re-export module for backward compatibility
- [ ] All imports updated; no dangling references
- [ ] All tests pass with new structure
- [ ] Type hints improved: no Variant types, explicit return types

## Dependencies

- Import standardization (ticket #1): Ensures clean imports

## Execution Plan

### Approach

1. Categorize current blender_utils.py functions by responsibility
2. Create 3 new focused modules with extracted functions
3. Keep blender_utils.py as thin re-export module for backward compatibility
4. Update all imports to use new modules directly
5. Delete old blender_utils.py (once re-exports deprecated)
6. Run full test suite

### Module Breakdown

| Module | Lines | Responsibility | Public API |
|--------|-------|-----------------|------------|
| `primitives.py` | ~150 | Basic geometry creation | `create_sphere()`, `create_cylinder()`, `create_cone()`, `create_box()` |
| `creature_parts.py` | ~200 | Creature-specific meshes | `create_eye_mesh()`, `create_pupil_mesh()`, `create_mouth_mesh()`, `create_tail_mesh()` |
| `mesh_ops.py` | ~150 | Mesh transformations | `apply_smooth_shading()`, `set_vertex_weight_painted_group()`, `detect_body_scale_from_mesh()`, etc. |
| `blender_utils.py` | ~30 | Re-exports (deprecated) | Re-export all for backward compat |

### Function Allocation

| Function | New Home |
|----------|----------|
| create_sphere | primitives.py |
| create_cylinder | primitives.py |
| create_cone | primitives.py |
| create_box | primitives.py |
| create_eye_mesh | creature_parts.py |
| create_pupil_mesh | creature_parts.py |
| create_mouth_mesh | creature_parts.py |
| create_tail_mesh | creature_parts.py |
| apply_smooth_shading | mesh_ops.py |
| set_vertex_weight_painted_group | mesh_ops.py |
| detect_body_scale_from_mesh | mesh_ops.py |
| *others* | mesh_ops.py |

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `primitives.py` (new) | Extract primitive creators | High |
| `creature_parts.py` (new) | Extract creature builders | High |
| `mesh_ops.py` (new) | Extract mesh operations | High |
| `blender_utils.py` | Reduce to re-exports, then delete | High |
| All consumers | Update imports | Medium |

### Success Criteria

- 3 modules with clear, single responsibility
- Each module < 250 LOC
- `pytest tests/core/` all pass
- No functionality changes; output identical
- Import paths clear and semantic
- Type hints: explicit return types for all functions

## Notes

- Low-risk refactoring; functions already independent
- Improves IDE navigation (know where to find primitives vs. operations)
- Good practice for onboarding new developers
- Creature parts grouping makes sense for animal-specific logic
