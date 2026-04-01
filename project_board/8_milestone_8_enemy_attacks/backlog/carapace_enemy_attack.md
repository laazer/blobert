# TICKET: carapace_enemy_attack

Title: Carapace enemy attack — slow charge with knockback

## Description

The carapace family enemy attacks by winding up a heavy charge, then launching itself along the X axis. On hit the player is knocked back significantly. High damage, long telegraph, high knockback — readable and avoidable but dangerous if caught.

## Acceptance Criteria

- Carapace enemy enters charge wind-up when player is within range (configurable, default 6 units)
- Wind-up lasts at least 0.6 seconds (longer than other families)
- Charge travels along the X axis until it hits the player, a wall, or exceeds max range
- On hit, player takes heavy damage and a large knockback force
- Enemy decelerates after charge completes (no infinite sliding)
- Attack cooldown is long (configurable, default 4.0s)
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `attack_telegraph_system`
