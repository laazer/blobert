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

Stage: TEST_DESIGN
Revision: 3
Last Updated By: Spec Agent
Next Responsible Agent: Test Designer Agent
Status: Proceed
Validation Status: Not yet validated.
Blocking Issues: None.

## NEXT ACTION

Test Designer Agent: author deterministic tests with trace IDs (`PEAR-T-##`) mapping to `project_board/specs/procedural_enemy_attack_loop_runtime_spec.md` AC-R1–R6; cover M8 attack attachment on procedural spawns, ≥2 attack cycles in range, dead-state suppression on procedural host, assembler spawn API parity (isolated room vs run path), and gate on `timeout 300 ci/scripts/run_tests.sh` exit 0. Hand off to Test Breaker Agent when suite is red where implementation is expected missing.
