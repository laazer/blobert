# TICKET: 03_camera_profile_system

**Milestone:** M39 Level Theming & Atmosphere  
**Status:** Backlog  
**Type:** Implementation

## Title

Camera Profile System — per-theme camera settings (FOV, distance, angle)

## Description

Bundle camera parameters into presets per theme (lab tight/high FOV, cavern wide/low angle, etc.). Rooms apply camera profile via config.

## Acceptance Criteria

- [x] CameraProfile resource with: fov, distance, angle_offset, smoothing_speed
- [x] 4+ profiles for each theme (matching lighting presets)
- [x] Room applies profile on load
- [x] Smooth transition between profiles
- [x] Tests verify camera parameter application
- [x] `run_tests.sh` exits 0

## Dependencies

- M1 (camera system)
- M39:01 (lighting presets for theme alignment)

## Implementation Notes

**Profile structure:**
```gdscript
class_name CameraProfile extends Resource

@export var name: String
@export var fov: float = 75.0
@export var distance: float = 8.0
@export var angle_offset: Vector3 = Vector3.ZERO
@export var smoothing_speed: float = 5.0
```

## Scope Notes

- No complex animation (smooth lerp acceptable)
- FOV change optional (constant OK for base)

