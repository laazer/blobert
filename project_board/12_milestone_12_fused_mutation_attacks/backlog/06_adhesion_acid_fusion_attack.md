# TICKET: 06_adhesion_acid_fusion_attack

# TICKET: 06_adhesion_acid_fusion_attack

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Adhesion + Acid fusion attack — sticky acid puddle (projectile with root + DoT zone)

## Description

Fusing adhesion and acid mutations creates an attack that fires a projectile which lands and creates an acid puddle that roots enemies standing in it. This combines the immobilisation/control power of adhesion with the sustained damage of acid — neither base mutation alone can apply both effects simultaneously. Enemies caught in the puddle cannot move and take continuous acid damage, making it a powerful tool for crowd control and zoning.

Implementation uses the `fusion_attack_framework` (M12 ticket 03) and extends the projectile system with on-impact area effect spawning.

## Acceptance Criteria

- [x] Fusion attack resource created: `attacks/resources/adhesion_acid_fusion.tres`
  - Effect type: `PROJECTILE_PUDDLE`
  - Projectile damage: 0.0 (damage comes from puddle DoT, not impact)
  - Projectile speed: 200.0
  - Attack cooldown: 4.0s
  - Puddle radius: 2.0
  - Puddle persistence: 5.0s
- [x] Projectile system extended for puddle creation
  - On impact, projectile spawns adhesion_acid_puddle at landing location
  - Projectile collision with environment triggers puddle spawn
  - Projectile collision with enemies does NOT spawn puddle (only environmental collision)
- [x] Puddle zone implementation
  - Persists for 5.0s with visual indicator (sticky amber/acidic color blend)
  - Area detector (CircleShape3D or equivalent) with 2.0 unit radius
  - All enemies within puddle are rooted (velocity = Vector3.ZERO) while in zone
  - Exit detection: enemies regain movement capability upon leaving puddle
  - Applies acid DoT at 0.5s intervals: `{ "acid_duration": 5.0, "acid_dps": 0.4, "tick_rate": 0.5 }`
- [x] Root mechanic verified
  - Rooted enemies cannot move (velocity clamped to 0)
  - Rooted enemies can still rotate/face direction
  - Root is NOT an immunity state (enemies can still take damage)
  - Animation plays slow/struggling motion during root (if available)
- [x] VFX and audio feedback
  - Projectile fire sound on attack
  - Puddle spawn impact sound on landing
  - Puddle visual: sticky amber + acid green swirl overlay (Color blend)
  - Root VFX: holding animation or particle effect on rooted enemies
  - DoT tick sound every 0.5s
- [x] Puddle-projectile collision handling
  - Projectile does not bounce; lands and despawns on impact
  - Only one puddle per projectile fire (no cluster spawning)
  - Puddle does not affect the player that created it
- [x] Attack balanced in test encounters
  - Total DPS from puddle: 0.4 acid × 10 ticks = 4.0 damage over 5.0s
  - Root duration: 5.0s (full puddle persistence)
  - Cooldown enforces 4.0s between puddle spawns
  - Puddle radius large enough to catch 1-2 enemies, small enough for positioning skill
- [x] Attacks database entry created (`attacks.json`)
- [x] All M11 prerequisite tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration
- M12 ticket 03: fusion_attack_framework
- M11 ticket 04: attack_resource
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Root implementation: set enemy `velocity = Vector3.ZERO` while in puddle trigger
- Puddle is NOT damage-dealing on projectile impact; only DoT from zone presence
- Use world space position for puddle spawn (projectile landing location)
- Test framework: verify puddle spawns at projectile impact point and root applies immediately

## Example Attack Resource

```gdscript
[gd_resource type="AttackResource" format=3]

[resource]
attack_id = 111
attack_name = "Sticky Puddle"
effect_type = "PROJECTILE_PUDDLE"
damage = 0.0
cooldown = 4.0
range = 10.0
projectile_speed = 200.0
knockback_magnitude = 0.0
color = Color(0.8, 0.8, 0.2)
vfx_scale = 1.3
modifiers = {
  "puddle_radius": 2.0,
  "puddle_persistence": 5.0,
  "acid_duration": 5.0,
  "acid_dps": 0.4,
  "tick_rate": 0.5,
  "root_while_in_puddle": true
}
```
