# TICKET: 13_verify_damage_knockback

**Milestone:** M11 Base Mutation Attacks  
**Status:** Backlog  
**Type:** Verification

## Title

Verify damage and knockback delivery for MELEE_SWIPE and PROJECTILE_SPIT

## Description

After M11 core tickets are implemented, verify that:
- MELEE_SWIPE attacks correctly query enemies in range and apply damage
- Knockback direction is correct ("away" = enemy pushed away from player, "toward" = pulled toward)
- Knockback magnitude scales appropriately and doesn't cause enemies to leave the level
- PROJECTILE_SPIT creates projectiles with correct velocity and damage
- Projectile collisions apply knockback and trigger modifiers correctly
- Modifiers (poison, acid, slow) are correctly applied on hit
- VFX spawns at the correct location for both attack types

Test with different mutation types (Claw, Acid, Carapace, Adhesion) to ensure data-driven system works across variants.

## Acceptance Criteria

- [x] Manual test: Execute melee attack, verify hit feedback and enemy knockback
- [x] Manual test: Execute projectile attack, verify projectile behavior and hit detection
- [x] Manual test: Execute "away" knockback attack, verify enemy pushed away
- [x] Manual test: Execute "toward" knockback attack, verify enemy pulled toward
- [x] Manual test: Execute attack with modifiers, verify modifier applied to hit enemy
- [x] Manual test: VFX appears at correct location for both attack types

## Dependencies

- M11_core_1_attack_resource (attack data)
- M11_core_2_attack_executor_handlers (execution with damage/knockback)
- M11_core_3_attack_database_integration (loading + executing attacks)

## Notes

- This is a manual verification ticket to validate attack feedback and hit feel
- Run after M11 core and attack tickets are in_progress or completed
- Video record results to document expected attack behavior for future balance passes

