# M11-10 Test Design Run

**Agent:** Test Designer Agent
**Date:** 2026-05-26
**Ticket:** project_board/11_milestone_11_base_mutation_attacks/in_progress/10_carapace_player_attack.md
**Spec:** project_board/specs/carapace_player_attack_spec.md

## Summary

Wrote 42 behavioral tests in `tests/scripts/attacks/test_carapace_attack.gd` (879 lines, under 900-line limit).

## Test Coverage Map

| Spec Requirement | Tests | Count |
|-----------------|-------|-------|
| CCA-1: AttackResource properties | test_cca1_carapace_resource_properties | 1 (11 assertions) |
| CCA-2: Database registration | test_cca2a..2d | 4 |
| CCA-3: Radial query + handler | test_cca3a..3j | 7 |
| CCA-4: Airborne deferral | test_cca4a, 4d, 4e | 3 |
| CCA-5: SLAM_AOE dispatch | test_cca5a..5f | 5 |
| CCA-6: VFX signal | test_cca6a, 6b, 6f, no_melee | 4 |
| CCA-7: Multi-enemy knockback | test_cca7a..7g | 6 |
| CCA-8: Pipeline integration | test_cca8b, 8c, 8_full | 3 |
| Edge cases | test_ec1..ec22 | 9 |

## Assumptions

None — all ambiguities resolved by spec discrepancy resolutions CCA-DR-1 through CCA-DR-6.

## Outcome

Stage advanced to TEST_BREAK. Handoff to Test Breaker Agent.
