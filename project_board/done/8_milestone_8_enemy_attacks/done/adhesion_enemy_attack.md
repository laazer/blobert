# TICKET: adhesion_enemy_attack

Title: Adhesion enemy attack — slow lunge that briefly roots the player

## Description

The adhesion family enemy attacks by lunging toward the player and applying a brief root effect (player movement speed reduced to 0 for ~0.5s) on hit. The lunge closes a short gap and the hit registers via the shared hitbox system.

## Acceptance Criteria

- Adhesion enemy enters a lunge state when player is within attack range
- Lunge moves the enemy forward along the X axis toward the player
- On successful hit, player movement speed is set to 0 for 0.5 seconds (root effect)
- Root effect wears off cleanly — no permanent slow
- Attack has a cooldown (configurable, default 2.0s) before re-triggering
- Attack telegraph plays before lunge (uses `attack_telegraph_system`)
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system` (proximity hit during lunge window in lieu of shared hitbox ticket)
- `attack_telegraph_system` (`EnemyAnimationController.begin_ranged_attack_telegraph` + `ranged_attack_telegraph_finished`)
- M15 (Enemy Navigation) — optional; lunge is range-gated toward current player position

---

## Execution Plan

1. `PlayerController3D`: movement root timer (`apply_enemy_movement_root`), zero horizontal input/velocity while active.
2. `AdhesionBugLungeAttack` child node: telegraph → lunge on X toward player → proximity hit → root on player; cooldown.
3. `EnemyInfection3D`: skip default `velocity.x = 0` while lunge child drives horizontal velocity (`enemy_writes_velocity_x_this_frame`); wire node when `mutation_drop == "adhesion"`.

---

## Specification

- **Range / cooldown / lunge:** Exported on `AdhesionBugLungeAttack` (`attack_range` 3, `cooldown_seconds` 2, `lunge_speed` 10, `lunge_duration_seconds` 0.28).
- **Hit:** Axis-aligned bounds: `hit_radius_x` 0.95, `hit_radius_y` 1.4 from enemy origin vs player origin; one root per lunge (`_hit_registered`).
- **Root:** `root_duration_seconds` 0.5; `apply_enemy_movement_root` uses `maxf` so overlapping applies refresh to the longer remaining window, not sum.
- **Telegraph:** Same as acid: `Attack` clip if present, else timer fallback (`telegraph_fallback_seconds` 0.3).
- **Process order:** Lunge node `process_physics_priority = -100` so it runs before enemy body and writes `velocity.x` before `move_and_slide`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `tests/scripts/combat/test_adhesion_enemy_attack.gd` (AELA-01..03, AELA-CHK, AELA-10); `ci/scripts/run_tests.sh` exit 0
- Static QA: Passing — no new linter errors on new scripts
- Integration: Partial — player root + lunge wiring covered by tests; full feel check in editor optional

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
{}
```

## Status
Proceed

## Reason
Automated tests cover root contract and lunge velocity gate; playtest adhesion bug in sandbox for timing/tuning if desired.
