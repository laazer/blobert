# TICKET: spike_trap_hazard

Title: Spike trap hazard — triggered spikes with telegraph before activation

## Description

Create a triggered spike trap: spikes that are flush with the floor/wall and extend on a timer or proximity trigger. The trap shows a visual telegraph (glow, sound, or animation) before activating, giving the player time to react. Placeable in room templates.

## Acceptance Criteria

- `scenes/hazards/spike_trap.tscn` exists and is a self-contained placeable scene
- Trap has two states: retracted (safe) and extended (dangerous)
- Before extending, a visible telegraph plays for at least 0.4 seconds
- While extended, contact deals 15 damage (same as static spikes)
- Trap cycles: extended for 1.0s, retracted for 2.0s (configurable via exports)
- Retracted trap deals no damage
- Timing is configurable via exported variables
- Scene can be placed in any room template without code changes
- `run_tests.sh` exits 0

## Dependencies

- `static_spikes_hazard` (shares damage model)
