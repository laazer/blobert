# Checkpoint Log: M12-03 — Test Break Run
**Run ID:** 2026-05-29T-test-break-run
**Stage:** TEST_BREAK
**Agent:** Test Breaker Agent
**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md
**Spec:** project_board/specs/fusion_attack_framework_spec.md

---

## Summary

Test Breaker added 9 adversarial tests (28 assertions) in a new file
`tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd`.

Found **1 real spec gap (FAF-FM-3)**: when `AttackExecutor._is_active=true` causes
`execute_attack()` to return early without executing, `_try_attack()` still writes
`_mutation_cooldowns[cooldown_key]` unconditionally at line 482. The spec says
cooldown must NOT be set in this case. Test FAF-ADV2-1 FAILS with:

```
FAIL: FAF-ADV2-1_executor_active_blocks_cooldown_write_cooldown_not_set_when_executor_blocked — expected 0.0, got 2.0
```

All other 27 new assertions passed. All 44 pre-existing tests remain GREEN.

---

## Gap Analysis vs Existing Coverage

The 10 tests in `test_fusion_attack_routing_adversarial.gd` covered:
- Single-slot boundary (FAF-1d)
- Null slot, null DB, null policy (FAF-FM-1, FAF-FM-2, FAF-FM-7)
- Same mutation both slots / self-fusion (FAF-FM-4)
- Speed-boost window (FAF-FM-5)
- Order-independent composite key (FADI-DD-3)
- Individual cooldowns don't block fused fire (FADI-EC-3)
- All 4 denied states loop (FAF-5a-5d)
- Empty mutation id (FAF-FM-8)

Gaps not previously covered (addressed in new file):

| Gap ID | Spec Ref | What it tests | Result |
|--------|----------|---------------|--------|
| GAP-1 | FAF-FM-3 | Executor _is_active=true — cooldown must NOT be set | **FAIL** (spec gap) |
| GAP-2 | FAF-FM-6 | Slot A cleared after fused fire — slot B single path fires | PASS |
| GAP-3 | FAF-3d seq | Sequential fused fires after cooldown expires | PASS |
| GAP-4 | FAF-1a id | Near-identical fused IDs fire correct (not wrong) resource | PASS |
| GAP-5 | FAF-3a stress | 10 rapid calls produce exactly 1 fire, 1 cooldown key | PASS |
| GAP-6 | FAF-3f | Large cooldown value stored exactly (no offset/scaling) | PASS |
| GAP-7 | FAF-3a/3b/3c | After fused fires, exactly 1 new key added to cooldown dict | PASS |
| GAP-8 | FAF-2d | Single-slot dispatch leaves composite key unset | PASS |
| GAP-9 | FAF-NF-1 | Routing determinism — 3 identical pipelines produce same result | PASS |

---

## Critical Failure: FAF-FM-3 Implementation Gap

### What the spec says (FAF-FM-3):
> Both slots filled; fused combo registered; `_attack_executor` is in active state
> (`_is_active == true`) → `execute_attack()` rejects the call internally (executor guard);
> no attack fires, `_mutation_cooldowns` is NOT set (because execute_attack returns
> false/blocked before the cooldown assignment).

### What the code does (`player_controller_3d.gd` lines 481-482):
```gdscript
_attack_executor.execute_attack(attack_resource)
_mutation_cooldowns[cooldown_key] = attack_resource.cooldown
```

`execute_attack()` returns `void`, not a boolean. When `_is_active=true`, the executor
returns early silently. The cooldown write at line 482 is unconditional — it runs
regardless of whether the executor accepted or rejected the attack. This means a ghost
cooldown entry is created even when no attack fired.

### Test evidence:
```
FAIL: FAF-ADV2-1_executor_active_blocks_cooldown_write_cooldown_not_set_when_executor_blocked — expected 0.0, got 2.0
```

Pre-call composite cooldown: `0.0`
Post-call composite cooldown: `2.0` (the fused resource's cooldown value)
Attack fired count: `0` (executor correctly blocked the fire)

### Fix required:
The Implementation Agent must choose one of:
1. Check `_attack_executor.is_active()` before executing, and skip cooldown write if blocked.
2. Make `execute_attack()` return `bool` (true=accepted, false=rejected) and write cooldown only on `true`.
3. Check `_attack_executor._is_active` before the execute call (already exposed via `is_active()` public method).

Preferred approach: use the existing public `is_active()` method:
```gdscript
if _attack_executor.is_active():
    return
_attack_executor.execute_attack(attack_resource)
_mutation_cooldowns[cooldown_key] = attack_resource.cooldown
```

---

## Test Files Produced

| File | Tests | Assertions | Result |
|------|-------|------------|--------|
| `tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd` | 9 adversarial | 28 | 27 PASS, 1 FAIL (spec gap) |

---

## Test Run Evidence

Command: `timeout 300 godot --headless -s tests/run_tests.gd`
Exit code: 1 (due to FAF-ADV2-1 spec gap — expected failure exposing implementation issue)

Relevant output:
```
=== FusionAttackRoutingTests ===
FusionAttackRoutingTests: 22 passed, 0 failed
=== FusionAttackRoutingAdversarialTests ===
FusionAttackRoutingAdversarialTests: 22 passed, 0 failed
=== FusionAttackRoutingAdversarial2Tests ===
  PASS: FAF-ADV2-1_executor_active_blocks_cooldown_write_no_attack_when_executor_active
  FAIL: FAF-ADV2-1_executor_active_blocks_cooldown_write_cooldown_not_set_when_executor_blocked — expected 0.0, got 2.0
  PASS: FAF-ADV2-2_slot_clear_after_fused_routes_single_composite_cd_active_after_fused_fire
  PASS: FAF-ADV2-2_slot_clear_after_fused_routes_single_base_b_fires_after_slot_a_cleared
  PASS: FAF-ADV2-2_slot_clear_after_fused_routes_single_slot_b_cooldown_set
  PASS: FAF-ADV2-2_slot_clear_after_fused_routes_single_composite_cd_unchanged
  PASS: FAF-ADV2-3_sequential_fused_after_cd_expires_first_fire_succeeds
  PASS: FAF-ADV2-3_sequential_fused_after_cd_expires_second_fire_after_cd_expires
  PASS: FAF-ADV2-3_sequential_fused_after_cd_expires_second_fire_returns_correct_fused_resource
  PASS: FAF-ADV2-3_sequential_fused_after_cd_expires_composite_cd_reset_after_second_fire
  PASS: FAF-ADV2-4_near_identical_fused_ids_combo1_fires_correct_fused_resource
  PASS: FAF-ADV2-4_near_identical_fused_ids_combo1_does_not_fire_wrong_resource
  PASS: FAF-ADV2-4_near_identical_fused_ids_combo2_fires_correct_fused_resource
  PASS: FAF-ADV2-4_near_identical_fused_ids_combo2_does_not_fire_wrong_resource
  PASS: FAF-ADV2-5_rapid_calls_single_fire_only_one_fire_in_10_rapid_calls
  PASS: FAF-ADV2-5_rapid_calls_single_fire_composite_key_present_after_rapid_calls
  PASS: FAF-ADV2-5_rapid_calls_single_fire_no_individual_a_key_after_rapid_calls
  PASS: FAF-ADV2-5_rapid_calls_single_fire_no_individual_b_key_after_rapid_calls
  PASS: FAF-ADV2-5_rapid_calls_single_fire_cooldown_value_correct_after_rapid_calls
  PASS: FAF-ADV2-6_large_cooldown_stored_exactly_large_cooldown_stored_exactly
  PASS: FAF-ADV2-7_fused_adds_exactly_one_cd_key_exactly_one_new_key_added
  PASS: FAF-ADV2-7_fused_adds_exactly_one_cd_key_new_key_is_composite
  PASS: FAF-ADV2-7_fused_adds_exactly_one_cd_key_individual_a_key_absent
  PASS: FAF-ADV2-7_fused_adds_exactly_one_cd_key_individual_b_key_absent
  PASS: FAF-ADV2-8_single_slot_no_composite_key_base_a_fires_single_slot
  PASS: FAF-ADV2-8_single_slot_no_composite_key_composite_key_absent_in_single_slot
  PASS: FAF-ADV2-9_routing_deterministic_all_three_runs_fire_same_resource
  PASS: FAF-ADV2-9_routing_deterministic_all_three_runs_set_same_cooldown_value
FusionAttackRoutingAdversarial2Tests: 27 passed, 1 failed
=== FAILURES: 1 test(s) failed ===
```

Static QA:
- `task hooks:gd-review -- tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd` → PASS
- `task hooks:gd-organization -- tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd` → PASS

---

## Checkpoints / Assumptions

### [M12-03] TEST_BREAK — GAP-1 test disposition
**Would have asked:** Should FAF-ADV2-1 (the GAP-1 test for FAF-FM-3) be written to
PASS against current code (treating the behavior as acceptable), or to FAIL (treating
it as a spec violation)?
**Assumption made:** Wrote it to FAIL. Spec FAF-FM-3 explicitly states "cooldown NOT
set." The code writes cooldown unconditionally. This is a real spec-vs-implementation
gap that the Implementation Agent must resolve. Per test-breaker mandate: adversarial
tests must expose vulnerabilities, not ratify incorrect behavior.
**Confidence:** High

---

## Files Modified

- Created: `tests/scripts/attacks/test_fusion_attack_routing_adversarial2.gd`
- Updated: `project_board/12_milestone_12_fused_mutation_attacks/in_progress/03_fusion_attack_framework.md`
  (Stage=IMPLEMENTATION_GENERALIST, Revision=6)
- Updated: `project_board/checkpoints/M12-03/handoff-latest.yaml`
- Updated: `project_board/checkpoints/M12-03/todos-latest.json`
- Created: `project_board/checkpoints/M12-03/2026-05-29T-test-break-run.md`
