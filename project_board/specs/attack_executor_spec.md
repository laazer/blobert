# SPEC: AttackExecutor Dispatch & Handlers

**Ticket:** M11-05 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/05_attack_executor_handlers.md`)  
**Spec ID:** AEX  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-25

---

## 1. Overview

AttackExecutor is a Godot `Node` that serves as the single dispatch hub for all player-side mutation attacks. It receives an `AttackResource`, reads `effect_type`, and routes to the appropriate handler method. M11-05 implements two handlers: `MELEE_SWIPE` and `PROJECTILE_SPIT`. Future handlers (SLAM_AOE, LUNGE, CHARGE) can be added via new `match` arms without modifying existing code.

AttackExecutor is a **behavior node**, not a data container. It has `_ready()`, signals, and runtime methods. It does NOT own cooldown tracking (that belongs to the caller — likely PlayerController3D in a later ticket). It does NOT modify `EnemyBase` — all enemy interactions use duck-typed `has_method()` calls.

**File location:** `scripts/attacks/attack_executor.gd`  
**Class name:** `AttackExecutor`  
**Extends:** `Node`

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/05_attack_executor_handlers.md` | Acceptance criteria, handler pseudocode |
| AttackResource spec | `project_board/specs/attack_resource_spec.md` | Frozen data model (15 properties, modifiers contract) |
| Design spec | `project_board/specs/mutation_attack_system_design_spec.md` | Dispatch pattern, handler pseudocode, activation flow |
| AttackResource impl | `scripts/attacks/attack_resource.gd` | Frozen class (M11-04 COMPLETE) |
| EnemyAttackHitbox | `scripts/enemies/enemy_attack_hitbox.gd` | Existing hitbox/knockback pattern (Area3D, `_compute_knockback()`) |
| AcidProjectile3D | `scripts/combat/acid_projectile_3d.gd` | Existing projectile pattern (Area3D, `setup()`, `_physics_process()`, `_on_body_entered()`) |
| AcidSpitterRangedAttack | `scripts/enemy/acid_spitter_ranged_attack.gd` | Enemy-side projectile spawning pattern |
| EnemyBase | `scripts/enemies/enemy_base.gd` | Enemy state (no `take_damage()` exists) |
| PlayerController3D | `scripts/player/player_controller_3d.gd` | Player `take_damage(amount, knockback)` API (reference, not modified) |
| Planning checkpoint | `project_board/checkpoints/M11-05/2026-05-25T-plan-run.md` | Design decisions, risk register |

---

## 3. Discrepancy Resolutions

### AEX-DR-1: Enemy `take_damage()` does not exist

**Problem:** The ticket pseudocode calls `enemy.take_damage(attack.damage)`, but `EnemyBase` has no `take_damage()` method. Only a state enum (`NORMAL`, `WEAKENED`, `INFECTED`) and `set_base_state()` exist.

**Evidence:** `scripts/enemies/enemy_base.gd` — no damage intake method. `PlayerController3D.take_damage(amount, knockback)` exists but is player-facing. The ticket notes section says "Assume enemy API: `take_damage(damage, knockback_vector)`".

**Resolution:** AttackExecutor calls `target.take_damage(damage, knockback_vector)` using a duck-typed `has_method("take_damage")` guard. Tests mock the enemy with a stub that implements `take_damage`. The actual `EnemyBase.take_damage()` integration is **deferred** — not part of M11-05 scope.

### AEX-DR-2: Modifier application methods do not exist on enemies

**Problem:** The ticket notes reference `apply_poison(duration, dps)`, `apply_acid(duration, dps)`, `apply_slowness(multiplier, duration)`. None of these exist on `EnemyBase`.

**Evidence:** `scripts/enemies/enemy_base.gd` — only `set_base_state()`, `get_base_state()`, `get_esm()`.

**Resolution:** AttackExecutor uses `has_method()` guard on each modifier method call. If the target does not have the method, the modifier is silently skipped. Tests use mock enemies that implement the expected methods. This follows the existing codebase pattern: `AdhesionBugLungeAttack` (line 114) uses `player.has_method("apply_enemy_movement_root")` before calling.

### AEX-DR-3: Startup frames — timer-based, not literal frame counting

**Problem:** `startup_frames: int` could mean literal `_physics_process` ticks or a time conversion. Frame-dependent waits are non-deterministic across different physics rates.

**Evidence:** Design spec uses `await get_tree().create_timer(attack.startup_frames / 60.0).timeout`. This assumes 60 FPS.

**Resolution:** Convert startup_frames to seconds via `startup_frames / 60.0` and use `get_tree().create_timer()`. This is consistent with the design spec and is testable. For `startup_frames == 0`, skip the timer entirely (no await, synchronous execution of the hit query).

### AEX-DR-4: Player-side projectile class

**Problem:** `AcidProjectile3D` is enemy-facing (damages player). No player-facing projectile exists. The ticket says "Projectile script already exists (from M8); reuse it" but M8's projectile targets the player, not enemies.

**Evidence:** `scripts/combat/acid_projectile_3d.gd` — `_on_body_entered` checks `body.is_in_group("player")`.

**Resolution:** A new `PlayerProjectile3D` class will be created at `scripts/attacks/player_projectile_3d.gd` following the same `Area3D` pattern but targeting entities with `has_method("take_damage")` (not the player). This is the executor's responsibility to instantiate. The projectile scene is deferred to the implementation agent (may use a minimal `.tscn` or pure code instantiation).

### AEX-DR-5: VFX/SFX — signal-based stubs

**Problem:** Ticket mentions `spawn_vfx()` and `play_sfx()`. No VFX/SFX system exists in the codebase for player attacks.

**Evidence:** No `VFXManager`, `AudioManager`, or equivalent autoload/node. Enemy-side attacks have no VFX calls either.

**Resolution:** AttackExecutor emits signals for VFX/SFX events. External systems (future milestones) connect to these signals. No actual particle or audio implementation in M11-05. Tests verify signal emission with correct parameters.

### AEX-DR-6: Knockback direction as top-level property

**Problem:** The design spec places `knockback_direction` inside `modifiers` dict. The frozen AttackResource spec (ATK-04) has it as a top-level export.

**Resolution:** Use the frozen AttackResource top-level `knockback_direction: String` property (ATK-DR-2 resolved this). The executor reads `attack_resource.knockback_direction` directly, not from `modifiers`.

---

## 4. Requirements

### AEX-1: Class Declaration

**Description:** `AttackExecutor` is a `Node` subclass (not `Resource`, not `CharacterBody3D`). It exists as a runtime behavior node that can be added as a child of any Node3D (typically PlayerController3D).

**File:** `scripts/attacks/attack_executor.gd`  
**Class name:** `AttackExecutor`  
**Extends:** `Node`

**Constraints:**
- No `_physics_process()` override (AttackExecutor is event-driven via `execute_attack()`, not per-frame).
- No state machine — single `_is_active: bool` flag prevents overlapping executions.

**Acceptance Criteria:**
- AC-1a: File exists at `scripts/attacks/attack_executor.gd`.
- AC-1b: First non-comment line contains `class_name AttackExecutor`.
- AC-1c: Script extends `Node`.
- AC-1d: Instantiation via `AttackExecutor.new()` succeeds.
- AC-1e: `is_instance_of(instance, Node)` returns `true`.
- AC-1f: `is_instance_of(instance, Resource)` returns `false`.

---

### AEX-2: Dispatch Function

**Description:** The primary entry point is `execute_attack(resource: AttackResource) -> void`. It reads `resource.effect_type` and dispatches to the corresponding handler via a `match` statement.

**Signature:**

```gdscript
func execute_attack(resource: AttackResource) -> void
```

**Behavior:**
1. If `_is_active == true`, return immediately (no overlapping attacks).
2. Set `_is_active = true`.
3. Emit `attack_started` signal with `resource`.
4. `match resource.effect_type`:
   - `"MELEE_SWIPE"` → call `_handle_melee_swipe(resource)`
   - `"PROJECTILE_SPIT"` → call `_handle_projectile_spit(resource)`
   - `_` (wildcard) → call `_handle_unknown(resource)`
5. After handler completes (or on unknown), set `_is_active = false`.

**Active-guard contract:** While `_is_active` is true, subsequent calls to `execute_attack()` are no-ops. The caller is responsible for cooldown timing. The executor only prevents overlapping handler execution.

**Acceptance Criteria:**
- AC-2a: `execute_attack(resource)` is callable with a valid `AttackResource`.
- AC-2b: `MELEE_SWIPE` effect_type routes to `_handle_melee_swipe`.
- AC-2c: `PROJECTILE_SPIT` effect_type routes to `_handle_projectile_spit`.
- AC-2d: Unknown effect_type routes to `_handle_unknown` (no crash).
- AC-2e: Calling `execute_attack()` while `_is_active == true` is a no-op.
- AC-2f: `attack_started` signal is emitted exactly once per successful dispatch.
- AC-2g: `_is_active` is `false` after handler completes.

---

### AEX-3: MELEE_SWIPE Handler Contract

**Description:** `_handle_melee_swipe(resource: AttackResource)` implements close-range area-of-effect melee.

**Behavior (sequential):**

1. **Startup delay:** If `resource.startup_frames > 0`, wait `resource.startup_frames / 60.0` seconds via `get_tree().create_timer()`. If `startup_frames == 0`, proceed immediately.
2. **Area query:** Query all bodies in a sphere (or AABB approximation) centered at `owner_position + facing_direction * resource.attack_range * 0.5` with radius `resource.attack_range * 0.5`. "Bodies" means any `Node3D` in the `"enemies"` group OR any `Node3D` with `has_method("take_damage")`.
3. **Per-enemy processing:** For each enemy found:
   a. Call `_apply_damage(enemy, resource.damage, knockback_vector)` where `knockback_vector` is computed per AEX-5.
   b. Call `_apply_modifiers(enemy, resource.modifiers)` per AEX-6.
   c. Emit `attack_hit` signal with `(enemy, resource)`.
4. **VFX signal:** Emit `melee_vfx_requested(hit_position, resource.color, resource.vfx_scale)` regardless of hit count (animation plays even on whiff).

**Owner position / facing direction:** The executor reads these from its parent node. The parent must expose:
- `global_position: Vector3` (standard Node3D property)
- `get_facing_sign() -> float` (returns `1.0` or `-1.0`)

If the parent does not have `get_facing_sign()`, default to `1.0` (facing right).

**Acceptance Criteria:**
- AC-3a: Startup delay of `startup_frames / 60.0` seconds before hitbox query when `startup_frames > 0`.
- AC-3b: Immediate hitbox query when `startup_frames == 0`.
- AC-3c: Enemies within `attack_range` of the hitbox center are hit.
- AC-3d: Enemies outside `attack_range` are not hit.
- AC-3e: `take_damage` is called on each hit enemy with correct damage and knockback vector.
- AC-3f: Modifiers are applied to each hit enemy per AEX-6.
- AC-3g: `attack_hit` signal emitted once per enemy hit.
- AC-3h: `melee_vfx_requested` signal emitted once per melee execution (hit or miss).
- AC-3i: No crash if zero enemies are in range.

---

### AEX-4: PROJECTILE_SPIT Handler Contract

**Description:** `_handle_projectile_spit(resource: AttackResource)` creates a player-owned projectile and adds it to the scene tree.

**Behavior (sequential):**

1. **Startup delay:** Same logic as AEX-3 step 1.
2. **Create projectile:** Instantiate a `PlayerProjectile3D` node.
3. **Configure projectile:**
   - `projectile.damage = resource.damage`
   - `projectile.speed = resource.projectile_speed`
   - `projectile.lifetime = resource.projectile_lifetime`
   - `projectile.knockback_magnitude = resource.knockback_magnitude`
   - `projectile.knockback_direction = resource.knockback_direction`
   - `projectile.modifiers = resource.modifiers.duplicate(true)` (deep copy to prevent mutation)
   - `projectile.direction_x = facing_sign` (1.0 or -1.0)
4. **Position:** Set `projectile.global_position = owner_global_position`.
5. **Add to scene:** Call `get_parent().add_child(projectile)` (projectile added as sibling of executor's parent, same as the existing `AcidSpitterRangedAttack` pattern of adding to room-level parent).
6. **Signal:** Emit `projectile_fired(projectile, resource)`.

**PlayerProjectile3D contract (implementation-level detail, not spec'd here beyond interface):**
- Extends `Area3D`.
- Moves along X at `direction_x * speed` units/sec.
- On body contact with a target that has `take_damage()`: applies damage, knockback, and modifiers, then `queue_free()`.
- Auto-despawns after `lifetime` seconds.
- Collision is with enemy layer (not player layer).

**Acceptance Criteria:**
- AC-4a: A `PlayerProjectile3D` instance is created.
- AC-4b: Projectile `damage`, `speed`, `lifetime`, `knockback_magnitude`, `knockback_direction`, and `modifiers` are set from the resource.
- AC-4c: Projectile `direction_x` matches the executor parent's facing sign.
- AC-4d: Projectile is added to the scene tree as a child of the executor's grandparent (executor parent's parent).
- AC-4e: `projectile_fired` signal emitted with the projectile instance and resource.
- AC-4f: No crash if `resource.projectile_speed == 0.0` (projectile is created but stationary).
- AC-4g: Startup delay respected before projectile creation.

---

### AEX-5: Knockback Direction Calculation

**Description:** Knockback vector is computed from `AttackResource.knockback_direction` (String) and `AttackResource.knockback_magnitude` (float).

**Algorithm:**

```
Given:
  target_position: Vector3  (enemy position)
  owner_position: Vector3   (player/executor-parent position)
  magnitude: float          (attack_resource.knockback_magnitude)
  direction: String         (attack_resource.knockback_direction)

1. If magnitude == 0.0 OR direction == "none":
     return Vector3.ZERO

2. delta = target_position - owner_position
   delta.z = 0.0   # Constrain to 2.5D play plane

3. If delta.length_squared() < 1e-8:
     delta = Vector3(1.0, 0.0, 0.0)  # Degenerate: default to right
   else:
     delta = delta.normalized()

4. match direction:
     "away":   return delta * magnitude
     "toward": return -delta * magnitude
     _:        return Vector3.ZERO   # Unknown direction = no knockback
```

**Constraints:**
- Z component is always zeroed (2.5D play plane constraint, per `EnemyAttackHitbox._compute_knockback()` pattern).
- The `"toward"` case inverts the direction (pull enemy toward player).
- Unknown `knockback_direction` strings (e.g., `"diagonal"`) are treated as `"none"` — no knockback, no crash.

**Acceptance Criteria:**
- AC-5a: `"away"` pushes enemy away from player (delta direction * magnitude).
- AC-5b: `"toward"` pulls enemy toward player (negative delta * magnitude).
- AC-5c: `"none"` returns `Vector3.ZERO`.
- AC-5d: `knockback_magnitude == 0.0` returns `Vector3.ZERO` regardless of direction string.
- AC-5e: Degenerate case (target == owner position) defaults direction to `(1, 0, 0)`.
- AC-5f: Z component of result is always `0.0`.
- AC-5g: Unknown direction strings (e.g., `"diagonal"`) return `Vector3.ZERO`.

---

### AEX-6: Modifier Application

**Description:** `_apply_modifiers(target: Node3D, modifiers: Dictionary)` reads known modifier keys from the dictionary and calls corresponding methods on the target using `has_method()` guards.

**Known modifier handlers:**

| Modifier Flag Key | Guard | Method Call on Target | Arguments | Defaults |
|-------------------|-------|----------------------|-----------|----------|
| `"poison"` | `modifiers.get("poison", false) == true` | `target.apply_poison(duration, dps)` | `duration = modifiers.get("poison_duration", 2.0)`, `dps = modifiers.get("poison_dps", 0.3)` | 2.0s, 0.3 dps |
| `"acid_on_hit"` | `modifiers.get("acid_on_hit", false) == true` | `target.apply_acid(duration, dps)` | `duration = modifiers.get("acid_duration", 2.0)`, `dps = modifiers.get("acid_dps", 0.2)` | 2.0s, 0.2 dps |
| `"slow"` | `modifiers.get("slow", 0.0) > 0.0` | `target.apply_slowness(multiplier, duration)` | `multiplier = modifiers.get("slow", 1.0)`, `duration = modifiers.get("slow_duration", 1.5)` | 1.0×, 1.5s |

**Guard pattern (per modifier):**

```
if modifiers.get("poison", false):
    if target.has_method("apply_poison"):
        target.apply_poison(
            modifiers.get("poison_duration", 2.0),
            modifiers.get("poison_dps", 0.3)
        )
```

**Constraints:**
- Each modifier key is checked independently — multiple modifiers can fire on the same hit.
- `has_method()` guard prevents crashes when the target does not implement a modifier method.
- If a modifier flag is present but the target lacks the method, the modifier is silently skipped (no error, no warning).
- Empty modifiers dictionary (`{}`) is valid — no modifiers are applied.
- Unknown modifier keys are ignored.

**Acceptance Criteria:**
- AC-6a: Poison modifier calls `apply_poison(duration, dps)` when flag is `true` and target has the method.
- AC-6b: Acid modifier calls `apply_acid(duration, dps)` when flag is `true` and target has the method.
- AC-6c: Slow modifier calls `apply_slowness(multiplier, duration)` when value > 0.0 and target has the method.
- AC-6d: Missing modifier method on target does not crash (silently skipped via `has_method()` guard).
- AC-6e: Empty modifiers dictionary results in zero method calls.
- AC-6f: Multiple modifiers can fire on the same target in the same hit.
- AC-6g: Default values are used when duration/dps/multiplier keys are absent.
- AC-6h: Unknown modifier keys (e.g., `"weaken"`) are ignored without error.

---

### AEX-7: Signals for VFX/SFX

**Description:** AttackExecutor emits signals to decouple combat logic from visual/audio presentation. No actual VFX/SFX implementation in M11-05.

**Signal declarations:**

```gdscript
signal attack_started(resource: AttackResource)
signal attack_hit(target: Node3D, resource: AttackResource)
signal projectile_fired(projectile: Node3D, resource: AttackResource)
signal melee_vfx_requested(position: Vector3, color: Color, scale: float)
```

**Emission rules:**

| Signal | Emitted By | When | Arguments |
|--------|-----------|------|-----------|
| `attack_started` | `execute_attack()` | Before handler dispatch (after active-guard passes) | The `AttackResource` being executed |
| `attack_hit` | `_handle_melee_swipe()` | Once per enemy hit | `(target, resource)` |
| `projectile_fired` | `_handle_projectile_spit()` | After projectile added to scene | `(projectile, resource)` |
| `melee_vfx_requested` | `_handle_melee_swipe()` | After all enemies processed (even on miss) | `(hit_center_position, resource.color, resource.vfx_scale)` |

**Acceptance Criteria:**
- AC-7a: `attack_started` emitted once per `execute_attack()` call that passes the active-guard.
- AC-7b: `attack_hit` emitted once per enemy hit during melee (0 times on whiff).
- AC-7c: `projectile_fired` emitted once when a projectile is successfully created and added.
- AC-7d: `melee_vfx_requested` emitted once per melee execution (regardless of hit count).
- AC-7e: No signal is emitted on unknown effect_type (except the implicit `_handle_unknown` flow).
- AC-7f: Signal arguments match the declared types.

---

### AEX-8: Unknown effect_type Handling (Fail-Closed)

**Description:** When `resource.effect_type` does not match any known handler, the executor handles it gracefully.

**Behavior:**
1. Call `push_warning("AttackExecutor: unknown effect_type '%s'" % resource.effect_type)`.
2. Set `_is_active = false`.
3. Do **not** crash, do **not** emit `attack_started` (already emitted in step 3 of AEX-2), do **not** apply any damage or modifiers.

**Rationale:** `push_warning` (not `push_error`) because unknown effect_types are an extensibility concern, not a fatal error. New types may not have handlers yet during development.

**Acceptance Criteria:**
- AC-8a: Unknown effect_type does not crash (no unhandled exception).
- AC-8b: `push_warning` is called with a message containing the unrecognized effect_type string.
- AC-8c: `_is_active` is set back to `false` after unknown handling.
- AC-8d: No damage is applied, no projectile is created, no modifiers fire.
- AC-8e: Empty string `""` effect_type is treated as unknown.
- AC-8f: `attack_started` signal was already emitted before the match (per AEX-2 step 3) — this is intentional.

---

## 5. Frozen API Surface

### AttackExecutor public interface

```gdscript
class_name AttackExecutor
extends Node

# --- Signals ---
signal attack_started(resource: AttackResource)
signal attack_hit(target: Node3D, resource: AttackResource)
signal projectile_fired(projectile: Node3D, resource: AttackResource)
signal melee_vfx_requested(position: Vector3, color: Color, scale: float)

# --- Public methods ---
func execute_attack(resource: AttackResource) -> void
func is_active() -> bool
```

### AttackExecutor internal methods (handler signatures, not public API)

```gdscript
func _handle_melee_swipe(resource: AttackResource) -> void
func _handle_projectile_spit(resource: AttackResource) -> void
func _handle_unknown(resource: AttackResource) -> void
func _apply_damage(target: Node3D, damage: float, knockback: Vector3) -> void
func _apply_modifiers(target: Node3D, modifiers: Dictionary) -> void
func _calculate_knockback(target_pos: Vector3, owner_pos: Vector3, magnitude: float, direction: String) -> Vector3
func _get_facing_sign() -> float
func _get_owner_position() -> Vector3
func _query_enemies_in_range(center: Vector3, radius: float) -> Array
```

### PlayerProjectile3D interface (created by executor, implementation detail)

```gdscript
class_name PlayerProjectile3D
extends Area3D

var damage: float = 0.0
var speed: float = 0.0
var lifetime: float = 2.0
var knockback_magnitude: float = 0.0
var knockback_direction: String = "away"
var modifiers: Dictionary = {}
var direction_x: float = 1.0
```

---

## 6. Deferred Boundary

The following are **explicitly out of scope** for M11-05:

| Item | Owner | Notes |
|------|-------|-------|
| `EnemyBase.take_damage()` method | Future ticket | Tests mock this. Executor calls it via `has_method()` guard. |
| `EnemyBase.apply_poison/acid/slowness` | Future ticket | Tests mock these. Executor calls via `has_method()`. |
| Cooldown tracking at player level | Future ticket | Executor has no cooldown timer. Caller manages cooldowns. |
| Actual VFX particles / SFX audio | Future milestone | Executor emits signals only. |
| SLAM_AOE handler | Future ticket | `match` arm added when needed. |
| LUNGE handler | Future ticket | `match` arm added when needed. |
| CHARGE handler | M12+ | Reserved for charged attacks. |
| AttackDatabase / resource registry | Future ticket | How attacks are looked up by mutation_id. |
| PlayerProjectile3D scene (.tscn) | M11-05 implementation | Implementation agent creates the scene. Spec defines only the interface contract. |
| Player-level attack input wiring | M11-03/future | PlayerController3D integration with input → execute_attack(). |
| Collision layer/mask configuration | Implementation detail | Implementation agent sets appropriate layers. |

---

## 7. Test Strategy

### Test scope

Unit tests with mock enemies and mock scene tree. No actual Godot physics, no collision detection, no real projectile movement. Tests verify:
- Dispatch routing
- Handler call contracts (what methods are called on targets, with what arguments)
- Signal emission (timing and arguments)
- Knockback calculation (pure math)
- Modifier application (has_method guards, argument passing)
- Active-guard (no overlapping execution)
- Unknown effect_type handling

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_attack_executor.gd` | Primary behavioral tests |
| `tests/scripts/attacks/test_attack_executor_adversarial.gd` | Edge cases and adversarial deepening |

### Test categories

| Category | What to test | AEX Requirement |
|----------|-------------|-----------------|
| Class identity | `AttackExecutor.new()`, `is_instance_of(Node)`, not Resource | AEX-1 |
| Dispatch routing | MELEE_SWIPE → melee handler, PROJECTILE_SPIT → projectile handler | AEX-2 |
| Active guard | Second `execute_attack()` during active execution is no-op | AEX-2 |
| Melee: hit detection | Enemies in range are hit, enemies out of range are not | AEX-3 |
| Melee: startup delay | Timer created for startup_frames > 0; immediate for 0 | AEX-3 |
| Melee: damage + knockback | `take_damage` called with correct args per AEX-5 | AEX-3, AEX-5 |
| Melee: modifiers | Poison/acid/slow applied when flags set and target has methods | AEX-3, AEX-6 |
| Melee: VFX signal | `melee_vfx_requested` emitted with position, color, scale | AEX-7 |
| Projectile: creation | `PlayerProjectile3D` instantiated with correct properties | AEX-4 |
| Projectile: scene addition | Added to scene tree at correct position | AEX-4 |
| Projectile: signal | `projectile_fired` emitted | AEX-7 |
| Knockback: away | Vector points target away from owner | AEX-5 |
| Knockback: toward | Vector points target toward owner | AEX-5 |
| Knockback: none | Returns ZERO | AEX-5 |
| Knockback: zero magnitude | Returns ZERO | AEX-5 |
| Knockback: degenerate position | Same position defaults to (1,0,0) | AEX-5 |
| Modifier: has_method guard | No crash if target lacks method | AEX-6 |
| Modifier: empty dict | No calls | AEX-6 |
| Modifier: multiple | All applicable modifiers fire | AEX-6 |
| Unknown effect_type | push_warning, no crash, no damage | AEX-8 |
| Empty effect_type | Treated as unknown | AEX-8 |
| Signals | All four signals emitted with correct arguments | AEX-7 |

### Mock enemy contract (for tests)

Tests create a mock enemy node with configurable methods:

```gdscript
# Mock enemy for unit tests
extends Node3D

var damage_taken: Array = []
var poison_applied: Array = []
var acid_applied: Array = []
var slow_applied: Array = []

func take_damage(damage: float, knockback: Vector3) -> void:
    damage_taken.append({"damage": damage, "knockback": knockback})

func apply_poison(duration: float, dps: float) -> void:
    poison_applied.append({"duration": duration, "dps": dps})

func apply_acid(duration: float, dps: float) -> void:
    acid_applied.append({"duration": duration, "dps": dps})

func apply_slowness(multiplier: float, duration: float) -> void:
    slow_applied.append({"multiplier": multiplier, "duration": duration})
```

Tests that need to verify `has_method()` guard behavior create a **bare mock** (Node3D with no extra methods) and verify no crash occurs.

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | AEX Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | `damage = 0.0` | `take_damage(0.0, knockback)` called; no skip | AEX-3 | Zero-damage utility attacks are valid (modifiers-only). |
| EC-2 | `attack_range = 0.0` | Query with zero radius returns only enemies at exact position (or none) | AEX-3 | Degenerate case; probably no enemies hit. |
| EC-3 | `knockback_magnitude = -10.0` | Knockback vector is computed with negative magnitude (points opposite) | AEX-5 | Resource allows negative values (ATK spec EC-10). Executor applies as-is. |
| EC-4 | `startup_frames = 99999` | Timer of ~1666 seconds created; handler blocks during wait | AEX-3 | Valid per AttackResource spec (EC-13). Executor does not cap. |
| EC-5 | `startup_frames = 0` | No timer; hitbox query is immediate | AEX-3 | Common case for instant attacks. |
| EC-6 | `effect_type = ""` | Treated as unknown; push_warning, no damage | AEX-8 | Empty string is default on AttackResource (ATK-03). |
| EC-7 | `effect_type = "SLAM_AOE"` | Treated as unknown (no handler in M11-05) | AEX-8 | Handler not implemented yet. |
| EC-8 | `projectile_speed = 0.0` | Projectile created but stationary | AEX-4 | Valid per AttackResource spec (EC-12). |
| EC-9 | `modifiers = {}` (empty) | No modifier methods called; no crash | AEX-6 | Default AttackResource state. |
| EC-10 | Target has no `take_damage()` | `has_method()` returns false; damage silently skipped | AEX-3 | Duck-type guard pattern (AEX-DR-1). |
| EC-11 | Target has no `apply_poison()` but modifier flag set | Modifier silently skipped | AEX-6 | has_method guard (AEX-DR-2). |
| EC-12 | Multiple enemies in melee range | Each enemy processed; `attack_hit` emitted per enemy | AEX-3 | Standard area-of-effect behavior. |
| EC-13 | No enemies in melee range | No damage, no modifiers; `melee_vfx_requested` still emitted | AEX-3, AEX-7 | Animation plays even on whiff. |
| EC-14 | `execute_attack()` called while active | No-op; no second dispatch, no signal | AEX-2 | Active-guard prevents overlapping. |
| EC-15 | `resource` is null | Guard at top of `execute_attack()`: return immediately, no crash | AEX-2 | Defensive programming. |
| EC-16 | Executor not in scene tree | `get_tree()` returns null; startup delay cannot create timer; skip delay, proceed with handler | AEX-3 | Testability: many unit tests run without full scene tree. |
| EC-17 | Parent has no `get_facing_sign()` | Default to `1.0` (facing right) | AEX-3 | Defensive default. |
| EC-18 | Concurrent poison + acid + slow modifiers | All three methods called on the same target | AEX-6 | Modifiers are independent. |
| EC-19 | `knockback_direction = "diagonal"` (unknown) | `_calculate_knockback` returns `Vector3.ZERO` | AEX-5 | Unknown directions treated as "none". |
| EC-20 | `modifiers` contains unknown keys (`"weaken": true`) | Key is ignored; no crash | AEX-6 | Only known handlers are checked. |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Enemy `take_damage()` missing in runtime | High — melee hits silently do nothing | `has_method()` guard; documented as deferred boundary. Integration ticket adds real method. |
| Modifier methods missing on all enemies | Medium — all modifiers silently skipped | Expected in M11; modifier effects are for future integration. Tests verify guard + call patterns. |
| Startup frame timing differs headless vs editor | Low — timer-based, not frame-counting | Design spec approach (`create_timer(frames / 60.0)`) handles this. |
| Projectile scene needs `.tscn` and Godot import | Low — CI handles `godot --import` | Implementation agent creates scene file. |
| Area query method (`_query_enemies_in_range`) implementation | Medium — no built-in Godot "query sphere at position" for non-physics nodes | Implementation detail: use `get_tree().get_nodes_in_group("enemies")` + distance filter, or PhysicsDirectSpaceState3D. Spec defines the contract, not implementation. |
| `push_warning` not easily testable in GDScript | Low — tests verify behavior (no crash, no damage) rather than the warning text | Warning text is a debug aid, not a contract. |

---

## 10. Clarifying Questions

All planning-phase ambiguities have been resolved:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Should executor directly call `enemy.take_damage()`? | Yes, via `has_method()` guard. Tests mock enemy. Actual `EnemyBase.take_damage()` deferred. (AEX-DR-1) | High |
| Duck-type vs signal for modifier application? | Duck-type with `has_method()`, matching existing pattern in `AdhesionBugLungeAttack` line 114. (AEX-DR-2) | High |
| Timer-based or frame-counting startup? | Timer-based: `create_timer(startup_frames / 60.0)`. (AEX-DR-3) | High |
| New projectile class or reuse AcidProjectile3D? | New `PlayerProjectile3D` — separate collision target (enemies, not player). (AEX-DR-4) | High |
| Real VFX/SFX or stubs? | Signal-based stubs only. (AEX-DR-5) | High |
| `knockback_direction` from modifiers or top-level? | Top-level, per frozen ATK spec. (AEX-DR-6) | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| `AttackExecutor` class created | AEX-1 | Class identity |
| Single dispatch function `execute_attack()` | AEX-2 | Dispatch routing |
| Match statement dispatches by effect_type | AEX-2 | Dispatch routing |
| `_handle_melee_swipe()` implemented | AEX-3 | Melee: hit/startup/damage/knockback |
| Startup frames wait | AEX-3 (step 1) | Melee: startup delay |
| Queries enemies in range | AEX-3 (step 2) | Melee: hit detection |
| Applies damage + knockback | AEX-3 (step 3a), AEX-5 | Melee: damage, Knockback |
| Applies modifiers (poison, acid, slow) | AEX-6 | Modifier application |
| Spawns VFX at hit location | AEX-7 | Melee: VFX signal |
| `_handle_projectile_spit()` implemented | AEX-4 | Projectile: creation |
| Creates projectile from scene | AEX-4 (step 2) | Projectile: creation |
| Sets velocity and damage | AEX-4 (step 3) | Projectile: creation |
| Attaches modifiers for on-hit effects | AEX-4 (step 3) | Projectile: creation |
| Fires forward | AEX-4 (step 3-5) | Projectile: scene addition |
| Dynamic knockback "away" | AEX-5 | Knockback: away |
| Dynamic knockback "toward" | AEX-5 | Knockback: toward |
| Dynamic knockback "none" | AEX-5 | Knockback: none |
| Tests validate both handlers | AEX-3, AEX-4 | All melee + projectile categories |
| `run_tests.sh` exits 0 | (integration) | Full suite run |
