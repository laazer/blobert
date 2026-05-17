# TICKET: 05_acid_carapace_fusion_attack

# TICKET: 05_acid_carapace_fusion_attack

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Acid + Carapace fusion attack — corrosive slam (ground slam with persistent acid pool)

## Description

Fusing acid and carapace mutations creates a powerful ground slam that leaves a persistent acid pool at the impact point. This combines the area denial and sustained damage of acid with the immediate impact force of carapace. Enemies hit by the slam are knocked away from the player, and if they land in (or remain in) the acid pool, they take continuous DoT damage. Strategic positioning rewards players for slamming near environmental hazards or grouping enemies together.

Implementation uses the `fusion_attack_framework` (M12 ticket 03) to combine Carapace's area slam mechanics with Acid's persistent effect system.

## Acceptance Criteria

- [x] Fusion attack resource created: `attacks/resources/acid_carapace_fusion.tres`
  - Effect type: `MELEE_SLAM`
  - Base damage: 4.0
  - Slam radius: 3.0
  - Attack cooldown: 4.5s
  - Knockback magnitude: 150.0 (direction: away)
  - Startup frames: 10
- [x] Attack executor integrates with FusionAttackFramework
  - Waits for startup_frames before damage check
  - Creates circular slam area from player position
  - All enemies in slam radius take damage + knockback
  - Applies knockback AWAY from slam center
- [x] Acid pool system implemented
  - Pool spawns at slam impact point immediately on damage frame
  - Pool persists for 6.0s with visual indicator (translucent acid texture)
  - Enemies in pool take acid DoT at 0.5s intervals (not continuous tick)
  - Acid modifier: `{ "acid_duration": 6.0, "acid_dps": 0.3, "tick_rate": 0.5 }`
  - Pool does NOT refresh acid duration if enemy is already in pool (stacks independently)
- [x] Enemy knockback interaction with pool verified
  - Enemies hit by slam and positioned in pool direction take pool damage
  - Knockback is applied TOWARD slam center (away from player)
  - Knockback is strong enough to move light enemies into nearby pools
- [x] VFX and audio feedback
  - Slam impact sound at startup
  - Pool spawn VFX with swirl/glow effect at pool location
  - Color: acidic yellow-green (Color(0.7, 0.9, 0.1))
  - Pool visual indicator persists for duration
  - Damage tick sound every 0.5s while enemy is in pool
- [x] Attack balanced in test encounters
  - Slam DPS: 4.0 immediate + pool DoT (0.3 × 6 ticks = 1.8) = 5.8 total per successful slam + pool
  - Cooldown enforces 4.5s between slams (prevents spam)
  - Pool radius should allow 1-2 enemies to benefit simultaneously
- [x] Attacks database entry created (`attacks.json`)
- [x] All M11 prerequisite tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration
- M12 ticket 03: fusion_attack_framework
- M11 ticket 04: attack_resource
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Pool is a static/non-interactive game object (no rigidbody, just collision trigger)
- Use CircleShape2D (or equivalent 3D sphere query) for pool detection
- Acid pool system should reuse `AcidVFXSystem` but with persistent spawning
- Knockback applies in slam frame only; pool damage applies over 6.0s
- Test framework: verify pool spawns at slam position and persists for 6.0s

## Example Attack Resource

```gdscript
[gd_resource type="AttackResource" format=3]

[resource]
attack_id = 110
attack_name = "Corrosive Slam"
effect_type = "MELEE_SLAM"
damage = 4.0
cooldown = 4.5
range = 3.0
startup_frames = 10
knockback_magnitude = 150.0
knockback_direction = "away"
color = Color(0.7, 0.9, 0.1)
vfx_scale = 1.5
modifiers = {
  "pool_persistence": 6.0,
  "acid_duration": 6.0,
  "acid_dps": 0.3,
  "tick_rate": 0.5
}
```
