# TICKET: 08_adhesion_carapace_fusion_attack

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Adhesion + Carapace fusion attack — armoured lunge slam (invulnerable charge + heavy hit)

## Description

Fusing adhesion and carapace mutations creates a charging slam that briefly makes the player invincible during the lunge. Blobert charges forward in an armoured state, is invulnerable to incoming damage, and on enemy contact deals heavy damage with significant knockback. The invincibility window is unique to this fusion and the only way to achieve player damage mitigation through mutations. High-risk/high-reward attack: must commit to the lunge but gain temporary defense.

Implementation uses the `fusion_attack_framework` (M12 ticket 03) to combine carapace's charging movement with adhesion's defensive state.

## Acceptance Criteria

- [x] Fusion attack resource created: `attacks/resources/adhesion_carapace_fusion.tres`
  - Effect type: `CHARGE_INVULNERABLE`
  - Charge damage: 3.5
  - Charge distance: 5.0 units
  - Charge duration: 0.5s
  - Attack cooldown: 5.0s
  - Knockback magnitude: 200.0 (away direction)
  - Startup frames: 3
- [x] Charge movement implemented
  - On activation, player is locked into forward lunge (cannot change direction mid-lunge)
  - Lunge moves player forward at constant velocity over 0.5s
  - Player travels exactly 5.0 units horizontally
  - Lunge movement is camera-relative or world-relative (specify in design)
  - Player animation plays charging/armoured motion
- [x] Invulnerability state applied during charge
  - Player is invulnerable to ALL damage sources during 0.5s lunge
  - Cannot be knocked back during lunge
  - Status effects (poison, acid, slow) do NOT apply during lunge
  - Player can still take damage after lunge ends (normal state)
  - Invulnerability duration: full 0.5s charge time
- [x] Enemy collision detection and hit during lunge
  - Hitbox positioned in front of player during charge
  - All enemies touched during lunge take damage
  - Each enemy hit takes 3.5 damage
  - Hit happens at first touch (not per-frame multi-hitting)
  - Knockback applies away from lunge direction (backward relative to movement)
- [x] VFX and audio feedback
  - Charge startup sound with charging animation
  - Armoured/invulnerability visual indicator during lunge (glow or shield effect)
  - Hit impact sound on enemy contact
  - Hit spark VFX at impact point per enemy
  - Lunge trail VFX following player during movement
- [x] Attack balanced in test encounters
  - Damage: 3.5 per hit (single target per contact)
  - High risk: invulnerability only during lunge (vulnerable after)
  - High reward: cannot be interrupted once initiated
  - Cooldown enforces 5.0s between lunges
  - Lunge distance (5.0 units) large enough to cross arena but not map-breaking
- [x] Attacks database entry created (`attacks.json`)
- [x] All M11 prerequisite tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration
- M12 ticket 03: fusion_attack_framework
- M11 ticket 04: attack_resource
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Invulnerability: create temporary `invulnerable` flag on player, set to true at lunge start, false at end
- Charge uses fixed movement (Tween with duration 0.5s or frame-based calculation)
- Disable player input during lunge (cannot jump, attack, or change direction)
- Test framework: verify player is invulnerable by applying damage during lunge and confirming no health change

## Example Attack Resource

```gdscript
[gd_resource type="AttackResource" format=3]

[resource]
attack_id = 113
attack_name = "Armoured Lunge Slam"
effect_type = "CHARGE_INVULNERABLE"
damage = 3.5
cooldown = 5.0
range = 5.0
startup_frames = 3
knockback_magnitude = 200.0
knockback_direction = "away"
color = Color(0.8, 0.6, 0.2)
vfx_scale = 1.4
modifiers = {
  "charge_distance": 5.0,
  "charge_duration": 0.5,
  "invulnerable_during_charge": true
}
```
