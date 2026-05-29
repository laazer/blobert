# M12-04 Test Break Run — 2026-05-29

**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
**Agent:** Test Breaker Agent
**Stage:** TEST_BREAK → IMPLEMENTATION_GENERALIST
**Run ID:** 2026-05-29T-test-break-run

---

## Outcome

21 adversarial tests added across 1 new file:

| File | Tests | Gaps Targeted |
|------|-------|---------------|
| `tests/scripts/attacks/test_acid_claw_combo_seams_adversarial.gd` | 21 | GAP-1 through GAP-10 + combinatorial + assumption check |

**All 21 tests are RED as expected — implementation not yet present.**

Pre-existing 73 tests (test_acid_claw_combo_attack.gd, test_acid_claw_combo_adversarial.gd, test_enemy_acid_stacking.gd) remain in their RED-before-implementation state; no pre-existing test was modified or removed.

---

## Gap Analysis: What the Designer Suite Left Uncovered

### GAP-1: combo_hits propagation — handler reads field, not hardcoded literal

**Seam:** A naive `_handle_melee_swipe_combo` could contain `for i in range(3)` instead of `for i in range(resource.combo_hits)`. The designer's test only tests combo_hits=3 (which would pass either implementation). Tests added: combo_hits=2 → exactly 2 hits; combo_hits=4 → exactly 4 hits; mutation matrix 1..5.

**Tests:** `test_gap1_combo_hits_2_produces_exactly_2_hits`, `test_gap1_combo_hits_4_produces_exactly_4_hits`, `test_gap9_combo_hits_1_through_5_each_produce_exact_count`

### GAP-2: stop_all_effects() called mid-combo — counter NOT reset

**Seam:** The designer covers counter monotonicity across stop_all_effects() (AC-3k: add 3, stop, add 1 → key "acid_stack_3"). The adversarial gap is: add 2 (simulating combo hits 1 and 2 landing), stop_all_effects(), add 1 more (simulating hit 3) — the next key must be "acid_stack_2", not "acid_stack_0". This interleaving is distinct from the designer's sequential test and better simulates the runtime mid-combo scenario where stop_all_effects() fires between hits. A second variant tests multiple stop/restart cycles to confirm the counter is strictly monotonic across all cycles.

**Tests:** `test_gap2_stop_mid_sequence_counter_not_reset`, `test_gap2_rapid_stop_restart_counter_always_advances`

### GAP-3: _is_active cleared after combo_hits=1 (synchronous completion)

**Seam:** The designer's `test_ac2l_is_active_false_after_combo_completes` only tests combo_hits=0 (the synchronous early-exit path). For combo_hits=1, the async wrapper `_run_melee_swipe_combo_async` fires — if the wrapper omits `_is_active = false` in a certain code path or places it before the await, the flag could remain true after the call returns in a headless synchronous context. Tests added: combo_hits=1 with enemy in range must leave is_active() == false; MELEE_SWIPE non-regression.

**Tests:** `test_gap3_is_active_false_after_combo_hits_1_sync`, `test_gap3_is_active_false_after_melee_swipe_not_regressed`

### GAP-4: Per-instance acid_stack_counter isolation via full EnemyBase delegation chain

**Seam:** `test_counters_are_per_instance_not_shared` in the designer suite tests EnemyEffectTracker directly. The gap is whether TWO separate EnemyBase instances maintain independent counters through the full `EnemyBase.apply_acid_stack() → _effect_tracker.add_acid_stack()` delegation chain. If `_acid_stack_counter` were accidentally declared as a class-level static variable instead of an instance variable, this test would catch it.

**Tests:** `test_gap4_two_enemy_bases_have_independent_counters`

### GAP-5: Large combo_hits WITH an enemy in range produces N stacks

**Seam:** The designer's `test_large_combo_hits_no_crash` runs combo_hits=10 as a whiff (no enemies). This only verifies no crash. It does NOT verify that 10 hits actually land and produce 10 stacks when an enemy is present. Added test places an enemy in range for combo_hits=10 and asserts exactly 10 stacks, 10 damage calls, 10 VFX, and total damage 18.0.

**Tests:** `test_gap5_combo_hits_10_with_enemy_produces_10_stacks`

### GAP-6: MELEE_SWIPE with combo_hits=3 explicitly set still fires exactly once

**Seam:** The designer tests that MELEE_SWIPE still fires a single hit after MELEE_SWIPE_COMBO is added. But none of the existing tests set combo_hits=3 on a MELEE_SWIPE resource. An implementation bug where execute_attack() routes MELEE_SWIPE resources through combo logic if combo_hits > 1 would not be caught by the existing suite. This test sets combo_hits=3 explicitly on a MELEE_SWIPE resource and asserts exactly 1 hit fires.

**Tests:** `test_gap6_melee_swipe_with_combo_hits_3_still_fires_once`

### GAP-7: _apply_combo_modifiers reads acid_dps and acid_duration from modifiers dict

**Seam:** If `_apply_combo_modifiers` hardcodes `DEFAULT_ACID_DPS` (0.2) instead of `modifiers.get("acid_dps")`, the normative spec value 0.4 would silently fail to reach the enemy. The designer's tests use acid_dps=0.4 throughout, which could pass even if 0.4 is hardcoded. Tests added with acid_dps=0.99 and acid_duration=7.77 to expose any constant substitution.

**Tests:** `test_gap7_combo_modifiers_reads_acid_dps_from_dict_not_constant`, `test_gap7_combo_modifiers_reads_acid_duration_from_dict_not_constant`

### GAP-8: startup_frames=0 on MELEE_SWIPE_COMBO — all 3 hits fire

**Seam:** AC-2m requires startup_frames to fire once before the first hit. The designer did not write an explicit test that startup_frames=0 produces all 3 hits (since this is the nominal path). Added as an explicit assertion to confirm the resource's startup_frames=0 attribute doesn't accidentally gate hit execution.

**Tests:** `test_gap8_startup_frames_0_all_3_hits_fire`

### GAP-9: Mutation matrix sweep combo_hits 1..5 (combines with GAP-1)

**Seam:** Extends GAP-1 into a combinatorial sweep: for combo_hits in {1,2,3,4,5}, verify attack_hit count and acid_stack_calls size match exactly. A loop-count bug of any kind (off-by-one, fence post, range start at 1 vs 0) is caught by this matrix.

**Tests:** `test_gap9_combo_hits_1_through_5_each_produce_exact_count`

### GAP-10: Dead-guard does not advance the acid_stack_counter

**Seam:** AC-EC-9 specifies that `add_acid_stack` with duration=0.0 must NOT increment the counter. Analogously, AC-3i specifies that `apply_acid_stack` on a dead enemy is a no-op. However: a bug where `_acid_stack_counter` is incremented BEFORE the duration guard check (or before the dead-guard delegation) would advance the counter for every no-op call, causing the next valid stack to use a key offset by the number of no-ops. The designer tests zero-duration behavior but only at the EnemyEffectTracker level. Added: (1) tracker-level zero-duration test verifying counter not advanced (confirming consistency with existing design), (2) full EnemyBase dead-guard path: 3 dead-guard no-ops on a base followed by marking alive, then applying one stack — must get key "acid_stack_0".

**Tests:** `test_gap10_dead_guard_does_not_advance_counter_in_tracker`, `test_gap10_dead_enemy_base_apply_does_not_affect_live_counter`

---

## Combinatorial and Assumption Tests

**Combinatorial — combo_hits=0 WITH enemy in range:** The designer's `test_ac2h` and `test_fail1_combo_hits_zero_no_attack_hit_no_crash` test with an enemy present but the newly added `test_combo_hits_zero_with_enemy_in_range_no_effects` explicitly asserts zero damage, zero stacks, zero attack_hit even though an enemy is in range.

**Assumption check — set("combo_hits", N) roundtrip:** Since `combo_hits` is not yet on AttackResource, `r.set("combo_hits", 3)` silently succeeds but `r.get("combo_hits")` returns null. This means ALL combo_hits tests in every file use null combo_hits. The assumption check test explicitly verifies the roundtrip succeeds when the field exists.

---

## Checkpoint Decisions

### [M12-04] TEST_BREAK — per-hit cooldown gap excluded

**Would have asked:** Should a test verify that the 2.0s cooldown is NOT written per-hit (only once after all hits complete)?
**Assumption made:** The cooldown is managed by the player controller (scripts/player/player_controller_3d.gd), not by AttackExecutor. AttackExecutor has no cooldown state. Testing cooldown timing requires the full player controller integration test, which is in scope for Integration/AC Gatekeeper. Excluded from this adversarial suite.
**Confidence:** High

### [M12-04] TEST_BREAK — AC-EC-1 (enemy out of range for hit 2) excluded

**Would have asked:** Should the per-hit fresh-query behavior (enemy moves out of range mid-combo) be adversarially tested?
**Assumption made:** This requires asynchronous timer advancement between hits, which is not possible in a synchronous headless test context without a live SceneTree process loop. The spec note in AC-6 risk analysis explicitly defers timer-dependent tests to Test Breaker with the caveat "use signal-await patterns or mock the tree timer." Since the inter-hit delay requires `await get_tree().create_timer()`, the in-range/out-of-range mid-combo case cannot be made deterministic without a timer mock infrastructure not present in the current harness. Excluded to keep tests deterministic.
**Confidence:** High

---

## Files Created

- `tests/scripts/attacks/test_acid_claw_combo_seams_adversarial.gd` (21 adversarial tests)

## Files Modified

- `project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md` (Stage IMPLEMENTATION_GENERALIST, Revision 6)
- `project_board/checkpoints/M12-04/handoff-latest.yaml`
- `project_board/checkpoints/M12-04/todos-latest.json`
- `project_board/CHECKPOINTS.md` (index entry added)
