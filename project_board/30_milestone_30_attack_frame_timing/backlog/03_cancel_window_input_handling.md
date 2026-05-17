# TICKET: 03_cancel_window_input_handling

**Milestone:** M30 Attack Frame Timing  
**Status:** Backlog  
**Type:** Implementation

## Title

Cancel Window Input Handling — input acceptance during attack frames

## Description

Implement cancel window detection so player input (attack, jump, dash) is accepted only during frames specified in `AttackResource.cancel_window_start` and `cancel_window_end`. Outside this window, input is ignored or queued (M33 handles queuing). This enables responsive combo flow and prevents input feeling sluggish.

## Acceptance Criteria

- [x] PlayerController reads cancel windows from active attack
- [x] Input during cancel window is accepted and executes next action
- [x] Input outside cancel window is logged as "bufferable" (for M33) or dropped per design
- [x] Cancel window is optional; attacks without defined windows use default (e.g., full endlag window)
- [x] Multiple simultaneous inputs during cancel window: last input wins (or implement priority per project convention)
- [x] Tests verify input acceptance at frame boundaries
- [x] `run_tests.sh` exits 0

## Dependencies

- M30:02 (frame event emission)
- M11 (PlayerController input flow)

## Implementation Notes

**Decision: input handling precedence**
- If multiple actions queued during cancel window, choose by priority: jump > attack > dash (or document actual priority used)

**GDScript pseudocode:**
```gdscript
func can_accept_input() -> bool:
    if not active_attack:
        return true
    
    var in_cancel_window = (frame_counter >= active_attack.cancel_window_start and 
                           frame_counter <= active_attack.cancel_window_end)
    return in_cancel_window

func handle_attack_input(action: String):
    if can_accept_input():
        execute_attack(action)
    else:
        # Buffer for M33
        input_buffer.append(action)
```

## Scope Notes

- No animation blending required (M32+ handles variants)
- No prediction/input lag compensation (future optimization)

