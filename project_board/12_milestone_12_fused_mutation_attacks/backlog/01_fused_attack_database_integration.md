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

