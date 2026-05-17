# TICKET: 04_per_zone_lighting_overrides

**Milestone:** M39 Level Theming & Atmosphere  
**Status:** Backlog  
**Type:** Implementation

## Title

Per-Zone Lighting Overrides — local lighting variations within room

## Description

Allow specific zones within a room to override global lighting. Boss arena might be darker/redder than rest of room. Zones defined via Area3D triggers with custom LightingPreset.

## Acceptance Criteria

- [x] Zone resource with override preset and transition distance
- [x] On player entry, lerp to zone preset (smooth transition)
- [x] On exit, lerp back to room preset
- [x] Transition distance prevents harsh cutoffs (default 2 units)
- [x] Multiple zones don't conflict (nearest zone wins)
- [x] Tests verify zone entry/exit and lerp
- [x] `run_tests.sh` exits 0

## Dependencies

- M39:01 (lighting preset system)
- M4 (zone/area system)

## Implementation Notes

**Zone area detection:**
```gdscript
func _on_player_entered_zone(zone: LightingZone):
    var tween = create_tween()
    tween.tween_property(world_lights, "preset", zone.preset, 0.5)

func _on_player_exited_zone():
    var tween = create_tween()
    tween.tween_property(world_lights, "preset", room_preset, 0.5)
```

## Scope Notes

- Overlap handling: nearest zone by distance
- No hierarchical zone stacking (single active zone at a time)

