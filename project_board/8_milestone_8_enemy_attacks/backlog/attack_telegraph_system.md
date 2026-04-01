# TICKET: attack_telegraph_system

Title: Enemy attack telegraphing — wind-up indicator before hitbox activates

## Description

Each enemy attack must be readable before it deals damage. Implement a telegraphing phase: a brief wind-up animation or visual indicator plays before the hitbox activates, giving the player time to react. The telegraph duration is configurable per family.

## Acceptance Criteria

- Wind-up phase lasts at minimum 0.3 seconds before hitbox activates
- A visual change occurs during wind-up (animation state change, color flash, or indicator node)
- Hitbox does NOT activate during wind-up — only after wind-up completes
- Telegraph duration is an exported variable, not hardcoded
- Works for all 4 enemy families
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `animation_controller_script` (M7)
