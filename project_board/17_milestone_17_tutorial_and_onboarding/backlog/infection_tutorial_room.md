# TICKET: infection_tutorial_room

Title: Infection tutorial room — guided infect → absorb with one pre-weakened enemy

## Description

Create a tutorial room that teaches the infection loop. The room contains a single pre-weakened enemy (already in WEAKENED state on spawn) and uses progressive hints to guide the player through: infect the enemy → wait for infection → absorb mutation. The room exits after a successful absorb.

## Acceptance Criteria

- `scenes/levels/rooms/intro_infection.tscn` exists and is a valid room template
- Room contains exactly one enemy, spawned in WEAKENED state
- Progressive hints guide: infect prompt appears when player is near the enemy → absorb prompt appears once enemy is INFECTED
- Room exit trigger activates after the player successfully absorbs a mutation
- If the enemy dies without being absorbed, a replacement spawns (player cannot softlock)
- Room runs between `intro_movement_room` and the first combat room in RunSceneAssembler
- `run_tests.sh` exits 0

## Dependencies

- `intro_movement_room`
- `progressive_hint_system`
- M2 (Infection Loop — infect and absorb must be working)
