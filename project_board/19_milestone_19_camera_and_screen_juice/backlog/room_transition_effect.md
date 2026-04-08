# TICKET: room_transition_effect

Title: Room transition effect — smooth fade or pan between rooms

## Description

Currently rooms change instantly when the player triggers a transition. Replace the instant cut with a brief fade-to-black and fade-in, or a directional pan. The effect plays during the existing `RunSceneAssembler` room swap.

## Acceptance Criteria

- Room transition is not an instant cut — a fade-to-black (0.2s out, 0.2s in) plays around the scene swap
- Player input is blocked during the transition (no movement or attack during fade)
- Transition does not affect game state — mutations, HP, and position are correct after fade-in
- Fade is implemented via a CanvasLayer ColorRect tween (not a shader)
- `RunSceneAssembler` calls a transition method rather than swapping scenes directly
- `run_tests.sh` exits 0

## Dependencies

- M6 (RunSceneAssembler must be the transition point)
