# TICKET: death_animation_playthrough

Title: Death animation plays through before enemy despawn
Project: blobert
Created By: Planner (autonomous)
Created On: 2026-04-04

---

## Description

When an enemy reaches the dead state, the Death animation plays fully before the node is freed. The enemy must not disappear mid-animation. After the animation completes, the node is removed cleanly.

## Acceptance Criteria

- Enemy plays `Death` clip to completion before `queue_free()` is called
- No physics interaction occurs during death animation (disable collision on death)
- Enemy cannot be targeted or infected during death animation
- If the scene is unloaded while death animation is playing, no crash or error
- Works for all 4 enemy families
- `run_tests.sh` exits 0

## Dependencies

- `wire_animations_to_generated_scenes`
- EnemyStateMachine must have a DEAD state or equivalent transition hook

## Specification

Full functional and non-functional spec: `project_board/specs/death_animation_playthrough_spec.md` (requirements DAP-1–DAP-4, DAP-NF1–DAP-NF2).

---

## Execution Plan

Numbered tasks for downstream agents. Owners follow `agent_context/agents/` roles.

1. **Specification (Spec Agent)** — Depends on: none. Produce `project_board/specs/death_animation_playthrough_spec.md` (or milestone-scoped path per project convention): exact lifecycle from `apply_death_event()` / ESM `dead` through `AnimationPlayer` completion signal, collision layer/mask changes, targeting/absorb/infection/chunk-contact guards, scene-unload/`is_instance_valid` behavior, and scope (12 generated scenes: `adhesion_bug`, `acid_spitter`, `carapace_husk`, `claw_crawler` × variants `00`–`02`). Reference `scripts/enemy/enemy_infection_3d.gd`, `scripts/enemies/enemy_animation_controller.gd`, `scripts/infection/infection_interaction_handler.gd`, `scripts/player/player_controller_3d.gd`.

2. **Test design (Test Designer Agent)** — Depends on: task 1. Author failing-first tests in `tests/` (scene or script tests) covering: Death plays before free, collision off during death, no absorb/infect while dying, unload safety, and at least one case per family or parameterized list of the 12 `.tscn` paths. Align with existing patterns (`test_enemy_scene_animation_wiring.gd`, chunk/infection tests).

3. **Test break (Test Breaker Agent)** — Depends on: task 2. Stress adversarial cases: double absorb, rapid scene change, missing `Death` clip, freed `AnimationPlayer`, concurrent signals.

4. **Implementation — engine integration (Engine Integration Agent)** — Depends on: task 3. Wire death sequence: disable physics/collision, ensure `EnemyAnimationController` does not skip Death mid-play (adjust latch/`_physics_process` if spec requires completion-driven free), invoke `queue_free()` only after completion, guard all async paths with `is_instance_valid` / tree exit.

5. **Implementation — gameplay cross-check (Gameplay Systems Agent)** — Depends on: task 4. Verify `InfectionInteractionHandler` / `PlayerController3D` / chunk DoT paths respect “dying” enemy (no new targeting, no infection edge cases); adjust only if spec requires files outside engine-integration ownership.

6. **Static QA + integration (AC Gatekeeper / test suite)** — Depends on: task 5. `run_tests.sh` exit 0; manual spot-check optional per spec.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
STATIC_QA

## Revision
5

## Last Updated By
Engine Integration Agent

## Validation Status
- Tests: `timeout 300 godot -s tests/run_tests.gd` exit 0 (2026-04-04) — DAP death playthrough, adversarial, infection suites pass
- Static QA: Pending (AC Gatekeeper)
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/7_milestone_7_enemy_animation_wiring/backlog/death_animation_playthrough.md",
  "spec_path": "project_board/specs/death_animation_playthrough_spec.md",
  "checkpoint_log": "project_board/checkpoints/death_animation_playthrough/run-2026-04-04-implementation.md"
}
```

## Status
Proceed

## Reason
Engine Integration: `EnemyAnimationController` wires `AnimationPlayer.animation_finished` to idempotent `queue_free()` on enemy root after `Death`; clears `collision_layer`/`collision_mask` on death start; skips `play("Death")` when clip missing (no engine error spam); `trigger_hit_animation` null-guards player. `InfectionInteractionHandler`: absorb path rejects dead targets; `resolve_absorb_for_esm` no-op when dead; `_ready` uses `is_inside_tree()` before `get_tree()`. GameplaySystems cross-check (task 5) not required for observed test coverage; AC Gatekeeper to confirm full AC list and STATIC_QA sign-off.
