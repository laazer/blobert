# TICKET: orbital_aim_ijkl_snap_input

Title: Orbital aim — IJKL cardinal snap, dual-key diagonals, simultaneous window, multi-key policy

## Description

Implement primary keyboard aim: IJKL snap to cardinal angles, dual-key combinations for 45° diagonals, a short time window for “simultaneous” dual presses, continuous resolution while keys are held, and a single consistent rule when three or more direction keys are active.

## Acceptance Criteria

- **AC-3.1** Single key sets θ instantly:
  - I → 90° (Up)
  - L → 0° (Right)
  - K → 270° (Down)
  - J → 180° (Left)
- **AC-3.2** Simultaneous pair snaps:
  - I + L → 45°
  - I + J → 135°
  - K + J → 225°
  - K + L → 315°
- **AC-3.3** Dual-key detection window: two key-down events within ≤ ~50 ms count as simultaneous (value exported/tunable; default ~50 ms).
- **AC-3.4** While dual keys are held, θ continuously resolves to the correct combined direction (no stale single-cardinal lock).
- **AC-3.5** If 3+ directional keys are pressed: choose and document one policy — last-input priority **or** clamp to nearest valid direction — and apply it consistently every frame.
- **AC-12.6** Dual-key detection window is exported/tunable.
- **AC-10.1 / AC-10.2 (partial)** Snap updates θ in the same frame as qualifying input; rapid key changes remain stable (no stuck diagonal state after release).
- `run_tests.sh` exits 0 (automate window + cardinal/diagonal expectations where feasible).

## Dependencies

- `orbital_aim_core_representation` — θ storage and normalization

## Notes

- Map keys via Godot input map or project convention; document actual action names in the ticket body when implemented.
