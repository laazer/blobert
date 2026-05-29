# M12-04 Static QA Fix Run — 2026-05-29

**Agent:** Gameplay Systems Agent
**Ticket:** M12-04 (Acid+Claw Fusion Attack — Venomous Shred)
**Stage:** STATIC_QA (fix pass)
**Run ID:** 2026-05-29T-static-qa-fix-run

---

## Issues Fixed

### CRITICAL-1: MELEE_SWIPE_COMBO async wrapper fix

**File:** `scripts/attacks/attack_executor.gd`, line 39-41

Changed dispatch from direct handler call to async wrapper pattern, mirroring SLAM_AOE exactly:

Before:
```gdscript
"MELEE_SWIPE_COMBO":
    _handle_melee_swipe_combo(resource)
```

After:
```gdscript
"MELEE_SWIPE_COMBO":
    _run_melee_swipe_combo_async(resource)
    return
```

The `_run_melee_swipe_combo_async` function already existed at lines 52-54 but was dead code. It now receives the dispatch. The early `return` prevents `execute_attack` from reaching `_is_active = false` at line 44; the async wrapper is responsible for clearing `_is_active` after all hits complete.

This means `execute_attack` does NOT touch `_is_active` for the MELEE_SWIPE_COMBO path (returns before reaching the assignment), and `_run_melee_swipe_combo_async` clears `_is_active` after `await _handle_melee_swipe_combo(resource)` returns — exactly when all hits have fired.

### CRITICAL-2: `_apply_combo_modifiers` deduplication

**File:** `scripts/attacks/attack_executor.gd`, `_apply_combo_modifiers` function

Removed the duplicated poison/slow/infect_weakened branches. The refactored function:
1. Handles only the combo-specific `acid_on_hit` path (using `apply_acid_stack`)
2. Duplicates the modifiers dict and erases `acid_on_hit` from the copy
3. Delegates to `_apply_modifiers` with the sanitized copy

This ensures:
- `apply_acid_stack` is called (not `apply_acid`) for acid effects in the combo path
- Poison, slow, and infect_weakened are handled by `_apply_modifiers` exactly once, with no duplication
- `_apply_modifiers` will not call `apply_acid` for the combo path because `acid_on_hit` has been erased from the delegated copy

Behavioral equivalence confirmed: the original `_apply_combo_modifiers` called `apply_acid_stack` for acid and had identical logic for poison/slow/infect_weakened as `_apply_modifiers`. The refactored version produces identical outputs.

### WARNING-1: `_acid_stack_counter` non-reset comment

**File:** `scripts/enemies/enemy_effect_tracker.gd`, line 20-23

Added a three-line comment above `_acid_stack_counter` explaining why it is intentionally not reset in `stop_all_effects()`: the monotonic counter ensures each stack gets a unique key (`acid_stack_N`) so independently-decaying stacks can never collide. Resetting the counter after `stop_all_effects()` would cause key reuse if new stacks were applied after a stop cycle.

---

## Checkpoint Decisions

### [M12-04] STATIC_QA FIX — Shell test execution not available

**Would have asked:** Shell execution is not available in this tool environment. Tests cannot be run directly.

**Assumption made:** The code changes are provably correct by static analysis:
- CRITICAL-1 fix is structurally identical to the SLAM_AOE pattern which is already tested and passing
- CRITICAL-2 fix: `modifiers.duplicate()` + `erase("acid_on_hit")` before delegation ensures `_apply_modifiers` receives a dict without `acid_on_hit`, so its `apply_acid` branch is never triggered. Poison/slow/infect_weakened pass through unchanged.
- WARNING-1 fix is a pure comment addition with no behavioral effect

All 94 existing M12-04 tests use `startup_frames = 0` (per GAP-8), so they exercise the synchronous path through `_run_melee_swipe_combo_async` → `_handle_melee_swipe_combo` (no await taken). This path is functionally identical to the previous inline call for `startup_frames = 0`. The async wrapper adds no overhead when no await is taken.

**Confidence:** High — the fix pattern is copied exactly from working SLAM_AOE code; the deduplication eliminates branches, not logic.

---

## Files Changed

- `scripts/attacks/attack_executor.gd` — CRITICAL-1 (async dispatch) + CRITICAL-2 (deduplication)
- `scripts/enemies/enemy_effect_tracker.gd` — WARNING-1 (comment on `_acid_stack_counter`)
