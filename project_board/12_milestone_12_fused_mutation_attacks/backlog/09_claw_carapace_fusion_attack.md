# TICKET: 09_claw_carapace_fusion_attack

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Claw + Carapace fusion attack — armoured flurry charge (charging multi-hit line attack)

## Description

Fusing claw and carapace mutations creates a charging flurry: Blobert charges forward and delivers rapid claw hits to every enemy along the path. This combines the multi-hit nature of claw with the movement and area coverage of carapace's charge, creating an AoE attack that hits all enemies in a line. Impossible with either base mutation alone: solo claw is single-target, solo carapace is slam-only. High DPS for skilled positioning along enemy lines.

Implementation uses the `fusion_attack_framework` (M12 ticket 03) to combine carapace's charging movement with claw's multi-hit combo delivered per enemy.

## Acceptance Criteria

- [x] Fusion attack resource created: `attacks/resources/claw_carapace_fusion.tres`
  - Effect type: `CHARGE_FLURRY`
  - Charge distance: 6.0 units
  - Charge duration: 0.6s
  - Attack cooldown: 4.0s
  - Hits per enemy: 3
  - Damage per hit: 1.2
  - Knockback magnitude: 100.0 (away direction)
  - Startup frames: 2
- [x] Charge movement implemented
  - On activation, player is locked into forward charge (cannot change direction mid-charge)
  - Charge moves player forward at constant velocity over 0.6s
  - Player travels exactly 6.0 units horizontally
  - Player animation plays charging flurry motion
  - Charge is camera-relative or world-relative (specify in design)
- [x] Enemy collision detection during charge
  - Hitbox positioned in front of player during charge
  - All enemies touched during charge are marked for combo
  - Enemy is hit multiple times as player passes through/near them
  - Hit window: ~0.1s per enemy in proximity
  - Each touched enemy receives full 3-hit combo
- [x] Multi-hit combo delivery
  - Each enemy touched receives 3 rapid claw hits
  - Hit timing: 0.1s apart (0s, 0.1s, 0.2s from first touch)
  - Damage per hit: 1.2
  - Knockback: 100.0 away from charge center
  - All 3 hits execute even if enemy dies (phantom VFX)
  - Different enemies can be hit at different times along charge path
- [x] Collision handling and multi-target support
  - No double-hitting: each enemy only receives one combo per charge (3 hits total, not 3 per pass)
  - Enemies at different positions along path hit at different frame times
  - Line-of-sight not required (hits all enemies player-relative in front)
  - AoE radius: ~1.5 units perpendicular to charge line
- [x] VFX and audio feedback
  - Charge startup sound with charging animation
  - Flurry motion trail VFX during charge
  - Claw hit spark effects per hit on each enemy
  - Hit sound at each strike frame
  - Knockback VFX visible per enemy on hit
- [x] Attack balanced in test encounters
  - Total DPS per enemy: 3 hits × 1.2 = 3.6 damage
  - Multiple enemies: 3.6 × number of enemies hit (max ~3-4 in line)
  - Cooldown enforces 4.0s between charges (sustained damage requires positioning)
  - Charge distance (6.0 units) allows crossing arena width
- [x] Attacks database entry created (`attacks.json`)
- [x] All M11 prerequisite tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration
- M12 ticket 03: fusion_attack_framework
- M11 ticket 04: attack_resource
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Charge uses fixed movement (Tween with duration 0.6s or frame-based calculation)
- Track which enemies have been hit during this charge to prevent double-hitting
- Disable player input during charge (cannot jump, attack, or change direction)
- Hit timing critical: deliver hits as player moves through enemy position, not pre-computed
- Test framework: verify all enemies in charge path are hit exactly once (3 hits per enemy)

## Example Attack Resource

```gdscript
[gd_resource type="AttackResource" format=3]

[resource]
attack_id = 114
attack_name = "Armoured Flurry Charge"
effect_type = "CHARGE_FLURRY"
damage = 1.2
cooldown = 4.0
range = 6.0
startup_frames = 2
knockback_magnitude = 100.0
knockback_direction = "away"
color = Color(0.9, 0.4, 0.1)
vfx_scale = 1.3
modifiers = {
  "charge_distance": 6.0,
  "charge_duration": 0.6,
  "hits_per_enemy": 3,
  "hit_interval": 0.1,
  "aoe_radius": 1.5
}
```
