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

## Specification

- **Normative:** `project_board/specs/hitbox_and_damage_system_spec.md` — **HADS-1** through **HADS-8**.
- **Summary:** `class_name EnemyAttackHitbox` extends `Area3D`; `set_hitbox_active` arms at most one hit; `body_entered` applies `take_damage` + planar knockback from hitbox→player; player clamps HP and adds XY velocity impulse.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- **Tests:** `tests/scripts/combat/test_hitbox_and_damage_system.gd` + `tests/scripts/combat/test_hitbox_and_damage_system_adversarial.gd` — HADS / ADV-HADS coverage; full Godot suite green.
- **Full pipeline:** `timeout 300 ci/scripts/run_tests.sh` exit **0** (Godot `=== ALL TESTS PASSED ===`; Python 419 passed, 2026-04-06).
- **AC — script on Area3D:** HADS-1 + implementation path `res://scripts/enemies/enemy_attack_hitbox.gd`.
- **AC — toggle off by default:** HADS-2 / `test_hads_hitbox_default_inactive`.
- **AC — overlap calls player damage:** HADS-4 + `_apply_hit` / `body_entered` contract in spec.
- **AC — HP decreases by configured amount:** `test_hads_hitbox_one_hit_per_activation`, `test_hads_take_damage_reduces_hp`.
- **AC — one hit per activation:** HADS-5 / `test_hads_hitbox_one_hit_per_activation`, `test_hads_hitbox_rearm_allows_second_hit`.
- **AC — knockback from hit direction:** HADS-6 / `test_hads_knockback_direction_away_from_hitbox`, ADV-HADS-01 fallback.
- **AC — `take_damage` on PlayerController3D:** HADS-7 implementation + tests.
- **AC — `run_tests.sh`:** recorded above.
- **Static QA:** No `godot --check-only` (project policy); satisfied via passing suite + spec alignment.

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "spec_ref": "project_board/specs/hitbox_and_damage_system_spec.md",
  "ticket_path": "project_board/8_milestone_8_enemy_attacks/done/hitbox_and_damage_system.md"
}
```

## Status
Proceed

## Reason
All acceptance criteria evidenced by automated tests and full `run_tests.sh`; ticket moved to milestone `done/`.
