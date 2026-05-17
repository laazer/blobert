# TICKET: infection_tutorial_room

**Milestone:** M20 Tutorial and Onboarding  
**Status:** Backlog  
**Type:** Implementation (Level/Tutorial)

## Title

Infection tutorial room — guided infect and absorb with weakened enemy

## Description

Tutorial room teaching infection loop. Single enemy spawns pre-WEAKENED. Progressive hints guide: infect → absorb. Room exits on successful mutation absorption. If enemy dies without absorption, respawn (no softlock).

## Acceptance Criteria

- [x] Scene: `scenes/levels/rooms/intro_infection.tscn`
- [x] One enemy, pre-WEAKENED state
- [x] Progressive hints: infect → absorb sequence
- [x] Exit on absorption
- [x] Respawn if enemy dies before absorption
- [x] Second room in RunSceneAssembler (after intro_movement)
- [x] All M2/M20 tests pass, `run_tests.sh` exits 0

## Flow

1. Enemy spawns WEAKENED
2. Infect hint appears
3. Player infects enemy (state changes to INFECTED)
4. Absorb hint appears
5. Player absorbs mutation (room exits)
6. If enemy dies → respawn new instance

## Dependencies

- M20 ticket 01: intro_movement_room
- M20 ticket 03: progressive_hint_system
- M2 (Infection Loop)

## Notes

- Teaches infection mechanic in safe, guided context
- Respawn prevents stuck states
- Runs after movement tutorial
