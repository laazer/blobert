# TICKET: wire_animations_to_generated_scenes

Title: Wire AnimationController to all 12 generated enemy scenes

## Description

Update `scripts/asset_generation/generate_enemy_scenes.gd` (or re-run it) so that each generated `.tscn` file includes an `EnemyAnimationController` child node. Verify all 12 scenes (4 families × 3 variants) load correctly and that the controller finds the AnimationPlayer at runtime.

## Acceptance Criteria

- All 12 generated `.tscn` files contain an `EnemyAnimationController` node
- Each controller correctly resolves the AnimationPlayer sibling at `_ready()`
- Placing any generated enemy in `test_movement_3d.tscn` shows idle animation playing in-editor (not a T-pose)
- No null reference errors in output log when scene loads
- `run_tests.sh` exits 0

## Dependencies

- `animation_controller_script`
- `blender_animation_export`
- `generate_enemy_scenes.gd` (M5, done)
