# Import Standardization

**Epic:** Milestone 9 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Standardize import patterns across the asset generation Python codebase. Remove `sys.path.insert()` hacks from entry points and consolidate on absolute imports (`from src.enemies.animated import ...`). This unblocks IDE autocomplete, simplifies test setup, and aligns with standard Python packaging.

## Acceptance Criteria

- [ ] All entry points (generator.py, player_generator.py, level_generator.py) use absolute imports with no `sys.path.insert()` calls
- [ ] All internal modules use absolute imports (`from src.enemies.animated import ...`) consistently
- [ ] No `try/except ImportError` fallback patterns exist
- [ ] `__init__.py` files expose public APIs via re-exports (schema, service, material_system, etc.)
- [ ] All tests pass with new import structure
- [ ] IDE autocomplete works correctly for all modules

## Dependencies

- None (foundational change that unblocks all Phase 2 work)

## Execution Plan

### Approach

1. Create comprehensive `__init__.py` files in all package directories with public API re-exports
2. Replace all `sys.path.insert()` calls in entry points with proper package setup
3. Convert all internal relative imports (`from ..utils import X`) to absolute imports (`from src.utils import X`)
4. Remove any hybrid import patterns (`try/except ImportError`)
5. Update backend integration code to use new import paths
6. Run full test suite to verify no import breakage

### File Changes Summary

| File | Change | Priority |
|------|--------|----------|
| `src/__init__.py` (new) | Create with key re-exports | High |
| `src/enemies/__init__.py` | Expose builders (AnimatedEnemyBuilder, etc.) | High |
| `src/materials/__init__.py` | Expose material_system | High |
| `src/model_registry/__init__.py` | Expose service | High |
| `src/generator.py` | Remove sys.path.insert(), use absolute imports | High |
| `src/player_generator.py` | Remove sys.path.insert(), use absolute imports | High |
| `src/level_generator.py` | Remove sys.path.insert(), use absolute imports | High |
| `asset_generation/web/backend/routers/*.py` | Update imports for new paths | High |
| All module imports | Replace relative with absolute | Medium |

### Success Criteria

- All imports follow pattern: `from src.{domain}.{module} import {item}`
- `python -m py_compile` passes on all .py files without import errors
- IDE (VSCode, PyCharm) shows autocomplete for all imports
- Test suite runs with `pytest` (no custom path setup needed)
- Git diff shows clean, mechanical changes (no logic changes)

## Notes

- This is mechanical work with low functional risk
- Strong test coverage (100+ tests) provides safety net
- Enables cleaner code organization in Phase 2
