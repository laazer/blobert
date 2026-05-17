# TICKET: 02_checkpoint_system

**Milestone:** M41 Interactive Elements & Checkpoints  
**Status:** Backlog  
**Type:** Implementation

## Title

Checkpoint System — save spawn point and run progress on touch

## Description

Checkpoint element that saves player position and current run state when touched. On death, player respawns at last checkpoint instead of run start. Respawn resets enemies but preserves mutations.

## Acceptance Criteria

- [x] Checkpoint inherits InteractiveElement
- [x] On player contact, save position, mutation state, room progress
- [x] On player death, load last checkpoint (position + mutations)
- [x] Enemies respawn (no carryover)
- [x] Visual feedback: checkpoint activation (glow, animation optional)
- [x] Save/load via RunState
- [x] Tests verify checkpoint save and load
- [x] `run_tests.sh` exits 0

## Dependencies

- M41:01 (interactive element base)
- M6 (run state save/load)

## Implementation Notes

**Checkpoint save:**
```gdscript
func on_interact():
    run_state.checkpoint_position = global_position
    run_state.checkpoint_mutations = player.get_current_mutations()
    on_checkpoint_activated.emit()

func player_died():
    player.global_position = run_state.checkpoint_position
    player.restore_mutations(run_state.checkpoint_mutations)
```

## Scope Notes

- One active checkpoint per room (last touched wins)
- Enemies reset on respawn (no enemy state carryover)

