# TICKET: 01_room_composition_dsl

**Milestone:** M40 Procedural Level Composition  
**Status:** Backlog  
**Type:** Implementation

## Title

Room Composition DSL — declarative rules for room layout and entities

## Description

Define a domain-specific language or rule-based system that describes room composition: platform patterns, enemy placements, hazard zones. Rules parameterized by difficulty level. Enables procedural generation without hardcoding.

## Acceptance Criteria

- [x] RoomComposition resource format: list of rules for placement
- [x] Rule types: platform_pattern, enemy_group, hazard_zone
- [x] Parameters per rule: min/max difficulty, seed_weight
- [x] At least 5 rule templates defined
- [x] DSL interpreter generates room layout from rules
- [x] Repeatable on same seed (deterministic)
- [x] Tests verify rule parsing and layout generation
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (room/level system)
- M6 (RunSceneAssembler)

## Implementation Notes

**DSL resource format:**
```gdscript
class_name RoomComposition extends Resource

class Rule:
    var type: String  # "platform_pattern", "enemy_group", "hazard_zone"
    var difficulty_min: int
    var difficulty_max: int
    var params: Dictionary

@export var rules: Array[Rule] = []
```

## Scope Notes

- Language simple (declarative rules, not Turing-complete)
- No visual editor (YAML or Godot resource files OK)

