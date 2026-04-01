# TICKET: static_spikes_hazard

Title: Static spikes hazard — instant damage on contact

## Description

Create static spike geometry: wall or floor spikes that deal instant damage on contact. Unlike tar and lava, spikes are a one-time hit per contact (player must leave and re-enter to be hit again). Placeable in room templates.

## Acceptance Criteria

- `scenes/hazards/static_spikes.tscn` exists and is a self-contained placeable scene
- Player takes 15 damage on first contact with spike Area3D
- After contact, a 0.5s immunity window prevents repeat damage (avoids damage spam on slow movement)
- Spikes have a clear visual (sharp geometry or sprite, visibly dangerous)
- Can be placed on floor or walls
- Scene can be placed in any room template without code changes
- `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level)
