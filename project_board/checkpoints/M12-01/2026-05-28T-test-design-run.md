# M12-01 Test Design Run — 2026-05-28

**Agent:** Test Designer Agent
**Stage:** TEST_DESIGN
**Ticket:** project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md
**Spec:** project_board/specs/fused_attack_database_integration_spec.md

## Summary

Wrote `tests/scripts/attacks/test_fused_combo_matrix.gd` containing 18 test methods
(36 total assertions) covering all 6 unordered canonical combos in three categories:

- 6 forward-lookup tests (FADI-6-1a through FADI-6-6a)
- 6 reverse-lookup tests (FADI-6-1b through FADI-6-6b) — validates FADI-DD-3 order-independence
- 6 player-dispatch tests (FADI-6-1c through FADI-6-6c) — validates FADI-4a, FADI-3a, FADI-3b

Test runner outcome: `=== ALL TESTS PASSED ===` (0 failures across full suite).

## Test File

`tests/scripts/attacks/test_fused_combo_matrix.gd`

## Design Decisions

### [M12-01] TEST_DESIGN — Composite cooldown key computation in dispatch tests

**Would have asked:** Should the dispatch test verify the composite key using
`"fcm_" + sorted_key` (i.e., prepend the namespace to the pre-sorted canonical key)
or compute the sort over the namespaced IDs?

**Assumption made:** The correct composite key is the result of sorting the actual
slot IDs (including namespace prefix) and joining with `_`. The test computes:
`var ns_pair: Array = [ns_a, ns_b]; ns_pair.sort(); ns_sorted_key = "%s_%s" % [ns_pair[0], ns_pair[1]]`
This mirrors exactly how `_try_attack()` computes the key at lines 469-471 of
`player_controller_3d.gd`. The simpler form `"fcm_" + sorted_key` would produce
`"fcm_acid_claw"` rather than `"fcm_acid_fcm_claw"` — a mismatch. The correct
approach matches the runtime key derivation.

**Confidence:** High (initial naive approach produced 6 failures; fix produced 0 failures)

### [M12-01] TEST_DESIGN — Test runner auto-discovery

**Would have asked:** Does the test file need manual registration in run_tests.gd?

**Assumption made:** `run_tests.gd` uses `_collect_test_files()` to auto-discover all
files under `tests/` beginning with `test_` and ending with `.gd`. No manual
registration needed. Confirmed by reading run_tests.gd lines 27-42.

**Confidence:** High
