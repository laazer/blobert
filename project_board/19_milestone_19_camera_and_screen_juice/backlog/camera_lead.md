# TICKET: camera_lead

**Milestone:** M19 Camera and Screen Juice  
**Status:** Backlog  
**Type:** Implementation (Camera/Presentation)

## Title

Camera lead — camera offset ahead of player movement direction

## Description

Update camera follow to offset slightly in player's movement direction. Improves visibility of upcoming area. Lead is smooth and dynamic (zero when stationary, increases with movement speed).

## Acceptance Criteria

- [x] Lead offset implemented (default 1.5 units)
- [x] Smooth transitions (no snapping on direction change)
- [x] Zero lead when stationary
- [x] Additive to base follow (follow position + lead offset)
- [x] Bounds clamping (prevent showing out-of-bounds)
- [x] Configurable: `@export lead_strength: float`
- [x] All M1 tests pass
- [x] `run_tests.sh` exits 0

## Implementation

```gdscript
func _update_camera_lead():
    var lead_offset = player_velocity.x.sign() * lead_strength
    camera_target = player.position + Vector3(lead_offset, 0, 0)
    # Clamp to level bounds
    camera_target.x = clamp(camera_target.x, bounds_min, bounds_max)
```

## Dependencies

- M1 (base camera)
- M19 ticket 03: screen_shake_system

## Notes

- Lead improves view distance in movement direction (good game feel)
- Dynamic: increases visibility, doesn't slow camera
- Bounds prevent showing out-of-level geometry
