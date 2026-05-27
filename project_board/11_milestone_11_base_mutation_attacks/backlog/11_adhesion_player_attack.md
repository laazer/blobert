# TICKET: 11_adhesion_player_attack

Title: Adhesion mutation attack — sticky projectile that briefly immobilises enemies

## Description

When the player has the adhesion mutation active and presses the attack input, Blobert fires a sticky projectile that briefly immobilises the first enemy it hits (root effect, ~1.0s). The attack interacts with the infection loop: a rooted enemy is easier to infect.

## What's Already Done

The generic PROJECTILE_SPIT pipeline and slow modifier hook are implemented:
- `AttackExecutor._handle_projectile_spit()` creates `PlayerProjectile3D` with modifiers (M11-05)
- `PlayerProjectile3D._on_body_entered()` calls `apply_slowness(multiplier, duration)` when `slow` modifier is set (M11-05)
- Projectile collision, consumed flag, velocity, and despawn on lifetime verified (M11-13)

## Remaining Work

- [ ] Register an adhesion-specific `AttackResource` with tuned values (cooldown 2.5s, projectile range 10 units)
- [ ] Implement full root effect: movement set to 0 for 1.0s (current `apply_slowness` is a multiplier, not a hard root)
- [ ] Root interaction with infection loop: rooted enemy is easier to infect
- [ ] Projectile despawns on wall collision (current despawn is lifetime-only)
- [ ] Visually distinct adhesion projectile

## Acceptance Criteria

- Firing projectile is visible and travels along the X axis from the player
- Projectile hits the first enemy in its path and despawns
- On hit, enemy movement is set to 0 for 1.0 seconds
- Enemy in NORMAL state can be infected during the root window (existing infection flow applies)
- Projectile despawns on wall collision or after max range (configurable, default 10 units)
- Attack cooldown: 2.5s
- `run_tests.sh` exits 0

## Dependencies

- ~~`attack_input_and_cooldown_framework`~~ (done — M11-03/04/05/06)
- M11-14 (Enemy Health & Damage Reception) — enemies must have `take_damage()` and `apply_slowness()`
