# Checkpoint Index

## Run: 2026-04-19T01-00-00Z-test-design-m25-04
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/04_part_rotation_controls.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/M25-04/run-2026-04-19T01-00-00Z-test-design.md`
- Outcome: Authored `asset_generation/python/tests/utils/test_part_rotation_controls.py`; 46 tests covering PRC-1..PRC-5, PRC-7, PRC-10; all 46 RED, 1766 pre-existing tests green; 3 checkpoint assumptions logged (ensure_blender_stubs pattern, _defaults_for_slug scope, parametrize coverage).

## Run: 2026-04-19T00-00-00Z-spec-m25-04
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/04_part_rotation_controls.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/M25-04/run-2026-04-19T00-00-00Z-spec.md`
- Outcome: Authored `project_board/specs/part_rotation_controls_spec.md`; 10 requirements (PRC-1..10) covering module-level constants and `_rig_rotation_control_defs()` (exact key names, types, bounds, step, defaults), insertion position in `animated_build_controls_for_api()` (conditional on ENEMY_CLASSES, after static_float, before mesh floats), `_defaults_for_slug()` wiring, `allowed_non_mesh` wiring, coerce/validate extend pattern (NaN→default, inf→clamp), Blender rotation application (`Euler((rx,ry,rz),'XYZ')` per slug), slug coverage matrix (all 6 animated enemies; player_slime excluded), Python test file spec, frontend comment-only verification, non-breaking guarantee; serialization contract and 4 checkpoint assumptions logged.

## Run: 2026-04-16T00-00-00Z-planning-m25-04
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/04_part_rotation_controls.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/M25-04/run-2026-04-16T00-00-00Z-planning.md`
- Outcome: Execution plan decomposed into 7 tasks (Python control defs, validation wiring, Blender rotation application per-slug, defaults/serialization, Python test suite, frontend verification note, AC gate); 5 assumptions logged on slug coverage, control def placement strategy, Blender rotation API, options_for_enemy wiring, and spec completeness type.

## Run: 2026-04-18T00-00-00Z-autopilot-single-m25-04
- Queue mode: single ticket
- Queue scope: `project_board/25_milestone_25_enemy_editor_visual_expression/backlog/04_part_rotation_controls.md`
- Lean: no
- Log root: `project_board/checkpoints/M25-04/`
- Stage: `PLANNING`
- Log: `project_board/checkpoints/M25-04/run-2026-04-18T00-00-00Z-autopilot.md`
- Note: M25-03 is BLOCKED on AC5 (manual visual smoke test); M25-04 proceeds per human instruction

## Run: 2026-04-16T20-00-00Z-test-break-m25-03
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/03_texture_upload_support.md`
- Stage: TEST_BREAK → IMPLEMENTATION_WEB
- Next Agent: Generalist Implementation Agent
- Log: `project_board/checkpoints/M25-03/run-2026-04-16T20-00-00Z-test-break.md`
- Outcome: Authored `asset_generation/web/frontend/src/components/Preview/BuildControls.textureUpload.adversarial.test.tsx`; 12 gap groups (GAP-1..12), 30+ adversarial test cases covering: image/jpg non-standard MIME rejection, Remove button type="button" attribute (TUS-7), reactive custom→none→custom mode-switch without remount (file input re-mounts, stale error state cleared), multiple-file FileList (only first processed), upload-while-in-error-state store verification, URL.createObjectURL throwing defensiveness (with CHECKPOINT annotations), empty filename MIME bypass attempt, zero-byte file acceptance (boundary 0<=2097152), 2097152-byte store-state verification, spy isolation, image/webp+bmp+svg+xml rejection, empty MIME type string rejection.

## Run: 2026-04-16T18-00-00Z-test-design-m25-03
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/03_texture_upload_support.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/M25-03/run-2026-04-16T18-00-00Z-test-design.md`
- Outcome: Authored `asset_generation/web/frontend/src/components/Preview/BuildControls.textureUpload.test.tsx`; covers TUS-1..TUS-9: "custom" option in selector, file input render conditions/accept/aria-label, MIME rejection (gif/pdf/bmp), size rejection (3 MB, 2097153-byte boundary), exact-boundary acceptance (2097152 bytes), valid PNG/JPEG acceptance, error cleared on valid re-upload, Remove button render conditions and click behavior (revokeObjectURL + null store + mode reset), prev-URL revocation ordering, buildControlDisabled sub-controls disabled under "custom", no bleed-over to pupil/mouth rules, empty-file edge case. Tests RED until Tasks 2–3 implemented.

## Run: 2026-04-16T15-00-00Z-spec-m25-03
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/03_texture_upload_support.md`
- Stage: SPECIFICATION → TEST_DESIGN
- Next Agent: Test Designer Agent
- Log: `project_board/checkpoints/M25-03/run-2026-04-16T15-00-00Z-spec.md`
- Outcome: Authored `project_board/specs/texture_upload_support_spec.md`; 10 requirements (TUS-1..10) covering "custom" option injection (client-side only, Python unchanged), file input UI (accept/.png/.jpg/.jpeg, aria-label="Upload texture"), validation rules (image/png|image/jpeg, 2097152 byte ceiling, exact error strings), blob URL lifecycle (BuildControls creates/revokes; GlbViewer disposes Texture only), Zustand store slice (customTextureUrl + setCustomTextureUrl), GlbViewer TextureLoader overlay (MeshStandardMaterial only, needsUpdate, customTextureRef, array-material handling, async-safety guard, "custom" as no-op in shader effect), Remove button (dual render condition, revoke+null+reset-to-none), Python comment (3-line exact text inside _texture_control_defs()), buildControlDisabled confirmation (sub-controls remain disabled under "custom"), non-breaking guarantee; 8 AC test coverage items for BuildControls.textureUpload.test.tsx enumerated; cross-requirement interaction table included.

## Run: 2026-04-17T00-00-00Z-autopilot-single-m25-03
- Queue mode: single ticket
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/03_texture_upload_support.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/M25-03/run-2026-04-17T00-00-00Z-autopilot.md`
- Outcome: Execution plan decomposed into 7 tasks (Python comment addition, Zustand store slice, BuildControls file input + validation + blob URL lifecycle, GlbViewer TextureLoader overlay + cleanup, Python tests n/a, frontend Vitest test suite, AC gate); 4 assumptions logged on URL storage ownership, Python doc style, spec type, and blob URL revocation boundary.

## Run: 2026-04-16T14-00-00Z-test-design-m25-ptp
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02_procedural_texture_presets.md`
- Stage: TEST_DESIGN → TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/M25-PTP/run-2026-04-16T14-00-00Z-test-design.md`
- Outcome: Authored `asset_generation/python/tests/utils/test_texture_controls.py` (PTP-6, 17 test classes, all 7 slugs, all 10 keys, coercion/clamping/defaults/idempotency/ordering) and `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx` (PTP-7, all mode disable/enable rules, no-bleed-over to pupil/mouth/tail, DOM opacity assertions). All tests RED until Tasks 1-4 implement `_texture_control_defs()`, wiring, and `buildControlDisabled()` extension.

## Resume: 2026-04-16T16-00-00Z-ap-continue
- Ticket: `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02_procedural_texture_presets.md`
- Resuming at Stage: TEST_BREAK
- Next Agent: Test Breaker Agent
- Log: `project_board/checkpoints/M25-PTP/run-2026-04-16T16-00-00Z-test-break.md`
- Outcome: Extended Python + frontend texture preset tests with adversarial coercion (None/whitespace/NaN/±inf, numeric strings), input-mutation guards, invalid `texture_mode` handling, and reactive store-update assertions. Tests remain RED pending implementation of Tasks 1–4.

### [M25-02] — OUTCOME: COMPLETE
Procedural texture presets (gradient/spots/stripes) implemented across all animated enemy slugs; real-time Three.js shader overlay; 10 control defs serialized to enemy config JSON; all tests passing.
Log: `project_board/checkpoints/M25-02/run-2026-04-15T12-00-00Z-autopilot.md`

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
