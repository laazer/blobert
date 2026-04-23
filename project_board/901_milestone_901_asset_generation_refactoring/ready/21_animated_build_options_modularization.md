# Animated Build Options Modularization

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Split animated build options logic into modular layers to improve DRY/OOP boundaries and reduce hidden coupling from local imports and broad dict contracts.

## Acceptance Criteria

- [ ] Build-options module is split into schema/defaults/merge/migration/validation layers.
- [ ] Local/lazy imports used only for justified runtime constraints.
- [ ] Shared typed contracts replace broad internal `dict[str, Any]` where practical.
- [ ] Existing build options API payload shape remains stable.
- [ ] Build options and adversarial validation tests pass.

## Dependencies

- Animated Build Options Consolidation
- Shared Manifest Schema Contract

## Execution Plan

1. Extract modular build-options components.
2. Introduce typed contracts for core option structures.
3. Refactor validation pipeline to consume typed intermediate structures.
4. Remove unnecessary function-local imports through dependency inversion.
5. Run build-options and related material pipeline tests.
