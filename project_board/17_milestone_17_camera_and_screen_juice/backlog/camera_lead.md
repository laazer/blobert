# TICKET: camera_lead

Title: Camera lead — camera anticipates player movement direction

## Description

Update the camera follow logic so the camera looks slightly ahead of the player in their movement direction rather than hard-following the player's position. This gives the player more visibility in the direction they're moving.

## Acceptance Criteria

- Camera target position is offset by a configurable lead amount in the player's movement direction (default: 1.5 units)
- Lead updates smoothly — no snapping when the player changes direction
- Lead amount is zero when the player is stationary
- Camera still follows the player position (lead is additive offset, not replacement)
- Lead does not cause camera to show out-of-bounds geometry (clamp if needed)
- Exported variable `lead_strength: float` controls the offset magnitude
- `run_tests.sh` exits 0

## Dependencies

- M1 (basic camera follow)
- `screen_shake_system` (build on top of the same Camera3D node)
