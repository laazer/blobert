# M11-08 Test Break Run — 2026-05-26

## Summary

Adversarial test suite created at `tests/scripts/attacks/test_claw_attack_adversarial.gd` (745 lines, 29 test functions). Covers 12 adversarial dimensions from the checklist matrix.

## Gaps Exposed

### [M11-08] TEST_BREAK — Dead enemy infection race
**Would have asked:** Should the infect_weakened modifier check is_dead() before transitioning? The spec handler (CPA-3, section 3) doesn't include an is_dead() guard, but CPA-3d says "Dead enemy → no transition."
**Assumption made:** A WEAKENED enemy killed by claw damage must NOT be infected post-mortem. The infect_weakened handler should check is_dead() or the implementation should guard set_base_state() against dead enemies. Test `test_adv_weakened_killed_by_damage_no_infect` asserts this.
**Confidence:** High

## Tests by Category

| Category | Count | Tests |
|----------|-------|-------|
| Boundary: Range | 4 | exact_boundary, just_outside, just_inside, zero_range |
| Boundary: Damage | 2 | zero_no_weaken, zero_damage_infects |
| Null & Empty | 3 | false_explicit, empty_id, null_resource |
| State Machine Edge | 4 | beyond_enum, killed_weakened, killed_normal, threshold_50pct |
| Knockback | 4 | facing_left, degenerate, none, zero_magnitude |
| Concurrency | 2 | active_blocks, rapid_three |
| Multi-enemy | 5 | five_weakened, mixed_range, behind_player, signal_count, vfx_once |
| Isolation | 3 | slow+infect, silent_parent, double_registration |
| Determinism | 1 | repeated_identical |
| Cooldown | 1 | value_matches_spec |

## Expected Failures (until implementation)

- `test_adv_zero_damage_weakened_still_infects` — needs infect_weakened modifier
- `test_adv_weakened_killed_by_damage_no_infect` — needs is_dead() guard in modifier
- `test_adv_five_weakened_all_infect` — needs infect_weakened modifier
- `test_adv_modifier_slow_and_infect_coexist` — needs infect_weakened modifier
- `test_adv_state_beyond_enum_no_crash` — partially passes (no crash), state assertion depends on modifier
