# TICKET: claw_player_attack

Title: Claw mutation attack — fast melee swipe with short cooldown

## Description

When the player has the claw mutation active and presses the attack input, Blobert performs a fast melee swipe in the facing direction. Short cooldown encourages aggressive play. A WEAKENED enemy hit by a claw swipe transitions directly to INFECTED (skipping the standard infect interaction window).

## Acceptance Criteria

- Swipe hitbox activates immediately in front of the player (short range, ~1.5 units)
- Swipe animation plays (or a visual indication — VFX placeholder acceptable)
- On hit, enemy takes damage
- If the enemy is WEAKENED, it transitions to INFECTED state (claw can trigger infection directly)
- Attack cooldown: 0.8s (shortest of all mutations)
- Hitbox is only active for one frame (no multi-hit from a single press)
- `run_tests.sh` exits 0

## Dependencies

- `attack_input_and_cooldown_framework`
