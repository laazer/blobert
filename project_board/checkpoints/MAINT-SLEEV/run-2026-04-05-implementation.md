# MAINT-SLEEV — implementation run 2026-04-05

## Done

- Added `res://scenes/levels/sandbox/test_movement_3d_legacy_enemy_visual.tscn`: duplicate of `test_movement_3d.tscn` with root `TestMovement3DLegacyEnemyVisual`; removed four `model_scene` overrides and four generated GLB `ext_resource` lines; preserved transforms, `mutation_drop`, `physics_interpolation_mode`, tree order, RespawnZone connection.
- `project.godot` `run/main_scene` unchanged.
- `timeout 300 ci/scripts/run_tests.sh` → exit 0.

## Handoff

Acceptance Criteria Gatekeeper (STATIC_QA): verify SLEEV-1..5 and ticket AC; close or route INTEGRATION per policy.
