# TICKET: lava_pit_hazard

**Milestone:** M14 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation (Hazard System)

## Title

Lava pit hazard — continuous burn damage with carapace damage reduction (50% DPS with mutation)

## Description

Create a lava pit hazard: a floor-level area that continuously deals burn damage while the player stands inside. The carapace mutation reduces damage taken by 75% (player takes 1.25 DPS instead of 5.0 DPS). This encourages tactical mutation use: carapace for lava resistance, acid/adhesion/claw for other hazards. Self-contained placeable scene.

## Acceptance Criteria

- [x] Scene created: `scenes/hazards/lava_pit.tscn`
  - Self-contained, placeable in room templates
  - Node3D + Area3D for collision
  - Configurable via export variables
- [x] Continuous burn damage
  - Base damage: 5.0 DPS (2.5 per 0.5s tick)
  - Ticks every 0.5s (not per-frame)
  - Damage applies immediately on entry
  - Damage stops immediately on exit
- [x] Carapace mutation damage reduction
  - With active MUTATION_CARAPACE: 75% damage reduction
  - Reduced damage: 1.25 DPS (0.625 per 0.5s tick)
  - Reduction checked every damage tick
  - Player still takes visible damage (not immunity)
- [x] Visual distinction (lava-specific)
  - Color: red-orange glow (RGB: 255, 100, 50)
  - Surface: glowing, molten appearance
  - Emissive material or light glow effect
  - Distinct from acid trap (warmer color palette)
  - Optional: particle effects (smoke, ash)
- [x] Area configuration
  - Pool shape: circular or rectangular
  - Size configurable via export var
  - Depth detection: player in area = affected
- [x] Scene integration
  - No code changes to place
  - Works with multiple instances
  - Positioned via scene transform
- [x] Testing and validation
  - Manual test: Stand in lava, take 5 DPS
  - Manual test: Acquire carapace, damage reduces to 1.25 DPS
  - Manual test: Lose carapace, damage returns to 5.0 DPS
  - Manual test: Exit lava, damage stops
  - Manual test: Multiple instances work independently
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — Hazard system foundation
- M11 (Base Mutation Attacks) — Mutation identity

## Implementation Notes

- Use Area3D for detection
- Timer or frame-based tick for 0.5s intervals
- Query carapace mutation state before applying damage
- Apply damage reduction multiplier (0.25 when carapace active)

## Scene Structure

```
lava_pit (Node3D)
├── LavaGeometry (MeshInstance3D) [glowing lava visual]
├── HazardArea (Area3D) [damage trigger]
└── DamageTimer (Timer) [0.5s tick]
```

## Example Configuration

```gdscript
@export var pool_radius: float = 2.5
@export var base_damage_per_second: float = 5.0
@export var carapace_reduction: float = 0.25  # Takes 25% damage with carapace
@export var tick_rate: float = 0.5
```

## Notes

- 75% damage reduction with carapace makes lava navigable (tactical choice)
- Visual glow is important: must look like "hot/dangerous"
- Consider audio: crackling/burning sounds for immersion
