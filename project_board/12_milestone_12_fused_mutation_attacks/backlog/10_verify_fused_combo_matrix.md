# TICKET: 10_verify_fused_combo_matrix

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Verification

## Title

Verify fused attack combo matrix coverage and unordered lookup

## Description

After M12 core tickets are implemented, verify that all 6 unordered fusion combinations are accessible via AttackDatabase:
- Claw + Acid (and Acid + Claw)
- Claw + Carapace (and Carapace + Claw)
- Claw + Adhesion (and Adhesion + Claw)
- Acid + Carapace (and Carapace + Acid)
- Acid + Adhesion (and Adhesion + Acid)
- Carapace + Adhesion (and Adhesion + Carapace)

Verify that `get_fused_attack(a, b)` matches `get_fused_attack(b, a)` for all combos. Test combo matrix transitions in gameplay (activate 2 mutations, execute fused attack).

## Acceptance Criteria

- [x] Manual test: Activate 2 mutations, attempt fused attack execution
- [x] Manual test: Switch mutation order (activate B then A), fused attack still works
- [x] Manual test: All 6 unique combos execute fused attack when both mutations active
- [x] Manual test: Fallback to base attack when 1 mutation or new combo is active
- [x] Manual test: Fused attack cooldown blocks both mutations appropriately

## Dependencies

- M11_core_3_attack_database_integration (base database)
- M12_core_1_fused_attack_database_integration (fused lookup)
- M12_core_2_fused_attack_resources (fused attack data)

## Notes

- This is a manual verification ticket to validate combo matrix completeness
- Run after M12 core tickets are in_progress or completed
- Document any unexpected fallback cases for future debugging

