# Type Hints and Documentation

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Improve code quality across refactored modules by adding comprehensive type hints and documentation. Replace bare `dict` with `dict[str, T]`, add Pydantic models for API payloads, document magic constants, and add module-level docstrings explaining architectural decisions.

## Acceptance Criteria

- [ ] No bare `dict` types remain; all use `dict[str, T]` or `Mapping[str, T]` or TypedDict
- [ ] Pydantic models added for all FastAPI request/response payloads
- [ ] Magic numbers extracted to named constants with explanatory comments
- [ ] Module-level docstrings added explaining responsibility and design decisions
- [ ] Function docstrings for non-obvious parameters or complex logic
- [ ] Type hints for 90%+ of functions (< 10% exemptions for Blender-facing code)
- [ ] `mypy --strict` passes on all refactored modules
- [ ] No loss of functionality; behavior unchanged

## Dependencies

- All Phase 1, 2, 3 tickets: Completes refactoring cycle after all decomposition done

## Execution Plan

### Approach

1. Run `mypy --strict` on all refactored modules and capture gaps
2. Add TypedDict definitions for complex dict structures
3. Add Pydantic models for API payloads (material_system, model_registry)
4. Extract magic numbers to named constants
5. Add module-level docstrings explaining architecture
6. Add targeted function docstrings for complex logic
7. Validate type safety with mypy

### Type Coverage Analysis

| Module | Current Coverage | Target | Gap |
|--------|------------------|--------|-----|
| schema.py | ~70% | 95% | Add TypedDict for all config structs |
| service.py | ~60% | 95% | Type returns from validators |
| material_system.py | ~50% | 95% | Pydantic models for payloads |
| builders | ~40% | 90% | Type rig params, mesh objects |
| blender_utils | ~30% | 85% | Blender context exemptions OK |

### Priority Type Conversions

| Change | Location | Justification |
|--------|----------|---------------|
| dict → dict[str, EnemyVersion] | model_registry.service | Clear value type |
| dict → dict[str, Material] | material_system | Material lookup clarity |
| dict → MaterialConfig (TypedDict) | material_system.py | Fixed key set for config |
| dict[str, Any] → Pydantic model | FastAPI routers | API documentation + validation |
| Magic numbers → constants | All | Better maintainability |

### File Changes Summary

| File | Changes | Priority |
|------|---------|----------|
| schema.py | Add TypedDict definitions | High |
| service.py | Type all dict structures | High |
| material_system.py | Add Pydantic models | High |
| presets.py | Extract magic color values | Medium |
| builders.py | Type rig parameters | Medium |
| blender_utils.py | Document bpy exemptions | Low |
| Test files | Update type annotations | Medium |

### Example Refactorings

**Before:**
```python
def get_materials(enemy_type: str) -> dict:
    """Returns materials for an enemy."""
    materials = {}
    for zone in ZONES:
        materials[zone] = create_material(...)
    return materials
```

**After:**
```python
class EnemyMaterials(TypedDict):
    """Material set for a single enemy type."""
    body: Material
    head: Material
    limbs: Material

def get_materials(enemy_type: str) -> EnemyMaterials:
    """Returns material set for an enemy type.
    
    Args:
        enemy_type: One of 'spider', 'imp', 'slug', etc.
        
    Returns:
        EnemyMaterials: Typed dict with body, head, limb materials.
    """
    ...
```

### Magic Number Extraction Example

**Before:**
```python
# In multiple files
for i in range(5):  # What does 5 mean?
    angle = i * (360.0 / 5)
    ...
```

**After:**
```python
# In config.py
NUM_ZONE_EXTRA_PLACEMENT_ANGLES = 5
ZONE_EXTRA_BASE_ANGLE_STEP_DEG = 360.0 / NUM_ZONE_EXTRA_PLACEMENT_ANGLES

# In attachment.py
for i in range(NUM_ZONE_EXTRA_PLACEMENT_ANGLES):
    angle = i * ZONE_EXTRA_BASE_ANGLE_STEP_DEG
```

### Success Criteria

- `mypy --strict` passes on all refactored modules
- All dict types have explicit value types
- All FastAPI endpoints use Pydantic models
- All magic constants have comments explaining their purpose
- Documentation reads naturally for future developers
- No functionality changes; behavior identical

## Notes

- Low-risk quality improvement
- Can run in parallel with Phase 3 refactorings or as final pass
- Type safety enables future refactoring with confidence
- Pydantic models improve FastAPI OpenAPI documentation
- Magic constant extraction improves readability (one of the most neglected best practices)
