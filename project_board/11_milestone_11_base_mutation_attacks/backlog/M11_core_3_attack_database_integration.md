# TICKET: M11_core_3_attack_database_integration

**Milestone:** M11 Base Mutation Attacks (Core Foundation)  
**Status:** Ready  
**Type:** Implementation

## Title

Implement AttackDatabase and integrate with PlayerController3D

## Description

AttackDatabase loads all attack resources (base + fused) and provides lookups:
- `get_base_attack(mutation_id)` → AttackResource for that mutation
- `get_fused_attack(slot_a, slot_b)` → AttackResource for that combo

Integrate with PlayerController3D to:
1. Load attacks from AttackDatabase
2. Execute via AttackExecutor
3. Track per-mutation cooldowns
4. Gate input by state (use state machine from prereq 1)

## Acceptance Criteria

- [x] `AttackDatabase` autoload created (`scripts/attacks/attack_database.gd`)
- [x] Loads attack resources from `res://attacks/base/*.tres` and `res://attacks/fused/*.tres`
- [x] Methods:
  - `get_base_attack(mutation_id: int) → AttackResource`
  - `get_fused_attack(slot_a: int, slot_b: int) → AttackResource`
  - Graceful fallback if attack not found (warning, return null)
- [x] PlayerController3D wired:
  - `_try_attack()` method checks:
    1. State machine permits attack input
    2. Active mutation exists
    3. Cooldown not active
  - Calls `AttackDatabase.get_base_attack(mutation_id)`
  - Calls `AttackExecutor.execute_attack(attack_resource)`
  - Sets `_mutation_cooldowns[mutation_id] = attack_resource.cooldown`
- [x] Cooldown tracking in `_physics_process`:
  - Decrement all active cooldowns by delta
  - When cooldown reaches 0, attack available again
- [x] Input gating by state (from prereq 1):
  - Attack input only checked in states that permit it (IDLE, WALK, JUMP, FALL, WALL_CLING)
  - Attack input NOT checked in HURT, DEAD, ABSORB, MUTATE states
- [x] Tests:
  - Attack resource loads correctly
  - Fused attack lookup works (and handles missing combos)
  - Cooldown blocks attack, then allows after expiry
  - State machine blocks attack in correct states
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_prereq_1_player_state_machine (state gating)
- M11_prereq_3_input_action_mapping (input action semantics)
- M11_core_1_attack_resource (attack data model)
- M11_core_2_attack_executor_handlers (execution logic)

## Integration Pseudocode

**PlayerController3D:**
```gdscript
func _physics_process(delta: float) -> void:
  state_machine.update(delta)
  _update_timers(delta)
  _handle_state(delta)  # Includes input checks
  # ... rest of physics ...

func _handle_state(delta: float) -> void:
  match state_machine.current:
    # ... IDLE, WALK, JUMP, etc. ...
    # Input checks happen here, including attack
    if Input.is_action_just_pressed("attack"):
      if state_machine.can_transition_to(ATTACK_USE):  # NEW: state gating
        _try_attack()

func _try_attack() -> void:
  var active_mutation = GameState.get_active_mutation()
  if active_mutation == NONE:
    return
  
  var cooldown_remaining = _mutation_cooldowns.get(active_mutation, 0.0)
  if cooldown_remaining > 0.0:
    return  # On cooldown
  
  var attack = AttackDatabase.get_base_attack(active_mutation)
  if not attack:
    push_error("No attack resource for mutation %d" % active_mutation)
    return
  
  AttackExecutor.execute_attack(attack)
  _mutation_cooldowns[active_mutation] = attack.cooldown

func _update_timers(delta: float) -> void:
  for mutation_id in _mutation_cooldowns:
    _mutation_cooldowns[mutation_id] = max(0.0, _mutation_cooldowns[mutation_id] - delta)
```

## Notes

- M11 core tickets don't add new states (ATTACK_USE, CHARGE_UP) yet — M11 attack tickets will do that
- AttackDatabase can load from code (in _register_base_attacks) or .tres files (decide in implementation)
- Fused attacks stored with key like "slot_a_slot_b" (e.g., "1_2" for Claw+Acid)
- If M1 already has implicit cooldown tracking, replace it with explicit per-mutation tracking
