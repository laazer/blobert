# SPEC: Adhesion Player Attack

**Ticket:** M11-11 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/11_adhesion_player_attack.md`)  
**Spec ID:** ADHA  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-26

---

## 1. Overview

The adhesion mutation attack is a sticky ranged projectile that roots (fully immobilises) the first enemy it hits for 1.0 second. It reuses the existing `PROJECTILE_SPIT` pipeline (AttackExecutor, PlayerProjectile3D). This ticket registers an adhesion-specific `AttackResource` with tuned values, fixes a critical falsy-zero bug in both `_apply_modifiers()` implementations (where `slow_val = 0.0` is silently skipped), implements wall collision despawn for projectiles, and defines the root + infection interaction.

**Key design principles:**
1. Root is implemented via the existing `apply_slowness(0.0, 1.0)` call — a speed multiplier of `0.0` is a complete movement stop. No new `apply_root()` API is introduced.
2. The falsy-zero bug (`if slow_val and slow_val > 0.0`) must be fixed in both `PlayerProjectile3D._apply_modifiers()` and `AttackExecutor._apply_modifiers()` so that `slow_val = 0.0` is correctly applied.
3. Wall collision despawn is a generic PROJECTILE_SPIT enhancement: any projectile that hits a body without `take_damage()` (e.g., StaticBody3D walls/floors) is consumed and freed. This benefits acid projectiles too.
4. The adhesion attack is the fourth base mutation registration in AttackDatabase, following claw/acid/carapace patterns.

**Files modified:**
- `scripts/attacks/attack_database.gd` — add adhesion registration in `_register_defaults()`
- `scripts/attacks/player_projectile_3d.gd` — fix falsy-zero slow check in `_apply_modifiers()`, add wall collision despawn in `_on_body_entered()`
- `scripts/attacks/attack_executor.gd` — fix falsy-zero slow check in `_apply_modifiers()`

**Files unmodified:**
- `scripts/attacks/attack_resource.gd` — frozen (M11-04); all needed exports exist
- `scripts/enemies/enemy_base.gd` — `apply_slowness(0.0, 1.0)` already functions correctly for full root (multiplier is clamped via `maxf(0.0, multiplier)` in EnemyEffectTracker)
- `scripts/enemies/enemy_effect_tracker.gd` — `set_slowness()` already handles `multiplier = 0.0` correctly; `get_speed_multiplier()` returns `0.0` while active

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/11_adhesion_player_attack.md` | Acceptance criteria, remaining work |
| Planning checkpoint | `project_board/checkpoints/M11-11/2026-05-26T-plan-run.md` | Execution plan, 4 assumptions (root via slowness, root+infection, wall collision, lifetime from range) |
| Acid spec | `project_board/specs/acid_player_attack_spec.md` | Reference for PROJECTILE_SPIT registration pattern (APA-1, APA-2), modifier logic (APA-3) |
| Carapace spec | `project_board/specs/carapace_player_attack_spec.md` | Reference for registration pattern (CCA-2) |
| AttackResource impl | `scripts/attacks/attack_resource.gd` | Frozen class — 15 exports including `modifiers`, `color`, `projectile_speed`, `projectile_lifetime` |
| AttackExecutor impl | `scripts/attacks/attack_executor.gd` | `_handle_projectile_spit()`, `_apply_modifiers()` with `slow` branch (lines 124-127) |
| PlayerProjectile3D impl | `scripts/attacks/player_projectile_3d.gd` | `_on_body_entered()`, `_apply_modifiers()` with `slow` branch (lines 76-79) |
| AttackDatabase impl | `scripts/attacks/attack_database.gd` | `_register_defaults()` with claw/acid/carapace registration patterns |
| EnemyBase impl | `scripts/enemies/enemy_base.gd` | `apply_slowness(multiplier, duration)`, `State` enum, `get_base_state()`, `set_base_state()`, `_check_weakened_threshold()` |
| EnemyEffectTracker impl | `scripts/enemies/enemy_effect_tracker.gd` | `set_slowness(multiplier, duration)`, `get_speed_multiplier()`, `_tick_slowness()` — all handle `multiplier = 0.0` correctly |

---

## 3. Discrepancy Resolutions

### ADHA-DR-1: Root implementation — new `apply_root()` vs reuse `apply_slowness(0.0, 1.0)`

**Problem:** Should the full root effect (movement = 0) be implemented as a new dedicated `apply_root()` method on EnemyBase, or reuse the existing `apply_slowness(multiplier=0.0, duration=1.0)` call via the `slow` modifier key?

**Evidence:**
- `EnemyEffectTracker.set_slowness(multiplier, duration)` uses `_slowness_multiplier = maxf(0.0, multiplier)` — correctly stores `0.0` without clamping it away.
- `EnemyEffectTracker.get_speed_multiplier()` returns `_slowness_multiplier` (which is `0.0`) when `_slowness_remaining > 0.0`, and `1.0` when expired.
- `EnemyBase.apply_slowness(0.0, 1.0)` delegates to `_effect_tracker.set_slowness(0.0, 1.0)` — the downstream system already handles complete root.
- The blocker is in `_apply_modifiers()`: `if slow_val and slow_val > 0.0` evaluates `0.0` as falsy and skips the call entirely.
- Planning checkpoint chose reuse with High confidence, noting the blocker must be fixed.

**Resolution:** Reuse `apply_slowness(0.0, 1.0)` via the existing `slow` modifier key. The downstream system (EnemyBase, EnemyEffectTracker) already supports `multiplier = 0.0`. The only change needed is fixing the falsy-zero check in `_apply_modifiers()` — both in `AttackExecutor` and `PlayerProjectile3D`. No new EnemyBase API surface is created. This is consistent with the established modifier pattern and avoids introducing a parallel effect system.

### ADHA-DR-2: Fixing the falsy-zero slow check

**Problem:** Both `AttackExecutor._apply_modifiers()` (line 124-125) and `PlayerProjectile3D._apply_modifiers()` (line 76-77) use:
```gdscript
var slow_val = modifiers.get("slow", 0.0)
if slow_val and slow_val > 0.0:
```
This is falsy for `slow_val = 0.0` because `0.0` is falsy in GDScript. A root effect (`slow = 0.0`) will silently not apply.

**Evidence:**
- GDScript truthiness: `0.0` is falsy, so `if slow_val` fails when `slow_val == 0.0`.
- The default value in `modifiers.get("slow", 0.0)` means *absence* of a `slow` key returns `0.0`, which is the same value as "full root." We need to distinguish "no slow modifier" from "slow = 0.0."
- Planning checkpoint flagged this as Critical Bug at High confidence.

**Resolution:** Change the check to use explicit presence testing. The fix:

```gdscript
var slow_val = modifiers.get("slow", null)
if slow_val != null:
    if target.has_method("apply_slowness"):
        target.apply_slowness(slow_val, modifiers.get("slow_duration", DEFAULT_SLOW_DURATION))
```

By changing the default from `0.0` to `null`, we distinguish "no slow key" (returns `null` → skipped) from "slow = 0.0" (returns `0.0` → applied). The `> 0.0` check is removed entirely because `0.0` is a valid multiplier value (full root). Any non-null slow value, including `0.0`, `0.5`, or `1.0`, will be applied. This fix applies identically to both files.

**Backward compatibility:** Existing acid and carapace attacks do not set a `slow` modifier key, so `modifiers.get("slow", null)` returns `null` → no change in behavior. Existing attacks that set `slow` to a positive value (e.g., `0.5`) continue to work because `0.5 != null` passes. This is a strictly correct fix with no regressions.

### ADHA-DR-3: Root + infection interaction mechanic

**Problem:** The ticket says "rooted enemy is easier to infect" but does not define the exact mechanic. Three options:
- (a) Rooted + NORMAL → auto-infect (too powerful, skips WEAKENED requirement)
- (b) Rooted + WEAKENED → auto-infect via adhesion projectile itself (extends existing `infect_weakened` modifier)
- (c) Reduced HP threshold during root (new mechanic, complex)

**Evidence:**
- The existing infection flow requires: (1) enemy HP drops below `WEAKENED_HP_THRESHOLD` (50%) to become WEAKENED, then (2) a claw hit with `infect_weakened: true` transitions WEAKENED → INFECTED.
- The adhesion projectile's role is to immobilise the enemy, making it easier for the player to land a follow-up claw hit on the stationary target.
- Planning checkpoint (Medium confidence) suggested adding `infect_weakened: true` to adhesion modifiers. However, this would make adhesion a standalone infection tool (root + infect in one hit if already WEAKENED), which undermines the claw's unique role.
- The most conservative interpretation: "easier to infect" means the rooted enemy cannot dodge the player's follow-up claw attack. The root IS the infection enabler — it creates a tactical window.

**Resolution:** The root effect itself is the infection interaction. A rooted enemy (speed multiplier = 0.0, duration 1.0s) cannot move, making it trivially easy for the player to close distance and land a claw hit. The adhesion projectile does NOT carry `infect_weakened: true` — infection requires a separate claw attack during the root window. This preserves the two-attack combo flow (adhesion root → claw infect) and keeps each mutation's tactical identity distinct.

The spec documents this as a **tactical synergy**, not a mechanical coupling:
- Adhesion roots the enemy (movement = 0 for 1.0s).
- During the root window, the player can freely approach and land a claw hit.
- If the rooted enemy is already WEAKENED (HP ≤ 50%), the claw's `infect_weakened` modifier transitions it to INFECTED.
- No new modifier keys, no new state checks, no changes to infection flow.

### ADHA-DR-4: Wall collision despawn mechanism

**Problem:** The ticket requires projectile despawn on wall collision. Currently `_on_body_entered()` only handles bodies with `take_damage()` — walls (StaticBody3D) silently pass through. Two approaches: (a) collision layer/mask configuration, or (b) extend `_on_body_entered()` to handle non-enemy bodies.

**Evidence:**
- `PlayerProjectile3D._on_body_entered(body)` checks `body.has_method("take_damage")` and skips otherwise (line 36).
- Walls in Godot 4 are typically `StaticBody3D` nodes without `take_damage()`.
- Planning checkpoint chose approach (b) with High confidence: extend `_on_body_entered()` to consume and free on any body without `take_damage()`.
- This is a generic enhancement to the PROJECTILE_SPIT pipeline — acid projectiles also benefit.

**Resolution:** Extend `_on_body_entered()` in `PlayerProjectile3D` to handle wall collisions. After the existing enemy-hit branch, add an `else` branch that consumes and frees the projectile when a non-enemy body is entered (i.e., a body without `take_damage()`). This covers StaticBody3D walls, floors, and any other physics bodies that aren't damageable.

Modified flow:
```
_on_body_entered(body):
  if _consumed: return
  if body.has_method("take_damage"):
    # existing enemy-hit logic
    _consumed = true
    body.take_damage(damage, kb)
    _apply_modifiers(body)
    queue_free()
  else:
    # wall/environment collision
    _consumed = true
    queue_free()
```

**Constraints:**
- The wall branch MUST set `_consumed = true` before `queue_free()` to prevent double-processing.
- The wall branch MUST NOT call `take_damage()`, `_apply_modifiers()`, or emit any hit signals.
- This is a generic pipeline change: all PROJECTILE_SPIT projectiles (acid, adhesion, future) gain wall despawn.

### ADHA-DR-5: Projectile speed and lifetime derivation

**Problem:** The ticket specifies "projectile range 10 units" but AttackResource has `projectile_lifetime` (seconds), not range. How to derive?

**Evidence:**
- Acid uses `projectile_speed = 8.0` and `projectile_lifetime = 2.0` → effective range = 16 units.
- Ticket says adhesion range should be 10 units with a 2.5s cooldown.
- Planning checkpoint: `projectile_lifetime = range / speed`. With range=10 and speed=8 (matching acid), lifetime ≈ 1.25s.

**Resolution:** Use `projectile_speed = 8.0` (matching acid — consistent projectile speed across PROJECTILE_SPIT attacks) and derive `projectile_lifetime = 10.0 / 8.0 = 1.25`. This gives a 10-unit effective range. The registration stores the computed lifetime value directly (1.25), not a formula.

### ADHA-DR-6: Adhesion projectile color

**Problem:** The ticket requires the adhesion projectile to be visually distinct. What color?

**Evidence:**
- Existing colors: claw = `Color.ORANGE_RED`, acid = `Color.CHARTREUSE`, carapace = `Color.SADDLE_BROWN`.
- Adhesion is thematically "sticky" — glue, web, resin.
- The acid spec (APA-6) noted "adhesion projectile (future): different color."

**Resolution:** Use `Color.DARK_GOLDENROD`. This is a warm amber/honey tone that evokes stickiness and is visually distinct from all existing attack colors (red, green, brown). As with all attack colors, the `color` property is the contract for future rendering systems; no mesh/material change is implemented in this ticket.

### ADHA-DR-7: Adhesion damage value

**Problem:** The ticket does not specify the adhesion projectile's direct-hit damage.

**Evidence:**
- Claw: 3.0 damage (melee, 0.8s cooldown) — burst damage.
- Acid: 1.0 damage (ranged, 2.0s cooldown) + 3.0 DoT = 4.0 total — DoT-focused.
- Carapace: 4.0 damage (AoE, 3.5s cooldown) — heavy AoE.
- Adhesion has 2.5s cooldown and its primary value is the root CC, not damage.

**Resolution:** Direct hit damage = `1.0`. Adhesion is a utility/CC attack — its value is the 1.0s root window, not raw damage. The low damage + high utility positioning matches its tactical role as a setup attack for claw follow-ups.

---

## 4. Requirements

### ADHA-1: Adhesion AttackResource Definition

**Description:** An adhesion-specific `AttackResource` instance with tuned parameters is created and registered in the AttackDatabase under mutation_id `"adhesion"`.

**Property values:**

| Property | Value | Rationale |
|----------|-------|-----------|
| `attack_id` | `4` | Fourth registered base attack (claw=1, acid=2, carapace=3) |
| `attack_name` | `"Sticky Spit"` | Descriptive name for UI — thematic adhesion |
| `description` | `"Sticky projectile that roots the first enemy hit, stopping all movement for 1.0s."` | UI tooltip |
| `effect_type` | `"PROJECTILE_SPIT"` | Routes to existing `_handle_projectile_spit()` |
| `damage` | `1.0` | Low direct damage — CC-focused attack (ADHA-DR-7) |
| `cooldown` | `2.5` | Per ticket AC |
| `attack_range` | `0.0` | N/A for projectiles (range governed by speed × lifetime) |
| `startup_frames` | `0` | Instant spit — no startup delay |
| `knockback_magnitude` | `0.0` | Root is the effect, not displacement |
| `knockback_direction` | `"none"` | No knockback |
| `projectile_speed` | `8.0` | Consistent with acid projectile speed |
| `projectile_lifetime` | `1.25` | Derived from range 10 / speed 8 = 1.25s (ADHA-DR-5) |
| `color` | `Color.DARK_GOLDENROD` | Sticky amber — visually distinct from acid green, claw red, carapace brown (ADHA-DR-6) |
| `vfx_scale` | `1.0` | Default — projectile is the visual |
| `modifiers` | `{"slow": 0.0, "slow_duration": 1.0}` | Full root (speed multiplier = 0.0) for 1.0 second |

**Constraints:**
- `effect_type` MUST be `"PROJECTILE_SPIT"` to reuse the existing projectile pipeline.
- `modifiers` MUST contain `"slow": 0.0` (full root, NOT a positive slowness value) and `"slow_duration": 1.0`.
- `cooldown` MUST be `2.5` (ticket requirement).
- `damage` MUST be `1.0` (CC-focused, not damage-focused).
- `color` MUST be `Color.DARK_GOLDENROD` (visual distinction requirement).
- `knockback_magnitude` MUST be `0.0` (rooted enemies should stay in place).
- `projectile_lifetime` MUST be `1.25` (10 units range ÷ 8.0 speed).
- `modifiers` MUST NOT contain `"infect_weakened": true` (infection is a separate claw responsibility — see ADHA-DR-3).

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-1a | AttackResource with `effect_type == "PROJECTILE_SPIT"` exists for adhesion | `db.get_base_attack("adhesion").effect_type == "PROJECTILE_SPIT"` |
| ADHA-1b | `damage == 1.0` | Property check |
| ADHA-1c | `cooldown == 2.5` | Property check |
| ADHA-1d | `projectile_speed == 8.0` | Property check |
| ADHA-1e | `projectile_lifetime == 1.25` | Property check (float comparison with tolerance) |
| ADHA-1f | `knockback_magnitude == 0.0` | Property check |
| ADHA-1g | `modifiers` contains `"slow": 0.0` | `db.get_base_attack("adhesion").modifiers.get("slow", null) == 0.0` (must not confuse with null) |
| ADHA-1h | `modifiers["slow_duration"] == 1.0` | Property check |
| ADHA-1i | `color == Color.DARK_GOLDENROD` | Property check |
| ADHA-1j | `attack_id == 4` | Property check |
| ADHA-1k | `modifiers` does NOT contain `"infect_weakened"` | `"infect_weakened" not in modifiers` |

---

### ADHA-2: AttackDatabase Registration

**Description:** `AttackDatabaseNode._register_defaults()` gains an adhesion registration block following the established claw/acid/carapace pattern. The adhesion `AttackResource` is registered under mutation_id `"adhesion"`.

**Implementation pattern (follows CPA-2, APA-2, CCA-2):**

```gdscript
const ADHESION_ATTACK_ID := 4
const ADHESION_DAMAGE := 1.0
const ADHESION_COOLDOWN := 2.5
const ADHESION_PROJECTILE_SPEED := 8.0
const ADHESION_PROJECTILE_LIFETIME := 1.25
const ADHESION_ROOT_DURATION := 1.0

# Inside _register_defaults():
var adhesion := AttackResource.new()
adhesion.attack_id = ADHESION_ATTACK_ID
adhesion.attack_name = "Sticky Spit"
adhesion.description = "Sticky projectile that roots the first enemy hit, stopping all movement for 1.0s."
adhesion.effect_type = "PROJECTILE_SPIT"
adhesion.damage = ADHESION_DAMAGE
adhesion.cooldown = ADHESION_COOLDOWN
adhesion.attack_range = 0.0
adhesion.startup_frames = 0
adhesion.knockback_magnitude = 0.0
adhesion.knockback_direction = "none"
adhesion.projectile_speed = ADHESION_PROJECTILE_SPEED
adhesion.projectile_lifetime = ADHESION_PROJECTILE_LIFETIME
adhesion.color = Color.DARK_GOLDENROD
adhesion.vfx_scale = 1.0
adhesion.modifiers = {"slow": 0.0, "slow_duration": ADHESION_ROOT_DURATION}
register_base_attack("adhesion", adhesion)
```

**Constraints:**
- Constants MUST be declared at module level in `attack_database.gd` (colocated with `CLAW_*`, `ACID_*`, `CARAPACE_*` constants).
- Registration MUST occur within `_register_defaults()`.
- Order: claw first, acid second, carapace third, adhesion fourth.
- Existing tests that call `register_base_attack()` directly are NOT affected because they create their own `AttackDatabaseNode` instances.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-2a | `has_base_attack("adhesion")` returns true after `_ready()` | Boolean check |
| ADHA-2b | `get_base_attack_count()` returns at least 4 after `_ready()` (claw + acid + carapace + adhesion) | Count check |
| ADHA-2c | Adhesion resource is distinct from claw, acid, and carapace resources | Object identity checks |
| ADHA-2d | Existing claw, acid, and carapace tests unaffected | `run_tests.sh` exits 0 |

---

### ADHA-3: Falsy-Zero Slow Modifier Fix

**Description:** Both `AttackExecutor._apply_modifiers()` and `PlayerProjectile3D._apply_modifiers()` have a bug where `slow_val = 0.0` is treated as falsy and skipped. This must be fixed to support the adhesion root effect (`slow = 0.0` means full movement stop).

**Current broken code (both files):**

```gdscript
var slow_val = modifiers.get("slow", 0.0)
if slow_val and slow_val > 0.0:
    if target.has_method("apply_slowness"):
        target.apply_slowness(slow_val, modifiers.get("slow_duration", DEFAULT_SLOW_DURATION))
```

**Fixed code (both files):**

```gdscript
var slow_val = modifiers.get("slow", null)
if slow_val != null:
    if target.has_method("apply_slowness"):
        target.apply_slowness(slow_val, modifiers.get("slow_duration", DEFAULT_SLOW_DURATION))
```

**Behavior rules:**

1. `modifiers.get("slow", null)` returns `null` if the key is absent, or the value if present (including `0.0`).
2. `if slow_val != null` is truthy for `0.0`, `0.5`, `1.0`, or any other numeric value — only `null` (key absent) skips.
3. `target.apply_slowness(0.0, 1.0)` is called for adhesion root — EnemyEffectTracker correctly sets speed multiplier to `0.0`.
4. Existing acid attack does not set `"slow"` in modifiers → `null` → skipped (no change in behavior).
5. Any future attack with `"slow": 0.5` still works because `0.5 != null` passes.

**Constraints:**
- The fix MUST apply to BOTH `AttackExecutor._apply_modifiers()` AND `PlayerProjectile3D._apply_modifiers()`.
- The default value in `modifiers.get()` MUST change from `0.0` to `null`.
- The condition MUST change from `if slow_val and slow_val > 0.0` to `if slow_val != null`.
- No other changes to the slow handling logic (the `apply_slowness` call signature remains identical).
- The fix is a regression fix that enables correct behavior for all slow values including `0.0`.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-3a | `slow = 0.0` in modifiers calls `apply_slowness(0.0, duration)` on target | Mock target records `apply_slowness` call with multiplier `0.0` |
| ADHA-3b | `slow = 0.5` in modifiers still calls `apply_slowness(0.5, duration)` | Backward compat: positive slow values still work |
| ADHA-3c | No `slow` key in modifiers → `apply_slowness` NOT called | `null` default correctly skips |
| ADHA-3d | Fix applied in AttackExecutor._apply_modifiers() | Code inspection |
| ADHA-3e | Fix applied in PlayerProjectile3D._apply_modifiers() | Code inspection |
| ADHA-3f | Existing acid attack unaffected (no `slow` key in acid modifiers) | Acid tests pass |
| ADHA-3g | Dead target does not receive slowness | `EnemyBase.apply_slowness` guards on `_is_dead` |

---

### ADHA-4: Root Effect via Slow Modifier

**Description:** When the adhesion projectile hits an enemy, it applies a full root effect: the enemy's speed multiplier is set to `0.0` for `1.0` second. The enemy cannot move during this period. After 1.0 second, the speed multiplier returns to `1.0` (normal speed).

**Mechanism chain:**

```
Projectile hits enemy
  → _on_body_entered(enemy)
    → body.take_damage(1.0, Vector3.ZERO)
    → _apply_modifiers(enemy)
      → slow_val = modifiers.get("slow", null)  →  0.0
      → slow_val != null  →  true
      → enemy.apply_slowness(0.0, 1.0)
        → EnemyEffectTracker.set_slowness(0.0, 1.0)
          → _slowness_multiplier = maxf(0.0, 0.0) = 0.0
          → _slowness_remaining = 1.0
        → get_speed_multiplier() returns 0.0 for 1.0s
        → _tick_slowness() decrements _slowness_remaining each frame
        → When _slowness_remaining <= 0.0:
          → _slowness_multiplier = 1.0 (speed restored)
```

**Behavior rules:**

1. On hit, `apply_slowness(0.0, 1.0)` is called — enemy's speed multiplier becomes `0.0`.
2. For exactly `1.0` second (minus frame-timing variance), `get_speed_multiplier()` returns `0.0`.
3. After `1.0` second, `_slowness_multiplier` resets to `1.0` and `get_speed_multiplier()` returns `1.0`.
4. The root does NOT affect knockback — if the adhesion projectile also had knockback (it doesn't, `knockback_magnitude = 0.0`), knockback would still apply.
5. Re-rooting (hitting a rooted enemy again) refreshes the duration: `set_slowness()` overwrites `_slowness_multiplier` and `_slowness_remaining`.
6. A stronger slow (e.g., `0.5`) applied during root overwrites the root — `set_slowness()` always overwrites, not stacks. The last-write-wins semantic means a `0.5` slow replaces `0.0` root.

**Constraints:**
- No modification to `EnemyBase.apply_slowness()` is required.
- No modification to `EnemyEffectTracker.set_slowness()` or `get_speed_multiplier()` is required.
- The root effect is fully implemented via the existing slowness system with multiplier `0.0`.
- Root does NOT prevent `take_damage()` — the enemy can still be damaged while rooted.
- Root does NOT prevent state transitions — a rooted NORMAL enemy can become WEAKENED via damage.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-4a | `get_speed_multiplier()` returns `0.0` immediately after adhesion hit | Property check after `apply_slowness(0.0, 1.0)` |
| ADHA-4b | `get_speed_multiplier()` returns `1.0` after 1.0 second has elapsed | Timer test with process ticks |
| ADHA-4c | Enemy movement is effectively zero during root | Speed multiplier = 0.0 used by movement system |
| ADHA-4d | Re-rooting refreshes duration to 1.0s | Second `apply_slowness(0.0, 1.0)` resets `_slowness_remaining` |
| ADHA-4e | Root does not prevent `take_damage()` | Enemy can be damaged while rooted |
| ADHA-4f | Root does not prevent state transitions (NORMAL → WEAKENED) | HP drop below threshold still transitions |
| ADHA-4g | Root expires naturally after 1.0s without external trigger | `_tick_slowness()` handles countdown |

---

### ADHA-5: Wall Collision Despawn

**Description:** `PlayerProjectile3D._on_body_entered()` is extended to despawn the projectile when it hits a non-damageable body (walls, floors, environment). This is a generic PROJECTILE_SPIT enhancement that benefits all projectile types.

**Current code:**

```gdscript
func _on_body_entered(body: Node3D) -> void:
    if _consumed:
        return
    if body.has_method("take_damage"):
        _consumed = true
        var kb := _compute_knockback(body)
        body.take_damage(damage, kb)
        _apply_modifiers(body)
        queue_free()
```

**Modified code:**

```gdscript
func _on_body_entered(body: Node3D) -> void:
    if _consumed:
        return
    if body.has_method("take_damage"):
        _consumed = true
        var kb := _compute_knockback(body)
        body.take_damage(damage, kb)
        _apply_modifiers(body)
        queue_free()
    else:
        _consumed = true
        queue_free()
```

**Behavior rules:**

1. If the body has `take_damage()` → existing enemy-hit logic (damage, modifiers, despawn).
2. If the body does NOT have `take_damage()` → wall collision: set `_consumed = true`, `queue_free()`.
3. No damage, no modifiers, no knockback on wall collision.
4. The `_consumed` flag prevents double-processing if both a wall and enemy are entered in the same physics frame.
5. This applies to ALL PROJECTILE_SPIT projectiles (acid and adhesion).

**Constraints:**
- The `else` branch MUST set `_consumed = true` before `queue_free()`.
- The `else` branch MUST NOT call `take_damage()`, `_apply_modifiers()`, `_compute_knockback()`, or emit any signals.
- The `else` branch handles ANY body without `take_damage()` — not just StaticBody3D. This is intentionally broad: any non-damageable physics body stops the projectile.
- No collision layer/mask changes are required — the existing Area3D monitoring configuration determines which bodies trigger `_on_body_entered()`.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-5a | Projectile despawns when hitting a body without `take_damage()` | `queue_free()` called, `_consumed = true` |
| ADHA-5b | No damage dealt on wall collision | `take_damage()` NOT called |
| ADHA-5c | No modifiers applied on wall collision | `_apply_modifiers()` NOT called |
| ADHA-5d | `_consumed` flag prevents double-processing | Second body-entered after wall hit is skipped |
| ADHA-5e | Enemy hit still works correctly (existing behavior preserved) | `take_damage()` + `_apply_modifiers()` called |
| ADHA-5f | Acid projectile also despawns on wall collision | Same code path; acid tests pass |
| ADHA-5g | Projectile that misses wall and enemy still despawns on lifetime | Lifetime expiry in `_physics_process` unchanged |

---

### ADHA-6: Visual Distinction — Adhesion Projectile Color

**Description:** The adhesion projectile is visually distinct from other projectiles via its `color` property. The color is set to `Color.DARK_GOLDENROD` (warm amber/honey tone) by the executor from the AttackResource.

**Visual contract (all PROJECTILE_SPIT attacks):**
- Acid: `Color.CHARTREUSE` (bright yellow-green)
- Adhesion: `Color.DARK_GOLDENROD` (amber/honey)
- The `color` property on `PlayerProjectile3D` is the contract for future rendering systems.

**Constraints:**
- The color MUST be set by `_handle_projectile_spit()` from `resource.color` (existing code path via `projectile.color = resource.color`).
- The adhesion projectile does NOT derive its own color — it receives it from the AttackResource.
- No mesh/material/shader change is implemented in this ticket. The property being correctly set is the acceptance criterion.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-6a | Adhesion projectile's `color == Color.DARK_GOLDENROD` after spawn | Property check after `_handle_projectile_spit()` |
| ADHA-6b | Adhesion color is distinct from acid color (`Color.CHARTREUSE`) | Color inequality |
| ADHA-6c | Adhesion color is distinct from claw color (`Color.ORANGE_RED`) | Color inequality |
| ADHA-6d | Adhesion color is distinct from carapace color (`Color.SADDLE_BROWN`) | Color inequality |

---

### ADHA-7: Root + Infection Tactical Synergy

**Description:** The root effect creates a tactical window for infection. A rooted enemy cannot move for 1.0 second, giving the player time to approach and land a claw hit. The adhesion projectile does NOT directly infect enemies — infection requires a separate claw attack with `infect_weakened: true`.

**Tactical flow:**

```
1. Player fires adhesion projectile at enemy (any state).
2. On hit: enemy takes 1.0 damage + root (speed = 0 for 1.0s).
3. If enemy HP drops below WEAKENED_HP_THRESHOLD (50%): enemy transitions to WEAKENED.
   (Adhesion's 1.0 damage alone won't weaken a 10 HP enemy from full — prior damage needed.)
4. Player approaches rooted enemy (can't dodge) during 1.0s root window.
5. Player switches to claw mutation and attacks.
6. Claw's infect_weakened modifier: if enemy state == WEAKENED → transition to INFECTED.
7. Root expires after 1.0s. If enemy is now INFECTED, infection mechanics take over.
```

**Behavior rules:**

1. Adhesion `modifiers` MUST NOT contain `"infect_weakened"` — infection is claw's domain.
2. The root window (1.0s) is the adhesion's contribution to the infection loop.
3. No code changes are needed to implement this synergy — it emerges from existing mechanics.
4. The spec defines this as a tactical interaction, not a mechanical one (no new modifier keys or state checks).

**Constraints:**
- Adhesion modifiers: `{"slow": 0.0, "slow_duration": 1.0}` — no infection-related keys.
- The infection interaction is tested by verifying: (a) enemy is rooted after adhesion hit, (b) claw can infect a rooted+WEAKENED enemy during the root window, (c) adhesion alone does NOT infect.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-7a | Adhesion projectile does NOT set `infect_weakened` in modifiers | Modifier key absence check |
| ADHA-7b | Rooted WEAKENED enemy can be infected by claw during root window | Claw hit on rooted WEAKENED enemy → state == INFECTED |
| ADHA-7c | Adhesion hit alone does NOT transition enemy to INFECTED | State remains NORMAL or WEAKENED after adhesion hit |
| ADHA-7d | Root creates a 1.0s window where enemy cannot dodge claw follow-up | `get_speed_multiplier() == 0.0` during root |

---

### ADHA-8: Integration with Existing PROJECTILE_SPIT Pipeline

**Description:** The adhesion attack integrates with the existing pipeline. The only changes to shared code are:
1. Falsy-zero slow fix in `_apply_modifiers()` of both AttackExecutor and PlayerProjectile3D (ADHA-3).
2. Wall collision despawn in `PlayerProjectile3D._on_body_entered()` (ADHA-5).

No changes to projectile movement, velocity, facing direction, lifetime despawn, or the `_handle_projectile_spit()` method.

**Pipeline flow for adhesion attack:**

```
Player presses J (attack input)
  → PlayerController3D._post_slide_housekeeping() checks input["attack_just_pressed"]
  → _try_attack()
    → State gate: PlayerInputActionPolicy.is_action_permitted(state, ACTION_ATTACK)
    → Mutation check: _mutation_slot.get_slot(0).get_active_mutation_id() == "adhesion"
    → Cooldown check: _mutation_cooldowns.get("adhesion", 0.0) <= 0.0
    → Database lookup: AttackDatabase.get_base_attack("adhesion") → adhesion AttackResource
    → Executor dispatch: _attack_executor.execute_attack(adhesion_resource)
      → _handle_projectile_spit(adhesion_resource)
        → Startup frames: 0 → no delay
        → Create PlayerProjectile3D with: damage=1.0, speed=8.0, lifetime=1.25,
           knockback=0.0, modifiers={slow:0.0, slow_duration:1.0},
           direction_x=facing, color=Color.DARK_GOLDENROD
        → Add to scene tree, set position
        → projectile_fired.emit(projectile, resource)
    → _mutation_cooldowns["adhesion"] = 2.5
```

**On projectile hit (enemy):**

```
PlayerProjectile3D._on_body_entered(enemy)
  → Guard: _consumed check
  → body.take_damage(1.0, Vector3.ZERO)  [knockback=0]
    → enemy._check_weakened_threshold() may transition NORMAL→WEAKENED
  → _apply_modifiers(enemy)
    → slow_val = modifiers.get("slow", null)  →  0.0
    → 0.0 != null  →  true
    → enemy.apply_slowness(0.0, 1.0)
      → EnemyEffectTracker._slowness_multiplier = 0.0
      → EnemyEffectTracker._slowness_remaining = 1.0
  → _consumed = true
  → queue_free()
```

**On projectile hit (wall):**

```
PlayerProjectile3D._on_body_entered(wall)
  → Guard: _consumed check
  → wall does NOT have take_damage()
  → _consumed = true
  → queue_free()
```

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| ADHA-8a | `_try_attack()` with adhesion mutation active calls `get_base_attack("adhesion")` | Database lookup verification |
| ADHA-8b | `execute_attack()` dispatches to `_handle_projectile_spit()` for adhesion | `effect_type == "PROJECTILE_SPIT"` routing |
| ADHA-8c | Cooldown set to 2.5 after adhesion attack | `_mutation_cooldowns["adhesion"] == 2.5` |
| ADHA-8d | Projectile travels along X axis at speed 8.0 | `global_position.x` changes by `8.0 * delta` per frame |
| ADHA-8e | Projectile hits first enemy (consumed on contact) | `_consumed = true` after hit, `queue_free()` called |
| ADHA-8f | Projectile despawns on wall collision | `_consumed = true` after wall hit, `queue_free()` called |
| ADHA-8g | Projectile despawns after 1.25s lifetime if no collision | Lifetime expiry via `_physics_process` |
| ADHA-8h | Existing claw, acid, and carapace tests continue to pass | `run_tests.sh` exits 0 |
| ADHA-8i | No changes to `_handle_projectile_spit()` | Code diff verification |

---

## 5. Frozen API Surface

### AttackDatabaseNode additions

```gdscript
const ADHESION_ATTACK_ID := 4
const ADHESION_DAMAGE := 1.0
const ADHESION_COOLDOWN := 2.5
const ADHESION_PROJECTILE_SPEED := 8.0
const ADHESION_PROJECTILE_LIFETIME := 1.25
const ADHESION_ROOT_DURATION := 1.0
```

### AttackExecutor._apply_modifiers() modification (slow branch)

```gdscript
var slow_val = modifiers.get("slow", null)
if slow_val != null:
    if target.has_method("apply_slowness"):
        target.apply_slowness(slow_val, modifiers.get("slow_duration", DEFAULT_SLOW_DURATION))
```

### PlayerProjectile3D._apply_modifiers() modification (slow branch)

Same logic as AttackExecutor (identical code).

### PlayerProjectile3D._on_body_entered() modification (wall branch)

```gdscript
func _on_body_entered(body: Node3D) -> void:
    if _consumed:
        return
    if body.has_method("take_damage"):
        _consumed = true
        var kb := _compute_knockback(body)
        body.take_damage(damage, kb)
        _apply_modifiers(body)
        queue_free()
    else:
        _consumed = true
        queue_free()
```

### No new public methods or signals.

---

## 6. Deferred Boundary

| Item | Owner | Notes |
|------|-------|-------|
| Actual adhesion projectile mesh/material/particles | Future milestone | `color` property exists; renderer connects later |
| Adhesion splatter VFX on hit | Future milestone | Could add signal similar to `melee_vfx_requested` |
| Root visual indicator on enemy (e.g., web wrapping, sticky overlay) | Future milestone | `get_speed_multiplier() == 0.0` is the testable state |
| Fused attacks involving adhesion (e.g., adhesion + acid) | M12 | AttackDatabase supports fused lookup |
| Root duration scaling by enemy type/size | Not planned | Duration is fixed at 1.0s via modifier |
| Root break on damage (CC break mechanic) | Not planned | Root always lasts full 1.0s regardless of incoming damage |
| Multiple adhesion projectiles in flight simultaneously | Not planned | Cooldown 2.5s > lifetime 1.25s prevents overlap in normal play |
| Adhesion puddle/area denial on miss | Not planned | Projectile despawns on wall or lifetime |

---

## 7. Test Strategy

### Test scope

Unit tests with mock enemies (Node3D subclass with `take_damage()`, `apply_slowness()`, `get_base_state()`, `is_dead()` stubs). Scene-tree setup for AttackDatabase `_ready()` tests. PlayerProjectile3D instantiation tests for wall collision and modifier application. Both executor and projectile modifier paths must be tested.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_adhesion_attack_behavior.gd` | Primary behavioral tests (ADHA-1 through ADHA-8) |
| `tests/scripts/attacks/test_adhesion_attack_adversarial.gd` | Edge cases and adversarial deepening |

### Test categories

| Category | What to test | ADHA Requirement |
|----------|-------------|-----------------|
| Registration | Adhesion resource exists in DB with correct values | ADHA-1, ADHA-2 |
| Registration: properties | All AttackResource properties match spec | ADHA-1 |
| Registration: _register_defaults | After `_ready()`: `has_base_attack("adhesion")` true, count >= 4 | ADHA-2 |
| Falsy-zero fix: root applied | `slow = 0.0` → `apply_slowness(0.0, 1.0)` called | ADHA-3 |
| Falsy-zero fix: positive slow | `slow = 0.5` → `apply_slowness(0.5, ...)` called (backward compat) | ADHA-3 |
| Falsy-zero fix: no slow key | No `slow` key → `apply_slowness` NOT called | ADHA-3 |
| Falsy-zero fix: both paths | Fix verified in AttackExecutor AND PlayerProjectile3D | ADHA-3 |
| Root effect: speed zero | `get_speed_multiplier() == 0.0` during root | ADHA-4 |
| Root effect: duration | Speed restores to 1.0 after 1.0s | ADHA-4 |
| Root effect: re-root refresh | Second hit refreshes root duration | ADHA-4 |
| Wall collision: despawn | Projectile freed on wall hit | ADHA-5 |
| Wall collision: no damage | `take_damage` NOT called on wall | ADHA-5 |
| Wall collision: consumed flag | `_consumed = true` on wall hit | ADHA-5 |
| Visual distinction | Projectile `color == Color.DARK_GOLDENROD` | ADHA-6 |
| Root+infection: no auto-infect | Adhesion alone does not infect | ADHA-7 |
| Root+infection: claw combo | Claw can infect rooted WEAKENED enemy | ADHA-7 |
| Pipeline: projectile spawns | Adhesion attack creates PlayerProjectile3D | ADHA-8 |
| Pipeline: projectile properties | Speed, damage, modifiers, direction, lifetime all correct | ADHA-8 |
| Pipeline: cooldown | 2.5s cooldown set after attack | ADHA-8 |
| Regression | Existing tests unaffected | ADHA-8 |

### Mock enemy contract (for tests)

```gdscript
extends Node3D

var damage_taken: Array = []
var slowness_applications: Array = []
var current_state: int = 0  # NORMAL=0, WEAKENED=1, INFECTED=2
var is_dead_flag: bool = false

func take_damage(damage: float, knockback: Vector3) -> void:
    damage_taken.append({"damage": damage, "knockback": knockback})

func apply_slowness(multiplier: float, duration: float) -> void:
    slowness_applications.append({"multiplier": multiplier, "duration": duration})

func get_base_state() -> int:
    return current_state

func set_base_state(state: int) -> void:
    current_state = state

func is_dead() -> bool:
    return is_dead_flag
```

### Mock wall contract (for tests)

```gdscript
extends Node3D

# Intentionally no take_damage() method — simulates a wall/environment body.
```

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | ADHA Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | Adhesion hit on NORMAL enemy, HP stays above WEAKENED threshold | 1.0 damage + root (speed = 0) for 1.0s, state stays NORMAL | ADHA-4 | Standard root-only hit |
| EC-2 | Adhesion hit on NORMAL enemy, HP drops below WEAKENED threshold from direct hit | Enemy becomes WEAKENED, root applied. State = WEAKENED + rooted | ADHA-4 | Post-damage weakened transition + root |
| EC-3 | Adhesion hit on already-WEAKENED enemy | 1.0 damage + root for 1.0s. State stays WEAKENED. NOT infected (no `infect_weakened` modifier) | ADHA-7 | Adhesion does not auto-infect |
| EC-4 | Adhesion hit on INFECTED enemy | 1.0 damage + root for 1.0s. State stays INFECTED | ADHA-4 | Root applies regardless of state |
| EC-5 | Adhesion hit on dead enemy | No damage (take_damage guards `_is_dead`), no slowness (apply_slowness guards `_is_dead`) | ADHA-4 | Dead enemies are inert |
| EC-6 | Adhesion hit on target without `apply_slowness()` method | Direct damage applied, slow modifier silently skipped (`has_method` guard) | ADHA-3 | Duck-type guard pattern |
| EC-7 | Adhesion hit on target without `take_damage()` method (wall) | Projectile consumed and freed, no damage, no modifiers | ADHA-5 | Wall collision despawn |
| EC-8 | Rapid adhesion presses within 2.5s cooldown | Only first fires; subsequent blocked by cooldown | ADHA-8 | Per-mutation cooldown system |
| EC-9 | Second adhesion hit on already-rooted enemy | Root duration refreshed to 1.0s (last-write-wins in `set_slowness`) | ADHA-4 | Slowness overwrite semantics |
| EC-10 | Adhesion root + acid DoT simultaneously | Both effects active: root (speed = 0) AND acid DoT ticking. Different systems, no interference | ADHA-4 | Slowness and DoT are independent |
| EC-11 | Adhesion root + claw slowness overwrite | Claw hit with `slow: 0.5` during root → `set_slowness(0.5, ...)` overwrites root → speed = 0.5 instead of 0.0 | ADHA-4 | Last-write-wins for slowness |
| EC-12 | Projectile hits wall before any enemy | Projectile consumed and freed on wall, no enemy damaged | ADHA-5 | Wall collision takes priority by position |
| EC-13 | Projectile lifetime expires (1.25s, no collision) | Projectile freed via `_physics_process` lifetime check | ADHA-8 | Standard lifetime despawn unchanged |
| EC-14 | Multiple enemies in line — projectile hits first | Consumed on first enemy, second enemy unaffected | ADHA-8 | Single-target projectile |
| EC-15 | Adhesion root on already-slowed enemy (e.g., slow = 0.5) | Root (0.0) overwrites partial slow (0.5) → speed = 0.0 | ADHA-4 | Last-write-wins for slowness |
| EC-16 | Root expires exactly at 1.0s boundary | Speed restores to 1.0. `_tick_slowness` sets `_slowness_multiplier = 1.0` when `_slowness_remaining <= 0.0` | ADHA-4 | Existing expiry logic in EnemyEffectTracker |
| EC-17 | `slow_duration` missing from modifiers | Falls back to `DEFAULT_SLOW_DURATION` (1.5s) — not the intended 1.0s. Test verifies modifier always includes explicit duration | ADHA-3 | Fallback defense; resource always specifies duration |
| EC-18 | Acid projectile hits wall (new behavior from ADHA-5 change) | Acid projectile also consumed and freed on wall — no acid DoT applied | ADHA-5 | Generic pipeline enhancement |
| EC-19 | Executor `_apply_modifiers()` with `slow = 0.0` (melee path, not projectile) | Fix also applies to executor path — `apply_slowness(0.0, ...)` correctly called | ADHA-3 | Both paths fixed identically |
| EC-20 | Projectile hits enemy and wall in same physics frame | `_consumed` flag prevents double processing — first body_entered wins | ADHA-5 | Consumed guard |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Falsy-zero fix changes behavior for all PROJECTILE_SPIT attacks | Medium | Only affects attacks with `"slow"` in modifiers. Acid and carapace do not set this key. Claw uses `infect_weakened`, not `slow`. No existing attack uses `slow: 0.0`. Regression risk is minimal. |
| Wall collision despawn is a generic change affecting all projectiles | Medium | Acid projectile gains wall despawn. This is a NET POSITIVE (acid should not pass through walls). Test acid wall collision explicitly. |
| `null` default in `modifiers.get("slow", null)` — GDScript null comparison | Low | GDScript `null != null` is `false`; `0.0 != null` is `true`. The comparison is well-defined in GDScript 4.x. |
| Root + slow overwrite (last-write-wins) could surprise players | Low | Slowness system is documented as last-write-wins. Future work could add a "stronger effect wins" policy, but that is out of scope. |
| `Color.DARK_GOLDENROD` may not be sufficiently distinct from `Color.SADDLE_BROWN` on all displays | Low | Both are warm tones but `DARK_GOLDENROD` is significantly lighter/more yellow. Color is a tunable constant. |
| Adhesion `infect_weakened: false` is explicitly excluded, but future ticket could re-add it | Low | ADHA-DR-3 documents the design decision. Future changes would be a new ticket with its own spec. |
| Identical modifier logic in two files (AttackExecutor + PlayerProjectile3D) | Ongoing drift risk | Both paths tested explicitly. Future extraction to shared utility deferred. |

---

## 10. Clarifying Questions

All ambiguities resolved via discrepancy resolutions and planning checkpoint:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Should root use new API or reuse `apply_slowness(0.0, 1.0)`? | Reuse `apply_slowness` — downstream system already supports 0.0 (ADHA-DR-1) | High |
| How to fix `slow_val = 0.0` being falsy? | Change default to `null`, check `!= null` instead of truthiness (ADHA-DR-2) | High |
| What does "rooted enemy easier to infect" mean? | Tactical synergy: root creates a 1.0s window for claw follow-up. No auto-infect (ADHA-DR-3) | High |
| How should wall collision despawn work? | Extend `_on_body_entered()` with `else` branch for non-damageable bodies (ADHA-DR-4) | High |
| What projectile speed and lifetime? | Speed 8.0, lifetime 1.25 (range 10 ÷ speed 8) (ADHA-DR-5) | High |
| What color for adhesion? | `Color.DARK_GOLDENROD` — distinct from all existing colors (ADHA-DR-6) | High |
| What direct-hit damage? | 1.0 — CC-focused, not damage-focused (ADHA-DR-7) | High |
| Should adhesion carry `infect_weakened`? | No — infection requires separate claw hit (ADHA-DR-3) | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| Firing projectile is visible and travels along the X axis from the player | ADHA-8 (pipeline integration), ADHA-6 (visual distinction) | Pipeline: projectile spawns, Visual distinction |
| Projectile hits the first enemy in its path and despawns | ADHA-8 (pipeline integration) | Pipeline: projectile properties |
| On hit, enemy movement is set to 0 for 1.0 seconds | ADHA-3 (falsy-zero fix), ADHA-4 (root effect) | Falsy-zero fix: root applied, Root effect: speed zero, Root effect: duration |
| Enemy in NORMAL state can be infected during the root window (existing infection flow applies) | ADHA-7 (root + infection tactical synergy) | Root+infection: claw combo |
| Projectile despawns on wall collision or after max range (configurable, default 10 units) | ADHA-5 (wall collision despawn), ADHA-1 (lifetime = 1.25s for 10 unit range) | Wall collision: despawn, Pipeline: projectile properties |
| Attack cooldown: 2.5s | ADHA-1 (cooldown), ADHA-8 (pipeline integration) | Registration: properties, Pipeline: cooldown |
| `run_tests.sh` exits 0 | ADHA-8 (regression) | Regression |
