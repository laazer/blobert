# M12-04 Static QA Run — 2026-05-29

**Agent:** Static QA Agent
**Ticket:** M12-04 (Acid+Claw Fusion Attack — Venomous Shred)
**Stage:** STATIC_QA
**Outcome:** BLOCKED — 2 CRITICAL issues found; implementation must fix before proceeding

---

## Files Reviewed

Implementation:
- `scripts/attacks/attack_resource.gd` — new `combo_hits` field
- `scripts/attacks/attack_executor.gd` — MELEE_SWIPE_COMBO case, `_handle_melee_swipe_combo()`, `_apply_combo_modifiers()`
- `scripts/enemies/enemy_effect_tracker.gd` — `add_acid_stack()`, `get_acid_stack_count()`
- `scripts/enemies/enemy_base.gd` — `apply_acid_stack()`, `get_acid_stack_count()` delegates
- `scripts/attacks/attack_database.gd` — acid_claw normative stat block

Tests:
- `tests/scripts/attacks/test_acid_claw_combo_attack.gd`
- `tests/scripts/attacks/test_acid_claw_combo_adversarial.gd`
- `tests/scripts/attacks/test_acid_claw_combo_seams_adversarial.gd`
- `tests/scripts/attacks/test_acid_claw_database_registration.gd`
- `tests/scripts/enemies/test_enemy_acid_stacking.gd`

---

## CRITICAL Issues (must fix before merge)

### CRITICAL-1 — MELEE_SWIPE_COMBO dispatches directly to handler, not async wrapper

**File:** `scripts/attacks/attack_executor.gd`, line 40

`execute_attack` dispatches `MELEE_SWIPE_COMBO` directly:
```gdscript
"MELEE_SWIPE_COMBO":
    _handle_melee_swipe_combo(resource)
```

`_handle_melee_swipe_combo` contains an `await` when `startup_frames > 0`. When called directly, GDScript suspends the function at the await and returns a coroutine to the caller. `execute_attack` then falls through to `_is_active = false` at line 43 — while the combo is still executing its startup timer. This clears the active guard before any hits land.

The orphaned `_run_melee_swipe_combo_async` wrapper at lines 51–53 exists but is never called.

**Fix:** Mirror the SLAM_AOE pattern exactly:
```gdscript
"MELEE_SWIPE_COMBO":
    _run_melee_swipe_combo_async(resource)
    return
```

**Why tests don't catch it:** All registered combo resources use `startup_frames = 0`. The `await` branch inside `_handle_melee_swipe_combo` is only taken when `startup_frames > 0`. GAP-8 explicitly notes this limitation. The bug is latent until a non-zero startup combo is registered.

### CRITICAL-2 — `_apply_combo_modifiers` duplicates `_apply_modifiers` (DRY violation)

**File:** `scripts/attacks/attack_executor.gd`, lines 87–120 and 195–224

The two functions share identical logic for poison, slow, and infect_weakened. The only difference is `apply_acid` vs `apply_acid_stack` in the acid block. All future changes to modifier dispatch must be applied in two places. CLAUDE.md requires flagging DRY violations.

**Fix options (in order of preference):**
1. Have `_apply_combo_modifiers` handle only the acid override, then delegate to `_apply_modifiers` for the remaining modifiers with `acid_on_hit` excluded from the delegation call.
2. Parameterize the acid method name in `_apply_modifiers`.

Minimum viable change to resolve the duplication:
```gdscript
func _apply_combo_modifiers(
    target: Node3D,
    modifiers: Dictionary,
    pre_damage_state: int = -1
) -> void:
    if modifiers.get("acid_on_hit", false):
        if target.has_method("apply_acid_stack"):
            var acid_dur: float = modifiers.get("acid_duration", 2.0)
            var acid_dps_val: float = modifiers.get("acid_dps", DEFAULT_ACID_DPS)
            if target.has_method("get_base_state") and target.get_base_state() == 1:
                acid_dur *= 2.0
            target.apply_acid_stack(acid_dur, acid_dps_val)
    var mods_sans_acid := modifiers.duplicate()
    mods_sans_acid.erase("acid_on_hit")
    _apply_modifiers(target, mods_sans_acid, pre_damage_state)
```

---

## WARNING Issues

### WARNING-1 — `_acid_stack_counter` non-reset undocumented

**File:** `scripts/enemies/enemy_effect_tracker.gd`, `stop_all_effects()` (line 66)

`_acid_stack_counter` is intentionally not reset in `stop_all_effects()` (per AC-3k monotonicity contract). This is a non-obvious design decision with behavioral consequences (post-stop stacks get keys `acid_stack_N+` not `acid_stack_0`). A comment explaining the intent is required.

### WARNING-2 — Silent miss on `apply_acid_stack` guard

**File:** `scripts/attacks/attack_executor.gd`, `_apply_combo_modifiers`, line 100

Enemies missing `apply_acid_stack` silently receive no acid DoT from combo attacks with no warning. Since `apply_acid` exists on `EnemyBase` (old API), a partially-upgraded enemy would silently lose the effect. Add `push_warning` on the miss path.

### WARNING-3 — `ACID_CLAW_KNOCKBACK = 80.0` unexplained tuning literal

**File:** `scripts/attacks/attack_database.gd`, line 37

`80.0` is 16x higher than the next highest knockback constant. Per CLAUDE.md reviewer policy, unexplained tuning literals are findings. A comment explaining the design intent (units, intentional strength, etc.) is required on the constant.

### WARNING-4 — `_handle_melee_swipe_combo` annotated `-> void` but is implicitly a coroutine

**File:** `scripts/attacks/attack_executor.gd`, line 56

The function contains `await` and is therefore a coroutine, but the return annotation is `-> void`. This resolves naturally once CRITICAL-1 is fixed by routing through the async wrapper. Flagged for completeness.

---

## INFO Issues

### INFO-1 — Tests use `r.set("combo_hits", ...)` instead of direct property access

Now that `combo_hits` is a declared `@export var`, direct property access is safe and more idiomatic. The `set()`/`get()` pattern was correct before the field existed; it is now a cleanup opportunity.

### INFO-2 — `_run_melee_swipe_combo_async` is dead code

Dead until CRITICAL-1 is fixed. Resolves automatically once the dispatch is corrected.

### INFO-3 — Tests access `tracker._active_dots[key]` directly

Minor test-design smell; `has_active_dot()` exists as a public accessor for the same information. Not a correctness issue.

### INFO-4 — Stale "Tests will be RED until implementation" comments

All five test files contain pre-implementation notes at the top. These are now stale and should be removed or replaced with "implementation complete" notes.

### INFO-5 — `test_acec2_enemy_killed_by_hit1_no_further_stacks` misleading label

The test sets `is_dead_flag = true` before the attack fires, testing a pre-dead scenario, not a mid-combo kill. The "killed by hit 1" scenario (where hit 1 causes death and hits 2–3 skip) is not covered.

---

## What Passed

- `attack_resource.gd`: `combo_hits` field correctly declared as `@export var combo_hits: int = 1`. Default, type, and inspector exposure are all correct.
- `enemy_effect_tracker.gd`: `add_acid_stack()` and `get_acid_stack_count()` implementation is correct. Monotonic counter, key prefix scheme, delegation to `add_dot`, and zero-duration guard are all implemented correctly.
- `enemy_base.gd`: `apply_acid_stack()` and `get_acid_stack_count()` delegates are correct. `_is_dead` guard on `apply_acid_stack`. `get_acid_stack_count` null-guards `_effect_tracker`. Both follow the existing delegation pattern.
- `attack_database.gd`: acid_claw normative stat block is correctly populated with all M12-04 values. Named constants used throughout. No magic strings. All 6 fused registrations intact.
- Test suite: Coverage is comprehensive for `startup_frames = 0` scenarios. 5 files × diverse behavioral, adversarial, and seam test cases. Test file names are behavior-descriptive. Traceability is in module docstrings, not file names.

---

## Required Action

The implementation agent must fix CRITICAL-1 and CRITICAL-2 in `scripts/attacks/attack_executor.gd`, then return to static QA.

Log: `project_board/checkpoints/M12-04/2026-05-29T-static-qa-run.md`
