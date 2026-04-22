# Material System DRY OOP Decomposition

**Epic:** Milestone 901 – Asset Generation Refactoring  
**Status:** Ready

---

## Description

Decompose `blobert_asset_gen.domain.materials.material_system` (currently `asset_generation/python/src/materials/material_system.py`) into cohesive components and remove duplicated color/finish/texture handling across material modules.

## Acceptance Criteria

- [ ] Material orchestration is separated from texture-mode handlers and feature-zone logic.
- [ ] Shared color parsing and finish mapping utilities are extracted and reused.
- [ ] Texture generation flow uses common persistence/loading helpers where applicable.
- [ ] Public behavior of material assignment and build options remains compatible.
- [ ] Material tests pass and coverage is maintained or improved.

## Dependencies

- Material System Refactoring
- Export Directory Contract Consolidation

## Execution Plan

1. Extract utility modules (`color_codec`, `finish_presets`, texture I/O helpers).
2. Move orchestration logic into smaller services.
3. Refactor callers to use extracted contracts.
4. Add regression tests for finish, hex-color, and texture modes.
5. Run material and adversarial test suites.
