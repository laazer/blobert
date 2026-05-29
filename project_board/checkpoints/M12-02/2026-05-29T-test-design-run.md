# Checkpoint Log: M12-02 Test Design Run
**Ticket:** `project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md`
**Run ID:** 2026-05-29T-test-design-run
**Stage:** TEST_DESIGN
**Agent:** Test Designer Agent
**Date:** 2026-05-29

---

## Summary

Wrote 36-function behavioral test suite for the 6 canonical fused AttackResource registrations.
Test file: `tests/scripts/attacks/test_fused_attack_resources.gd`

Tests confirmed RED on clean checkout (49 failures, 18 pass). All pre-existing tests remain green.

---

## Decisions Made

### [M12-02] TEST_DESIGN — Add-child vs manual _register_defaults() call
**Would have asked:** Should we use `add_child(db)` to trigger `_ready()` or call `_register_defaults()` manually?
**Assumption made:** Used `add_child(db)` to trigger `_ready() -> _register_defaults()`, matching the spec's recommended setup pattern (Section 8). This is the same integration path the production autoload uses.
**Confidence:** High

### [M12-02] TEST_DESIGN — Float comparison for 0.8 and 0.6
**Would have asked:** Spec says use `is_equal_approx` or `absf` for 0.8 and 0.6 (FAR-EC-8). Which to use?
**Assumption made:** Used `_assert_approx()` from test_utils.gd (which uses `abs(a - b) < 1e-4`), matching the project's existing helper. Values 1.2 (acid_adhesion acid_dps) is also not exactly representable and gets the same treatment.
**Confidence:** High

### [M12-02] TEST_DESIGN — FAR-7 combined into one test function or per-combo?
**Would have asked:** Spec Section 8 groups FAR-7 as items 20-25. Should each be a separate function or one combined?
**Assumption made:** Combined all FAR-7a through FAR-7l into one test function (`test_far7_fused_attacks_differ_from_base_components`) with per-assertion labels. This keeps the suite at 36 functions rather than exploding to 50+. Each assertion is still individually labeled so failures are distinguishable.
**Confidence:** High

---

## Test Execution Result

Command: `timeout 300 godot --headless -s tests/run_tests.gd`

```
FusedAttackResourcesTests: 18 passed, 49 failed
```

49 failures are expected — all from `get_fused_attack()` returning null (fused attacks not yet
registered in `_register_defaults()`). The 18 passing tests cover:
- FAR-5b (clear() yields count 0)
- FAR-5c (base count unchanged = 4)
- FAR-6 reverse "same resource" checks when both lookups return null (null == null passes)
- FAR-3h (base attack IDs not in range 101-106)
- FAR-NF-4 (fused key names not in _base_attacks)

Pre-existing test suites: all green (0 new regressions introduced).

---

## Coverage

36 test functions covering:
- FAR-5: Registration completeness (4 tests)
- FAR-6: Bidirectional lookup, all 6 combos (12 tests)
- FAR-3: Attack ID mapping and uniqueness (8 tests)
- FAR-4: Per-combo stat values (6 tests + 2 supporting tests)
- FAR-EC-2: Modifier dict size (1 test with 6 sub-cases)
- FAR-EC-1: Falsy-zero slow==0.0 (2 tests)
- FAR-7: Meaningful distinction from base components (1 test with 12 assertions)
- FAR-NF-4 / FAR-NF-6: No cross-contamination, unique names (2 tests)
