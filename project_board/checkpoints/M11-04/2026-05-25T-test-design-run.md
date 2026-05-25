# Checkpoint: M11-04 Test Design Run

**Agent:** Test Designer Agent
**Date:** 2026-05-25
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/04_attack_resource.md`
**Spec:** `project_board/specs/attack_resource_spec.md`

## What was done

Wrote primary behavioral test suite at `tests/scripts/attacks/test_attack_resource.gd`.

- 23 test functions covering ATK-01 through ATK-09
- 131 assertions total
- Extends `res://tests/utils/test_utils.gd` (project convention)
- Auto-discovered by `tests/run_tests.gd` (test_ prefix)
- Loads implementation via `load("res://scripts/attacks/attack_resource.gd")`

## Test coverage map

| Spec Requirement | Test Functions | Assertion Count |
|------------------|---------------|-----------------|
| ATK-01 (instantiation) | `test_atk01_instantiation` | 3 |
| ATK-02 (identity defaults) | `test_atk02_identity_defaults`, `test_atk02_identity_assignable` | 6 |
| ATK-03 (effect type) | `test_atk03_effect_type_default`, `test_atk03_effect_type_known_values`, `test_atk03_effect_type_extensibility` | 6 |
| ATK-04 (combat params) | `test_atk04_combat_defaults`, `test_atk04_combat_assignable`, `test_atk04_knockback_direction_values` | 15 |
| ATK-05 (projectile) | `test_atk05_projectile_defaults`, `test_atk05_projectile_assignable` | 4 |
| ATK-06 (visual) | `test_atk06_visual_defaults`, `test_atk06_visual_assignable` | 10 |
| ATK-07 (modifiers) | `test_atk07_modifiers_default`, `test_atk07_modifiers_set_get`, `test_atk07_modifiers_get_nonexistent`, `test_atk07_modifiers_coexist` | 12 |
| ATK-08 (serialization) | `test_atk08_duplicate_preserves`, `test_atk08_duplicate_independence` | 20 |
| ATK-09 (example configs) | `test_atk09_claw_swipe`, `test_atk09_acid_spit`, `test_atk09_carapace_slam`, `test_atk09_adhesion_lunge` | 55 |

## Expected RED state

All 23 test functions fail (load returns null for nonexistent `scripts/attacks/attack_resource.gd`).
Expected RED count: **23 failures, 0 passes**.

## Assumptions

| # | Would have asked | Assumption made | Confidence |
|---|-----------------|-----------------|------------|
| 1 | Whether to use `_make()` helper vs inline load per test | Used `_make()` helper to reduce duplication, consistent with DRY | High |
| 2 | Whether Resource.duplicate() preserves Dictionary modifier values by value or reference | Tested both preservation AND independence (ATK-08) — covers both behaviors | High |
| 3 | Whether Color components should be tested individually vs Color equality | Individual component comparison using `_assert_eq_float` for precision control | High |

## Spec gaps

None identified. ATK-01 through ATK-09 are fully testable as specified.

## Log

- Created `tests/scripts/attacks/` directory
- Wrote `tests/scripts/attacks/test_attack_resource.gd` (481 lines, 23 tests, 131 assertions)
- All tests expected RED until implementation at `scripts/attacks/attack_resource.gd`
