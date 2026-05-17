# TICKET: 02_moving_platform_controller

**Milestone:** M38 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation

## Title

Moving Platform Controller — linear movement with configurable axis/speed

## Description

Implement controller for MovingPlatform: moves back and forth on axis (X, Y, Z) with configurable speed and range. Player standing on platform rides along. Supports extraction of metadata from asset pipeline.

## Acceptance Criteria

- [x] MovingPlatform inherits from RigidBody3D with kinematic movement
- [x] Properties: axis (x/y/z), speed (units/sec), range (distance)
- [x] Moves linearly from start to start+range, back and forth, looping
- [x] Player/enemy standing on platform moves with it (platform carries passengers)
- [x] Speed and range exported and tweakable
- [x] Tests verify movement speed and looping
- [x] `run_tests.sh` exits 0

## Dependencies

- M38:01 (platform templates)
- M6 (movement system — passenger detection)

## Implementation Notes

**Movement controller:**
```gdscript
var current_direction: int = 1
var current_position: float = 0.0

func _physics_process(delta):
    current_position += speed * current_direction * delta
    
    if current_position >= range or current_position <= 0:
        current_direction *= -1
    
    global_position.x += speed * current_direction * delta  # for axis = x
```

## Scope Notes

- No animation (instant movement OK)
- No deceleration easing (linear velocity acceptable)

