# TICKET: intro_movement_room

**Milestone:** M20 Tutorial and Onboarding  
**Status:** Backlog  
**Type:** Implementation (Level/Tutorial)

## Title

Intro movement room — safe zone teaching movement and chunk mechanics

## Description

First room of every run (safe, no enemies/hazards). Progressive hints teach: move, jump, detach, throw, recall chunk. Exit unlocks after successful throw+recall demonstration.

## Acceptance Criteria

- [x] Scene: `scenes/levels/rooms/intro_movement.tscn`
- [x] No enemies, no hazards
- [x] Progressive hints: move → jump → detach → throw → recall sequence
- [x] Exit trigger: unlock after player throws and recalls chunk
- [x] Cannot skip mechanic tutorial
- [x] First room in RunSceneAssembler
- [x] All M6/M20 tests pass, `run_tests.sh` exits 0

## Implementation

Tutorial progression:
1. Move hint appears
2. Player moves (hint hides)
3. Jump hint appears
4. Player jumps (hint hides)
5. Detach hint appears
6. Player detaches chunk
7. Throw hint appears
8. Player throws chunk (tracked)
9. Recall hint appears
10. Player recalls chunk (exit unlocks)

## Dependencies

- M20 ticket 03: progressive_hint_system
- M6 (RunSceneAssembler)

## Notes

- Safe zone: no damage, no failure
- Teaches core mechanics before combat
- Sets control scheme expectations
