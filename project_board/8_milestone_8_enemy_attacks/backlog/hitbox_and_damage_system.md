# TICKET: hitbox_and_damage_system

Title: Enemy hitbox system — player takes damage on contact

## Description

Create the foundational damage system that enemy attacks use to deal damage to the player. Each enemy scene needs an attack hitbox (Area3D) that activates during the attack window and deals damage to the player on overlap. This is the shared infrastructure all 4 family attack tickets depend on.

## Acceptance Criteria

- `scripts/enemies/enemy_attack_hitbox.gd` exists and attaches to an Area3D node
- Hitbox has an enabled/disabled toggle (off by default; activated during attack animation window)
- On overlap with player, calls a damage method on PlayerController3D
- Player HP decreases by the hitbox's configured damage amount
- Hitbox auto-disables after one hit per attack swing (no multi-hit from single activation)
- Player takes knockback vector from the hit direction
- `run_tests.sh` exits 0

## Dependencies

- M7 (Enemy Animation Wiring) — hitbox activation is tied to animation frames
- PlayerController3D must expose a `take_damage(amount: float, knockback: Vector3)` method
