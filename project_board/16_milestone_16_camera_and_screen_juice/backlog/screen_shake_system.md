# TICKET: screen_shake_system

Title: Screen shake system — configurable trauma-based camera shake

## Description

Implement a trauma-based screen shake system attached to the Camera3D. Trauma is added by game events (player hit, chunk impact, enemy death, ability use) and decays over time. Higher trauma = more shake. All shake parameters are exported and tunable.

## Acceptance Criteria

- `scripts/camera/screen_shake.gd` exists and attaches to the Camera3D node
- Trauma value (0.0–1.0) drives shake magnitude (shake = trauma²)
- Trauma decays at a configurable rate (default: 1.0 per second)
- `add_trauma(amount: float)` is callable from any game system
- Shake offsets the camera position (not rotation) along X and Y
- Max shake offset is exported (default: 0.3 units)
- Shake triggers on: player taking damage, chunk hitting an enemy, enemy dying
- No shake when trauma is 0 (no idle jitter)
- `run_tests.sh` exits 0

## Dependencies

- M1 (basic camera follow must exist)
