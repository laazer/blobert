# TICKET: M11_attack_1_verify_cooldown_behavior

**Milestone:** M11 Base Mutation Attacks  
**Status:** Backlog  
**Type:** Verification

## Title

Verify cooldown behavior across player state transitions

## Description

After M11 core tickets are implemented, verify that cooldown tracking behaves correctly across all player state transitions:
- Cooldown continues to decrement during all movement states (IDLE, WALK, JUMP, FALL, WALL_CLING)
- Cooldown pauses or continues appropriately during HURT state (design choice)
- Cooldown resets on death (DEAD state)
- Attack becomes available exactly when cooldown reaches 0
- Rapid input does not trigger multiple attacks during cooldown

Test with multiple mutations to ensure per-mutation cooldown tracking is independent.

## Acceptance Criteria

- [x] Manual test: Execute attack, wait for cooldown, verify attack available
- [x] Manual test: Execute attack, transition through different states, verify cooldown continues
- [x] Manual test: Switch active mutations mid-cooldown, verify each mutation has independent cooldown
- [x] Manual test: Take damage (HURT state), verify cooldown behavior is consistent
- [x] Manual test: Die and respawn, verify cooldown resets

## Dependencies

- M11_prereq_1_player_state_machine (states)
- M11_core_1_attack_resource (attack data)
- M11_core_2_attack_executor_handlers (execution)
- M11_core_3_attack_database_integration (integration + cooldown tracking)

## Notes

- This is a manual verification ticket to catch edge cases not covered by unit tests
- Run after M11 core tickets are in_progress or completed
- Results document expected cooldown behavior for future attack additions

