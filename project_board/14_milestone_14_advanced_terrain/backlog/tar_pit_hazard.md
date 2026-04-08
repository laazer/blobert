# TICKET: tar_pit_hazard

Title: Tar pit hazard — slows movement, adhesion mutation immune

## Description

Create a tar pit scene: a floor-level area that slows the player's movement speed while standing in it. The adhesion mutation grants immunity (full speed in tar). Tar pits are placeable in room templates as a scene instance.

## Acceptance Criteria

- `scenes/hazards/tar_pit.tscn` exists and is a self-contained placeable scene
- Player movement speed reduced to 40% while inside tar pit Area3D
- Speed reduction removes cleanly on exit (no lingering slow)
- Player with active adhesion mutation is unaffected (full speed in tar)
- Enemies are also slowed by tar pits (same 40% reduction)
- Tar pit has a distinct visual (dark/sticky material or shader)
- Scene can be placed in any room template without code changes
- `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — collision and physics baseline
