# TICKET: 04_trigger_conditions_and_events

**Milestone:** M41 Interactive Elements & Checkpoints  
**Status:** Backlog  
**Type:** Implementation

## Title

Trigger Conditions & Events — conditional interaction dispatch

## Description

Extend InteractiveElement with conditional triggers: activate only when player has specific mutation, has killed N enemies, etc. Dispatch custom events on condition met.

## Acceptance Criteria

- [x] TriggerCondition interface: `is_satisfied() -> bool`
- [x] Condition types: has_mutation, enemy_count, time_elapsed
- [x] Elements can have multiple conditions (AND logic)
- [x] Custom event emitted on condition satisfied
- [x] Event can trigger other elements (chain reactions)
- [x] Tests verify condition evaluation and chaining
- [x] `run_tests.sh` exits 0

## Dependencies

- M41:01 (interactive element base)

## Implementation Notes

**Condition structure:**
```gdscript
class_name TriggerCondition extends Resource

class MutationCondition extends TriggerCondition:
    @export var required_mutation: String
    
    func is_satisfied() -> bool:
        return player.has_mutation(required_mutation)

func all_conditions_met(conditions: Array[TriggerCondition]) -> bool:
    for condition in conditions:
        if not condition.is_satisfied():
            return false
    return true
```

## Scope Notes

- AND logic only (no OR in base)
- Conditions evaluated once per frame (caching OK)

