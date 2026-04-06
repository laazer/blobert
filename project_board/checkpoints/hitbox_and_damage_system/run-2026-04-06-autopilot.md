# hitbox_and_damage_system — run-2026-04-06-autopilot

## Planning / orchestration

- Single-ticket autopilot; dequeued from `8_milestone_8_enemy_attacks/backlog/` → `in_progress/`.
- **Assumption made:** `EnemyAttackHitbox` extends `Area3D` with `set_hitbox_active`; tests preload script path because `class_name` is not visible to sibling test parse order.
- **Confidence:** High

## Implementation summary

- `enemy_attack_hitbox.gd`: one hit per activation, knockback from planar delta, `collision_mask = 1`.
- `PlayerController3D.take_damage`: HP clamp + velocity XY impulse.

## Validation

- `timeout 300 ci/scripts/run_tests.sh` exit 0 (2026-04-06).
