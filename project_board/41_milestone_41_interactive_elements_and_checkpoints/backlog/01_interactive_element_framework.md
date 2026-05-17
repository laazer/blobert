# TICKET: 01_interactive_element_framework

**Milestone:** M41 Interactive Elements & Checkpoints  
**Status:** Backlog  
**Type:** Implementation

## Title

Interactive Element Framework — base class for interactable objects (triggers, chests, switches)

## Description

Define base InteractiveElement class with standard interface: `on_interact()`, `is_interactable()`, state tracking. Supports triggers (on-sight), pickups (on-contact), and manual interactions (on-button).

## Acceptance Criteria

- [x] InteractiveElement base class with virtual `on_interact()`, `is_interactable()`
- [x] Interaction modes: trigger (on-sight), contact (on-collision), button (on-input)
- [x] State tracking: active/inactive, cooldown
- [x] Dispatch signals: `on_interacted`, `on_state_changed`
- [x] At least 3 element types implemented (checkpoint, collectible, hazard trigger)
- [x] Tests verify interaction dispatch
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (scene/level system)
- M6 (run state)

## Implementation Notes

**Base class:**
```gdscript
class_name InteractiveElement extends Area3D

func on_interact():
    pass

func is_interactable() -> bool:
    return active and not on_cooldown
```

## Scope Notes

- Simple state machine (active/inactive only)
- Cooldown prevents rapid re-interaction (configurable per element)

