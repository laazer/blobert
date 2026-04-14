# TICKET: orbital_aim_uo_rotation_and_precision

Title: Orbital aim — U/O rotation (tap vs hold), acceleration curve, speed limits, Shift precision

## Description

Add secondary rotation on U (counter-clockwise) and O (clockwise): discrete step on quick tap, continuous rotation on hold with time-based acceleration segments, minimum and maximum angular speed, and a precision modifier (default Shift) that scales tap step and hold ramp.

## Acceptance Criteria

- **AC-4.1** U rotates θ counter-clockwise; O rotates θ clockwise (consistent with θ increasing direction used in AC-3 mapping).
- **AC-4.2 (Tap)** Short press applies a fixed angle step per tap (exported; suggested range 2–5° default documented in inspector).
- **AC-4.3 (Hold)** Holding applies continuous rotation over time.
- **AC-4.4** While holding, rotation speed ramps with an exported curve or piecewise timing, e.g. 0–150 ms slow, 150–400 ms medium, 400 ms+ fast, with a hard cap.
- **AC-4.5** Rotation has exported minimum speed (responsiveness floor) and maximum cap.
- **AC-5.1** Holding precision modifier reduces effective rotation speed (tap and hold paths).
- **AC-5.2** Precision mode reduces tap step size and slows hold acceleration ramp (both exported multipliers or separate curves).
- **AC-11.2** U + O together: net rotation is zero for the frame (cancel).
- **AC-12.1** Tap angle step exported.
- **AC-12.2** Rotation acceleration curve / segment timings exported.
- **AC-12.3** Max rotation speed (and min if distinct) exported.
- **AC-12.4** Precision modifier multipliers exported.
- **AC-9.5 (partial)** Hold rotation interpolates smoothly at run time — no visible jitter from conflicting micro-updates (full visual pass may land in visual ticket).
- `run_tests.sh` exits 0.

## Dependencies

- `orbital_aim_core_representation`

## Notes

- Tap vs hold detection should use exported time thresholds; document them beside AC-4.2 defaults.
