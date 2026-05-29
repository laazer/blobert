# Specification: Acid + Claw Fusion Attack — Venomous Shred

**Ticket ID:** M12-04
**Ticket Path:** project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
**Spec Version:** 1.0
**Status:** COMPLETE
**Last Updated:** 2026-05-29 by Spec Agent

---

## Overview

The acid + claw fused mutation attack (attack_id 101, name "Venomous Shred") is a 3-hit melee combo that applies a separate, independently-decaying acid DoT stack on each successful hit. The attack requires five net-new capabilities:

1. A new `combo_hits: int` field on `AttackResource` (backward-compatible).
2. A new `"MELEE_SWIPE_COMBO"` case in `AttackExecutor.execute_attack()`.
3. A new `add_acid_stack()` / `get_acid_stack_count()` API on `EnemyEffectTracker` and `EnemyBase`.
4. An update to the `attack_database.gd` acid_claw registration (superseding the M12-02 placeholder).
5. No new `AcidVFXSystem` class — the existing `enemy.apply_acid()` API is the target (ticket fiction resolved).

The five gaps documented in the planning checkpoint (`project_board/checkpoints/M12-04/2026-05-29T-plan-run.md`) are each resolved by a numbered requirement below.

---

## Evidence Sources

| Source | Path |
|--------|------|
| Ticket | `project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md` |
| Planning checkpoint | `project_board/checkpoints/M12-04/2026-05-29T-plan-run.md` |
| AttackExecutor | `scripts/attacks/attack_executor.gd` |
| AttackResource | `scripts/attacks/attack_resource.gd` |
| EnemyEffectTracker | `scripts/enemies/enemy_effect_tracker.gd` |
| EnemyBase | `scripts/enemies/enemy_base.gd` |
| AttackDatabase | `scripts/attacks/attack_database.gd` |
| FADI spec | `project_board/specs/fused_attack_database_integration_spec.md` |

---

## Frozen Design Decisions

### AC-DD-1: Normative Stat Block — Ticket AC Overrides M12-02 Registration

The existing `attack_database.gd` registration for acid_claw (attack_id 101) was entered during M12-02 as a placeholder stub named "Toxic Slash" using `MELEE_SWIPE` (single swipe, damage=4.0, cooldown=1.5, range=1.5, knockback=3.0). That stub is superseded in full by M12-04. The M12-04 ticket AC is the normative stat block.

**Normative stats (all implementation must match exactly):**
- `attack_id`: 101
- `attack_name`: "Venomous Shred"
- `effect_type`: "MELEE_SWIPE_COMBO"
- `damage` (per hit): 1.8
- `combo_hits`: 3
- `cooldown`: 2.0
- `attack_range`: 1.2
- `knockback_magnitude`: 80.0
- `knockback_direction`: "away"
- `startup_frames`: 0
- Acid modifier: `{ "acid_on_hit": true, "acid_duration": 2.5, "acid_dps": 0.4 }`

Knockback 80.0 is deliberately high relative to base single-hit attacks (claw=2.0, carapace=5.0). This is intentional game design: each hit in the combo applies a smaller per-hit knockback force (80.0 is in arbitrary internal units scaled per-hit, not a global impulse summed across hits). The value is normative from the ticket AC. Implementation agents must use it without reduction.

The following M12-02 constants in `attack_database.gd` must be replaced:
- `ACID_CLAW_DAMAGE := 4.0` → `1.8`
- `ACID_CLAW_COOLDOWN := 1.5` → `2.0`
- `ACID_CLAW_RANGE := 1.5` → `1.2`
- `ACID_CLAW_KNOCKBACK := 3.0` → `80.0`
- `ACID_CLAW_ACID_DURATION := 2.0` → `2.5`
- `ACID_CLAW_ACID_DPS := 0.8` → `0.4`

New constants to add:
- `ACID_CLAW_COMBO_HITS := 3`
- `ACID_CLAW_COMBO_FRAME_INTERVAL := 6`

### AC-DD-2: MELEE_SWIPE_COMBO — New Case, Not Extension of MELEE_SWIPE

`MELEE_SWIPE_COMBO` is implemented as a new case in the `match resource.effect_type` block of `execute_attack()`. The existing `"MELEE_SWIPE"` case is not modified. This preserves backward compatibility for all existing MELEE_SWIPE registrations.

### AC-DD-3: AcidVFXSystem Does Not Exist — Use Existing API

`AcidVFXSystem` is not a real class and must not be created. The ticket description used this term fictionally. Implementation targets `enemy.apply_acid_stack(duration, dps)` (a new method on `EnemyBase`), which delegates to `EnemyEffectTracker.add_acid_stack(duration, dps)`. No global `AcidVFXSystem` node or class is introduced.

### AC-DD-4: Stacking Acid via Indexed Keys

`EnemyEffectTracker.add_dot("acid", ...)` overwrites the `"acid"` key. Independent stacking acid requires auto-indexed keys. The mechanism is:
- `EnemyEffectTracker` maintains an internal `_acid_stack_counter: int = 0` that increments on each `add_acid_stack()` call.
- Each stack is stored under key `"acid_stack_%d" % _acid_stack_counter`.
- The counter never resets within a combat encounter (preventing key reuse that could overwrite an active stack).
- `get_acid_stack_count()` counts active keys matching the `"acid_stack_"` prefix.
- Existing `apply_acid()` on `EnemyBase` and `add_dot("acid", ...)` are left unchanged for backward compatibility.

### AC-DD-5: combo_hits as @export Field on AttackResource

`combo_hits: int = 1` is added as a new `@export` field on `AttackResource`. Default value 1 ensures all existing single-hit resources continue to behave correctly without modification. The field is read by `_handle_melee_swipe_combo()` to determine the loop count.

### AC-DD-6: Inter-Hit Timing — 6 Frames at 60fps

The ticket specifies hitbox spawns at frames 6, 12, and 18 from combo start. This is interpreted as: each hit is separated by 6 frames (0.1s at 60fps). The `_handle_melee_swipe_combo()` handler waits `combo_frame_interval / FRAMES_PER_SECOND` seconds between each swipe using `await get_tree().create_timer(...)`. The constant `ACID_CLAW_COMBO_FRAME_INTERVAL := 6` is stored in `attack_database.gd` as a named constant; the handler uses `resource.modifiers.get("combo_frame_interval", 6)` to allow per-resource override without a new field.

---

## Functional Requirements

---

### Requirement AC-1: AttackResource Schema Extension — combo_hits Field

#### 1. Spec Summary

- **Description:** `AttackResource` gains a new `@export var combo_hits: int = 1` field. This field specifies how many individual hit events occur during a single `MELEE_SWIPE_COMBO` execution. For all existing `MELEE_SWIPE`, `PROJECTILE_SPIT`, and `SLAM_AOE` attacks, `combo_hits` is ignored by their handlers.
- **Constraints:** Default value must be `1` (not `0`) to prevent divide-by-zero or empty-loop edge cases. The field must be declared with `@export` so it is visible in the Godot inspector and serializable in `.tres` files. No other field on `AttackResource` is modified.
- **Assumptions:** No `.tres` resource files for existing attacks exist in this repository. All existing attacks are registered programmatically in `attack_database.gd`. Backward compatibility is achieved solely by the default value of 1.
- **Scope:** `scripts/attacks/attack_resource.gd`.

#### 2. Acceptance Criteria

- **AC-1a:** `AttackResource.new()` produces an instance where `combo_hits == 1`.
- **AC-1b:** Assigning `combo_hits = 3` on a resource instance and reading it back returns `3`.
- **AC-1c:** Assigning `combo_hits = 0` stores `0` (no clamping by the field itself; the handler is responsible for safe loop behavior).
- **AC-1d:** Assigning `combo_hits = -1` stores `-1` (no clamping by the field; handlers guard against this).
- **AC-1e:** An existing `AttackResource` instance created with all other fields set and `combo_hits` unset reports `combo_hits == 1`.
- **AC-1f:** `combo_hits` is an `int`, not a `float`. Assigning `2.9` coerces to `2` per GDScript int assignment semantics.
- **AC-1g:** The acid_claw resource registered in `_register_fused_defaults()` sets `combo_hits = ACID_CLAW_COMBO_HITS` (value 3).

#### 3. Risk and Ambiguity Analysis

- **Backward compatibility:** All existing tests that construct `AttackResource` instances without setting `combo_hits` will continue to pass because the default is 1. No existing test explicitly asserts `combo_hits` does not exist, so adding the field is safe.
- **No type coercion risk for int:** GDScript `@export var combo_hits: int = 1` enforces integer type at the script level. Float assignment coerces silently.

#### 4. Clarifying Questions

None. Decision frozen per AC-DD-5.

---

### Requirement AC-2: MELEE_SWIPE_COMBO Handler in AttackExecutor

#### 1. Spec Summary

- **Description:** `AttackExecutor.execute_attack()` gains a new case `"MELEE_SWIPE_COMBO"` that routes to `_handle_melee_swipe_combo(resource)`. This handler executes `resource.combo_hits` sequential hit events, each identical in structure to a single `_handle_melee_swipe()` hit, separated by `combo_frame_interval_seconds` seconds of async delay. The handler is async (uses `await`) and must follow the same `_is_active` lifecycle as `_run_slam_attack_async()`.
- **Constraints:**
  - `combo_hits` must be read from `resource.combo_hits`. If `combo_hits <= 0`, the handler exits without executing any hits.
  - The inter-hit delay is `modifiers.get("combo_frame_interval", 6) / FRAMES_PER_SECOND` seconds (default 0.1s at 60fps).
  - Each hit performs: hitbox query at range → per-hit acid stack call → per-hit knockback → per-hit `attack_hit` signal emission → per-hit `melee_vfx_requested` signal emission.
  - No startup delay before the first hit (acid_claw has `startup_frames = 0`; the handler must still honor `startup_frames > 0` on the resource for consistency).
  - The `_is_active` flag is set to `true` before the handler runs and to `false` after all hits complete (or if zero hits). The async pattern mirrors `_run_slam_attack_async()`.
  - If `get_tree()` returns null during any inter-hit delay, the handler aborts the remaining hits and sets `_is_active = false`.
- **Assumptions:** The acid-specific stacking behavior (`apply_acid_stack`) is applied as part of the modifier processing for `MELEE_SWIPE_COMBO`. The handler calls a new private method `_apply_combo_modifiers(enemy, resource.modifiers, pre_state)` or reuses `_apply_modifiers()` extended to call `apply_acid_stack` when `acid_on_hit == true` and the effect type context is a combo. See Requirement AC-3 for the stacking modifier dispatch decision.
- **Scope:** `scripts/attacks/attack_executor.gd`.

#### 2. Acceptance Criteria

- **AC-2a:** `execute_attack(resource)` where `resource.effect_type == "MELEE_SWIPE_COMBO"` and `combo_hits == 3` results in exactly 3 `attack_hit` signal emissions (one per hit, each with the same resource).
- **AC-2b:** Between each pair of consecutive hits, `get_tree().create_timer(interval)` is awaited, where `interval == modifiers.get("combo_frame_interval", 6) / 60.0`.
- **AC-2c:** Each hit performs a fresh hitbox query (`_query_enemies_in_range`) using the same center and radius formula as `_handle_melee_swipe()`. An enemy that moves out of range between hits is NOT hit by subsequent swipes.
- **AC-2d:** Each hit calls `apply_acid_stack` on each enemy in range (see AC-3 for the stacking call contract). The existing `apply_acid()` is NOT called for `MELEE_SWIPE_COMBO`.
- **AC-2e:** Each hit applies knockback independently using `_calculate_knockback()` with `resource.knockback_magnitude` and `resource.knockback_direction`.
- **AC-2f:** `melee_vfx_requested` signal is emitted once per hit (total 3 emissions for `combo_hits == 3`).
- **AC-2g:** `attack_started` signal is emitted exactly once at the start of the combo (before any hits), not once per hit.
- **AC-2h:** With `combo_hits == 0`, no `attack_hit` signal is emitted and `_is_active` returns to `false` after the handler completes.
- **AC-2i:** With `combo_hits == 1`, exactly one hit fires — the handler behaves identically to a single `MELEE_SWIPE` in terms of hit count, but uses the stacking acid path.
- **AC-2j:** If `get_tree()` is null during the inter-hit delay, the handler does not crash and `_is_active` is set to `false`.
- **AC-2k:** A second call to `execute_attack()` while the first combo is still running (i.e., `_is_active == true`) is silently ignored (no second combo starts).
- **AC-2l:** After the combo completes (all hits fired, all delays elapsed), `_is_active == false`.
- **AC-2m:** `startup_frames` on the resource is honored: if `startup_frames > 0`, the handler waits `startup_frames / FRAMES_PER_SECOND` seconds before the first hit. For the acid_claw resource specifically, `startup_frames == 0`, so no startup delay occurs.

#### 3. Risk and Ambiguity Analysis

- **Async lifecycle:** The `execute_attack()` method currently returns immediately for MELEE_SWIPE (synchronous) and uses `_run_slam_attack_async()` for SLAM_AOE to handle the async lifecycle. MELEE_SWIPE_COMBO must follow the same async-wrapper pattern. The `execute_attack()` match case for `"MELEE_SWIPE_COMBO"` must call `_run_melee_swipe_combo_async(resource)` and return immediately (do not await inline), matching the SLAM_AOE pattern.
- **Per-hit query vs single query:** The spec requires a fresh query per hit (AC-2c). This means if a target moves out of range mid-combo, later hits miss. This is intentional game behavior rewarding enemy positioning.
- **VFX timing:** The `melee_vfx_requested` signal is emitted per hit, which means the VFX system will see 3 emissions per combo. The VFX system is downstream and not in this spec's scope; the contract is "emit once per hit at the center position calculated for that hit."
- **Modifier context for acid stacking:** `_apply_modifiers()` currently calls `apply_acid()` (non-stacking). The combo handler must not call `_apply_modifiers()` unchanged — it must call `_apply_combo_modifiers()` (new method) or modify the dispatch to call `apply_acid_stack()` instead. See AC-3.

#### 4. Clarifying Questions

None. All design points frozen per AC-DD-2 and AC-DD-6.

---

### Requirement AC-3: Stacking Acid DoT — EnemyEffectTracker and EnemyBase Extension

#### 1. Spec Summary

- **Description:** `EnemyEffectTracker` gains two new methods: `add_acid_stack(duration: float, dps: float) -> void` and `get_acid_stack_count() -> int`. `EnemyBase` gains one new method: `apply_acid_stack(duration: float, dps: float) -> void`. These enable independent, non-refreshing acid stacks that decay separately.
- **Constraints:**
  - `add_acid_stack()` generates a unique key by appending the current value of `_acid_stack_counter` (e.g., `"acid_stack_0"`, `"acid_stack_1"`, `"acid_stack_2"`), then increments `_acid_stack_counter`.
  - The counter is an instance variable initialized to `0` and never resets within the object's lifetime (no reset in `stop_all_effects()`). This prevents key collision with still-active stacks if the same counter value is recycled.
  - `get_acid_stack_count()` returns the count of active entries in `_active_dots` whose keys begin with `"acid_stack_"`. It returns `0` if none are active.
  - `stop_all_effects()` clears all acid stack entries along with all other active DoT entries (no change needed — `_active_dots.clear()` already removes all).
  - `EnemyBase.apply_acid_stack()` checks `_is_dead` (returns early if dead) and delegates to `_effect_tracker.add_acid_stack(duration, dps)`.
  - The existing `EnemyBase.apply_acid()` method and `EnemyEffectTracker.add_dot("acid", ...)` are not modified. They remain available for non-combo acid effects.
  - `dot_tick_requested` signal is emitted with the stack key (e.g., `"acid_stack_0"`) as the `effect_name` argument, consistent with the existing `_tick_dots()` loop.
- **Assumptions:** The `_acid_stack_counter` is per-instance. Two separate `EnemyEffectTracker` instances do not share the counter. This is the correct per-enemy isolation.
- **Scope:** `scripts/enemies/enemy_effect_tracker.gd` and `scripts/enemies/enemy_base.gd`.

#### 2. Acceptance Criteria

- **AC-3a:** After three calls to `enemy.apply_acid_stack(2.5, 0.4)` on the same enemy, `enemy.get_effect_tracker().get_acid_stack_count() == 3`.
- **AC-3b:** The three stacks are stored under keys `"acid_stack_0"`, `"acid_stack_1"`, `"acid_stack_2"` (assuming counter started at 0 for this enemy instance).
- **AC-3c:** Each stack has its own `remaining_duration` initialized to `2.5` and its own `dps` initialized to `0.4`.
- **AC-3d:** After stack `"acid_stack_0"` expires (its `remaining_duration` reaches 0), `get_acid_stack_count() == 2` (the other two stacks are unaffected).
- **AC-3e:** The three stacks tick independently: `dot_tick_requested` is emitted three times per tick interval (once per stack), each with its respective key and `tick_damage = dps * DOT_TICK_INTERVAL`.
- **AC-3f:** A fourth call to `apply_acid_stack()` after the first stack expires generates key `"acid_stack_3"` (counter was 3 at that point), not `"acid_stack_0"`.
- **AC-3g:** Calling `enemy.apply_acid()` (non-stacking) after `apply_acid_stack()` stores at key `"acid"` and does not affect any `"acid_stack_*"` entries.
- **AC-3h:** `get_acid_stack_count()` returns `0` on a freshly instantiated `EnemyEffectTracker`.
- **AC-3i:** `apply_acid_stack()` on a dead enemy (`_is_dead == true`) returns without adding any stack.
- **AC-3j:** `stop_all_effects()` sets `get_acid_stack_count() == 0` regardless of how many stacks were active.
- **AC-3k:** The `_acid_stack_counter` persists across `stop_all_effects()` calls: after `stop_all_effects()`, a subsequent `add_acid_stack()` call uses the next counter value (not 0), preventing key reuse during a rapid re-stack scenario.
- **AC-3l:** `EnemyBase` exposes `apply_acid_stack(duration: float, dps: float) -> void` as a public method callable via `has_method("apply_acid_stack")`.
- **AC-3m:** `EnemyBase` exposes access to `get_acid_stack_count()` either directly or by exposing `_effect_tracker` for test assertions. Recommended: add `func get_acid_stack_count() -> int` on `EnemyBase` that delegates to `_effect_tracker.get_acid_stack_count()`. This is the observable contract for test assertions per the ticket's `enemy.acid_stacks.size() == 3` requirement — tests must assert `enemy.get_acid_stack_count() == 3`, not access `enemy.acid_stacks` (that array does not exist and must not be created).

#### 3. Risk and Ambiguity Analysis

- **Counter persistence across stop_all_effects:** This is intentional (AC-3k). If the counter reset to 0 on `stop_all_effects()`, a rapid combo immediately after a stop would reuse `"acid_stack_0"`, potentially colliding with a still-active tick processing the cleared stack in the same frame. Counter monotonicity eliminates this race.
- **Key iteration in get_acid_stack_count():** `_active_dots.keys()` returns a GDScript `Array`. Iterating it to count keys starting with `"acid_stack_"` is O(n) where n is total active DoT count. In practice n is small (acid stacks plus at most one poison and one non-stack acid). No performance concern.
- **dot_tick_requested signal consumers:** The `EnemyBase._on_dot_tick_requested()` handler applies tick damage generically by `effect_name` (it calls `_apply_dot_damage(effect_name, tick_damage)`). Since `"acid_stack_0"` etc. are distinct from `"acid"`, the per-tick `dot_tick` signal on `EnemyBase` will emit `"acid_stack_0"` etc. as the effect name. Downstream systems (HUD, debug display) that key on `"acid"` by exact string will NOT see these ticks as acid. This is a known downstream integration concern outside this spec's scope; the damage application itself is correct.
- **Ticket fiction: enemy.acid_stacks.size():** The ticket AC used `enemy.acid_stacks.size() == 3`. This asserts a property that does not exist. The spec resolves this as: tests must use `enemy.get_acid_stack_count() == 3`. No `acid_stacks` array is introduced.

#### 4. Clarifying Questions

None. All design points frozen per AC-DD-3 and AC-DD-4.

---

### Requirement AC-4: AttackExecutor Modifier Dispatch for MELEE_SWIPE_COMBO

#### 1. Spec Summary

- **Description:** The `MELEE_SWIPE_COMBO` handler must apply acid stacks (not a single-refresh acid effect) when `modifiers["acid_on_hit"] == true`. This requires a new private method `_apply_combo_modifiers(target, modifiers, pre_damage_state)` on `AttackExecutor` that differs from `_apply_modifiers()` only in the acid dispatch: it calls `target.apply_acid_stack(duration, dps)` instead of `target.apply_acid(duration, dps)`.
- **Constraints:**
  - `_apply_combo_modifiers()` must honor `_is_dead` via `has_method` guard (same `has_method("apply_acid_stack")` check before calling).
  - All other modifier keys (`poison`, `slow`, `infect_weakened`) in `_apply_combo_modifiers()` behave identically to `_apply_modifiers()`.
  - `_apply_modifiers()` is not changed. It continues to call `apply_acid()` for `MELEE_SWIPE` and `SLAM_AOE` attacks.
  - The WEAKENED state duration-doubling (currently in `_apply_modifiers()` for acid) must also apply in `_apply_combo_modifiers()`. If `target.get_base_state() == 1` (WEAKENED), `acid_dur *= 2.0` before calling `apply_acid_stack`.
- **Assumptions:** No other fused attack currently uses `MELEE_SWIPE_COMBO`. This method is created for combo handlers generically; if a future combo also uses acid, it routes through the same `_apply_combo_modifiers()`.
- **Scope:** `scripts/attacks/attack_executor.gd`.

#### 2. Acceptance Criteria

- **AC-4a:** When `_apply_combo_modifiers()` is called with `modifiers = {"acid_on_hit": true, "acid_duration": 2.5, "acid_dps": 0.4}` on a NORMAL state enemy, `apply_acid_stack(2.5, 0.4)` is called on the enemy.
- **AC-4b:** When called on a WEAKENED state enemy, `apply_acid_stack(5.0, 0.4)` is called (duration doubled: 2.5 * 2.0 = 5.0).
- **AC-4c:** `apply_acid()` is NOT called when routing through `_apply_combo_modifiers()`.
- **AC-4d:** Calling `_apply_combo_modifiers()` on a target without the `apply_acid_stack` method (a bare enemy mock) does not crash.
- **AC-4e:** Non-acid modifiers (`poison`, `slow`, `infect_weakened`) in `_apply_combo_modifiers()` behave identically to `_apply_modifiers()`.

#### 3. Risk and Ambiguity Analysis

- **Parallel method duplication:** `_apply_combo_modifiers()` duplicates most of `_apply_modifiers()`. This is an intentional minimal approach — refactoring the shared logic is deferred to avoid breaking existing tests. Implementation agents must not merge the two methods into one parametric version unless all downstream tests continue to pass.
- **Pre-damage-state capture:** The `MELEE_SWIPE_COMBO` handler must capture `pre_state` before calling `_apply_damage()`, same as `_handle_melee_swipe()`. The captured state is passed to `_apply_combo_modifiers()` for the `infect_weakened` check.

#### 4. Clarifying Questions

None.

---

### Requirement AC-5: AttackDatabase Registration Update for acid_claw

#### 1. Spec Summary

- **Description:** The `_register_fused_defaults()` method in `attack_database.gd` must be updated to register the acid_claw attack with the normative M12-04 stat block (AC-DD-1). All affected named constants must be updated. Two new constants must be added. The registration must set `effect_type = "MELEE_SWIPE_COMBO"` and `combo_hits = ACID_CLAW_COMBO_HITS`.
- **Constraints:**
  - All numeric values must use named constants (existing DR-4 from FAR spec).
  - The attack_id remains 101 (ACID_CLAW_ATTACK_ID, unchanged).
  - The combo key `"acid_claw"` (sorted from "acid" and "claw") remains unchanged.
  - `combo_frame_interval` is stored in the modifiers dict as `"combo_frame_interval": ACID_CLAW_COMBO_FRAME_INTERVAL` (value 6). This allows the executor to read it without a new field on AttackResource.
  - The attack name changes from "Toxic Slash" to "Venomous Shred".
  - The description changes to reflect the 3-hit combo nature.
- **Assumptions:** No other code in the codebase references `ACID_CLAW_DAMAGE`, `ACID_CLAW_COOLDOWN`, etc. by name outside `attack_database.gd` except test files that assert the registered resource's field values. Test files asserting old values will correctly become RED (they must be updated during TEST_DESIGN to assert the new normative values).
- **Scope:** `scripts/attacks/attack_database.gd`.

#### 2. Acceptance Criteria

- **AC-5a:** `db.get_fused_attack("acid", "claw").damage == 1.8` (within float epsilon 0.001).
- **AC-5b:** `db.get_fused_attack("acid", "claw").cooldown == 2.0`.
- **AC-5c:** `db.get_fused_attack("acid", "claw").attack_range == 1.2`.
- **AC-5d:** `db.get_fused_attack("acid", "claw").knockback_magnitude == 80.0`.
- **AC-5e:** `db.get_fused_attack("acid", "claw").effect_type == "MELEE_SWIPE_COMBO"`.
- **AC-5f:** `db.get_fused_attack("acid", "claw").combo_hits == 3`.
- **AC-5g:** `db.get_fused_attack("acid", "claw").attack_id == 101`.
- **AC-5h:** `db.get_fused_attack("acid", "claw").attack_name == "Venomous Shred"`.
- **AC-5i:** `db.get_fused_attack("acid", "claw").modifiers.get("acid_on_hit") == true`.
- **AC-5j:** `db.get_fused_attack("acid", "claw").modifiers.get("acid_duration") == 2.5`.
- **AC-5k:** `db.get_fused_attack("acid", "claw").modifiers.get("acid_dps") == 0.4`.
- **AC-5l:** `db.get_fused_attack("acid", "claw").modifiers.get("combo_frame_interval") == 6`.
- **AC-5m:** The constant `ACID_CLAW_COMBO_HITS := 3` is declared in `attack_database.gd`.
- **AC-5n:** The constant `ACID_CLAW_COMBO_FRAME_INTERVAL := 6` is declared in `attack_database.gd`.
- **AC-5o:** All other five fused attack registrations (adhesion_claw, carapace_claw, acid_adhesion, acid_carapace, adhesion_carapace) are unchanged.

#### 3. Risk and Ambiguity Analysis

- **Pre-existing tests asserting old stats:** Tests written during M12-02 that assert `acid_claw.damage == 4.0` or `acid_claw.effect_type == "MELEE_SWIPE"` will become RED when this registration is updated. This is correct and expected — Test Designer must update the relevant assertions in the fused attack resources test suite to assert the new normative values. These are not test failures to fix by reverting the spec; they are test updates required by the spec change.
- **combo_hits field must exist before this registration can compile:** The implementation order must be: (1) Add `combo_hits` field to `AttackResource`, (2) Update `attack_database.gd` registration. If done in reverse order, GDScript will not error at parse time (the field just won't be set), but the AC-5f assertion will fail.

#### 4. Clarifying Questions

None. Stats frozen per AC-DD-1.

---

### Requirement AC-6: Full Combo Execution Integration

#### 1. Spec Summary

- **Description:** When a player with both "acid" and "claw" mutation slots fires a fused attack, the complete observable outcome is: 3 sequential hits over 0.2s total (hit 1 at t=0, hit 2 at t=0.1s, hit 3 at t=0.2s), each dealing 1.8 direct damage with 80.0-magnitude knockback, and each applying one acid stack (duration 2.5s, dps 0.4). After all 3 hits land on a single enemy, the enemy has 3 active acid stacks and has taken 5.4 total direct damage (3 × 1.8).
- **Constraints:**
  - The 2.0s cooldown (`_mutation_cooldowns["acid_claw"] = 2.0`) is set after the combo is fired (using the same composite-key cooldown model from FADI-DD-1).
  - The M12-04 DPS formula in the ticket: direct damage = 3 × 1.8 = 5.4 per combo; acid DoT per stack = 0.4 dps × 2.5s = 1.0 damage; 3 stacks = 3.0 total acid damage. Full combo damage = 5.4 + 3.0 = 8.4. This is informational; no DPS assertion is required in unit tests (DPS is validated via integration/balance tests outside this spec).
  - `run_tests.sh` must exit 0 after implementation (all M11 and M12 pre-existing tests remain GREEN).
- **Assumptions:** The player controller's `_try_attack()` routing (FADI-DD-1) requires no changes — it routes to `execute_attack(resource)` regardless of effect type. The new `MELEE_SWIPE_COMBO` case in `AttackExecutor` handles the rest.
- **Scope:** Integration of AC-1 through AC-5.

#### 2. Acceptance Criteria

- **AC-6a:** After a full 3-hit combo lands on a single enemy, `enemy.get_acid_stack_count() == 3`.
- **AC-6b:** After a full 3-hit combo, the enemy's `current_hp` has decreased by exactly 5.4 (3 × 1.8) from direct hit damage (before any DoT ticks).
- **AC-6c:** Each of the 3 acid stacks has `remaining_duration` initialized to 2.5s at the moment of application.
- **AC-6d:** The combo cooldown key `"acid_claw"` is set to `2.0` after the combo fires (consistent with FADI-DD-1 composite key model).
- **AC-6e:** The full combo completes (all 3 hits) in approximately 0.2s real time (2 inter-hit delays × 0.1s each), measurable via the number of timer awaits.
- **AC-6f:** An enemy that is killed by hit 2 (hp reaches 0) does not receive hit 3 (the `_is_dead` guard in `apply_acid_stack()` and `take_damage()` prevents further application).

#### 3. Risk and Ambiguity Analysis

- **Headless timer testing:** In GDScript unit tests running headless, `get_tree().create_timer()` may not tick at wall-clock speed. Test Designer must use signal-await patterns or mock the tree timer to control timing rather than relying on `await get_scene_tree().process_frame` N times. The observable contract is the count of hits and stacks, not wall-clock elapsed time.
- **Enemy kill mid-combo:** AC-6f is an edge case the Test Breaker must cover. The `take_damage()` guard in `EnemyBase` already sets `_is_dead = true` and stops DoTs. `apply_acid_stack()` must check `_is_dead` before delegating. The handler does not need to detect the enemy death between hits — the dead guard in each method suffices.

#### 4. Clarifying Questions

None.

---

## Non-Functional Requirements

| Requirement | Specification | Rationale |
|---|---|---|
| **AC-NF-1: Backward Compatibility** | All 237+ existing M11/M12 fused attack tests must remain GREEN after adding `combo_hits` to `AttackResource` and adding stacking methods to `EnemyEffectTracker`/`EnemyBase`. | No regressions on pre-existing functionality. |
| **AC-NF-2: Named Constants** | All numeric literals in `attack_database.gd` for acid_claw must use named constants (per FAR DR-4). No inline numeric literals in the registration block. | Consistent with existing codebase pattern; enables confident modification later. |
| **AC-NF-3: No New Global Classes** | `AcidVFXSystem` must not be created. No new autoload nodes. Stacking acid is a method extension on existing classes. | Minimal surface area; avoids global state complexity. |
| **AC-NF-4: Fail-Closed on Unknown effect_type** | The `_handle_unknown()` branch in `execute_attack()` continues to fire for any unrecognized effect type. Adding `MELEE_SWIPE_COMBO` does not remove this fallback. | Defense in depth for misregistered resources. |
| **AC-NF-5: GDScript Static Typing** | New methods and fields must use explicit GDScript static types: `var combo_hits: int`, `func add_acid_stack(duration: float, dps: float) -> void`, `func get_acid_stack_count() -> int`. | Required by existing code style and Ruff-equivalent GDScript linter. |
| **AC-NF-6: Test File Naming** | New test files must use behavior-descriptive names: `test_acid_claw_combo_attack.gd` (behavioral), `test_acid_claw_combo_adversarial.gd` (adversarial). No milestone IDs in filenames. Traceability (M12-04, AC-1 through AC-6) belongs in module docstring. | Mandated by CLAUDE.md project convention. |
| **AC-NF-7: run_tests.sh Exit 0** | `bash ci/scripts/run_tests.sh` (or `timeout 300 godot --headless -s tests/run_tests.gd`) must exit 0 after all implementation is complete. | Required gate before Stage COMPLETE. |

---

## Failure Modes and Error Handling

### Failure 1: combo_hits <= 0 on a MELEE_SWIPE_COMBO Resource

- **Detection:** `_handle_melee_swipe_combo()` checks `if resource.combo_hits <= 0` before the hit loop.
- **Behavior:** Handler returns immediately without executing any hits. `_is_active` is set to `false`. No `attack_hit` signal is emitted.
- **No error/warning:** Silent no-op is the correct behavior. The resource is technically valid (the default is 1; 0 is an unusual but not invalid value in the schema).
- **Test:** `test_combo_hits_zero_fires_no_hits` — creates a resource with `combo_hits = 0`, calls `execute_attack`, asserts zero `attack_hit` signals.

### Failure 2: apply_acid_stack on a Dead Enemy

- **Detection:** `EnemyBase.apply_acid_stack()` checks `if _is_dead: return`.
- **Behavior:** Stack is not added. `get_acid_stack_count()` is unchanged.
- **No error/warning:** Consistent with existing `apply_acid()` and `apply_poison()` dead guards.
- **Test:** `test_acid_stack_not_applied_to_dead_enemy` — kills enemy, calls `apply_acid_stack(2.5, 0.4)`, asserts `get_acid_stack_count() == 0`.

### Failure 3: get_tree() Null During Inter-Hit Delay

- **Detection:** `if get_tree() == null` before each `create_timer()` call.
- **Behavior:** Handler aborts the remaining hits, sets `_is_active = false`, returns.
- **No error/warning:** Consistent with existing null-tree guards in `_handle_melee_swipe()` and `_handle_slam_aoe()`.
- **Test:** `test_combo_aborts_on_null_tree` — removes executor from scene tree mid-combo, verifies no crash and `is_active() == false` afterward.

### Failure 4: Missing apply_acid_stack Method on Target

- **Detection:** `if target.has_method("apply_acid_stack")` before calling.
- **Behavior:** Acid stack is not applied. Direct damage and knockback proceed normally. No error/warning.
- **No error/warning:** Consistent with existing `has_method` guard pattern throughout `_apply_modifiers()`.
- **Test:** `test_combo_on_enemy_without_acid_stack_method` — uses a bare mock enemy without `apply_acid_stack`, verifies no crash and damage is applied.

---

## Schema and Contracts

### AttackResource Schema (post-M12-04)

Full field list with the new `combo_hits` field highlighted:

```
@export var attack_id: int = 0
@export var attack_name: String = ""
@export var description: String = ""
@export var effect_type: String = ""
@export var damage: float = 1.0
@export var cooldown: float = 0.8
@export var attack_range: float = 1.5
@export var startup_frames: int = 0
@export var combo_hits: int = 1            # NEW — default 1 for backward compat
@export var knockback_magnitude: float = 0.0
@export var knockback_direction: String = "away"
@export var projectile_speed: float = 0.0
@export var projectile_lifetime: float = 2.0
@export var color: Color = Color.WHITE
@export var vfx_scale: float = 1.0
@export var modifiers: Dictionary = {}
```

### acid_claw Registration Contract (normative)

```
attack_id:          101
attack_name:        "Venomous Shred"
description:        (implementation choice — must mention 3-hit combo and acid stacks)
effect_type:        "MELEE_SWIPE_COMBO"
damage:             1.8     (ACID_CLAW_DAMAGE)
cooldown:           2.0     (ACID_CLAW_COOLDOWN)
attack_range:       1.2     (ACID_CLAW_RANGE)
startup_frames:     0
combo_hits:         3       (ACID_CLAW_COMBO_HITS)
knockback_magnitude: 80.0   (ACID_CLAW_KNOCKBACK)
knockback_direction: "away"
color:              ACID_CLAW_COLOR (unchanged: Color(0.6, 0.85, 0.0))
vfx_scale:          1.3     (ACID_CLAW_VFX_SCALE, unchanged)
modifiers: {
    "acid_on_hit": true,
    "acid_duration": 2.5,   (ACID_CLAW_ACID_DURATION)
    "acid_dps":     0.4,    (ACID_CLAW_ACID_DPS)
    "combo_frame_interval": 6  (ACID_CLAW_COMBO_FRAME_INTERVAL)
}
```

### EnemyEffectTracker New API

```gdscript
# New field
var _acid_stack_counter: int = 0

# New methods
func add_acid_stack(duration: float, dps: float) -> void
    # Stores under "acid_stack_%d" % _acid_stack_counter
    # Increments _acid_stack_counter
    # Delegates to add_dot() internally with the indexed key

func get_acid_stack_count() -> int
    # Returns count of _active_dots keys starting with "acid_stack_"
```

### EnemyBase New API

```gdscript
func apply_acid_stack(duration: float, dps: float) -> void
    # Guards: if _is_dead: return
    # Delegates to _effect_tracker.add_acid_stack(duration, dps)

func get_acid_stack_count() -> int
    # Delegates to _effect_tracker.get_acid_stack_count()
    # Returns 0 if _effect_tracker is null
```

### AttackExecutor New Private Method

```gdscript
func _handle_melee_swipe_combo(resource: AttackResource) -> void
    # Async — called via _run_melee_swipe_combo_async()
    # Loop resource.combo_hits times:
    #   Optional startup delay (first hit only if startup_frames > 0)
    #   Query enemies in range
    #   For each enemy: capture pre_state, _apply_damage, _apply_combo_modifiers
    #   Emit attack_hit per enemy
    #   Emit melee_vfx_requested
    #   If not last hit: await timer(combo_frame_interval / FRAMES_PER_SECOND)

func _apply_combo_modifiers(target: Node3D, modifiers: Dictionary, pre_damage_state: int = -1) -> void
    # Identical to _apply_modifiers() except:
    #   acid_on_hit branch calls apply_acid_stack() instead of apply_acid()

func _run_melee_swipe_combo_async(resource: AttackResource) -> void
    # await _handle_melee_swipe_combo(resource)
    # _is_active = false
```

---

## Edge Cases

| ID | Edge Case | Behavior | Risk Level |
|----|-----------|----------|-----------|
| AC-EC-1 | Enemy out of range for hit 2 but in range for hit 1 and 3 | Hits 1 and 3 land; hit 2 misses. Per-hit fresh query. Each hit's acid stack and damage apply independently. | Medium — per-hit query is non-obvious but intended. |
| AC-EC-2 | Enemy killed by hit 1 | Hits 2 and 3: `take_damage()` returns early (dead guard), `apply_acid_stack()` returns early. No additional effects. | Medium — dead guard required in apply_acid_stack. |
| AC-EC-3 | Enemy already has one "acid" stack (from prior non-combo acid attack) | `get_acid_stack_count()` returns count of `"acid_stack_*"` only — the base `"acid"` key is NOT counted. The two systems are independent. | Low — explicit separation by key prefix. |
| AC-EC-4 | Three combo hits on WEAKENED enemy | Each hit's `_apply_combo_modifiers()` checks WEAKENED state; each stack gets doubled duration (5.0s). 3 stacks × 5.0s × 0.4 dps = 6.0 acid damage. | Medium — WEAKENED check must occur per-hit, not once at combo start. |
| AC-EC-5 | combo_hits = 1 (valid degenerate case) | Exactly one hit fires. One acid stack is applied. Behavior identical to a single MELEE_SWIPE except acid uses stacking path. | Low — default case. |
| AC-EC-6 | _is_active during combo; second execute_attack() called | Second call is silently ignored (existing re-entrancy guard at top of execute_attack()). First combo continues uninterrupted. | Low — existing guard covers this. |
| AC-EC-7 | acid_claw cooldown active; player tries to fire | _try_attack() checks _mutation_cooldowns["acid_claw"] > 0.0 and returns without firing (FADI-DD-1). No combo starts. | Low — composite key cooldown model handles this. |
| AC-EC-8 | Three combo hits on a single enemy that has another enemy behind it | Each hit queries ALL enemies in range independently. The secondary enemy receives hits and stacks it was in range for. | Low — intended area behavior consistent with MELEE_SWIPE. |
| AC-EC-9 | add_acid_stack called with duration = 0.0 | add_dot() guard: `if duration <= 0.0: return`. Stack is not stored. Counter is NOT incremented (no point consuming a counter slot for a no-op). | Medium — counter increment must be conditional on actual storage. |
| AC-EC-10 | MELEE_SWIPE_COMBO with no enemies in range | All three hit loops execute, each querying zero enemies. Zero attack_hit signals, zero acid stacks applied. melee_vfx_requested emitted 3 times (whiff VFX). | Low — consistent with MELEE_SWIPE whiff behavior. |

---

## Test Strategy (for Test Designer Agent)

### Files Required

All new test files must use behavior-descriptive names with no milestone IDs. Traceability belongs in module docstrings.

| File | Coverage | Minimum Test Functions |
|------|----------|----------------------|
| `tests/scripts/attacks/test_acid_claw_combo_attack.gd` | AC-1 through AC-6, AC-NF behavioral | 30 minimum |
| `tests/scripts/attacks/test_acid_claw_combo_adversarial.gd` | AC-EC-1 through AC-EC-10, failure modes, mid-combo kills | 20 minimum |
| `tests/scripts/enemies/test_enemy_acid_stacking.gd` | AC-3 in isolation (no executor) | 15 minimum |

### Mandatory Test Categories

**AttackResource extension (AC-1):**
- Default combo_hits == 1 on new instance
- Explicit combo_hits = 3 assignment and readback
- acid_claw registered resource has combo_hits == 3

**MELEE_SWIPE_COMBO handler (AC-2):**
- 3 attack_hit signals for combo_hits = 3
- 0 attack_hit signals for combo_hits = 0
- attack_started emitted exactly once
- melee_vfx_requested emitted 3 times
- _is_active false after combo completes
- _is_active true during combo (cannot start second)
- Inter-hit timer invoked with correct interval

**Acid stacking (AC-3):**
- 3 calls → get_acid_stack_count() == 3
- Each stack independent duration
- First stack expiry doesn't affect second and third
- apply_acid_stack on dead enemy: no stack
- Counter monotonicity across stop_all_effects

**Modifier dispatch (AC-4):**
- acid_on_hit calls apply_acid_stack not apply_acid
- WEAKENED doubles acid_duration per hit
- Missing apply_acid_stack method: no crash

**Database registration (AC-5):**
- All 11 field assertions (AC-5a through AC-5l)
- Other 5 fused attacks unchanged (spot check effect_type and damage)

**Integration (AC-6):**
- Full combo: 3 stacks, 5.4 direct damage
- Mid-combo kill: no post-death stacks
- WEAKENED combo: doubled duration stacks

### Adversarial Priorities

1. Mid-combo null tree abort (does not crash, is_active resets)
2. Combo on enemy with no apply_acid_stack method (no crash)
3. Rapid re-fire attempt mid-combo (second call blocked)
4. combo_hits = -1 (no crash, no hits)
5. All three hits miss (whiff: no stacks, no damage, vfx still fires)
6. WEAKENED check per-hit vs once (assert 3 stacks at 5.0s not 2.5s on WEAKENED enemy)

---

## Deferred Scope

### Not in Scope for M12-04

1. **Melee swipe sound triggers:** The ticket AC mentions "melee swipe sound triggers per hit." The signal contract (`melee_vfx_requested` per hit) is defined here; actual audio system hookup is outside `AttackExecutor`'s domain and outside this spec's scope. Audio integration is a separate ticket concern.

2. **Poison VFX color overlay per stack:** The `melee_vfx_requested` signal is emitted per hit. Rendering a per-stack color overlay on the enemy is a visual/HUD system concern. `AttackExecutor` emits the signal; rendering is downstream and out of scope.

3. **Debug display for 3 stacks visible:** The ticket AC mentions "3 simultaneous stacks visible in enemy debug display." Debug display implementation is not in scope. The observable contract for tests is `get_acid_stack_count() == 3`.

4. **Balance validation in test encounters:** The ticket AC mentions "attack balanced in test encounters." Balance is a design-time concern, not a unit-test assertion. The DPS formula (5.4 direct + 3.0 acid = 8.4 total per full combo) is documented here for reference.

5. **Lunge effect type:** Listed in the M11-04 spec as one of 4 effect types. Not implemented in AttackExecutor. Not in scope here.

6. **attacks.json file:** The ticket AC mentions "Attacks database entry created (attacks.json)." No `attacks.json` file exists in this repository; all attack registrations are done via `_register_defaults()` in `attack_database.gd`. No JSON file is created or modified.

---

## Checkpoint Log Reference

Assumptions made during this spec run are logged at:
`project_board/checkpoints/M12-04/2026-05-29T-spec-run.md`

Pre-planning gap analysis (5 gaps, all resolved):
`project_board/checkpoints/M12-04/2026-05-29T-plan-run.md`

---

## Revision History

| Revision | Date | Agent | Change |
|----------|------|-------|--------|
| 1.0 | 2026-05-29 | Spec Agent | Initial frozen spec. Resolves all 5 planning gaps: MELEE_SWIPE_COMBO contract (AC-2), AcidVFXSystem fiction → real API (AC-3/AC-DD-3), stacking mechanism via indexed keys (AC-3/AC-DD-4), AttackResource schema extension (AC-1/AC-DD-5), stat conflict resolved with M12-04 ticket AC as normative (AC-DD-1). |
