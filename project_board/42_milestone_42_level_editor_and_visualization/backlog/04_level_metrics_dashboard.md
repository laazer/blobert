# TICKET: 04_level_metrics_dashboard

**Milestone:** M42 Level Editor & Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Level Metrics Dashboard — in-editor level analysis summary

## Description

Display statistics about current level: total enemy count, total platform count, average difficulty, player death rate (from replays), mutation/item distribution. Helps designers identify balance gaps.

## Acceptance Criteria

- [x] Dashboard panel shows: enemy count, platform count, hazard count, collectible count
- [x] Calculate average difficulty from heatmap (M42:02)
- [x] Death rate analysis from recording replays (M42:03)
- [x] Mutation distribution in drops (M35 integration)
- [x] Recommendations: "too many enemies", "too little healing" (heuristic)
- [x] Export metrics to CSV or markdown
- [x] Real-time updates on level edits
- [x] `run_tests.sh` exits 0 (editor-only)

## Dependencies

- M42:02 (difficulty heatmap)
- M42:03 (replay recording)
- M35 (mutation drop tables)

## Implementation Notes

**Metrics calculation:**
```gdscript
func calculate_metrics() -> Dictionary:
    return {
        "total_enemies": get_enemy_count(),
        "total_platforms": get_platform_count(),
        "avg_difficulty": calculate_average_difficulty(),
        "enemy_per_platform": get_enemy_count() / float(get_platform_count()),
        "death_rate": analyze_death_rate_from_replays()
    }
```

## Scope Notes

- Recommendations based on simple thresholds (not ML)
- No visualization beyond numbers (text only OK)

