# M11-14 Test Break Run — 2026-05-26

**Agent:** Test Breaker Agent
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/14_enemy_health_and_damage_reception.md`
**Spec:** `project_board/specs/enemy_health_damage_reception_spec.md`
**Stage:** TEST_BREAK → IMPLEMENTATION_GAMEPLAY (Revision 4 → 5)

## Gap Analysis

Analyzed 79 existing tests across 2 files. Identified 12 gap categories not covered by primary suite:

| # | Gap | Spec Seam | Why It Matters |
|---|-----|-----------|----------------|
| 1 | Killing-blow knockback gating | EHD-2 step 6 | Primary suite uses Vector3.ZERO on killing blow; never tests non-zero knockback on lethal hit |
| 2 | Signal ordering (damaged before died) | EHD-2 step 5/7 | Each signal tested independently; order never verified |
| 3 | Double-lethal idempotency | EHD-6 one-way latch | Two lethal blows tested for signal count but not knockback/HP invariants |
| 4 | Rapid burst through death boundary | EHD-2, EHD-6 | Only 3 hits tested (EC-17); death mid-burst not verified |
| 5 | Concurrent DoT + direct damage | EHD-4, EHD-2 | Never combined in same frame |
| 6 | Dual-DoT kill race | EHD-4, EHD-6 | Two DoTs ticking when only enough HP for one; second must noop |
| 7 | Floating-point HP accumulation | EHD-1e | No stress test with many small damages |
| 8 | Knockback convergence/NaN | EHD-3 | Only 1-frame decay tested; no extreme values |
| 9 | DoT lag-spike multi-tick | EHD-4 (spec risk note) | Large delta causing floor(delta/interval) ticks |
| 10 | Negative DoT params | EHD-4 | Negative duration/DPS not tested |
| 11 | Slowness boundary precision | EHD-7 | Exact expiry boundary, many small deltas |
| 12 | Zero-knockback residual preservation | EHD-3i | Zero knockback should not overwrite existing impulse |

## Tests Written

**File:** `tests/scripts/enemies/test_enemy_health_adversarial.gd` (838 lines, 42 test functions)

### Test Inventory

| Test Function | Gap # | Spec Ref | What It Catches |
|---|---|---|---|
| test_adv_killing_blow_does_not_apply_knockback | 1 | EHD-2 step 6 | Knockback on lethal hit must be skipped |
| test_adv_near_lethal_blow_does_apply_knockback | 1 | EHD-2 step 6 | Non-lethal hit applies knockback normally |
| test_adv_damaged_signal_fires_on_killing_blow | 2 | EHD-2 step 7 | damaged signal emits on killing blow (not just alive hits) |
| test_adv_signal_order_damaged_before_died | 2 | EHD-2 steps 5,7 | damaged fires before died |
| test_adv_double_lethal_blow | 3 | EHD-6 | Only first lethal triggers signals |
| test_adv_rapid_damage_burst_death_midsequence | 4 | EHD-2, EHD-6 | 5-hit burst, death at hit 4, hit 5 noop |
| test_adv_dot_tick_then_direct_damage_same_frame | 5 | EHD-4, EHD-2 | DoT tick + take_damage reduce HP independently |
| test_adv_direct_damage_then_dot_tick_kills | 5 | EHD-4, EHD-6 | DoT tick kills after direct damage weakened |
| test_adv_two_dots_race_on_killing_tick | 6 | EHD-4, EHD-6 | First DoT kills; second is noop; died emits once |
| test_adv_dot_reapply_after_dot_kills | 6 | EHD-4, EHD-6 | Reapply poison after death is noop |
| test_adv_all_effects_noop_after_death | 6 | EHD-6 | apply_poison/acid/slowness all noop after death |
| test_adv_weakened_threshold_custom_max_hp_20 | — | EHD-5a | 50% of 20 = 10 |
| test_adv_weakened_threshold_custom_max_hp_7 | — | EHD-5a | 50% of 7 = 3.5 (fractional) |
| test_adv_weakened_threshold_just_above | — | EHD-5c | 50.01% stays NORMAL |
| test_adv_weakened_threshold_just_below | — | EHD-5b | 49.99% triggers WEAKENED |
| test_adv_weakened_constant_value | — | EHD-5 | WEAKENED_HP_THRESHOLD == 0.5 |
| test_adv_zero_max_hp_weakened_never_triggers | — | EHD-1, EC-3 | max_hp=0 → dead or never-WEAKENED |
| test_adv_tiny_max_hp | — | EHD-1, EC-3 | max_hp=0.001 |
| test_adv_floating_point_many_small_damages | 7 | EHD-1e | 100 x 0.01 on 1.0 HP |
| test_adv_floating_point_dot_accumulation | 7 | EHD-4, EHD-1e | 20 DoT ticks of 0.05 |
| test_adv_knockback_decay_converges_to_zero | 8 | EHD-3d,3e | 200 frames, large impulse |
| test_adv_knockback_no_nan_after_extreme_values | 8 | EHD-3 | 500 frames, extreme (9999) impulse |
| test_adv_dot_lag_spike_multiple_ticks | 9 | EHD-4 risk | 1.5s delta → 3 ticks |
| test_adv_dot_lag_spike_kills_midway | 9 | EHD-4, EHD-6 | Lag spike kills during multi-tick |
| test_adv_dot_negative_duration | 10 | EHD-4 | Negative duration → no ticks |
| test_adv_dot_negative_dps | 10 | EHD-4 | Negative DPS → no healing |
| test_adv_slowness_expires_exactly_on_boundary | 11 | EHD-7d | Process 0.5+0.5 for 1.0s duration |
| test_adv_slowness_many_small_deltas | 11 | EHD-7d | 100 x 0.01s deltas |
| test_adv_slowness_greater_than_one_speed_boost | 11 | EHD-7 | Multiplier > 1.0 valid |
| test_adv_zero_knockback_preserves_residual | 12 | EHD-3i | Zero-vector does not clear existing |
| test_adv_tracker_add_many_dot_types | — | EHD-8 | 4 custom DoT types simultaneously |
| test_adv_tracker_stop_then_readd | — | EHD-8f | Stop all, then re-add |
| test_adv_tracker_two_instances_isolated | — | EHD-8 | Two trackers don't share state |
| test_adv_tracker_stop_all_is_idempotent | — | EHD-8f | Double stop is safe |
| test_adv_dot_tick_and_direct_damage_signal_isolation | — | EHD-4i | dot_tick vs damaged signal separation |
| test_adv_dot_tick_signal_stops_after_death | — | EHD-4m | No dot_tick after death |
| test_adv_exact_hp_damage_kills | — | EHD-2, EHD-6 | Precision kill with fractional max_hp |
| test_adv_physics_process_noop_after_death | — | EHD-3, EHD-6 | Dead enemy: no knockback mutation |
| test_adv_weakened_via_dot_custom_max_hp | — | EHD-4k, EHD-5 | DoT triggers WEAKENED at 50% of 20 |
| test_adv_infected_during_dot_no_weakened_trigger | — | EHD-5f | INFECTED unchanged despite HP < 50% |
| test_adv_negative_damage_with_knockback | — | EHD-2g | Negative damage=0, knockback still applies |
| test_adv_zero_damage_on_dead_enemy | — | EHD-6e | Zero damage on dead = noop |
| test_adv_knockback_3axis_decay_uniform | — | EHD-3d | All 3 axes decay at same rate |

## Implementation Notes for Gameplay Systems Agent

1. **Killing-blow knockback gating (critical):** `take_damage()` spec step 6 gates knockback on "not dead". After HP reduction + death check, only apply knockback if `current_hp > 0.0`. Test `test_adv_killing_blow_does_not_apply_knockback` will catch this.

2. **Signal ordering:** `damaged.emit()` must fire BEFORE `died.emit()` on the killing blow. Test `test_adv_signal_order_damaged_before_died` uses an ordered array to verify.

3. **Zero-knockback preservation (EHD-3i):** When `knockback == Vector3.ZERO`, do NOT overwrite `_knockback_velocity`. Only set `_knockback_velocity = knockback` when `knockback != Vector3.ZERO`.

4. **DoT death guard:** `_apply_dot_damage()` must check `_is_dead` at the top. In multi-tick bursts (lag spike), each tick must independently check the death latch.

5. **Negative parameter clamping:** `damage` → `max(0.0, damage)`. DoT `dps` → clamp negative to 0. DoT `duration` → clamp ≤ 0 to noop. Slowness `multiplier` → `max(0.0, multiplier)`.

6. **Effect application after death:** `apply_poison()`, `apply_acid()`, `apply_slowness()` must all check `_is_dead` and noop.

## Checkpoint Decisions

### [M11-14] TEST_BREAK — Zero-knockback overwrite ambiguity
**Would have asked:** EHD-3i says "zero knockback does not create impulse" but EHD-3j says "new knockback overwrites residual." Which wins when knockback is Vector3.ZERO?
**Assumption made:** Zero-vector is not a "new knockback" — it means "no impulse requested." Existing residual should be preserved. Test encodes this assumption.
**Confidence:** Medium

### [M11-14] TEST_BREAK — Negative DoT parameters
**Would have asked:** Spec does not explicitly define behavior for negative duration or negative DPS. Should they be clamped or treated as errors?
**Assumption made:** Conservative: negative duration = noop (no effect created), negative DPS = 0 (no healing). Tests encode these guards.
**Confidence:** High
