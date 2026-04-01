# TICKET: intro_movement_room

Title: Intro movement room — safe room teaching movement and chunk mechanics

## Description

Create a dedicated intro room scene (no enemies, no hazards) that the player starts every run in. The room uses the progressive hint system to guide the player through: move left/right, jump, detach chunk, throw chunk, recall chunk. The room has a clear exit trigger that advances to the next room once the player has thrown and recalled the chunk at least once.

## Acceptance Criteria

- `scenes/levels/rooms/intro_movement.tscn` exists and is a valid room template
- Room contains no enemies and no hazards
- Progressive hints guide: move → jump → detach → throw → recall (in sequence)
- Room exit trigger activates after player has thrown and recalled the chunk at least once
- Player cannot skip the exit trigger until the chunk mechanic is demonstrated
- Room integrates into `RunSceneAssembler` as the first room in every run
- `run_tests.sh` exits 0

## Dependencies

- `progressive_hint_system`
- M6 (RunSceneAssembler room sequencing)
