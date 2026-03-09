# Spec: Two Mutation Slots
**Ticket:** `two_mutation_slots.md`
**Epic:** Milestone 3 – Dual Mutation + Fusion
**Spec Stage:** SPECIFICATION
**Last Updated By:** Spec Agent
**Date:** 2026-03-08

---

## Context Summary

The current system owns a single `MutationSlot` (`scripts/mutation_slot.gd`) that is instantiated inside `InfectionInteractionHandler`. `PlayerController3D` reads `is_filled()` from that slot to apply a 1.25x speed multiplier. `InfectionUI` reads the slot to drive a single HUD label and icon. `InfectionAbsorbResolver` fills the slot on successful absorb via duck-typed `set_active_mutation_id`.

This spec extends that system to two independent mutation slots managed by a new pure-logic coordinator `MutationSlotManager`. The `MutationSlot` class API is frozen and must not be modified.

---

## Out of Scope (Explicit)

The following behaviors are explicitly **not** covered by this spec and must not be implemented under this ticket:

- Fusion rules: how slot A and slot B combine to produce a hybrid mutation.
- Hybrid mutation IDs or any mutation effect that reads both slot values simultaneously.
- Slot consumption on fusion (which slot is cleared after fusing).
- Player-directed slot selection (player choosing which slot to fill).
- Any mutation effect other than the existing flat 1.25x speed multiplier.
- Persistence or save/load of slot state across sessions.
- A second chunk (covered by `second_chunk_logic.md`).
- Any visual beyond two always-visible slot label/icon pairs in the HUD.

These items are addressed by `slot_consumption_rules.md`, `fusion_rules_and_hybrid.md`, and `second_chunk_logic.md`.

---

## Requirement DSM-1: `MutationSlotManager` Pure-Logic Class

### 1. Spec Summary

**Description:** A new GDScript file `scripts/mutation_slot_manager.gd` defines `class_name MutationSlotManager extends RefCounted`. It owns exactly two `MutationSlot` instances, referred to as slot A (index 0) and slot B (index 1). It exposes the following public API:

| Method | Signature | Returns |
|--------|-----------|---------|
| `get_slot` | `get_slot(index: int) -> RefCounted` | The `MutationSlot` at the given index, or `null` if index is out of range. |
| `fill_next_available` | `fill_next_available(id: String) -> void` | Fills the next available slot per the fill-order rule (see DSM-2). |
| `get_slot_count` | `get_slot_count() -> int` | Returns `2` always. |
| `any_filled` | `any_filled() -> bool` | Returns `true` if at least one slot `is_filled()`; `false` if both are empty. |
| `clear_all` | `clear_all() -> void` | Calls `clear()` on both slots. |
| `clear_slot` | `clear_slot(index: int) -> void` | Calls `clear()` on the slot at the given index. No-op if index is out of range. |

**Constraints:**
- `MutationSlotManager` must be `extends RefCounted` (not a Node).
- Must not modify `scripts/mutation_slot.gd`.
- Both slot instances are created in `_init()` or equivalent initialization; they are never null during the manager's lifetime.
- `get_slot` with an out-of-range index (any integer not equal to 0 or 1) returns `null` and does not crash.
- `clear_slot` with an out-of-range index is a no-op (no crash, no error).
- `fill_next_available` with an empty string (`""`) must be handled safely; see DSM-2 for the exact rule.

**Assumptions:**
- Two slots is the fixed capacity for this ticket. Parameterizing the count is out of scope.
- The manager uses duck-typed calls into `MutationSlot` (`is_filled()`, `set_active_mutation_id()`, `clear()`); it does not cast to a typed `MutationSlot` variable, to remain consistent with existing codebase patterns.

**Scope:** `scripts/mutation_slot_manager.gd` only. No other files are modified under DSM-1.

### 2. Acceptance Criteria

- **DSM-1-AC-1:** `MutationSlotManager` can be instantiated headlessly via `load("res://scripts/mutation_slot_manager.gd").new()` without a scene tree.
- **DSM-1-AC-2:** `get_slot_count()` returns exactly `2` on a freshly instantiated manager.
- **DSM-1-AC-3:** `get_slot(0)` returns a non-null object that has `is_filled()`, `get_active_mutation_id()`, `set_active_mutation_id(id)`, and `clear()` methods.
- **DSM-1-AC-4:** `get_slot(1)` returns a non-null object with the same methods as DSM-1-AC-3.
- **DSM-1-AC-5:** `get_slot(0)` and `get_slot(1)` return **different** object references (the two slots are independent instances).
- **DSM-1-AC-6:** `get_slot(-1)`, `get_slot(2)`, and `get_slot(99)` all return `null` without crashing.
- **DSM-1-AC-7:** `clear_slot(-1)` and `clear_slot(2)` do not crash or emit any error.
- **DSM-1-AC-8:** `MutationSlotManager` is not a `Node` (i.e., `manager is Node` evaluates to `false`).
- **DSM-1-AC-9:** Two independently instantiated `MutationSlotManager` instances do not share slot state — writing to one does not affect the other.

### 3. Risk & Ambiguity Analysis

- **Risk:** If `MutationSlot` is instantiated via script load rather than `MutationSlot.new()`, the class name alias may not be available in headless test contexts. Implementation should use `preload("res://scripts/mutation_slot.gd").new()` for deterministic headless loading.
- **Edge case:** Calling methods on the result of `get_slot()` with an out-of-range index would crash if the caller does not null-check. The spec does not require the manager to protect callers; callers are responsible for index validation. This must be noted in code comments.

### 4. Clarifying Questions

None. All ambiguities resolved via checkpointed assumptions (see CHECKPOINTS.md).

---

## Requirement DSM-2: Fill-Order Rule

### 1. Spec Summary

**Description:** `fill_next_available(id: String)` implements a deterministic, first-available fill with last-absorb-wins fallback:

1. If slot A (`index 0`) is empty, fill slot A with `id`. Done.
2. Else if slot B (`index 1`) is empty, fill slot B with `id`. Done.
3. Else (both slots are filled), overwrite slot B with `id`. Done.

"Fill" means calling `set_active_mutation_id(id)` on the target slot.

**Empty-string guard:** If `id == ""`, `fill_next_available` must call `push_error` with a descriptive message and return without modifying any slot. This prevents silent slot corruption via the absorb resolver passing an empty ID.

**Constraints:**
- The fill order is fixed: A before B. There is no mechanism to prefer B first.
- Slot A is never overwritten by `fill_next_available` when slot A is filled and slot B is available or empty. Slot A is only overwritten if `clear_slot(0)` or `clear_all()` is called explicitly.
- The last-absorb-wins behavior for slot B (rule 3 above) matches the existing single-slot behavior where calling `set_active_mutation_id` on an already-filled slot overwrites the previous ID.

**Assumptions:**
- This fill strategy is intentionally simple. If the design later requires player-directed slot selection, that is a new ticket.
- "Both full — overwrite B" is a conservative choice that preserves slot A (the primary/oldest mutation) and lets the player keep filling by absorbing new enemies. The player will see slot B update in the HUD.

**Scope:** `fill_next_available` method in `MutationSlotManager`.

### 2. Acceptance Criteria

- **DSM-2-AC-1:** After `fill_next_available("mutation_a")` on an empty manager, `get_slot(0).get_active_mutation_id()` equals `"mutation_a"` and `get_slot(1).is_filled()` is `false`.
- **DSM-2-AC-2:** After `fill_next_available("mutation_a")` then `fill_next_available("mutation_b")`, `get_slot(0).get_active_mutation_id()` equals `"mutation_a"` and `get_slot(1).get_active_mutation_id()` equals `"mutation_b"`.
- **DSM-2-AC-3:** After `fill_next_available("mutation_a")`, `fill_next_available("mutation_b")`, then `fill_next_available("mutation_c")` (both slots were already full), `get_slot(0).get_active_mutation_id()` equals `"mutation_a"` (slot A unchanged) and `get_slot(1).get_active_mutation_id()` equals `"mutation_c"` (slot B overwritten).
- **DSM-2-AC-4:** After `fill_next_available("")` on an empty manager, both slots remain empty and `any_filled()` returns `false`. No crash occurs.
- **DSM-2-AC-5:** `fill_next_available("x")` after `clear_slot(0)` on a fully-filled manager fills slot A (not slot B), because slot A is now empty.

### 3. Risk & Ambiguity Analysis

- **Risk:** Players may find the "slot A never overwritten" rule unintuitive (you always lose your most recent slot B mutation, not your oldest). The spec chooses this conservatively to preserve the oldest mutation. This is a known UX trade-off and should be surfaced to the designer before implementation ships.
- **Checkpoint logged:** "last-absorb-wins for slot B" was already recorded in CHECKPOINTS.md as a planner assumption; this spec formalizes it.

### 4. Clarifying Questions

None.

---

## Requirement DSM-3: Speed-Buff Effect Rule

### 1. Spec Summary

**Description:** The existing 1.25x speed multiplier (`_MUTATION_SPEED_MULTIPLIER` in `PlayerController3D`) is applied if and only if `any_filled()` returns `true` on the `MutationSlotManager`. The multiplier is flat and applied once — filling both slots does not stack the multiplier.

Exact speed formula (unchanged from single-slot behavior):
```
effective_max_speed = _base_max_speed * (1.25 if manager.any_filled() else 1.0)
```

**Constraints:**
- The multiplier constant `1.25` remains unchanged from the existing `_MUTATION_SPEED_MULTIPLIER`.
- `_base_max_speed` is captured once in `_ready()` from `_simulation.max_speed`, same as today.
- The speed buff is active as long as at least one slot is filled. It deactivates only when both slots are cleared.
- No new speed multiplier values are introduced under this ticket.
- Stacking (e.g., `1.25^2 = 1.5625` when both slots are filled) is explicitly out of scope.

**PlayerController3D wiring:** The controller's `_ready()` must prefer fetching a `MutationSlotManager` via `get_mutation_slot_manager()` from `InfectionInteractionHandler` (if that method exists). It falls back to `get_mutation_slot()` if `get_mutation_slot_manager()` is not available. The speed-buff check in `_physics_process` must switch from `_mutation_slot.is_filled()` to `_slot_manager.any_filled()` when a manager is available.

**Assumptions:**
- If the controller still holds only a single `MutationSlot` reference (the backward-compat fallback), the existing `is_filled()` check continues to work as before, so existing movement tests remain green.

**Scope:** Speed-buff logic in `scripts/player_controller_3d.gd`; `any_filled()` in `MutationSlotManager`.

### 2. Acceptance Criteria

- **DSM-3-AC-1:** When both slots are empty, `any_filled()` returns `false` and `_simulation.max_speed == _base_max_speed`.
- **DSM-3-AC-2:** When slot A is filled and slot B is empty, `any_filled()` returns `true` and `_simulation.max_speed == _base_max_speed * 1.25`.
- **DSM-3-AC-3:** When slot B is filled and slot A is empty, `any_filled()` returns `true` and `_simulation.max_speed == _base_max_speed * 1.25`.
- **DSM-3-AC-4:** When both slots are filled, `any_filled()` returns `true` and `_simulation.max_speed == _base_max_speed * 1.25` (no stacking — same as one filled slot).
- **DSM-3-AC-5:** After `clear_all()`, `any_filled()` returns `false` and `_simulation.max_speed` returns to `_base_max_speed` (within float precision; `abs(actual - expected) < 0.001`).
- **DSM-3-AC-6:** `any_filled()` on a fresh (empty) manager returns `false`.

### 3. Risk & Ambiguity Analysis

- **Risk:** `_base_max_speed` is captured in `_ready()`; if `_simulation.max_speed` is modified before `_ready()` completes, the base may be wrong. This is pre-existing behavior, not introduced by this ticket.
- **Edge case:** If `InfectionInteractionHandler` is not present in the scene, the controller falls back gracefully with no slot manager, and no speed buff is applied (safe default).

### 4. Clarifying Questions

None.

---

## Requirement DSM-4: HUD Layout — Two Slot Labels and Icons

### 1. Spec Summary

**Description:** `InfectionUI` (`scripts/infection_ui.gd`) and `game_ui.tscn` are updated to show two independent, always-visible slot displays. Each slot display consists of:

- A `Label` node showing the slot's current state text.
- A `ColorRect` node showing the slot's icon color.

The two displays are driven independently by `manager.get_slot(0)` and `manager.get_slot(1)`.

**Node naming convention (exact names required by implementation):**

| Slot | Label node name | Icon node name |
|------|----------------|----------------|
| A (index 0) | `MutationSlot1Label` | `MutationIcon1` |
| B (index 1) | `MutationSlot2Label` | `MutationIcon2` |

The existing nodes named `MutationSlotLabel` and `MutationIcon` (singular, no number) continue to exist in the scene to avoid breaking any scene references or currently-running tests that query them by name. They become legacy nodes and are either hidden or maintained to reflect slot A's state — the implementation agent will decide; the spec requires they do not crash any test.

**Label text format (per slot):**

| Slot state | Label text | Label modulate color |
|------------|-----------|---------------------|
| Filled (id known) | `"Slot [N]: [id] active"` where N is 1 or 2 | `Color(0.9, 1.0, 0.9, 1.0)` (light green) |
| Empty | `"Slot [N]: Empty"` where N is 1 or 2 | `Color(0.7, 0.7, 0.7, 1.0)` (grey) |

**Icon color (per slot):**

| Slot state | ColorRect color |
|------------|----------------|
| Filled | `Color(0.4, 0.85, 0.55, 1.0)` (green) |
| Empty | `Color(0.2, 0.2, 0.2, 0.6)` (dark grey) |

**Always-visible:** Both slot labels and both icons are always `visible = true`. They are never hidden regardless of slot state.

**Constraints:**
- `InfectionUI._ready()` must prefer calling `get_mutation_slot_manager()` on `InfectionInteractionHandler` and storing the result; if that method is unavailable it falls back to `get_mutation_slot()` for legacy behavior.
- `_update_mutation_display()` drives both slot displays each `_process` frame.
- The update is independent: filling or clearing slot A does not affect the display of slot B, and vice versa.
- No fusion-state display is added in this ticket.

**Assumptions:**
- Exact visual layout (horizontal vs. vertical, spacing, font sizes) is the Presentation Agent's responsibility; the spec only defines node names, text formats, and colors.
- The absorb-feedback flash (800 ms green flash) continues to apply to `MutationLabel` (the global mutation count label) unchanged from existing behavior.

**Scope:** `scripts/infection_ui.gd` and `scenes/game_ui.tscn` (scene must add `MutationSlot1Label`, `MutationIcon1`, `MutationSlot2Label`, `MutationIcon2` nodes).

### 2. Acceptance Criteria

- **DSM-4-AC-1:** Both `MutationSlot1Label` and `MutationSlot2Label` are always `visible = true`, independent of slot fill state.
- **DSM-4-AC-2:** Both `MutationIcon1` and `MutationIcon2` are always `visible = true`, independent of slot fill state.
- **DSM-4-AC-3:** When slot A is empty, `MutationSlot1Label.text == "Slot 1: Empty"` and `MutationIcon1.color == Color(0.2, 0.2, 0.2, 0.6)`.
- **DSM-4-AC-4:** When slot A is filled with id `"infection_mutation_01"`, `MutationSlot1Label.text == "Slot 1: infection_mutation_01 active"` and `MutationIcon1.color == Color(0.4, 0.85, 0.55, 1.0)`.
- **DSM-4-AC-5:** When slot B is empty, `MutationSlot2Label.text == "Slot 2: Empty"` and `MutationIcon2.color == Color(0.2, 0.2, 0.2, 0.6)`.
- **DSM-4-AC-6:** When slot B is filled with id `"infection_mutation_01"`, `MutationSlot2Label.text == "Slot 2: infection_mutation_01 active"` and `MutationIcon2.color == Color(0.4, 0.85, 0.55, 1.0)`.
- **DSM-4-AC-7:** Filling slot A does not change the display of slot B, and vice versa (independent rendering).
- **DSM-4-AC-8:** Existing `MutationSlotLabel` (singular) does not crash when queried; it is either hidden or shows slot A state.
- **DSM-4-AC-9:** `timeout 120 godot --headless --check-only` exits 0 after changes to `infection_ui.gd` and `game_ui.tscn`.

### 3. Risk & Ambiguity Analysis

- **Risk:** `game_ui.tscn` is a scene file; adding nodes must be done carefully to preserve existing node paths. If the Presentation Agent adds nodes with names that conflict with existing references (e.g., something named `MutationSlotLabel1` when code queries `MutationSlot1Label`), the display will silently fail (returns null, label not updated). The exact names in the table above are binding.
- **Risk:** The existing `infection_ui.gd` references `PlayerController` (the 2D class) via `get_first_node_in_group("player")`. This pre-existing issue is out of scope; do not fix or break it.
- **Checkpoint logged:** Two-slot HUD layout was logged as a planner checkpoint (CHECKPOINTS.md).

### 4. Clarifying Questions

None.

---

## Requirement DSM-5: Backward Compatibility — `MutationSlot` API Frozen; `get_mutation_slot()` Alias

### 1. Spec Summary

**Description:** Two backward-compatibility guarantees must be maintained:

**5A — `MutationSlot` API frozen:** The file `scripts/mutation_slot.gd` and the `MutationSlot` class must not be modified. All existing public methods (`is_filled()`, `get_active_mutation_id()`, `set_active_mutation_id(id: String)`, `clear()`) continue to exist with identical signatures and behavior. All tests in `test_mutation_slot_system_single.gd` must remain green with zero failures.

**5B — `get_mutation_slot()` alias on `InfectionInteractionHandler`:** The method `get_mutation_slot() -> RefCounted` continues to exist on `InfectionInteractionHandler`. It returns the `MutationSlot` at index 0 (slot A) from the `MutationSlotManager`. This alias is the single source of backward compatibility for any caller that was not updated to use `get_mutation_slot_manager()`.

New method added: `get_mutation_slot_manager() -> RefCounted` returns the full `MutationSlotManager` instance. Updated callers (`PlayerController3D`, `InfectionUI`) must call `get_mutation_slot_manager()` first and fall back to `get_mutation_slot()` only if the new method is unavailable (via `has_method` guard).

**Constraints:**
- `get_mutation_slot()` must not be removed, renamed, or have its return type changed.
- The return value of `get_mutation_slot()` must be a `MutationSlot` instance (or duck-type equivalent with all four methods), not the `MutationSlotManager`.
- The absorb resolver (`InfectionAbsorbResolver`) must also maintain backward compatibility: `resolve_absorb(esm, inv)` with no slot argument continues to work; `resolve_absorb(esm, inv, slot)` where `slot` is a single `MutationSlot` continues to work; `resolve_absorb(esm, inv, manager)` where `manager` is a `MutationSlotManager` is the new preferred form.

**Assumptions:**
- Duck-typing via `has_method("fill_next_available")` is sufficient to distinguish a `MutationSlotManager` from a single `MutationSlot` in the resolver.
- No hard `is` type check is used anywhere in the wiring (consistent with existing codebase patterns).

**Scope:** `scripts/infection_interaction_handler.gd`, `scripts/infection_absorb_resolver.gd`.

### 2. Acceptance Criteria

- **DSM-5-AC-1:** All tests in `tests/system/test_mutation_slot_system_single.gd` pass (0 failures) after the dual-slot system is fully implemented.
- **DSM-5-AC-2:** `InfectionInteractionHandler.get_mutation_slot()` returns a non-null object with `is_filled()`, `get_active_mutation_id()`, `set_active_mutation_id(id)`, and `clear()`.
- **DSM-5-AC-3:** The object returned by `get_mutation_slot()` is the same instance as `get_mutation_slot_manager().get_slot(0)` (i.e., slot A, not a copy).
- **DSM-5-AC-4:** `InfectionInteractionHandler.get_mutation_slot_manager()` returns a non-null object with `any_filled()`, `fill_next_available(id)`, `get_slot(index)`, `get_slot_count()`, `clear_all()`, and `clear_slot(index)`.
- **DSM-5-AC-5:** `InfectionAbsorbResolver.resolve_absorb(esm, inv)` (two-argument form, no slot) does not crash and transitions the ESM to dead.
- **DSM-5-AC-6:** `InfectionAbsorbResolver.resolve_absorb(esm, inv, single_slot)` where `single_slot` is a `MutationSlot` continues to call `single_slot.set_active_mutation_id(DEFAULT_MUTATION_ID)`.
- **DSM-5-AC-7:** `InfectionAbsorbResolver.resolve_absorb(esm, inv, manager)` where `manager` is a `MutationSlotManager` calls `manager.fill_next_available(DEFAULT_MUTATION_ID)` instead of `set_active_mutation_id`.
- **DSM-5-AC-8:** `scripts/mutation_slot.gd` file content is byte-for-byte identical to its pre-ticket state (no modifications).

### 3. Risk & Ambiguity Analysis

- **Risk:** If `InfectionAbsorbResolver.resolve_absorb` is updated to check `has_method("fill_next_available")` and call it, but a future object also happens to have that method by coincidence, the duck-type dispatch could route incorrectly. This is low probability given the codebase size; document the dispatch logic in a comment.
- **Risk:** The existing `test_mutation_slot_system_single.gd` tests create `MutationSlot` directly from the script, not via `MutationSlotManager`. They must continue to pass because `MutationSlot` is untouched.

### 4. Clarifying Questions

None.

---

## Requirement DSM-6: `InfectionAbsorbResolver` — Dual-Slot Dispatch

### 1. Spec Summary

**Description:** The existing `resolve_absorb(esm, inv, slot: Object = null)` method in `InfectionAbsorbResolver` is updated so that the third argument can be either:
- `null` (no slot update),
- a single `MutationSlot` (detected by `has_method("set_active_mutation_id")` and NOT having `fill_next_available`), or
- a `MutationSlotManager` (detected by `has_method("fill_next_available")`).

Dispatch rules:

| Third argument | Action |
|----------------|--------|
| `null` | No slot operation. ESM dies and inventory is granted as before. |
| Single slot (has `set_active_mutation_id`, no `fill_next_available`) | `slot.set_active_mutation_id(DEFAULT_MUTATION_ID)` — existing behavior unchanged. |
| Manager (has `fill_next_available`) | `manager.fill_next_available(DEFAULT_MUTATION_ID)` — fills next available slot per DSM-2. |

The method signature does not change: `resolve_absorb(esm: EnemyStateMachine, inv: Object, slot: Object = null) -> void`.

**Constraints:**
- The `DEFAULT_MUTATION_ID` constant (`"infection_mutation_01"`) is unchanged.
- Both `can_absorb()` check and `esm.apply_death_event()` + `inv.grant()` calls are unchanged regardless of slot argument type.
- Error handling: if `slot` is non-null but has neither `set_active_mutation_id` nor `fill_next_available`, emit `push_error` and skip the slot update without crashing.

**Assumptions:**
- No other mutation IDs are introduced by this ticket; only `DEFAULT_MUTATION_ID` is granted.

**Scope:** `scripts/infection_absorb_resolver.gd`.

### 2. Acceptance Criteria

- **DSM-6-AC-1:** `resolve_absorb(infected_esm, inv, null)` kills the ESM and grants inventory entry; no crash.
- **DSM-6-AC-2:** `resolve_absorb(infected_esm, inv, single_slot)` kills ESM, grants inventory, and calls `single_slot.set_active_mutation_id("infection_mutation_01")`.
- **DSM-6-AC-3:** `resolve_absorb(infected_esm, inv, manager)` kills ESM, grants inventory, and calls `manager.fill_next_available("infection_mutation_01")`.
- **DSM-6-AC-4:** `resolve_absorb(infected_esm, inv, bogus_object)` where `bogus_object` has neither method: ESM dies, inventory granted, no crash, `push_error` is called.
- **DSM-6-AC-5:** `resolve_absorb(non_infected_esm, inv, manager)` returns without modifying ESM, inventory, or manager (existing guard unchanged).

### 3. Risk & Ambiguity Analysis

- **Risk:** A `MutationSlotManager` technically also has `set_active_mutation_id` if GDScript call forwarding is used. The dispatch must check `fill_next_available` first (higher-specificity check) to avoid routing a manager through the single-slot path.
- **Mitigation:** Check `has_method("fill_next_available")` first, then `has_method("set_active_mutation_id")`.

### 4. Clarifying Questions

None.

---

## Non-Functional Requirements

### NFR-1: Pure-Logic Isolation

`MutationSlotManager` must be instantiable headlessly (no scene tree, no Node parent) for unit testing. All test suites must be executable via `timeout 300 godot --headless -s tests/run_tests.gd`.

### NFR-2: Typed GDScript

All new and modified GDScript files use typed variables and return types wherever GDScript static typing supports them. `Object` or untyped return types are acceptable only where duck-typing is intentional (e.g., `get_slot() -> RefCounted` returning a `MutationSlot` instance).

### NFR-3: No Silent Failures

Critical error paths (empty ID passed to `fill_next_available`, unknown object type passed to resolver) must call `push_error(...)` with a descriptive message. Non-critical no-op paths (out-of-range index in `clear_slot`) may silently return.

### NFR-4: No Magic Strings

The mutation ID `"infection_mutation_01"` must remain a named constant (`DEFAULT_MUTATION_ID`) in `InfectionAbsorbResolver`. New code must reference this constant, not a hard-coded string literal.

### NFR-5: Godot Syntax Validity

After all file edits, `timeout 120 godot --headless --check-only` must exit 0 (no syntax errors).

### NFR-6: Test Suite Integration

Both `tests/system/test_mutation_slot_system_dual.gd` and `tests/system/test_mutation_slot_system_dual_adversarial.gd` must be registered in `tests/run_tests.gd` under the `# --- system ---` section. The full suite `timeout 300 godot --headless -s tests/run_tests.gd` must exit 0.

---

## Requirement-to-Ticket AC Cross-Reference

| Ticket AC | Covered By |
|-----------|-----------|
| Two mutation slots exist and can be filled independently via infection/absorb | DSM-1, DSM-2, DSM-6 |
| Slot assignment (which chunk or which slot) is clear and consistent | DSM-2 (fill-order rule fully specified) |
| Both mutations can be used or fused per fusion rules | DSM-3 (use: speed buff); fusion is out of scope |
| Slot consumption rules apply when fusing | Explicitly out of scope (slot_consumption_rules.md) |
| Dual-slot system is human-playable in-editor: both slots, contents, and UI visible without debug overlays | DSM-4 (two always-visible slot labels + icons) |

---

## Implementation File Ownership Summary

| File | Owner Task | Change Type |
|------|-----------|-------------|
| `scripts/mutation_slot_manager.gd` | Task 4 (Core Simulation Agent) | Create new |
| `scripts/mutation_slot.gd` | None — FROZEN | No change |
| `scripts/infection_absorb_resolver.gd` | Task 5 (Core Simulation Agent) | Modify |
| `scripts/infection_interaction_handler.gd` | Task 6 (Gameplay Systems Agent) | Modify |
| `scripts/player_controller_3d.gd` | Task 7 (Gameplay Systems Agent) | Modify |
| `scripts/infection_ui.gd` | Task 8 (Presentation Agent) | Modify |
| `scenes/game_ui.tscn` | Task 8 (Presentation Agent) | Modify |
| `tests/system/test_mutation_slot_system_dual.gd` | Task 2 (Test Designer Agent) | Create new |
| `tests/system/test_mutation_slot_system_dual_adversarial.gd` | Task 3 (Test Breaker Agent) | Create new |
| `tests/run_tests.gd` | Task 9 (Core Simulation Agent) | Modify |
