# TICKET: acid_player_attack

Title: Acid mutation attack — ranged acid spit with damage over time

## Description

When the player has the acid mutation active and presses the attack input, Blobert spits an acid projectile. On enemy hit, the enemy takes a damage-over-time debuff for 3s. If the enemy is already WEAKENED, the DoT duration is doubled.

## Acceptance Criteria

- Acid projectile is visually distinct from adhesion projectile
- Projectile travels along the X axis and hits the first enemy
- On hit, enemy takes DoT damage every 0.5s for 3.0s
- If enemy is WEAKENED, DoT duration increases to 6.0s
- DoT does not stack from the same mutation (only one acid DoT per enemy at a time; refreshes on re-hit)
- Attack cooldown: 2.0s
- `run_tests.sh` exits 0

## Dependencies

- `attack_input_and_cooldown_framework`
