# Specification: hitbox_and_damage_system

Normative IDs **HADS-1** … **HADS-8** for the enemy attack `Area3D` + player damage path.

## HADS-1 — Script and host node

- `res://scripts/enemies/enemy_attack_hitbox.gd` defines `class_name EnemyAttackHitbox` extending `Area3D`.
- The script is intended to be the `Area3D` root script (not a child helper).

## HADS-2 — Default inactive

- After `_ready()`, `monitoring` is **false** until an explicit activation API is used (`set_hitbox_active(true)`).

## HADS-3 — Activation API

- `set_hitbox_active(active: bool)`:
  - `true`: hitbox is **armed** for at most one successful hit; `monitoring` is **true**.
  - `false`: disarmed; `monitoring` is **false**.

## HADS-4 — Player damage

- When an armed, monitoring hitbox receives `body_entered` for a `PlayerController3D`, it calls `take_damage(damage_amount, knockback_vector)` on that player.
- `damage_amount` is an `@export` on the hitbox (default positive scalar; tests use fixed values).

## HADS-5 — One hit per activation

- After a successful hit on the player, the hitbox sets `_armed` false and `monitoring` false before returning.
- Further overlaps in the same “swing” do not apply damage until `set_hitbox_active(true)` runs again (new activation).

## HADS-6 — Knockback direction

- Knockback is a `Vector3` with **Z = 0** in world space.
- Direction is `(player.global_position - hitbox.global_position)` projected to the X/Y plane and normalized, multiplied by `knockback_strength` (`@export`).
- If that projected delta length is below a small epsilon, direction defaults to **+X** (conservative testable fallback).

## HADS-7 — Player API

- `PlayerController3D.take_damage(amount: float, knockback: Vector3)`:
  - Reduces `_current_state.current_hp` by `amount`, clamped to `min_hp` (same pattern as existing enemy damage helpers).
  - Adds knockback to `velocity` (X/Y only; Z discarded).

## HADS-8 — Collision filtering

- Hitbox `collision_mask` includes layer **1** (player default body layer in blobert scenes) so `body_entered` fires for the player in authored scenes.

## Non-functional

- Headless unit tests may call `_apply_hit` on the hitbox with a prepared player instance to assert HADS-4–6 without stepping the physics server; production path remains `body_entered` → `_apply_hit`.
