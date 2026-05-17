# TICKET: 03_cancel_window_queue_dispatch

**Milestone:** M33 Input Buffering System  
**Status:** Backlog  
**Type:** Implementation

## Title

Cancel Window Queue Dispatch — automatic action dispatch at cancel window

## Description

Integrate action queue with cancel window frame events (M30). When cancel window opens, automatically dispatch next queued action if one exists. No manual input required during cancel window.

## Acceptance Criteria

- [x] On `on_cancel_window_open` signal, dequeue and dispatch highest-priority action
- [x] Dequeued action executes with fresh frame counter (no frame bleed-through)
- [x] Queue priority respected during dispatch (highest priority executes)
- [x] If queue empty at cancel window, nothing happens (no stall)
- [x] Manual input during cancel window still works (overrides queue if higher priority)
- [x] Tests verify dispatch timing and action ordering
- [x] `run_tests.sh` exits 0

## Dependencies

- M30:02 (frame event emission)
- M33:01–02 (action queue with priority)

## Implementation Notes

**Cancel window signal handler:**
```gdscript
func _on_cancel_window_open():
    expire_old_actions()
    if action_queue.size() > 0:
        var queued = action_queue.pop_front()
        execute_attack(queued.action)
```

## Scope Notes

- Cancel window is automatic (no player choice needed)
- Manual input during window may override queue (if higher priority) — document behavior

