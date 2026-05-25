# SPEC: AttackDatabase & PlayerController3D Integration

**Ticket:** M11-06 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/06_attack_database_integration.md`)  
**Spec ID:** ADB  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-25

---

## 1. Overview

AttackDatabase is a Godot `Node` autoload that serves as the canonical registry of all mutation attacks (base and fused). It maps mutation identity strings to `AttackResource` instances via `get_base_attack()` and `get_fused_attack()`. PlayerController3D is extended with `_try_attack()`, per-mutation cooldown tracking, and state-gated attack input to complete the player attack pipeline: input → policy check → cooldown check → AttackDatabase lookup → AttackExecutor dispatch.

**Scope:** AttackDatabase class, PlayerController3D wiring (attack input, cooldown, AttackExecutor child node, `get_facing_sign()`), `attack` InputMap registration in `project.godot`, autoload registration.

**Not in scope:** New player states (ATTACK_USE, CHARGE_UP), .tres resource file creation (database starts empty; test/runtime registration via API), fused attack resource data, actual enemy `take_damage()` integration.

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/06_attack_database_integration.md` | Acceptance criteria, pseudocode |
| AttackResource spec | `project_board/specs/attack_resource_spec.md` | Frozen data model (15 properties) |
| AttackExecutor spec | `project_board/specs/attack_executor_spec.md` | Dispatch contract, signals, active-guard |
| IAM spec | `project_board/specs/input_action_mapping_spec.md` | `ACTION_ATTACK`, permit matrix, default binding J (IAM-3.1) |
| PSM spec | `project_board/specs/player_state_machine_spec.md` | State enum, transition rules |
| Design spec | `project_board/specs/mutation_attack_system_design_spec.md` | Overall attack system design |
| AttackResource impl | `scripts/attacks/attack_resource.gd` | Frozen class (M11-04 COMPLETE) |
| AttackExecutor impl | `scripts/attacks/attack_executor.gd` | Frozen class (M11-05 COMPLETE) |
| PlayerInputActionPolicy | `scripts/player/player_input_action_policy.gd` | Permit matrix, ACTION_ATTACK defined |
| PlayerStateMachine | `scripts/player/player_state_machine.gd` | State enum, `get_state()` |
| PlayerController3D | `scripts/player/player_controller_3d.gd` | Physics frame order, existing wiring |
| MutationSlot | `scripts/mutation/mutation_slot.gd` | `_active_mutation_id: String`, `is_filled()`, `get_active_mutation_id()` |
| MutationSlotManager | `scripts/mutation/mutation_slot_manager.gd` | Dual-slot system, `any_filled()`, `get_slot()` |
| EnemyInfection3D | `scripts/enemy/enemy_infection_3d.gd` | `mutation_drop: String` export |
| InfectionAbsorbResolver | `scripts/infection/infection_absorb_resolver.gd` | `resolve_absorb()` passes mutation_id String |
| project.godot | `project.godot` | Autoload section, input section |
| Planning checkpoint | `project_board/checkpoints/M11-06/2026-05-25T-plan-run.md` | Design decisions from planner |

---

## 3. Discrepancy Resolutions

### ADB-DR-1: mutation_id type — int vs String

**Problem:** The ticket AC and pseudocode use `mutation_id: int` for `get_base_attack(mutation_id: int)`. However, the existing mutation slot system (`MutationSlot._active_mutation_id`, `EnemyInfection3D.mutation_drop`, `InfectionAbsorbResolver.resolve_absorb(mutation_id: String)`) uses **String** identifiers throughout.

**Evidence:**
- `scripts/mutation/mutation_slot.gd` line 5: `var _active_mutation_id: String = ""`
- `scripts/enemy/enemy_infection_3d.gd` line 14: `@export var mutation_drop: String = "infection_mutation_01"`
- `scripts/infection/infection_absorb_resolver.gd` line 23: `mutation_id: String = ""`
- `scripts/attacks/attack_resource.gd` line 4: `@export var attack_id: int = 0` (this is the attack's own numeric ID, distinct from mutation identity)

**Resolution:** Use **String** for mutation_id throughout AttackDatabase. `get_base_attack(mutation_id: String)` and `get_fused_attack(slot_a_id: String, slot_b_id: String)` accept strings. This preserves compatibility with the existing mutation slot system and avoids a breaking change. `AttackResource.attack_id: int` remains the attack's own unique numeric identifier, independent of mutation_id.

### ADB-DR-2: Fused attack key format — numeric pair vs string pair

**Problem:** Ticket says `"slot_a_slot_b"` (e.g., "1_2" for Claw+Acid). But since mutation_id is String (per ADB-DR-1), the key format must use string mutation IDs.

**Resolution:** Fused attack keys use **alphabetically sorted** mutation_id pairs joined by `"_"`. Example: `get_fused_attack("claw", "acid")` and `get_fused_attack("acid", "claw")` both produce canonical key `"acid_claw"`. This makes lookup **order-independent** — the caller does not need to know which slot is A vs B.

### ADB-DR-3: GameState.get_active_mutation() does not exist

**Problem:** Ticket pseudocode uses `GameState.get_active_mutation()`. No such global or method exists.

**Evidence:** `PlayerController3D._mutation_slot` is obtained from `InfectionInteractionHandler.get_mutation_slot_manager()`. `MutationSlotManager` has `get_slot(index) -> MutationSlot`, and each `MutationSlot` has `get_active_mutation_id() -> String`.

**Resolution:** `_try_attack()` reads mutation_id from `_mutation_slot` (the existing `MutationSlotManager` reference in PlayerController3D). For a base attack: use slot A's `get_active_mutation_id()`. For a fused attack: use both slots' mutation IDs. The spec freezes the selection logic in ADB-7.

### ADB-DR-4: AttackDatabase — .tres file scanning vs code registration

**Problem:** Ticket notes say "AttackDatabase can load from code (in _register_base_attacks) or .tres files (decide in implementation)."

**Resolution:** Spec freezes a **code-registration API** (`register_base_attack()`, `register_fused_attack()`) as the primary interface. An optional `_ready()` auto-scan of `res://attacks/base/` and `res://attacks/fused/` directories is an implementation detail — if the directories exist and contain `.tres` files, they are loaded; otherwise the database starts empty. Tests use the code-registration API exclusively. This decouples tests from filesystem layout.

### ADB-DR-5: AttackExecutor node ownership

**Problem:** AttackExecutor is a `Node` subclass. Its `_get_owner_position()` and `_get_facing_sign()` read from `get_parent()`. Where should it live?

**Resolution:** AttackExecutor is instantiated as a **child node** of PlayerController3D in `_ready()`. This gives it access to the player's `global_position` (via parent) and `get_facing_sign()` (via parent method, per ADB-8). This follows the same pattern as `MovementSimulation` and `PlayerStateMachine` initialization.

### ADB-DR-6: attack input default binding

**Problem:** IAM spec (IAM-3.1) designates **J** as the default binding. But `infect` already uses **F**. The ticket mentions "F key per IAM-3.1" which contradicts the actual IAM spec.

**Evidence:** `project_board/specs/input_action_mapping_spec.md` line 219: `| attack | **J** | — | **No** (deferred) |`. project.godot line 70: `infect` uses physical keycode 70 (F).

**Resolution:** Use **J** key (physical keycode 74) per the frozen IAM spec table. The ticket's "F key" reference is an error in the planning notes; F is already bound to `infect`.

### ADB-DR-7: Cooldown timer placement in PFO

**Problem:** Planning notes suggest "cooldown decrement in Step 2c or Step 8." Step 2c is documented as "reserved for future invulnerability / iframes timers" in the current code. Step 8 is `_post_slide_housekeeping`.

**Resolution:** Cooldown decrement goes in **Step 2** (`_tick_controller_timers()`), alongside the jump buffer timer. Step 2c's "reserved" comment allows cooldown timers (they are controller timers, not invulnerability). Attack attempt (`_try_attack()`) goes in **Step 8** (`_post_slide_housekeeping()`), after collision resolution and before FSM derivation. This means the state used for policy gating is from the **previous frame's** Step 9, which is correct per IAM-4.1.

---

## 4. Requirements

### ADB-1: AttackDatabase Class Declaration

**Description:** `AttackDatabase` is a `Node` subclass that serves as a global autoload registry of mutation attacks.

**File:** `scripts/attacks/attack_database.gd`  
**Class name:** `AttackDatabase`  
**Extends:** `Node`

**Constraints:**
- No `_physics_process()` override (event-driven via lookup methods, not per-frame).
- No scene-tree coupling beyond autoload registration.
- Must be registered in `project.godot` `[autoload]` section.

**Acceptance Criteria:**
- AC-1a: File exists at `scripts/attacks/attack_database.gd`.
- AC-1b: First non-comment line contains `class_name AttackDatabase`.
- AC-1c: Script extends `Node`.
- AC-1d: Instantiation via `AttackDatabase.new()` succeeds and returns a valid `Node` instance.
- AC-1e: `project.godot` `[autoload]` section contains `AttackDatabase="*res://scripts/attacks/attack_database.gd"`.

---

### ADB-2: Internal Storage

**Description:** AttackDatabase maintains two internal dictionaries for base and fused attack lookups.

**Data structures:**

```gdscript
var _base_attacks: Dictionary = {}    # String mutation_id → AttackResource
var _fused_attacks: Dictionary = {}   # String canonical_key → AttackResource
```

**Constraints:**
- Keys are always `String`.
- Values are always `AttackResource` (non-null after registration).
- Dictionaries are initialized empty.

**Acceptance Criteria:**
- AC-2a: `_base_attacks` is a `Dictionary`, initially empty.
- AC-2b: `_fused_attacks` is a `Dictionary`, initially empty.

---

### ADB-3: Base Attack Registration

**Description:** `register_base_attack(mutation_id: String, resource: AttackResource) -> void` stores a mutation→attack mapping.

**Signature:**

```gdscript
func register_base_attack(mutation_id: String, resource: AttackResource) -> void
```

**Behavior:**
1. If `mutation_id` is empty string `""`, call `push_warning("AttackDatabase: cannot register base attack with empty mutation_id")` and return.
2. If `resource` is `null`, call `push_warning("AttackDatabase: cannot register null resource for mutation_id '%s'" % mutation_id)` and return.
3. Store `_base_attacks[mutation_id] = resource`.
4. If `mutation_id` already existed, the new resource **overwrites** the previous one (last-write-wins, no error).

**Acceptance Criteria:**
- AC-3a: `register_base_attack("claw", resource)` stores the resource keyed by `"claw"`.
- AC-3b: Calling with the same mutation_id again overwrites the previous resource.
- AC-3c: Empty `mutation_id` is rejected with `push_warning`; no entry stored.
- AC-3d: Null `resource` is rejected with `push_warning`; no entry stored.
- AC-3e: After registration, `get_base_attack("claw")` returns the registered resource.

---

### ADB-4: Base Attack Lookup

**Description:** `get_base_attack(mutation_id: String) -> AttackResource` retrieves the attack resource for a given mutation identity.

**Signature:**

```gdscript
func get_base_attack(mutation_id: String) -> AttackResource
```

**Behavior:**
1. If `mutation_id` is in `_base_attacks`, return the stored `AttackResource`.
2. Otherwise, call `push_warning("AttackDatabase: no base attack found for mutation_id '%s'" % mutation_id)` and return `null`.

**Acceptance Criteria:**
- AC-4a: Returns the registered `AttackResource` for a known mutation_id.
- AC-4b: Returns `null` for an unregistered mutation_id.
- AC-4c: `push_warning` is called when mutation_id is not found.
- AC-4d: Empty string `""` mutation_id returns `null` with warning.
- AC-4e: Return type is `AttackResource` (or null).

---

### ADB-5: Fused Attack Registration

**Description:** `register_fused_attack(slot_a_id: String, slot_b_id: String, resource: AttackResource) -> void` stores a fused attack resource keyed by the canonical sorted pair.

**Signature:**

```gdscript
func register_fused_attack(slot_a_id: String, slot_b_id: String, resource: AttackResource) -> void
```

**Behavior:**
1. Compute canonical key: sort `[slot_a_id, slot_b_id]` alphabetically, join with `"_"`. Example: `("claw", "acid")` → `"acid_claw"`.
2. If either `slot_a_id` or `slot_b_id` is empty string, call `push_warning` and return.
3. If `slot_a_id == slot_b_id`, call `push_warning("AttackDatabase: fused attack requires two different mutations, got '%s'" % slot_a_id)` and return. Self-fusion is invalid.
4. If `resource` is `null`, call `push_warning` and return.
5. Store `_fused_attacks[canonical_key] = resource`.
6. Duplicate keys overwrite (last-write-wins).

**Canonical key function (pure helper):**

```gdscript
func _make_fused_key(id_a: String, id_b: String) -> String:
    var pair: Array = [id_a, id_b]
    pair.sort()
    return "%s_%s" % [pair[0], pair[1]]
```

**Acceptance Criteria:**
- AC-5a: `register_fused_attack("claw", "acid", resource)` stores under key `"acid_claw"`.
- AC-5b: `register_fused_attack("acid", "claw", resource)` stores under the same key `"acid_claw"` (order-independent).
- AC-5c: Empty slot ID is rejected with warning.
- AC-5d: Same mutation in both slots is rejected with warning (self-fusion).
- AC-5e: Null resource is rejected with warning.
- AC-5f: Duplicate registration overwrites previous entry.

---

### ADB-6: Fused Attack Lookup

**Description:** `get_fused_attack(slot_a_id: String, slot_b_id: String) -> AttackResource` retrieves the fused attack resource for a mutation pair.

**Signature:**

```gdscript
func get_fused_attack(slot_a_id: String, slot_b_id: String) -> AttackResource
```

**Behavior:**
1. Compute canonical key via `_make_fused_key(slot_a_id, slot_b_id)`.
2. If key exists in `_fused_attacks`, return the stored `AttackResource`.
3. Otherwise, call `push_warning("AttackDatabase: no fused attack found for combo '%s' + '%s'" % [slot_a_id, slot_b_id])` and return `null`.

**Acceptance Criteria:**
- AC-6a: Returns the registered `AttackResource` for a known fused pair.
- AC-6b: Lookup is order-independent (`get_fused_attack("a", "b")` == `get_fused_attack("b", "a")`).
- AC-6c: Returns `null` with warning for an unregistered pair.
- AC-6d: Returns `null` with warning when either slot ID is empty.

---

### ADB-7: PlayerController3D Attack Pipeline (_try_attack)

**Description:** `_try_attack()` implements the full attack attempt sequence within PlayerController3D: state gating → mutation check → cooldown check → database lookup → executor dispatch → cooldown set.

**Signature:**

```gdscript
func _try_attack() -> void
```

**Behavior (sequential):**

1. **State gating:** Read current state via `_player_state_machine.get_state()`. Check `PlayerInputActionPolicy.is_action_permitted(state, ACTION_ATTACK)`. If not permitted, return. (Permitted states per IAM-5.2: IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING. Denied states: ABSORB, MUTATE, HURT, DEAD.)
2. **Mutation active check:** If `_mutation_slot == null`, return (no mutation system available). Check if any mutation is active. If not, return.
3. **Mutation ID extraction:** Determine which attack to use:
   - If both slots are filled (slot A and slot B): attempt fused attack. Get `slot_a_id = slot_a.get_active_mutation_id()`, `slot_b_id = slot_b.get_active_mutation_id()`. Call `AttackDatabase.get_fused_attack(slot_a_id, slot_b_id)`. If result is null (no fused attack for this combo), **fall back to slot A's base attack**.
   - If only one slot is filled: use that slot's mutation_id for base attack lookup.
4. **Cooldown check:** Check `_mutation_cooldowns.get(lookup_mutation_id, 0.0) > 0.0`. If on cooldown, return. The `lookup_mutation_id` is the mutation_id used for the attack (slot A for base attacks, canonical fused key for fused attacks).
5. **Database lookup:** Call `AttackDatabase.get_base_attack(mutation_id)` or `AttackDatabase.get_fused_attack(slot_a_id, slot_b_id)` as determined in step 3. If result is null, return (warning already emitted by AttackDatabase).
6. **Execute:** Call `_attack_executor.execute_attack(attack_resource)`. If `_attack_executor.is_active()` is true (already executing), the executor's internal guard handles the no-op.
7. **Set cooldown:** Set `_mutation_cooldowns[cooldown_key] = attack_resource.cooldown`. The cooldown key is the mutation_id for base attacks, or the canonical fused key for fused attacks.

**Policy instantiation:** PlayerController3D must hold a `_input_policy: PlayerInputActionPolicy` reference (instantiated in `_ready()`).

**Acceptance Criteria:**
- AC-7a: Attack is blocked when `PlayerInputActionPolicy.is_action_permitted()` returns false (ABSORB, MUTATE, HURT, DEAD states).
- AC-7b: Attack is permitted in IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING states.
- AC-7c: Attack is blocked when no mutation is active (empty slots).
- AC-7d: Attack is blocked when cooldown is active (> 0.0).
- AC-7e: `AttackDatabase.get_base_attack()` is called with the correct mutation_id.
- AC-7f: `AttackExecutor.execute_attack()` is called with the returned resource.
- AC-7g: Cooldown is set to `attack_resource.cooldown` after successful execution.
- AC-7h: Null result from AttackDatabase does not crash; _try_attack returns silently.
- AC-7i: When both slots are filled and a fused attack exists, the fused attack is used.
- AC-7j: When both slots are filled but no fused attack exists, slot A's base attack is used as fallback.

---

### ADB-8: PlayerController3D — get_facing_sign()

**Description:** PlayerController3D must expose a `get_facing_sign() -> float` method so that AttackExecutor (as a child node) can determine attack direction via its existing `_get_facing_sign()` method.

**Signature:**

```gdscript
func get_facing_sign() -> float
```

**Behavior:**
1. Determine facing from horizontal velocity: if `velocity.x >= 0.0`, return `1.0` (facing right); if `velocity.x < 0.0`, return `-1.0` (facing left).
2. If velocity is zero, default to `1.0` (facing right).

**Rationale:** AttackExecutor line 158 checks `parent.has_method("get_facing_sign")`. Without this method, melee hitboxes and projectiles always fire to the right (default `1.0`).

**Acceptance Criteria:**
- AC-8a: `get_facing_sign()` returns `1.0` when `velocity.x >= 0.0`.
- AC-8b: `get_facing_sign()` returns `-1.0` when `velocity.x < 0.0`.
- AC-8c: AttackExecutor's `_get_facing_sign()` returns the correct value when parented to PlayerController3D.

---

### ADB-9: Per-Mutation Cooldown Tracking

**Description:** PlayerController3D tracks per-mutation cooldown timers to prevent attack spam.

**Data structure:**

```gdscript
var _mutation_cooldowns: Dictionary = {}  # String key → float seconds remaining
```

**Cooldown key semantics:**
- Base attacks: key = mutation_id string (e.g., `"claw"`).
- Fused attacks: key = canonical fused key (e.g., `"acid_claw"`).

**Tick behavior (Step 2 of PFO):**

In `_tick_controller_timers(delta, ...)`:
1. Iterate all keys in `_mutation_cooldowns`.
2. For each key, decrement by `delta`.
3. Clamp to `0.0` via `max(0.0, value - delta)`.
4. Optionally remove keys at `0.0` (implementation choice; functionally equivalent to keeping them).

**Set behavior (in `_try_attack()`):**

After successful `execute_attack()` call, set `_mutation_cooldowns[key] = attack_resource.cooldown`.

**Acceptance Criteria:**
- AC-9a: `_mutation_cooldowns` starts empty.
- AC-9b: After attack, cooldown is set to `attack_resource.cooldown`.
- AC-9c: Cooldown decrements by `delta` each physics tick.
- AC-9d: Cooldown is clamped to `0.0` (never negative).
- AC-9e: When cooldown reaches `0.0`, `_try_attack()` succeeds (attack available).
- AC-9f: When cooldown is > `0.0`, `_try_attack()` is blocked.
- AC-9g: Different mutations have independent cooldowns (attacking with "claw" does not affect "acid" cooldown).

---

### ADB-10: Attack Input in PFO Step 0

**Description:** `_read_player_input()` is extended to read the `attack` input action.

**Addition to `_read_player_input()` return dictionary:**

```gdscript
"attack_just_pressed": Input.is_action_just_pressed("attack")
```

**Constraints:**
- Follows the same `is_action_just_pressed()` pattern as existing inputs (jump, detach, etc.).
- No debounce or edge-tracking needed (unlike jump, attack does not use `is_action_pressed` or `_pressed_last_frame` tracking).
- When `_enemy_movement_root_remaining > 0.0` (enemy movement root active), attack input is **not suppressed** — attack input is independent of movement root (player can attack while rooted).

**PFO placement:** Step 0, inside `_read_player_input()`.

**Acceptance Criteria:**
- AC-10a: `_read_player_input()` returns `"attack_just_pressed"` key.
- AC-10b: Value is `true` when `Input.is_action_just_pressed("attack")` is true.
- AC-10c: Value is `false` otherwise.
- AC-10d: Attack input is NOT suppressed by enemy movement root.

---

### ADB-11: Attack Attempt in PFO Step 8

**Description:** `_post_slide_housekeeping()` is extended to check attack input and call `_try_attack()`.

**Addition to `_post_slide_housekeeping()`:**

After existing logic (chunk processing, acid DoTs, movement root decrement), add:

```gdscript
if input["attack_just_pressed"]:
    _try_attack()
```

**PFO placement:** Step 8 (`_post_slide_housekeeping()`), at the end of the method.

**Constraints:**
- `_try_attack()` uses `_player_state_machine.get_state()` which reflects the **previous frame's** Step 9 derivation. This is correct per IAM-4.1.
- Step 9 (`_sync_player_state_machine()`) runs after Step 8, so the state used for gating is stable.

**Acceptance Criteria:**
- AC-11a: `_try_attack()` is called when `input["attack_just_pressed"]` is true.
- AC-11b: `_try_attack()` is NOT called when `input["attack_just_pressed"]` is false.
- AC-11c: Attack gating uses the previous frame's FSM state (from Step 9 of the prior tick).

---

### ADB-12: AttackExecutor Child Node Wiring

**Description:** PlayerController3D instantiates an `AttackExecutor` as a child node during `_ready()`.

**Wiring in `_ready()`:**

```gdscript
var _attack_executor: AttackExecutor

# In _ready():
_attack_executor = AttackExecutor.new()
add_child(_attack_executor)
```

**Constraints:**
- `_attack_executor` is a private member variable on PlayerController3D.
- `add_child()` must be called after the PlayerController3D is in the scene tree (i.e., inside `_ready()`).
- AttackExecutor's `_get_owner_position()` reads `get_parent().global_position` → returns PlayerController3D's position.
- AttackExecutor's `_get_facing_sign()` calls `get_parent().get_facing_sign()` → uses ADB-8.

**Acceptance Criteria:**
- AC-12a: `_attack_executor` is a valid `AttackExecutor` instance after `_ready()`.
- AC-12b: `_attack_executor` is a child of PlayerController3D in the scene tree.
- AC-12c: `_attack_executor._get_owner_position()` returns PlayerController3D's `global_position`.
- AC-12d: `_attack_executor._get_facing_sign()` returns PlayerController3D's `get_facing_sign()` value.

---

### ADB-13: InputMap Registration — attack Action

**Description:** Register the `attack` action in `project.godot` `[input]` section with default binding J.

**project.godot entry:**

```ini
attack={
"deadzone": 0.5,
"events": [Object(InputEventKey,...,"physical_keycode":74,...)]
}
```

Physical keycode 74 = J key.

**Constraints:**
- Must not conflict with existing bindings (J is unused; F = infect, G = fuse).
- Follows the same InputEventKey format as existing actions.
- `deadzone: 0.5` matches existing actions.

**Acceptance Criteria:**
- AC-13a: `project.godot` `[input]` section contains an `attack` action entry.
- AC-13b: Default binding is J key (physical keycode 74).
- AC-13c: `InputMap.has_action("attack")` returns true at runtime.
- AC-13d: Pressing J triggers `Input.is_action_just_pressed("attack")`.

---

### ADB-14: PlayerInputActionPolicy Integration

**Description:** `_try_attack()` uses `PlayerInputActionPolicy.is_action_permitted()` for state gating, ensuring attack input is only processed in valid states.

**Existing policy matrix (from `player_input_action_policy.gd`):**

| State | ACTION_ATTACK permitted |
|-------|------------------------|
| IDLE | true |
| WALK | true |
| JUMP | true |
| FALL | true |
| FLOAT | true |
| WALL_CLING | true |
| ABSORB | false (not in row) |
| MUTATE | false (not in row) |
| HURT | false (not in row) |
| DEAD | false (not in row) |

**Integration:**
- PlayerController3D holds a `_input_policy: PlayerInputActionPolicy` instance (created in `_ready()`).
- `_try_attack()` calls `_input_policy.is_action_permitted(_player_state_machine.get_state(), PlayerInputActionPolicy.ACTION_ATTACK)`.

**Acceptance Criteria:**
- AC-14a: `_input_policy` is instantiated in `_ready()`.
- AC-14b: `_try_attack()` calls `is_action_permitted()` with the current FSM state and `ACTION_ATTACK`.
- AC-14c: Attack is blocked in ABSORB, MUTATE, HURT, DEAD.
- AC-14d: Attack is permitted in IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING.

---

### ADB-15: Autoload Registration

**Description:** AttackDatabase is registered as a Godot autoload in `project.godot`.

**Entry in `[autoload]` section:**

```ini
AttackDatabase="*res://scripts/attacks/attack_database.gd"
```

**Constraints:**
- The `*` prefix enables the autoload.
- Must be accessible globally via `AttackDatabase` singleton.
- Position in the autoload list: after existing autoloads (AudioManager, GameManager, InputHintsConfig, Logging).

**Acceptance Criteria:**
- AC-15a: `project.godot` contains the autoload entry.
- AC-15b: `AttackDatabase` is accessible as a global singleton at runtime.
- AC-15c: `AttackDatabase` is a Node instance (not null) during gameplay.

---

## 5. Frozen API Surface

### AttackDatabase public interface

```gdscript
class_name AttackDatabase
extends Node

# --- Registration ---
func register_base_attack(mutation_id: String, resource: AttackResource) -> void
func register_fused_attack(slot_a_id: String, slot_b_id: String, resource: AttackResource) -> void

# --- Lookup ---
func get_base_attack(mutation_id: String) -> AttackResource
func get_fused_attack(slot_a_id: String, slot_b_id: String) -> AttackResource
```

### AttackDatabase internal methods

```gdscript
func _make_fused_key(id_a: String, id_b: String) -> String
```

### PlayerController3D additions

```gdscript
# --- New member variables ---
var _attack_executor: AttackExecutor
var _mutation_cooldowns: Dictionary = {}
var _input_policy: PlayerInputActionPolicy

# --- New methods ---
func _try_attack() -> void
func get_facing_sign() -> float

# --- Modified methods (additions only, no removals) ---
func _ready() -> void                  # Add: AttackExecutor child, PolicyInputActionPolicy init
func _read_player_input() -> Dictionary # Add: "attack_just_pressed" key
func _tick_controller_timers(delta, ...) -> void  # Add: cooldown decrement loop
func _post_slide_housekeeping(...) -> void         # Add: attack input check + _try_attack()
```

---

## 6. Deferred Boundary

The following are **explicitly out of scope** for M11-06:

| Item | Owner | Notes |
|------|-------|-------|
| New player states (ATTACK_USE, CHARGE_UP) | Future M11 attack tickets | M11-06 does not add states to PlayerStateMachine |
| .tres resource file creation | Implementation detail | Database starts empty; register via API |
| Fused attack resource data | M12 | AttackDatabase supports fused lookup but no fused resources are registered in M11 |
| `EnemyBase.take_damage()` integration | Future ticket | AttackExecutor already handles via `has_method()` guard |
| VFX/SFX for attacks | Future milestone | AttackExecutor emits signals only |
| Attack animation states | Future ticket | No animation integration in M11-06 |
| `PlayerInputActionPolicy.resolve_consumed_actions()` integration | Future ticket | `_try_attack()` uses `is_action_permitted()` directly, not the full consumption pipeline |
| Directory auto-scan (`res://attacks/base/`, `res://attacks/fused/`) | Implementation option | Spec freezes the code-registration API; auto-scan is optional |

---

## 7. Test Strategy

### Test scope

Unit tests with mock/stub objects. No actual Godot physics, no real scene tree for database tests. Controller integration tests may use minimal scene tree setup for AttackExecutor child node.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_attack_database.gd` | AttackDatabase registration, lookup, edge cases |
| `tests/scripts/attacks/test_attack_database_controller_integration.gd` | PlayerController3D attack pipeline: _try_attack, cooldown, state gating |

### Test categories

| Category | What to test | ADB Requirement |
|----------|-------------|-----------------|
| Class identity | `AttackDatabase.new()`, `is_instance_of(Node)` | ADB-1 |
| Base registration | register + get round-trip | ADB-3, ADB-4 |
| Base overwrite | duplicate mutation_id overwrites | ADB-3 |
| Base missing | unknown mutation_id returns null + warning | ADB-4 |
| Fused registration | register + get round-trip, order-independent | ADB-5, ADB-6 |
| Fused key symmetry | `("a", "b")` == `("b", "a")` | ADB-5, ADB-6 |
| Fused self-fusion | same ID in both slots rejected | ADB-5 |
| Fused missing | unknown combo returns null + warning | ADB-6 |
| Empty/null guards | empty mutation_id, null resource | ADB-3, ADB-4, ADB-5 |
| _try_attack: state permits | attack succeeds in IDLE/WALK/JUMP/FALL/FLOAT/WALL_CLING | ADB-7, ADB-14 |
| _try_attack: state denies | attack blocked in ABSORB/MUTATE/HURT/DEAD | ADB-7, ADB-14 |
| _try_attack: no mutation | attack blocked when slots empty | ADB-7 |
| _try_attack: cooldown blocks | attack blocked when cooldown > 0 | ADB-7, ADB-9 |
| _try_attack: cooldown expires | attack succeeds when cooldown reaches 0 | ADB-9 |
| _try_attack: correct lookup | `get_base_attack` called with mutation_id from slot | ADB-7 |
| _try_attack: executor called | `execute_attack` called with resource | ADB-7 |
| _try_attack: cooldown set | cooldown set to `resource.cooldown` after execution | ADB-7, ADB-9 |
| _try_attack: fused attack | two-slot → fused lookup → executor | ADB-7 |
| _try_attack: fused fallback | two-slot, no fused resource → base attack from slot A | ADB-7 |
| Cooldown independent | different mutations have independent cooldowns | ADB-9 |
| Cooldown decrement | cooldown decreases by delta each tick | ADB-9 |
| Input read | `_read_player_input()` includes `attack_just_pressed` | ADB-10 |
| Facing sign | `get_facing_sign()` returns correct sign | ADB-8 |
| Executor wiring | AttackExecutor is child, reads parent position/facing | ADB-12 |

### Mock contracts

**Mock MutationSlotManager (for _try_attack tests):**

```gdscript
# Stub that simulates MutationSlotManager for controller tests
var _slot_a_id: String = ""
var _slot_b_id: String = ""

func any_filled() -> bool:
    return _slot_a_id != "" or _slot_b_id != ""

func get_slot(index: int) -> RefCounted:
    # Return a mock MutationSlot
    ...
```

**Mock AttackDatabase (for controller tests):**

Tests that verify `_try_attack()` behavior can either:
1. Use a real `AttackDatabase` instance with pre-registered resources, or
2. Mock the autoload reference.

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | ADB Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | `register_base_attack("", resource)` | Warning; no entry stored | ADB-3 | Empty mutation_id is invalid |
| EC-2 | `register_base_attack("claw", null)` | Warning; no entry stored | ADB-3 | Null resource is invalid |
| EC-3 | `get_base_attack("unknown")` | Returns null; warning emitted | ADB-4 | Missing lookup is graceful |
| EC-4 | `get_base_attack("")` | Returns null; warning emitted | ADB-4 | Empty string lookup |
| EC-5 | Duplicate `register_base_attack("claw", r1)` then `register_base_attack("claw", r2)` | r2 overwrites r1; `get_base_attack("claw")` returns r2 | ADB-3 | Last-write-wins |
| EC-6 | `register_fused_attack("claw", "claw", resource)` | Warning; no entry stored (self-fusion) | ADB-5 | Self-fusion is semantically invalid |
| EC-7 | `get_fused_attack("claw", "acid")` vs `get_fused_attack("acid", "claw")` | Both return same resource | ADB-6 | Order-independent via canonical key |
| EC-8 | `get_fused_attack("unknown_a", "unknown_b")` | Returns null; warning | ADB-6 | Missing fused combo |
| EC-9 | `_try_attack()` when `_mutation_slot == null` | Returns immediately; no crash | ADB-7 | Defensive null check |
| EC-10 | `_try_attack()` when AttackDatabase returns null | Returns silently; no crash | ADB-7 | Database warning handles logging |
| EC-11 | `_try_attack()` when AttackExecutor `_is_active == true` | Executor's internal guard returns; no double attack | ADB-7 | AttackExecutor has its own active-guard |
| EC-12 | Cooldown with `attack_resource.cooldown == 0.0` | Cooldown set to 0.0; next frame attack is immediately available | ADB-9 | Zero cooldown = no wait |
| EC-13 | Cooldown with `attack_resource.cooldown < 0.0` | Cooldown set to negative; immediately clamped to 0.0 on next tick | ADB-9 | Defensive clamping |
| EC-14 | Rapid attack input (every frame while cooldown active) | All blocked until cooldown expires | ADB-9 | Cooldown properly gates |
| EC-15 | Attack input during enemy movement root | Attack proceeds (not suppressed) | ADB-10 | Attack independent of movement root |
| EC-16 | `get_facing_sign()` when stationary (`velocity.x == 0`) | Returns `1.0` (default right) | ADB-8 | Consistent default |
| EC-17 | Two slots filled, fused attack exists | Fused attack used | ADB-7 | Fusion takes priority |
| EC-18 | Two slots filled, no fused attack registered | Falls back to slot A base attack | ADB-7 | Graceful degradation |
| EC-19 | One slot filled (A only), one empty | Base attack from slot A | ADB-7 | Single mutation |
| EC-20 | Slot B filled, slot A empty | Base attack from slot B | ADB-7 | Either slot triggers base |
| EC-21 | `_try_attack()` in DEAD state | Blocked by policy matrix | ADB-14 | DEAD row has no ACTION_ATTACK |
| EC-22 | `_try_attack()` during ABSORB | Blocked by policy | ADB-14 | ABSORB only permits MENU |
| EC-23 | Cooldown key collision: base key "acid_claw" vs fused key "acid_claw" | Theoretically possible if a mutation_id contains underscore. Spec assumes mutation IDs do not contain underscores. | ADB-9 | Naming convention constraint |
| EC-24 | Multiple independent cooldowns decrement simultaneously | Each decremented independently by delta | ADB-9 | Dictionary iteration |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| mutation_id naming convention not enforced | Low — underscore in mutation_id could collide with fused key separator | Document convention: mutation_ids should not contain underscore. No runtime enforcement in M11-06; defer to naming policy. |
| AttackDatabase autoload load order | Low — autoload initialized before _ready() of scene nodes | Godot autoloads initialize in declaration order. AttackDatabase is after existing autoloads; no dependency on them. |
| `_mutation_slot` may be null if InfectionInteractionHandler is missing | Medium — `_try_attack()` silently returns | Already handled: null check at step 2 of `_try_attack()`. Matches existing `_is_mutation_active()` pattern. |
| project.godot editing by implementation agent | Low — must preserve existing entries | Implementation agent must append, not replace, existing autoload and input entries. |
| AttackExecutor re-entrancy during await | Low — `_is_active` guard prevents overlapping | Already spec'd in AEX-2. `_try_attack()` does not need to check `is_active()` separately; the executor handles it internally. |
| `get_facing_sign()` zero-velocity default | Low — player stationary facing right is reasonable | Consistent with `_get_facing_sign()` default in `AttackExecutor` (returns 1.0 when parent lacks method). |

---

## 10. Clarifying Questions

All ambiguities resolved via discrepancy resolutions:

| Question | Resolution | Confidence |
|----------|------------|------------|
| mutation_id type: int or String? | String, matching existing slot system (ADB-DR-1) | High |
| Fused key format? | Alphabetically sorted, underscore-joined string pair (ADB-DR-2) | High |
| How to get active mutation? | Via existing `_mutation_slot` (MutationSlotManager) reference in PlayerController3D (ADB-DR-3) | High |
| .tres scanning vs code registration? | Code-registration API is primary; .tres scanning is optional implementation detail (ADB-DR-4) | High |
| AttackExecutor node ownership? | Child of PlayerController3D (ADB-DR-5) | High |
| attack key binding? | J key (physical keycode 74) per IAM spec (ADB-DR-6) | High |
| Cooldown PFO placement? | Decrement in Step 2, attempt in Step 8 (ADB-DR-7) | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| `AttackDatabase` autoload created | ADB-1, ADB-15 | Class identity |
| Loads attack resources from directories | ADB-3, ADB-5 (registration API; auto-scan deferred) | Base/fused registration |
| `get_base_attack(mutation_id) → AttackResource` | ADB-4 | Base lookup |
| `get_fused_attack(slot_a, slot_b) → AttackResource` | ADB-6 | Fused lookup |
| Graceful fallback (warning, return null) | ADB-4 (AC-4b/c), ADB-6 (AC-6c/d) | Missing lookup |
| `_try_attack()` checks state machine | ADB-7 (step 1), ADB-14 | State gating |
| `_try_attack()` checks active mutation | ADB-7 (step 2) | No mutation |
| `_try_attack()` checks cooldown | ADB-7 (step 4), ADB-9 | Cooldown blocks/expires |
| Calls `AttackDatabase.get_base_attack(mutation_id)` | ADB-7 (step 5) | Correct lookup |
| Calls `AttackExecutor.execute_attack(resource)` | ADB-7 (step 6) | Executor called |
| Sets `_mutation_cooldowns[id] = cooldown` | ADB-7 (step 7), ADB-9 | Cooldown set |
| Cooldown decrement in `_physics_process` | ADB-9 (tick behavior) | Cooldown decrement |
| Attack input in permitted states | ADB-7, ADB-14 | State permits/denies |
| Tests: resource loads correctly | ADB-3, ADB-4 | Base registration |
| Tests: fused lookup works | ADB-5, ADB-6 | Fused registration |
| Tests: cooldown blocks then allows | ADB-9 | Cooldown lifecycle |
| Tests: state machine blocks | ADB-7, ADB-14 | State gating |
| `run_tests.sh` exits 0 | (integration) | Full suite run |
