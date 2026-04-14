# TICKET: orbital_aim_input_integration_edge_cases

Title: Orbital aim — snap vs rotation precedence, wrap, responsiveness, conflicting inputs

## Description

Integrate IJKL snap with U/O rotation so rules are unambiguous each frame: snap wins, rotation continues from the new θ, no fighting. Verify angle wrapping, same-frame responsiveness, and precedence when rotation and direction keys overlap.

## Acceptance Criteria

- **AC-6.1** IJKL snap immediately overrides current θ when snap input is active for the frame.
- **AC-6.2** After a snap, U/O rotation applies from the new θ without discontinuity beyond the intentional snap.
- **AC-6.3** Rotation never fights snap: if both classes of input apply in one frame, **snap wins** for that frame (document order in `_physics_process` / `_process`).
- **AC-10.1** Aim updates in the same frame as input processing (no extra-frame lag from deferred queues unless documented and justified).
- **AC-10.2** Rapid tapping and rapid switching between snap and rotation behave predictably (no dropped snaps, no stuck rotation state).
- **AC-11.1** Rotating past 360° wraps into \[0°, 360°) correctly.
- **AC-11.3** If direction snap and rotation occur together, **directional snap takes precedence** for that frame (aligns with AC-6.3).
- **AC-11.2** Covered in rotation ticket — this ticket re-verifies in combined scenarios (snap then U+O same frame, etc.).
- `run_tests.sh` exits 0 (integration tests for ordering and wrap).

## Dependencies

- `orbital_aim_ijkl_snap_input`
- `orbital_aim_uo_rotation_and_precision`

## Notes

- Add a short “input resolution order” comment block in code as the source of truth for frame arbitration.
