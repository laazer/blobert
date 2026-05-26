# SPEC: Enemy Health System and Damage/Modifier Reception

**Ticket:** M11-14 (`project_board/11_milestone_11_base_mutation_attacks/in_progress/14_enemy_health_and_damage_reception.md`)  
**Spec ID:** EHD  
**Status:** Frozen  
**Revision:** 1  
**Author:** Spec Agent  
**Spec Exit Type:** generic  
**Date:** 2026-05-26

---

## 1. Overview

EnemyBase is a 32-line shell (`scripts/enemies/enemy_base.gd`) extending `CharacterBody3D` with identity exports, a three-state enum (`NORMAL`, `WEAKENED`, `INFECTED`), and state accessors. The existing attack pipeline (`AttackExecutor`, `PlayerProjectile3D`) calls `take_damage()`, `apply_poison()`, `apply_acid()`, and `apply_slowness()` via duck-typed `has_method()` guards — but none of these methods exist on EnemyBase. Until they do, the entire attack system has no runtime effect.

This spec defines the complete enemy-side damage reception contract: HP tracking, knockback impulse, damage-over-time effects, slowness modifier, HP-based WEAKENED state transition, and death behavior. A helper node (`EnemyEffectTracker`) extracts DoT and modifier logic to keep EnemyBase under 200 lines.

**Files modified:** `scripts/enemies/enemy_base.gd`, `scripts/enemies/enemy_ai_controller.gd`  
**Files created:** `scripts/enemies/enemy_effect_tracker.gd`

---

## 2. Evidence Sources

| Source | Path | Role |
|--------|------|------|
| Ticket | `project_board/11_milestone_11_base_mutation_attacks/in_progress/14_enemy_health_and_damage_reception.md` | Acceptance criteria |
| Planning checkpoint | `project_board/checkpoints/M11-14/2026-05-26T-plan-run.md` | Design decisions, risk register, assumptions |
| EnemyBase (current) | `scripts/enemies/enemy_base.gd` | 32-line shell to be extended |
| EnemyAIController | `scripts/enemies/enemy_ai_controller.gd` | AI movement, state transitions, chase_speed_multiplier |
| AttackExecutor | `scripts/attacks/attack_executor.gd` | Duck-typed `take_damage`, `apply_poison`, `apply_acid`, `apply_slowness` |
| PlayerProjectile3D | `scripts/attacks/player_projectile_3d.gd` | Same duck-typed calls on body_entered |
| AttackResource | `scripts/attacks/attack_resource.gd` | Defines damage values, modifiers dictionary |
| AttackExecutor spec | `project_board/specs/attack_executor_spec.md` | Duck-type guard pattern (AEX-DR-1, AEX-DR-2, AEX-6) |
| MovementSimulation | `scripts/movement/movement_simulation.gd` | Pure simulation pattern reference |
| Existing EnemyBase tests | `tests/scripts/enemy/test_enemy_base.gd` | Tests that must not break |
| Existing EnemyBase adversarial tests | `tests/scripts/enemy/test_enemy_base_adversarial.gd` | Tests that must not break |

---

## 3. Discrepancy Resolutions

### EHD-DR-1: State enum expansion — DEAD state not in enum

**Problem:** The ticket requires a death state, but the current `State` enum has only `NORMAL = 0`, `WEAKENED = 1`, `INFECTED = 2`. Adding a `DEAD` member would change the enum member count, breaking existing test `test_eb_enum_5_state_has_exactly_3_members` which asserts exactly 3 members.

**Resolution:** Do NOT add `DEAD` to the `State` enum. Instead, use a separate boolean `_is_dead: bool = false`. Death is orthogonal to the infection lifecycle (NORMAL → WEAKENED → INFECTED). An enemy can be WEAKENED and then die — the `State` enum tracks the infection progression, not the alive/dead status. This preserves backward compatibility with the existing 3-member enum assertion and the `EnemyAIController`'s `match` statement which expects exactly three cases.

### EHD-DR-2: Knockback conflict with AI controller velocity writes

**Problem:** `EnemyAIController._physics_process()` sets `enemy_base.velocity` directly for chase/patrol movement. A knockback impulse also needs to affect velocity. These could fight each other.

**Resolution:** EnemyBase maintains a separate `_knockback_velocity: Vector3` component. EnemyBase defines `_physics_process()` which: (1) applies `_knockback_velocity` to `velocity` additively, (2) decays `_knockback_velocity` by an exponential factor, (3) calls `move_and_slide()`. The AI controller sets `enemy_base.velocity.x` and `enemy_base.velocity.z` for navigation; the knockback is layered on top. This means EnemyBase now has `_physics_process`, which changes the backward-compat test (`test_eb_compat_1_no_physics_process_override`). That test must be updated — see EHD-9 backward compatibility requirements.

### EHD-DR-3: EnemyEffectTracker as child Node vs RefCounted

**Problem:** Planning checkpoint asked whether the effect tracker should be a child `Node` (can own `_process`) or a `RefCounted` (lighter, manually ticked).

**Resolution:** Use a child `Node` named `EnemyEffectTracker`. It owns its own `_process(delta)` for DoT tick timing, follows the codebase pattern of behavior composition via child nodes (like `EnemyAIController` is a child `Node3D`), and can be independently tested. EnemyBase creates and adds it as a child in `_ready()`.

### EHD-DR-4: Slowness modifier delivery to AI controller

**Problem:** How does the AI controller read the current slowness multiplier?

**Resolution:** EnemyBase exposes `get_speed_multiplier() -> float`. This method queries the `EnemyEffectTracker` for the current slowness multiplier. When no slowness is active, returns `1.0`. `EnemyAIController` calls `enemy_base.get_speed_multiplier()` and multiplies its chase/patrol speed by the result.

---

## 4. Requirements

### EHD-1: HP Core System

#### 1. Spec Summary

- **Description:** EnemyBase gains a configurable maximum health pool and a mutable current health value. HP starts at `max_hp` on `_ready()`. HP is reduced by `take_damage()` and DoT ticks. HP is never negative (clamped to 0.0). HP is never restored above `max_hp` by external methods (no healing in this spec).
- **Constraints:** `max_hp` must be an `@export var` for inspector tuning per-enemy-type. `current_hp` is a plain `var` (not exported) — runtime-only. Both are `float`.
- **Assumptions:** No healing system exists. HP only decreases or stays the same within this ticket's scope.
- **Scope:** `scripts/enemies/enemy_base.gd`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-1a | `max_hp` is an `@export var` of type `float` with default `10.0` | Instantiate EnemyBase; read `max_hp`; assert 10.0 |
| EHD-1b | `current_hp` is a `var` of type `float` | Instantiate; read `current_hp`; assert type float |
| EHD-1c | `current_hp` initializes to `max_hp` after `_ready()` | Add to scene tree (or call `_ready()`); assert `current_hp == max_hp` |
| EHD-1d | `current_hp` is settable via `max_hp` override before `_ready()` | Set `max_hp = 25.0` before tree entry; after `_ready()`, assert `current_hp == 25.0` |
| EHD-1e | `current_hp` is never negative after damage | Deal damage > current_hp; assert `current_hp == 0.0` |
| EHD-1f | `current_hp` is never greater than `max_hp` | Set `current_hp` directly to `max_hp + 10`; assert clamped to `max_hp` (via setter or external invariant) |

#### 3. Risk & Ambiguity Analysis

- **Risk:** `_ready()` timing — `current_hp = max_hp` must happen in `_ready()`, so tests that don't add the node to the scene tree may see `current_hp` at its declaration default (0.0). Tests should either call `_ready()` explicitly or add to a scene tree.
- **Edge case:** `max_hp = 0.0` means the enemy is effectively dead on spawn. This is a valid degenerate config; `current_hp` initializes to 0.0, which immediately triggers the death branch on first `take_damage()` call.

---

### EHD-2: take_damage() Method

#### 1. Spec Summary

- **Description:** `take_damage(damage: float, knockback: Vector3) -> void` is the primary damage intake method. It reduces `current_hp` by `damage` (clamped to 0.0), applies a knockback impulse, emits the `damaged` signal, checks the WEAKENED threshold, and checks for death.
- **Constraints:** This method satisfies the duck-type contract from `AttackExecutor._apply_damage()` (line 94) and `PlayerProjectile3D._on_body_entered()` (line 38). The signature must be exactly `take_damage(damage: float, knockback: Vector3)`.
- **Assumptions:** `damage` may be 0.0 (valid — zero-damage utility attacks per AEX EC-1). Negative `damage` is treated as 0.0 (no healing via damage). `knockback` may be `Vector3.ZERO` (no impulse).
- **Scope:** `scripts/enemies/enemy_base.gd`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-2a | Method signature is `take_damage(damage: float, knockback: Vector3) -> void` | `has_method("take_damage")` returns true; call with (5.0, Vector3.ZERO) does not error |
| EHD-2b | `current_hp` is reduced by `damage` | HP starts at 10.0; call `take_damage(3.0, Vector3.ZERO)`; assert `current_hp == 7.0` |
| EHD-2c | `current_hp` is clamped to 0.0 (not negative) | HP at 2.0; call `take_damage(5.0, Vector3.ZERO)`; assert `current_hp == 0.0` |
| EHD-2d | `damaged` signal is emitted with `(damage, current_hp)` | Connect signal; call `take_damage(3.0, kb)`; assert signal received with args `(3.0, 7.0)` |
| EHD-2e | Knockback impulse is applied (sets `_knockback_velocity`) | Call `take_damage(1.0, Vector3(5, 0, 0))`; assert `_knockback_velocity == Vector3(5, 0, 0)` |
| EHD-2f | `damage = 0.0` is valid — signal still emits, HP unchanged | Call `take_damage(0.0, Vector3.ZERO)`; assert HP unchanged; assert `damaged` signal emitted |
| EHD-2g | Negative `damage` is treated as 0.0 | Call `take_damage(-5.0, Vector3.ZERO)`; assert HP unchanged |
| EHD-2h | No-op after death (HP already 0, `_is_dead` true) | Kill enemy; call `take_damage(5.0, Vector3.RIGHT)`; assert HP stays 0.0, no signal, no knockback |

#### 3. Risk & Ambiguity Analysis

- **Risk:** Ordering within `take_damage()` matters: reduce HP → check WEAKENED → check death → apply knockback → emit signal. Death check must gate knockback application (dead enemies should not be knocked back).
- **Edge case:** Calling `take_damage()` on an already-dead enemy is a no-op — no signal, no HP change, no knockback. This prevents post-mortem state corruption.

**Normative order of operations inside `take_damage()`:**

1. If `_is_dead`: return immediately (no-op).
2. Clamp `damage` to `max(0.0, damage)`.
3. `current_hp = max(0.0, current_hp - damage)`.
4. Check WEAKENED threshold (EHD-5).
5. If `current_hp <= 0.0`: enter death state (EHD-6).
6. Else: set `_knockback_velocity = knockback`.
7. Emit `damaged.emit(damage, current_hp)`.

Note: Step 6 is gated on "not dead" — dead enemies do not receive knockback. Step 7 (signal) fires in both alive and death cases (except the early return in step 1 for already-dead).

**Correction to step 7:** The `damaged` signal emits for the killing blow (the blow that brings HP to 0), but NOT for subsequent calls after death. The `died` signal (EHD-6) also fires on the killing blow. Both signals fire on the same call that causes death.

---

### EHD-3: Knockback Impulse System

#### 1. Spec Summary

- **Description:** When `take_damage()` receives a non-zero `knockback` vector, the impulse is stored in `_knockback_velocity: Vector3`. On each `_physics_process(delta)` frame, `_knockback_velocity` is added to `CharacterBody3D.velocity`, then decayed exponentially. `move_and_slide()` is called. The knockback decays to near-zero and does not permanently alter the AI-driven velocity.
- **Constraints:** Exponential decay: `_knockback_velocity *= KNOCKBACK_DECAY_RATE` per physics frame, where `KNOCKBACK_DECAY_RATE` is a constant (0.0 to 1.0 exclusive). When `_knockback_velocity.length() < KNOCKBACK_EPSILON`, it is zeroed out to prevent floating-point drift. Decay is frame-rate dependent by design (matches Godot physics tick behavior).
- **Assumptions:** `KNOCKBACK_DECAY_RATE` defaults to `0.8` (tuning constant). `KNOCKBACK_EPSILON` defaults to `0.01`. These are module-level constants on EnemyBase, not exports (internal tuning, not designer-facing).
- **Scope:** `scripts/enemies/enemy_base.gd`, `_physics_process()`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-3a | `_knockback_velocity` is initialized to `Vector3.ZERO` | Instantiate; assert `_knockback_velocity == Vector3.ZERO` |
| EHD-3b | `take_damage()` sets `_knockback_velocity` to the knockback argument | Call `take_damage(1.0, Vector3(10, 0, 0))`; assert `_knockback_velocity == Vector3(10, 0, 0)` |
| EHD-3c | `_physics_process()` adds `_knockback_velocity` to `velocity` | After impulse, simulate one frame; assert `velocity` includes knockback component |
| EHD-3d | `_knockback_velocity` decays by `KNOCKBACK_DECAY_RATE` each frame | After one frame: `_knockback_velocity.length() == original * KNOCKBACK_DECAY_RATE`. After N frames: `original * KNOCKBACK_DECAY_RATE^N` |
| EHD-3e | Knockback zeroes out below `KNOCKBACK_EPSILON` | After enough frames, `_knockback_velocity == Vector3.ZERO` |
| EHD-3f | AI velocity is not permanently altered after knockback decays | Apply knockback; simulate until decay completes; AI sets velocity; assert AI velocity is uncontaminated |
| EHD-3g | `KNOCKBACK_DECAY_RATE` is `0.8` (constant) | Read constant from script; assert value |
| EHD-3h | `KNOCKBACK_EPSILON` is `0.01` (constant) | Read constant from script; assert value |
| EHD-3i | `Vector3.ZERO` knockback does not create a knockback impulse | Call `take_damage(5.0, Vector3.ZERO)`; assert `_knockback_velocity` stays `Vector3.ZERO` |
| EHD-3j | New knockback overwrites residual knockback (not additive) | Apply knockback(10,0,0); before decay completes, apply knockback(0,0,5); assert `_knockback_velocity == Vector3(0,0,5)` |

#### 3. Risk & Ambiguity Analysis

- **Risk:** The `_physics_process` on EnemyBase means both EnemyBase and EnemyAIController have `_physics_process` running. Order depends on scene tree child order. Since EnemyAIController sets `velocity` for movement and EnemyBase applies knockback and calls `move_and_slide()`, the AI controller must run **before** EnemyBase's `_physics_process`. Implementation note: EnemyAIController should NOT call `move_and_slide()` — it only sets `velocity`. EnemyBase's `_physics_process()` calls `move_and_slide()` after compositing knockback + AI velocity.
- **Breaking change:** Currently `EnemyAIController._chase_player()` (line 128) calls `enemy_base.move_and_slide()`. This must be removed — `move_and_slide()` should only be called once per frame from EnemyBase's `_physics_process()`. This is an implementation detail, but the spec must note it as a required refactor.
- **Edge case:** Knockback overwrites (EHD-3j) is the simplest model — no stacking of impulses. Rapid hits simply reset the knockback direction/magnitude.

---

### EHD-4: Damage-Over-Time (DoT) Effects

#### 1. Spec Summary

- **Description:** Two named DoT effect types exist: `"poison"` and `"acid"`. Both use the same tick mechanic but are tracked as independent named effects. Each effect is defined by a `duration: float` (seconds) and `dps: float` (damage per second). Effects tick every `DOT_TICK_INTERVAL` (0.5 seconds), dealing `dps * DOT_TICK_INTERVAL` damage per tick. Effects do not stack — re-application of the same named effect refreshes the duration (restarts the timer) without adding a second instance. Poison and acid can be active simultaneously (they are independent named effects). DoT damage calls the same HP reduction path as `take_damage()` (but with `Vector3.ZERO` knockback and without emitting the `damaged` signal — DoT ticks emit a separate `dot_tick` signal).
- **Constraints:** `DOT_TICK_INTERVAL = 0.5` (constant on EnemyEffectTracker). DoT damage does NOT emit the `damaged` signal (that is reserved for direct hits). DoT damage DOES check the WEAKENED threshold and death condition. DoT damage is applied via an internal method on EnemyBase (e.g., `_apply_dot_damage(amount: float)`), not via `take_damage()`.
- **Assumptions:** No assumptions on visual distinction (poison vs acid appearance is a presentation concern, out of scope).
- **Scope:** `scripts/enemies/enemy_effect_tracker.gd` (tick tracking, timer management), `scripts/enemies/enemy_base.gd` (method signatures, HP reduction path).

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-4a | `apply_poison(duration: float, dps: float)` exists on EnemyBase and satisfies `has_method("apply_poison")` | `enemy.has_method("apply_poison")` returns true |
| EHD-4b | `apply_acid(duration: float, dps: float)` exists on EnemyBase and satisfies `has_method("apply_acid")` | `enemy.has_method("apply_acid")` returns true |
| EHD-4c | Poison deals `dps * 0.5` damage every 0.5 seconds | Apply poison(4.0, 2.0); after 0.5s: HP reduced by 1.0; after 1.0s: HP reduced by 2.0 total |
| EHD-4d | Acid deals `dps * 0.5` damage every 0.5 seconds | Same verification as poison but with acid |
| EHD-4e | DoT effect expires after `duration` seconds | Apply poison(2.0, 1.0); after 2.0s (4 ticks): poison inactive; no further HP reduction |
| EHD-4f | Re-applying the same DoT refreshes duration, does not stack | Apply poison(2.0, 1.0); after 1.0s apply poison(2.0, 1.0) again; total active duration resets to 2.0s from re-apply point; only one poison instance active |
| EHD-4g | Re-applying with different DPS updates the DPS value | Apply poison(3.0, 1.0); after 0.5s apply poison(3.0, 2.0); next tick uses 2.0 dps |
| EHD-4h | Poison and acid are independent — both can be active simultaneously | Apply poison(2.0, 1.0) and acid(2.0, 1.0); both tick independently; HP reduced by both |
| EHD-4i | DoT does not emit `damaged` signal | Connect to `damaged`; apply poison; wait 0.5s; assert `damaged` not emitted |
| EHD-4j | DoT emits `dot_tick` signal with `(effect_name: String, tick_damage: float, current_hp: float)` | Connect to `dot_tick`; apply poison(2.0, 2.0); after 0.5s: signal received ("poison", 1.0, 9.0) |
| EHD-4k | DoT tick can trigger WEAKENED threshold | Start at 10 HP; apply poison(10.0, 10.0) (5.0 per tick); after tick 1: HP=5.0 (50%), WEAKENED triggered |
| EHD-4l | DoT tick can trigger death | Start at 1.0 HP; apply poison(2.0, 4.0) (2.0 per tick); first tick kills; died signal emitted |
| EHD-4m | DoT stops ticking after death | Kill enemy; assert no further DoT ticks |
| EHD-4n | Duration of 0.0 is a no-op (no ticks) | Apply poison(0.0, 5.0); assert no HP reduction |
| EHD-4o | DPS of 0.0 ticks but deals 0 damage | Apply poison(2.0, 0.0); ticks fire; HP unchanged |
| EHD-4p | `DOT_TICK_INTERVAL` is `0.5` (constant) | Read constant; assert 0.5 |

#### 3. Risk & Ambiguity Analysis

- **Risk:** Tick timing accuracy — `_process(delta)` accumulates time. Ticks fire when accumulated time >= `DOT_TICK_INTERVAL`. Multiple ticks can fire in a single frame if delta is large (e.g., lag spike). This is acceptable behavior.
- **Risk:** DoT + direct damage on same frame — both reduce HP independently. If DoT tick and `take_damage()` happen on the same frame, HP may drop past death threshold. The death check occurs in both paths; the first one to trigger death sets `_is_dead = true`, and subsequent damage paths are no-ops.
- **Edge case:** Very short duration (e.g., 0.1s < DOT_TICK_INTERVAL) — zero ticks fire. This is correct: the effect expires before the first tick.

---

### EHD-5: WEAKENED State Threshold

#### 1. Spec Summary

- **Description:** When `current_hp` drops to or below 50% of `max_hp`, the enemy's `current_state` transitions to `State.WEAKENED` — but only if it is currently `State.NORMAL`. This coexists with the existing `set_base_state(State.WEAKENED)` manual override — "whichever comes first" per the ticket. Once WEAKENED (by either mechanism), subsequent HP drops below 50% do not re-trigger the transition. The threshold check also does not apply if the enemy is already `INFECTED` (infection is a later lifecycle stage).
- **Constraints:** Threshold is `current_hp <= max_hp * 0.5`. Check happens inside `take_damage()` and inside the DoT damage path, after HP reduction, before death check.
- **Assumptions:** `max_hp = 0.0` edge case: `0.0 * 0.5 = 0.0`, so threshold is 0.0. An enemy with 0 max HP is effectively always at threshold. Since `_ready()` sets `current_hp = max_hp = 0.0`, the first damage call would trigger death, not WEAKENED.
- **Scope:** `scripts/enemies/enemy_base.gd`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-5a | HP dropping to exactly 50% triggers WEAKENED | HP=10; damage 5.0; assert `current_state == State.WEAKENED` |
| EHD-5b | HP dropping below 50% triggers WEAKENED | HP=10; damage 6.0; assert `current_state == State.WEAKENED` |
| EHD-5c | HP above 50% does not trigger WEAKENED | HP=10; damage 4.0 (HP=6.0, 60%); assert `current_state == State.NORMAL` |
| EHD-5d | Manual `set_base_state(WEAKENED)` still works | Call `set_base_state(WEAKENED)` at full HP; assert state is WEAKENED |
| EHD-5e | HP threshold does not re-trigger if already WEAKENED | Set WEAKENED manually; damage further; assert state stays WEAKENED (not reset or re-emitted) |
| EHD-5f | HP threshold does not trigger if already INFECTED | Set `set_base_state(INFECTED)`; damage below 50%; state stays INFECTED |
| EHD-5g | HP threshold does not trigger if dead | Kill enemy; state does not change post-death |
| EHD-5h | DoT tick can trigger WEAKENED threshold | See EHD-4k |

#### 3. Risk & Ambiguity Analysis

- **Idempotency:** The WEAKENED transition is one-way within the HP system — once triggered (by threshold or manual set), subsequent damage does not re-trigger or emit any "weakened" event. `set_base_state()` remains freely callable by external systems.
- **Edge case:** `max_hp` changes after `_ready()` — if `max_hp` is modified at runtime, the 50% threshold recalculates against the new `max_hp`. This is acceptable but unlikely in practice.

---

### EHD-6: Death State

#### 1. Spec Summary

- **Description:** When `current_hp` reaches 0.0 (via `take_damage()` or DoT), the enemy enters a dead state: `_is_dead = true`, the `EnemyEffectTracker` is stopped (no more DoT ticks), the AI controller is disabled, and the `died` signal is emitted. The node is NOT removed from the tree (`queue_free()` is NOT called) — the node remains for potential death animations or post-death effects.
- **Constraints:** `_is_dead` is a one-way latch — once true, it is never set back to false within this ticket's scope. All damage methods (`take_damage`, DoT) become no-ops when `_is_dead` is true. The `died` signal is emitted exactly once.
- **Assumptions:** Death animation and node cleanup are presentation concerns deferred to a future ticket. AI controller disable means setting a flag or disconnecting `_physics_process` — implementation detail.
- **Scope:** `scripts/enemies/enemy_base.gd`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-6a | `_is_dead` is `false` by default | Instantiate; assert `_is_dead == false` |
| EHD-6b | `_is_dead` becomes `true` when `current_hp` reaches 0.0 | HP=10; damage 10; assert `_is_dead == true` |
| EHD-6c | `died` signal is emitted exactly once on death | Connect signal; kill enemy; assert signal received once |
| EHD-6d | `died` signal is not emitted on subsequent damage after death | Kill; connect counter; damage again; assert counter still 1 |
| EHD-6e | `take_damage()` is a no-op after death | Kill; `take_damage(5.0, Vector3.RIGHT)`; assert HP=0.0, no knockback, no `damaged` signal |
| EHD-6f | DoT ticks stop after death | Apply poison; kill via direct damage; assert no further DoT ticks |
| EHD-6g | AI controller is disabled after death | Kill enemy; assert AI controller's `_physics_process` is not executing (via `set_physics_process(false)` or similar) |
| EHD-6h | Node is NOT queue_free'd after death | Kill; assert `is_inside_tree()` is still true |
| EHD-6i | `is_dead()` public method returns `_is_dead` | Assert `is_dead()` returns false before death, true after |

#### 3. Risk & Ambiguity Analysis

- **Risk:** Other systems (EnemyAIController, run assembler) may not check `_is_dead` before interacting with the enemy. The AI controller must check `_is_dead` at the top of its `_physics_process`. Alternatively, EnemyBase disables the AI controller's processing.
- **Approach for AI disable:** EnemyBase holds a reference to its `EnemyEffectTracker` child and any `EnemyAIController` child. On death, it calls `set_physics_process(false)` on the AI controller and `stop_all_effects()` on the effect tracker.

---

### EHD-7: Slowness Modifier

#### 1. Spec Summary

- **Description:** `apply_slowness(multiplier: float, duration: float)` applies a speed reduction modifier for the given duration. The `multiplier` value (0.0 to 1.0 range, where 0.5 = 50% speed) is stored and queryable via `get_speed_multiplier() -> float`. When no slowness is active, `get_speed_multiplier()` returns `1.0`. Re-application refreshes duration and updates the multiplier value (same non-stacking semantics as DoT).
- **Constraints:** The multiplier is applied by the AI controller to its speed calculations. `EnemyAIController` calls `enemy_base.get_speed_multiplier()` when computing chase speed and patrol speed. The multiplier does NOT affect knockback velocity (knockback bypasses speed modification). Duration is tracked by `EnemyEffectTracker` with a simple countdown timer in `_process(delta)`.
- **Assumptions:** `multiplier = 0.0` means full stop (valid). `multiplier > 1.0` means speed boost (valid but unusual — no clamping). Negative multiplier is treated as 0.0. Duration of 0.0 is a no-op.
- **Scope:** `scripts/enemies/enemy_base.gd` (public API), `scripts/enemies/enemy_effect_tracker.gd` (tracking), `scripts/enemies/enemy_ai_controller.gd` (consumption).

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-7a | `apply_slowness(multiplier: float, duration: float)` exists and satisfies `has_method("apply_slowness")` | `enemy.has_method("apply_slowness")` returns true |
| EHD-7b | `get_speed_multiplier()` returns `1.0` when no slowness active | Instantiate; assert `get_speed_multiplier() == 1.0` |
| EHD-7c | After `apply_slowness(0.5, 2.0)`, `get_speed_multiplier()` returns `0.5` | Apply; assert return value |
| EHD-7d | After duration expires, `get_speed_multiplier()` returns `1.0` | Apply `apply_slowness(0.5, 1.0)`; wait 1.0s; assert `1.0` |
| EHD-7e | Re-application refreshes duration | Apply `apply_slowness(0.5, 2.0)`; wait 1.0s; apply `apply_slowness(0.5, 2.0)` again; wait 1.5s; assert still slowed |
| EHD-7f | Re-application updates multiplier | Apply `apply_slowness(0.5, 3.0)`; apply `apply_slowness(0.3, 3.0)`; assert `get_speed_multiplier() == 0.3` |
| EHD-7g | `EnemyAIController` uses `get_speed_multiplier()` for chase speed | Apply slowness; AI chases; assert chase speed is `BASE_CHASE_SPEED * chase_speed_multiplier * get_speed_multiplier()` |
| EHD-7h | Slowness does NOT affect knockback velocity | Apply slowness(0.1, 10.0); take_damage with knockback; assert knockback magnitude unaffected |
| EHD-7i | Slowness stops on death | Kill enemy; assert slowness timer cleared |
| EHD-7j | Duration 0.0 is a no-op | Apply `apply_slowness(0.5, 0.0)`; assert `get_speed_multiplier() == 1.0` |
| EHD-7k | Negative multiplier treated as 0.0 | Apply `apply_slowness(-0.5, 2.0)`; assert `get_speed_multiplier() == 0.0` |

#### 3. Risk & Ambiguity Analysis

- **Risk:** `EnemyAIController` currently does not read a speed multiplier from `EnemyBase`. The controller's `_chase_player()` uses `BASE_CHASE_SPEED * chase_speed_multiplier` directly. A one-line change is needed: multiply by `enemy_base.get_speed_multiplier()`.
- **Same for weakened chase:** `_handle_weakened_state` uses `WEAKENED_CHASE_SPEED * chase_speed_multiplier`. This should also multiply by `enemy_base.get_speed_multiplier()`.
- **Same for patrol:** `_move_in_direction()` uses `DEFAULT_MOVE_SPEED`. This should also be affected by slowness.

---

### EHD-8: EnemyEffectTracker Helper Node

#### 1. Spec Summary

- **Description:** `EnemyEffectTracker` is a `Node` subclass that manages all active DoT effects and the slowness modifier. It is created by `EnemyBase._ready()` and added as a child node. It owns `_process(delta)` for tick timing. EnemyBase delegates `apply_poison()`, `apply_acid()`, and `apply_slowness()` to the tracker. The tracker calls back to EnemyBase for HP reduction when DoT ticks fire.
- **Constraints:** The tracker must be a separate `.gd` file: `scripts/enemies/enemy_effect_tracker.gd`. It uses `class_name EnemyEffectTracker`. The tracker does NOT know about knockback (that stays on EnemyBase). The tracker does NOT directly modify `current_hp` — it calls a method on its parent (EnemyBase) to request HP reduction.
- **Assumptions:** The tracker uses a Dictionary to store active effects by name key. Each effect entry holds `{remaining_duration: float, dps: float, elapsed_since_tick: float}`.
- **Scope:** `scripts/enemies/enemy_effect_tracker.gd`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-8a | `EnemyEffectTracker` extends `Node` | `is_instance_of(tracker, Node)` returns true |
| EHD-8b | `class_name EnemyEffectTracker` declared | Source code contains `class_name EnemyEffectTracker` |
| EHD-8c | `add_dot(effect_name: String, duration: float, dps: float) -> void` method exists | Callable without error |
| EHD-8d | `set_slowness(multiplier: float, duration: float) -> void` method exists | Callable without error |
| EHD-8e | `get_speed_multiplier() -> float` returns current multiplier | Returns 1.0 when no slowness; returns multiplier when active |
| EHD-8f | `stop_all_effects() -> void` clears all DoTs and slowness | Call after applying effects; assert all cleared |
| EHD-8g | `has_active_dot(effect_name: String) -> bool` returns true when named DoT is active | Apply poison; assert `has_active_dot("poison") == true` |
| EHD-8h | Tracker emits `dot_tick_requested(effect_name: String, tick_damage: float)` when a DoT tick fires | Connect signal; wait 0.5s; assert signal received |
| EHD-8i | Tracker file is under 150 lines | Count lines of `enemy_effect_tracker.gd` |
| EHD-8j | EnemyBase file (with all additions from this spec) is under 200 lines | Count lines of `enemy_base.gd` |

#### 3. Risk & Ambiguity Analysis

- **Callback pattern:** The tracker signals `dot_tick_requested` and EnemyBase connects to it, calling its internal `_apply_dot_damage()`. This avoids the tracker needing a typed reference to EnemyBase (loose coupling).
- **Risk:** Multiple DoT effects ticking on the same frame — both call `_apply_dot_damage()` in sequence. The second call may find the enemy dead from the first. The death check inside `_apply_dot_damage()` gates subsequent calls, same as `take_damage()`.

---

### EHD-9: Backward Compatibility

#### 1. Spec Summary

- **Description:** All existing tests that reference `EnemyBase` must continue to pass without modification (with one exception: `test_eb_compat_1_no_physics_process_override` must be updated since EnemyBase now has `_physics_process`). All existing `AttackExecutor` and `PlayerProjectile3D` tests that use mock enemies with duck-typed `has_method()` guards must continue to pass unchanged — the mocks remain valid because they implement the same method signatures.
- **Constraints:** The `State` enum must retain exactly 3 members: `NORMAL = 0`, `WEAKENED = 1`, `INFECTED = 2`. No renumbering, no additions. The `set_base_state()` and `get_base_state()` signatures must not change. All existing exports (`enemy_id`, `enemy_family`, `mutation_drop`) must remain unchanged.
- **Assumptions:** No assumptions.
- **Scope:** All files in `tests/scripts/enemy/`, `tests/scripts/attacks/`.

#### 2. Acceptance Criteria

| ID | Criterion | Verifiable By |
|----|-----------|---------------|
| EHD-9a | `State` enum has exactly 3 members | `body.State.keys().size() == 3` (test `test_eb_enum_5_state_has_exactly_3_members`) |
| EHD-9b | `State.NORMAL == 0`, `WEAKENED == 1`, `INFECTED == 2` | Existing enum tests pass |
| EHD-9c | `set_base_state()` and `get_base_state()` unchanged | Existing state tests pass |
| EHD-9d | Identity exports unchanged | Existing export tests pass |
| EHD-9e | `test_eb_compat_1_no_physics_process_override` is updated to accept `_physics_process` | Test updated to reflect new reality (EnemyBase now has `_physics_process`) |
| EHD-9f | All AttackExecutor tests pass | `run_tests.sh` exits 0 |
| EHD-9g | All PlayerProjectile3D tests pass | `run_tests.sh` exits 0 |
| EHD-9h | `run_tests.sh` exits 0 (full suite) | Run full test suite |

#### 3. Risk & Ambiguity Analysis

- **Risk:** The one test that MUST be updated is `test_eb_compat_1_no_physics_process_override` — it asserts that `enemy_base.gd` source does not contain `_physics_process`. Since EnemyBase now needs `_physics_process` for knockback and `move_and_slide()`, this test should be changed to verify that `_physics_process` EXISTS (inverted assertion) or removed entirely and replaced with a test that verifies the knockback + move_and_slide behavior.
- **Risk:** `EnemyAIController` currently calls `enemy_base.move_and_slide()` in `_chase_player()` (line 128) and `_handle_weakened_state` (line 193). Since EnemyBase now calls `move_and_slide()` in its own `_physics_process`, the AI controller must stop calling it. This is a breaking change to `EnemyAIController` but not to its public API — only internal behavior changes.

---

## 5. Frozen API Surface

### EnemyBase public interface (additions only; existing API preserved)

```gdscript
# --- Signals (new) ---
signal damaged(damage: float, current_hp: float)
signal died()
signal dot_tick(effect_name: String, tick_damage: float, current_hp: float)

# --- Exports (new) ---
@export var max_hp: float = 10.0

# --- Vars (new) ---
var current_hp: float = 0.0  # initialized to max_hp in _ready()

# --- Constants (new) ---
const KNOCKBACK_DECAY_RATE: float = 0.8
const KNOCKBACK_EPSILON: float = 0.01
const WEAKENED_HP_THRESHOLD: float = 0.5  # 50% of max_hp

# --- Public methods (new) ---
func take_damage(damage: float, knockback: Vector3) -> void
func apply_poison(duration: float, dps: float) -> void
func apply_acid(duration: float, dps: float) -> void
func apply_slowness(multiplier: float, duration: float) -> void
func get_speed_multiplier() -> float
func is_dead() -> bool
```

### EnemyBase internal (new)

```gdscript
var _is_dead: bool = false
var _knockback_velocity: Vector3 = Vector3.ZERO
var _effect_tracker: EnemyEffectTracker = null

func _ready() -> void
func _physics_process(delta: float) -> void
func _apply_dot_damage(amount: float) -> void
func _check_weakened_threshold() -> void
func _enter_death_state() -> void
```

### EnemyEffectTracker public interface

```gdscript
class_name EnemyEffectTracker
extends Node

signal dot_tick_requested(effect_name: String, tick_damage: float)

func add_dot(effect_name: String, duration: float, dps: float) -> void
func set_slowness(multiplier: float, duration: float) -> void
func get_speed_multiplier() -> float
func has_active_dot(effect_name: String) -> bool
func stop_all_effects() -> void
```

### EnemyAIController modifications (changes only)

```gdscript
# In _chase_player(): multiply speed by enemy_base.get_speed_multiplier()
# In _handle_weakened_state(): multiply speed by enemy_base.get_speed_multiplier()
# In _move_in_direction(): multiply speed by enemy_base.get_speed_multiplier()
# Remove move_and_slide() calls from _chase_player() and _handle_weakened_state()
```

---

## 6. Deferred Boundary

| Item | Owner | Notes |
|------|-------|-------|
| Death animation | Presentation ticket | `died` signal is the hook; no animation in this ticket |
| Node cleanup / queue_free | Presentation ticket | Enemy stays in tree after death |
| Healing / HP restoration | Future ticket | HP only decreases in M11-14 |
| Visual DoT indicators (poison vs acid appearance) | Presentation ticket | Separate from game logic |
| `DEAD` enum state in State | Future ticket | Using `_is_dead` boolean instead |
| Enemy-to-enemy damage | Not planned | Only player → enemy damage path |
| Damage resistance / armor | Not planned | `take_damage` applies raw damage |
| DoT damage type differentiation (for resistance) | Not planned | Both poison and acid deal untyped damage |

---

## 7. Test Strategy

### Test scope

Unit tests with direct EnemyBase instantiation (no mocks for EnemyBase itself). The `EnemyEffectTracker` can be tested in isolation. DoT timing tested via simulated delta (call `_process(delta)` directly on the tracker). Knockback decay tested via direct `_physics_process(delta)` calls.

### Test files

| File | Purpose |
|------|---------|
| `tests/scripts/enemy/test_enemy_health_damage.gd` | HP core, take_damage, signals, death, WEAKENED threshold |
| `tests/scripts/enemy/test_enemy_effect_tracker.gd` | DoT ticks, non-stacking, slowness, stop_all_effects |
| `tests/scripts/enemy/test_enemy_knockback.gd` | Knockback impulse, decay, no permanent velocity change |
| `tests/scripts/enemy/test_enemy_health_damage_adversarial.gd` | Edge cases (see table below) |
| `tests/scripts/enemy/test_enemy_ai_slowness_integration.gd` | AI controller reads speed multiplier correctly |

### Test categories

| Category | What to test | EHD Requirement |
|----------|-------------|-----------------|
| HP defaults | max_hp = 10.0, current_hp = max_hp after _ready | EHD-1 |
| take_damage basic | HP reduction, clamping, signal | EHD-2 |
| take_damage dead guard | No-op after death | EHD-2 |
| Knockback impulse | Velocity component, decay, zeroing | EHD-3 |
| Knockback overwrite | New impulse replaces old | EHD-3 |
| Poison DoT | Tick timing, duration, HP reduction | EHD-4 |
| Acid DoT | Same as poison, independent | EHD-4 |
| DoT non-stacking | Refresh on re-apply | EHD-4 |
| DoT concurrent | Poison + acid simultaneously | EHD-4 |
| WEAKENED threshold | 50% trigger, one-way latch | EHD-5 |
| WEAKENED manual | set_base_state still works | EHD-5 |
| Death state | _is_dead, died signal, AI disable | EHD-6 |
| Death post-mortem | No damage, no DoT, no knockback | EHD-6 |
| Slowness modifier | Multiplier, duration, expiry | EHD-7 |
| Slowness + AI | Chase speed affected | EHD-7 |
| Effect tracker isolation | add_dot, set_slowness, stop_all | EHD-8 |
| Backward compat | Existing tests pass | EHD-9 |

---

## 8. Edge Cases Table

| # | Scenario | Expected Behavior | EHD Req | Rationale |
|---|----------|-------------------|---------|-----------|
| EC-1 | `damage = 0.0` | HP unchanged; `damaged` signal emits with (0.0, current_hp) | EHD-2 | Zero-damage utility attacks (modifier-only) per AEX EC-1 |
| EC-2 | `damage < 0` (negative) | Treated as 0.0; no healing via damage | EHD-2 | Defensive guard |
| EC-3 | `max_hp = 0.0` | `current_hp = 0.0` on ready; first damage triggers death immediately | EHD-1 | Degenerate config |
| EC-4 | Knockback `Vector3.ZERO` | No knockback impulse applied | EHD-3 | No-knockback attacks are valid |
| EC-5 | Overlapping knockback (hit during knockback) | New knockback overwrites residual | EHD-3 | Simplest model; avoids stacking complexity |
| EC-6 | DoT duration < DOT_TICK_INTERVAL | Zero ticks fire; effect expires silently | EHD-4 | Duration too short for any tick |
| EC-7 | DoT DPS = 0.0 | Ticks fire but deal 0 damage | EHD-4 | Valid; may be used for visual-only effects |
| EC-8 | Concurrent poison + acid + slowness | All three active independently | EHD-4, EHD-7 | Effects are orthogonal |
| EC-9 | Damage after death | No-op (no HP change, no signals, no knockback) | EHD-6 | Post-mortem guard |
| EC-10 | DoT kills during tick | `died` signal emitted; remaining DoT ticks cancelled | EHD-4, EHD-6 | Death is final |
| EC-11 | WEAKENED at exactly 50% HP | State transitions to WEAKENED (inclusive threshold) | EHD-5 | `<=` comparison, not `<` |
| EC-12 | WEAKENED already set manually, then HP drops below 50% | No re-trigger; state stays WEAKENED | EHD-5 | One-way latch |
| EC-13 | INFECTED state + HP below 50% | State stays INFECTED; WEAKENED not triggered | EHD-5 | Infection overrides weakening |
| EC-14 | Two EnemyBase instances, independent HP | Damaging one does not affect the other | EHD-1 | Instance isolation |
| EC-15 | `apply_slowness(0.0, 5.0)` | Full stop (speed = 0); valid | EHD-7 | Edge of multiplier range |
| EC-16 | `apply_slowness(-1.0, 5.0)` | Treated as 0.0 (clamped) | EHD-7 | Defensive guard |
| EC-17 | Multiple `take_damage()` calls in one frame | All reduce HP sequentially; death may trigger mid-sequence | EHD-2 | No batching of damage |
| EC-18 | `take_damage()` with large knockback (100, 0, 0) | Knockback applied and decayed normally; no special cap | EHD-3 | No magnitude cap |
| EC-19 | Re-apply DoT with different DPS | DPS updates to new value; duration refreshes | EHD-4 | Non-stacking refresh semantics |
| EC-20 | Slowness re-apply with longer duration | Duration refreshes to new (longer) value | EHD-7 | Non-stacking refresh |

---

## 9. Risk & Ambiguity Analysis (Cross-Cutting)

| Risk | Impact | Mitigation |
|------|--------|------------|
| `_physics_process` ordering between EnemyBase and EnemyAIController | Medium — AI sets velocity, then EnemyBase adds knockback and calls `move_and_slide`. If order is reversed, knockback applies before AI overwrites velocity. | Child nodes process before parents in Godot's default order. Since EnemyAIController is a child of EnemyBase, it processes first. AI sets velocity → EnemyBase adds knockback → `move_and_slide()`. This is the correct order. |
| `move_and_slide()` called twice per frame (AI + EnemyBase) | High — double physics step causes incorrect movement | Remove `move_and_slide()` from EnemyAIController; only EnemyBase calls it |
| EnemyBase line count exceeds 200 | Medium — ticket requirement violated | EnemyEffectTracker helper extracts ~60-80 lines of DoT/slowness logic. EnemyBase stays ~120-160 lines. |
| DoT timing non-determinism in tests | Medium — flaky tests | Tests call `_process(delta)` directly on the tracker with controlled delta values; no reliance on real time |
| Existing test breakage from `_physics_process` addition | Low — only one test affected | `test_eb_compat_1_no_physics_process_override` must be updated |

---

## 10. Clarifying Questions

All planning-phase ambiguities have been resolved:

| Question | Resolution | Confidence |
|----------|------------|------------|
| Child Node or RefCounted for effect tracker? | Child Node (EHD-DR-3) — owns `_process`, follows codebase pattern | High |
| Knockback decay model? | Exponential: `_knockback_velocity *= 0.8` per frame (EHD-3) | Medium |
| Death behavior — queue_free or keep in tree? | Keep in tree, `_is_dead` flag, emit `died` signal (EHD-6) | High |
| How does slowness reach AI controller? | `enemy_base.get_speed_multiplier()` called by AI controller (EHD-DR-4) | High |
| DEAD enum value needed? | No — using `_is_dead` boolean to preserve 3-member enum (EHD-DR-1) | High |
| Knockback overwrite vs stack? | Overwrite — new impulse replaces old (EHD-3j) | High |
| DoT damage signal — use `damaged` or separate? | Separate `dot_tick` signal; `damaged` reserved for direct hits (EHD-4) | High |

No unresolved ambiguities remain.

---

## 11. Traceability Matrix

| Ticket AC | Spec Requirement | Test Category |
|-----------|-----------------|---------------|
| `max_hp` export, default 10.0, `current_hp` var | EHD-1 | HP defaults |
| `take_damage(damage, knockback)` reduces HP, applies knockback, emits `damaged` | EHD-2 | take_damage basic |
| `current_hp <= 0` → death state, disable AI, emit `died` | EHD-6 | Death state |
| `apply_poison(duration, dps)` ticking DoT | EHD-4 | Poison DoT |
| `apply_acid(duration, dps)` ticking DoT | EHD-4 | Acid DoT |
| DoT non-stacking, refresh on re-apply | EHD-4 (EHD-4f, EHD-4g) | DoT non-stacking |
| `apply_slowness(multiplier, duration)` | EHD-7 | Slowness modifier |
| Knockback impulse, decays, no permanent velocity | EHD-3 | Knockback |
| WEAKENED at HP threshold (50%) or `set_base_state()` | EHD-5 | WEAKENED threshold |
| Existing attack pipeline tests pass | EHD-9 | Backward compat |
| New integration tests: EnemyBase + AttackExecutor + PlayerProjectile3D | EHD-9f, EHD-9g | Integration |
| `run_tests.sh` exits 0 | EHD-9h | Full suite |
