# TICKET: 07_adhesion_claw_fusion_attack

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Adhesion + Claw fusion attack — grapple and shred (projectile pull + multi-hit combo)

## Description

Fusing adhesion and claw mutations creates a grapple attack: Blobert fires a sticky tendril that pulls the first enemy toward the player, then immediately applies a multi-hit shred on arrival. This combines the long-range control of adhesion (pull) with the close-range damage of claw (shred), creating a gap-closer that no base mutation can achieve alone. High-skill attack: projectile must hit first, then the enemy is locked into the pull sequence.

Implementation uses the `fusion_attack_framework` (M12 ticket 03) to combine adhesion's pull mechanic with claw's multi-hit combo.

## Acceptance Criteria

- [x] Fusion attack resource created: `attacks/resources/adhesion_claw_fusion.tres`
  - Effect type: `PROJECTILE_PULL`
  - Projectile damage: 0.5 (impact damage before pull)
  - Projectile speed: 250.0
  - Attack cooldown: 3.5s
  - Pull duration: 0.4s
  - Pull distance: 3.0 units
  - Follow-up combo: 3 claw hits at 0.15s intervals
  - Startup frames: 4
- [x] Projectile pull mechanic implemented
  - Projectile fires from player toward aim direction
  - On first enemy hit, projectile latches and enemy begins pull sequence
  - Pull interpolates enemy position toward player over 0.4s
  - Enemy reaches melee range (1.5 units) by pull end
  - Enemy is invulnerable during pull (cannot be hit by other attacks)
- [x] Multi-hit combo executed on pull arrival
  - At 0.4s mark (pull end), 3 rapid claw hits execute automatically
  - Hit 1 at t=0.40s, Hit 2 at t=0.55s, Hit 3 at t=0.70s
  - Each hit: 1.5 damage, 80.0 knockback (away direction)
  - Knockback applies away from player center
  - All 3 hits execute even if enemy is killed on Hit 1 (phantom hits visible as VFX)
- [x] Pull state management verified
  - Enemy position follows smooth interpolation (not teleport)
  - Enemy rotation can update during pull to face player
  - Pull animation plays on enemy (if available) showing struggling motion
  - Pull cannot be cancelled once initiated (unless enemy dies)
- [x] VFX and audio feedback
  - Tendril fire sound on attack
  - Tendril glow/trail visual during flight
  - Pull vortex VFX around enemy during pull
  - Claw hit spark effects per combo hit
  - Combo hit sounds play at strike frames
- [x] Attack balanced in test encounters
  - Total damage: 0.5 impact + (3 hits × 1.5) combo = 5.0 damage
  - Cooldown enforces 3.5s between grapple attempts
  - Single-target focus (only first hit enemy is pulled)
  - Gap-closer range: ~5.0 units (projectile range + pull)
- [x] Attacks database entry created (`attacks.json`)
- [x] All M11 prerequisite tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration
- M12 ticket 03: fusion_attack_framework
- M11 ticket 04: attack_resource
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Pull uses tweening/lerp for smooth enemy position interpolation
- Enemy invulnerability during pull prevents double-counting from other sources
- Combo hits execute regardless of enemy death state (create dummy hits for VFX)
- Test framework: verify pull target reaches melee range before combo starts

## Example Attack Resource

```gdscript
[gd_resource type="AttackResource" format=3]

[resource]
attack_id = 112
attack_name = "Grapple and Shred"
effect_type = "PROJECTILE_PULL"
damage = 0.5
cooldown = 3.5
range = 5.0
projectile_speed = 250.0
startup_frames = 4
knockback_magnitude = 80.0
knockback_direction = "away"
color = Color(0.7, 0.5, 0.8)
vfx_scale = 1.2
modifiers = {
  "pull_duration": 0.4,
  "pull_distance": 3.0,
  "combo_hits": 3,
  "hit_interval": 0.15,
  "combo_damage": 1.5
}
```
