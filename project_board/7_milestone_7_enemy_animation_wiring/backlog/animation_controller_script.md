# TICKET: animation_controller_script

Title: Implement shared enemy animation controller script

## Description

Create `scripts/enemies/enemy_animation_controller.gd` that reads the current EnemyStateMachine state each frame and plays the matching animation clip on the enemy's AnimationPlayer. The controller must handle state transitions without animation pop (crossfade where applicable).

States to animation mapping:
- NORMAL + not moving → `Idle`
- NORMAL + moving → `Walk`
- WEAKENED → `Idle` (slower playback speed)
- INFECTED → `Idle` (frozen or minimal)
- On hit received → `Hit` (one-shot, then return to state clip)
- On death → `Death` (one-shot, no loop, holds last frame)

## Acceptance Criteria

- Script exists at `scripts/enemies/enemy_animation_controller.gd`
- Attaches to generated enemy scenes as a child node of the enemy root
- Plays `Idle` when enemy is stationary in NORMAL state
- Plays `Walk` when enemy is moving
- Plays `Hit` as a one-shot on damage received, then resumes state clip
- Plays `Death` on death; holds last frame; no loop
- WEAKENED state plays `Idle` at 0.5× speed
- No animation pop on state transition (use `AnimationPlayer.play` with blend time ≥ 0.1s)
- `run_tests.sh` exits 0

## Dependencies

- `blender_animation_export` — animation clips must exist in GLBs
- EnemyStateMachine must expose current state readably
