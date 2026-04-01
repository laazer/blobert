# TICKET: acid_enemy_attack

Title: Acid enemy attack — ranged acid projectile with damage over time

## Description

The acid family enemy attacks by spitting an acid projectile at the player from range. On hit, the projectile applies a damage-over-time (DoT) debuff for 3 seconds. The projectile travels along the X axis at a fixed speed.

## Acceptance Criteria

- Acid enemy fires a projectile when player is within attack range (configurable, default 8 units)
- Projectile travels toward the player along the X axis
- Projectile despawns on wall collision or after 3 seconds
- On hit, player takes initial impact damage and then DoT damage every 0.5s for 3s
- DoT can stack if hit multiple times (each hit adds a new DoT instance)
- Attack has a cooldown (configurable, default 3.0s)
- Attack telegraph plays before projectile fires
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `attack_telegraph_system`
