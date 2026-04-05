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

## Run: 2026-04-04T00-00-00Z-autopilot
- Queue mode: single ticket
- Queue scope: `project_board/7_milestone_7_enemy_animation_wiring/backlog/death_animation_playthrough.md`
- Log root: project_board/checkpoints/

### [death_animation_playthrough] — OUTCOME: COMPLETE
Death plays to completion then `queue_free` on enemy root; collision cleared on death; infection/absorb guards; missing-Death clip queues free immediately (GDScript review follow-up). Ticket: `project_board/7_milestone_7_enemy_animation_wiring/done/death_animation_playthrough.md`.
Log: `project_board/checkpoints/death_animation_playthrough/` (planning, spec, test-design, test-break, implementation scoped logs).

## Run: 2026-04-05T00-00-00Z-autopilot-maintenance
- Queue mode: directory scan
- Queue scope: `project_board/maintenance/backlog/`
- Log root: project_board/checkpoints/

### MAINT-AERC / run-2026-04-05-dequeue
- Ticket: `project_board/maintenance/in_progress/animated_enemy_registry_cleanup.md`
- Stage: PLANNING (dequeued)
- Log: `project_board/checkpoints/MAINT-AERC/run-2026-04-05-dequeue.md`

### [MAINT-AERC] — OUTCOME: COMPLETE
Central registry in `src/enemies/animated/registry.py`; package `animated/__init__.py` re-exports builder + six classes; `animated_enemies.py` removed; imports and docs updated; `uv run pytest tests/ -q` → 380 passed. Ticket: `project_board/maintenance/done/animated_enemy_registry_cleanup.md`.
Log: `project_board/checkpoints/MAINT-AERC/run-2026-04-05-ap-continue.md` (unblock + implementation); `project_board/specs/animated_enemy_registry_cleanup_spec.md`.

## Resume: 2026-04-05 (ap-continue) — superseded
- Prior resume pointed at BLOCKED state; dependencies completed; pipeline finished same day.

### MAINT-BMSBA / run-2026-04-05-dequeue
- Ticket: `project_board/maintenance/in_progress/base_models_split_by_archetype.md`
- Stage: PLANNING (dequeued)
- Log: `project_board/checkpoints/MAINT-BMSBA/run-2026-04-05-dequeue.md`

### MAINT-BMSBA / run-2026-04-05-test-design
- Ticket: `project_board/maintenance/in_progress/base_models_split_by_archetype.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/MAINT-BMSBA/run-2026-04-05-test-design.md`
- Outcome: `test_base_models_factory.py` added; `uv run pytest tests/ -q` → 335 passed.

## Resume: 2026-04-05 (ap-continue) — MAINT-BMSBA
- Ticket: `project_board/maintenance/in_progress/base_models_split_by_archetype.md`
- Resuming at Stage: IMPLEMENTATION_GENERALIST (implementation already on disk; verify + commit + COMPLETE)
- Next Agent: Implementation Generalist → AC Gatekeeper (same resume)

### [MAINT-BMSBA] — OUTCOME: COMPLETE
Package `src/enemies/base_models/` committed; monolithic `base_models.py` removed; pytest 380 passed. Ticket: `project_board/maintenance/done/base_models_split_by_archetype.md`.
Log: `project_board/checkpoints/MAINT-BMSBA/run-2026-04-05-ap-continue.md`

## Run: 2026-04-05T12-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/maintenance/backlog/split_animated_acid_spitter.md`
- Log root: project_board/checkpoints/

### [split_animated_acid_spitter] — OUTCOME: COMPLETE
`AnimatedAcidSpitter` moved to `src/enemies/animated_acid_spitter.py`; registry and re-export unchanged; 345 pytest passed; ticket `project_board/maintenance/done/split_animated_acid_spitter.md`.
Log: `project_board/checkpoints/split_animated_acid_spitter/run-2026-04-05-autopilot.md`

## Run: 2026-04-05T14-30-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/maintenance/backlog/split_animated_adhesion_bug.md`
- Log root: project_board/checkpoints/

### [split_animated_adhesion_bug] — OUTCOME: COMPLETE
`AnimatedAdhesionBug` moved to `src/enemies/animated_adhesion_bug.py`; registry unchanged; 360 pytest passed; ticket `project_board/maintenance/done/split_animated_adhesion_bug.md`.
Log: `project_board/checkpoints/split_animated_adhesion_bug/run-2026-04-05-autopilot.md`

## Run: 2026-04-05T16-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/maintenance/backlog/split_animated_carapace_husk.md`
- Log root: project_board/checkpoints/

### [split_animated_carapace_husk] — OUTCOME: COMPLETE
`AnimatedCarapaceHusk` moved to `src/enemies/animated_carapace_husk.py`; registry unchanged; 362 pytest passed; ticket `project_board/maintenance/done/split_animated_carapace_husk.md`.
Log: `project_board/checkpoints/split_animated_carapace_husk/run-2026-04-05-autopilot.md`

## Run: 2026-04-05T18-30-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/maintenance/backlog/split_animated_claw_crawler.md`
- Log root: project_board/checkpoints/

### [split_animated_claw_crawler] — OUTCOME: COMPLETE
`AnimatedClawCrawler` moved to `src/enemies/animated_claw_crawler.py`; registry unchanged; 364 pytest passed; ticket `project_board/maintenance/done/split_animated_claw_crawler.md`.
Log: `project_board/checkpoints/split_animated_claw_crawler/run-2026-04-05-autopilot.md`

## Run: 2026-04-05T21-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/maintenance/backlog/split_animated_ember_imp.md`
- Log root: project_board/checkpoints/

### [split_animated_ember_imp] — OUTCOME: COMPLETE
`AnimatedEmberImp` moved to `src/enemies/animated_ember_imp.py`; registry maps `ember_imp` to that module’s class; 372 pytest passed; ticket `project_board/maintenance/done/split_animated_ember_imp.md`.
Log: `project_board/checkpoints/split_animated_ember_imp/run-2026-04-05-autopilot.md`

## Run: 2026-04-05T22-30-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/maintenance/backlog/split_animated_tar_slug.md`
- Log root: project_board/checkpoints/

### [split_animated_tar_slug] — OUTCOME: COMPLETE
`AnimatedTarSlug` moved to `src/enemies/animated_tar_slug.py`; registry unchanged; 380 pytest passed; ticket `project_board/maintenance/done/split_animated_tar_slug.md`.
Log: `project_board/checkpoints/split_animated_tar_slug/run-2026-04-05-autopilot.md`

## Run: 2026-04-05T23-59-00Z-autopilot-maintenance-backlog
- Queue mode: maintenance backlog directory
- Queue scope: `project_board/maintenance/backlog/`
- Log root: project_board/checkpoints/

### MAINT-EAPD / run-2026-04-05-autopilot
- Ticket: `project_board/maintenance/done/enemy_animation_per_type_policies_deferred.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/MAINT-EAPD/run-2026-04-05-autopilot.md`

### [MAINT-EAPD] — OUTCOME: COMPLETE
Defer-only placeholder closed with policy spec + EAPD-P1..P22 tests; shared `EnemyAnimationController` unchanged; AC-2 explicitly future-only.
Log: `project_board/checkpoints/MAINT-EAPD/run-2026-04-05-autopilot.md`

### MAINT-EMMU / run-2026-04-05-autopilot
- Ticket: `project_board/maintenance/done/enemy_mutation_map_unify.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/MAINT-EMMU/run-2026-04-05-autopilot.md`

### [MAINT-EMMU] — OUTCOME: COMPLETE
`enemy_mutation_map.gd` is the sole `MUTATION_BY_FAMILY` literal; consumers preload it; EMU tests + `run_tests.sh` green; post-review `load_assets` capsule/zero-AABB aligned with `generate_enemy_scenes.gd`.
Log: `project_board/checkpoints/MAINT-EMMU/run-2026-04-05-autopilot.md`

### MAINT-ESEG / run-2026-04-05-autopilot
- Ticket: `project_board/maintenance/done/enemy_script_extension_and_scene_generator.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/MAINT-ESEG/run-2026-04-05-autopilot.md`

### [MAINT-ESEG] — OUTCOME: COMPLETE
Shared `enemy_root_script_resolver.gd`; dual generator parity; ESEG tests; `push_error` on missing/failed root script load after review.
Log: `project_board/checkpoints/MAINT-ESEG/run-2026-04-05-autopilot.md`

### MAINT-ETRP / run-2026-04-05-autopilot
- Ticket: `project_board/maintenance/done/enemy_types_registry_python.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/MAINT-ETRP/run-2026-04-05-autopilot.md`

### [MAINT-ETRP] — OUTCOME: COMPLETE
`enemy_slug_registry.py` holds animated/static tuples; `EnemyTypes` delegates; pytest contract + `main.py list` fixed for six animated slugs.
Log: `project_board/checkpoints/MAINT-ETRP/run-2026-04-05-autopilot.md`

## Run: 2026-04-05
- Queue mode: maintenance backlog directory
- Queue scope: `project_board/maintenance/backlog/`
- Log root: project_board/checkpoints/

### MAINT-EMSI / run-2026-04-05-planning
- Ticket: `project_board/maintenance/in_progress/enemy_model_scale_input.md`
- Stage: PLANNING
- Log: `project_board/checkpoints/MAINT-EMSI/run-2026-04-05-planning.md`

### MAINT-EMSI / run-2026-04-05-spec
- Ticket: `project_board/maintenance/in_progress/enemy_model_scale_input.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/MAINT-EMSI/run-2026-04-05-spec.md`
- Outcome: Formal spec `project_board/specs/enemy_model_scale_input_spec.md` (EMSI-1..5); invalid scale → ValueError; uniform scaling contract + rotation exclusion documented.

### MAINT-EMSI / run-2026-04-05-test-design
- Ticket: `project_board/maintenance/in_progress/enemy_model_scale_input.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/MAINT-EMSI/run-2026-04-05-test-design.md`
- Outcome: EMSI behavioral tests in `asset_generation/python/tests/enemies/test_enemy_model_scale_input.py`; pytest on that file fails pre-implementation (expected) until factory/base/archetypes implement `scale`.

### MAINT-EMSI / run-2026-04-05-test-break
- Ticket: `project_board/maintenance/in_progress/enemy_model_scale_input.md`
- Stage: TEST_BREAK → IMPLEMENTATION_GENERALIST
- Log: `project_board/checkpoints/MAINT-EMSI/run-2026-04-05-test-break.md`
- Outcome: Adversarial extensions (fail-fast empty log, subnormal/huge finite, fractional multiply, primitive-sequence determinism, positional/int scale, unknown-type fallback, direct `HumanoidModel` validation); `# CHECKPOINT` on structural assumptions; pytest file still red until implementation.
