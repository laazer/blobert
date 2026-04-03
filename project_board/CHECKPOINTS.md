# Checkpoint Index

This file is intentionally small and acts as an index only.
Full checkpoint bodies live under `project_board/checkpoints/`.

## Index-only rules (agents must follow)

- **Do not** append checkpoint decision bodies here: no `**Would have asked:**`, no `**Assumption made:**`, no multi-paragraph assumptions.
- **Do** write those only under `project_board/checkpoints/<ticket-id>/<run-id>.md`.
- **Do** keep entries here short: run/resume headers, ticket path, stage, `Log:` path, and optional one-line outcome summaries.

## Migration

- Monolithic log frozen on 2026-03-30:
  - `project_board/checkpoints/frozen/CHECKPOINTS-2026-03-30-frozen.md`
- New write target for checkpoint details:
  - `project_board/checkpoints/<ticket-id>/<run-id>.md`
- Backward compatibility:
  - If a consumer cannot find a scoped log yet, it may read the frozen file.

---

## Run Index

### 2026-03-30-migration
- Ticket: N/A (checkpoint system migration)
- Stage: migration
- Log: `project_board/checkpoints/frozen/CHECKPOINTS-2026-03-30-frozen.md`
- Notes: monolithic checkpoint log frozen and replaced by index-only file.

### first_4_families_in_level / run-2026-03-30-01
- Ticket: `project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md`
- Stage: IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE → resuming at AC Gatekeeper
- Log: `project_board/checkpoints/first_4_families_in_level/run-2026-03-30-01.md`
- Outcome: generate_enemy_scenes.gd written; 12 .tscn files generated and committed; level updated with 4 family enemies; all 54 FESG tests pass. Engine Integration Agent (run-2): fixed AC-4 positions (ClawCrawlerEnemy→(0,1,4), CarapaceHuskEnemy→(0,1,-4)); implemented AC-3 per-family mutation dispatch (mutation_drop export on EnemyInfection3D, optional enemy_node param on set_target_esm, optional mutation_id param on resolve_absorb, level mutation_drop overrides); all tests pass.

## Run: 2026-04-01
- Queue mode: milestone directory scan
- Queue scope: `project_board/7_milestone_7_enemy_animation_wiring/backlog/`
- Log root: project_board/checkpoints/

### M7-ACS / run-2026-04-01-planning
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/animation_controller_script.md`
- Stage: PLANNING → SPECIFICATION
- Log: `project_board/checkpoints/M7-ACS/run-2026-04-01-planning.md`
- Outcome: Decomposed into 6 tasks; resolved state system ambiguity (EnemyStateMachine strings are canonical), stub-based test strategy chosen, AnimationPlayer null-guard pattern documented.

### M7-WAGS / run-2026-04-03-planning
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/wire_animations_to_generated_scenes.md`
- Stage: PLANNING
- Log: `project_board/checkpoints/M7-WAGS/run-2026-04-03-planning.md`

### M7-WAGS / run-2026-04-03-ac-gatekeeper
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/wire_animations_to_generated_scenes.md`
- Stage: IMPLEMENTATION → INTEGRATION (AC-3 manual open)
- Log: `project_board/checkpoints/M7-WAGS/run-2026-04-03-ac-gatekeeper.md`
- Outcome: AC-1,2,4,5 evidenced; `ci/scripts/run_tests.sh` bounded with `timeout` on `--import` + headless test run; AC-3 pending human editor idle check.

### M7-WAGS — OUTCOME: COMPLETE
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/done/wire_animations_to_generated_scenes.md`
- Stage: INTEGRATION → COMPLETE (human AC-3 sign-off 2026-04-03)
- Log: `project_board/checkpoints/M7-WAGS/run-2026-04-03-ac-gatekeeper.md` (superseded by ticket Validation Status)
- Outcome: Generated .tscn wiring + infection/GLB animation path + non-looping replay; all AC met; ticket in `done/`.

### M7-BAE — OUTCOME: COMPLETE
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/done/blender_animation_export.md`
- Stage: IMPLEMENTATION_GENERALIST → COMPLETE
- Log: `project_board/checkpoints/M7-BAE/`
- Outcome: animation_system.py NLA wiring + constants.py export name map implemented; 12 GLBs regenerated with 13 clips each (Idle/Walk/Hit/Death + 9 extended); all BAE-01..16 + ADV-BAE-G tests pass; 329 Python tests pass; run_tests.sh exits 0.

### M7-ACS — OUTCOME: COMPLETE
State-driven AnimationController implemented with 39 tests (23 primary + 16 adversarial). Key rework: GDScript review caught untyped @export + RefCounted serialization conflict; generator re-run required after code changes; spec corrected to match accepted design. All 12 generated .tscn files contain AnimationPlayer + EnemyAnimationController nodes.
Log: project_board/checkpoints/M7-ACS/

## Run: 2026-03-31
- Queue mode: milestone directory scan
- Queue scope: `project_board/7_milestone_7_enemy_animation_wiring/backlog/`
- Log root: project_board/checkpoints/

### M7-BAE / run-2026-03-31-planning
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md`
- Stage: PLANNING
- Log: `project_board/checkpoints/M7-BAE/run-2026-03-31-planning.md`

## Run: 2026-04-02

### M7-BAE / run-2026-04-02-spec
- Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/M7-BAE/run-2026-03-31-planning.md` (appended)
- Outcome: Full spec produced at `project_board/specs/blender_animation_export_spec.md`. NLA wiring pattern, export name mapping (13 clips), OBJECT mode guard, and GLTF export flag contract specified. Ticket advanced to TEST_DESIGN.
