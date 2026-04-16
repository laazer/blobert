# Checkpoint Index

## Run: 2026-04-16T14-00-00Z-test-design-m25-ptp
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02_procedural_texture_presets.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/M25-PTP/run-2026-04-16T14-00-00Z-test-design.md`
- Outcome: Authored `asset_generation/python/tests/utils/test_texture_controls.py` (PTP-6, 17 test classes, all 7 slugs, all 10 keys, coercion/clamping/defaults/idempotency/ordering) and `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx` (PTP-7, all mode disable/enable rules, no-bleed-over to pupil/mouth/tail, DOM opacity assertions). All tests RED until Tasks 1-4 implement `_texture_control_defs()`, wiring, and `buildControlDisabled()` extension.

## Run: 2026-04-16T12-00-00Z-spec-m25-ptp
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02_procedural_texture_presets.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/M25-PTP/run-2026-04-16T12-00-00Z-spec.md`
- Outcome: Authored `project_board/specs/procedural_texture_presets_spec.md`; 8 requirements (PTP-1..8) covering all 10 control declarations with exact types/options/defaults/bounds, insertion position in merged list, `allowed_non_mesh` and `static_defs.extend()` wiring, coercion/validation (invalid mode→none, float clamps, hex passthrough), per-slug coverage matrix (all 7 slugs), serialization contract, frontend buildControlDisabled rules per mode group, Three.js shader overlay (material capture/restore/re-capture, gradient/spots/stripes ShaderMaterials, hex→THREE.Color conversion), non-breaking guarantee; constant inventory fully enumerated.

## Run: 2026-04-16T00-00-00Z-planner-m25-ptp
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02_procedural_texture_presets.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/M25-PTP/run-2026-04-16T00-00-00Z-planning.md`
- Outcome: Execution plan decomposed into 8 tasks (Python control defs, validation wiring, defaults/serialization, frontend conditional disabling, Three.js texture overlay, Python test suite, frontend Vitest suite, AC gate); assumptions logged on inline vs component approach, `type: "str"` for hex fields, `allowed_non_mesh` wiring, and spec completeness type.

## Run: 2026-04-15T04-00-00Z-test-break-m25-mte
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/06_mouth_and_tail_extras.md`
- Stage: TEST_BREAK
- Next Agent: Generalist Implementation Agent
- Log: `project_board/checkpoints/M25-MTE/run-2026-04-15T04-00-00Z-test-break.md`
- Outcome: Adversarially extended all three test files. 10 gaps exposed: location sign correctness (MTE-4), constant constraints (MTE-5-AC-5, MTE-6), import verification (MTE-7-AC-7), mouth_shape=None mutation guard, 6-slug baseline regression, player_slime isolation, tail_length 3.001 boundary, ordering (tail_length in float block), tail length scaling via blender_utils stub.

## Run: 2026-04-15T15:45:00Z
- Queue mode: single ticket (resume)
- Queue scope: project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/06_mouth_and_tail_extras.md
- Lean: no
- Resuming at: TEST_BREAK → Implementation
- Log root: project_board/checkpoints/

## Run: 2026-04-15T01-00-00Z-spec-m25-mte
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/06_mouth_and_tail_extras.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/M25-MTE/run-2026-04-15T01-00-00Z-spec.md`
- Outcome: Authored `project_board/specs/mouth_and_tail_extras_spec.md`; 11 requirements (MTE-1..11) covering control declarations, coercion/validation, per-slug defaults, geometry placement formulas, `create_mouth_mesh`/`create_tail_mesh` signatures, per-slug wiring (all 6 animated slugs geometry-wired), non-breaking guarantee, serialization contract, frontend disabling, types freeze; constant inventory and slug coverage matrix fully enumerated.

## Run: 2026-04-15T15:13:53Z
- Queue mode: single ticket
- Queue scope: project_board/25_milestone_25_enemy_editor_visual_expression/backlog/06_mouth_and_tail_extras.md
- Lean: no
- Log root: project_board/checkpoints/

### [01_eye_shape_and_pupil_system] — OUTCOME: COMPLETE
Python controls + geometry builders already in e4b3f85; 1-line frontend buildControlDisabled fix cleared 28 test failures; 2 stale empty-state assertions fixed. 1219 Python + 313 frontend tests green; diff-cover 92%.
Log: project_board/checkpoints/M25-ESPS/

## Run: 2026-04-14T21-00-00Z-test-break-m25-esps
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/backlog/01_eye_shape_and_pupil_system.md`
- Stage: TEST_BREAK → IMPLEMENTATION_GENERALIST
- Next Agent: Engine Integration Agent
- Log: `project_board/checkpoints/M25-ESPS/run-2026-04-14T21-00-00Z-test-break.md`
- Outcome: Adversarial Python controls suite (`test_eye_shape_pupil_controls_adversarial.py`): mutation guard, idempotency, dynamic slug coverage, None/whitespace coercion, no server-side pupil_shape suppression, fresh-list-per-call guard, combinatorial boundary. Adversarial Python geometry suite (`test_eye_shape_pupil_geometry_adversarial.py`): shared-mutable-state guard, stress eye_count=99, triangle fallback → sphere not box, pupil location differs from eye location, non-uniform oval/slit scale, pupil primitive dispatch exclusivity, claw_crawler max-peripheral boundary, determinism. Adversarial frontend suite (`BuildControls.eyeShape.adversarial.test.tsx`): reactive toggle false→true, toggle round-trip, unknown key isolation, claw_crawler slug-agnostic rule, integer 0/1 falsy/truthy coercion, no bleed-over to other controls. Ticket advanced to IMPLEMENTATION_GENERALIST; note appended that this is a Python/frontend ticket routed under generalist path.

## Run: 2026-04-14T20-00-00Z-test-design-m25-esps
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/backlog/01_eye_shape_and_pupil_system.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/M25-ESPS/run-2026-04-14T20-00-00Z-test-design.md`
- Outcome: Wrote 3 test files covering ESPS-1..8: `tests/utils/test_eye_shape_pupil_controls.py` (controls, coercion, serialization, defaults, controls-only slugs), `tests/enemies/test_eye_shape_pupil_geometry.py` (eye shape and pupil geometry dispatch via patched blender_utils), `src/components/Preview/BuildControls.eyeShape.test.tsx` (conditional disabling DOM behavior). All tests RED until implementation.

## Run: 2026-04-14T19-00-00Z-spec-m25-esps
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/backlog/01_eye_shape_and_pupil_system.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/M25-ESPS/run-2026-04-14T19-00-00Z-spec.md`
- Outcome: Spec authored at `project_board/specs/eye_shape_and_pupil_system_spec.md`; 9 requirements (ESPS-1..9) covering control declarations, coercion, eye shape geometry, pupil mesh, serialization, per-slug defaults, controls-only slugs, frontend disabling, types freeze; constant inventory and slug coverage matrix fully enumerated.

## Run: 2026-04-14T18-00-00Z-planner-m25-01
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/backlog/01_eye_shape_and_pupil_system.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/M25-ESPS/run-2026-04-14T18-00-00Z-planning.md`
- Outcome: Decomposed eye shape + pupil system into 7 tasks (Python controls, Python geometry builder, serialization/validation, frontend controls, frontend conditional disabling, Python tests, frontend tests); assumptions logged on enemy scope, geometry approach, pupil mesh strategy.

## Run: 2026-04-14-procedural-enemy-attack-test-design
- Ticket: `project_board/10_milestone_10_procedural_enemies_in_level/in_progress/03_procedural_enemy_attack_loop_runtime.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/03-procedural-enemy-attack-loop-runtime/run-2026-04-14T17-05-00Z-test-design.md`
- Outcome: Added `tests/system/test_procedural_enemy_attack_loop_runtime_contract.gd` (PEAR-T-01..16); Godot suite reports 11 new failing assertions until `EnemyInfection3D` host + M8 wiring land for procedural spawns.

## Run: 2026-04-11-pipeline-18-19-complete
- Tickets: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/18_registry_subtabs_by_pipeline_cmd.md`, `.../done/19_model_viewer_fullscreen_button.md`
- Stage: STATIC_QA → COMPLETE (AC Gatekeeper)
- Outcome: Vitest adversarial tests + `npm run build`; tickets moved to milestone `done/`.

## Resume: 2026-04-11T21-00-00Z-ap-continue
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md` (from spec `@enemy_body_part_extras_spec.md`)
- Resuming at Stage: `TEST_BREAK`
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`

### [extras-shell-visible-spikes-on-top] — OUTCOME: COMPLETE
Visible shell via `create_sphere` + `shell_scale`; spike tip factor 1.0; 55 focused pytest + full `run_tests.sh` green; spec updated for shell/spike semantics.
Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`

## Run: 2026-04-14T-eye-shape-pupil-system
- Queue mode: single ticket
- Queue scope: project_board/25_milestone_25_enemy_editor_visual_expression/backlog/01_eye_shape_and_pupil_system.md
- Lean: no
- Log root: project_board/checkpoints/

This file is intentionally small and acts as an index only.
Full checkpoint bodies live under `project_board/checkpoints/`.

## Index-only rules (agents must follow)

- **Do not** append checkpoint decision bodies here: no `**Would have asked:**`, no `**Assumption made:**`, no multi-paragraph assumptions.
- **Do** write those only under `project_board/checkpoints/<ticket-id>/<run-id>.md`.
- **Do** keep entries here short: run/resume headers, ticket path, stage, `Log:` path, and optional one-line outcome summaries.

## Migration

- Monolithic log frozen on 2026-03-30:
  - `project_board/checkpoints/frozen/CHECKPOINTS-2026-03-30-frozen.md`
