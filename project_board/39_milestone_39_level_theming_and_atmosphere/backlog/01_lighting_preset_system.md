# TICKET: 01_lighting_preset_system

**Milestone:** M39 Level Theming & Atmosphere  
**Status:** Backlog  
**Type:** Implementation

## Title

Lighting Preset System — reusable ambient + directional light bundles

## Description

Define preset lighting configurations (lab, cavern, alien, lava, etc.). Each preset bundles ambient color/intensity, directional light angle/color/intensity, fog settings, and skybox. Rooms apply presets via config.

## Acceptance Criteria

- [x] LightingPreset resource format defined with all light parameters
- [x] At least 4 presets created: Lab (white/bright), Cavern (orange/warm), Alien (purple/cool), Lava (red/hot)
- [x] Each preset specifies: ambient_color, ambient_intensity, dir_light_color, dir_light_intensity, dir_light_angle
- [x] Room/level can apply preset via single property
- [x] Smooth transition between presets (crossfade optional for M39:future)
- [x] Preset serialized with room config
- [x] Tests verify preset application
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (room/level system)
- M6 (RunSceneAssembler)

## Implementation Notes

**Preset structure:**
```gdscript
class_name LightingPreset extends Resource

@export var name: String
@export var ambient_color: Color
@export var ambient_intensity: float = 1.0
@export var dir_light_color: Color
@export var dir_light_intensity: float = 1.5
@export var dir_light_angle: Vector3  # euler angles
```

## Scope Notes

- No fog/skybox support in base (visual polish future)
- Instant application OK (no crossfade)

