# Checkpoint: M11-05 Test Design Run

**Ticket:** M11-05 — Implement AttackExecutor with MELEE_SWIPE and PROJECTILE_SPIT handlers
**Agent:** Test Designer Agent
**Date:** 2026-05-25
**Stage transition:** TEST_DESIGN → TEST_BREAK (Rev 3 → 4)

## Summary

Wrote 38 behavioral tests at `tests/scripts/attacks/test_attack_executor.gd` covering AEX-1 through AEX-8 from the frozen spec (`project_board/specs/attack_executor_spec.md`).

## Test File

`tests/scripts/attacks/test_attack_executor.gd` — 38 test functions, all expected RED (implementation `scripts/attacks/attack_executor.gd` does not exist yet).

## AEX Coverage Matrix

| AEX Req | Test Functions | Count | Key Assertions |
|---------|---------------|-------|----------------|
| AEX-1 | test_aex01_script_loads, test_aex01_class_identity | 2 | Script loads, is Node, not Resource |
| AEX-2 | test_aex02_melee_dispatch, test_aex02_projectile_dispatch, test_aex02_active_guard, test_aex02_active_resets_after_handler | 4 | Dispatch routing, active guard blocks overlap, _is_active resets |
| AEX-3 | test_aex03_melee_hits_in_range, test_aex03_melee_misses_out_of_range, test_aex03_melee_damage_and_knockback, test_aex03_melee_no_enemies, test_aex03_melee_multiple_enemies | 5 | In-range hit, out-of-range miss, damage+knockback values, no crash on empty, multi-enemy AoE |
| AEX-4 | test_aex04_projectile_created, test_aex04_projectile_properties, test_aex04_projectile_direction, test_aex04_zero_speed | 4 | Child added to grandparent, property transfer, facing direction, zero speed valid |
| AEX-5 | test_aex05_knockback_away, test_aex05_knockback_toward, test_aex05_knockback_none, test_aex05_knockback_zero_magnitude, test_aex05_knockback_degenerate, test_aex05_knockback_z_zeroed, test_aex05_knockback_unknown_direction | 7 | Away/toward/none vectors, zero mag, degenerate position default, z always 0, unknown dir |
| AEX-6 | test_aex06_poison, test_aex06_acid, test_aex06_slow, test_aex06_guard_no_crash, test_aex06_empty_modifiers, test_aex06_multiple_concurrent, test_aex06_default_values | 7 | Each modifier type, has_method guard, empty dict, concurrent, defaults |
| AEX-7 | test_aex07_attack_started, test_aex07_attack_hit_per_enemy, test_aex07_projectile_fired, test_aex07_melee_vfx_on_miss, test_aex07_no_signals_on_unknown | 5 | Signal emission timing and counts for all 4 signals |
| AEX-8 | test_aex08_unknown_no_crash, test_aex08_empty_effect_type, test_aex08_active_resets, test_aex08_no_damage_no_projectile | 4 | No crash, empty string as unknown, active resets, no side effects |

**Total:** 38 tests, 38 expected RED failures

## Test Design Decisions

1. **Mock inner classes:** `MockEnemy` (Node3D with recording methods), `BareEnemy` (Node3D with no extra methods for guard tests), `MockParent` (Node3D with `get_facing_sign()`).
2. **Scene tree setup:** `_build_scene()` helper creates a Node3D hierarchy attached to the active SceneTree for tests requiring groups and tree traversal (melee hit detection, projectile scene addition).
3. **startup_frames = 0 throughout:** All tests use synchronous handler execution. Async timer behavior deferred to adversarial test suite.
4. **Knockback tested directly:** `_calculate_knockback()` called on executor instances for pure-math validation (AEX-5 tests don't require scene tree).
5. **Modifier tested directly:** `_apply_modifiers()` called on executor instances with mock enemies (AEX-6 tests don't require scene tree).

## Would Have Asked

- None. Spec (AEX-1..AEX-8, 6 DRs, 20 edge cases) resolved all ambiguities.

## Assumptions

- `startup_frames = 0` tests are sufficient for the primary suite; timer-based delay tests belong in adversarial deepening.

## Confidence

High — spec is frozen with complete edge case table; test mock contracts match spec Section 7 mock enemy contract exactly.

## Next

Test Breaker Agent writes adversarial tests at `tests/scripts/attacks/test_attack_executor_adversarial.gd`.
