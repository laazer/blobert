# Cooldown Cross-State Behavior Specification

**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/12_verify_cooldown_behavior.md`  
**Type:** Verification (with one small implementation fix)  
**Spec ID:** CDB (Cooldown-Decrement-Behavior)

---

## Requirement CDB-1: State-Independent Cooldown Decrement

### 1. Spec Summary

- **Description:** All entries in `_mutation_cooldowns` decrement by `delta` on every `_physics_process` frame, regardless of the current `PlayerStateMachine.PlayerState`. Cooldown tick is unconditional.
- **Constraints:** Decrement occurs in `_tick_controller_timers(delta, ...)` which is Step 2 of the physics pipeline. No state check gates this path.
- **Assumptions:** No assumptions — this is existing implemented behavior verified by code inspection (`player_controller_3d.gd:229-235`).
- **Scope:** `PlayerController3D._tick_controller_timers()`.

### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CDB-1a | Cooldown decrements in state IDLE | Set cooldown=1.0, call `_tick_controller_timers(0.25, false)` with PSM in IDLE, assert 0.75 |
| CDB-1b | Cooldown decrements in state WALK | Same as above with PSM in WALK |
| CDB-1c | Cooldown decrements in state JUMP | Same as above with PSM in JUMP |
| CDB-1d | Cooldown decrements in state FALL | Same as above with PSM in FALL |
| CDB-1e | Cooldown decrements in state WALL_CLING | Same as above with PSM in WALL_CLING |
| CDB-1f | Cooldown decrements in state HURT | Same as above with PSM in HURT |
| CDB-1g | Cooldown decrements in state ABSORB | Same as above with PSM in ABSORB |
| CDB-1h | Cooldown decrements in state MUTATE | Same as above with PSM in MUTATE |
| CDB-1i | Cooldown does NOT decrement in state DEAD | NOT APPLICABLE — cooldown still decrements in DEAD because the code is unconditional. This is acceptable since dead state leads to reset_hp() which clears cooldowns (CDB-3). |

**Design decision (CDB-1f):** Cooldown CONTINUES during HURT. Rationale: the player should not be penalized for taking damage. When HURT ends, the cooldown has already ticked during that time, so the attack becomes available sooner.

### 3. Risk & Ambiguity Analysis

- **Risk:** None for decrement behavior. The existing code is unconditional and correct.
- **Edge case:** If `delta` is 0.0 (e.g. paused physics), cooldown does not change — this is correct behavior via `maxf(0.0, val - 0.0)`.

### 4. Clarifying Questions

None — resolved by code inspection.

---

## Requirement CDB-2: Cross-State Transition Cooldown Continuity

### 1. Spec Summary

- **Description:** When the player transitions between any two states (A → B), an active cooldown that was ticking in state A continues ticking in state B without interruption, reset, or loss of progress.
- **Constraints:** The `_mutation_cooldowns` dictionary is never conditionally cleared or frozen based on state transitions. The only mutation of cooldown values occurs in `_tick_controller_timers` (decrement) and `_try_attack` (set on execution).
- **Assumptions:** No assumptions — verified by code path analysis.
- **Scope:** `PlayerController3D._tick_controller_timers()`, `PlayerStateMachine.transition()`.

### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CDB-2a | IDLE→WALK continuity | Set cd=1.0 in IDLE, tick 0.1 (→0.9), change state to WALK, tick 0.1, assert cd==0.8 |
| CDB-2b | WALK→JUMP continuity | Set cd=0.8, tick in WALK (→0.7), transition to JUMP, tick (→0.6) |
| CDB-2c | JUMP→FALL continuity | Set cd=0.5 in JUMP, tick 0.1 (→0.4), transition to FALL, tick 0.1, assert 0.3 |
| CDB-2d | FALL→IDLE (landing) continuity | Set cd=0.6 in FALL, tick 0.2 (→0.4), transition to IDLE, tick 0.2, assert 0.2 |
| CDB-2e | Any→HURT continuity | Set cd=0.5 in IDLE, transition to HURT, tick 0.3, assert 0.2 |
| CDB-2f | HURT→IDLE recovery continuity | Set cd=0.4 in HURT, transition back to IDLE, tick 0.2, assert 0.2 |
| CDB-2g | IDLE→WALL_CLING continuity | Set cd=0.7, transition to WALL_CLING, tick 0.3, assert 0.4 |

### 3. Risk & Ambiguity Analysis

- **Risk:** Very low. The code has no state-aware branching in the cooldown path.
- **Edge case:** Rapid state oscillation (IDLE↔WALK within a single frame) — cooldown still only ticks once per `_tick_controller_timers` call.

### 4. Clarifying Questions

None.

---

## Requirement CDB-3: Death Resets All Cooldowns

### 1. Spec Summary

- **Description:** When `reset_hp()` is called (player death/respawn), ALL entries in `_mutation_cooldowns` MUST be cleared. After reset, every mutation's cooldown is 0.0, allowing immediate attack upon respawn.
- **Constraints:** `reset_hp()` currently does NOT clear `_mutation_cooldowns`. This requires a **one-line implementation change**: add `_mutation_cooldowns.clear()` to `reset_hp()`.
- **Assumptions:** `reset_hp()` is the canonical death/respawn entry point. The ticket AC explicitly states "Die and respawn, verify cooldown resets."
- **Scope:** `PlayerController3D.reset_hp()`.

### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CDB-3a | `reset_hp()` clears `_mutation_cooldowns` | Set cd["mut_a"]=0.5, cd["mut_b"]=1.0, call `reset_hp()`, assert `_mutation_cooldowns.size() == 0` |
| CDB-3b | Attack is available immediately after respawn | After `reset_hp()`, verify `_mutation_cooldowns.get("any_key", 0.0) == 0.0` for any key |
| CDB-3c | Cooldown reset applies to ALL mutations | Set 3+ cooldown keys with various values, call `reset_hp()`, verify all cleared |

### 3. Risk & Ambiguity Analysis

- **Risk:** None. `_mutation_cooldowns.clear()` is a safe dictionary operation with no side effects.
- **Implementation note:** This is the ONLY code change required by this ticket. All other behaviors already work correctly.

### 4. Clarifying Questions

None — resolved by ticket AC + planner checkpoint (confidence: High).

---

## Requirement CDB-4: Per-Mutation Independence Across State Changes

### 1. Spec Summary

- **Description:** Each mutation's cooldown tracks independently in `_mutation_cooldowns` via its mutation ID as the dictionary key. State transitions affect all cooldowns identically (all continue ticking); no mutation is treated differently from another during state changes.
- **Constraints:** Dictionary keying uses mutation ID for base attacks, and sorted pair `"id_a_id_b"` for fused attacks. Independence is inherent to the data structure.
- **Assumptions:** No assumptions.
- **Scope:** `PlayerController3D._mutation_cooldowns`, `_tick_controller_timers()`, `_try_attack()`.

### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CDB-4a | Two mutations tick independently across transitions | Set cd["claw"]=1.0, cd["acid"]=0.5; transition IDLE→JUMP; tick 0.3; assert cd["claw"]==0.7, cd["acid"]==0.2 |
| CDB-4b | Executing one attack does not affect another's cooldown | Set cd["claw"]=0.0, cd["acid"]=0.5; execute claw attack; assert cd["claw"]==resource.cooldown, cd["acid"]==0.5 |
| CDB-4c | Three mutations remain independent through multi-state path | Set cd["a"]=1.0, cd["b"]=0.6, cd["c"]=0.2; tick through IDLE→WALK→JUMP; verify each decremented by total delta |

### 3. Risk & Ambiguity Analysis

- **Risk:** None. Per-mutation independence is inherent to dictionary iteration in `_tick_controller_timers`.
- **Edge case:** Fused cooldown key (`"id_a_id_b"`) vs individual keys — these are separate dictionary entries and naturally independent.

### 4. Clarifying Questions

None.

---

## Requirement CDB-5: Rapid Input Rejection During Cooldown Across State Boundaries

### 1. Spec Summary

- **Description:** While a mutation's cooldown is active (value > 0.0), pressing the attack button does NOT trigger an attack, regardless of how many state transitions have occurred since the cooldown was set. The rejection is enforced by the `_mutation_cooldowns.get(cooldown_key, 0.0) > 0.0` check in `_try_attack()`.
- **Constraints:** Attack input rejection during cooldown operates independently of the state-based `is_action_permitted()` check. Both guards must pass for an attack to execute.
- **Assumptions:** No assumptions.
- **Scope:** `PlayerController3D._try_attack()`.

### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CDB-5a | Attack rejected in IDLE during cooldown | Set cd["mut"]=0.5, PSM=IDLE, call `_try_attack()`, verify executor NOT called |
| CDB-5b | Attack rejected in WALK during cooldown | Same with PSM=WALK |
| CDB-5c | Attack rejected after IDLE→JUMP→FALL transition | Set cd in IDLE, transition to JUMP then FALL, call `_try_attack()`, verify rejected |
| CDB-5d | Attack succeeds after cooldown expires post-transition | Set cd=0.1, tick 0.2, transition to WALK, call `_try_attack()`, verify executor IS called |
| CDB-5e | Rapid repeated calls to `_try_attack()` do not bypass | Call `_try_attack()` 5 times in sequence while cd > 0; verify executor called 0 times |
| CDB-5f | Attack rejected in state where ACTION_ATTACK is denied even at cd=0 | Set cd=0.0, PSM=HURT, call `_try_attack()`, verify rejected (state gate) |

### 3. Risk & Ambiguity Analysis

- **Risk:** None. Both gates (state permit + cooldown > 0) are checked sequentially in `_try_attack()`.
- **Edge case:** Attack at exact frame when cooldown reaches 0.0 — `maxf(0.0, val - delta)` ensures the value floors at 0.0, and the check `> 0.0` correctly allows it.

### 4. Clarifying Questions

None.

---

## Implementation Summary

### Code Changes Required

| Change | File | Description |
|--------|------|-------------|
| Add `_mutation_cooldowns.clear()` | `scripts/player/player_controller_3d.gd` → `reset_hp()` | Clear cooldowns on death/respawn |

**All other behaviors (CDB-1, CDB-2, CDB-4, CDB-5) are already correctly implemented and require NO code changes — only test coverage.**

### Test Strategy

The Test Designer should create a single integration test file `tests/scripts/attacks/test_cooldown_cross_state_behavior.gd` with test methods organized by requirement:
- CDB-1: Parameterized state loop asserting decrement
- CDB-2: Sequential state transition with intermediate cooldown assertions
- CDB-3: `reset_hp()` clears dictionary
- CDB-4: Multi-key dictionary independence across transitions
- CDB-5: Rapid input + cross-state attack rejection

### Key Source Files

- `scripts/player/player_controller_3d.gd` — `_tick_controller_timers()` (line 229-235), `_try_attack()` (line 675-711), `reset_hp()` (line 765-779)
- `scripts/player/player_state_machine.gd` — `PlayerState` enum, `transition()`
- `scripts/player/player_input_action_policy.gd` — `_PERMIT_MATRIX`
- `scripts/attacks/attack_resource.gd` — `cooldown` property
- `scripts/attacks/attack_database.gd` — `get_base_attack()`, `get_fused_attack()`

### Edge Cases for Test Breaker

- Negative delta values (should not increase cooldown)
- Very large delta (cooldown floors at 0.0, never goes negative)
- Empty `_mutation_cooldowns` dictionary iteration (no-op, no crash)
- Cooldown key not present in dictionary (`get(key, 0.0)` returns 0.0 — attack allowed)
- State set to DEAD + cooldown still > 0 — verify no crash on `_tick_controller_timers` (dictionary still iterates)
- Fused cooldown key independence from individual mutation keys
