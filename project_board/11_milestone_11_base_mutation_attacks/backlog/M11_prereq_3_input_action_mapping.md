# TICKET: M11_prereq_3_input_action_mapping

**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Status:** Ready  
**Type:** Spec

## Title

Define input action mapping for M11+ attack system

## Description

Centralize and document all input actions used by M11+ (base attacks, fused attacks, future features). Create a spec that lists:
- All action names (move_left, move_right, jump, attack, absorb, mutate, swap_mutation, menu)
- Which input states permit which actions
- Default key bindings (configurable, but with defaults)
- Input consumption semantics (e.g., "attack" input doesn't also trigger "absorb")

This spec is the source of truth for input handling across M11 and M12.

## Acceptance Criteria

- [x] Input action mapping spec written (`project_board/specs/input_action_mapping_spec.md` or embedded in this ticket)
- [x] All input actions enumerated with descriptions
- [x] State-action matrix: which states permit which inputs
  - Example: IDLE/WALK/JUMP/FALL permit "attack", but HURT/DEAD do not
- [x] Default key bindings defined (can be overridden in settings)
- [x] Input consumption rules documented (no input can trigger multiple conflicting actions)
- [x] Spec references player state machine (from prereq 1)

## Dependencies

- M11_prereq_1_player_state_machine (spec must reference states)

## Example: State-Action Matrix

| State | move_left | move_right | jump | attack | absorb | menu |
|-------|-----------|------------|------|--------|--------|------|
| IDLE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WALK | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| JUMP | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ |
| FALL | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| WALL_CLING | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| ABSORB | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| HURT | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| DEAD | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

## Notes

- This is a spec-only ticket; no code changes in PlayerController yet
- Default bindings should match current M1 (check existing input map)
- M11 core tickets will implement the state-action gating logic
