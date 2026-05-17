# TICKET: 04_encounter_template_library

**Milestone:** M40 Procedural Level Composition  
**Status:** Backlog  
**Type:** Implementation

## Title

Encounter Template Library — reusable enemy + platform combos for rule composition

## Description

Build library of reusable encounter templates (e.g., "CliffPursuitCombo", "SpikeTrapGauntlet", "BossArenaCircle"). Templates parameterized and used as building blocks in room composition rules.

## Acceptance Criteria

- [x] EncounterTemplate resource: enemy_types, positions, platform_layout, hazards
- [x] At least 10 templates covering varied gameplay (chase, platform, hazard)
- [x] Templates parameterized (spawn count, mutation level, difficulty)
- [x] DSL rules reference templates by ID
- [x] Templates instantiated correctly in room generation
- [x] Tests verify template instantiation
- [x] `run_tests.sh` exits 0

## Dependencies

- M40:01–02 (composition DSL and scaling)
- M4 (room/entity system)

## Implementation Notes

**Template structure:**
```gdscript
class_name EncounterTemplate extends Resource

class EnemyGroup:
    var enemy_type: String
    var count: int
    var positions: Array[Vector3]
    var mutation_level: int

@export var name: String
@export var enemies: Array[EnemyGroup] = []
@export var platforms: Array[String] = []  # platform type IDs
@export var hazards: Array[String] = []    # hazard type IDs
```

## Scope Notes

- Positions hardcoded per template (no dynamic placement in base)
- No animation/timing (static placement OK)

