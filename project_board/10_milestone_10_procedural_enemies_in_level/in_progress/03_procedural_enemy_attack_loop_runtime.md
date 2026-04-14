# TICKET: 03_procedural_enemy_attack_loop_runtime

Title: Procedural-spawned enemies run a continuous attack loop in combat

## Description

Enemies placed via procedural combat rooms must **enter and stay in** an offensive loop when the player is in range (or per family policy): e.g. idle → wind-up / telegraph → active hitbox window → recovery, repeating as appropriate. Behavior must reuse existing M8 attack / telegraph / damage plumbing (`EnemyStateMachine`, family attack scripts, `AnimationPlayer` clips) rather than one-off room scripts.

If per-enemy `.attacks.json` (or equivalent) exists next to exports, use it for timing **or** document that clip-driven state transitions are authoritative and JSON is optional for this milestone.

## Acceptance Criteria

- In a play session through a procedural combat room, a spawned enemy **attacks more than once** across an engagement (not a single one-shot).
- Attack cycles respect existing telegraph and hitbox rules from M8; no duplicate damage pipelines.
- No manual editor step required; behavior is identical whether the room was opened from a run or instantiated in isolation for tests.
- `timeout 300 ci/scripts/run_tests.sh` exits 0 — include at least one automated check where feasible (scene load + state probe, or documented skip with headless limitation noted in ticket revision if truly impossible).

## Dependencies

- `02_wire_generated_enemies_combat_rooms`
- M7 — animation clips on spawned instances
- M8 — attack systems and telegraphs

## WORKFLOW STATE

Stage: SPECIFICATION
Revision: 2
Last Updated By: Planner Agent
Next Responsible Agent: Spec Agent
Status: Proceed
Validation Status: Not yet validated.
Blocking Issues: None.

## NEXT ACTION

Spec Agent: author `project_board/specs/procedural_enemy_attack_loop_runtime_spec.md` (or extend M10-01 spec with additive §) tracing M10-01 R4/R5 onto procedural-spawned instances: family attack script attachment/`mutation_drop` parity, `EnemyAnimationController` + existing telegraph/hitbox paths, `GeneratedEnemyEsmStub` vs real `EnemyStateMachine` decision, `.attacks.json` authority vs clip/script timing, and headless hooks for “more than one attack” + run-assembled vs isolated scene parity. Reference scoped log for planner assumptions.
