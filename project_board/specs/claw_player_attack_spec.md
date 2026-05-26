# SPEC: Claw Player Attack

**Ticket:** M11-08 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/08_claw_player_attack.md`)  
**Spec ID:** CPA  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-26

---

## 1. Overview

The claw mutation attack is a fast melee swipe that leverages the existing `MELEE_SWIPE` pipeline (AttackExecutor, AttackDatabase, PlayerController3D cooldown). This ticket registers a claw-specific `AttackResource` with tuned values and adds a **claw-specific post-hit modifier** (`"infect_weakened"`) that transitions WEAKENED enemies to INFECTED. No changes to generic executor dispatch or melee handler are required — the claw attack flows through the existing `execute_attack → _handle_melee_swipe → _apply_damage → _apply_modifiers` pipeline. The only executor extension is a new modifier handler branch in `_apply_modifiers()`.

**Key design principle:** Claw is the first concrete mutation registration in the AttackDatabase. The registration pattern must be clean and reusable for acid, adhesion, and carapace attacks.

**Files modified:**
- `scripts/attacks/attack_database.gd` — add `_register_defaults()` with claw registration
- `scripts/attacks/attack_executor.gd` — add `"infect_weakened"` modifier handler in `_apply_modifiers()`

**Files unmodified:**
- `scripts/attacks/attack_resource.gd` — frozen (M11-04)
- `scripts/player/player_controller_3d.gd` — attack pipeline already wired (M11-06)
- `scripts/enemies/enemy_base.gd` — `take_damage()`, `set_base_state()`, `get_base_state()` already exist (M11-14)

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/08_claw_player_attack.md` | Acceptance criteria, remaining work |
| Planning checkpoint | `project_board/checkpoints/M11-08/2026-05-26T-plan-run.md` | Execution plan, risk register, 2 assumptions |
| AttackResource spec | `project_board/specs/attack_resource_spec.md` | Frozen data model (15 properties, modifiers contract) |
| AttackExecutor spec | `project_board/specs/attack_executor_spec.md` | Dispatch contract, `_apply_modifiers()` (AEX-6), signals |
| AttackDatabase spec | `project_board/specs/attack_database_integration_spec.md` | Registration API, `_try_attack()` pipeline (ADB-3, ADB-7) |
| Cooldown spec | `project_board/specs/cooldown_cross_state_behavior_spec.md` | Per-mutation cooldown behavior (CDB-1..CDB-5) |
| AttackResource impl | `scripts/attacks/attack_resource.gd` | Frozen class — 15 exports including `modifiers: Dictionary` |
| AttackExecutor impl | `scripts/attacks/attack_executor.gd` | `_handle_melee_swipe()`, `_apply_modifiers()`, `melee_vfx_requested` signal |
| AttackDatabase impl | `scripts/attacks/attack_database.gd` | `register_base_attack()`, `get_base_attack()`, `_base_attacks` dict |
| EnemyBase impl | `scripts/enemies/enemy_base.gd` | `State` enum, `take_damage()`, `set_base_state()`, `get_base_state()`, `WEAKENED_HP_THRESHOLD` |
| PlayerController3D impl | `scripts/player/player_controller_3d.gd` | `_try_attack()`, `_mutation_cooldowns`, `_tick_controller_timers()` |
| EnemyAIController impl | `scripts/enemies/enemy_ai_controller.gd` | `on_chunk_infect()` — existing WEAKENED→INFECTED via chunk system |

---

## 3. Discrepancy Resolutions

### CPA-DR-1: WEAKENED→INFECTED mechanism — modifier vs post-hit callback vs executor extension

**Problem:** The ticket says the WEAKENED→INFECTED transition is "claw-specific" and should "not be in the generic executor." Three approaches are viable: (a) a dedicated modifier key checked in `_apply_modifiers()`, (b) a post-hit signal handler on the claw resource, (c) an override in a subclassed executor.

**Evidence:**
- `_apply_modifiers()` already handles poison, acid, and slow via `has_method()` guards on the target.
- The `attack_hit` signal exists but connecting a handler to it would require scene-tree wiring external to the executor.
- Subclassing AttackExecutor would break the single-instance pattern in PlayerController3D.

**Resolution:** Use approach (a): a new modifier key `"infect_weakened": true` in the claw resource's modifiers dictionary, with a corresponding handler branch added to `_apply_modifiers()`. This is:
- **Consistent** with existing modifier patterns (poison, acid, slow).
- **Minimal** — one new branch in an existing function.
- **Reusable** — other mutations could set `"infect_weakened": true` if desired.
- **Claw-specific** via the resource's modifiers dict, not via executor dispatch changes.

The handler checks `target.get_base_state() == EnemyBase.State.WEAKENED` using `has_method("get_base_state")` and `has_method("set_base_state")` guards, then calls `target.set_base_state(EnemyBase.State.INFECTED)`. This matches the `enemy_ai_controller.gd:on_chunk_infect()` pattern.

### CPA-DR-2: Same-hit weaken+infect ambiguity

**Problem:** If a claw hit drops an enemy from NORMAL to WEAKENED (via HP threshold in `take_damage() → _check_weakened_threshold()`), should that same hit also trigger the WEAKENED→INFECTED transition via the modifier?

**Evidence:**
- `_handle_melee_swipe()` calls `_apply_damage()` BEFORE `_apply_modifiers()` (line 57-58 of `attack_executor.gd`).
- `take_damage()` calls `_check_weakened_threshold()` synchronously during damage application.
- Therefore, by the time `_apply_modifiers()` runs, the enemy's state has already been updated to WEAKENED if the HP threshold was crossed.

**Resolution:** **No** — a single claw hit MUST NOT both weaken and infect in the same hit. The `infect_weakened` modifier handler checks the enemy's state **before the current hit's damage was applied** by design. However, since `_apply_damage` runs before `_apply_modifiers` in the existing pipeline, the state will already reflect the post-damage WEAKENED transition.

To enforce the two-hit requirement, the `infect_weakened` modifier handler must track whether the enemy was WEAKENED **before** `_apply_damage` ran. The implementation approach: `_handle_melee_swipe()` captures each enemy's pre-damage state before calling `_apply_damage()`, then passes that pre-damage state information to `_apply_modifiers()`. Specifically, the modifiers dictionary passed to `_apply_modifiers()` will include a runtime key `"_pre_hit_states"` mapping each target to its pre-damage state. The `infect_weakened` handler checks the pre-hit state, not the current (post-damage) state.

**Alternative (simpler):** Add a `pre_hit_state` parameter to `_apply_modifiers()` so it can check the state before damage was applied. This avoids polluting the modifiers dictionary with runtime data.

**Frozen decision:** Add a `pre_damage_state` parameter to `_apply_modifiers()`:

```gdscript
func _apply_modifiers(target: Node3D, modifiers: Dictionary, pre_damage_state: int = -1) -> void
```

The `infect_weakened` handler checks `pre_damage_state == EnemyBase.State.WEAKENED` (value `1`). If `pre_damage_state` is `-1` (default, for backward compatibility with projectile calls), it falls back to checking `target.get_base_state()`. In `_handle_melee_swipe()`, before the per-enemy loop, capture each enemy's state; pass it to `_apply_modifiers()`.

### CPA-DR-3: Registration site — _register_defaults() vs external caller

**Problem:** No mutations are currently registered in AttackDatabase. The planner assumed a `_register_defaults()` method on AttackDatabaseNode called from `_ready()`.

**Evidence:** `attack_database.gd` has no `_ready()` method and no `_register_defaults()`. All existing tests use the code-registration API (`register_base_attack()`).

**Resolution:** Add a `_ready()` method to `AttackDatabaseNode` that calls `_register_defaults()`. This colocates all base attack definitions in one place. The method creates and registers each mutation's AttackResource with hardcoded tuning values. This is the first registration; acid/adhesion/carapace will follow the same pattern.

### CPA-DR-4: VFX placeholder scope

**Problem:** The ticket requires "VFX/animation placeholder for claw swipe." The existing `melee_vfx_requested` signal already emits on every melee execution (hit or miss) with `(position, color, scale)`. No actual particle or mesh system exists.

**Evidence:** `attack_executor.gd` line 61: `melee_vfx_requested.emit(center, resource.color, resource.vfx_scale)`. No VFXManager exists.

**Resolution:** The VFX placeholder requirement is satisfied by:
1. Setting `color` and `vfx_scale` on the claw AttackResource to distinguishable values (e.g., `Color.ORANGE_RED`, scale `1.2`).
2. The existing `melee_vfx_requested` signal emission — any future VFX system connects to this signal.
3. No new particle system, mesh flash, or animation controller is required for M11-08. The signal with configured parameters IS the placeholder.

---

## 4. Requirements

### CPA-1: Claw AttackResource Definition

**Description:** A claw-specific `AttackResource` instance with tuned combat parameters is created and registered in the AttackDatabase under mutation_id `"claw"`.

**Property values:**

| Property | Value | Rationale |
|----------|-------|-----------|
| `attack_id` | `1` | First registered base attack |
| `attack_name` | `"Claw Swipe"` | Descriptive name for UI |
| `description` | `"Fast melee swipe with short cooldown. Infects weakened enemies."` | UI tooltip |
| `effect_type` | `"MELEE_SWIPE"` | Routes to existing `_handle_melee_swipe()` |
| `damage` | `3.0` | Moderate damage per ticket ("~3.0") |
| `cooldown` | `0.8` | Shortest mutation cooldown per ticket |
| `attack_range` | `1.5` | Short melee range per ticket ("~1.5 units") |
| `startup_frames` | `0` | Instant — no startup delay for fast attacks |
| `knockback_magnitude` | `2.0` | Light push to give positional feedback |
| `knockback_direction` | `"away"` | Push enemies away from player |
| `projectile_speed` | `0.0` | N/A for melee |
| `projectile_lifetime` | `2.0` | Default — unused for melee |
| `color` | `Color.ORANGE_RED` | VFX placeholder color (claw = aggressive/warm) |
| `vfx_scale` | `1.2` | Slightly larger than default (1.0) for visual emphasis |
| `modifiers` | `{"infect_weakened": true}` | Triggers WEAKENED→INFECTED on hit (CPA-DR-1) |

**Constraints:**
- `effect_type` MUST be `"MELEE_SWIPE"` to reuse the existing melee pipeline.
- `modifiers` MUST contain `"infect_weakened": true` as the only modifier key.
- `cooldown` MUST be `0.8` (ticket requirement: "shortest of all mutations").
- `attack_range` MUST be `1.5` (ticket requirement).
- `damage` MUST be `3.0`.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-1a | AttackResource with `effect_type == "MELEE_SWIPE"` exists for claw | `db.get_base_attack("claw").effect_type == "MELEE_SWIPE"` |
| CPA-1b | `damage == 3.0` | `db.get_base_attack("claw").damage == 3.0` |
| CPA-1c | `cooldown == 0.8` | `db.get_base_attack("claw").cooldown == 0.8` |
| CPA-1d | `attack_range == 1.5` | `db.get_base_attack("claw").attack_range == 1.5` |
| CPA-1e | `knockback_magnitude == 2.0` | Property check |
| CPA-1f | `knockback_direction == "away"` | Property check |
| CPA-1g | `modifiers` contains `"infect_weakened": true` | `db.get_base_attack("claw").modifiers.get("infect_weakened", false) == true` |
| CPA-1h | `startup_frames == 0` | Property check (instant attack) |
| CPA-1i | `color == Color.ORANGE_RED` | Property check (VFX placeholder) |
| CPA-1j | `vfx_scale == 1.2` | Property check |

---

### CPA-2: AttackDatabase Registration Site

**Description:** `AttackDatabaseNode` gains a `_ready()` method that calls `_register_defaults()`, which creates and registers the claw AttackResource. This establishes the canonical registration pattern for all future base mutation attacks.

**Implementation pattern:**

```gdscript
func _ready() -> void:
    _register_defaults()

func _register_defaults() -> void:
    var claw := AttackResource.new()
    claw.attack_id = 1
    claw.attack_name = "Claw Swipe"
    claw.description = "Fast melee swipe with short cooldown. Infects weakened enemies."
    claw.effect_type = "MELEE_SWIPE"
    claw.damage = 3.0
    claw.cooldown = 0.8
    claw.attack_range = 1.5
    claw.startup_frames = 0
    claw.knockback_magnitude = 2.0
    claw.knockback_direction = "away"
    claw.color = Color.ORANGE_RED
    claw.vfx_scale = 1.2
    claw.modifiers = {"infect_weakened": true}
    register_base_attack("claw", claw)
```

**Constraints:**
- `_register_defaults()` MUST be called from `_ready()` so attacks are available when the scene tree initializes.
- `_register_defaults()` MUST be a separate method (not inline in `_ready()`) for readability and to establish the pattern for future mutations.
- Future mutation registrations (acid, adhesion, carapace) will be added as additional blocks within `_register_defaults()`.
- Existing tests that call `register_base_attack()` directly are NOT affected because they create their own `AttackDatabaseNode` instances (not autoloaded).

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-2a | `AttackDatabaseNode._ready()` exists and calls `_register_defaults()` | Code inspection |
| CPA-2b | `_register_defaults()` registers claw attack via `register_base_attack("claw", ...)` | After `_ready()`, `has_base_attack("claw")` returns `true` |
| CPA-2c | `get_base_attack_count()` returns at least 1 after `_ready()` | Count check |
| CPA-2d | Existing tests that manually register attacks are not broken | `run_tests.sh` exits 0 |

---

### CPA-3: WEAKENED→INFECTED Modifier (`infect_weakened`)

**Description:** A new modifier handler is added to `AttackExecutor._apply_modifiers()` that transitions WEAKENED enemies to INFECTED state when the `"infect_weakened"` modifier flag is present.

**Modified signature:**

```gdscript
func _apply_modifiers(target: Node3D, modifiers: Dictionary, pre_damage_state: int = -1) -> void
```

**New parameter:**
- `pre_damage_state: int` — the enemy's `EnemyBase.State` value captured BEFORE `_apply_damage()` was called. Default `-1` means "not provided" (backward compat for projectile calls).

**Handler logic (appended after existing slow handler):**

```gdscript
if modifiers.get("infect_weakened", false):
    if target.has_method("get_base_state") and target.has_method("set_base_state"):
        var check_state: int = pre_damage_state if pre_damage_state >= 0 else -1
        if check_state < 0 and target.has_method("get_base_state"):
            check_state = target.get_base_state()
        if check_state == 1:  # EnemyBase.State.WEAKENED
            target.set_base_state(2)  # EnemyBase.State.INFECTED
```

**Behavior rules:**

1. If `modifiers.get("infect_weakened", false)` is falsy, skip entirely.
2. If the target does not have `get_base_state()` or `set_base_state()`, skip silently (`has_method()` guard).
3. If `pre_damage_state >= 0`, use it as the state to check. This is the pre-damage snapshot captured by `_handle_melee_swipe()`.
4. If `pre_damage_state == -1` (default, e.g., projectile path), fall back to `target.get_base_state()` (current state).
5. Transition only if the checked state equals `WEAKENED` (int value `1`).
6. If the enemy is NORMAL, INFECTED, or dead — no transition, no error.

**Two-hit invariant (CPA-DR-2):**
A single claw hit that drops an enemy from NORMAL to WEAKENED (via `_check_weakened_threshold()` in `take_damage()`) does NOT also infect in the same hit. The `pre_damage_state` parameter ensures the modifier checks the enemy's state from before the damage was applied. Since the enemy was NORMAL pre-damage, the `infect_weakened` check sees NORMAL (not WEAKENED) and skips.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-3a | Enemy in WEAKENED state before hit → transitions to INFECTED after claw hit | `target.get_base_state() == EnemyBase.State.INFECTED` |
| CPA-3b | Enemy in NORMAL state before hit → stays NORMAL (or becomes WEAKENED via HP only, NOT INFECTED) | `target.get_base_state() != EnemyBase.State.INFECTED` |
| CPA-3c | Enemy already INFECTED → no change, no error | State unchanged, no crash |
| CPA-3d | Dead enemy → no transition, no error | `is_dead() == true`, state unchanged |
| CPA-3e | Target without `get_base_state()`/`set_base_state()` → silently skipped | No crash on bare Node3D |
| CPA-3f | Two-hit pattern: first hit weakens (NORMAL→WEAKENED via HP), second hit infects (WEAKENED→INFECTED via modifier) | Sequence verified |
| CPA-3g | Same-hit weaken+infect blocked: single hit that crosses WEAKENED threshold does NOT also infect | `pre_damage_state == NORMAL`, modifier skips |
| CPA-3h | Other modifiers (poison, acid, slow) still function independently alongside `infect_weakened` | Multi-modifier test |
| CPA-3i | Resource without `"infect_weakened"` key → no infection behavior | Default `{}` modifiers, no state change |

---

### CPA-4: Pre-Damage State Capture in Melee Handler

**Description:** `_handle_melee_swipe()` is modified to capture each enemy's state before calling `_apply_damage()`, and pass that state to `_apply_modifiers()` via the new `pre_damage_state` parameter.

**Modified flow in `_handle_melee_swipe()`:**

```gdscript
for enemy in enemies:
    var pre_state: int = -1
    if enemy.has_method("get_base_state"):
        pre_state = enemy.get_base_state()
    var kb := _calculate_knockback(...)
    _apply_damage(enemy, resource.damage, kb)
    _apply_modifiers(enemy, resource.modifiers, pre_state)
    attack_hit.emit(enemy, resource)
```

**Constraints:**
- `pre_state` is captured BEFORE `_apply_damage()` via `has_method("get_base_state")` guard.
- If the target has no `get_base_state()`, `pre_state` remains `-1` and `_apply_modifiers()` falls back to current state check.
- The projectile path (`PlayerProjectile3D`) does NOT pass `pre_damage_state` — it uses the default `-1`, so `infect_weakened` falls back to `target.get_base_state()` (post-damage). This is acceptable because projectiles should NOT have the `infect_weakened` modifier.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-4a | Pre-damage state is captured before `_apply_damage()` in melee loop | Code path verification via test: enemy starts NORMAL, takes enough damage to cross WEAKENED threshold, `infect_weakened` modifier sees NORMAL pre-state |
| CPA-4b | `_apply_modifiers()` receives the pre-damage state | Modifier behavior verified via CPA-3 tests |
| CPA-4c | Targets without `get_base_state()` get `pre_state == -1` | No crash on bare Node3D targets |
| CPA-4d | Existing modifier behavior (poison, acid, slow) is unaffected by the new parameter | Regression tests pass |

---

### CPA-5: Single-Frame Hitbox Semantics

**Description:** The claw attack's hitbox is active for exactly one frame (one call to `_handle_melee_swipe()`). This is NOT new behavior — it is an inherent property of the existing `MELEE_SWIPE` handler, which performs a single spatial query and returns. There is no persistent hitbox, no Area3D, and no multi-frame overlap.

**Existing guarantees (from AEX-3):**
- `_handle_melee_swipe()` runs to completion in a single call (no await when `startup_frames == 0`).
- The spatial query (`_query_enemies_in_range`) is a point-in-time check.
- Each enemy in range is hit exactly once per `execute_attack()` call.
- The executor's `_is_active` flag prevents overlapping executions.

**Claw-specific constraints:**
- `startup_frames == 0` → no timer, no await, fully synchronous.
- Per-mutation cooldown (`0.8s`) prevents re-execution within the cooldown window.
- A single button press → one `_try_attack()` call → one `execute_attack()` call → one `_handle_melee_swipe()` call → one hitbox query.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-5a | Single claw attack press hits each in-range enemy exactly once | Count `take_damage` calls on mock enemy |
| CPA-5b | Rapid presses within cooldown (0.8s) are rejected | `_mutation_cooldowns["claw"] > 0.0` blocks second attack |
| CPA-5c | No persistent hitbox exists after the attack completes | No Area3D created, no timer running |
| CPA-5d | Enemy moving into previous attack position after completion is not hit | Spatial query is point-in-time |

---

### CPA-6: VFX Placeholder

**Description:** The claw attack uses the existing `melee_vfx_requested` signal as its VFX placeholder. The signal emits on every melee execution (hit or miss) with the claw resource's `color` and `vfx_scale` parameters.

**Signal emission (already implemented in AEX-7):**

```gdscript
melee_vfx_requested.emit(center, resource.color, resource.vfx_scale)
```

For claw: `melee_vfx_requested.emit(center, Color.ORANGE_RED, 1.2)`.

**What constitutes "visual indication" for M11-08:**
- The `melee_vfx_requested` signal emission with claw-specific color and scale parameters.
- Any future VFX system connects to this signal to render particles, mesh flashes, etc.
- No particle system, shader, or animation is created in this ticket.

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-6a | `melee_vfx_requested` signal emitted on claw attack | Signal monitoring in test |
| CPA-6b | Signal carries `Color.ORANGE_RED` as color argument | Argument check |
| CPA-6c | Signal carries `1.2` as scale argument | Argument check |
| CPA-6d | Signal emitted even on whiff (no enemies hit) | Test with zero enemies in range |

---

### CPA-7: Integration with Existing Pipeline (No Generic Changes)

**Description:** The claw attack integrates fully with the existing attack pipeline without modifying the generic dispatch, cooldown, or input systems. The only changes to shared code are:
1. A new modifier branch in `_apply_modifiers()` (CPA-3).
2. A new parameter on `_apply_modifiers()` signature (CPA-4).
3. Pre-damage state capture in `_handle_melee_swipe()` (CPA-4).

**Pipeline flow for claw attack:**

```
Player presses J (attack input)
  → PlayerController3D._post_slide_housekeeping() checks input["attack_just_pressed"]
  → _try_attack()
    → State gate: PlayerInputActionPolicy.is_action_permitted(state, ACTION_ATTACK)
    → Mutation check: _mutation_slot.get_slot(0).get_active_mutation_id() == "claw"
    → Cooldown check: _mutation_cooldowns.get("claw", 0.0) <= 0.0
    → Database lookup: AttackDatabase.get_base_attack("claw") → claw AttackResource
    → Executor dispatch: _attack_executor.execute_attack(claw_resource)
      → _handle_melee_swipe(claw_resource)
        → Capture pre-damage state for each enemy
        → _apply_damage(enemy, 3.0, knockback)
          → enemy.take_damage(3.0, knockback) → HP decreases, may trigger WEAKENED
        → _apply_modifiers(enemy, {"infect_weakened": true}, pre_state)
          → infect_weakened handler: if pre_state == WEAKENED → set_base_state(INFECTED)
        → attack_hit.emit(enemy, resource)
      → melee_vfx_requested.emit(center, Color.ORANGE_RED, 1.2)
    → _mutation_cooldowns["claw"] = 0.8
```

**Acceptance Criteria:**

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| CPA-7a | `_try_attack()` with claw mutation active calls `get_base_attack("claw")` | Mock database verification |
| CPA-7b | `execute_attack()` dispatches to `_handle_melee_swipe()` for claw | `effect_type == "MELEE_SWIPE"` routing |
| CPA-7c | Cooldown set to 0.8 after claw attack | `_mutation_cooldowns["claw"] == 0.8` |
| CPA-7d | Existing 69+ attack tests continue to pass | `run_tests.sh` exits 0 |
| CPA-7e | No changes to `_handle_projectile_spit()`, `_handle_unknown()`, or dispatch `match` | Code diff verification |
| CPA-7f | No changes to `_try_attack()`, `_tick_controller_timers()`, or `_read_player_input()` | Code diff verification |

---

## 5. Frozen API Surface

### AttackDatabaseNode additions

```gdscript
func _ready() -> void
func _register_defaults() -> void
```

### AttackExecutor modifications

```gdscript
# Modified signature (backward compatible via default parameter):
func _apply_modifiers(target: Node3D, modifiers: Dictionary, pre_damage_state: int = -1) -> void
```

### No new public methods or signals.

---

## 6. Deferred Boundary

| Item | Owner | Notes |
|------|-------|-------|
| Actual VFX particles/animation for claw | Future milestone | Signal exists; renderer connects later |
| Claw-specific attack animation state on player | Future milestone | No ATTACK_USE state in PSM yet |
| Fused attacks involving claw (e.g., claw+acid) | M12 | AttackDatabase supports fused lookup; no fused resources registered |
| Other base mutation registrations (acid, adhesion, carapace) | M11-09, M11-10, M11-11 | Follow CPA-2 pattern in `_register_defaults()` |
| `EnemyBase` integration tests with real scene tree | M11-08 Task 5 | AC Gatekeeper verifies end-to-end |
| `PlayerProjectile3D` infect_weakened support | Not planned | Projectiles should not infect; modifier key is on claw resource only |

---

## 7. Test Strategy

### Test scope

Unit tests with mock enemies (Node3D subclass with `take_damage()`, `get_base_state()`, `set_base_state()` stubs). Scene-tree setup for AttackDatabase `_ready()` tests. No actual Godot physics or collision detection.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/attacks/test_claw_attack_behavior.gd` | Primary behavioral tests (CPA-1 through CPA-7) |
| `tests/scripts/attacks/test_claw_attack_adversarial.gd` | Edge cases and adversarial deepening |

### Test categories

| Category | What to test | CPA Requirement |
|----------|-------------|-----------------|
| Registration | Claw resource exists in DB with correct values | CPA-1, CPA-2 |
| Registration: properties | All 15 AttackResource properties match spec | CPA-1 |
| Registration: _register_defaults | `_ready()` → `_register_defaults()` → `has_base_attack("claw")` | CPA-2 |
| Infect modifier: WEAKENED→INFECTED | Claw hit on WEAKENED enemy → state becomes INFECTED | CPA-3 |
| Infect modifier: NORMAL enemy | Claw hit on NORMAL → no infection (may weaken via HP only) | CPA-3 |
| Infect modifier: already INFECTED | No change, no crash | CPA-3 |
| Infect modifier: dead enemy | No change, no crash | CPA-3 |
| Infect modifier: bare target | Target without state methods → silently skipped | CPA-3 |
| Two-hit pattern | First hit weakens, second infects | CPA-3, CPA-4 |
| Same-hit block | Single hit crossing WEAKENED threshold does NOT also infect | CPA-3, CPA-4 |
| Pre-damage state | State captured before `_apply_damage()` | CPA-4 |
| Single-frame hitbox | One press → one hit per enemy | CPA-5 |
| Cooldown rejection | Rapid presses within 0.8s blocked | CPA-5 |
| VFX signal | `melee_vfx_requested` emitted with correct args | CPA-6 |
| VFX on whiff | Signal emitted even with zero enemies | CPA-6 |
| Pipeline integration | Full flow: input → database → executor → damage + modifier | CPA-7 |
| Regression | Existing attack tests unaffected | CPA-7 |

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

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | CPA Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | Claw hit on NORMAL enemy, HP stays above WEAKENED threshold | Damage applied, state stays NORMAL, no infection | CPA-3 | Standard non-weakening hit |
| EC-2 | Claw hit on NORMAL enemy, HP drops below WEAKENED threshold | Damage applied, state becomes WEAKENED (via `_check_weakened_threshold`), NOT INFECTED (pre-state was NORMAL) | CPA-3, CPA-4 | Two-hit invariant (CPA-DR-2) |
| EC-3 | Claw hit on WEAKENED enemy | Damage applied, state transitions to INFECTED via `infect_weakened` modifier | CPA-3 | Core claw behavior |
| EC-4 | Claw hit on INFECTED enemy | Damage applied, state unchanged (already INFECTED) | CPA-3 | No double-infection |
| EC-5 | Claw hit on dead enemy | No damage (EnemyBase.take_damage guards `_is_dead`), no state change | CPA-3 | Dead enemies are inert |
| EC-6 | Claw hit on target without `get_base_state()` | Modifier silently skipped, damage still applied via `has_method("take_damage")` | CPA-3 | Duck-type guard pattern |
| EC-7 | Claw hit on target without `take_damage()` | Damage skipped, modifier skipped (no state methods either) | CPA-3 | Bare Node3D in enemies group |
| EC-8 | Two claw hits in sequence on NORMAL enemy with enough damage to weaken | First hit: damage → NORMAL→WEAKENED. Second hit: damage → WEAKENED→INFECTED | CPA-3 | Two-hit infection pattern |
| EC-9 | Rapid claw presses within 0.8s cooldown | Only first press triggers attack; subsequent blocked by cooldown | CPA-5 | Per existing cooldown system |
| EC-10 | Claw attack with zero enemies in range | No damage, no modifiers, `melee_vfx_requested` still emitted | CPA-5, CPA-6 | Whiff behavior |
| EC-11 | Multiple enemies in melee range, mixed states | Each enemy processed independently; WEAKENED ones → INFECTED, others unaffected | CPA-3 | Per-enemy state check |
| EC-12 | `AttackDatabaseNode._ready()` called multiple times | Claw resource overwrites itself (last-write-wins per ADB-3); no error | CPA-2 | Idempotent registration |
| EC-13 | Test registers custom attack with `mutation_id="claw"` after `_ready()` | Custom resource overwrites default; tests can override | CPA-2 | Supports test isolation |
| EC-14 | Claw resource has both `infect_weakened` and `poison` modifiers | Both fire independently; infection check + poison application | CPA-3 | Modifier independence (AEX-6) |
| EC-15 | `pre_damage_state` is `-1` (projectile path fallback) and enemy is WEAKENED | Falls back to `target.get_base_state()` which returns WEAKENED → infects | CPA-4 | Backward compat for projectile; but projectiles should not have `infect_weakened` modifier |
| EC-16 | `infect_weakened` modifier key is absent from resource modifiers | No infection behavior; existing modifier handlers fire normally | CPA-3 | Default AttackResource has `{}` modifiers |
| EC-17 | Enemy transitions NORMAL→WEAKENED from a non-claw source, then claw hits | Claw's pre-state capture sees WEAKENED → infects on first claw hit | CPA-3, CPA-4 | Cross-attack interaction |
| EC-18 | `_apply_modifiers` called directly with `pre_damage_state = 1` (WEAKENED) on a NORMAL enemy | Infects based on `pre_damage_state`, not current state | CPA-4 | Parameter takes precedence |

---

## 9. Risk & Ambiguity Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| `_apply_modifiers()` signature change breaks existing callers | High | Default parameter `pre_damage_state: int = -1` ensures backward compatibility. Projectile path continues to work without changes. |
| `_register_defaults()` auto-registers in tests that instantiate `AttackDatabaseNode` | Medium | Tests that need an empty database create `AttackDatabaseNode.new()` then call `clear()`. Or tests that verify specific registrations can check after `_ready()`. |
| `EnemyBase.State` integer values used directly (0, 1, 2) instead of enum names | Low | Necessary because `_apply_modifiers` receives the target as `Node3D` and cannot reference `EnemyBase.State` enum without a cast. The values are stable per `enemy_base.gd` line 23. |
| Same-hit weaken+infect race condition | High | Explicitly addressed by `pre_damage_state` parameter (CPA-DR-2). Test verifies the invariant. |
| Future mutations adding `"infect_weakened": true` to their modifiers | Low | By design — the modifier is reusable. If another mutation should infect, it adds the key. If not, it omits it. |

---

## 10. Clarifying Questions

All ambiguities resolved via discrepancy resolutions and planning checkpoint:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Where does WEAKENED→INFECTED logic live? | `_apply_modifiers()` with new `"infect_weakened"` modifier key (CPA-DR-1) | High |
| Can a single hit both weaken and infect? | No — `pre_damage_state` parameter ensures two-hit pattern (CPA-DR-2) | High |
| Where are attacks registered? | `AttackDatabaseNode._register_defaults()` called from `_ready()` (CPA-DR-3) | High |
| What is the VFX placeholder? | Existing `melee_vfx_requested` signal with claw-specific color/scale (CPA-DR-4) | High |
| Does claw modify the generic executor? | Only `_apply_modifiers()` gains a new branch and parameter; dispatch/melee handler logic unchanged | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| Swipe hitbox activates in front of player (~1.5 units) | CPA-1 (`attack_range = 1.5`), CPA-5 | Registration: properties, Single-frame hitbox |
| Swipe animation plays (VFX placeholder acceptable) | CPA-6 | VFX signal, VFX on whiff |
| On hit, enemy takes damage | CPA-7 (pipeline integration) | Pipeline integration |
| WEAKENED enemy → INFECTED on claw hit | CPA-3 | Infect modifier: WEAKENED→INFECTED |
| Attack cooldown: 0.8s | CPA-1 (`cooldown = 0.8`), CPA-5 | Registration: properties, Cooldown rejection |
| Hitbox active for one frame only (no multi-hit) | CPA-5 | Single-frame hitbox |
| `run_tests.sh` exits 0 | CPA-7 | Regression |
