# TICKET: claw_enemy_attack

Title: Claw enemy attack — fast multi-hit melee swipe

## Description

The claw family enemy attacks with a fast 2-hit swipe combo when the player is at close range. Short cooldown makes the claw enemy aggressive and punishing if the player stands still.

## Acceptance Criteria

- Claw enemy triggers attack when player is within melee range (configurable, default 2 units)
- Attack is a 2-hit combo: first swipe fires, brief pause, second swipe fires
- Each hit uses the shared hitbox system
- Per-hit damage is lower than other families (compensated by 2 hits)
- Attack cooldown is short (configurable, default 1.2s)
- Each swipe has a minimal telegraph (short wind-up animation frame)
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `attack_telegraph_system`
- M15 (Enemy Navigation) recommended — claw enemy must close distance to be threatening
