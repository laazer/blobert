# M11-06 Test Design Run

**Ticket:** M11-06 (AttackDatabase Integration)
**Agent:** Test Designer Agent
**Stage:** TEST_DESIGN → TEST_BREAK
**Date:** 2026-05-25

## Summary

Created 2 test files with 48 behavioral tests covering all 15 spec requirements (ADB-1 through ADB-15) plus 4 edge-case scenarios.

### Test Files

| File | Tests | Spec Coverage |
|------|-------|---------------|
| `tests/scripts/attacks/test_attack_database.gd` | 26 | ADB-1 through ADB-6 (class identity, internal storage, base registration, base lookup, fused registration, fused lookup) |
| `tests/scripts/attacks/test_attack_database_controller_integration.gd` | 22 | ADB-7 through ADB-14 (state gating, facing sign, executor wiring, cooldown tracking, attack pipeline, input reading) |

### RED/GREEN Status

- **GREEN (2 tests):** ADB-14 state gating (policy matrix already configured with ACTION_ATTACK)
- **RED (46 tests):** All others — AttackDatabase script does not exist; controller lacks _try_attack, get_facing_sign, _mutation_cooldowns, _attack_executor, _input_policy

### Checkpoints

### [M11-06] TEST_DESIGN — Controller instantiation strategy
**Would have asked:** Should _try_attack pipeline tests instantiate the full PlayerController3D (complex _ready) or use mock objects?
**Assumption made:** Tests instantiate the real controller via scene tree. If _ready() fails due to missing scene dependencies, the test fails RED. Implementation agent must ensure the controller works in headless test mode.
**Confidence:** High

### [M11-06] TEST_DESIGN — Autoload access in tests
**Would have asked:** How should tests access the AttackDatabase autoload?
**Assumption made:** Tests access the autoload via `Engine.get_main_loop().root.get_node_or_null("AttackDatabase")`. Before implementation, this returns null and tests fail RED. After implementation registers the autoload in project.godot, it becomes available in the headless test runner.
**Confidence:** High

### [M11-06] TEST_DESIGN — Mutation slot override for testing
**Would have asked:** How to control mutation state in _try_attack tests?
**Assumption made:** Tests override `_mutation_slot` on the controller via `set()` after _ready() completes, using a fresh MutationSlotManager with controlled slot states. The current controller declares `_mutation_slot: Object = null`.
**Confidence:** High

### [M11-06] TEST_DESIGN — Cooldown decrement test via _tick_controller_timers
**Would have asked:** Can we call _tick_controller_timers(delta, false) directly to test cooldown decrement?
**Assumption made:** Yes. The method signature is `_tick_controller_timers(delta: float, jump_just_pressed: bool)`. Implementation will add cooldown decrement logic to this method. Tests call it directly with `false` for jump_just_pressed.
**Confidence:** High
