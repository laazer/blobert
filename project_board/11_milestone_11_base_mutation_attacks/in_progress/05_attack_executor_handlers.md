# TICKET: 05_attack_executor_handlers

**Milestone:** M11 Base Mutation Attacks (Core Foundation)  
**Status:** Ready  
**Type:** Implementation

## Title

Implement AttackExecutor with MELEE_SWIPE and PROJECTILE_SPIT handlers

## Description

AttackExecutor is the dispatch hub for all attacks. It:
1. Receives an AttackResource
2. Matches on effect_type (MELEE_SWIPE, PROJECTILE_SPIT, etc.)
3. Calls the appropriate handler

Implement two handlers for M11:
- `_handle_melee_swipe()` — hitbox in front, check enemies, apply damage + knockback + modifiers
- `_handle_projectile_spit()` — create projectile, fire forward, attach modifiers for on-hit effects

Future handlers (CHARGE, LUNGE, etc.) can be added without changing dispatch logic.

## Acceptance Criteria

- [x] `AttackExecutor` class created (`scripts/attacks/attack_executor.gd`)
- [x] Single dispatch function `execute_attack(attack_resource: AttackResource)`
- [x] Match statement dispatches by effect_type (extensible for future types)
- [x] `_handle_melee_swipe()` implemented:
  - Waits for startup_frames (animation lead)
  - Queries enemies in range
  - Applies damage + knockback (direction-aware)
  - Applies modifiers (poison, acid, slow, etc.)
  - Spawns VFX at hit location
- [x] `_handle_projectile_spit()` implemented:
  - Creates projectile from scene
  - Sets velocity and damage
  - Attaches modifiers for on-hit effects
  - Fires forward
- [x] Dynamic knockback applied correctly:
  - "away" = enemy pushed away from player
  - "toward" = enemy pulled toward player
  - "none" = no knockback
- [x] Tests validate both handlers (successful hits, no hits, knockback direction)
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_core_1_attack_resource (must define AttackResource first)

## Handler Pseudocode

**MELEE_SWIPE:**
```
startup_wait(attack.startup_frames)
enemies = query_enemies_in_range(player.position + facing_direction * attack.range, attack.range)
for enemy in enemies:
  enemy.take_damage(attack.damage)
  apply_knockback(enemy, attack.knockback_magnitude, attack.knockback_direction)
  apply_modifiers(enemy, attack.modifiers)
spawn_vfx(hit_position, attack.color, attack.vfx_scale)
play_sfx("melee_hit")
```

**PROJECTILE_SPIT:**
```
projectile = create_projectile()
projectile.velocity = Vector3(facing_sign * attack.projectile_speed, 0, 0)
projectile.damage = attack.damage
projectile.modifiers = attack.modifiers
projectile.knockback_magnitude = attack.knockback_magnitude
scene.add_child(projectile)
play_sfx("projectile_fire")
```

## Notes

- Assume enemy API: `take_damage(damage, knockback_vector)`, `apply_poison(duration, dps)`, `apply_acid(duration, dps)`, `apply_slowness(multiplier, duration)`, etc.
- Projectile script already exists (from M8); reuse it
- Dynamic knockback calculation: `(enemy.position - player.position).normalized() * magnitude` for "away", reverse for "toward"

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: RED (38 expected failures — implementation does not exist yet)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
- Ticket path: `project_board/11_milestone_11_base_mutation_attacks/in_progress/05_attack_executor_handlers.md`
- Spec: `project_board/specs/attack_executor_spec.md`
- Primary tests: `tests/scripts/attacks/test_attack_executor.gd`
- Plan log: `project_board/checkpoints/M11-05/2026-05-25T-plan-run.md`
- Spec log: `project_board/checkpoints/M11-05/2026-05-25T-spec-run.md`
- Test design log: `project_board/checkpoints/M11-05/2026-05-25T-test-design-run.md`
- Handoff: `project_board/checkpoints/M11-05/handoff-latest.yaml`
- Dependency spec: `project_board/specs/attack_resource_spec.md`
- Spec exit type: generic

## Status
Proceed
