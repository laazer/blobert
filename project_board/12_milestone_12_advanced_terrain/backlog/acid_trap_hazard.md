# TICKET: acid_trap_hazard

Title: Acid trap hazard — area denial pool with DoT, acid mutation immune

## Description

Create an acid pool hazard: a floor-level area that deals damage over time while the player stands in it. The acid mutation grants immunity. Acid pools are intended as area denial — routing the player around them unless they have the mutation. Placeable in room templates.

## Acceptance Criteria

- `scenes/hazards/acid_trap.tscn` exists and is a self-contained placeable scene
- Player takes 8 damage per second (ticking every 0.5s) while inside
- Player with active acid mutation takes no damage from acid traps
- Acid trap has a distinct visual (green/corrosive appearance) clearly different from lava
- Scene can be placed in any room template without code changes
- `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level)
