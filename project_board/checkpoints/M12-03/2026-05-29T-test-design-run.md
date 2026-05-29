# Checkpoint Log: M12-03 — Test Design Run
**Run ID:** 2026-05-29T-test-design-run
**Stage:** TEST_DESIGN
**Agent:** Test Designer Agent
**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md
**Spec:** project_board/specs/fusion_attack_framework_spec.md

---

## Summary

Test suite for M12-03 fusion attack dispatch routing written and verified. All 44 assertions GREEN against existing codebase. No spec gaps identified. No implementation changes required.

---

## Test Files Produced

| File | Tests | Assertions | Result |
|------|-------|------------|--------|
| `tests/scripts/attacks/test_fusion_attack_routing.gd` | 14 behavioral | 22 | 22/22 PASS |
| `tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd` | 10 adversarial | 22 | 22/22 PASS |

---

## Test Run Evidence

Command: `timeout 300 godot --headless -s tests/run_tests.gd`
Exit code: 0 (ALL TESTS PASSED)

Relevant output:
```
=== FusionAttackRoutingTests ===
  PASS: FAF-1_fused_route_fires_both_slots_fused_resource_fired
  PASS: FAF-2_base_route_only_slot_a_base_a_fires
  PASS: FAF-2_base_route_only_slot_a_slot_a_cooldown_set
  PASS: FAF-3_base_route_only_slot_b_base_b_fires
  PASS: FAF-3_base_route_only_slot_b_slot_b_cooldown_set
  PASS: FAF-4_no_attack_no_slots_no_attack_fired
  PASS: FAF-5_fused_cd_composite_only_composite_key_set_to_resource_cooldown
  PASS: FAF-5_fused_cd_composite_only_slot_a_individual_key_unset
  PASS: FAF-5_fused_cd_composite_only_slot_b_individual_key_unset
  PASS: FAF-6_fused_cd_blocks_repeat_first_call_fires
  PASS: FAF-6_fused_cd_blocks_repeat_composite_cd_set_after_first_fire
  PASS: FAF-6_fused_cd_blocks_repeat_second_call_blocked_by_cd
  PASS: FAF-7_no_attack_speed_boost_window_is_fusion_active_returns_true
  PASS: FAF-7_no_attack_speed_boost_window_no_attack_fires_in_speed_boost_window
  PASS: FAF-8_blocked_absorb_attack_blocked_in_absorb
  PASS: FAF-9_blocked_mutate_attack_blocked_in_mutate
  PASS: FAF-10_blocked_hurt_attack_blocked_in_hurt
  PASS: FAF-11_blocked_dead_attack_blocked_in_dead
  PASS: FAF-12_permitted_idle_fused_fires_in_idle
  PASS: FAF-13_base_independent_of_fused_cd_base_a_fires_despite_composite_cd
  PASS: FAF-14_fallback_slot_a_no_fused_slot_a_base_fires_on_fallback
  PASS: FAF-14_fallback_slot_a_no_fused_slot_b_cooldown_unset_on_fallback
FusionAttackRoutingTests: 22 passed, 0 failed
=== FusionAttackRoutingAdversarialTests ===
  PASS: FAF-ADV-1_single_slot_no_fused_path_fused_not_fired_with_single_slot
  PASS: FAF-ADV-1_single_slot_no_fused_path_base_a_fires_not_fused
  PASS: FAF-ADV-2_null_mutation_slot_no_attack_when_slot_null
  PASS: FAF-ADV-2_null_mutation_slot_no_crash
  PASS: FAF-ADV-3_null_attack_database_no_crash_without_db
  PASS: FAF-ADV-4_same_mutation_both_slots_base_fires_when_self_fusion
  PASS: FAF-ADV-5_speed_boost_active_no_slots_no_attack_in_speed_boost_window
  PASS: FAF-ADV-6_composite_key_order_independent_forward_composite_key_present
  PASS: FAF-ADV-6_composite_key_order_independent_forward_slot_a_key_absent
  PASS: FAF-ADV-6_composite_key_order_independent_forward_slot_b_key_absent
  PASS: FAF-ADV-6_composite_key_order_independent_reverse_composite_key_present
  PASS: FAF-ADV-6_composite_key_order_independent_reverse_slot_claw_key_absent
  PASS: FAF-ADV-6_composite_key_order_independent_reverse_slot_acid_key_absent
  PASS: FAF-ADV-7_individual_cd_nonzero_fused_still_fires_fused_fires_despite_individual_cds
  PASS: FAF-ADV-8_null_input_policy_no_attack_when_policy_null
  PASS: FAF-ADV-8_null_input_policy_no_crash
  PASS: FAF-ADV-9_all_denied_states_independent_state_6_blocked
  PASS: FAF-ADV-9_all_denied_states_independent_state_7_blocked
  PASS: FAF-ADV-9_all_denied_states_independent_state_8_blocked
  PASS: FAF-ADV-9_all_denied_states_independent_state_9_blocked
  PASS: FAF-ADV-10_empty_mutation_id_no_crash_no_attack_for_unregistered_ids
  PASS: FAF-ADV-10_empty_mutation_id_no_crash_no_crash
FusionAttackRoutingAdversarialTests: 22 passed, 0 failed
```

Pre-commit hooks: gd-review PASS, gd-organization PASS.
Commit: 85b0135 `test(attacks): add M12-03 fusion attack routing regression suite`

---

## Spec↔Test Traceability

| Test | Spec Reference | Behavior Verified |
|------|----------------|-------------------|
| test_fused_route_fires_when_both_slots_filled | FAF-1a, FAF-1b | Fused resource fires when both slots filled + combo registered |
| test_base_route_fires_when_only_slot_a_filled | FAF-1d, FAF-2a | Slot A only → base A fires; cooldown key is slot A id |
| test_base_route_fires_when_only_slot_b_filled | FAF-1e, FAF-2b | Slot B only (via direct set_active_mutation_id) → base B fires |
| test_no_attack_when_no_slots_filled | FAF-1f | Neither slot filled → no attack |
| test_fused_cooldown_key_is_composite_not_individual | FAF-3a, FAF-3b, FAF-3c | Composite key set; individual keys absent after fused fire |
| test_fused_cooldown_blocks_repeat_fire | FAF-3d | Composite cooldown > 0 blocks second fire |
| test_no_attack_during_speed_boost_window | FAF-4c, FAF-4d | is_fusion_active()=true + slots empty → no attack |
| test_attack_blocked_in_absorb_state | FAF-5a | ABSORB blocks fused dispatch |
| test_attack_blocked_in_mutate_state | FAF-5b | MUTATE blocks fused dispatch |
| test_attack_blocked_in_hurt_state | FAF-5c | HURT blocks fused dispatch |
| test_attack_blocked_in_dead_state | FAF-5d | DEAD blocks fused dispatch |
| test_attack_permitted_in_idle_state | FAF-5e | IDLE permits fused dispatch |
| test_base_route_not_disrupted_by_fused_cooldown_on_different_key | FAF-2c, FADI-EC-3 | Composite cd on different key; single-slot base fires freely |
| test_fallback_to_slot_a_when_no_fused_registered | FAF-1g, FADI-5a/5c | No fused registered → slot A base fires; slot B cd unset |
| test_routing_boundary_one_slot_filled_does_not_enter_fused_path | FAF-1d | Single slot: fused NOT entered even when combo registered |
| test_null_mutation_slot_does_not_crash | FAF-FM-1 | Null slot → no crash, no attack |
| test_null_attack_database_does_not_crash | FAF-FM-2 | No db autoload → no crash |
| test_same_mutation_in_both_slots_falls_back_to_base | FAF-FM-4, FADI-NF-4 | Same id both slots → self-fusion rejected → base A fires |
| test_speed_boost_active_both_slots_empty_no_attack | FAF-FM-5 | _fusion_active=true, slots empty → no attack |
| test_composite_key_is_order_independent | FADI-DD-3 | A/B swap → same composite key in cooldowns |
| test_fused_cooldown_set_independently_of_individual_slot_cooldowns | FADI-EC-3 adv | Individual cds non-zero; fused still fires (checks composite only) |
| test_policy_null_returns_early | FAF-FM-7 | _input_policy null → no crash |
| test_all_four_denied_states_block_independently | FAF-5a–5d | Each denied state independently blocks (loop 4x isolated) |
| test_empty_mutation_id_does_not_crash | FAF-FM-8 | Unregistered ids → null resource → final guard → no crash |

---

## Checkpoints / Assumptions

### [M12-03] TEST_DESIGN — Slot B isolation setup
**Would have asked:** MutationSlotManager.fill_next_available always fills slot 0 first. How to fill only slot 1 for the FAF-1e/FAF-2b "only slot B filled" test?
**Assumption made:** Used `msm.get_slot(1).set_active_mutation_id(ns_b)` directly (MutationSlot.set_active_mutation_id is public API per mutation_slot.gd). This correctly places a mutation in slot 1 with slot 0 remaining empty.
**Confidence:** High

### [M12-03] TEST_DESIGN — FAF-FM-8 implementation
**Would have asked:** FAF-FM-8 requires slot returning "" from get_active_mutation_id(). But MutationSlot.is_filled() returns false for empty string, which means the slot would not be "filled" and _try_attack returns at the slot guard — not reaching the empty-id path at all. How to exercise the actual FAF-FM-8 path?
**Assumption made:** The truly unreachable scenario (is_filled()=true AND get_active_mutation_id()="") cannot be exercised without violating MutationSlot invariants. The equivalent defensive path — both slots filled with unregistered mutation IDs — exercises the same null-resource final-guard in _try_attack without violating invariants. Test uses unregistered ids (no crash on null resource).
**Confidence:** High

---

## Spec Gaps

None. All 14 behavioral and 10 adversarial tests from spec Section 7 are implemented. FAF-FM-8 has an implementation note above (guard path exercised via unregistered ids, which is the observable equivalent of the described failure mode).

---

## Files Modified

- Created: `tests/scripts/attacks/test_fusion_attack_routing.gd`
- Created: `tests/scripts/attacks/test_fusion_attack_routing_adversarial.gd`
- Updated: `project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md` (Stage=TEST_BREAK, Revision=5)
- Updated: `project_board/checkpoints/M12-03/handoff-latest.yaml`
- Updated: `project_board/checkpoints/M12-03/todos-latest.json`
- Created: `project_board/checkpoints/M12-03/2026-05-29T-test-design-run.md`
