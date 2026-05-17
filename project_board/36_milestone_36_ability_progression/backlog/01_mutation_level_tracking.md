# TICKET: 01_mutation_level_tracking

**Milestone:** M36 Ability Progression & Leveling  
**Status:** Backlog  
**Type:** Implementation

## Title

Mutation Level Tracking — per-mutation level state in inventory

## Description

Track level for each mutation in player inventory. Absorbing same mutation multiple times increases level. Level caps at 5 (or configurable). Level is serialized with run state for persistence.

## Acceptance Criteria

- [x] Inventory tracks per-mutation level (1–5)
- [x] Absorbing existing mutation increments level
- [x] Level cap enforced (default 5, exported)
- [x] Level visible in HUD (M37 integration)
- [x] Serialized in run save (M6 integration)
- [x] Deserialize correctly on load
- [x] Tests verify level increment and cap
- [x] `run_tests.sh` exits 0

## Dependencies

- M35 (mutation drops)
- M3 (inventory system)

## Implementation Notes

**Per-mutation level storage:**
```gdscript
class MutationSlot:
    var mutation_id: String
    var level: int = 1  # starts at 1
    var max_level: int = 5

func grant_mutation(mutation_id: String):
    if has_mutation(mutation_id):
        get_mutation(mutation_id).level = min(
            get_mutation(mutation_id).level + 1,
            max_level
        )
    else:
        add_new_mutation(mutation_id, level=1)
```

## Scope Notes

- Level starts at 1 when first acquired
- No level-down mechanic (monotonic increase only)

