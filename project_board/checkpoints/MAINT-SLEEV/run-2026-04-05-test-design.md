# MAINT-SLEEV — Test Designer run 2026-04-05

**Ticket:** `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`  
**Spec:** `project_board/specs/sandbox_scene_legacy_external_enemy_visuals_spec.md`  
**Stage handoff:** TEST_DESIGN → TEST_BREAK  

## Summary

- Added `tests/scenes/levels/test_legacy_enemy_visual_sandbox_scene.gd` mapping **SLEEV-1** (file exists + packed load + `Node3D` root), **SLEEV-2** (root name ≠ `TestMovement3D`, top-level child names/order vs source, `Floor.collision_mask == 3`), **SLEEV-3** (four enemies: `EnemyInfection3D`, `physics_interpolation_mode`, `mutation_drop`, translation parity, `model_scene == null`; `.tscn` text has none of the four forbidden `generated_glb/*_animated_00.glb` paths; no `model_scene =` line; no `.glb` in any `[ext_resource]` line), **SLEEV-4.1** (`run/main_scene` must not reference `test_movement_3d_legacy_enemy_visual`).
- `run_all` gates on **SLEEV-1.1** once so a missing duplicate scene yields **one** failing assertion until Implementation adds `test_movement_3d_legacy_enemy_visual.tscn`.

## Evidence

- `timeout 120 godot --headless --path . -s tests/run_tests.gd` → `FAIL: SLEEV-1.1_file_exists` (expected pre-implementation); `=== FAILURES: 1 test(s) failed ===`.

## Spec gaps / assumptions (for Spec / Planner)

- **SLEEV-4.2 vs repo:** Spec/ticket text calls for `run/main_scene` == `test_movement_3d.tscn`; current `project.godot` uses `procedural_run.tscn` per **ADV-PRS-19**. Automated test asserts only **SLEEV-4.1** (main scene is not the legacy duplicate). Planner/gatekeeper should reconcile SLEEV-4.2 with M6 entry policy if needed.

## Would have asked

- None (spec names paths and tables explicitly).

## Assumption made

- “No GLB `ext_resource`” on the level file is enforced as: no `[ext_resource]` line containing `.glb` (stricter than SLEEV-3.1’s four paths alone; matches ticket devlog intent).

## Confidence

High for SLEEV-1–3 and SLEEV-4.1; SLEEV-4.2 full string equality intentionally not asserted against `project.godot` to avoid contradicting ADV-PRS-19.
