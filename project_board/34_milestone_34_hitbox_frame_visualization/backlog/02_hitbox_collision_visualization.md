# TICKET: 02_hitbox_collision_visualization

**Milestone:** M34 Hitbox & Frame Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Hitbox Collision Visualization — render collision shapes during active window

## Description

Render hitbox collision shapes (spheres, capsules) during attack active window with color coding (green=active/safe, red=collision/damage). Helps visualize range and verify no clipping.

## Acceptance Criteria

- [x] Hitbox rendered as wireframe or semi-transparent solid when active_frames > 0
- [x] Color: green during active, gray during startup/endlag
- [x] Separate color for collision-with-enemy (red) vs no collision (green)
- [x] Hitbox follows hitbox position (not stuck on player)
- [x] Toggle via `debug_hitbox_visualization` bool
- [x] No performance impact when disabled
- [x] Multiple simultaneous hitboxes render correctly (combo hits)
- [x] `run_tests.sh` exits 0

## Dependencies

- M30:02 (frame events for active window timing)
- M11 (hitbox spawning)

## Implementation Notes

**DebugDraw helpers:**
```gdscript
func debug_draw_hitbox(shape: Shape3D, pos: Vector3, color: Color):
    if not debug_hitbox_visualization:
        return
    
    if shape is SphereShape3D:
        DebugDraw.sphere(pos, shape.radius, color, 0)
    elif shape is CapsuleShape3D:
        DebugDraw.capsule(pos, shape.radius, shape.height, color, 0)
```

## Scope Notes

- Wireframe preferred (less performance overhead than solid)
- No animation playback in this ticket (static frame views)

