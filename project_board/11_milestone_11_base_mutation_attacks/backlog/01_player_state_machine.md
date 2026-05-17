# TICKET: 01_player_state_machine

**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Status:** Ready  
**Type:** Refactor (M1 code)

## Title

Refactor PlayerController3D: Extract implicit state management into explicit RefCounted state machine

## Description

M1's PlayerController3D manages state implicitly (jump vs. walk vs. fall detected through velocity checks). M11 needs explicit state transitions to gate attack input correctly (can't attack while HURT, can attack while FALLING, etc.).

Extract implicit states (IDLE, WALK, JUMP, FALL, WALL_CLING, HURT, DEAD, and any others) into a RefCounted FSM with:
- Enum listing all states
- `transition(new_state)` method with guard logic
- `can_transition_to(new_state)` to enforce rules
- `state_timer` tracking time in current state (for minimum action durations)

This is a non-breaking refactor: gameplay behavior unchanged, just codified as a state machine.

## Acceptance Criteria

- [x] RefCounted state machine class created (`scripts/player/player_state_machine.gd`)
- [x] All player states enumerated (IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING, ABSORB, MUTATE, HURT, DEAD)
- [x] Transition rules enforced (e.g., can't go DEAD → any state)
- [x] PlayerController3D uses state machine for all state checks
- [x] State timer incremented each frame and reset on transition
- [x] All M1 tests still pass (no behavior change)
- [x] `run_tests.sh` exits 0

## Dependencies

- M1 (completed, but code will be modified)

## Notes

- Do not add attack-specific states yet (CHARGE_UP, ABILITY_USE) — M11 core will add those
- State transitions can be logged for debugging, but not required
- Minimum action durations (e.g., 0.05s before FLOAT from JUMP) should use `state_timer` checks
