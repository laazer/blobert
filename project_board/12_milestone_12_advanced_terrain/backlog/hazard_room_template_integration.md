# TICKET: hazard_room_template_integration

Title: Integrate hazards into M6 room template system as first-class placeable elements

## Description

All 5 hazard types must plug into the M6 roguelike room template system. Room templates should be able to declare hazard types and density; the procedural room chaining system treats hazard presence as a room property, not hardcoded layout. Spawn-safe zones (player start, enemy spawns, pickup anchors) must be respected.

## Acceptance Criteria

- Each hazard scene is registered as a valid element in the room template system
- At least 2 existing room templates (combat, cooldown) include optional hazard placement slots
- Hazard slots respect spawn-safe zones — no hazard spawns on player start or enemy spawn markers
- Hazard density is configurable per room template (0 = none, 1 = sparse, 2 = dense)
- Procedurally generated runs place hazards according to room template configuration
- A combat room with tar pits and a cooldown room with no hazards both generate correctly
- `run_tests.sh` exits 0

## Dependencies

- All 5 hazard tickets (tar, lava, static spikes, spike trap, acid trap)
- M6 (Roguelike Run Structure) — room template system must be in place
