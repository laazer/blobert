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

Stage: COMPLETE
Revision: 8
Last Updated By: Acceptance Criteria Gatekeeper Agent
Next Responsible Agent: Human
Status: Proceed
Validation Status:
- Tests: `godot --headless -s tests/run_tests.gd` exit 0 (`ALL TESTS PASSED`; project convention: `timeout 300 godot --headless -s tests/run_tests.gd`). `ci/scripts/run_tests.sh` exit 0 (`timeout 300 ci/scripts/run_tests.sh`). PEAR contract `tests/system/test_procedural_enemy_attack_loop_runtime_contract.gd` (PEAR-T-* per spec) provides objective coverage mapped to ticket ACs: (1) **Multi-attack engagement** — `test_pear_t_08_procedural_acid_completes_two_attack_cycles_headless` / PEAR-T-08 (≥2 completed cycles, ≥2 projectiles) and PEAR-T-09 (cooldown separation between cycles), as the headless substitute for “attacks more than once” in combat. (2) **M8 telegraph/hitbox, single pipeline** — PEAR-T-01–07, PEAR-T-15 (exactly one family attack node, non-null host, assembler source does not attach attack nodes directly, mutation_drop contract), plus PEAR-T-12 (dead suppresses further cycles), PEAR-T-14 (attack scripts avoid `get_nodes_in_group`). (3) **No manual editor; run vs isolated parity** — PEAR-T-10 (spawn parity), PEAR-T-11 (`RunSceneAssembler` production path uses `_spawn_generated_enemies_for_room`).
- Static QA: Not separately required by ticket ACs; not asserted here beyond green CI.
- Integration: Ticket AC “play session … attacks more than once” is evidenced by the same headless scenario (assembled procedural combat room + physics/animation pump) via PEAR-T-08/09, matching ticket AC that calls for automated checks “where feasible.”
Blocking Issues: None.
Escalation Notes: None.

## NEXT ACTION

Next Responsible Agent: Human
Required Input Schema: N/A
Status: Proceed
Reason: All acceptance criteria have explicit test and CI evidence in Validation Status (PEAR-T-* contract tests; `godot --headless -s tests/run_tests.gd` and `ci/scripts/run_tests.sh` both exit 0). Ticket path aligns with folder rule (`project_board/10_milestone_10_procedural_enemies_in_level/done/`); Stage COMPLETE.
