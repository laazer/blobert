# Spec: wire_animations_to_generated_scenes

Ticket: `project_board/7_milestone_7_enemy_animation_wiring/in_progress/wire_animations_to_generated_scenes.md`

## WAGS-1 Functional

### WAGS-1.1 Root AnimationPlayer clips
Each generated enemy `.tscn` (12 files: 4 families × variants `00`–`02`) SHALL expose clips named `Idle`, `Walk`, `Hit`, and `Death` on the **root** `AnimationPlayer` node (direct child of the `CharacterBody3D` root named `AnimationPlayer`).

### WAGS-1.2 Library source
Clip data SHALL be copied from the first `AnimationPlayer` found under `Visual/Model` (the instantiated GLB subtree) at generation time, using `AnimationLibrary.duplicate(true)` per library name returned by `get_animation_library_list()`.

### WAGS-1.3 Track root
The root `AnimationPlayer` SHALL set `root_node` to `NodePath("../Visual/Model")` so animation tracks authored relative to the GLB root resolve correctly from the enemy root.

### WAGS-1.4 EnemyAnimationController
Each scene SHALL include an `EnemyAnimationController` direct child of the root with script `res://scripts/enemies/enemy_animation_controller.gd`.

### WAGS-1.5 Generated idle ESM (persistent)
Because `state_machine` is not serialized, each generated scene SHALL include a child of `EnemyAnimationController` named `GeneratedEnemyEsmStub` with script `res://scripts/enemies/enemy_generated_esm_stub.gd` implementing `get_state() -> String` returning `"idle"`.

### WAGS-1.6 Controller resolution
`EnemyAnimationController._ready()` SHALL, when `state_machine == null`, assign `state_machine` from `find_child("GeneratedEnemyEsmStub", true, false)` before computing `_ready_ok`.

## WAGS-2 Non-functional

### WAGS-NF1 Tests
A new suite `tests/scenes/enemies/test_enemy_scene_animation_wiring.gd` SHALL assert for all 12 paths: scene loads, root `AnimationPlayer` lists contain the four clips, `EnemyAnimationController` exists, and after the instance is added to the main `SceneTree` root, `_ready_ok` is true and `animation_player` is non-null.

### WAGS-NF2 CI
`run_tests.sh` SHALL exit 0.

## WAGS-3 Out of scope

- Replacing `setup(null)` with a serialized RefCounted (not supported without export changes).
- Changing `EnemyStateMachine` production wiring (M15).
