# TICKET: 02_difficulty_scaling_system

**Milestone:** M40 Procedural Level Composition  
**Status:** Backlog  
**Type:** Implementation

## Title

Difficulty Scaling System — parameterize room composition by difficulty level

## Description

Extend room generation to select and parameterize rules based on difficulty slider (1–10). Higher difficulty = harder platform patterns, more enemies, tougher mutations. Rules include difficulty range (`difficulty_min`, `difficulty_max`).

## Acceptance Criteria

- [x] RunState tracks difficulty (1–10, exported)
- [x] DSL rules filtered by difficulty range during generation
- [x] Rule parameters scale: enemy_count, enemy_mutation_level, hazard_density
- [x] Difficulty 1 = easy (fewer enemies, weak mutations)
- [x] Difficulty 10 = hard (dense enemies, strong mutations)
- [x] Scaling formula linear or documented
- [x] Tests verify rule selection and scaling
- [x] `run_tests.sh` exits 0

## Dependencies

- M40:01 (room composition DSL)
- M6 (run state)

## Implementation Notes

**Scaling function:**
```gdscript
func scale_for_difficulty(base_value: float, difficulty: int) -> float:
    # Difficulty 1 = 0.5×, difficulty 10 = 1.5×
    return base_value * (0.5 + (difficulty - 1) * 0.1)
```

## Scope Notes

- Linear scaling acceptable (no exponential curves)
- UI difficulty selector (M6 feature, not this ticket)

