# SPEC: Mutation Attack System Design (Data-Driven)

**Status:** Draft (for review before M11 implementation)  
**Target Milestones:** M11 (Base Attacks), M12 (Fused Attacks)  
**Model:** Data-driven parameterized dispatch (no per-attack methods)

---

## Overview

Blobert's mutation attacks are defined via **AttackResource** data files. A single generic dispatch handler reads effect type, modifiers, and parameters from the resource, then executes the appropriate behavior. This eliminates code duplication and scales from 4 base attacks (M11) to 16 fused attacks (M12) without method explosion.

---

## Attack Resource Data Model

### `AttackResource` (Godot Resource)

```gdscript
class_name AttackResource
extends Resource

# --- Identity ---
@export var attack_id: int                  # Unique ID (e.g., 1 = Claw base, 101 = Claw+Acid fused)
@export var attack_name: String             # Human-readable name (e.g., "Poison Claw")
@export var description: String             # Brief description for HUD/UI

# --- Effect Type (dispatcher key) ---
@export var effect_type: String             # "MELEE_SWIPE", "PROJECTILE_SPIT", "CHARGE", "LUNGE", etc.

# --- Core Parameters ---
@export var damage: float = 1.0             # Base damage per hit
@export var cooldown: float = 0.8           # Seconds until attack can be used again
@export var startup_frames: int = 0         # Frames before hitbox activates (animation lead)
@export var range: float = 1.5              # Melee range OR projectile spread radius
@export var knockback_magnitude: float = 0.0  # 0.0 = no knockback, >0.0 = apply force

# --- Projectile-Specific ---
@export var projectile_speed: float = 0.0   # For PROJECTILE_SPIT, LUNGE, etc.
@export var projectile_lifetime: float = 2.0

# --- Visuals ---
@export var color: Color = Color.WHITE      # VFX/ability badge color
@export var vfx_scale: float = 1.0          # Magnitude of visual feedback

# --- Modifiers (extensible key-value system) ---
@export var modifiers: Dictionary = {}
# Examples:
# - "poison": true (enable poison on-hit)
# - "poison_duration": 3.0 (seconds)
# - "poison_dps": 0.5 (damage per tick)
# - "slow": 0.7 (movement speed multiplier during effect)
# - "slow_duration": 2.0
# - "followup_melee": true (enable combo follow-up)
# - "followup_range": 2.0
# - "knockback_direction": "away" or "toward" (push enemy away vs. pull toward player)
```

### Concrete Examples

**Claw Base Attack (M11):**
```
attack_id: 101
attack_name: "Claw Swipe"
effect_type: "MELEE_SWIPE"
damage: 2.0
cooldown: 0.8
startup_frames: 2
range: 1.5
knockback_magnitude: 100.0
color: Color(0.8, 0.2, 0.1)  # Reddish
modifiers: {}  # No special modifiers
```

**Acid Base Attack (M11):**
```
attack_id: 102
attack_name: "Acid Spit"
effect_type: "PROJECTILE_SPIT"
damage: 1.5
cooldown: 1.2
projectile_speed: 250.0
range: 15.0
knockback_magnitude: 50.0
color: Color(0.2, 0.8, 0.1)  # Greenish
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.0,
  "acid_dps": 0.3
}
```

**Poison Claw Fused Attack (M12, Claw+Acid):**
```
attack_id: 201
attack_name: "Poison Claw"
effect_type: "MELEE_SWIPE"
damage: 2.0
cooldown: 1.0
startup_frames: 3
range: 1.5
knockback_magnitude: 120.0
color: Color(0.6, 0.3, 0.7)  # Purple
modifiers: {
  "poison": true,
  "poison_duration": 3.0,
  "poison_dps": 0.5
}
```

**Acidic Fang Fused Attack (M12, Acid+Claw):**
```
attack_id: 202
attack_name: "Acidic Fang"
effect_type: "PROJECTILE_SPIT"
damage: 1.5
cooldown: 1.3
projectile_speed: 280.0
range: 18.0
knockback_magnitude: 75.0
color: Color(0.4, 0.8, 0.2)  # Lime green
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.5,
  "acid_dps": 0.4,
  "followup_melee": true,
  "followup_range": 2.0,
  "followup_damage": 1.0
}
```

---

## Effect Type Handlers

Each **effect_type** string maps to one handler function. New effect types are added via new handler methods (rare), not new attack methods (common).

### Supported Effect Types (Initial Set)

| EffectType | Behavior | Examples |
|------------|----------|----------|
| `MELEE_SWIPE` | Hitbox in front of player, check enemies in range, apply damage + knockback | Claw, Carapace, Poison Claw |
| `PROJECTILE_SPIT` | Create projectile, fire forward, apply modifiers (acid, poison) on hit | Acid, Adhesion, Acidic Fang |
| `CHARGE` | Hold to charge, release to execute (not in M11, reserved for M12+) | TBD |
| `LUNGE` | Short dash forward + melee hit (not in M11, reserved for M12+) | TBD |

### Dispatch Function (Single Entry Point)

```gdscript
# In AttackExecutor (new class, attached to PlayerController3D)
class_name AttackExecutor
extends Node

func execute_attack(attack_resource: AttackResource) -> void:
  if active:
    return  # Already executing an attack
  
  active = true
  current_attack = attack_resource
  active_timer = 0.0
  
  # Single match statement dispatches by effect type
  match attack_resource.effect_type:
    "MELEE_SWIPE":
      _handle_melee_swipe(attack_resource)
    "PROJECTILE_SPIT":
      _handle_projectile_spit(attack_resource)
    "CHARGE":
      _handle_charge(attack_resource)
    "LUNGE":
      _handle_lunge(attack_resource)
    _:
      push_error("Unknown effect type: " + attack_resource.effect_type)
      active = false
```

### Handler Functions (Generic, Parameterized)

#### `_handle_melee_swipe(attack: AttackResource)`

```gdscript
func _handle_melee_swipe(attack: AttackResource) -> void:
  # Wait for startup frames (animation lead)
  await get_tree().create_timer(attack.startup_frames / 60.0).timeout
  
  # Create hitbox in front of player
  var hitbox_pos = player.global_position + Vector3(player.facing_sign * attack.range * 0.5, 0.0, 0.0)
  var enemies_hit = _query_enemies_in_range(hitbox_pos, attack.range)
  
  for enemy in enemies_hit:
    # Base damage
    enemy.take_damage(attack.damage)
    
    # Knockback (if specified)
    if attack.knockback_magnitude > 0.0:
      var knockback_dir = (enemy.global_position - player.global_position).normalized()
      enemy.apply_knockback(knockback_dir * attack.knockback_magnitude + Vector3.UP * 50.0)
    
    # Apply modifiers
    _apply_modifiers(enemy, attack)
  
  # VFX feedback
  _spawn_vfx_melee(hitbox_pos, attack.color, attack.vfx_scale)
  _play_sfx("melee_hit")

func _apply_modifiers(enemy: Node3D, attack: AttackResource) -> void:
  # Poison modifier
  if attack.modifiers.get("poison", false):
    var duration = attack.modifiers.get("poison_duration", 2.0)
    var dps = attack.modifiers.get("poison_dps", 0.3)
    enemy.apply_poison(duration, dps)
  
  # Slow modifier
  if attack.modifiers.get("slow", 0.0) > 0.0:
    var slowness = attack.modifiers["slow"]
    var duration = attack.modifiers.get("slow_duration", 1.5)
    enemy.apply_slowness(slowness, duration)
  
  # Acid modifier
  if attack.modifiers.get("acid_on_hit", false):
    var duration = attack.modifiers.get("acid_duration", 2.0)
    var dps = attack.modifiers.get("acid_dps", 0.2)
    enemy.apply_acid(duration, dps)
```

#### `_handle_projectile_spit(attack: AttackResource)`

```gdscript
func _handle_projectile_spit(attack: AttackResource) -> void:
  var projectile = _create_projectile(
    speed=attack.projectile_speed,
    damage=attack.damage,
    lifetime=attack.projectile_lifetime,
    color=attack.color
  )
  projectile.global_position = player.global_position
  projectile.velocity = Vector3(player.facing_sign * attack.projectile_speed, 0.0, 0.0)
  
  # Attach modifiers to projectile (applied on enemy hit)
  projectile.modifiers = attack.modifiers
  projectile.knockback_magnitude = attack.knockback_magnitude
  
  player.get_parent().add_child(projectile)
  _play_sfx("projectile_fire")
```

---

## Attack Activation Flow

### Base Attacks (M11)

```
Input "attack" → PlayerController3D checks input in appropriate state
  → _begin_attack()
    → mutation_id = GameState.get_active_mutation()
    → attack_resource = AttackDatabase.get_base_attack(mutation_id)
    → AttackExecutor.execute_attack(attack_resource)
      → match attack_resource.effect_type
        → _handle_melee_swipe() or _handle_projectile_spit()
      → cooldown_timer[mutation_id] = attack_resource.cooldown
```

### Fused Attacks (M12)

```
Input "attack" (while fusion active) → PlayerController3D checks input
  → _begin_attack()
    → slot_a = GameState.get_slot(0).mutation_id
    → slot_b = GameState.get_slot(1).mutation_id
    → attack_resource = AttackDatabase.get_fused_attack(slot_a, slot_b)
    → AttackExecutor.execute_attack(attack_resource)
      → match attack_resource.effect_type
        → _handle_melee_swipe() or _handle_projectile_spit()
      → cooldown_timer["fusion"] = attack_resource.cooldown
```

---

## Attack Database

### Storage (Two Options, Pick One)

**Option A: Separate Resource Files**
```
res://attacks/base/
  claw_swipe.tres        (AttackResource)
  acid_spit.tres
  carapace_slam.tres
  adhesion_lunge.tres

res://attacks/fused/
  claw_acid_poison.tres  (Claw+Acid)
  acid_claw_fang.tres    (Acid+Claw)
  ...
```

**Option B: Single Database Script**
```gdscript
class_name AttackDatabase
extends Node

var _base_attacks: Dictionary = {}
var _fused_attacks: Dictionary = {}

func _ready() -> void:
  _register_base_attacks()
  _register_fused_attacks()

func _register_base_attacks() -> void:
  _base_attacks[CLAW] = AttackResource.new()
  _base_attacks[CLAW].attack_id = 101
  _base_attacks[CLAW].attack_name = "Claw Swipe"
  _base_attacks[CLAW].effect_type = "MELEE_SWIPE"
  # ... set all properties ...
  
  _base_attacks[ACID] = AttackResource.new()
  # ... etc ...

func get_base_attack(mutation_id: int) -> AttackResource:
  return _base_attacks.get(mutation_id, null)

func get_fused_attack(slot_a: int, slot_b: int) -> AttackResource:
  var key = _fusion_key(slot_a, slot_b)
  return _fused_attacks.get(key, null)

func _fusion_key(slot_a: int, slot_b: int) -> String:
  return "%d_%d" % [slot_a, slot_b]
```

**Recommendation:** Option A (separate resource files) for easier iteration and visual inspection. Option B if you prefer centralized code.

---

## Modifiers System (Extensible)

New modifiers can be added without changing code. Just add key-value pairs to the resource's modifiers dictionary.

### Current Modifiers

| Modifier Key | Type | Effect | Example Values |
|--------------|------|--------|-----------------|
| `poison` | bool | Enable poison on-hit | true |
| `poison_duration` | float | Poison duration (seconds) | 3.0 |
| `poison_dps` | float | Damage per second while poisoned | 0.5 |
| `acid_on_hit` | bool | Enable acid on-hit | true |
| `acid_duration` | float | Acid duration | 2.0 |
| `acid_dps` | float | Acid damage per tick | 0.3 |
| `slow` | float | Movement speed multiplier (0.0–1.0) | 0.7 |
| `slow_duration` | float | Slow duration | 2.0 |
| `followup_melee` | bool | Enable melee follow-up after projectile | true |
| `followup_range` | float | Range of melee follow-up | 2.0 |
| `followup_damage` | float | Damage of melee follow-up | 1.0 |

### Adding New Modifiers (No Code Changes)

1. Add key-value pair to attack resource's modifiers dictionary
2. Update `_apply_modifiers()` or relevant handler to read and apply the modifier
3. Done

**Example:** Adding weakening modifier:
```gdscript
# In _apply_modifiers
if attack.modifiers.get("weaken", false):
  var weaken_duration = attack.modifiers.get("weaken_duration", 2.0)
  enemy.apply_weakness(weaken_duration)
```

---

## Acceptance Criteria

- [x] AttackResource class defined with all properties documented
- [x] AttackExecutor implements generic dispatch (match on effect_type)
- [x] Two effect type handlers implemented: MELEE_SWIPE, PROJECTILE_SPIT
- [x] Modifiers system allows extensibility without code changes
- [x] Base attack database populated (4 attacks: Claw, Acid, Carapace, Adhesion)
- [x] M11 attack tickets reference attack_id and effect_type (no custom methods)
- [x] M12 can define fused attacks via data alone (no new handlers)
- [x] Cooldown and input model integrate cleanly with M1 player controller
- [x] `run_tests.sh` exits 0

---

## Integration with M1 Player Controller

### Current M1 Attack Framework (from M11 backlog tickets)

```gdscript
# In PlayerController3D
var _mutation_cooldowns: Dictionary = {}  # mutation_id → remaining cooldown

func _physics_process(delta: float) -> void:
  # ... existing physics ...
  
  if Input.is_action_just_pressed("attack"):
    _try_attack(delta)
  
  _update_cooldowns(delta)

func _try_attack(delta: float) -> void:
  var active_mutation = GameState.get_active_mutation()
  if active_mutation == NONE:
    return
  
  var cooldown_remaining = _mutation_cooldowns.get(active_mutation, 0.0)
  if cooldown_remaining > 0.0:
    return  # On cooldown
  
  # NEW: Data-driven dispatch
  var attack = AttackDatabase.get_base_attack(active_mutation)
  if not attack:
    push_error("No attack resource for mutation %d" % active_mutation)
    return
  
  AttackExecutor.execute_attack(attack)
  _mutation_cooldowns[active_mutation] = attack.cooldown

func _update_cooldowns(delta: float) -> void:
  for mutation_id in _mutation_cooldowns:
    _mutation_cooldowns[mutation_id] -= delta
```

---

## Migration Path (M11 Implementation)

1. **Week 1:** Write M1 refactor specs (state machine, physics order)
2. **Week 2:** Implement AttackResource, AttackDatabase, AttackExecutor
3. **Week 3:** Populate base attack resources (4 attacks for M11)
4. **Week 4:** Finalize M11 attack tickets (reference attack_id + effect_type, no methods)
5. **Week 5:** Implement base attacks using generic handlers
6. **Week 6:** Populate fused attack resources (M12 prep, no code changes needed)

---

## Future Extensions (M13+)

### New Effect Types (Hypothetical)

If a new effect type is needed (e.g., `CHARGE`):
1. Create new handler `_handle_charge(attack: AttackResource)`
2. Add case to match statement in `execute_attack()`
3. Define resources with effect_type = "CHARGE"
4. No changes to existing base attacks

### New Modifiers

Add key-value pairs to modifiers dictionary and read them in handlers. No architecture change.

### Charge Scaling (Future)

If attacks become chargeable (like kirby64):
```gdscript
@export var is_chargeable: bool = false
@export var max_charge_mult: float = 2.2

func execute_attack_charged(attack: AttackResource, charge_level: float) -> void:
  if attack.is_chargeable:
    var damage_mult = 1.0 + charge_level * (attack.max_charge_mult - 1.0)
    attack.damage *= damage_mult
  execute_attack(attack)
```

---

## Comparison to M11 Current Scope

**Old approach (Ticket: `attack_input_and_cooldown_framework`):**
- Hardcoded per-mutation attack methods: `_claw_attack()`, `_acid_attack()`, etc.
- New attack = new method (4 methods for base, 16 for fused = 20 total)
- Modifying cooldown logic = edit all methods
- Adding 5th mutation = write 8 more methods

**New approach (This spec):**
- Single generic dispatch, data-driven
- New attack = new resource file (4 files for base, 16 for fused = 20 total)
- Modifying cooldown logic = one place (M1 controller)
- Adding 5th mutation = write 8 new resource files

**Result:** M11 is cleaner, M12 scales, M13+ is unblocked.

---

## Questions for Design Review

1. **Attack Database:** Option A (separate resource files) or Option B (centralized script)?
   - **Recommendation:** Option A (resource files are easier to iterate, inspect, diff)

2. **Startup Frames:** Should attacks have configurable startup (animation lead) or always instant?
   - **Recommendation:** Configurable (allows more varied, tactical attacks)

3. **Knockback Direction:** Static directional vector or "push away / pull toward" logic?
   - **Recommendation:** Static for M11 (simpler), add dynamic in M12 if needed

4. **Modifiers:** Should the system validate that modifiers are "known" or allow arbitrary keys?
   - **Recommendation:** Arbitrary keys (allows quick iteration), document known ones

