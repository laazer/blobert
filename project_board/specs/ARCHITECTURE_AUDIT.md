# Architecture Audit: Battle-Tested Player Systems

**Date:** 2026-05-16  
**Source:** Analysis of a complete, working 3D platformer with complex ability system  
**Context:** Patterns to encode into blobert specs without implementation reference

---

## 1. State Machine: Simple, Explicit Transitions

**Pattern:** Lightweight RefCounted FSM with explicit transition rules.

```
States: IDLE, WALK, JUMP, FALL, FLOAT, INHALE, INHALE_HOLD, SWALLOW, SPIT, 
         ABILITY_USE, CHARGE_UP, CROUCH, HURT, DEAD

Transition rules live in can_transition_to(new_state):
  - FLOAT only from: JUMP, FALL, FLOAT (hold-to-extend mechanic)
  - ABILITY_USE blocked by: HURT, DEAD, INHALE, INHALE_HOLD, SWALLOW, SPIT
  - HURT blocked when: already HURT or DEAD
  - Most ground states can transition to ABILITY_USE mid-air

State timer tracks duration since entry (incremented each frame).
Minimum action durations enforced via state_timer checks (e.g., 0.05s before float).
```

**Why this works:**
- No spaghetti conditionals—transitions are guarded at the machine level
- Soft constraints (can_transition_to) vs. hard blocks keep code readable
- State timer enables cool-down logic without separate timer variables per action
- Dispatch via match statement is O(1) and cache-friendly

**For blobert:**
- Encode state list (what states exist)
- Encode transition graph (which states can reach which others)
- Encode "special handling": states that require minimum duration before exit


---

## 2. Physics: Layered, Frame-Ordered Execution

**Pattern:** Physics happens in a strict order each `_physics_process`:
1. State machine updates (advance state timer)
2. Update logical timers (coyote, jump buffer, iframes)
3. Dispatch state handler (reads input, applies physics)
4. Update collision masks (one-way platforms)
5. Sync renderer (all visual state from controller state)
6. Call move_and_slide()

**Key constants:**
- `JUMP_VELOCITY := 260.0` — velocity imparted on jump
- `GRAVITY := 600.0` — downward acceleration when airborne
- `WALK_SPEED := 80.0` — horizontal movement target
- `COYOTE_TIME := 0.1` — frames after leaving ground to still jump
- `JUMP_BUFFER_TIME := 0.1` — frames before landing to queue jump

**Jump buffering:** Store jump input time. Check if `buffer_timer > 0 and is_on_floor()` → consume buffer.

**Coyote time:** On transition from floor to air, set `coyote_timer = COYOTE_TIME`. Decrement each frame. Jump check: `if coyote_timer > 0 and check_jump_input()`.

**One-way platforms:** Collision mask changes based on velocity direction:
- Moving up? Only solid ground (exclude one-way).
- Moving down? Include one-way platforms.
- This allows jumping through from below, landing from above.

**Why this works:**
- Explicit order prevents "did I check this before gravity?" bugs
- Jump buffer removes frame-perfect input requirements
- Coyote time rewards skilled play without feeling unfair
- One-way mask trick is elegant and robust

**For blobert:**
- Specs must document the frame-order execution
- Separate "input check" from "physics apply"
- Define coyote + buffer times as acceptance criteria
- Detail one-way platform behavior in level design spec


---

## 3. Ability System: Data-Driven Dispatch

**Pattern:** Ability execution is **stateless dispatch**, not state machines.

### Data Layer
Each ability has:
- `id: int` (unique identifier)
- `effect_type: EffectType` (enum: PROJECTILE, MELEE_CLOSE, MELEE_WIDE, AURA, STONE, BEAM_CHANNEL, SLEEP_HEAL, MIRROR_PARRY, BLACK_HOLE, MOVEMENT, etc.)
- `damage: float`
- `use_duration: float` (how long ability stays active)
- `projectile_speed: float` (if applicable)
- `burst_count: int` (if applicable)
- `boomerang_distance: float` (if applicable)
- `color: Color` (visual feedback)

### Execution Layer
```gdscript
func _dispatch_ability(ability_id: int) -> void:
  match AbilityDB.get_effect_type(ability_id):
    E.PROJECTILE:   _fire_forward(ability_id)
    E.MELEE_CLOSE:  _melee_close(ability_id)
    E.MELEE_WIDE:   _melee_wide(ability_id)
    E.AURA:         _aura(ability_id)
    E.BEAM_CHANNEL: _beam_channel(ability_id)
    E.SLEEP_HEAL:   _sleep_enter(ability_id)
    ...
```

New abilities require:
1. New `EffectType` entry (if behavior is novel)
2. New ability ID in the database
3. New case in `_dispatch_ability()` (if new EffectType)
4. Implementation of behavior function (e.g., `_projectile_fire()`)

### Charge Scaling
Abilities can be charged. Charge level: 0.0 (no charge) → 1.0 (full charge).
Damage multiplier: `1.0 + charge_level * (MAX_CHARGE_MULT - 1.0)` where `MAX_CHARGE_MULT = 2.2`.

Chargeable abilities:
- Enter CHARGE_UP state
- Charge timer increments while ability button held
- On release, call `execute_charged(ability_id, charge_level)`
- Non-chargeable abilities go straight to ABILITY_USE

### Activation Gate
```gdscript
func _begin_ability_action() -> void:
  if GameState.ability_is_chargeable:
    state_machine.transition(KirbyStateMachine.State.CHARGE_UP)
    _charge_timer = 0.0
  else:
    _use_ability()
```

Why this works:
- Dispatch is O(1) and declarative (match on enum)
- Adding new ability is just a new row in the database + one case in dispatch
- Charge scaling is multiplicative and uniform
- Effect-type driven dispatch means animation/sound can query the same enum

**For blobert:**
- Spec should define the EffectType enum with clear categories
- Specs should document "what happens in execute()" as a sequence of steps
- Acceptance criteria: "New abilities require no code changes outside AbilityExecutor"
- Detail charge scaling acceptance criteria


---

## 4. Timing: Active Flag + Use Timer

**Pattern:** Ability executor tracks `active: bool` and `use_timer: float`.

```gdscript
func execute(ability_id: int) -> void:
  active = true
  use_timer = AbilityDB.get_use_duration(ability_id)
  _dispatch_ability(ability_id)

func _physics_process(delta: float) -> void:
  if active:
    use_timer -= delta
    _tick_sustained(delta)  # For beam, sleep, black hole
    if use_timer <= 0.0:
      _end_ability()

func _end_ability() -> void:
  _on_ability_end(current_ability)
  active = false
```

Controller checks `if not ability_executor.active` to transition back to IDLE.

Sustained abilities (beam, sleep, black hole) tick each frame:
- Beam: deal damage to enemies in cone every 0.12s
- Sleep: heal Kirby every frame at a fixed rate
- Black hole: grow radius, pull enemies, tick damage

Why this works:
- No nested state machines
- Active flag is the source of truth
- Timer expiry triggers cleanup automatically
- Tick-based sustained abilities are predictable and testable

**For blobert:**
- Specs should document: "Abilities block input and state transitions until active = false"
- Detail what happens on _physics_process for sustained abilities
- Acceptance criteria: "Ability can be interrupted by state transitions (land, take damage)" if that's desired


---

## 5. Knockback and Enemy Interaction

**Pattern:** Damage calls include knockback vector.

```gdscript
func _melee_close(ability_id: int) -> void:
  var damage := _scaled_damage(ability_id)
  var knockback := Vector3(dir_x * 100.0, 80.0, 0.0)
  _damage_enemies_in_range(hit_pos, MELEE_RANGE, damage, knockback)

# Call signature:
enemy.take_damage(damage: float, knockback: Vector3 = Vector3.ZERO)
```

Some abilities use dynamic knockback based on enemy position:
- Gravity abilities: pull toward Kirby
- Wind abilities: push away from Kirby
- Mirror abilities: reflect away from Kirby

These iterate over enemies and calculate knockback per target:
```gdscript
for enemy in get_tree().get_nodes_in_group("enemy"):
  if in_range:
    var knockback := (enemy.position - kirby.position).normalized() * force
    enemy.take_damage(damage, knockback)
```

Why this works:
- Knockback is independent of damage
- Per-enemy knockback enables complex interactions (pull + damage = gravity abilities)
- Group queries are O(n enemies) but simple and easy to debug

**For blobert:**
- Specs should encode knockback as part of ability definition
- Detail which abilities have static vs. dynamic knockback
- Acceptance criteria: "Knockback can be 0.0 (e.g., freeze) or directional"


---

## 6. Input Handling: Centralized, Action-Based

**Pattern:** Single InputMapper autoload registers actions.

```gdscript
# InputMapper._register_actions()
_bind("jump",        [KEY_SPACE, KEY_UP])
_bind("ability",     [KEY_X])
_bind("inhale",      [KEY_Z])
_bind("move_left",   [KEY_A, KEY_LEFT])
_bind("move_right",  [KEY_D, KEY_RIGHT])
_bind("move_down",   [KEY_S, KEY_DOWN])
_bind("swap_ability",[KEY_C])
```

Controller checks input via `Input.is_action_just_pressed()` and `Input.is_action_pressed()`.

**Why this works:**
- Input mapping is separate from game logic
- New input bindings don't touch controller code
- InputMap is a Godot singleton, so autoload is natural
- Action names are symbolic (not magic key codes scattered in code)

**For blobert:**
- InputMapper should already exist (check)
- Specs should document which actions are checked in which states
- Acceptance criteria: "New abilities don't require new input actions"


---

## 7. Renderer Sync: One-Way Data Flow

**Pattern:** Controller is the source of truth. Renderer syncs each frame.

```gdscript
# KirbyController._sync_renderer() called each _physics_process
func _sync_renderer() -> void:
  kirby_visual.facing_right = facing_right
  kirby_visual.current_state = state_machine.current
  kirby_visual.ability_color = ...

# KirbyRenderer._process(delta)
func _process(delta: float) -> void:
  _update_walk_animation(delta)
  _sync_appearance(delta)  # Reads facing_right, current_state, charge_level, etc.
```

Renderer animates based on state (idle, walk, jump, sleep, etc.) without knowing game logic.

Why this works:
- No callback hell
- Renderer can't break gameplay (it's read-only from controller's perspective)
- Animation state is always in sync with game state
- Visual bugs are isolated to renderer

**For blobert:**
- Specs should enforce: "Renderer is a child node that reads controller state only"
- Detail which state properties the renderer reads (facing, current_state, charge_level, is_using_ability, etc.)
- Acceptance criteria: "Renderer cannot emit signals back to controller"


---

## 8. Cooldown Semantics: Use Duration Only

**Pattern:** No separate cooldown timer. Ability is "active" for `use_duration`, then done.

Example:
- Punch: use_duration = 0.15s → active for 0.15s, then return to IDLE
- Beam: use_duration = 2.0s → active for 2.0s (tick each frame), then return to IDLE
- Charge: state = CHARGE_UP until button released

There is **no cooldown before next use**. Once active = false, ability can be used again next frame.

Why this works:
- Simpler than cooldown-per-ability
- Ability duration defines how long Kirby is "locked in"
- Natural rhythm: ability plays, Kirby returns to control, can act immediately

**For blobert:**
- Spec: "Cooldown is named use_duration, not cooldown"
- Acceptance criteria: "Abilities are executable again once executor.active becomes false"
- Detail edge case: "If ability is interrupted (e.g., take damage), use_duration is not refunded"


---

## 9. State-Ability Interaction: Selective Blocking

**Pattern:** Some states block ability use. Controller checks in appropriate states.

```gdscript
# In _state_idle, _state_walk, _state_jump, _state_fall
if Input.is_action_just_pressed("ability") and GameState.has_any_ability():
  _begin_ability_action()

# NOT checked in: INHALE, INHALE_HOLD, SWALLOW, SPIT, HURT, DEAD
```

Transition rules enforce further: ABILITY_USE can't be entered from HURT, DEAD, or inhale states.

Why this works:
- Clear which states allow ability activation
- Input consumption is explicit (not guarded by state machine)
- State machine provides a second layer of protection

**For blobert:**
- Specs should document: "Which states permit ability input?"
- Acceptance criteria: "Abilities are blocked during inhale, while hurt, while dead"
- Detail edge case: "Ability interrupts move_down crouch input"


---

## 10. Enemy Groups and Spatial Queries

**Pattern:** Abilities iterate over `get_tree().get_nodes_in_group("enemy")`.

```gdscript
for enemy in get_tree().get_nodes_in_group("enemy"):
  var dist := global_position.distance_to(enemy.global_position)
  if dist <= range:
    if enemy.has_method("take_damage"):
      enemy.take_damage(damage, knockback)
```

Distance checks are explicit (no Area3D). Directional checks use offset:
```gdscript
var offset := enemy.global_position - kirby.global_position
if offset.length() <= MELEE_WIDE_RANGE and offset.x * dir_x >= -8.0:
  # Enemy is in front, within range
```

Why this works:
- Groups are simple and flexible
- Distance checks are O(n enemies) but cache-friendly
- Directional checks prevent hitting enemies behind Kirby
- No Area3D overlap callbacks = no race conditions

**For blobert:**
- Specs should enforce: "Enemies are in 'enemy' group"
- Detail spatial queries: "Distance checks use vector length; directional checks use dot product or offset.x * facing"
- Acceptance criteria: "Abilities work with arbitrary enemy counts"


---

## Summary: Principles Embedded in This Architecture

| Principle | Implementation |
|-----------|-----------------|
| **Stateless dispatch** | Match on EffectType, not ability ID |
| **Data-driven** | Ability properties live in AbilityResource; behavior follows enum |
| **Separation of concerns** | Controller (logic), Renderer (animation), AbilityExecutor (ability dispatch) |
| **No racing conditions** | One-way data flow; renderer reads controller state each frame |
| **Predictable timing** | Explicit frame order; use_duration is the only timer |
| **Extensible without code** | New abilities = new database row + case in dispatch (if new EffectType) |
| **Testable** | Pure state machine; stateless ability dispatch; no callbacks |

---

## Next Steps

These patterns should be encoded into blobert specs as:
1. **Spec for State Machine**: Define states, transitions, timer behavior
2. **Spec for Ability System**: Define EffectType, dispatch rules, charge scaling
3. **Spec for Movement**: Define coyote, jump buffer, one-way logic
4. **Spec for Cooldowns**: Clarify use_duration vs. cooldown
5. **Spec for Input**: Document action-to-state mapping

Each spec should be specific enough that an implementer naturally converges on this architecture.
