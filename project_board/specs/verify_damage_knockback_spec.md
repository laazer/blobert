# SPEC: Verify Damage and Knockback Delivery

**Ticket:** M11-13 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/13_verify_damage_knockback.md`)  
**Spec ID:** VDK  
**Status:** Active  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-25

---

## 1. Overview

This is a **verification spec**. The attack system (AttackResource, AttackExecutor, PlayerProjectile3D, AttackDatabaseNode) is fully implemented and passing 80+ unit/adversarial tests. This spec defines **testable behavioral contracts for the 5 identified coverage gaps** that the existing test suite does not exercise:

1. Cross-mutation integration (AttackDatabase → lookup → AttackExecutor dispatch)
2. VFX spawn position correctness
3. PlayerProjectile3D on-hit behavior (damage + knockback + modifiers on collision)
4. End-to-end knockback direction in melee (verifying "toward" pulls)
5. Projectile velocity correctness (`_physics_process` movement)

No implementation changes are expected. Tests use mock enemies (duck-typed `take_damage`/`apply_*` stubs). `EnemyBase` integration methods remain deferred per AEX spec Section 6.

**Evidence Sources:**

| Source | Path | Role |
|--------|------|------|
| AttackResource impl | `scripts/attacks/attack_resource.gd` | 15-property data model (frozen M11-04) |
| AttackExecutor impl | `scripts/attacks/attack_executor.gd` | Dispatch hub: MELEE_SWIPE + PROJECTILE_SPIT handlers |
| PlayerProjectile3D impl | `scripts/attacks/player_projectile_3d.gd` | Area3D projectile with `_on_body_entered` and `_physics_process` |
| AttackDatabase impl | `scripts/attacks/attack_database.gd` | Base/fused attack registry (Dictionary-backed) |
| AEX spec (frozen) | `project_board/specs/attack_executor_spec.md` | Handler contracts, knockback algorithm, modifier rules |
| ATK spec (frozen) | `project_board/specs/attack_resource_spec.md` | Property contracts, 4 example configurations (ATK-09) |
| Planning checkpoint | `project_board/checkpoints/M11-13/2026-05-25T-plan-run.md` | 5 identified coverage gaps |
| Existing tests | `tests/scripts/attacks/test_attack_executor*.gd`, `test_attack_resource*.gd` | 80+ tests (primary + adversarial) |

---

## 2. Discrepancy Resolutions

### VDK-DR-1: Carapace and Adhesion effect_types are not handled by AttackExecutor

**Problem:** Carapace Slam uses `SLAM_AOE` and Adhesion Lunge uses `LUNGE`. The AttackExecutor only has handlers for `MELEE_SWIPE` and `PROJECTILE_SPIT`. Calling `execute_attack()` with these types routes to `_handle_unknown`.

**Evidence:** `scripts/attacks/attack_executor.gd` lines 26–32: match statement only matches `"MELEE_SWIPE"` and `"PROJECTILE_SPIT"`.

**Resolution:** Cross-mutation tests for Carapace and Adhesion verify: (a) the resource is correctly registered and retrieved from AttackDatabase, (b) `execute_attack()` does not crash when called with an unhandled effect_type, (c) `_is_active` resets to false after the unknown handler path. These tests validate the data-driven pipeline end-to-end even though the handler does not apply damage. Full `SLAM_AOE` and `LUNGE` handler implementation is deferred to future tickets.

### VDK-DR-2: EnemyBase lacks take_damage and modifier methods

**Problem:** `EnemyBase` has no `take_damage()`, `apply_poison()`, `apply_acid()`, or `apply_slowness()`.

**Evidence:** `scripts/enemies/enemy_base.gd` — only `set_base_state()`, `get_base_state()`, `get_esm()`.

**Resolution:** All tests use mock enemy stubs (Node3D subclasses with the duck-typed methods), consistent with AEX spec Section 6: Deferred Boundary. This is the established testing pattern across the existing 80+ tests.

---

## 3. Requirements

### VDK-1: Cross-Mutation Integration — AttackDatabase → Executor Pipeline

**Description:** Verify that for each of the 4 M11 mutation variants (Claw, Acid, Carapace, Adhesion), an `AttackResource` can be registered in `AttackDatabaseNode`, retrieved by mutation_id, and passed to `AttackExecutor.execute_attack()` without errors. For variants with implemented handlers (Claw/MELEE_SWIPE, Acid/PROJECTILE_SPIT), verify correct damage delivery.

**Constraints:**
- Each mutation variant uses the canonical ATK-09 configuration values from the frozen AttackResource spec.
- `AttackDatabaseNode.register_base_attack()` + `get_base_attack()` round-trip must preserve all resource properties.
- AttackExecutor must dispatch correctly based on the retrieved resource's `effect_type`.

**Acceptance Criteria:**

- **AC-1a (Claw):** Register a Claw Swipe resource (attack_id=101, effect_type=MELEE_SWIPE, damage=2.0, knockback_magnitude=100.0, knockback_direction="away") under mutation_id `"claw"`. Retrieve it. Execute against a mock enemy in range. Verify: `take_damage` called with damage=2.0 and knockback.x > 0 (away from player at origin).
- **AC-1b (Acid):** Register an Acid Spit resource (attack_id=102, effect_type=PROJECTILE_SPIT, damage=1.5, projectile_speed=250.0, modifiers={"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3}) under mutation_id `"acid"`. Retrieve it. Execute. Verify: a `PlayerProjectile3D` instance is created as a child in the scene tree with `damage == 1.5`, `speed == 250.0`, `modifiers["acid_on_hit"] == true`.
- **AC-1c (Carapace):** Register a Carapace Slam resource (attack_id=103, effect_type=SLAM_AOE) under mutation_id `"carapace"`. Retrieve it. Execute. Verify: no crash, executor `_is_active` returns false after handler, `attack_started` signal emitted, no `attack_hit` signal (unknown handler path).
- **AC-1d (Adhesion):** Register an Adhesion Lunge resource (attack_id=104, effect_type=LUNGE, modifiers={"root_duration": 0.5}) under mutation_id `"adhesion"`. Retrieve it. Execute. Verify: no crash, executor `_is_active` returns false, resource modifiers preserved through pipeline.
- **AC-1e (Property preservation):** For each mutation_id, `get_base_attack()` returns a resource whose `attack_name`, `damage`, `cooldown`, `attack_range`, `knockback_magnitude`, `knockback_direction`, and `modifiers` all match the registered values.

---

### VDK-2: VFX Spawn Position Correctness

**Description:** Verify that `melee_vfx_requested` signal emits the correct hit center position. Per AEX-3, the hitbox center (and therefore VFX position) is: `owner_position + Vector3(facing_sign * attack_range * HITBOX_RANGE_FACTOR, 0.0, 0.0)` where `HITBOX_RANGE_FACTOR = 0.5`.

**Evidence:** `attack_executor.gd` line 48: `var center := owner_pos + Vector3(facing * resource.attack_range * HITBOX_RANGE_FACTOR, 0.0, 0.0)` and line 61: `melee_vfx_requested.emit(center, ...)`.

**Constraints:**
- VFX position is computed from the executor's parent position, NOT from the enemy position.
- The position must be offset by `facing_sign * attack_range * 0.5` along the X axis.
- Y and Z components of the VFX position match the owner position's Y and Z (which is 0.0 for Z since the owner is Node3D).

**Acceptance Criteria:**

- **AC-2a (Facing right):** Owner at `(0, 0, 0)`, facing sign `1.0`, attack_range `4.0`. VFX position must be `(2.0, 0.0, 0.0)` (= 0 + 1.0 * 4.0 * 0.5).
- **AC-2b (Facing left):** Owner at `(10, 0, 0)`, facing sign `-1.0`, attack_range `6.0`. VFX position must be `(7.0, 0.0, 0.0)` (= 10 + (-1.0) * 6.0 * 0.5).
- **AC-2c (Non-zero Y):** Owner at `(5, 3, 0)`, facing sign `1.0`, attack_range `2.0`. VFX position must be `(6.0, 0.0, 0.0)`. Note: the VFX position Y is 0.0 because the center calculation uses `Vector3(facing * range * factor, 0.0, 0.0)` added to owner_pos which has its own global Y — the actual emitted position Y should reflect the owner's Y through `_get_owner_position()`. Correction based on code: `center = owner_pos + Vector3(facing * range * factor, 0.0, 0.0)` means `center.y = owner_pos.y`. So VFX position is `(6.0, 3.0, 0.0)`.
- **AC-2d (Zero range):** Owner at `(0, 0, 0)`, attack_range `0.0`. VFX position must equal owner position `(0, 0, 0)`.

---

### VDK-3: PlayerProjectile3D On-Hit Behavior

**Description:** Verify that when `PlayerProjectile3D._on_body_entered()` is triggered with a target that has `take_damage()`, the projectile correctly: (a) applies damage with computed knockback, (b) applies all active modifiers, (c) self-destructs via `queue_free()`, (d) does not apply damage more than once (consumed flag).

**Evidence:** `scripts/attacks/player_projectile_3d.gd` lines 32–40: `_on_body_entered` checks `_consumed`, calls `take_damage`, `_apply_modifiers`, `queue_free`. Lines 43–58: `_compute_knockback` mirrors AttackExecutor's algorithm.

**Constraints:**
- Knockback algorithm in PlayerProjectile3D uses the projectile's `global_position` as the origin (not the player's position), since the projectile may be far from the player at impact time.
- The `_consumed` flag prevents double-hit on the same body entry event.
- `queue_free()` is called after damage application, so the projectile is removed from the tree on the next frame.

**Acceptance Criteria:**

- **AC-3a (Damage on hit):** Projectile with `damage=5.0`, `knockback_magnitude=10.0`, `knockback_direction="away"`. Target at `(10, 0, 0)`, projectile at `(8, 0, 0)`. Calling `_on_body_entered(target)` results in `target.take_damage(5.0, knockback)` where `knockback.x > 0` (away from projectile).
- **AC-3b (Knockback toward):** Projectile with `knockback_direction="toward"`, target at `(10, 0, 0)`, projectile at `(8, 0, 0)`. Knockback vector `x < 0` (toward projectile).
- **AC-3c (Zero knockback):** Projectile with `knockback_magnitude=0.0`. `take_damage` called with `knockback == Vector3.ZERO`.
- **AC-3d (Modifier application):** Projectile with `modifiers={"poison": true, "poison_duration": 3.0, "poison_dps": 0.5}`. After `_on_body_entered`, target's `apply_poison(3.0, 0.5)` is called.
- **AC-3e (Acid modifier):** Projectile with `modifiers={"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.2}`. Target's `apply_acid(2.0, 0.2)` is called.
- **AC-3f (Slow modifier):** Projectile with `modifiers={"slow": 0.5, "slow_duration": 1.5}`. Target's `apply_slowness(0.5, 1.5)` is called.
- **AC-3g (Multiple modifiers):** Projectile with all three modifiers active. All three apply_* methods called on target.
- **AC-3h (Consumed flag):** After first `_on_body_entered`, `_consumed == true`. A second call to `_on_body_entered` with a different target results in zero additional `take_damage` calls.
- **AC-3i (No crash on bare target):** Target without `take_damage()` method. `_on_body_entered` completes without error; `_consumed` remains false (body entered but no damage path).
- **AC-3j (queue_free called):** After `_on_body_entered` with a valid target, projectile has `queue_free()` pending (verified by `is_queued_for_deletion()` or by checking it's removed after the next frame process).

---

### VDK-4: End-to-End Knockback Direction in Melee

**Description:** Verify that full melee execution (not just the isolated `_calculate_knockback` function) produces correct knockback vectors on mock enemies, specifically testing the "toward" direction which existing tests do not cover in end-to-end melee flow.

**Evidence:** Existing tests cover `_calculate_knockback()` in isolation (AEX-05 tests) and melee with "away" knockback (AEX-03). No test wires a full melee with `knockback_direction="toward"` and verifies the resulting vector on the mock enemy's `damage_taken` array.

**Constraints:**
- Knockback direction is derived from `target_pos - owner_pos` (per AEX-5 algorithm).
- "away" = delta * magnitude (push away from player).
- "toward" = -delta * magnitude (pull toward player).
- Z component always zeroed (2.5D plane constraint).

**Acceptance Criteria:**

- **AC-4a (Melee "away" e2e):** Player at origin, enemy at `(3, 0, 0)`. MELEE_SWIPE with `knockback_direction="away"`, `knockback_magnitude=10.0`, `attack_range=8.0`. Enemy's `damage_taken[0]["knockback"].x > 0` and `.z == 0.0`.
- **AC-4b (Melee "toward" e2e):** Player at origin, enemy at `(3, 0, 0)`. MELEE_SWIPE with `knockback_direction="toward"`, `knockback_magnitude=10.0`, `attack_range=8.0`. Enemy's `damage_taken[0]["knockback"].x < 0` (pulled toward player) and `.z == 0.0`.
- **AC-4c (Melee "none" e2e):** Player at origin, enemy at `(3, 0, 0)`. MELEE_SWIPE with `knockback_direction="none"`, `knockback_magnitude=10.0`, `attack_range=8.0`. Enemy's `damage_taken[0]["knockback"] == Vector3.ZERO`.
- **AC-4d (Enemy left of player):** Player at `(5, 0, 0)`, enemy at `(3, 0, 0)`, facing `-1.0`. MELEE_SWIPE with `knockback_direction="away"`, `knockback_magnitude=8.0`, `attack_range=6.0`. Enemy's `knockback.x < 0` (pushed further left, away from player).
- **AC-4e (Multiple enemies, mixed positions):** Two enemies: one at `(2, 0, 0)` and one at `(1, 0, 0)`. Player at origin, facing `1.0`. Both hit by MELEE_SWIPE with "away" knockback. Both enemies receive positive knockback.x (pushed rightward, away from player).

---

### VDK-5: Projectile Velocity Correctness

**Description:** Verify that `PlayerProjectile3D._physics_process(delta)` moves the projectile at the correct rate: `direction_x * speed * delta` units per physics frame along the X axis.

**Evidence:** `scripts/attacks/player_projectile_3d.gd` line 29: `global_position.x += direction_x * speed * delta`.

**Constraints:**
- Movement is along X axis only; Y and Z remain constant.
- When `_consumed == true`, no movement occurs.
- When `_age >= lifetime`, projectile sets `_consumed = true` and calls `queue_free()` (despawn).

**Acceptance Criteria:**

- **AC-5a (Rightward movement):** Projectile with `direction_x=1.0`, `speed=100.0`, starting at `(0, 0, 0)`. After `_physics_process(0.1)`, `global_position.x ≈ 10.0` (within float tolerance).
- **AC-5b (Leftward movement):** Projectile with `direction_x=-1.0`, `speed=200.0`, starting at `(50, 0, 0)`. After `_physics_process(0.05)`, `global_position.x ≈ 40.0`.
- **AC-5c (Zero speed):** Projectile with `speed=0.0`, `direction_x=1.0`. After `_physics_process(1.0)`, position unchanged.
- **AC-5d (Y/Z unchanged):** Projectile starting at `(0, 5, 3)`. After any `_physics_process` call, `global_position.y == 5` and `global_position.z == 3`.
- **AC-5e (No movement when consumed):** Set `_consumed = true` before calling `_physics_process(0.1)`. Position unchanged.
- **AC-5f (Lifetime expiration):** Projectile with `lifetime=1.0`. Simulate cumulative `_physics_process(delta)` calls totaling >= 1.0 seconds. After expiration, `_consumed == true` and `queue_free()` is pending.
- **AC-5g (Cumulative movement):** Projectile with `speed=50.0`, `direction_x=1.0`. Three sequential calls: `_physics_process(0.1)`, `_physics_process(0.2)`, `_physics_process(0.05)`. Final position.x ≈ 17.5 (= 50 * 0.35).

---

## 4. Frozen API Surface (Reference — No Changes)

All classes referenced in this spec are frozen. No API changes are required.

### AttackExecutor (existing)

```gdscript
signal attack_started(resource: AttackResource)
signal attack_hit(target: Node3D, resource: AttackResource)
signal projectile_fired(projectile: Node3D, resource: AttackResource)
signal melee_vfx_requested(position: Vector3, color: Color, scale: float)

func execute_attack(resource: AttackResource) -> void
func is_active() -> bool

const HITBOX_RANGE_FACTOR := 0.5
const DEFAULT_POISON_DPS := 0.3
const DEFAULT_ACID_DPS := 0.2
const DEFAULT_SLOW_DURATION := 1.5
```

### PlayerProjectile3D (existing)

```gdscript
var damage: float
var speed: float
var lifetime: float
var knockback_magnitude: float
var knockback_direction: String
var modifiers: Dictionary
var direction_x: float

func _physics_process(delta: float) -> void
func _on_body_entered(body: Node3D) -> void
```

### AttackDatabaseNode (existing)

```gdscript
func register_base_attack(mutation_id: String, resource: AttackResource) -> void
func get_base_attack(mutation_id: String) -> AttackResource
func has_base_attack(mutation_id: String) -> bool
```

---

## 5. Test Strategy

### Test scope

Integration-level tests using real class instances (AttackExecutor, AttackDatabaseNode, PlayerProjectile3D, AttackResource) with mock enemy stubs. No Godot physics simulation — projectile movement tested by directly calling `_physics_process(delta)`. Collision tested by directly calling `_on_body_entered(body)`.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_verify_damage_knockback.gd` | VDK-1 through VDK-5 behavioral verification tests |

### Test categories

| Category | Requirements | Count |
|----------|-------------|-------|
| Cross-mutation integration | VDK-1 (AC-1a through AC-1e) | 5 |
| VFX position | VDK-2 (AC-2a through AC-2d) | 4 |
| Projectile on-hit | VDK-3 (AC-3a through AC-3j) | 10 |
| E2E knockback direction | VDK-4 (AC-4a through AC-4e) | 5 |
| Projectile velocity | VDK-5 (AC-5a through AC-5g) | 7 |
| **Total** | | **31** |

### Mock enemy contract (same as existing tests)

```gdscript
class MockEnemy extends Node3D:
    var damage_taken: Array = []
    var poison_calls: Array = []
    var acid_calls: Array = []
    var slow_calls: Array = []

    func take_damage(damage: float, knockback: Vector3) -> void
    func apply_poison(duration: float, dps: float) -> void
    func apply_acid(duration: float, dps: float) -> void
    func apply_slowness(multiplier: float, duration: float) -> void
```

---

## 6. Edge Cases Table

| # | Scenario | Expected Behavior | VDK Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | AttackDatabase lookup for unregistered mutation_id | `get_base_attack()` returns null + push_warning | VDK-1 | Database already handles this; verify no crash in pipeline |
| EC-2 | Projectile hits target at exact same position | `_compute_knockback` uses degenerate fallback `(1, 0, 0)` | VDK-3 | Mirrors AttackExecutor's DEGENERATE_DISTANCE_SQ logic |
| EC-3 | Projectile with zero lifetime | Sets `_consumed = true` on first `_physics_process` call; `queue_free()` called | VDK-5 | Boundary: _age starts at 0, 0 >= 0 is true |
| EC-4 | Melee VFX position when attack_range is very large | Position computed correctly; no overflow | VDK-2 | Float arithmetic, no clamping in executor |
| EC-5 | Projectile on_body_entered with body that lacks take_damage | Body ignored, `_consumed` stays false, projectile continues moving | VDK-3 | has_method guard in _on_body_entered |
| EC-6 | Cross-mutation: retrieve resource, modify it, verify DB copy unaffected | Database stores the original reference; modifications affect it (no deep copy in DB) | VDK-1 | AttackDatabaseNode stores direct reference, not a copy |
| EC-7 | Multiple sequential _physics_process calls accumulate position correctly | Position = initial + direction_x * speed * sum(deltas) | VDK-5 | Verifies no state reset between frames |
| EC-8 | Melee "toward" with enemy directly above player (Y offset only) | delta = (0, Y, 0), after z=0 zeroing: delta=(0, Y, 0), normalized. Knockback has Y component | VDK-4 | 2.5D plane: Z zeroed but Y preserved in knockback calculation |

---

## 7. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| PlayerProjectile3D._on_body_entered requires Godot signal wiring | Low | Tests call `_on_body_entered()` directly as a method, bypassing Area3D signal infrastructure |
| _physics_process testing without scene tree | Low | Directly call method; set `global_position` manually before call |
| queue_free() verification in headless tests | Low | Check `is_queued_for_deletion()` or verify `_consumed` flag state |
| AttackDatabase stores references, not copies | Medium | Tests should verify this behavior explicitly (EC-6); future tickets may need to deep-copy |
| Carapace (SLAM_AOE) and Adhesion (LUNGE) have no handlers | None (expected) | Tests verify unknown-handler path; full handler implementation is future scope |

---

## 8. Clarifying Questions

All ambiguities resolved via code inspection and frozen specs:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Does PlayerProjectile3D use the same knockback algorithm as AttackExecutor? | Yes — identical algorithm in `_compute_knockback()`, using projectile position as origin instead of player position | High |
| Can Carapace and Adhesion attacks be tested end-to-end? | Partially — DB → lookup → executor dispatch works, but damage/hit logic requires SLAM_AOE/LUNGE handlers (deferred) | High |
| Does the projectile move in Y or Z? | No — only `global_position.x` is modified in `_physics_process` | High |
| Is the projectile consumed when hitting a body without take_damage? | No — the `has_method("take_damage")` guard prevents entering the consume path | High |
| Are VFX positions relative to owner or world? | World-space — computed as `owner_global_position + offset` | High |

No unresolved ambiguities remain.

---

## 9. Deferred Boundary (Out of Scope)

| Item | Owner | Notes |
|------|-------|-------|
| `EnemyBase.take_damage()` implementation | Future ticket | Tests use mock enemies |
| `EnemyBase.apply_poison/acid/slowness()` | Future ticket | Tests use mock enemies |
| SLAM_AOE handler implementation | Future ticket | Carapace Slam routes to unknown handler |
| LUNGE handler implementation | Future ticket | Adhesion Lunge routes to unknown handler |
| Knockback boundary clamping (level edges) | Future ticket | No clamping exists in current implementation; enemies can theoretically be knocked outside level bounds |
| Actual VFX/SFX particle rendering | Future milestone | Executor emits signals only |
| Cooldown enforcement | Caller's responsibility | Executor has no cooldown timer |
| Fused attack verification | M12+ | AttackDatabaseNode.get_fused_attack() exists but no fused configs are defined yet |

---

## 10. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| MELEE_SWIPE damage/knockback verified | VDK-1 (AC-1a), VDK-4 (AC-4a..AC-4e) | Cross-mutation + E2E knockback |
| PROJECTILE_SPIT behavior/hit verified | VDK-1 (AC-1b), VDK-3 (AC-3a..AC-3j), VDK-5 (AC-5a..AC-5g) | Cross-mutation + On-hit + Velocity |
| "away" knockback verified | VDK-4 (AC-4a) | E2E knockback |
| "toward" knockback verified | VDK-4 (AC-4b) | E2E knockback |
| Modifiers applied on hit | VDK-3 (AC-3d..AC-3g) | Projectile on-hit |
| VFX at correct location | VDK-2 (AC-2a..AC-2d) | VFX position |
| Cross-mutation variants tested | VDK-1 (AC-1a..AC-1e) | Cross-mutation integration |
