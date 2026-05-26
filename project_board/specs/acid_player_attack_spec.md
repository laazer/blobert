# SPEC: Acid Player Attack

**Ticket:** M11-09 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/09_acid_player_attack.md`)  
**Spec ID:** APA  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-26

---

## 1. Overview

The acid mutation attack is a ranged projectile (acid spit) that inflicts damage-over-time on enemy hit. It leverages the existing `PROJECTILE_SPIT` pipeline (AttackExecutor, PlayerProjectile3D, EnemyEffectTracker). This ticket registers an acid-specific `AttackResource` with tuned values, implements WEAKENED-state duration doubling in the modifier logic, and ensures the acid projectile is visually distinct from other projectiles (adhesion).

**Key design principle:** The acid attack is the second base mutation registration in AttackDatabase, following the claw pattern (CPA-2). The WEAKENED doubling logic lives in `_apply_modifiers()` (both AttackExecutor and PlayerProjectile3D), matching the established pattern where modifier logic inspects target state before applying effects. The `apply_acid()` method on EnemyBase remains a simple pass-through to EnemyEffectTracker.

**Files modified:**
- `scripts/attacks/attack_database.gd` — add acid registration in `_register_defaults()`
- `scripts/attacks/attack_executor.gd` — modify `acid_on_hit` handler in `_apply_modifiers()` to check WEAKENED state and double duration
- `scripts/attacks/player_projectile_3d.gd` — modify `acid_on_hit` handler in `_apply_modifiers()` to check WEAKENED state and double duration; apply `color` from resource

**Files unmodified:**
- `scripts/attacks/attack_resource.gd` — frozen (M11-04); `color` field already exists
- `scripts/enemies/enemy_base.gd` — `apply_acid(duration, dps)` already delegates to `_effect_tracker.add_dot("acid", ...)` (M11-14)
- `scripts/enemies/enemy_effect_tracker.gd` — DoT system with non-stacking (`add_dot` overwrites by key), 0.5s tick interval already implemented (M11-14)

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/09_acid_player_attack.md` | Acceptance criteria, remaining work |
| Planning checkpoint | `project_board/checkpoints/M11-09/2026-05-26T-plan-run.md` | Execution plan, 3 assumptions (WEAKENED location, DPS value, visual mechanism) |
| Claw spec | `project_board/specs/claw_player_attack_spec.md` | Reference for registration pattern, pre_damage_state pattern |
| AttackExecutor spec | `project_board/specs/attack_executor_spec.md` | Dispatch contract, `_apply_modifiers()` (AEX-6), PROJECTILE_SPIT handler |
| AttackResource impl | `scripts/attacks/attack_resource.gd` | Frozen class — 15 exports including `modifiers: Dictionary`, `color: Color` |
| AttackExecutor impl | `scripts/attacks/attack_executor.gd` | `_handle_projectile_spit()`, `_apply_modifiers()` with `acid_on_hit` branch |
| PlayerProjectile3D impl | `scripts/attacks/player_projectile_3d.gd` | `_on_body_entered()`, `_apply_modifiers()` with `acid_on_hit` branch |
| AttackDatabase impl | `scripts/attacks/attack_database.gd` | `_register_defaults()` with claw pattern |
| EnemyBase impl | `scripts/enemies/enemy_base.gd` | `apply_acid(duration, dps)`, `State` enum, `get_base_state()` |
| EnemyEffectTracker impl | `scripts/enemies/enemy_effect_tracker.gd` | `add_dot(name, duration, dps)`, `DOT_TICK_INTERVAL = 0.5`, non-stacking by key overwrite |

---

## 3. Discrepancy Resolutions

### APA-DR-1: WEAKENED duration doubling — where the check lives

**Problem:** The ticket requires "WEAKENED state doubles DoT duration to 6.0s." Three locations are viable: (a) inside `_apply_modifiers()` on both AttackExecutor and PlayerProjectile3D (checking target state before calling `apply_acid`), (b) inside `EnemyBase.apply_acid()` (checking own state), (c) inside `EnemyEffectTracker.add_dot()`.

**Evidence:**
- `_apply_modifiers()` already handles `acid_on_hit` in both `AttackExecutor` (line 109-114) and `PlayerProjectile3D` (line 68-73).
- The claw spec (CPA-DR-1) established the pattern: modifier logic inspects target state via `has_method("get_base_state")` before applying effects.
- Placing the check in `apply_acid()` or `add_dot()` would couple enemy internals to attack-specific mechanics.
- The planning checkpoint explicitly chose modifier logic for consistency with the claw pattern.

**Resolution:** Place the WEAKENED duration doubling check inside `_apply_modifiers()` in **both** `AttackExecutor` and `PlayerProjectile3D`. Before calling `target.apply_acid(duration, dps)`, check if `target.get_base_state() == 1` (WEAKENED); if so, double the duration. This keeps `apply_acid()` and `EnemyEffectTracker` simple pass-throughs and maintains consistency with how the claw modifier inspects target state.

**Note on pre_damage_state:** Unlike claw's `infect_weakened` which requires the *pre-damage* state to enforce a two-hit invariant, acid's WEAKENED doubling should use the **current** (post-damage) state. Rationale: if a hit weakens an enemy AND applies acid simultaneously, it is correct for the acid to benefit from the weakened state — acid is a debuff enhancement, not a state transition. The projectile path naturally uses post-damage state (projectile damage applies via `take_damage` in `_on_body_entered` before `_apply_modifiers` runs). The executor path similarly applies damage before modifiers.

### APA-DR-2: Acid DPS value

**Problem:** The ticket specifies 3.0s duration, 0.5s tick interval, but not explicit DPS. The planning checkpoint noted `DEFAULT_ACID_DPS = 0.2` exists as a fallback but suggested 1.0 DPS for meaningful damage.

**Evidence:**
- `EnemyBase.max_hp` defaults to `10.0`.
- `DOT_TICK_INTERVAL = 0.5`, so 3.0s duration = 6 ticks.
- At 1.0 DPS: each tick deals `1.0 * 0.5 = 0.5` damage → 6 ticks × 0.5 = 3.0 total DoT damage (30% of max HP).
- At 0.2 DPS (current DEFAULT_ACID_DPS): each tick deals `0.2 * 0.5 = 0.1` → 6 × 0.1 = 0.6 total (6% of max HP — too weak for a primary attack effect).
- The acid projectile also has direct hit damage; combined damage should be threatening but not one-shot.

**Resolution:** Use `1.0` DPS for the acid AttackResource's `acid_dps` modifier value. Combined with `1.0` direct hit damage: total = 1.0 (hit) + 3.0 (DoT) = 4.0 damage per successful acid hit. Against WEAKENED (6.0s, 12 ticks): total = 1.0 + 6.0 = 7.0 damage. Both are meaningful but not lethal against 10 HP enemies.

### APA-DR-3: Visual distinction mechanism

**Problem:** The ticket requires "acid projectile is visually distinct from adhesion projectile." The `AttackResource.color` field exists but `PlayerProjectile3D` currently does not apply it visually.

**Evidence:**
- `AttackResource` has `@export var color: Color = Color.WHITE` (line 16).
- `_handle_projectile_spit()` does NOT pass `resource.color` to the projectile (lines 73-80).
- The planning checkpoint resolved: "color differentiation only (acid green, `Color.CHARTREUSE` or similar)."

**Resolution:** Two changes required:
1. The acid `AttackResource` sets `color = Color.CHARTREUSE` (acid green).
2. `_handle_projectile_spit()` passes `resource.color` to the projectile instance. `PlayerProjectile3D` gains a `color: Color` property that is set by the executor. The projectile itself stores this color for visual systems to consume (e.g., a future mesh/particle tint system). For M11-09, the color property being set and readable is the contract — actual rendering is deferred.

This matches the claw pattern (CPA-6) where the VFX placeholder is the presence of correct data on the right signal/property, not the actual rendering.

### APA-DR-4: Projectile direct-hit damage value

**Problem:** The ticket lists "damage" in the resource but does not specify the projectile's direct-hit damage value (separate from DoT DPS).

**Evidence:**
- Claw does 3.0 direct damage (melee, 0.8s cooldown).
- Acid has 2.0s cooldown (slower), but adds DoT on top.
- Total acid value should be competitive with claw over time but not per-hit.

**Resolution:** Direct hit damage = `1.0`. This makes acid a DoT-focused attack (1.0 upfront + 3.0 over time = 4.0 total) vs claw's burst damage (3.0 instant). Different tactical identity: acid rewards patience, claw rewards precision.

---

## 4. Requirements

### APA-1: Acid AttackResource Definition

**Description:** An acid-specific `AttackResource` instance with tuned parameters is created and registered in the AttackDatabase under mutation_id `"acid"`.

**Property values:**

| Property | Value | Rationale |
|----------|-------|-----------|
| `attack_id` | `2` | Second registered base attack (claw=1) |
| `attack_name` | `"Acid Spit"` | Descriptive name for UI |
| `description` | `"Ranged acid projectile. Applies damage over time. WEAKENED enemies suffer double duration."` | UI tooltip |
| `effect_type` | `"PROJECTILE_SPIT"` | Routes to existing `_handle_projectile_spit()` |
| `damage` | `1.0` | Direct hit damage (APA-DR-4) |
| `cooldown` | `2.0` | Per ticket AC |
| `attack_range` | `0.0` | N/A for projectiles (range is governed by speed × lifetime) |
| `startup_frames` | `0` | Instant spit — no startup delay |
| `knockback_magnitude` | `0.0` | Acid does not knock back (DoT is the effect) |
| `knockback_direction` | `"none"` | No knockback |
| `projectile_speed` | `8.0` | Moderate projectile speed (traverses ~16 units in 2s lifetime) |
| `projectile_lifetime` | `2.0` | Default lifetime |
| `color` | `Color.CHARTREUSE` | Acid green — visually distinct from adhesion (APA-DR-3) |
| `vfx_scale` | `1.0` | Default — no emphasis needed (projectile is the visual) |
| `modifiers` | `{"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}` | Triggers DoT application with explicit params |

**Constraints:**
- `effect_type` MUST be `"PROJECTILE_SPIT"` to reuse the existing projectile pipeline.
- `modifiers` MUST contain `"acid_on_hit": true` with `"acid_duration": 3.0` and `"acid_dps": 1.0`.
- `cooldown` MUST be `2.0` (ticket requirement).
- `damage` MUST be `1.0` (direct-hit; DoT is separate via modifiers).
- `color` MUST be `Color.CHARTREUSE` (visual distinction requirement).
- `knockback_magnitude` MUST be `0.0` (acid's value proposition is DoT, not displacement).

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-1a | AttackResource with `effect_type == "PROJECTILE_SPIT"` exists for acid | `db.get_base_attack("acid").effect_type == "PROJECTILE_SPIT"` |
| APA-1b | `damage == 1.0` | Property check |
| APA-1c | `cooldown == 2.0` | Property check |
| APA-1d | `projectile_speed == 8.0` | Property check |
| APA-1e | `knockback_magnitude == 0.0` | Property check |
| APA-1f | `modifiers` contains `"acid_on_hit": true` | `db.get_base_attack("acid").modifiers.get("acid_on_hit", false) == true` |
| APA-1g | `modifiers["acid_duration"] == 3.0` | Property check |
| APA-1h | `modifiers["acid_dps"] == 1.0` | Property check |
| APA-1i | `color == Color.CHARTREUSE` | Property check |
| APA-1j | `attack_id == 2` | Property check |

---

### APA-2: AttackDatabase Registration

**Description:** `AttackDatabaseNode._register_defaults()` gains an acid registration block following the established claw pattern. The acid `AttackResource` is registered under mutation_id `"acid"`.

**Implementation pattern (follows CPA-2):**

```gdscript
const ACID_DAMAGE := 1.0
const ACID_COOLDOWN := 2.0
const ACID_PROJECTILE_SPEED := 8.0
const ACID_DPS := 1.0
const ACID_DURATION := 3.0

# Inside _register_defaults():
var acid := AttackResource.new()
acid.attack_id = 2
acid.attack_name = "Acid Spit"
acid.description = "Ranged acid projectile. Applies damage over time. WEAKENED enemies suffer double duration."
acid.effect_type = "PROJECTILE_SPIT"
acid.damage = ACID_DAMAGE
acid.cooldown = ACID_COOLDOWN
acid.attack_range = 0.0
acid.startup_frames = 0
acid.knockback_magnitude = 0.0
acid.knockback_direction = "none"
acid.projectile_speed = ACID_PROJECTILE_SPEED
acid.projectile_lifetime = 2.0
acid.color = Color.CHARTREUSE
acid.vfx_scale = 1.0
acid.modifiers = {"acid_on_hit": true, "acid_duration": ACID_DURATION, "acid_dps": ACID_DPS}
register_base_attack("acid", acid)
```

**Constraints:**
- Constants MUST be declared at module level in `attack_database.gd` (colocated with `CLAW_*` constants).
- Registration MUST occur within `_register_defaults()` (not a separate method).
- Order: claw first, acid second — preserves existing behavior.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-2a | `has_base_attack("acid")` returns true after `_ready()` | Boolean check |
| APA-2b | `get_base_attack_count()` returns at least 2 after `_ready()` (claw + acid) | Count check |
| APA-2c | Acid resource is distinct from claw resource | `get_base_attack("acid") != get_base_attack("claw")` |
| APA-2d | Existing claw tests unaffected | `run_tests.sh` exits 0 |

---

### APA-3: WEAKENED State Doubles DoT Duration

**Description:** When the `acid_on_hit` modifier is applied to a target that is in the WEAKENED state (post-damage), the acid duration is doubled from 3.0s to 6.0s. This check lives in `_apply_modifiers()` of both `AttackExecutor` and `PlayerProjectile3D`.

**Modified logic in `_apply_modifiers()` (both files):**

```gdscript
if modifiers.get("acid_on_hit", false):
    if target.has_method("apply_acid"):
        var acid_dur: float = modifiers.get("acid_duration", 2.0)
        var acid_dps_val: float = modifiers.get("acid_dps", DEFAULT_ACID_DPS)
        if target.has_method("get_base_state") and target.get_base_state() == 1:  # WEAKENED
            acid_dur *= 2.0
        target.apply_acid(acid_dur, acid_dps_val)
```

**Behavior rules:**

1. Check if `modifiers.get("acid_on_hit", false)` is truthy. If not, skip.
2. Check if `target.has_method("apply_acid")`. If not, skip silently.
3. Read `acid_duration` and `acid_dps` from modifiers dictionary (with fallbacks to 2.0 and DEFAULT_ACID_DPS).
4. Check if `target.has_method("get_base_state")` AND `target.get_base_state() == 1` (WEAKENED).
5. If WEAKENED, multiply duration by 2.0.
6. Call `target.apply_acid(acid_dur, acid_dps_val)`.

**Why post-damage state (not pre-damage):**
Unlike `infect_weakened` (which requires a two-hit invariant), acid's WEAKENED bonus is a **damage amplification** — it is correct for a single hit that weakens an enemy to also apply the doubled DoT. If the projectile's direct damage drops an enemy below WEAKENED_HP_THRESHOLD, the acid DoT should benefit from that weakened state. This makes acid more effective against wounded targets (rewarding accuracy/timing).

**Constraints:**
- The WEAKENED check MUST use `target.get_base_state() == 1` (duck-typed, `has_method` guarded).
- The doubling MUST be `acid_dur *= 2.0` (multiplicative, not additive).
- The check MUST happen AFTER damage is applied (use current state, not pre-damage state).
- Both `AttackExecutor._apply_modifiers()` AND `PlayerProjectile3D._apply_modifiers()` MUST implement this identically.
- The `DEFAULT_ACID_DPS` constant (0.2) remains as fallback for modifiers that don't specify `acid_dps`. The acid resource explicitly sets `acid_dps: 1.0`.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-3a | Target in NORMAL state receives acid with base duration (3.0s) | `apply_acid` called with `duration == 3.0` |
| APA-3b | Target in WEAKENED state receives acid with doubled duration (6.0s) | `apply_acid` called with `duration == 6.0` |
| APA-3c | Target in INFECTED state receives acid with base duration (3.0s) | `apply_acid` called with `duration == 3.0` |
| APA-3d | Target without `get_base_state()` receives acid with base duration | Fallback to non-doubled path |
| APA-3e | Dead target does not receive acid | `EnemyBase.apply_acid` guards on `_is_dead` |
| APA-3f | Duration doubling is multiplicative (2.0x), not additive | `acid_dur *= 2.0` |
| APA-3g | Both AttackExecutor and PlayerProjectile3D implement identical logic | Verified in projectile-hit and executor paths |
| APA-3h | DPS value is NOT doubled — only duration | `acid_dps_val` unchanged when WEAKENED |
| APA-3i | Hit that weakens enemy + applies acid → acid gets doubled duration | Post-damage state is WEAKENED, so acid benefits |

---

### APA-4: DoT Parameters and Tick System (Already Implemented)

**Description:** The DoT tick system is fully implemented in `EnemyEffectTracker` (M11-14). This requirement documents the contract that the acid attack relies on.

**Existing contract (EnemyEffectTracker):**
- `DOT_TICK_INTERVAL = 0.5` seconds
- `add_dot(effect_name, duration, dps)` — adds/overwrites a DoT entry keyed by `effect_name`
- Each tick deals `dps * DOT_TICK_INTERVAL` damage
- Duration countdown runs independently of tick timing
- When `remaining_duration <= 0.0`, the effect is removed

**Acid DoT behavior (given APA-1 params):**
- Base: 3.0s duration, 1.0 DPS → 6 ticks × 0.5 damage = 3.0 total DoT damage
- WEAKENED: 6.0s duration, 1.0 DPS → 12 ticks × 0.5 damage = 6.0 total DoT damage
- Tick interval: every 0.5s (first tick at 0.5s after application)

**Constraints:**
- No modification to EnemyEffectTracker is required.
- No modification to EnemyBase.apply_acid() is required.
- The acid DPS value (1.0) is passed via modifiers, not via `DEFAULT_ACID_DPS` constant.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-4a | Acid DoT ticks every 0.5s | EnemyEffectTracker._tick_dots with DOT_TICK_INTERVAL = 0.5 |
| APA-4b | Each tick deals `dps * 0.5` = 0.5 damage | `dot_tick_requested` signal carries 0.5 |
| APA-4c | DoT lasts 3.0s on NORMAL/INFECTED targets | Effect removed after remaining_duration <= 0.0 |
| APA-4d | DoT lasts 6.0s on WEAKENED targets | Duration doubled before `apply_acid` call |
| APA-4e | Total DoT damage on NORMAL: 3.0 (6 ticks × 0.5) | Sum of tick damages |
| APA-4f | Total DoT damage on WEAKENED: 6.0 (12 ticks × 0.5) | Sum of tick damages |

---

### APA-5: Non-Stacking — Same-Source Refresh

**Description:** The DoT system does not stack multiple acid DoTs. Re-hitting an enemy with acid refreshes the duration (overwrites the existing entry). This is already implemented by `EnemyEffectTracker.add_dot()` which uses dictionary key overwrite semantics.

**Existing implementation:**
```gdscript
# EnemyEffectTracker.add_dot():
_active_dots[effect_name] = {
    "remaining_duration": duration,
    "dps": dps,
    "elapsed_since_tick": 0.0,
}
```

Key `"acid"` is the same for all acid applications → last-write-wins.

**Behavior rules:**
1. First acid hit: creates `_active_dots["acid"]` with `{remaining_duration: 3.0, dps: 1.0, elapsed_since_tick: 0.0}`.
2. Second acid hit (before first expires): overwrites `_active_dots["acid"]` with fresh duration, resetting `elapsed_since_tick` to 0.0.
3. Different DoT types (poison + acid) do NOT interfere — different dictionary keys.
4. Acid from different mutation sources (e.g., future fused acid attack) still uses key `"acid"` → still non-stacking.

**Constraints:**
- No modification to EnemyEffectTracker is required.
- The effect key MUST be `"acid"` (hardcoded in `EnemyBase.apply_acid()`).

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-5a | Second acid hit refreshes duration to full (3.0s or 6.0s) | `_active_dots["acid"].remaining_duration` reset |
| APA-5b | Only one acid DoT active at a time per enemy | `_active_dots` has at most one `"acid"` key |
| APA-5c | Poison and acid can coexist on same enemy | Both keys present in `_active_dots` simultaneously |
| APA-5d | Re-application resets tick timer (`elapsed_since_tick = 0.0`) | Immediate overwrite |
| APA-5e | DPS updates on refresh (if future resources have different DPS) | Last-write value used |

---

### APA-6: Visual Distinction — Acid Projectile Color

**Description:** The acid projectile is visually distinct from other projectiles via its color property. `PlayerProjectile3D` gains a `color` property that `_handle_projectile_spit()` sets from the `AttackResource.color` field.

**Changes required:**

1. **PlayerProjectile3D** — add `var color: Color = Color.WHITE` property.
2. **AttackExecutor._handle_projectile_spit()** — add `projectile.color = resource.color` after setting other properties.

**Visual contract:**
- Acid projectile: `Color.CHARTREUSE` (bright yellow-green)
- Adhesion projectile (future): different color (TBD, likely `Color.WEB_PURPLE` or similar)
- The `color` property is the contract for any future rendering system (mesh tint, particle color, trail color).

**Constraints:**
- `PlayerProjectile3D.color` is a public `var`, not `@export` (projectiles are code-instantiated, not scene-placed).
- The color MUST be set by the executor from `resource.color`; the projectile does NOT derive its own color.
- No actual mesh/material/shader change is implemented in M11-09. The property being correctly set is the acceptance criterion.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-6a | `PlayerProjectile3D` has a `color` property | Property exists on instance |
| APA-6b | Acid projectile's `color == Color.CHARTREUSE` after spawn | Check property after `_handle_projectile_spit()` |
| APA-6c | `_handle_projectile_spit()` sets `projectile.color = resource.color` | Code path verification |
| APA-6d | Acid color is distinct from claw color (`Color.ORANGE_RED`) | `Color.CHARTREUSE != Color.ORANGE_RED` |
| APA-6e | Default projectile color is `Color.WHITE` (backward compat) | New property default |

---

### APA-7: Integration with Existing PROJECTILE_SPIT Pipeline

**Description:** The acid attack integrates with the existing pipeline without modifying the generic dispatch, projectile movement, collision, or despawn systems. The only changes to shared code are:
1. WEAKENED doubling logic added to `acid_on_hit` branch in `_apply_modifiers()` (APA-3).
2. `color` property set on projectile in `_handle_projectile_spit()` (APA-6).

**Pipeline flow for acid attack:**

```
Player presses J (attack input)
  → PlayerController3D._post_slide_housekeeping() checks input["attack_just_pressed"]
  → _try_attack()
    → State gate: PlayerInputActionPolicy.is_action_permitted(state, ACTION_ATTACK)
    → Mutation check: _mutation_slot.get_slot(0).get_active_mutation_id() == "acid"
    → Cooldown check: _mutation_cooldowns.get("acid", 0.0) <= 0.0
    → Database lookup: AttackDatabase.get_base_attack("acid") → acid AttackResource
    → Executor dispatch: _attack_executor.execute_attack(acid_resource)
      → _handle_projectile_spit(acid_resource)
        → Startup frames: 0 → no delay
        → Create PlayerProjectile3D with: damage=1.0, speed=8.0, lifetime=2.0,
           knockback=0.0, modifiers={acid_on_hit:true, acid_duration:3.0, acid_dps:1.0},
           direction_x=facing, color=Color.CHARTREUSE
        → Add to scene tree, set position
        → projectile_fired.emit(projectile, resource)
    → _mutation_cooldowns["acid"] = 2.0
```

**On projectile hit:**
```
PlayerProjectile3D._on_body_entered(enemy)
  → Guard: _consumed check
  → body.take_damage(1.0, Vector3.ZERO)  [knockback=0]
    → enemy._check_weakened_threshold() may transition NORMAL→WEAKENED
  → _apply_modifiers(enemy)
    → acid_on_hit: true
      → Check target state: get_base_state()
      → If WEAKENED (1): acid_dur = 3.0 * 2.0 = 6.0
      → Else: acid_dur = 3.0
      → target.apply_acid(acid_dur, 1.0)
        → _effect_tracker.add_dot("acid", acid_dur, 1.0)
  → queue_free()
```

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| APA-7a | `_try_attack()` with acid mutation active calls `get_base_attack("acid")` | Database lookup verification |
| APA-7b | `execute_attack()` dispatches to `_handle_projectile_spit()` for acid | `effect_type == "PROJECTILE_SPIT"` routing |
| APA-7c | Cooldown set to 2.0 after acid attack | `_mutation_cooldowns["acid"] == 2.0` |
| APA-7d | Projectile travels along X axis at speed 8.0 | `global_position.x` changes by `8.0 * delta` per frame |
| APA-7e | Projectile hits first enemy (consumed on contact) | `_consumed = true` after hit, `queue_free()` called |
| APA-7f | Existing claw and framework tests continue to pass | `run_tests.sh` exits 0 |
| APA-7g | No changes to projectile movement, collision, lifetime, or despawn logic | Code diff verification |

---

## 5. Frozen API Surface

### AttackDatabaseNode additions

```gdscript
const ACID_DAMAGE := 1.0
const ACID_COOLDOWN := 2.0
const ACID_PROJECTILE_SPEED := 8.0
const ACID_DPS := 1.0
const ACID_DURATION := 3.0
```

### PlayerProjectile3D additions

```gdscript
var color: Color = Color.WHITE
```

### AttackExecutor._handle_projectile_spit() addition

```gdscript
projectile.color = resource.color
```

### AttackExecutor._apply_modifiers() modification (acid_on_hit branch)

```gdscript
if modifiers.get("acid_on_hit", false):
    if target.has_method("apply_acid"):
        var acid_dur: float = modifiers.get("acid_duration", 2.0)
        var acid_dps_val: float = modifiers.get("acid_dps", DEFAULT_ACID_DPS)
        if target.has_method("get_base_state") and target.get_base_state() == 1:
            acid_dur *= 2.0
        target.apply_acid(acid_dur, acid_dps_val)
```

### PlayerProjectile3D._apply_modifiers() modification (acid_on_hit branch)

Same logic as AttackExecutor (identical code).

### No new public methods or signals.

---

## 6. Deferred Boundary

| Item | Owner | Notes |
|------|-------|-------|
| Actual acid projectile mesh/material/particles | Future milestone | `color` property exists; renderer connects later |
| Acid splatter VFX on hit | Future milestone | Could add signal similar to `melee_vfx_requested` |
| Adhesion projectile visual distinction | M11-11 | Will use a different color on same property |
| Fused attacks involving acid (e.g., acid+carapace) | M12 | AttackDatabase supports fused lookup |
| Acid puddle/area denial on miss | Not planned | Projectile despawns on lifetime expiry |
| DoT damage numbers/UI feedback | Future milestone | `dot_tick` signal exists on EnemyBase |
| Acid resistance/immunity on certain enemies | Not planned | Could be added via `apply_acid` guard in subclass |

---

## 7. Test Strategy

### Test scope

Unit tests with mock enemies (Node3D subclass with `take_damage()`, `apply_acid()`, `get_base_state()`, `is_dead()` stubs). Scene-tree setup for AttackDatabase `_ready()` tests. PlayerProjectile3D instantiation tests without physics simulation.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_acid_attack_behavior.gd` | Primary behavioral tests (APA-1 through APA-7) |
| `tests/scripts/attacks/test_acid_attack_adversarial.gd` | Edge cases and adversarial deepening |

### Test categories

| Category | What to test | APA Requirement |
|----------|-------------|-----------------|
| Registration | Acid resource exists in DB with correct values | APA-1, APA-2 |
| Registration: properties | All relevant AttackResource properties match spec | APA-1 |
| Registration: _register_defaults | After `_ready()`: `has_base_attack("acid")` true | APA-2 |
| WEAKENED doubling: executor path | `_apply_modifiers` with WEAKENED target → doubled duration | APA-3 |
| WEAKENED doubling: projectile path | ProjectileProjectile3D `_apply_modifiers` with WEAKENED → doubled | APA-3 |
| WEAKENED doubling: NORMAL target | Base duration (3.0s) used | APA-3 |
| WEAKENED doubling: INFECTED target | Base duration (3.0s) used | APA-3 |
| WEAKENED doubling: no state method | Base duration fallback | APA-3 |
| DoT params | Correct duration and DPS passed to `apply_acid` | APA-4 |
| Non-stacking | Second hit refreshes, doesn't stack | APA-5 |
| Visual distinction | Projectile `color == Color.CHARTREUSE` | APA-6 |
| Color set by executor | `_handle_projectile_spit` sets projectile.color | APA-6 |
| Pipeline: projectile spawns | Acid attack creates PlayerProjectile3D | APA-7 |
| Pipeline: projectile properties | Speed, damage, modifiers, direction all correct | APA-7 |
| Pipeline: cooldown | 2.0s cooldown set after attack | APA-7 |
| Regression | Existing tests unaffected | APA-7 |

### Mock enemy contract (for tests)

```gdscript
extends Node3D

var damage_taken: Array = []
var acid_applications: Array = []
var current_state: int = 0  # NORMAL=0, WEAKENED=1, INFECTED=2
var is_dead_flag: bool = false

func take_damage(damage: float, knockback: Vector3) -> void:
    damage_taken.append({"damage": damage, "knockback": knockback})

func apply_acid(duration: float, dps: float) -> void:
    acid_applications.append({"duration": duration, "dps": dps})

func get_base_state() -> int:
    return current_state

func set_base_state(state: int) -> void:
    current_state = state

func is_dead() -> bool:
    return is_dead_flag
```

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | APA Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | Acid hit on NORMAL enemy, HP stays above WEAKENED threshold | Direct damage applied, acid DoT with 3.0s duration | APA-3, APA-4 | Standard non-weakened target |
| EC-2 | Acid hit on NORMAL enemy, HP drops below WEAKENED threshold from direct hit | Enemy becomes WEAKENED via `_check_weakened_threshold()`, then acid applies with 6.0s doubled duration | APA-3 | Post-damage state is WEAKENED, acid benefits (APA-DR-1) |
| EC-3 | Acid hit on already-WEAKENED enemy | Direct damage applied, acid DoT with 6.0s doubled duration | APA-3 | Core WEAKENED doubling behavior |
| EC-4 | Acid hit on INFECTED enemy | Direct damage applied, acid DoT with 3.0s base duration | APA-3 | Only WEAKENED triggers doubling, not INFECTED |
| EC-5 | Acid hit on dead enemy | No damage (take_damage guards `_is_dead`), no acid applied (apply_acid guards `_is_dead`) | APA-3 | Dead enemies are inert |
| EC-6 | Acid hit on target without `apply_acid()` method | Direct damage applied, acid modifier silently skipped | APA-3 | `has_method` guard pattern |
| EC-7 | Acid hit on target without `get_base_state()` | Acid applied with base duration (3.0s) — WEAKENED check skipped | APA-3 | Graceful fallback for non-enemy targets |
| EC-8 | Rapid acid hits (within 2.0s cooldown) | Only first hit fires; subsequent blocked by cooldown | APA-7 | Per-mutation cooldown system |
| EC-9 | Second acid hit before first DoT expires | Duration refreshed to full 3.0s (or 6.0s if WEAKENED), `elapsed_since_tick` reset | APA-5 | Non-stacking refresh behavior |
| EC-10 | Acid and poison applied simultaneously | Both DoTs active (different keys: "acid" and "poison"), tick independently | APA-5 | Dictionary key isolation |
| EC-11 | Acid projectile misses (hits no enemy before lifetime) | Projectile despawns via `queue_free()` after 2.0s, no acid applied | APA-7 | Standard projectile lifetime |
| EC-12 | Acid projectile hits wall/environment (non-enemy body) | Projectile does NOT consume on non-`take_damage` bodies (per existing guard) | APA-7 | `_on_body_entered` checks `has_method("take_damage")` |
| EC-13 | Multiple enemies in line — projectile hits first | Projectile consumed on first hit (`_consumed = true`), second enemy unaffected | APA-7 | Single-target projectile |
| EC-14 | Acid DPS is 0.0 (edge case for future resources) | `apply_acid(3.0, 0.0)` — DoT ticks deal 0 damage each tick | APA-4 | `EnemyEffectTracker` handles gracefully |
| EC-15 | Acid duration is 0.0 or negative (malformed modifiers) | `EnemyEffectTracker.add_dot()` returns early for `duration <= 0.0` — no DoT applied | APA-4 | Existing guard in add_dot |
| EC-16 | Enemy dies mid-DoT | `_enter_death_state()` calls `_effect_tracker.stop_all_effects()` — DoT cleared | APA-4 | Already implemented |
| EC-17 | Acid projectile color not set (executor doesn't set it) | Falls back to `Color.WHITE` default | APA-6 | Backward compat for other projectile types |
| EC-18 | WEAKENED enemy transitions to INFECTED between acid application and DoT ticks | DoT continues with original duration (6.0s) — state check only at application time | APA-3 | Duration set once at apply-time; not rechecked during ticks |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Identical modifier logic in two files (AttackExecutor + PlayerProjectile3D) | Drift risk if one is updated without the other | Test both paths explicitly. Consider future extraction to shared utility (deferred — not in scope for M11-09). |
| `DEFAULT_ACID_DPS` constant (0.2) vs explicit `acid_dps: 1.0` in modifiers | Confusion if someone uses fallback thinking it's the real value | Acid resource ALWAYS specifies explicit `acid_dps` in modifiers. DEFAULT_ACID_DPS is only for legacy/fallback paths. |
| Post-damage state for WEAKENED check (APA-DR-1) differs from claw's pre-damage state pattern | Possible confusion for future developers about which pattern to use | Claw uses pre-damage (two-hit invariant for state transition). Acid uses post-damage (damage amplification for debuff). Document distinction in code comment at each modifier branch. |
| `Color.CHARTREUSE` may not be sufficiently distinct on all monitors | Low visual clarity impact | Color choice is a placeholder; can be tuned later. The contract is "color property is set and distinct from other mutations." |
| Projectile `color` property added but unused visually in M11-09 | May appear incomplete | Matches claw VFX pattern (CPA-6): presence of data is the placeholder. Actual rendering is future work. |

---

## 10. Clarifying Questions

All ambiguities resolved via discrepancy resolutions and planning checkpoint:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Where does WEAKENED doubling logic live? | `_apply_modifiers()` in both AttackExecutor and PlayerProjectile3D (APA-DR-1) | High |
| Does WEAKENED check use pre-damage or post-damage state? | Post-damage (correct: acid is damage amplification, not state transition) (APA-DR-1) | High |
| What DPS value for acid? | 1.0 DPS (APA-DR-2); total DoT = 3.0 damage over 3.0s | High |
| How is acid visually distinct? | `Color.CHARTREUSE` on ProjectileProjectile3D.color property (APA-DR-3) | High |
| What is direct hit damage? | 1.0 (APA-DR-4); DoT-focused attack | High |
| Does acid knock back? | No (knockback_magnitude = 0.0) | High |
| Does projectile pierce multiple enemies? | No; consumed on first hit (existing behavior) | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| Acid projectile is visually distinct from adhesion projectile | APA-6 (color property) | Visual distinction |
| Projectile travels along the X axis and hits the first enemy | APA-7 (pipeline integration) | Pipeline: projectile spawns, projectile properties |
| On hit, enemy takes DoT damage every 0.5s for 3.0s | APA-3, APA-4 (WEAKENED doubling, DoT params) | WEAKENED doubling: NORMAL target, DoT params |
| If enemy is WEAKENED, DoT duration increases to 6.0s | APA-3 (WEAKENED doubling) | WEAKENED doubling: executor path, projectile path |
| DoT does not stack from the same mutation | APA-5 (non-stacking refresh) | Non-stacking |
| Attack cooldown: 2.0s | APA-1 (cooldown), APA-7 (pipeline) | Registration: properties, Pipeline: cooldown |
| `run_tests.sh` exits 0 | APA-7 (regression) | Regression |
