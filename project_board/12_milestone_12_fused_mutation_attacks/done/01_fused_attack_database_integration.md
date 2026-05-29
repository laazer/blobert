# TICKET: 01_fused_attack_database_integration

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Integrate fused attacks with AttackDatabase and PlayerController3D

## Description

Extend the M11 attack system to support fused attack combos. When player has 2 mutations:
1. Check if a fused combo exists for (slot_a, slot_b)
2. If fused exists and input pressed, execute fused attack instead of base attack
3. Apply fused attack cooldown to both mutations separately (or shared, design choice)
4. Return to base attacks when player has only 1 active mutation

Reuse AttackDatabase (extend `get_fused_attack()` method) and AttackExecutor dispatch logic.

## Acceptance Criteria

- [x] PlayerController3D detects 2 active mutations via GameState
- [x] Before executing base attack, check `AttackDatabase.get_fused_attack(mutation_a, mutation_b)`
- [x] If fused exists, execute fused attack instead of base
- [x] Fused attack applies correct cooldown(s) to participating mutations
- [x] Fallback to base attack if fused not found (graceful degradation)
- [x] Input gating still applies (state machine checks, per-slot cooldowns)
- [x] Tests validate fused attack lookup and fallback behavior
- [x] Tests validate combo matrix coverage (6 unordered combos)
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_core_1_attack_resource (attack data model)
- M11_core_3_attack_database_integration (database API + player integration)
- M12_core_2_fused_attack_resources (fused attack .tres files + resource registry)

## Integration Pseudocode

**PlayerController3D._try_attack():**
```gdscript
func _try_attack() -> void:
  var active_mutations = GameState.get_active_mutations()
  
  # Try fused attack if 2 mutations active
  if active_mutations.size() == 2:
    var fused = AttackDatabase.get_fused_attack(active_mutations[0], active_mutations[1])
    if fused:
      # Check cooldowns for both mutations
      if _mutation_cooldowns.get(active_mutations[0], 0.0) > 0.0 or \
         _mutation_cooldowns.get(active_mutations[1], 0.0) > 0.0:
        return
      
      AttackExecutor.execute_attack(fused)
      _mutation_cooldowns[active_mutations[0]] = fused.cooldown
      _mutation_cooldowns[active_mutations[1]] = fused.cooldown
      return
  
  # Fall back to base attack (from M11)
  # ...
```

## Notes

- Unordered combo matrix: `get_fused_attack(a, b)` should match `get_fused_attack(b, a)`
- Fused cooldown may be different from base attack cooldowns
- Decide: shared cooldown (both mutations on same timer) or independent (each slot independent)

---

## Execution Plan

### Planning findings (2026-05-28)

**What already exists — no implementation needed:**
- `scripts/attacks/attack_database.gd`: `register_fused_attack()` and `get_fused_attack()` fully implemented with alphabetical sort key for order-independence.
- `scripts/player/player_controller_3d.gd` lines 445–482: `_try_attack()` has complete fused path (both-slot check → fused lookup → sorted composite cooldown key → fallback to slot_a base attack).
- `tests/scripts/attacks/test_attack_database_controller_integration.gd`: `test_adb07_fused_when_both_slots` and `test_adb07_fused_fallback_to_base` exist and pass.
- `tests/scripts/attacks/test_attack_database.gd`: ADB-5 and ADB-6 cover `register_fused_attack` / `get_fused_attack` including order-independence.

**Gaps requiring work (Spec Agent must address):**
1. **No spec document for M12-01.** The Spec Agent must produce `project_board/specs/fused_attack_database_integration_spec.md`.
2. **No combo matrix test.** No test exercises all 6 unordered real-mutation combos (claw+acid, claw+carapace, claw+adhesion, acid+carapace, acid+adhesion, carapace+adhesion). The AC checkbox for this is unchecked.
3. **Cooldown model undocumented.** The current implementation uses a single composite key (e.g., `"acid_claw"`) for fused cooldown — a single shared timer — not two independent per-slot timers. The Spec Agent must freeze this as the normative design and document the behavior precisely.
4. **Fallback cooldown key asymmetry.** When both slots are filled but no fused combo exists, `_try_attack()` falls back to slot_a's cooldown key (`cooldown_key = a_id`) only. This means slot_b's cooldown is not checked or set on a fallback. The Spec Agent must determine and document whether this is intentional or a gap.

**Work plan:**
- Task 1 (Spec Agent): Write `project_board/specs/fused_attack_database_integration_spec.md`. Freeze: composite key cooldown model, fallback key asymmetry, combo matrix definition, order-independence contract. Spec type: `generic`. **COMPLETE.**
- Task 2 (Test Designer): Write combo matrix behavioral tests in `tests/scripts/attacks/test_fused_combo_matrix.gd` — 6 forward lookups + 6 reverse lookups + 6 player-dispatch paths. Use synthetic AttackResources (not real `.tres` files).
- Task 3 (Test Breaker): Adversarial tests — null fused when only 1 slot filled, composite key collision, both-slot gating under active fused cooldown, fallback key behavior, order determinism stress.
- Task 4 (Gameplay Systems Agent): Any implementation changes required by the spec (likely none, but fallback key asymmetry may require a one-line fix).
- Task 5 (AC Gatekeeper): Verify all 9 ACs (including the previously unchecked combo matrix AC).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
6

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Pass — FusedComboMatrixTests: 36 passed, 0 failed; FusedComboMatrixAdversarialTests: 59 passed, 0 failed; full suite === ALL TESTS PASSED ===. Confirmed by Test Breaker checkpoint 2026-05-29T-test-break-run.md.
- Static QA: Pass — scripts/attacks/attack_database.gd (ACID_PROJECTILE_LIFETIME constant extracted, no other findings); scripts/player/player_controller_3d.gd (no findings). Confirmed by Gameplay Systems Agent checkpoint 2026-05-29T-gameplay-systems-run.md.
- Integration: All 9 ACs verified by AC Gatekeeper against code (player_controller_3d.gd lines 445–482, attack_database.gd), primary tests (test_adb07_fused_when_both_slots, test_adb07_fused_fallback_to_base), combo matrix tests (test_fused_combo_matrix.gd — 18 tests, 6 pairs, 3 categories), and adversarial tests (test_fused_combo_matrix_adversarial.gd — 26 functions, 59 assertions).
- Git state: All M12-01 implementation files clean and committed. (Unrelated dirty files from other work streams present in working tree — advisory to Human only.)

## Blocking Issues
- None

## Escalation Notes
- Advisory to Human: Working tree has uncommitted changes in files unrelated to M12-01 (asset_generation/ Python files, web frontend, test_player_mutation_slot_late_bind.gd). These should be committed before next agent pipeline runs to prevent false positives.
- Action required: Run `git rm project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md` and commit, since the AC Gatekeeper lacked shell access to execute `git mv`. The authoritative copy is now at `done/01_fused_attack_database_integration.md`.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/12_milestone_12_fused_mutation_attacks/done/01_fused_attack_database_integration.md"
}
```

## Status
Proceed

## Reason
All 9 acceptance criteria verified with explicit test and code evidence. AC1 (two-mutation detection): _try_attack() lines 453-456, 464; AC2 (fused lookup before base): line 467; AC3 (execute fused if found): lines 467-482, all 6 FADI-6-Nc dispatch tests; AC4 (correct cooldown): composite key lines 469-471/482, slot keys unset confirmed by EC-3/EC-6 adversarial tests; AC5 (fallback): lines 472-474, test_adb07_fused_fallback_to_base; AC6 (input gating): lines 447-452/479, FADI-7a tests; AC7 (lookup+fallback tests): test_adb07_fused_when_both_slots + fallback; AC8 (combo matrix): test_fused_combo_matrix.gd 18 tests / 36 assertions covering all 6 unordered pairs; AC9 (run_tests exits 0): === ALL TESTS PASSED === confirmed. Ticket written to done/. Human must remove backlog copy (git rm) since AC Gatekeeper lacked shell access for git mv.
