# M11-12 Test Design Run — 2026-05-25

**Agent:** Test Designer Agent  
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/12_verify_cooldown_behavior.md`  
**Spec:** `project_board/specs/cooldown_cross_state_behavior_spec.md`  
**Stage:** TEST_DESIGN → TEST_BREAK

## Summary

Created 23 behavioral tests in `tests/scripts/attacks/test_cooldown_cross_state_behavior.gd` covering all 5 spec requirements (CDB-1 through CDB-5).

## Test Mapping

| Spec ID | Tests | Count |
|---------|-------|-------|
| CDB-1 (state-independent decrement) | `test_cdb1_decrement_in_all_states` (parameterized across 9 states) | 9 assertions |
| CDB-2 (cross-state continuity) | `test_cdb2a` through `test_cdb2g` + `test_cdb2_multi_state_chain` | 8 tests |
| CDB-3 (death resets cooldowns) | `test_cdb3a` through `test_cdb3c` + `test_cdb3_attack_fires_immediately_after_reset` | 4 tests |
| CDB-4 (per-mutation independence) | `test_cdb4a` through `test_cdb4c` + `test_cdb4_fused_key_independent_from_base_keys` | 4 tests |
| CDB-5 (rapid input rejection) | `test_cdb5a` through `test_cdb5f` + `test_cross_state_lifecycle_attack_refire` | 7 tests |

## Key Decisions

### [M11-12] TEST_DESIGN — CDB-3 tests as regression tests
**Would have asked:** Should CDB-3 tests be written to pass or fail against the current code (which lacks `_mutation_cooldowns.clear()` in `reset_hp()`)?
**Assumption made:** Written as regression tests that assert the CORRECT behavior (cooldowns cleared). These will FAIL until the implementation agent adds the one-line fix. This is the standard TDD approach — failing tests drive the implementation.
**Confidence:** High

### [M11-12] TEST_DESIGN — CDB-1i DEAD state decrement
**Would have asked:** Should we test cooldown decrement in DEAD state specifically?
**Assumption made:** Included DEAD in the parameterized CDB-1 loop. The spec notes CDB-1i as "NOT APPLICABLE" but clarifies cooldowns still decrement in DEAD because the code is unconditional. Testing it confirms no crash and correct decrement.
**Confidence:** High

## Outcome

Stage advanced to TEST_BREAK. Test Breaker Agent should add adversarial/edge-case tests (negative delta, concurrent reset+tick, rapid state oscillation).
