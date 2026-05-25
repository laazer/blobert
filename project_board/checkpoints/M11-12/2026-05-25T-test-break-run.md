# M11-12 Test Breaker Run — 2026-05-25

**Agent:** Test Breaker Agent  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/12_verify_cooldown_behavior.md`  
**Stage:** TEST_BREAK → IMPLEMENTATION_GAMEPLAY

## Summary

Created adversarial test suite `tests/scripts/attacks/test_cooldown_cross_state_adversarial.gd` with 29 test functions targeting edge cases, stress scenarios, and spec gaps in the cooldown cross-state behavior system.

## Gaps Discovered

### GAP-1: Negative delta increases cooldown (ADV-1)
- `_tick_controller_timers` uses `maxf(0.0, val - delta)`. If delta is negative, `val - (-x) = val + x`, causing cooldown to INCREASE.
- **Severity:** Low (engine should never pass negative delta, but no defensive guard exists)
- **Recommendation:** Implementation agent should add `delta = maxf(0.0, delta)` guard or document assumption.

### GAP-2: Zero-cooldown resource allows infinite attack spam (ADV-11)
- If `AttackResource.cooldown == 0.0`, after execution the cooldown is set to 0.0. The check `> 0.0` immediately passes, allowing another attack on the same frame (only blocked by executor's `_is_active` flag which resets synchronously for non-startup-frames attacks).
- **Severity:** Medium (gameplay balance concern; may be intentional for some mutations)
- **Recommendation:** Document as design decision or add minimum cooldown floor.

### GAP-3: CDB-3 regression confirmed (ADV-15, ADV-21)
- `reset_hp()` still does NOT call `_mutation_cooldowns.clear()`. Tests ADV-15 and ADV-21 will FAIL until this one-line fix is applied.
- **Severity:** High (spec-mandated behavior not implemented yet)

## Checkpoint Entries

### [M11-12] TEST_BREAK — Negative delta behavior
**Would have asked:** Should _tick_controller_timers guard against negative delta?
**Assumption made:** Documented as spec gap; test marks expected behavior (cooldown should not increase). Implementation agent decides on guard.
**Confidence:** High

### [M11-12] TEST_BREAK — Zero cooldown resource behavior
**Would have asked:** Is cooldown=0.0 on AttackResource valid/intentional?
**Assumption made:** Test documents current behavior; implementation agent should validate design intent.
**Confidence:** Medium

## Artifact

- Test file: `tests/scripts/attacks/test_cooldown_cross_state_adversarial.gd` (29 tests)
- Coverage dimensions: Negative/zero delta, large delta, empty dict, boundary floats, stress (50 keys), state oscillation, fused key sorting, null guards, reset stability, determinism, fallback logic
