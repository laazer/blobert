# Integration Roadmap: Encoding Battle-Tested Patterns into Blobert Specs

**Goal:** Update existing blobert tickets with architectural details so implementers naturally converge on proven patterns without referencing the reference project.

**Scope:** Core gameplay (movement, abilities, input, state machine)

---

## Phase 1: Audit Current Tickets

**Action:** Check existing specs in `project_board/specs/` against these categories:

### Movement & Physics
- [ ] `player_movement_3d_spec.md` — Does it define jump buffer and coyote time?
- [ ] `player_jumping_spec.md` — Does it document frame-order execution?
- [ ] One-way platform spec — Does it exist? Should it?

### State Machine
- [ ] `player_state_machine_spec.md` — Does it exist?
- [ ] If yes, does it enumerate all states and transition rules?
- [ ] Does it forbid certain state combinations?

### Ability System
- [ ] `ability_system_design_spec.md` or similar — Does it exist?
- [ ] If yes, does it define EffectType enum?
- [ ] Does it document data-driven dispatch (match on EffectType)?
- [ ] Does it define use_duration vs. cooldown semantics?

### Input Handling
- [ ] `input_handling_spec.md` — Does it exist?
- [ ] Does it list all input actions?
- [ ] Does it document which states permit which actions?

### Renderer Integration
- [ ] `player_renderer_spec.md` — Does it exist?
- [ ] Does it enforce one-way data flow (controller → renderer)?

---

## Phase 2: Enrich Specs with Architectural Details

### Template: Spec Enrichment Sections

Each spec should include:

**Architecture Rationale:**
- Why this pattern, not others
- What problems does it solve
- What constraints does it impose

**Data Structures:**
- Exact types and their fields
- Constants and their values
- Enum values (for EffectType, States, etc.)

**Execution Order / Frame Structure:**
- Step-by-step what happens each frame
- When checks happen (before or after apply)
- Where side effects occur

**Integration Points:**
- Which other systems does this depend on
- Which systems depend on this
- Signal/callback responsibilities

**Acceptance Criteria:**
- Examples of correct and incorrect behavior
- Edge cases to validate
- Performance constraints

---

## Phase 3: Ticket Updates by Category

### A. State Machine Spec (`player_state_machine_spec.md`)

**Current Gap:** Likely either missing or vague about transitions.

**Update Content:**

```markdown
## States and Transitions

States (13 total):
- IDLE, WALK, JUMP, FALL, FLOAT, INHALE, INHALE_HOLD, SWALLOW, SPIT, 
  ABILITY_USE, CHARGE_UP, CROUCH, HURT, DEAD

Transition Rules (implemented in can_transition_to()):
- FLOAT → only from [JUMP, FALL, FLOAT]
- ABILITY_USE → NOT from [HURT, DEAD, INHALE, INHALE_HOLD, SWALLOW, SPIT]
- CHARGE_UP → from [IDLE, WALK, JUMP, FALL, FLOAT]
- HURT → NOT if already HURT or DEAD
- All ground states → [IDLE, WALK, JUMP, FALL, FLOAT, ABILITY_USE, HURT]

State Timer:
- Incremented each _physics_process(delta)
- Reset to 0.0 on every transition
- Used for minimum action durations (e.g., 0.05s before float from jump)

## Frame Structure (Pseudocode)

_physics_process(delta):
  1. state_machine.update(delta)  # Advance state_timer
  2. _update_timers(delta)        # Coyote, jump buffer, iframes
  3. _handle_state(delta)         # Input checks, physics apply
  4. _sync_renderer()             # One-way: controller → renderer
  5. move_and_slide()

## Acceptance Criteria

- [x] Cannot transition to ABILITY_USE while HURT
- [x] Float can only extend from JUMP/FALL/FLOAT (not from IDLE)
- [x] Minimum action durations honored (state_timer)
- [x] State transitions are atomic (no mid-transition input reads)
```

**Why this helps:** Implementer sees the exact transition graph and frame order. No guessing.

---

### B. Movement Physics Spec (`player_movement_spec.md`)

**Current Gap:** Likely missing coyote and jump buffer.

**Update Content:**

```markdown
## Jump Buffer and Coyote Time

### Jump Buffer (0.1 seconds)
- Player presses jump; store press time in _jump_buffer_timer
- If _jump_buffer_timer > 0 and is_on_floor() → consume buffer, jump
- Decrement each frame

**Why:** Removes frame-perfect input. Player can press jump up to 0.1s before landing.

### Coyote Time (0.1 seconds)
- On transition from is_on_floor() to not is_on_floor(), set _coyote_timer = COYOTE_TIME
- Jump check: if _coyote_timer > 0 and check_jump_input() → jump
- Decrement each frame

**Why:** Rewards skill. Player can jump up to 0.1s after walking off a platform.

## One-Way Platforms

When velocity.y > 0 (moving up): collision_mask = GROUND only (exclude ONE_WAY)
When velocity.y ≤ 0 (falling): collision_mask = GROUND | ONE_WAY

**Why:** Player passes through from below, lands from above.

## Frame Order (Mandatory)

_physics_process(delta):
  1. _apply_gravity(delta)              # Modify velocity.y
  2. _read_input(delta)                 # Check Input.*
  3. _update_velocity(delta)            # Move velocity.x toward target
  4. _update_one_way_mask()             # Adjust collision based on velocity.y
  5. move_and_slide()

Violating this order causes:
- Jump checks after gravity = jumps feel sluggish
- Input reads after movement = frame lag
- Collision updates after move = one-way platforms fail

## Acceptance Criteria

- [x] Jump is executable up to 0.1s before landing
- [x] Jump is executable up to 0.1s after walking off platform
- [x] Jump from one-way platform requires moving down first
- [x] Player can jump through one-way platform from below
```

**Why this helps:** Implementer knows the exact timing guarantees and frame dependencies.

---

### C. Ability System Spec (`ability_system_design_spec.md`)

**Current Gap:** Likely missing or vague about EffectType dispatch and charge scaling.

**Update Content:**

```markdown
## Ability Data Model

### AbilityResource Properties
```gdscript
effect_type: EffectType  # Determines dispatch behavior
damage: float
use_duration: float      # Active time (not cooldown)
projectile_speed: float
burst_count: int
boomerang_distance: float
color: Color
is_chargeable: bool
```

### EffectType Enum

```
PROJECTILE, BOOMERANG, LOB, BURST, SCATTER, PILLAR,          # Projectile family
MELEE_CLOSE, MELEE_WIDE,                                      # Melee family
AURA, AURA_WIDE,                                              # Area family
STONE,                                                        # Physical family
GRAPPLE, MOVEMENT,                                            # Utility family
BEAM_CHANNEL, SLEEP_HEAL, MIRROR_PARRY, BLACK_HOLE          # Sustained family
```

Each EffectType has **one dispatch handler** in AbilityExecutor.

### Charge Scaling

```
charge_level: 0.0 (no charge) → 1.0 (full charge)
damage_multiplier = 1.0 + charge_level * (2.2 - 1.0)

range: 1.0× (no charge) → 2.2× (full charge)
```

## Ability Activation Flow

### Non-Chargeable
```
Input "ability" → _begin_ability_action()
  → GameState.ability_is_chargeable == false
  → _use_ability()
  → state_machine.transition(ABILITY_USE)
  → ability_executor.execute(ability_id)
  → AbilityExecutor._dispatch_ability(id)
    → match EffectType: behavior_handler(id)
```

### Chargeable
```
Input "ability" (pressed) → _begin_ability_action()
  → GameState.ability_is_chargeable == true
  → state_machine.transition(CHARGE_UP)
  → _charge_timer starts incrementing
  → kirby_visual.charge_level = _charge_timer / MAX_CHARGE_TIME (visual feedback)

Input "ability" (released) → _fire_charged_ability()
  → charge_level = _charge_timer / MAX_CHARGE_TIME
  → state_machine.transition(ABILITY_USE)
  → ability_executor.execute_charged(ability_id, charge_level)
  → scales damage by charge_level
```

## Use Duration (Not Cooldown)

```
execute(ability_id):
  active = true
  use_timer = AbilityDB.get_use_duration(ability_id)
  _dispatch_ability(ability_id)

_physics_process(delta):
  if active:
    use_timer -= delta
    if use_timer <= 0.0:
      _end_ability()
      active = false

_state_ability_use(delta):
  if not ability_executor.active:
    state_machine.transition(IDLE)
```

**Semantics:** Ability is "locked in" for use_duration. After timer expires, immediately available again. No separate cooldown.

Example: Punch with use_duration = 0.15s
- Frame 0: ability starts
- Frame 9 (0.15s later): ability ends, Kirby is back in IDLE
- Frame 10: Kirby can punch again

## Adding a New Ability

1. Add new ID constant to AbilityDB
2. Create AbilityResource with effect_type, damage, use_duration, etc.
3. If EffectType is novel: add new case in `_dispatch_ability()`
4. If EffectType already exists: no code changes needed (data-driven)

**Example:** Adding "Fireball" (PROJECTILE type)
```gdscript
# In AbilityDB
const FIREBALL := 201

# Create AbilityResource
# - effect_type = PROJECTILE
# - projectile_speed = 300
# - damage = 1.5
# - use_duration = 0.2
# - color = Color.RED

# No code changes needed; _dispatch_ability() already handles PROJECTILE
```

## Acceptance Criteria

- [x] Abilities dispatch based on EffectType, not ID
- [x] New abilities require no code changes outside AbilityExecutor (if EffectType exists)
- [x] Charge scaling is multiplicative: 1.0–2.2× range
- [x] use_duration is the only timer; no separate cooldown
- [x] Ability is reusable immediately after use_timer expires
- [x] EffectType dispatch covers 15+ ability variants (punch, fire, ice, etc.)
```

**Why this helps:** Implementer understands the extension mechanism. Adding new abilities is data-centric.

---

### D. Input Handling Spec (`input_system_spec.md`)

**Update Content:**

```markdown
## Input Actions

Registered at startup (InputMapper):
- jump, ability, inhale, move_left, move_right, move_down, swap_ability, menu

## Input Checks by State

### IDLE, WALK (ground states)
```gdscript
if _read_horizontal_input() != 0.0:
  state_machine.transition(WALK)
if Input.is_action_just_pressed("jump"):
  _start_jump()
if Input.is_action_just_pressed("ability") and GameState.has_any_ability():
  _begin_ability_action()
if Input.is_action_just_pressed("inhale"):
  state_machine.transition(INHALE)
if Input.is_action_just_pressed("move_down"):
  state_machine.transition(CROUCH)
```

### JUMP, FALL (air states)
```gdscript
if Input.is_action_just_pressed("jump"):
  state_machine.transition(FLOAT)  # Only if state_timer > 0.05
if Input.is_action_just_pressed("ability") and GameState.has_any_ability():
  _begin_ability_action()
if Input.is_action_just_pressed("inhale"):
  state_machine.transition(INHALE)
```

### CHARGE_UP (holding ability)
```gdscript
_charge_timer += delta
if not Input.is_action_pressed("ability"):
  _fire_charged_ability()
```

### NOT checked in: INHALE, INHALE_HOLD, SWALLOW, SPIT, HURT, DEAD

## Input → State Mapping Table

| Input | States Checked | Transition |
|-------|----------------|-----------|
| jump | IDLE, WALK, JUMP, FALL | JUMP → FLOAT → FALL |
| ability | IDLE, WALK, JUMP, FALL, CROUCH | CHARGE_UP or ABILITY_USE |
| inhale | All ground + air | INHALE |
| move_down | IDLE, WALK | CROUCH |
| swap_ability | Most states | No state change |

## Acceptance Criteria

- [x] Input is only checked in permitted states
- [x] State machine transitions enforce ability use blocking
- [x] New abilities don't require new input actions
- [x] Input checks are atomic (read once, consume once)
```

**Why this helps:** Implementer knows exactly which states permit which inputs.

---

### E. Renderer Integration Spec (`player_renderer_integration_spec.md`)

**Update Content:**

```markdown
## One-Way Data Flow

```
_physics_process(delta):
  [Controller updates game state]
  _sync_renderer()
    → renderer.facing_right = facing_right
    → renderer.current_state = state
    → renderer.charge_level = charge_level
    → renderer.ability_color = ability_color
    → renderer.is_sleeping = is_sleeping
    → renderer.is_beaming = is_beaming

_process(delta):  [Renderer updates visuals]
  _update_walk_animation(delta)
  _sync_appearance(delta)
```

**Key Constraint:** Renderer never calls back into controller. No signals, no methods.

## Renderer Reads (Read-Only)

```gdscript
var facing_right: bool
var current_state: KirbyStateMachine.State
var charge_level: float
var ability_color: Color
var is_sleeping: bool
var is_beaming: bool
```

## Renderer Responsibilities

- Animate walk cycle based on current_state and timer
- Apply charge_level to visual feedback (glow, size, etc.)
- Blink based on blink_visible timer (set by controller iframes)
- Apply ability_color to badge/aura
- Mirror scale based on facing_right

## Renderer Cannot

- Emit signals back to controller
- Call controller methods
- Modify controller state
- Depend on frame order

## Acceptance Criteria

- [x] Renderer is a child node (not the controller itself)
- [x] All renderer state is written by controller each _physics_process
- [x] Renderer does not call controller methods
- [x] Animation state is always in sync with game state
- [x] Renderer visual bugs cannot break gameplay
```

**Why this helps:** Implementer knows the boundary. Renderer is isolated and safe.

---

## Phase 4: Ticket Template for New Abilities

When a new ability ticket is created, it should include:

```markdown
## Ability Definition

- **EffectType:** PROJECTILE | MELEE_CLOSE | AURA | BEAM_CHANNEL | MOVEMENT | etc.
- **Chargeable:** Yes / No
- **Damage:** X.X
- **Use Duration:** Y.Y seconds
- **Range/Radius:** Z units (if applicable)
- **Knockback:** Static (X, Y, 0) or Dynamic (toward/away from Kirby)

## Execution Sequence

1. On activation:
   - [SFX/VFX description]
   - [Movement/velocity changes]
   - [Enemy damage + knockback]

2. If sustained (BEAM_CHANNEL, SLEEP_HEAL, BLACK_HOLE):
   - Tick behavior every N seconds
   - Damage/heal per tick
   - Cleanup on end

3. On end:
   - [Final effect, if any]
   - Return to IDLE

## Acceptance Criteria

- [x] Ability follows dispatch pattern (no custom state machine)
- [x] Damage is scaled by charge_level if chargeable
- [x] Effects match EffectType family (visual + gameplay consistency)
- [x] No input checks needed (dispatch handles it)
```

---

## Phase 5: Validation Checklist

Before a ticket is marked COMPLETE:

- [ ] **State Machine:** Does the implementation respect transition rules?
- [ ] **Ability Dispatch:** Does new EffectType handler only live in AbilityExecutor?
- [ ] **Charge Scaling:** Is damage scaled by 1.0–2.2× correctly?
- [ ] **Use Duration:** Is use_timer the only ability timer (no separate cooldown)?
- [ ] **Renderer Sync:** Is controller state synced to renderer each frame?
- [ ] **Input Gating:** Are abilities blocked in correct states?
- [ ] **Knockback:** Are enemies pushed/pulled correctly?
- [ ] **No Callbacks:** Does renderer never call back to controller?

---

## Timeline

- **Week 1:** Audit existing specs (Phase 1)
- **Week 2:** Enrich core specs (Phase 2–3: State Machine, Movement, Ability System)
- **Week 3:** Enrich input + renderer specs (Phase 3)
- **Week 4:** Test ticket template + validation checklist on first new ability

---

## Example: How a Spec Prevents Surprises

**Old Vague Spec:**
> "Implement a fire ability that does damage and knockback."

**Result:** Implementer invents a custom state, hooks up signals, adds a cooldown timer, and creates a new input action.

**New Rich Spec:**
> "Fire Punch: EffectType.MELEE_CLOSE, chargeable, 1.5 damage, 0.15s use_duration.
> On activation: boost Kirby up, hit enemies in 36-unit cone with 1.0×–2.2× scaled damage.
> Knockback: 100.0 units horizontal, 80.0 units vertical.
> No code changes needed outside AbilityExecutor._dispatch_ability()."

**Result:** Implementer writes `_melee_close(FIRE_PUNCH)` inside the existing dispatch, uses charge_scale for damage, and is done in an hour.

---

## Tracking

Record which specs have been enriched:
- [ ] player_state_machine_spec.md
- [ ] player_movement_spec.md
- [ ] ability_system_design_spec.md
- [ ] input_system_spec.md
- [ ] player_renderer_integration_spec.md

Add a note to each: "Updated [date] with architectural patterns."
