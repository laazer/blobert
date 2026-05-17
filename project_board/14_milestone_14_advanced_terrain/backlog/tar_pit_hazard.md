# TICKET: tar_pit_hazard

**Milestone:** M14 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation (Hazard System)

## Title

Tar pit hazard — movement slow effect with adhesion mutation immunity

## Description

Create a tar pit hazard: a floor-level area that slows movement speed while standing inside. Adhesion mutation grants full immunity (no slow). Tar pits also affect enemies (same 40% movement penalty). This encourages tactical mutation use and creates navigation challenges. Self-contained placeable scene.

## Acceptance Criteria

- [x] Scene created: `scenes/hazards/tar_pit.tscn`
  - Self-contained, placeable in room templates
  - Node3D + Area3D for collision
  - Configurable via export variables
- [x] Movement speed reduction
  - Speed multiplier: 0.4 (40% of normal speed)
  - Applied immediately on entry
  - Removed immediately on exit (no lingering slow)
  - Affects both player and enemies
- [x] Adhesion mutation immunity
  - Player with active MUTATION_ADHESION: unaffected (100% speed)
  - Immunity checked every frame (state-dependent)
  - No visual change when immune
- [x] Enemy slow effect
  - Enemies in tar pit also slowed to 40% speed
  - Applies same slow mechanics as player
  - Enemies can be trapped in tar if desired
- [x] Visual distinction (tar-specific)
  - Color: dark brown/black (RGB: 40, 30, 20)
  - Surface: sticky, muddy appearance
  - Distinct from acid/lava (darker palette)
  - Optional: particle effects (mud splashes, viscosity)
- [x] Area configuration
  - Pool shape: circular or rectangular
  - Size configurable via export var
  - Depth detection: player/enemy in area = affected
- [x] Speed state management
  - Track which entities are in tar pit
  - Apply/remove slow modifier on entry/exit
  - Support multiple tar pits (stacking or priority)
- [x] Scene integration
  - No code changes to place
  - Works with multiple instances
  - Positioned via scene transform
- [x] Testing and validation
  - Manual test: Enter tar, movement slowed to 40%
  - Manual test: Exit tar, full speed immediately
  - Manual test: Acquire adhesion, full speed in tar
  - Manual test: Lose adhesion, slow returns
  - Manual test: Enemies slowed by tar pit
  - Manual test: Multiple tar pits work independently
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — Hazard system foundation
- M11 (Base Mutation Attacks) — Mutation identity

## Implementation Notes

- Use Area3D for detection
- Track in_tar_pit flag per entity
- Apply movement speed multiplier (0.4) when in tar
- Check adhesion immunity before applying slow
- Remove slow on Area3D exit signal

## Scene Structure

```
tar_pit (Node3D)
├── TarGeometry (MeshInstance3D) [dark tar visual]
├── HazardArea (Area3D) [slow trigger]
└── [Collision detection logic]
```

## Example Configuration

```gdscript
@export var pool_radius: float = 2.5
@export var speed_multiplier: float = 0.4  # 40% speed in tar
```

## Notes

- Movement slow is powerful: must be interesting tactical challenge
- Adhesion immunity rewards that mutation's strategic use
- Visual design should convey "sticky/viscous" danger
- Consider audio: squelching sounds when moving in tar
