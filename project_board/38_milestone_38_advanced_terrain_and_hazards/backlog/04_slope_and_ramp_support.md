# TICKET: 04_slope_and_ramp_support

**Milestone:** M38 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation

## Title

Slope & Ramp Support — angled platforms 15–45° for vertical navigation

## Description

Extend platform system to support angled ramps. Player moves up/down slopes naturally. Movement simulation adjusts velocity along slope plane. Collision shape reflects angle.

## Acceptance Criteria

- [x] RampPlatform scene added with angled mesh + collision shape
- [x] Slope angle configurable (15–45°, exported)
- [x] Player movement follows slope (velocity projected on slope plane)
- [x] No sliding backward on moderate slopes (friction/cling)
- [x] Jumping on slope maintains momentum (direction adjustment optional)
- [x] Multiple slopes at different angles work together
- [x] Tests verify slope movement and no-slide conditions
- [x] `run_tests.sh` exits 0

## Dependencies

- M38:01–02 (platform system)
- M6 (movement simulation)

## Implementation Notes

**Slope movement projection:**
```gdscript
func get_slope_normal(collider: Node3D) -> Vector3:
    # raycast down to determine slope normal
    return raycast_result.normal

func project_velocity_on_slope(vel: Vector3, slope_normal: Vector3) -> Vector3:
    return vel - slope_normal * vel.dot(slope_normal)
```

## Scope Notes

- No wall-running or edge cases (simple slope only)
- Cling to slope implicit (no player sliding off)

