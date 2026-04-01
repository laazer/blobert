# TICKET: adhesion_enemy_attack

Title: Adhesion enemy attack — slow lunge that briefly roots the player

## Description

The adhesion family enemy attacks by lunging toward the player and applying a brief root effect (player movement speed reduced to 0 for ~0.5s) on hit. The lunge closes a short gap and the hit registers via the shared hitbox system.

## Acceptance Criteria

- Adhesion enemy enters a lunge state when player is within attack range
- Lunge moves the enemy forward along the X axis toward the player
- On successful hit, player movement speed is set to 0 for 0.5 seconds (root effect)
- Root effect wears off cleanly — no permanent slow
- Attack has a cooldown (configurable, default 2.0s) before re-triggering
- Attack telegraph plays before lunge (uses `attack_telegraph_system`)
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `attack_telegraph_system`
- M15 (Enemy Navigation) — lunge is most meaningful once enemies can pursue
