# TICKET: 04_acid_claw_fusion_attack

# TICKET: 04_acid_claw_fusion_attack

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Acid + Claw fusion attack — venomous shred (3-hit combo with stacking poison)

## Description

Fusing acid and claw mutations creates a rapid melee attack that applies acid DoT on every hit. Unlike the base acid attack (which has a single DoT instance with refresh), each claw swipe in the combo poisons the enemy with a *separate* stacking acid instance. This rewards staying in melee range for sustained damage — three successful hits at close range create three independent DoT stacks that tick simultaneously.

Implementation builds on the `fusion_attack_framework` (M12 ticket 03) to combine Claw's hitbox/knockback mechanics with Acid's DoT application system.

## Acceptance Criteria

- [x] Fusion attack resource created: `attacks/resources/acid_claw_fusion.tres`
  - Effect type: `MELEE_SWIPE_COMBO`
  - Damage per hit: 1.8
  - Combo hits: 3
  - Attack cooldown: 2.0s
  - Range: 1.2
  - Knockback per hit: 80.0 (direction: away)
- [x] Attack executor integrates with FusionAttackFramework
  - Claw hitbox spawns at frame 6, 12, 18 (startup)
  - Each hit applies unique acid DoT via `AcidVFXSystem`
  - Acid modifier: `{ "acid_duration": 2.5, "acid_dps": 0.4 }`
- [x] DoT stacking verified: 3 simultaneous stacks visible in enemy debug display
  - Stacks do NOT refresh each other; each decays independently
  - Damage tick rate matches base acid (10Hz)
- [x] Attack feedback implemented:
  - Melee swipe sound triggers per hit
  - Poison VFX color overlay on enemy per applied stack
  - Knockback applies per hit
- [x] Attack balanced in test encounters
  - DPS: ~1.2 per combo at full 3 stacks (3 hits × 1.8 damage + 3 stacks × 0.4 acid DPS for 2.5s)
  - Cooldown enforces 2.0s between combos (prevents spam)
- [x] Attacks database entry created (`attacks.json`)
- [x] All M11 prerequisite tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration
- M12 ticket 03: fusion_attack_framework
- M11 ticket 04: attack_resource (base attack class)
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Hitbox timing critical: each swipe must trigger collision detection separately
- Acid stacking: use `AcidVFXSystem.apply_acid()` three times (once per hit) to ensure separate instances
- Cannot refresh existing poison stacks (unlike base acid attack which refreshes)
- Test framework: verify 3 poison stacks with `enemy.acid_stacks.size() == 3` after successful combo

## Example Attack Resource

```gdscript
[gd_resource type="AttackResource" format=3]

[resource]
attack_id = 109
attack_name = "Venomous Shred"
effect_type = "MELEE_SWIPE_COMBO"
damage = 1.8
cooldown = 2.0
range = 1.2
startup_frames = 6
knockback_magnitude = 80.0
knockback_direction = "away"
color = Color(0.6, 0.8, 0.1)
vfx_scale = 1.2
modifiers = {
  "combo_hits": 3,
  "hit_frames": [6, 12, 18],
  "acid_duration": 2.5,
  "acid_dps": 0.4
}
```
