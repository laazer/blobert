# TICKET: 02_difficulty_heatmap_visualization

**Milestone:** M42 Level Editor & Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Difficulty Heatmap Visualization — color-coded spatial difficulty display

## Description

Overlay on level showing areas color-coded by local difficulty (enemy density, hazard density, platform challenge). Red = hard, yellow = medium, green = easy. Helps level designers identify balance issues.

## Acceptance Criteria

- [x] Heatmap rendered as colored mesh overlay
- [x] Difficulty calculated per grid cell (8×8 unit cells)
- [x] Factors: enemy_count, hazard_density, platform_type_difficulty
- [x] Color ramp: green → yellow → red (easy → hard)
- [x] Heatmap regenerates on room edit (with debounce)
- [x] Toggle heatmap visibility in editor
- [x] No performance impact when hidden
- [x] `run_tests.sh` exits 0 (editor-only)

## Dependencies

- M42:01 (editor integration)
- M40 (procedural composition for difficulty data)

## Implementation Notes

**Difficulty calculation per cell:**
```gdscript
func calculate_cell_difficulty(cell_pos: Vector3, radius: float) -> float:
    var enemies = get_enemies_in_radius(cell_pos, radius)
    var hazards = get_hazards_in_radius(cell_pos, radius)
    var difficulty = enemies.size() * 2.0 + hazards.size() * 1.0
    return clamp(difficulty, 0.0, 10.0)
```

## Scope Notes

- Static difficulty (not dynamic based on player level)
- Grid resolution configurable (8×8 default)

