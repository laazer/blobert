# TICKET: M12_attack_2_verify_fused_attack_balance

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Verification

## Title

Verify fused attack balance and feel compared to base attacks

## Description

After M12 core tickets and fused attack resources are implemented, verify that fused attacks feel meaningfully different from base attacks:
- Fused attacks have higher damage (cost/benefit tradeoff for requiring 2 mutations)
- Fused attack cooldown is longer (prevents spam with 2 mutations)
- Fused attacks apply combined modifiers from both base mutations (or unique custom effects)
- VFX visually indicates fusion (color, scale, particle type)
- Knockback magnitude and direction feel appropriate for the fused combo

Test gameplay loop: activate 2 mutations, use base attacks, then execute fused combo, verify it feels powerful and deliberate.

## Acceptance Criteria

- [x] Manual test: Compare fused attack damage vs base attack damage
- [x] Manual test: Compare fused attack cooldown vs base attack cooldown
- [x] Manual test: Verify fused attack applies expected modifier effects
- [x] Manual test: Verify VFX visually distinguishes fused from base attacks
- [x] Manual test: Play with fused attacks in combat scenario, document feel

## Dependencies

- M12_core_1_fused_attack_database_integration (fused lookup + execution)
- M12_core_2_fused_attack_resources (fused attack data + VFX)

## Notes

- This is a manual verification ticket to validate game feel and balance
- Run after M12 core tickets are in_progress or completed
- Document balance decisions (damage multiplier, cooldown scaling) for future balance passes
- Recommend video recording gameplay to evaluate visual feedback

