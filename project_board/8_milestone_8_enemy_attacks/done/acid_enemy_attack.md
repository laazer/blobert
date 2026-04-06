# TICKET: acid_enemy_attack

Title: Acid enemy attack — ranged acid projectile with damage over time

## Description

The acid family enemy attacks by spitting an acid projectile at the player from range. On hit, the projectile applies a damage-over-time (DoT) debuff for 3 seconds. The projectile travels along the X axis at a fixed speed.

## Acceptance Criteria

- Acid enemy fires a projectile when player is within attack range (configurable, default 8 units)
- Projectile travels toward the player along the X axis
- Projectile despawns on wall collision or after 3 seconds
- On hit, player takes initial impact damage and then DoT damage every 0.5s for 3s
- DoT can stack if hit multiple times (each hit adds a new DoT instance)
- Attack has a cooldown (configurable, default 3.0s)
- Attack telegraph plays before projectile fires
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system` (partially superseded: player damage via `PlayerController3D.apply_enemy_acid_damage`)
- `attack_telegraph_system` (partially superseded: `EnemyAnimationController.begin_ranged_attack_telegraph`)

---

## Execution Plan

1. Add player-side stacking acid DoT tracker and impact API on `PlayerController3D`.
2. Add `AcidProjectile3D` Area3D scene: X-axis motion, lifetime, player vs StaticBody3D collision.
3. Add `AcidSpitterRangedAttack` node; spawn from `EnemyInfection3D` when `mutation_drop == "acid"` after animation wiring.
4. Extend `EnemyAnimationController` with Attack telegraph that suppresses idle/walk until the clip finishes.
5. Tests under `tests/scripts/combat/test_acid_enemy_attack.gd` for DoT math, stacking, projectile motion, static despawn.

---

## Specification

- **Range / cooldown / speed:** Exported on `AcidSpitterRangedAttack` (`attack_range` 8, `cooldown_seconds` 3, `projectile_speed` 14).
- **Projectile:** Moves only on world X; `max_lifetime_seconds` 3; `collision_mask` 1; first player touch applies damage then `queue_free`; `StaticBody3D` touch despawns without damaging player.
- **Damage:** Exported on `AcidProjectile3D` (`impact_damage` 8, `dot_tick_damage` 4); DoT uses `round(duration / interval)` ticks (6 for 3s / 0.5s).
- **Telegraph:** If `Attack` exists on the root `AnimationPlayer`, play it to completion before spawn; else timer fallback (`telegraph_fallback_seconds` 0.35).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `tests/scripts/combat/test_acid_enemy_attack.gd` (AEAA-01..03, AEAA-10..11, AEAA-CHK); full `ci/scripts/run_tests.sh` exit 0
- Static QA: Passing — GDScript review for touched files
- Integration: N/A — combat covered by automated tests; manual playtest optional

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
All acceptance criteria are implemented and evidenced by automated tests; optional in-editor playthrough of acid spitter vs player.
