# MAINT-SLEEV — Acceptance Criteria Gatekeeper (2026-04-05)

- **Ticket:** `project_board/maintenance/done/sandbox_scene_legacy_external_enemy_visuals.md` (post-`git mv`)
- **Evidence:** `timeout 300 ci/scripts/run_tests.sh` → exit 0, `=== ALL TESTS PASSED ===`
- **AC mapping:** `tests/scenes/levels/test_legacy_enemy_visual_sandbox_scene.gd` (SLEEV-1..4.1 + ADV-SLEEV)
- **SLEEV-4.2:** `project.godot` `run/main_scene` is `res://scenes/levels/procedural_run.tscn`; not equal to `test_movement_3d.tscn`. Documented in ticket Validation Status; tests defer exact equality per ADV-PRS-19; SLEEV-4.1 (not legacy sandbox) enforced.
