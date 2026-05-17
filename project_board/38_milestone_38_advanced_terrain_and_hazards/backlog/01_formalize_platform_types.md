# TICKET: 01_formalize_platform_types

**Milestone:** M38 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation

## Title

Formalize Platform Types — standard Godot scenes for 8 platform/hazard types

## Description

Define 8 platform/hazard types as Godot 3D scenes with standardized properties. Types: FlatPlatform, MovingPlatform, CrumblingPlatform, SolidWall, CrenellatedWall, SpikeTrap, FireTrap, Checkpoint. Each with mutation interaction rules.

## Acceptance Criteria

- [x] 8 platform scene templates created in `scenes/platforms/`
- [x] Each scene has StaticBody3D or RigidBody3D base + CollisionShape3D + MeshInstance3D
- [x] Mutation interaction tags: immunity/resistance per platform type
- [x] Example: AcidTrap immune to Acid mutation, resists Fire
- [x] Scenes exported with configurable size, color, material
- [x] Tests verify scene instantiation and collision detection
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level — procedural room system)
- M2–M13 (mutation system for interactions)

## Implementation Notes

**Scene structure:**
```
FlatPlatform.tscn
├── StaticBody3D
│   ├── CollisionShape3D (BoxShape3D 4×0.5×4)
│   ├── MeshInstance3D (colored material)
│   └── PlatformInteraction (script, mutation tags)
```

## Scope Notes

- Visual polish (detailed mesh, texture) deferred to M39
- Mutation interactions trigger via script signals

