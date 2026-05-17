# TICKET: 02_queue_priority_and_expiry

**Milestone:** M33 Input Buffering System  
**Status:** Backlog  
**Type:** Implementation

## Title

Queue Priority & Expiry — action precedence and timeout decay

## Description

Extend action queue with priority levels and expiry timeouts. High-priority actions (jump) override low-priority (attack). Queued actions expire if not dispatched within buffer timeout window (default ~150ms).

## Acceptance Criteria

- [x] Queue supports priority: jump(3) > dash(2) > attack(1)
- [x] High-priority input inserted at head of queue, displacing lower-priority
- [x] Action expires if queued longer than `buffer_timeout` (default 0.15s, exported)
- [x] Expired action silently discarded (no alert needed)
- [x] Tests verify priority insertion and timeout expiry
- [x] `run_tests.sh` exits 0

## Dependencies

- M33:01 (action queue)

## Implementation Notes

**Priority structure:**
```gdscript
class QueuedAction:
    var action: String
    var priority: int
    var queued_at: float

func queue_action_with_priority(action: String, priority: int):
    var new_action = QueuedAction.new()
    new_action.action = action
    new_action.priority = priority
    new_action.queued_at = get_tree().get_elapsed_time()
    
    # Insert by priority
    for i in range(action_queue.size()):
        if action_queue[i].priority < priority:
            action_queue.insert(i, new_action)
            return
    action_queue.append(new_action)

func expire_old_actions():
    var now = get_tree().get_elapsed_time()
    action_queue = action_queue.filter(
        func(a): return (now - a.queued_at) < buffer_timeout
    )
```

## Scope Notes

- No priority blending (discrete levels only)
- Expiry check per frame during `_process`

