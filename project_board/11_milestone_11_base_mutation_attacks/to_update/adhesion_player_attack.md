# TICKET: adhesion_player_attack

Title: Adhesion mutation attack — sticky projectile that briefly immobilises enemies

## Description

When the player has the adhesion mutation active and presses the attack input, Blobert fires a sticky projectile that briefly immobilises the first enemy it hits (root effect, ~1.0s). The attack interacts with the infection loop: a rooted enemy is easier to infect.

## Acceptance Criteria

- Firing projectile is visible and travels along the X axis from the player
- Projectile hits the first enemy in its path and despawns
- On hit, enemy movement is set to 0 for 1.0 seconds
- Enemy in NORMAL state can be infected during the root window (existing infection flow applies)
- Projectile despawns on wall collision or after max range (configurable, default 10 units)
- Attack cooldown: 2.5s
- `run_tests.sh` exits 0

## Dependencies

- `attack_input_and_cooldown_framework`
