# TICKET: 02_parallax_background_layers

**Milestone:** M39 Level Theming & Atmosphere  
**Status:** Backlog  
**Type:** Implementation

## Title

Parallax Background Layers — depth illusion with camera-relative motion

## Description

Add multiple background layers that move at different speeds relative to camera, creating depth illusion. Layers scroll slowly to reinforce scene atmosphere (distant mountains, clouds, etc.).

## Acceptance Criteria

- [x] 3+ background layers in each level (distant, mid, foreground)
- [x] Each layer has depth/parallax factor (0.2, 0.5, 1.0 recommended)
- [x] Layers move slower than camera (factor < 1.0) for distant appearance
- [x] Implemented via Canvas2D layers or quadPlanes following camera
- [x] No performance regression (billboards OK)
- [x] Seamless looping textures (no seams visible)
- [x] Tests verify parallax calculation
- [x] `run_tests.sh` exits 0

## Dependencies

- M39:01 (lighting establishes mood)
- M1 (camera system)

## Implementation Notes

**Parallax layer movement:**
```gdscript
func update_parallax_layer(camera_pos: Vector3, layer_factor: float):
    var effective_pos = camera_pos * layer_factor
    layer_mesh.global_position = effective_pos
```

## Scope Notes

- 2D parallax (Y-axis only, not full 3D)
- Texture wrapping/looping handled by material

