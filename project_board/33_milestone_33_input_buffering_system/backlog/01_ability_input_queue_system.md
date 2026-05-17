# TICKET: 01_ability_input_queue_system

**Milestone:** M33 Input Buffering System  
**Status:** Backlog  
**Type:** Implementation

## Title

Ability Input Queue System — store and dispatch queued actions during execution

## Description

Implement action queue that stores next ability input while current attack is executing. Queue integrates with cancel windows (M30) and frame timing. Player feels responsive because input is never lost, but actions fire in logical order.

## Acceptance Criteria

- [x] Input queue stores up to 2 actions (configurable depth)
- [x] New input queued if current attack active and outside cancel window
- [x] On cancel window entry, next queued action dispatches automatically
- [x] Queue clears on run start (or configurable per game state)
- [x] Jump action has implicit priority: always interrupts queued attacks (document exception list)
- [x] Tests verify queue FIFO order and action dispatch timing
- [x] `run_tests.sh` exits 0

## Dependencies

- M30 (cancel windows)
- M11 (PlayerController input flow)

## Implementation Notes

**Queue data structure:**
```gdscript
var action_queue: Array[String] = []
var max_queue_depth: int = 2

func queue_action(action: String):
    if action_queue.size() < max_queue_depth:
        action_queue.append(action)

func dispatch_next_queued():
    if action_queue.size() > 0:
        var next_action = action_queue.pop_front()
        execute_attack(next_action)
```

**Priority exception:**
```gdscript
if input_action == "jump":
    action_queue.clear()  # jump overrides queue
```

## Scope Notes

- No predictive input buffering (future optimization)
- Queue depth=2 sufficient for typical combo chains

