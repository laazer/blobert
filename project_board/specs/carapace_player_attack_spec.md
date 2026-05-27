# SPEC: Carapace Player Attack

**Ticket:** M11-10 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/10_carapace_player_attack.md`)  
**Spec ID:** CCA  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-26

---

## 1. Overview

The carapace mutation attack is a heavy ground slam that damages and knocks back all enemies within a radial area-of-effect centered on the player's position. Unlike claw (directional melee, `MELEE_SWIPE`) and acid (ranged projectile, `PROJECTILE_SPIT`), carapace introduces a brand-new effect type `SLAM_AOE` that requires a new handler `_handle_slam_aoe()` in `AttackExecutor`. This is the first handler addition since the initial two were implemented in M11-05, validating the extensibility claim in AEX-8.

**Key novel elements vs prior attacks:**
1. **Omnidirectional radial query** — centered on player position, not offset by facing direction.
2. **Wind-up delay** — 0.2s (12 startup_frames) before hitbox activates, giving enemies a reaction window.
3. **Airborne slam deferral** — if the player is airborne when the attack fires, the slam delays until landing (or times out after 3.0s).
4. **Multi-enemy simultaneous hit** — all enemies in radius take damage + knockback in the same handler call.
5. **New VFX signal** — `slam_vfx_requested` (distinct from `melee_vfx_requested`).

**Files modified:**
- `scripts/attacks/attack_executor.gd` — add `SLAM_AOE` match arm, `_handle_slam_aoe()` handler, `slam_vfx_requested` signal
- `scripts/attacks/attack_database.gd` — add carapace registration in `_register_defaults()`

**Files unmodified:**
- `scripts/attacks/attack_resource.gd` — frozen (M11-04); `startup_frames`, `attack_range`, `knockback_direction` already exist
- `scripts/player/player_controller_3d.gd` — `_try_attack()`, `is_on_floor()`, cooldown system already wired (M11-06); airborne deferral is handled inside the executor, not the controller
- `scripts/enemies/enemy_base.gd` — `take_damage()`, `get_base_state()`, knockback impulse already exist (M11-14)

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/10_carapace_player_attack.md` | Acceptance criteria, remaining work |
| Planning checkpoint | `project_board/checkpoints/M11-10/2026-05-26T-plan-run.md` | Execution plan, 4 assumptions (radial center, startup_frames, airborne mechanism, VFX signal) |
| Claw spec | `project_board/specs/claw_player_attack_spec.md` | Reference for registration pattern (CPA-2), melee handler flow |
| Acid spec | `project_board/specs/acid_player_attack_spec.md` | Reference for registration pattern (APA-2), modifier pattern |
| AttackExecutor spec | `project_board/specs/attack_executor_spec.md` | Dispatch contract (AEX-2), unknown handling (AEX-8), knockback calc (AEX-5), signals (AEX-7), `_query_enemies_in_range` |
| AttackResource impl | `scripts/attacks/attack_resource.gd` | Frozen class — 15 exports including `startup_frames`, `attack_range`, `knockback_direction` |
| AttackExecutor impl | `scripts/attacks/attack_executor.gd` | `execute_attack()`, `_handle_melee_swipe()`, `_query_enemies_in_range()`, `_calculate_knockback()`, `_apply_damage()`, `_apply_modifiers()`, `_is_active` guard, `_get_owner_position()` |
| AttackDatabase impl | `scripts/attacks/attack_database.gd` | `_register_defaults()` with claw + acid constants pattern |
| PlayerController3D impl | `scripts/player/player_controller_3d.gd` | `_try_attack()`, `_mutation_cooldowns`, `is_on_floor()`, `_attack_executor` child node |
| EnemyBase impl | `scripts/enemies/enemy_base.gd` | `take_damage(damage, knockback)`, `State` enum, `_knockback_velocity`, `is_dead()` |

---

## 3. Discrepancy Resolutions

### CCA-DR-1: Radial query center — player position vs facing offset

**Problem:** The existing `_handle_melee_swipe()` offsets the query center by `facing * attack_range * HITBOX_RANGE_FACTOR`. Should `_handle_slam_aoe()` do the same?

**Evidence:**
- `_handle_melee_swipe()` (attack_executor.gd line 48): `center := owner_pos + Vector3(facing * resource.attack_range * HITBOX_RANGE_FACTOR, 0.0, 0.0)`.
- Planning checkpoint assumption A1: "Radial query reuses `_query_enemies_in_range()` centered on player (not offset by facing)."
- A ground slam is semantically omnidirectional — the impact radiates from where the player lands, not from a point in front.

**Resolution:** Center the query on `_get_owner_position()` with zero offset. The slam radius IS `attack_range` (not halved). This means `_handle_slam_aoe()` calls `_query_enemies_in_range(owner_pos, resource.attack_range)` — using the full `attack_range` as radius, not `attack_range * HITBOX_RANGE_FACTOR`. The factor was designed for directional melee (offset center needs smaller radius); a centered radial query uses the full configured radius.

### CCA-DR-2: Wind-up delay — startup_frames vs new field

**Problem:** Should the 0.2s wind-up use the existing `startup_frames: int` (12 frames at 60fps) or a new `startup_delay_seconds: float` field?

**Evidence:**
- `AttackResource.startup_frames: int` already exists (attack_resource.gd line 11).
- `AttackExecutor.FRAMES_PER_SECOND = 60.0` (attack_executor.gd line 4).
- Both `_handle_melee_swipe()` and `_handle_projectile_spit()` already convert via `resource.startup_frames / FRAMES_PER_SECOND`.
- Planning checkpoint assumption A2: "Use `startup_frames = 12` (0.2s at 60fps)."
- CPA-5 confirms `startup_frames = 0` means instant.

**Resolution:** Use `startup_frames = 12`. The conversion `12 / 60.0 = 0.2` seconds is exact. No new field needed. The `_handle_slam_aoe()` handler uses the same timer pattern as existing handlers: `await tree.create_timer(resource.startup_frames / FRAMES_PER_SECOND).timeout`.

### CCA-DR-3: Airborne slam deferral mechanism — executor-internal vs controller-external

**Problem:** Two viable approaches exist: (a) `_handle_slam_aoe()` polls `is_on_floor()` via parent after wind-up; (b) `PlayerController3D._try_attack()` queues the attack for execution on next grounded frame.

**Evidence:**
- Planning checkpoint assumption A3: "Handle inside `_handle_slam_aoe()` within AttackExecutor" with Medium confidence. Notes controller-side is also viable but more invasive.
- `PlayerController3D._try_attack()` (line 675-711) is a synchronous method that calls `execute_attack()` and sets cooldown immediately. Queuing would require additional state tracking.
- `AttackExecutor._is_active` flag naturally blocks overlapping attacks while waiting for landing.
- The executor already uses `await` for startup timer — adding a landing await is consistent.
- `_get_owner_position()` accesses the parent's `global_position`; similarly, the handler can check `parent.is_on_floor()` via `has_method`.

**Resolution:** Handle inside `_handle_slam_aoe()`. After the wind-up delay, the handler checks if the player is on the floor via `parent.is_on_floor()` (with `has_method` guard). If airborne, the handler enters a polling loop using `get_tree().create_timer(0.05).timeout` (50ms intervals), rechecking `is_on_floor()` each iteration. A maximum wait time of 3.0 seconds prevents infinite hangs — if the player has not landed after 3.0s, the slam is cancelled (`_is_active` set to false, no damage applied). The `_is_active` flag remains `true` during the wait, preventing any other attack from firing.

**Rationale for executor-internal:**
1. Self-contained — no changes to `PlayerController3D._try_attack()` flow.
2. Consistent — executor already uses `await` for startup timer.
3. Safe — `_is_active` guard prevents overlapping.
4. Testable — mock parent with `is_on_floor()` stub.

### CCA-DR-4: VFX signal — new vs reuse melee signal

**Problem:** Should carapace reuse `melee_vfx_requested(position, color, scale)` or add a new signal?

**Evidence:**
- Planning checkpoint assumption: "Add a new `slam_vfx_requested` signal" with Medium confidence.
- Claw/melee uses `melee_vfx_requested` — directional slash arc.
- Slam has different visual semantics: radial ground impact, dust ring, ground crack.
- `projectile_fired` is distinct from `melee_vfx_requested` — effect-type-specific signals are the established pattern.

**Resolution:** Add a new signal `slam_vfx_requested(position: Vector3, radius: float, color: Color, scale: float)`. This includes `radius` as an additional parameter (melee signal lacks it) because the slam impact area is a key visual element. The signal emits after the damage query completes (hit or miss), mirroring the melee pattern where VFX fires even on whiff.

### CCA-DR-5: Cooldown timing — when does cooldown start?

**Problem:** Carapace has a wind-up + potential airborne wait. Should cooldown start when the attack button is pressed, or when the slam actually impacts?

**Evidence:**
- `PlayerController3D._try_attack()` (line 711): `_mutation_cooldowns[cooldown_key] = attack_resource.cooldown`. This runs immediately after `execute_attack()` is called, before the handler's `await` completes (because `execute_attack` returns the control flow to the caller upon first `await`).
- This means cooldown starts at button press, not at impact. This is consistent for all attacks — claw's cooldown starts before the (instant) hit, acid's cooldown starts before the projectile travels.

**Resolution:** No change needed. Cooldown starts at button press (existing behavior from `_try_attack()`). For carapace with 3.5s cooldown and 0.2s wind-up, the effective cooldown after impact is ~3.3s. The 3.5s value accounts for the wind-up.

### CCA-DR-6: Airborne deferral interaction with execute_attack async behavior

**Problem:** `execute_attack()` in the current implementation sets `_is_active = true`, calls the handler, then sets `_is_active = false` — all synchronously. If `_handle_slam_aoe()` uses `await`, the `_is_active = false` line will execute immediately after the handler's first `await`, not after the handler completes.

**Evidence:**
- `attack_executor.gd` lines 19-33: `execute_attack()` calls the handler and then sets `_is_active = false`. But if the handler uses `await` (as melee/projectile do for startup_frames), GDScript coroutine semantics mean `_is_active = false` runs as soon as the handler awaits.
- However, examining the existing code more carefully: `_handle_melee_swipe()` already uses `await` for startup delay. After that await, `execute_attack()` proceeds to `_is_active = false`. This means `_is_active` is only true during the synchronous prologue before the first `await` in the handler.
- This is the existing pattern for ALL handlers. The `_is_active` flag is NOT held for the full handler duration when `await` is involved.

**Resolution:** The `_handle_slam_aoe()` handler must manage `_is_active` internally for the airborne-wait phase, matching how existing handlers implicitly work. Specifically: `execute_attack()` keeps its current structure (set `_is_active = true`, call handler, set `_is_active = false`). But for `_handle_slam_aoe()`, the handler should NOT rely on `execute_attack()`'s `_is_active = false` after the handler's first await. Instead, `_handle_slam_aoe()` must explicitly set `_is_active = false` when it completes (after landing or timeout), and `execute_attack()` must be modified to NOT reset `_is_active` after calling an async handler.

**Frozen design:** Modify `execute_attack()` to make the SLAM_AOE handler responsible for its own `_is_active` lifecycle. The handler sets `_is_active = false` when it finishes (after wind-up + optional airborne wait + damage + VFX). For the SLAM_AOE match arm only, `execute_attack()` does NOT set `_is_active = false` after the handler call (the handler does it). For MELEE_SWIPE and PROJECTILE_SPIT, the existing behavior is preserved.

Implementation approach:

```gdscript
func execute_attack(resource: AttackResource) -> void:
    if resource == null:
        return
    if _is_active:
        return
    _is_active = true
    attack_started.emit(resource)
    match resource.effect_type:
        "MELEE_SWIPE":
            _handle_melee_swipe(resource)
        "PROJECTILE_SPIT":
            _handle_projectile_spit(resource)
        "SLAM_AOE":
            _handle_slam_aoe(resource)
            return  # handler manages _is_active lifecycle
        _:
            _handle_unknown(resource)
    _is_active = false
```

This is minimally invasive: the only change to `execute_attack()` is the new match arm + `return` after `_handle_slam_aoe()`. Existing handlers are unaffected.

---

## 4. Requirements

### CCA-1: Carapace AttackResource Definition

**Description:** A carapace-specific `AttackResource` instance with tuned combat parameters is created and registered in the AttackDatabase under mutation_id `"carapace"`.

**Property values:**

| Property | Value | Rationale |
|----------|-------|-----------|
| `attack_id` | `3` | Third registered base attack (claw=1, acid=2) |
| `attack_name` | `"Ground Slam"` | Descriptive name for UI |
| `description` | `"Heavy ground slam. Damages and knocks back all enemies in radius. Slams on landing if airborne."` | UI tooltip |
| `effect_type` | `"SLAM_AOE"` | Routes to new `_handle_slam_aoe()` |
| `damage` | `4.0` | Heavy hit — strongest single-hit of base mutations (claw=3.0, acid=1.0) |
| `cooldown` | `3.5` | Slowest cooldown per ticket (claw=0.8, acid=2.0) |
| `attack_range` | `3.0` | Slam radius per ticket ("configurable, default 3.0 units") |
| `startup_frames` | `12` | 0.2s wind-up (12 / 60.0 = 0.2s) per ticket |
| `knockback_magnitude` | `5.0` | Strong knockback — thematic for a heavy slam (claw=2.0) |
| `knockback_direction` | `"away"` | Push enemies away from player (radially) |
| `projectile_speed` | `0.0` | N/A for slam |
| `projectile_lifetime` | `2.0` | Default — unused for slam |
| `color` | `Color.SADDLE_BROWN` | Carapace/shell/earth-tone brown |
| `vfx_scale` | `1.5` | Larger than claw (1.2) — emphasizes the area-of-effect |
| `modifiers` | `{}` | No special modifiers — pure damage + knockback |

**Constraints:**
- `effect_type` MUST be `"SLAM_AOE"` to route to the new handler.
- `cooldown` MUST be `3.5` (ticket requirement: "slowest attack of all base mutations").
- `attack_range` MUST be `3.0` (ticket requirement: "configurable, default 3.0 units").
- `startup_frames` MUST be `12` (ticket requirement: "0.2s wind-up").
- `knockback_direction` MUST be `"away"` (ticket requirement: "knockback away from the player").
- `modifiers` MUST be `{}` (carapace is a pure damage/knockback attack; no DoT, no infection, no slow).

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-1a | AttackResource with `effect_type == "SLAM_AOE"` exists for carapace | `db.get_base_attack("carapace").effect_type == "SLAM_AOE"` |
| CCA-1b | `damage == 4.0` | Property check |
| CCA-1c | `cooldown == 3.5` | Property check |
| CCA-1d | `attack_range == 3.0` | Property check |
| CCA-1e | `knockback_magnitude == 5.0` | Property check |
| CCA-1f | `knockback_direction == "away"` | Property check |
| CCA-1g | `startup_frames == 12` | Property check |
| CCA-1h | `modifiers` is empty `{}` | `db.get_base_attack("carapace").modifiers.size() == 0` |
| CCA-1i | `color == Color.SADDLE_BROWN` | Property check |
| CCA-1j | `vfx_scale == 1.5` | Property check |
| CCA-1k | `attack_id == 3` | Property check |

---

### CCA-2: AttackDatabase Registration

**Description:** `AttackDatabaseNode._register_defaults()` gains a carapace registration block following the established claw/acid pattern. The carapace `AttackResource` is registered under mutation_id `"carapace"`.

**Implementation pattern (follows CPA-2, APA-2):**

```gdscript
const CARAPACE_DAMAGE := 4.0
const CARAPACE_COOLDOWN := 3.5
const CARAPACE_RANGE := 3.0
const CARAPACE_KNOCKBACK := 5.0
const CARAPACE_STARTUP_FRAMES := 12
const CARAPACE_VFX_SCALE := 1.5

# Inside _register_defaults():
var carapace := AttackResource.new()
carapace.attack_id = 3
carapace.attack_name = "Ground Slam"
carapace.description = "Heavy ground slam. Damages and knocks back all enemies in radius. Slams on landing if airborne."
carapace.effect_type = "SLAM_AOE"
carapace.damage = CARAPACE_DAMAGE
carapace.cooldown = CARAPACE_COOLDOWN
carapace.attack_range = CARAPACE_RANGE
carapace.startup_frames = CARAPACE_STARTUP_FRAMES
carapace.knockback_magnitude = CARAPACE_KNOCKBACK
carapace.knockback_direction = "away"
carapace.color = Color.SADDLE_BROWN
carapace.vfx_scale = CARAPACE_VFX_SCALE
carapace.modifiers = {}
register_base_attack("carapace", carapace)
```

**Constraints:**
- Constants MUST be declared at module level in `attack_database.gd` (colocated with `CLAW_*` and `ACID_*` constants).
- Registration MUST occur within `_register_defaults()`.
- Order: claw first, acid second, carapace third.
- Existing tests that call `register_base_attack()` directly are NOT affected because they create their own `AttackDatabaseNode` instances.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-2a | `has_base_attack("carapace")` returns true after `_ready()` | Boolean check |
| CCA-2b | `get_base_attack_count()` returns at least 3 after `_ready()` (claw + acid + carapace) | Count check |
| CCA-2c | Carapace resource is distinct from claw and acid resources | `get_base_attack("carapace") != get_base_attack("claw")` etc. |
| CCA-2d | Existing claw and acid tests unaffected | `run_tests.sh` exits 0 |

---

### CCA-3: SLAM_AOE Handler — `_handle_slam_aoe()`

**Description:** A new handler method `_handle_slam_aoe(resource: AttackResource)` is added to `AttackExecutor`. It performs a radial enemy query centered on the player, applies damage and knockback to all enemies in range, and manages its own `_is_active` lifecycle due to the async airborne-wait.

**Handler behavior (sequential):**

1. **Wind-up delay:** If `resource.startup_frames > 0`, await `resource.startup_frames / FRAMES_PER_SECOND` seconds via `get_tree().create_timer()`. If `startup_frames == 0`, proceed immediately.
2. **Airborne check:** Call `_is_owner_on_floor()` (new helper, see CCA-3 constraints). If the player is on the floor, proceed to step 3. If airborne, enter landing-wait loop (step 2a).
   - **2a. Landing-wait loop:** Poll `_is_owner_on_floor()` every 50ms (`get_tree().create_timer(0.05).timeout`). Track elapsed wait time. If the player lands (`_is_owner_on_floor()` returns `true`), proceed to step 3. If 3.0 seconds elapse without landing, cancel the slam: set `_is_active = false` and return (no damage, no VFX).
3. **Radial area query:** Call `_query_enemies_in_range(_get_owner_position(), resource.attack_range)`. This uses the full `attack_range` as radius (not halved — see CCA-DR-1).
4. **Per-enemy processing:** For each enemy in the result array:
   a. Calculate knockback via `_calculate_knockback(enemy.global_position, owner_pos, resource.knockback_magnitude, resource.knockback_direction)`.
   b. Call `_apply_damage(enemy, resource.damage, knockback)`.
   c. Call `_apply_modifiers(enemy, resource.modifiers)` (no special modifiers for carapace, but future resources could add them).
   d. Emit `attack_hit(enemy, resource)`.
5. **VFX signal:** Emit `slam_vfx_requested(_get_owner_position(), resource.attack_range, resource.color, resource.vfx_scale)` regardless of hit count (VFX plays even on whiff).
6. **Cleanup:** Set `_is_active = false`.

**New helper method:**

```gdscript
func _is_owner_on_floor() -> bool:
    var parent := get_parent()
    if parent and parent.has_method("is_on_floor"):
        return parent.is_on_floor()
    return true  # conservative default: treat as grounded if unknown
```

**Constants:**

```gdscript
const SLAM_LANDING_POLL_INTERVAL := 0.05
const SLAM_LANDING_TIMEOUT := 3.0
```

**Constraints:**
- The handler MUST manage `_is_active` — set it to `false` at the end (step 6) or on timeout cancellation (step 2a).
- `execute_attack()` MUST NOT set `_is_active = false` after calling `_handle_slam_aoe()` (the handler owns its own lifecycle via `return` in the match arm — see CCA-DR-6).
- The radial query uses `_get_owner_position()` as center (no facing offset — see CCA-DR-1).
- The radius is `resource.attack_range` (full value, not halved by `HITBOX_RANGE_FACTOR`).
- Knockback is calculated per-enemy using `_calculate_knockback()` — each enemy receives knockback pointing AWAY from the player (radial).
- The handler MUST be `async` (uses `await` for wind-up timer, landing poll timer).
- `_apply_modifiers()` is called even though carapace has empty modifiers — this ensures future carapace resources with modifiers work without handler changes.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-3a | Wind-up delay of `startup_frames / 60.0` seconds (0.2s for carapace) before hitbox query | Timer verification in test |
| CCA-3b | Radial query centered on player position (not offset by facing) | Query center == `_get_owner_position()` |
| CCA-3c | Query radius is full `attack_range` (3.0), not halved | `_query_enemies_in_range(pos, 3.0)` |
| CCA-3d | All enemies within radius take damage | `take_damage` called on each with `damage == 4.0` |
| CCA-3e | Each enemy receives knockback AWAY from player | Knockback vector points from player to enemy |
| CCA-3f | Enemies outside radius are NOT hit | Distance check excludes them |
| CCA-3g | `attack_hit` signal emitted once per enemy hit | Signal count == enemy count in radius |
| CCA-3h | `slam_vfx_requested` emitted once per slam execution (hit or miss) | Signal monitoring |
| CCA-3i | `_is_active == false` after handler completes | State check post-execution |
| CCA-3j | No crash if zero enemies are in range | Empty result array handled gracefully |
| CCA-3k | `_apply_modifiers()` called for each enemy (even with empty modifiers) | Call verification |

---

### CCA-4: Airborne Slam Deferral

**Description:** If the player is not on the floor when the attack is triggered (after the wind-up delay), the slam hitbox activation is deferred until the player lands. A timeout of 3.0 seconds prevents the attack from hanging indefinitely.

**Behavior rules:**

1. After the wind-up delay completes, check `_is_owner_on_floor()`.
2. If grounded → proceed to damage immediately.
3. If airborne → enter polling loop:
   a. Wait 50ms (`SLAM_LANDING_POLL_INTERVAL`).
   b. Check `_is_owner_on_floor()`.
   c. If grounded → proceed to damage.
   d. If still airborne and elapsed < 3.0s → repeat from (a).
   e. If elapsed >= 3.0s (`SLAM_LANDING_TIMEOUT`) → cancel slam, set `_is_active = false`, return.
4. During the entire airborne-wait, `_is_active` remains `true` — no other attack can fire.
5. Cooldown was already set by `_try_attack()` at button press — the airborne wait does not reset or extend it.

**Constraints:**
- The polling interval MUST be 50ms (responsive enough for landing detection, not wasteful).
- The timeout MUST be 3.0 seconds (generous for any reasonable jump/fall).
- On timeout, the slam is silently cancelled — no damage, no VFX, no signal except `attack_started` (which already fired).
- The `_is_active` flag MUST remain `true` during the wait to prevent overlapping attacks.
- The handler MUST NOT hold references to enemies during the wait — the query runs AFTER landing.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-4a | Slam fires immediately if player is on floor after wind-up | Grounded test: no polling loop, immediate damage |
| CCA-4b | Slam defers until landing if player is airborne | Airborne→land test: damage applied after `is_on_floor()` returns true |
| CCA-4c | Slam cancels after 3.0s timeout if player never lands | Timeout test: no damage, no VFX, `_is_active` reset |
| CCA-4d | `_is_active` remains true during airborne wait | Active-guard test: second attack during wait is rejected |
| CCA-4e | Cooldown unaffected by airborne wait | Cooldown starts at button press regardless |
| CCA-4f | Enemy positions queried at landing time, not at button-press time | Deferred query test: enemies that moved into range after button press are hit |

---

### CCA-5: SLAM_AOE Match Arm in `execute_attack()`

**Description:** `execute_attack()` gains a new `"SLAM_AOE"` match arm that dispatches to `_handle_slam_aoe()`. Because the SLAM_AOE handler manages its own `_is_active` lifecycle (due to async airborne wait), the match arm returns immediately after calling the handler, skipping the `_is_active = false` line.

**Modified dispatch:**

```gdscript
match resource.effect_type:
    "MELEE_SWIPE":
        _handle_melee_swipe(resource)
    "PROJECTILE_SPIT":
        _handle_projectile_spit(resource)
    "SLAM_AOE":
        _handle_slam_aoe(resource)
        return
    _:
        _handle_unknown(resource)
_is_active = false
```

**Constraints:**
- The `return` after `_handle_slam_aoe()` is REQUIRED — without it, `_is_active = false` would execute immediately after the handler's first `await`, breaking the active-guard for the entire wind-up + airborne-wait duration.
- Existing MELEE_SWIPE and PROJECTILE_SPIT behavior MUST NOT change. Their `_is_active = false` still runs after the handler call (which is fine because their async behavior is limited to startup_frames, and the existing pattern already has this characteristic).
- Unknown effect_types still route to `_handle_unknown()` (AEX-8 preserved).

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-5a | `"SLAM_AOE"` effect_type routes to `_handle_slam_aoe()` | Dispatch test |
| CCA-5b | `_is_active` is NOT reset by `execute_attack()` for SLAM_AOE (handler does it) | State check after async handler |
| CCA-5c | Existing MELEE_SWIPE dispatch unaffected | Claw tests pass |
| CCA-5d | Existing PROJECTILE_SPIT dispatch unaffected | Acid tests pass |
| CCA-5e | Unknown effect_types still route to `_handle_unknown()` | Unknown test passes |
| CCA-5f | `attack_started` signal emitted before SLAM_AOE dispatch | Signal timing test |

---

### CCA-6: VFX Placeholder — `slam_vfx_requested` Signal

**Description:** A new signal `slam_vfx_requested` is added to `AttackExecutor` for slam-specific visual effects. This is distinct from `melee_vfx_requested` because the slam has different visual semantics (radial ground impact vs directional slash arc) and includes `radius` as an additional parameter.

**Signal declaration:**

```gdscript
signal slam_vfx_requested(position: Vector3, radius: float, color: Color, scale: float)
```

**Emission:**
- Emitted by `_handle_slam_aoe()` after the damage query completes (step 5), regardless of hit count.
- Arguments: `(_get_owner_position(), resource.attack_range, resource.color, resource.vfx_scale)`.
- For carapace: `slam_vfx_requested.emit(pos, 3.0, Color.SADDLE_BROWN, 1.5)`.

**Constraints:**
- `slam_vfx_requested` MUST be a NEW signal, not a reuse of `melee_vfx_requested`.
- The signal MUST include `radius` as the second parameter (melee signal does not have this).
- The signal MUST emit even if zero enemies were hit (VFX plays on whiff).
- The signal MUST NOT emit on timeout cancellation (no slam occurred → no visual).
- No particle system, shader, or animation is created in M11-10. The signal with correct data IS the placeholder.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-6a | `slam_vfx_requested` signal exists on `AttackExecutor` | Signal declaration check |
| CCA-6b | Signal emitted on successful slam with correct position | Argument check |
| CCA-6c | Signal carries `radius == 3.0` for carapace | Argument check |
| CCA-6d | Signal carries `Color.SADDLE_BROWN` for carapace | Argument check |
| CCA-6e | Signal carries `scale == 1.5` for carapace | Argument check |
| CCA-6f | Signal emitted even on whiff (no enemies hit) | Zero-enemy test |
| CCA-6g | Signal NOT emitted on timeout cancellation (airborne timeout) | Timeout test |

---

### CCA-7: Multi-Enemy Simultaneous Hit

**Description:** All enemies within the slam radius receive damage and knockback in the same handler execution. The knockback direction is radial — each enemy is pushed directly away from the player's position.

**Behavior rules:**

1. `_query_enemies_in_range()` returns ALL enemies within the radius (no cap on count).
2. Each enemy is processed in a single `for` loop — damage, knockback, modifiers, and signal emission.
3. Knockback direction is `"away"` — computed individually per enemy using `_calculate_knockback(enemy.global_position, owner_pos, magnitude, "away")`. Each enemy gets a knockback vector pointing from the player to the enemy (radially outward).
4. Enemies at the exact player position (degenerate case) receive knockback in the default direction `(1, 0, 0)` per AEX-5 degenerate handling.
5. Processing order is deterministic (order returned by `_query_enemies_in_range()`), but the spec does NOT guarantee any specific ordering.

**Constraints:**
- All enemies MUST be processed in a single pass — no enemies are skipped based on previous hits.
- Knockback is PER-ENEMY: two enemies at different positions relative to the player receive knockback in different directions.
- Dead enemies in the `"enemies"` group are handled by `_apply_damage` → `take_damage()` → `is_dead` guard on `EnemyBase`.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-7a | 3 enemies in radius → all 3 take damage | `take_damage` call count == 3 |
| CCA-7b | Knockback vector for enemy to the right of player points right (+X) | Vector direction check |
| CCA-7c | Knockback vector for enemy to the left of player points left (-X) | Vector direction check |
| CCA-7d | Knockback vector for enemy above player points up (+Y area, normalized) | Vector direction check |
| CCA-7e | Two enemies at different positions get different knockback directions | Per-enemy vector comparison |
| CCA-7f | Enemy at exact player position gets default knockback `(5.0, 0, 0)` | Degenerate case per AEX-5 |
| CCA-7g | Dead enemy in radius — `take_damage` called but `EnemyBase` guards against it | No error, dead enemy not damaged further |

---

### CCA-8: Integration with Existing Attack Pipeline

**Description:** The carapace attack integrates with the existing pipeline. The changes to shared code are:
1. New `"SLAM_AOE"` match arm in `execute_attack()` (CCA-5).
2. New `_handle_slam_aoe()` handler with `_is_owner_on_floor()` helper (CCA-3).
3. New `slam_vfx_requested` signal (CCA-6).
4. New constants for landing poll and timeout (CCA-3).

No changes to `_handle_melee_swipe()`, `_handle_projectile_spit()`, `_handle_unknown()`, `_apply_damage()`, `_apply_modifiers()`, `_calculate_knockback()`, `_query_enemies_in_range()`, or `_get_owner_position()`.

**Pipeline flow for carapace attack:**

```
Player presses J (attack input)
  → PlayerController3D._post_slide_housekeeping() checks input["attack_just_pressed"]
  → _try_attack()
    → State gate: PlayerInputActionPolicy.is_action_permitted(state, ACTION_ATTACK)
    → Mutation check: _mutation_slot.get_slot(0).get_active_mutation_id() == "carapace"
    → Cooldown check: _mutation_cooldowns.get("carapace", 0.0) <= 0.0
    → Database lookup: AttackDatabase.get_base_attack("carapace") → carapace AttackResource
    → Executor dispatch: _attack_executor.execute_attack(carapace_resource)
      → _is_active = true
      → attack_started.emit(carapace_resource)
      → match "SLAM_AOE" → _handle_slam_aoe(carapace_resource)
        → Wind-up: await 0.2s (12 / 60.0)
        → Airborne check: _is_owner_on_floor()?
          → YES → proceed to query
          → NO → poll every 50ms, timeout at 3.0s
        → Query: _query_enemies_in_range(player_pos, 3.0)
        → For each enemy:
          → knockback = _calculate_knockback(enemy_pos, player_pos, 5.0, "away")
          → _apply_damage(enemy, 4.0, knockback)
            → enemy.take_damage(4.0, knockback)
          → _apply_modifiers(enemy, {})
          → attack_hit.emit(enemy, resource)
        → slam_vfx_requested.emit(player_pos, 3.0, Color.SADDLE_BROWN, 1.5)
        → _is_active = false
      → return (handler owns lifecycle)
    → _mutation_cooldowns["carapace"] = 3.5
```

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CCA-8a | `_try_attack()` with carapace mutation active calls `get_base_attack("carapace")` | Database lookup verification |
| CCA-8b | `execute_attack()` dispatches to `_handle_slam_aoe()` for carapace | `effect_type == "SLAM_AOE"` routing |
| CCA-8c | Cooldown set to 3.5 after carapace attack | `_mutation_cooldowns["carapace"] == 3.5` |
| CCA-8d | Existing claw and acid tests continue to pass | `run_tests.sh` exits 0 |
| CCA-8e | No changes to `_handle_melee_swipe()` or `_handle_projectile_spit()` | Code diff verification |
| CCA-8f | No changes to `_try_attack()`, `_tick_controller_timers()`, or `_read_player_input()` | Code diff verification |

---

## 5. Frozen API Surface

### AttackExecutor additions

```gdscript
# New signal
signal slam_vfx_requested(position: Vector3, radius: float, color: Color, scale: float)

# New constants
const SLAM_LANDING_POLL_INTERVAL := 0.05
const SLAM_LANDING_TIMEOUT := 3.0

# New handler (internal)
func _handle_slam_aoe(resource: AttackResource) -> void

# New helper (internal)
func _is_owner_on_floor() -> bool
```

### AttackExecutor modification

```gdscript
# execute_attack() gains SLAM_AOE match arm:
"SLAM_AOE":
    _handle_slam_aoe(resource)
    return
```

### AttackDatabaseNode additions

```gdscript
const CARAPACE_DAMAGE := 4.0
const CARAPACE_COOLDOWN := 3.5
const CARAPACE_RANGE := 3.0
const CARAPACE_KNOCKBACK := 5.0
const CARAPACE_STARTUP_FRAMES := 12
const CARAPACE_VFX_SCALE := 1.5
```

### No new public methods on AttackExecutor.

### No changes to AttackResource, PlayerController3D, or EnemyBase.

---

## 6. Deferred Boundary

| Item | Owner | Notes |
|------|-------|-------|
| Actual VFX particles/animation for slam (ground crack, dust ring) | Future milestone | `slam_vfx_requested` signal exists; renderer connects later |
| Slam-specific attack animation state on player | Future milestone | No ATTACK_USE state in PSM yet |
| Camera shake on slam impact | Future milestone | Could connect to `slam_vfx_requested` signal |
| Fused attacks involving carapace (e.g., carapace+claw) | M12 | AttackDatabase supports fused lookup; no fused resources registered |
| Other base mutation registrations (adhesion) | M11-11 | Follow CCA-2 pattern in `_register_defaults()` |
| Slam damage falloff by distance (closer = more damage) | Not planned | All enemies in radius take equal damage |
| Ground detection via raycast (for non-CharacterBody3D) | Not planned | `is_on_floor()` is sufficient for player |
| Screen shake / controller rumble on slam | Future milestone | Deferred visual/haptic feedback |

---

## 7. Test Strategy

### Test scope

Unit tests with mock enemies (Node3D subclass with `take_damage()`, `get_base_state()` stubs) and mock parent (Node3D with `is_on_floor()`, `get_facing_sign()`, `global_position`). Scene-tree setup for AttackDatabase `_ready()` tests and timer-based delay tests. No actual Godot physics or collision detection.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_carapace_attack_behavior.gd` | Primary behavioral tests (CCA-1 through CCA-8) |
| `tests/scripts/attacks/test_carapace_attack_adversarial.gd` | Edge cases and adversarial deepening |

### Test categories

| Category | What to test | CCA Requirement |
|----------|-------------|-----------------|
| Registration | Carapace resource exists in DB with correct values | CCA-1, CCA-2 |
| Registration: properties | All AttackResource properties match spec | CCA-1 |
| Registration: _register_defaults | After `_ready()`: `has_base_attack("carapace")` true, count >= 3 | CCA-2 |
| SLAM_AOE dispatch | `execute_attack("SLAM_AOE")` routes to `_handle_slam_aoe` | CCA-5 |
| Radial query: center | Query centered on player position (not offset) | CCA-3 |
| Radial query: radius | Query uses full `attack_range` (not halved) | CCA-3 |
| Radial query: enemies in range | Enemies within 3.0 units hit | CCA-3, CCA-7 |
| Radial query: enemies out of range | Enemies beyond 3.0 units not hit | CCA-3 |
| Multi-enemy hit | 3+ enemies in range all take damage | CCA-7 |
| Knockback: radial away | Each enemy receives knockback away from player | CCA-7 |
| Knockback: degenerate | Enemy at player position → default (1,0,0) direction | CCA-7 |
| Wind-up delay | 0.2s timer before hitbox query | CCA-3 |
| Airborne: grounded | Slam fires immediately if on floor | CCA-4 |
| Airborne: deferred to landing | Slam waits and fires when is_on_floor() true | CCA-4 |
| Airborne: timeout cancellation | 3.0s timeout → slam cancelled, no damage | CCA-4 |
| Airborne: active guard during wait | Second attack blocked during airborne wait | CCA-4 |
| VFX signal: emission | `slam_vfx_requested` emitted with correct args | CCA-6 |
| VFX signal: whiff | Signal emitted with zero enemies | CCA-6 |
| VFX signal: timeout | Signal NOT emitted on timeout cancellation | CCA-6 |
| Cooldown | 3.5s cooldown set at button press | CCA-8 |
| Pipeline integration | Full flow: input → database → executor → damage + knockback | CCA-8 |
| Regression | Existing claw + acid tests unaffected | CCA-8 |

### Mock enemy contract (for tests)

```gdscript
extends Node3D

var damage_taken: Array = []
var current_state: int = 0  # NORMAL=0, WEAKENED=1, INFECTED=2
var is_dead_flag: bool = false

func take_damage(damage: float, knockback: Vector3) -> void:
    damage_taken.append({"damage": damage, "knockback": knockback})

func get_base_state() -> int:
    return current_state

func set_base_state(state: int) -> void:
    current_state = state

func is_dead() -> bool:
    return is_dead_flag
```

### Mock parent contract (for tests)

```gdscript
extends Node3D

var _on_floor: bool = true

func is_on_floor() -> bool:
    return _on_floor

func get_facing_sign() -> float:
    return 1.0
```

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | CCA Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | Slam with zero enemies in range | No damage, no modifiers, `slam_vfx_requested` still emitted | CCA-3, CCA-6 | VFX plays even on whiff |
| EC-2 | Slam with one enemy exactly at `attack_range` distance (3.0 units) | Enemy IS hit — `_query_enemies_in_range` uses `<=` comparison | CCA-3 | Inclusive boundary per existing implementation |
| EC-3 | Slam with one enemy at 3.001 units (just outside range) | Enemy NOT hit | CCA-3 | Outside radius |
| EC-4 | Slam with 10 enemies in range | All 10 take damage + knockback | CCA-7 | No cap on multi-hit |
| EC-5 | Slam while player is on floor (common case) | Immediate damage after 0.2s wind-up, no polling loop | CCA-4 | Standard grounded slam |
| EC-6 | Slam triggered mid-air, player lands 0.5s later | Slam fires 0.5s after wind-up completes (0.7s total from button press) | CCA-4 | Airborne deferral |
| EC-7 | Slam triggered mid-air, player never lands (timeout) | Slam cancelled after 3.2s (0.2s wind-up + 3.0s timeout), no damage | CCA-4 | Timeout prevents infinite hang |
| EC-8 | Slam triggered mid-air, second attack pressed during wait | Second attack rejected (`_is_active` is true) | CCA-4 | Active guard prevents overlap |
| EC-9 | Slam on dead enemy in enemies group | `take_damage` called but `EnemyBase.take_damage()` guards `_is_dead` | CCA-7 | Dead enemies are inert |
| EC-10 | Slam on target without `take_damage()` method | Damage silently skipped via `has_method` guard in `_apply_damage` | CCA-3 | Duck-type guard pattern |
| EC-11 | Slam with `startup_frames == 0` (hypothetical non-carapace SLAM_AOE) | No wind-up delay, immediate airborne check + damage | CCA-3 | Handler supports any startup value |
| EC-12 | Enemy moves into range during wind-up | Hit — query runs AFTER wind-up completes | CCA-3 | Query is point-in-time after delay |
| EC-13 | Enemy moves out of range during wind-up | Not hit — query runs AFTER wind-up | CCA-3 | Point-in-time query |
| EC-14 | Enemy moves into range during airborne wait | Hit — query runs at landing time | CCA-4 | Deferred query uses landing-time positions |
| EC-15 | Rapid slam presses within 3.5s cooldown | Only first fires; subsequent blocked by cooldown | CCA-8 | Per-mutation cooldown system |
| EC-16 | Slam with `knockback_magnitude == 0.0` (hypothetical) | No knockback, damage still applied | CCA-7 | `_calculate_knockback` returns ZERO for magnitude==0 |
| EC-17 | Two enemies at same position as player (degenerate) | Both get knockback in default direction (1,0,0) × magnitude | CCA-7 | AEX-5 degenerate handling |
| EC-18 | Slam while enemies in WEAKENED state | Damage + knockback applied; no special modifier (carapace has `{}`) | CCA-3 | Carapace is pure damage, no state transitions |
| EC-19 | Execute attack with `null` resource | `execute_attack` returns immediately (existing null guard) | CCA-5 | Defensive programming |
| EC-20 | Parent node has no `is_on_floor()` method | `_is_owner_on_floor()` returns `true` (treat as grounded) | CCA-4 | Conservative default |
| EC-21 | Executor not in scene tree during slam | `get_tree()` returns null → startup timer skipped; airborne check defaults to grounded; `_query_enemies_in_range` returns [] → whiff | CCA-3 | Testability: unit tests run without full scene tree |
| EC-22 | Slam + melee_vfx_requested — only slam signal should emit | `melee_vfx_requested` NOT emitted by `_handle_slam_aoe()` | CCA-6 | Distinct signals for distinct effect types |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| `execute_attack()` change (SLAM_AOE return) could introduce subtle `_is_active` bugs for existing handlers | High | SLAM_AOE is the only arm with `return`. Existing arms fall through to `_is_active = false` unchanged. Regression tests verify claw/acid behavior. |
| Airborne polling loop could miss a single-frame landing | Low | 50ms poll interval is well below typical physics frame (16.7ms at 60fps). Even if a frame is missed, the next poll catches it. |
| 3.0s timeout may feel too long or too short for gameplay | Low | Timeout is a named constant (`SLAM_LANDING_TIMEOUT`), trivially tunable. 3.0s covers any reasonable jump arc. |
| `_is_active` held during airborne wait blocks ALL attacks (not just carapace) | Medium — by design | This is intentional: the player committed to the slam. The active guard prevents exploits where airborne slam + instant claw fire simultaneously. The 3.0s timeout ensures the player isn't locked out forever. |
| Cooldown starts at button press, not at impact | Low | Consistent with claw/acid. The 3.5s cooldown value already accounts for the 0.2s wind-up. |
| `_query_enemies_in_range` iterates ALL enemies group nodes | Low | Expected to have < 20 enemies per room. Linear scan is acceptable. |
| `Color.SADDLE_BROWN` may not be the ideal carapace color | Very low | Color is a placeholder, tunable via the constant. The spec contract is "distinct from claw (ORANGE_RED) and acid (CHARTREUSE)." |

---

## 10. Clarifying Questions

All ambiguities resolved via discrepancy resolutions and planning checkpoint:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Should slam query center on player or offset by facing? | Player center — omnidirectional (CCA-DR-1) | High |
| Should wind-up use `startup_frames` or new field? | `startup_frames = 12` — reuses existing field (CCA-DR-2) | High |
| Should airborne deferral be in executor or controller? | Executor-internal — self-contained, no controller changes (CCA-DR-3) | High |
| Should slam reuse `melee_vfx_requested` or new signal? | New `slam_vfx_requested` with `radius` parameter (CCA-DR-4) | High |
| When does cooldown start? | At button press — existing behavior, consistent with all attacks (CCA-DR-5) | High |
| How does async `_handle_slam_aoe()` interact with `_is_active`? | Handler owns its lifecycle; `execute_attack()` returns after dispatch (CCA-DR-6) | High |
| What is the slam damage value? | 4.0 — heaviest single-hit base mutation (claw=3.0, acid=1.0) | High |
| What is the knockback magnitude? | 5.0 — strong push, thematic for heavy slam (claw=2.0) | High |
| What color for carapace? | `Color.SADDLE_BROWN` — distinct from claw (ORANGE_RED) and acid (CHARTREUSE) | Medium |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| Slam hitbox activates in a radius around the player (configurable, default 3.0 units) | CCA-1 (`attack_range = 3.0`), CCA-3 (radial query) | Registration: properties, Radial query: center/radius/in/out |
| All enemies within radius take damage and receive knockback away from the player | CCA-3 (per-enemy processing), CCA-7 (multi-enemy hit) | Multi-enemy hit, Knockback: radial away |
| Slam has a brief wind-up before the hitbox activates (0.2s) | CCA-1 (`startup_frames = 12`), CCA-3 (wind-up delay) | Wind-up delay |
| Attack cooldown: 3.5s | CCA-1 (`cooldown = 3.5`), CCA-8 (pipeline integration) | Registration: properties, Cooldown |
| If player is airborne, slam triggers on landing | CCA-4 (airborne deferral) | Airborne: grounded, deferred to landing, timeout |
| `run_tests.sh` exits 0 | CCA-8 (regression) | Regression |
