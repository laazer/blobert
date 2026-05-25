# M11-06 Implementation Run — Gameplay Systems Agent

**Date:** 2026-05-25
**Stage:** IMPLEMENTATION_GAMEPLAY → INTEGRATION
**Agent:** Gameplay Systems Agent

## Summary

Implemented AttackDatabase and wired PlayerController3D attack pipeline per spec ADB-1 through ADB-15.

### Deliverables

1. **`scripts/attacks/attack_database.gd`** — `AttackDatabaseNode extends Node` with:
   - `_base_attacks` / `_fused_attacks` dictionaries
   - `register_base_attack()`, `get_base_attack()` (null + warning on miss)
   - `register_fused_attack()`, `get_fused_attack()` (order-independent canonical key)
   - `has_base_attack()`, `get_base_attack_count()`, `get_fused_attack_count()`, `clear()`
   - Empty string, null resource, self-fusion guards per ADB-3/ADB-5

2. **`scripts/player/player_controller_3d.gd`** modifications:
   - `_attack_executor: AttackExecutor` child node in `_ready()`
   - `_mutation_cooldowns: Dictionary` with per-frame decrement in `_tick_controller_timers()`
   - `_input_policy: PlayerInputActionPolicy` instantiated in `_ready()`
   - `get_facing_sign() -> float` (velocity.x sign, default 1.0)
   - `_try_attack()` — full pipeline: policy gate → slot check → DB lookup (fused priority, base fallback) → cooldown gate → executor dispatch → cooldown set
   - `"attack_just_pressed"` key in `_read_player_input()` return dict
   - Attack trigger in `_post_slide_housekeeping()` Step 8

3. **`project.godot`** changes:
   - `AttackDatabase` autoload registered
   - `attack` InputMap action (J key, physical keycode 74)

### Test Results

- **156 of 157** attack-related tests pass (35 + 47 + 41 + 33 = 156)
- **1 failure:** `EC-20_slot_b_fires_base_attack` — see checkpoint below
- All other test suites unaffected (0 regressions)
- `task hooks:gd-review` — PASS
- `task hooks:gd-organization` — PASS

### [M11-06] IMPLEMENTATION_GAMEPLAY — EC-20 test setup bug
**Would have asked:** The test `test_ec20_slot_b_only_base_attack` calls `msm.fill_next_available("test_slot_b_acid")` (fills slot A at index 0), then `msm.clear_slot(0)` (clears slot A). Both slots are now empty. The test expects an attack to fire from slot B, but no mutation was ever placed in slot B. Should the test be fixed to call `fill_next_available` twice before clearing slot 0?
**Assumption made:** The test has a setup bug — `fill_next_available()` fills index 0 first per MutationSlotManager contract. After clearing index 0, both slots are empty and `_try_attack()` correctly returns without firing. The implementation is correct per spec ADB-7 step 3 ("If only one slot is filled: use that slot's mutation_id"). The test setup does not achieve the intended "slot B only" state. Routing to next agent for test fix.
**Confidence:** High

### [M11-06] IMPLEMENTATION_GAMEPLAY — class_name vs autoload conflict
**Would have asked:** Godot 4.6 prevents `class_name AttackDatabase` on scripts registered as autoload "AttackDatabase" (`Parse Error: Class "AttackDatabase" hides an autoload singleton`). The org check requires class_name. What class_name should be used?
**Assumption made:** Used `class_name AttackDatabaseNode` to satisfy the org check while avoiding autoload name collision. The autoload singleton remains accessible as `AttackDatabase` globally. Tests use `load(path).new()` pattern and are unaffected.
**Confidence:** High
