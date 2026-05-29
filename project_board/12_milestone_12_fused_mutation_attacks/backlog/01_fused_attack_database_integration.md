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
- [ ] Tests validate combo matrix coverage (6 unordered combos)
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
IMPLEMENTATION_GAMEPLAY

## Revision
4

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Pass (FusedComboMatrixAdversarialTests: 59 passed, 0 failed; FusedComboMatrixTests: 36 passed, 0 failed; full suite === ALL TESTS PASSED ===)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Gameplay Systems Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md",
  "spec_path": "project_board/specs/fused_attack_database_integration_spec.md",
  "primary_test_files": [
    "tests/scripts/attacks/test_fused_combo_matrix.gd",
    "tests/scripts/attacks/test_fused_combo_matrix_adversarial.gd"
  ],
  "impl_domain": "GDScript",
  "impl_files": [
    "scripts/player/player_controller_3d.gd",
    "scripts/attacks/attack_database.gd"
  ],
  "breaker_finding": "No implementation changes required. All acceptance criteria already satisfied by existing code. The unchecked AC (combo matrix coverage) is now covered by test_fused_combo_matrix.gd (18 tests). Fallback key asymmetry (FADI-DD-2) is intentional per spec."
}
```

## Status
Proceed

## Reason
Test Breaker completed 26 adversarial test functions (59 assertions) in tests/scripts/attacks/test_fused_combo_matrix_adversarial.gd covering all 7 FADI-EC edge cases, FADI-3b/3c/3d, FADI-5b/5c, FADI-7a, FADI-NF-1/NF-4/NF-5, last-write-wins overwrite, order stress, cooldown decay via tick, and combinatorial invalid sequences. Full suite exits 0. Key finding: no implementation gaps — existing code is correct per spec. Gameplay Systems Agent must verify remaining acceptance criteria and advance to COMPLETE.
