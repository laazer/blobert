# TICKET: carapace_player_attack

Title: Carapace mutation attack — ground slam with area knockback

## Description

When the player has the carapace mutation active and presses the attack input, Blobert performs a heavy ground slam. All enemies within a short radius are knocked back and take damage. Slowest attack of all base mutations but hits multiple enemies.

## Acceptance Criteria

- Slam hitbox activates in a radius around the player (configurable, default 3.0 units)
- All enemies within radius take damage and receive knockback away from the player
- Slam has a brief wind-up before the hitbox activates (0.2s)
- Attack cooldown: 3.5s
- If player is airborne, slam triggers on landing (gravity assists — more satisfying)
- `run_tests.sh` exits 0

## Dependencies

- `attack_input_and_cooldown_framework`
