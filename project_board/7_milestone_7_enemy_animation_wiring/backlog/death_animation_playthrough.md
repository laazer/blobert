# TICKET: death_animation_playthrough

Title: Death animation plays through before enemy despawn

## Description

When an enemy reaches the dead state, the Death animation plays fully before the node is freed. The enemy must not disappear mid-animation. After the animation completes, the node is removed cleanly.

## Acceptance Criteria

- Enemy plays `Death` clip to completion before `queue_free()` is called
- No physics interaction occurs during death animation (disable collision on death)
- Enemy cannot be targeted or infected during death animation
- If the scene is unloaded while death animation is playing, no crash or error
- Works for all 4 enemy families
- `run_tests.sh` exits 0

## Dependencies

- `wire_animations_to_generated_scenes`
- EnemyStateMachine must have a DEAD state or equivalent transition hook
