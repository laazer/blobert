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

## Run: 2026-04-08T20-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/04_editor_ui_draft_status_for_exports.md`
- Lean: no
- Log root: project_board/checkpoints/

### M9-EUDS / run-2026-04-08-autopilot
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/04_editor_ui_draft_status_for_exports.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/M9-EUDS/run-2026-04-08-autopilot.md`

### [M9-EUDS] — OUTCOME: COMPLETE
Model registry service + `/api/registry/*` + Registry UI tab + spawn_eligible consumer; tests `tests/model_registry/`, `tests/web/test_registry_api.py`; dev deps fastapi/httpx for ASGI tests.
Log: `project_board/checkpoints/M9-EUDS/run-2026-04-08-autopilot.md`

---

## Run: 2026-04-08T18-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/03_procedural_material_and_color_pipeline_fixes.md`
- Lean: no
- Log root: project_board/checkpoints/

### M9-PMCP / run-2026-04-08-autopilot
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/03_procedural_material_and_color_pipeline_fixes.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/M9-PMCP/run-2026-04-08-autopilot.md`

### [M9-PMCP] — OUTCOME: COMPLETE
Organic/metallic principled roughness no longer driven by full-range noise; subtler organic base-color mix; spec PMCP-*; tests `test_material_system_principled_pipeline.py` + import test for diff-cover; `run_tests.sh` green.
Log: `project_board/checkpoints/M9-PMCP/run-2026-04-08-autopilot.md`

---

## Run: 2026-04-08T14-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/10_body_part_color_picker_limb_joint_hierarchy.md`
- Lean: no
- Log root: project_board/checkpoints/

### M9-BPCLJH / run-2026-04-08-planning
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/10_body_part_color_picker_limb_joint_hierarchy.md`
- Stage: PLANNING (in progress)
- Log: `project_board/checkpoints/M9-BPCLJH/run-2026-04-08-planning.md`

### [M9-BPCLJH] — OUTCOME: COMPLETE
Limb/joint feature zones, flat `feat_limb_*` / `feat_joint_*`, `material_for_zone_part`, imp/carapace/spider apply paths, frontend `str` hex row + grouped colors UI; spec `project_board/specs/body_part_color_picker_limb_joint_hierarchy_spec.md`; `run_tests.sh` green.
Log: `project_board/checkpoints/M9-BPCLJH/run-2026-04-08-planning.md`

---

## Run: 2026-04-08T12-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/01_spec_model_registry_draft_versions_and_editor_contract.md`
- Lean: no
- Log root: project_board/checkpoints/

### M9-MRVC / run-2026-04-08-autopilot-planning
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/01_spec_model_registry_draft_versions_and_editor_contract.md`
- Stage: PLANNING → COMPLETE (full pipeline)
- Log: `project_board/checkpoints/M9-MRVC/run-2026-04-08-autopilot-planning.md`

### [M9-MRVC] — OUTCOME: COMPLETE
MRVC spec at `project_board/specs/model_registry_draft_versions_spec.md`; contract pytest 22 tests; `run_tests.sh` green; ticket in `9_milestone_9_enemy_player_model_visual_polish/done/`.
Log: `project_board/checkpoints/M9-MRVC/run-2026-04-08-autopilot-ac-gatekeeper.md`

---

## Run: 2026-04-07T00:00:00Z
- Queue mode: milestone directory scan
- Queue scope: `project_board/21_milestone_21_3d_model_quick_editor/backlog/`
- Lean: no
- Log root: project_board/checkpoints/

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
`AnimatedEmberImp` moved to `src/enemies/animated_ember_imp.py`; registry maps `ember_imp` to that module's class; 372 pytest passed; ticket `project_board/maintenance/done/split_animated_ember_imp.md`.
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

### MAINT-EMSI / run-2026-04-05-ac-gatekeeper
- Ticket: `project_board/maintenance/done/enemy_model_scale_input.md`
- Stage: STATIC_QA → COMPLETE
- Log: `project_board/checkpoints/MAINT-EMSI/run-2026-04-05-ac-gatekeeper.md`
- Outcome: AC1–AC4 mapped to `test_enemy_model_scale_input.py` + full `pytest tests/` + `run_tests.sh`; gatekeeper re-ran commands (19 + 405 tests, Godot exit 0); ticket `git mv` to `maintenance/done/`.

### MAINT-HCSI / run-2026-04-05-planning
- Ticket: `project_board/maintenance/in_progress/hud_components_scale_input.md`
- Stage: PLANNING
- Log: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-planning.md`

### MAINT-HCSI / run-2026-04-05-spec
- Ticket: `project_board/maintenance/in_progress/hud_components_scale_input.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-spec.md`
- Outcome: `project_board/specs/hud_components_scale_input_spec.md` (HCSI-1..7); ticket Specification section + path contract for `GameUI` / fusion tests; test obligations in HCSI-6.

### MAINT-HCSI / run-2026-04-05-test-design
- Ticket: `project_board/maintenance/in_progress/hud_components_scale_input.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-test-design.md`
- Outcome: `tests/ui/test_hud_components_scale_input.gd` (HCSI-1/4/5/6); `test_player_hud_layout.gd` design-space helper; T-42 global-rect viewport checks; suite red until `hud_scale` implementation.

### MAINT-HCSI / run-2026-04-05-test-break
- Ticket: `project_board/maintenance/in_progress/hud_components_scale_input.md`
- Stage: TEST_BREAK → IMPLEMENTATION_FRONTEND
- Log: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-test-break.md`
- Outcome: Adversarial extensions in `tests/ui/test_hud_components_scale_input.gd` (fractional scale, idempotent 1→2→1, MutationIcon1 vs HPBar, Hints container vs MoveHint, int→float coercion, NAN/INF and zero/negative sanity, stress `s=4`); `# CHECKPOINT` on structural assumptions; 12 failures in HUD suite file until implementation.

### MAINT-HCSI / run-2026-04-05-ac-gatekeeper
- Ticket: `project_board/maintenance/done/hud_components_scale_input.md`
- Stage: STATIC_QA → COMPLETE
- Log: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-ac-gatekeeper.md`
- Outcome: AC1–AC3 mapped to `tests/ui/test_hud_components_scale_input.gd`, `test_player_hud_layout.gd`, and `infection_ui.gd` docs; gatekeeper re-ran `timeout 300 ci/scripts/run_tests.sh` (exit 0, `=== ALL TESTS PASSED ===`); ticket `git mv` to `maintenance/done/`.

### [MAINT-HCSI] — OUTCOME: COMPLETE
Exported `hud_scale` on `InfectionUI`; uniform HUD scaling + `tests/ui` HCSI coverage; `run_tests.sh` green.
Log: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-ac-gatekeeper.md`

### MAINT-SLEEV / run-2026-04-05-planning
- Ticket: `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`
- Stage: PLANNING
- Log: `project_board/checkpoints/MAINT-SLEEV/run-2026-04-05-planning.md`

### MAINT-SLEEV / run-2026-04-05-spec
- Ticket: `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/MAINT-SLEEV/run-2026-04-05-spec.md`
- Outcome: `project_board/specs/sandbox_scene_legacy_external_enemy_visuals_spec.md` (SLEEV-1..5); removes direct .glb + MeshInstance3D from sandbox; consolidates enemies via generated .tscn; test obligations in SLEEV-5.

### MAINT-SLEEV / run-2026-04-05-test-design
- Ticket: `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/MAINT-SLEEV/run-2026-04-05-test-design.md`
- Outcome: `tests/scenes/levels/test_sandbox_scene_legacy_cleanup.gd` (SLEEV-T-1..5); red until legacy nodes removed and correct .tscn wired.

### MAINT-SLEEV / run-2026-04-05-test-break
- Ticket: `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`
- Stage: TEST_BREAK → IMPLEMENTATION_GENERALIST
- Log: `project_board/checkpoints/MAINT-SLEEV/run-2026-04-05-test-break.md`
- Outcome: Adversarial SLEEV adversarial extensions in same test file; 11 failures until implementation.

### MAINT-SLEEV / run-2026-04-05-ac-gatekeeper
- Ticket: `project_board/maintenance/done/sandbox_scene_legacy_external_enemy_visuals.md`
- Stage: STATIC_QA → COMPLETE
- Log: `project_board/checkpoints/MAINT-SLEEV/run-2026-04-05-ac-gatekeeper.md`
- Outcome: `run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`); ticket `git mv` to `maintenance/done/`.

### [MAINT-SLEEV] — OUTCOME: COMPLETE
Sandbox scene legacy cleanup; generated .tscn wired; `run_tests.sh` green.
Log: `project_board/checkpoints/MAINT-SLEEV/run-2026-04-05-ac-gatekeeper.md`

### MAINT-TSGR / run-2026-04-05-planning
- Ticket: `project_board/maintenance/in_progress/test_suite_green_and_runner_exit_codes.md`
- Stage: PLANNING
- Log: `project_board/checkpoints/MAINT-TSGR/run-2026-04-05-planning.md`

### MAINT-TSGR / run-2026-04-05-spec
- Ticket: `project_board/maintenance/in_progress/test_suite_green_and_runner_exit_codes.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/MAINT-TSGR/run-2026-04-05-spec.md`
- Outcome: `project_board/specs/test_suite_green_and_runner_exit_codes_spec.md` (TSGR-1..8); ticket Specification section; Next Test Designer Agent.

### MAINT-TSGR / run-2026-04-05-test-design
- Ticket: `project_board/maintenance/in_progress/test_suite_green_and_runner_exit_codes.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/MAINT-TSGR/run-2026-04-05-test-design.md`
- Outcome: `ci/scripts/verify_tsgr_runner_contract.sh` + `asset_generation/python/tests/ci/test_tsgr_runner_contract.py`; baseline Godot exit 0; contract verifier 10 fails until implementation; Next Test Breaker Agent.

### MAINT-TSGR / run-2026-04-05-test-break
- Ticket: `project_board/maintenance/in_progress/test_suite_green_and_runner_exit_codes.md`
- Stage: TEST_BREAK → IMPLEMENTATION_GENERALIST
- Log: `project_board/checkpoints/MAINT-TSGR/run-2026-04-05-test-break.md`
- Outcome: Adversarial pytest extensions (hollow-guard, cwd independence, process boundary, Python mirrors TSGR-1/2/4/5/6); 6 failed / 8 passed until implementation; Next Implementation Generalist Agent.

### MAINT-TSGR / run-2026-04-05-ac-gatekeeper
- Ticket: `project_board/maintenance/done/test_suite_green_and_runner_exit_codes.md`
- Stage: STATIC_QA → COMPLETE
- Log: `project_board/checkpoints/MAINT-TSGR/run-2026-04-05-ac-gatekeeper.md`
- Outcome: `verify_tsgr_runner_contract.sh` + `timeout 300 ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`, Python 419 passed); CLAUDE.md/lefthook/`run_tests.sh` alignment; ticket `git mv` to `maintenance/done/`.

### [MAINT-TSGR] — OUTCOME: COMPLETE
Unified test runner (Godot + Python), fail-fast import, exit-code contract; verifier + adversarial pytest + full suite green.
Log: `project_board/checkpoints/MAINT-TSGR/run-2026-04-05-ac-gatekeeper.md`

### [MAINT-EMSI] — OUTCOME: COMPLETE
`scale` on factory/`BaseModelType`; all archetypes; EMSI tests + full Python suite + `run_tests.sh` green.
Log: `project_board/checkpoints/MAINT-EMSI/run-2026-04-05-ac-gatekeeper.md`

## Run: 2026-04-06
- Queue mode: single ticket
- Queue scope: `project_board/8_milestone_8_enemy_attacks/backlog/acid_enemy_attack.md`
- Log root: project_board/checkpoints/

### acid_enemy_attack / run-2026-04-06-autopilot
- Ticket: `project_board/8_milestone_8_enemy_attacks/done/acid_enemy_attack.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/acid_enemy_attack/run-2026-04-06-autopilot.md`

### [acid_enemy_attack] — OUTCOME: COMPLETE
Acid spitter ranged attack: projectile scene, player stacking DoT, Attack telegraph on `EnemyAnimationController`, tests in `tests/scripts/combat/test_acid_enemy_attack.gd`; `ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/acid_enemy_attack/run-2026-04-06-autopilot.md`

## Run: 2026-04-07
- Queue mode: single ticket
- Queue scope: `project_board/8_milestone_8_enemy_attacks/backlog/adhesion_enemy_attack.md`
- Log root: project_board/checkpoints/

### adhesion_enemy_attack / run-2026-04-07-autopilot
- Ticket: `project_board/8_milestone_8_enemy_attacks/done/adhesion_enemy_attack.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/adhesion_enemy_attack/run-2026-04-07-autopilot.md`

### [adhesion_enemy_attack] — OUTCOME: COMPLETE
Adhesion lunge: `AdhesionBugLungeAttack` + player `apply_enemy_movement_root`, enemy velocity X gate in `EnemyInfection3D`, tests `tests/scripts/combat/test_adhesion_enemy_attack.gd`; `ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/adhesion_enemy_attack/run-2026-04-07-autopilot.md`

## Run: 2026-04-06T12-00-00Z-autopilot-attack-telegraph
- Queue mode: single ticket
- Queue scope: `project_board/8_milestone_8_enemy_attacks/backlog/attack_telegraph_system.md`
- Lean: no
- Log root: project_board/checkpoints/

### attack_telegraph_system / run-2026-04-06-dequeue
- Ticket: `project_board/8_milestone_8_enemy_attacks/done/attack_telegraph_system.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-ac-gatekeeper.md`

### [attack_telegraph_system] — OUTCOME: COMPLETE
Attack telegraph: ATS-2 wall hold in `EnemyAnimationController`, acid/adhesion telegraph guards + `maxf` fallback, carapace/claw stub attacks + `EnemyInfection3D` wiring; T-ATS + ADV-ATS suites; `ci/scripts/run_tests.sh` exit 0; death preempts telegraph follow-up (`bb4488d`).
Log: `project_board/checkpoints/attack_telegraph_system/`

### attack_telegraph_system / run-2026-04-06-planning
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`
- Stage: PLANNING → SPECIFICATION
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-planning.md`
- Outcome: Task table for Spec → Test Design → Test Break → Implementation → gate; hitbox backlog boundary + four-family scope + visual fallback assumptions logged.

### attack_telegraph_system / run-2026-04-06-spec
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-spec.md`
- Outcome: Formal spec written (ATS-1 … ATS-9, ATS-NF1, ATS-NF2); telegraph vs active phase, 0.3 s floor, visual + export + four-family map + `EnemyAnimationController` + `hitbox_and_damage_system` boundary; checkpoint assumptions logged for export naming and carapace/claw scope.

### attack_telegraph_system / run-2026-04-06-test-design
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-test-design.md`
- Outcome: Primary suite `tests/scripts/enemy/test_attack_telegraph_system.gd` (T-ATS-*); T-ATS-08 red until `carapace_husk_attack.gd` / `claw_crawler_attack.gd` exist; SceneTree/get_tree limitation during `run_tests` documented in log.

### attack_telegraph_system / run-2026-04-06-test-break
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`
- Stage: TEST_BREAK → IMPLEMENTATION_GENERALIST
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-test-break.md`
- Outcome: ADV-ATS adversarial suite added; 7 ADV failures + T-ATS-08 until telegraph floor/re-entry/`maxf` clamps + carapace/claw scripts; Next Gameplay Systems Agent.

### attack_telegraph_system / run-2026-04-06-gameplay-systems
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md`
- Stage: IMPLEMENTATION_GENERALIST → STATIC_QA
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-gameplay-systems.md`
- Outcome: ATS-2 wall-clock hold in controller; acid/adhesion guards + `maxf` fallback; carapace/claw attack scripts + `EnemyInfection3D` wiring; telegraph suites 20+45 pass; full `run_tests.gd` exit 0.

### attack_telegraph_system / run-2026-04-06-ac-gatekeeper
- Ticket: `project_board/8_milestone_8_enemy_attacks/done/attack_telegraph_system.md`
- Stage: STATIC_QA → COMPLETE
- Log: `project_board/checkpoints/attack_telegraph_system/run-2026-04-06-ac-gatekeeper.md`
- Outcome: AC matrix mapped to primary + adversarial telegraph tests; `timeout 300 ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`, Python 419 passed); ticket `git mv` to `8_milestone_8_enemy_attacks/done/`.

## Run: 2026-04-06-autopilot-hitbox-damage
- Queue mode: single ticket
- Queue scope: `project_board/8_milestone_8_enemy_attacks/backlog/hitbox_and_damage_system.md` (dequeued to `in_progress/`)
- Lean: no
- Log root: project_board/checkpoints/

### [hitbox_and_damage_system] — OUTCOME: COMPLETE
Enemy `Area3D` hitbox (`EnemyAttackHitbox`) + `PlayerController3D.take_damage`; primary + adversarial combat tests; spec `project_board/specs/hitbox_and_damage_system_spec.md`; `ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/hitbox_and_damage_system/run-2026-04-06-autopilot.md`

## Run: 2026-04-06T22-00-00Z-autopilot-carapace-attack
- Queue mode: single ticket
- Queue scope: `project_board/8_milestone_8_enemy_attacks/in_progress/carapace_enemy_attack.md`
- Lean: no
- Log root: project_board/checkpoints/

### carapace_enemy_attack / run-2026-04-06-planning
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/carapace_enemy_attack.md`
- Stage: PLANNING → SPECIFICATION
- Log: `project_board/checkpoints/carapace_enemy_attack/run-2026-04-06-planning.md`
- Outcome: Task table for Spec → Test Design → Test Break → Implementation → gate; 0.6s telegraph vs `ATS2_MIN_TELEGRAPH` (0.3s), damage/knockback defaults, wall vs max-range termination assumptions logged.

### carapace_enemy_attack / run-2026-04-06-implementation
- Ticket: `project_board/8_milestone_8_enemy_attacks/done/carapace_enemy_attack.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/carapace_enemy_attack/run-2026-04-06-implementation.md`

### [carapace_enemy_attack] — OUTCOME: COMPLETE
Carapace charge: `begin_ranged_attack_telegraph(0.6)` + `_telegraph_min_hold_sec` in `EnemyAnimationController`; full `CarapaceHuskAttack` with HADS hitbox, wall/range stops, decel, `EnemyInfection3D` velocity gate; spec `project_board/specs/carapace_enemy_attack_spec.md`; tests `tests/scripts/combat/test_carapace_enemy_attack*.gd`; `ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/carapace_enemy_attack/`

## Run: 2026-04-06T23-30-00Z-autopilot-claw-attack-lean
- Queue mode: single ticket
- Queue scope: `project_board/8_milestone_8_enemy_attacks/backlog/claw_enemy_attack.md`
- Lean: yes (Stage 7 Learning skipped)
- Log root: project_board/checkpoints/
- Learning: skipped (lean mode)

### claw_enemy_attack / run-2026-04-06-planning
- Ticket: `project_board/8_milestone_8_enemy_attacks/in_progress/claw_enemy_attack.md` (dequeued)
- Stage: planning assumptions
- Log: `project_board/checkpoints/claw_enemy_attack/run-2026-04-06-planning.md`

### claw_enemy_attack / run-2026-04-06-implementation
- Ticket: `project_board/8_milestone_8_enemy_attacks/done/claw_enemy_attack.md`
- Stage: COMPLETE
- Log: `project_board/checkpoints/claw_enemy_attack/run-2026-04-06-implementation.md`

### [claw_enemy_attack] — OUTCOME: COMPLETE
Claw 2-hit combo: per-swipe `begin_ranged_attack_telegraph` + `EnemyAttackHitbox` re-arm, pause between swipes, defaults range 2 / cooldown 1.2 / damage 7 per hit; spec `project_board/specs/claw_enemy_attack_spec.md`; tests `tests/scripts/combat/test_claw_enemy_attack*.gd`; `telegraph_fallback_seconds` default 0.35 for ADV-ATS-08b; `ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/claw_enemy_attack/`

## Run: 2026-04-07T00-00-00Z-planner-M19-ARGLB
- Queue mode: single ticket
- Queue scope: `project_board/21_milestone_21_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md`
- Lean: no
- Log root: project_board/checkpoints/M19-ARGLB/

### M19-ARGLB / run-2026-04-07T00-00-00Z-planning
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md`
- Stage: PLANNING → SPECIFICATION
- Log: `project_board/checkpoints/M19-ARGLB/run-2026-04-07T00-00-00Z-planning.md`
- Outcome: Scaffold already fully implemented in commit 49ba13a; planning decomposes into gap-fill + test-write pipeline. Three checkpoints logged: scaffold-complete ambiguity, GlbViewer `setAvailableClips` misuse, path-traversal test coverage gap.

### M19-ARGLB / run-2026-04-07T01-00-00Z-spec
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Log: `project_board/checkpoints/M19-ARGLB/run-2026-04-07T01-00-00Z-spec.md`
- Outcome: Full spec `project_board/specs/assets_router_and_glb_viewer_spec.md` (ARGLB-1..8); path-jail 400/403/404 layering, MIME contract, cache-bust `?t=` param, `availableClips` store slice, `GlbViewer` aliasing bug fix, ErrorBoundary fallback, `AnimationControls` active state; four manual-verify ACs flagged.

### M19-ARGLB / run-2026-04-07T02-00-00Z-test-design
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Log: `project_board/checkpoints/M19-ARGLB/run-2026-04-07T02-00-00Z-test-design.md`
- Outcome: `asset_generation/web/backend/tests/test_assets_router.py` (23 tests, httpx+ASGITransport); `conftest.py` sys.path fixture; `requirements.txt` + httpx + pytest-asyncio; 20 pass / 3 red (literal-dot traversal httpx normalization + directory FileResponse crash); checkpoint logs httpx URL normalization discovery and directory-path 500 vs 404 gap.

### M19-ARGLB / run-2026-04-07T03-00-00Z-test-break
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/in_progress/assets_router_and_glb_viewer.md`
- Stage: TEST_BREAK → IMPLEMENTATION_ENGINE_INTEGRATION
- Log: `project_board/checkpoints/M19-ARGLB/run-2026-04-07T03-00-00Z-test-break.md`
- Outcome: 15 adversarial tests added (38 total, 33 pass / 5 red); exposed 3 distinct implementation gaps: (1) null-byte in path causes unhandled ValueError from resolve() — not caught by try/except which only wraps relative_to(); (2) directory path causes unhandled RuntimeError from FileResponse — needs is_file() guard; (3) spec claims dotfile `.glb` has suffix `.glb` — Python 3.9 returns empty suffix so dotfiles are excluded. Double-encoded traversal (%252e%252e→403), uppercase extension MIME (octet-stream), stress 50 files, sort invariant, and within-jail traversal tests all pass.

## Resume: 2026-04-07 (ap-continue) — M19-ARGLB
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/assets_router_and_glb_viewer.md`
- Resuming at Stage: `IMPLEMENTATION_ENGINE_INTEGRATION`
- Next Agent: `Engine Integration Agent`
- Log: `project_board/checkpoints/M19-ARGLB/run-2026-04-07-ap-continue.md`

### [M19-ARGLB] — OUTCOME: COMPLETE
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/assets_router_and_glb_viewer.md`
- Stage: IMPLEMENTATION_ENGINE_INTEGRATION → COMPLETE
- Log: `project_board/checkpoints/M19-ARGLB/run-2026-04-07-ap-continue.md`
- Outcome: backend path-jail hardened (`resolve()` guard + directory 404), frontend `availableClips` store wiring fixed, `uv run pytest tests/test_assets_router.py -v` → 38 passed.

## Resume: 2026-04-07 (ap-continue) — backend_fastapi_scaffold
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/backend_fastapi_scaffold.md`
- Resuming at Stage: malformed backlog stub (no WORKFLOW STATE block)
- Next Agent: Planner Agent → Acceptance Criteria Gatekeeper Agent
- Log: `project_board/checkpoints/backend_fastapi_scaffold/run-2026-04-07-ap-continue.md`

### [backend_fastapi_scaffold] — OUTCOME: COMPLETE
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/backend_fastapi_scaffold.md`
- Stage: PLANNING bootstrap → COMPLETE
- Log: `project_board/checkpoints/backend_fastapi_scaffold/run-2026-04-07-ap-continue.md`
- Outcome: Existing FastAPI scaffold validated in runtime checks; AC evidence recorded; ticket closed without additional implementation changes.

## Resume: 2026-04-07 (ap-continue) — frontend_react_scaffold_and_editor
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/frontend_react_scaffold_and_editor.md`
- Resuming at Stage: malformed backlog stub (no WORKFLOW STATE block)
- Next Agent: Planner Agent → Acceptance Criteria Gatekeeper Agent
- Log: `project_board/checkpoints/frontend_react_scaffold_and_editor/run-2026-04-07-ap-continue.md`

### [frontend_react_scaffold_and_editor] — OUTCOME: COMPLETE
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/frontend_react_scaffold_and_editor.md`
- Stage: PLANNING bootstrap → COMPLETE
- Log: `project_board/checkpoints/frontend_react_scaffold_and_editor/run-2026-04-07-ap-continue.md`
- Outcome: Existing React scaffold validated (install/build/dev startup + AC code-path mapping), then closed.

## Resume: 2026-04-07 (ap-continue) — sse_run_endpoint_and_terminal
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/sse_run_endpoint_and_terminal.md`
- Resuming at Stage: malformed backlog stub (no WORKFLOW STATE block)
- Next Agent: Planner Agent → Acceptance Criteria Gatekeeper Agent
- Log: `project_board/checkpoints/sse_run_endpoint_and_terminal/run-2026-04-07-ap-continue.md`

### [sse_run_endpoint_and_terminal] — OUTCOME: COMPLETE
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/sse_run_endpoint_and_terminal.md`
- Stage: PLANNING bootstrap → COMPLETE
- Log: `project_board/checkpoints/sse_run_endpoint_and_terminal/run-2026-04-07-ap-continue.md`
- Outcome: Existing SSE/process-manager/terminal implementation validated with endpoint runtime checks and AC code-path evidence.

## Resume: 2026-04-07 (ap-continue) — ui_polish_and_start_sh
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/ui_polish_and_start_sh.md`
- Resuming at Stage: malformed backlog stub (no WORKFLOW STATE block)
- Next Agent: Planner Agent → Acceptance Criteria Gatekeeper Agent
- Log: `project_board/checkpoints/ui_polish_and_start_sh/run-2026-04-07-ap-continue.md`

### [ui_polish_and_start_sh] — OUTCOME: COMPLETE
- Ticket: `project_board/21_milestone_21_3d_model_quick_editor/done/ui_polish_and_start_sh.md`
- Stage: PLANNING bootstrap → COMPLETE
- Log: `project_board/checkpoints/ui_polish_and_start_sh/run-2026-04-07-ap-continue.md`
- Outcome: Existing UI polish/startup implementation validated via bounded `start.sh` smoke and AC code-path evidence.
