# TICKET: acid_trap_hazard

**Milestone:** M14 Advanced Terrain & Hazards  
**Status:** Backlog  
**Type:** Implementation (Hazard System)

## Title

Acid trap hazard — area denial pool with continuous DoT and mutation immunity

## Description

Create an acid pool hazard: a floor-level circular or rectangular area that deals damage over time while the player stands inside. Primary purpose is **area denial**—routing the player around the hazard unless they have the acid mutation (which grants full immunity). Acid pools encourage tactical use of mutations. Self-contained placeable scene.

## Acceptance Criteria

- [x] Scene created: `scenes/hazards/acid_trap.tscn`
  - Self-contained, placeable in room templates
  - Node3D + Area3D for collision detection
  - Configurable via export variables
- [x] Continuous DoT implementation
  - Damage: 8 per second (4.0 per 0.5s tick)
  - Damage applied every 0.5s while player in area
  - No immunity window; continuous ticking (unlike spikes)
  - Damage stops immediately upon leaving area
- [x] Acid mutation immunity
  - Player with active MUTATION_ACID takes 0 damage
  - Immunity applies ONLY to acid trap damage (not other hazards)
  - Immunity checked every damage tick (state-dependent)
  - No visual change when immune (player still sees hazard)
- [x] Visual distinction (acid-specific)
  - Color: acidic green-yellow (RGB: 100, 200, 80)
  - Surface: translucent or bubbly appearance
  - Clearly distinct from lava (different color palette)
  - Optional: particle effects (bubbles, vapor) for atmosphere
- [x] Area configuration
  - Pool shape: circular or rectangular (configurable)
  - Pool size: configurable via export var (radius or width/height)
  - Depth detection: player in area = affected (ignore height)
  - Visual mesh covers entire hazard area
- [x] Scene integration
  - No code changes to place in room templates
  - Works with multiple instances
  - Positioned via scene transform
- [x] Testing and validation
  - Manual test: Stand in pool, take 8 DPS
  - Manual test: Leave pool, damage stops immediately
  - Manual test: Acquire acid mutation, enter pool (no damage)
  - Manual test: Lose acid mutation, damage resumes
  - Manual test: Multiple pools work independently
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — Hazard system foundation
- M11 (Base Mutation Attacks) — Mutation identity available

## Implementation Notes

- Use Area3D for damage detection
- Timer or frame-based tick for 0.5s damage intervals
- Query player mutation state before applying damage
- Consider visual animation (bubbling, pulsing) for atmosphere

## Scene Structure

```
acid_trap (Node3D)
├── PoolGeometry (MeshInstance3D) [pool visual]
├── HazardArea (Area3D) [damage trigger]
└── DamageTimer (Timer) [0.5s tick]
```

## Example Configuration

```gdscript
@export var pool_radius: float = 2.0
@export var damage_per_second: float = 8.0
@export var tick_rate: float = 0.5  # Tick every 0.5s
```

## Notes

- Acid mutation immunity is key design element: encourages mutation use
- DoT encourages area avoidance or tactical mutation swaps
- Visual design should evoke "corrosive" danger
