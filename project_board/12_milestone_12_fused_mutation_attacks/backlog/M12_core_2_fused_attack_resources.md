# TICKET: M12_core_2_fused_attack_resources

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Create fused attack resource files (`.tres`) for all 6 combos

## Description

Define all 6 unordered fusion combinations as AttackResource `.tres` files:
1. Claw + Acid
2. Claw + Carapace
3. Claw + Adhesion
4. Acid + Carapace
5. Acid + Adhesion
6. Carapace + Adhesion

Each fused attack is data-driven using the same AttackResource model from M11. Fused attacks may have:
- Different effect_type (e.g., combined melee + projectile hybrid)
- Different damage/cooldown (typically stronger than base, longer cooldown)
- Custom modifiers (combined effects from both base mutations)
- Unique VFX colors/scales representing the fusion

Store in `res://attacks/fused/` directory for AttackDatabase to load.

## Acceptance Criteria

- [x] All 6 fused attack `.tres` files created in `res://attacks/fused/`
- [x] Each fused attack inherits from AttackResource
- [x] All properties defined (effect_type, damage, cooldown, range, knockback, color, modifiers)
- [x] Fused attacks represent meaningful fusion (not identical to base)
- [x] AttackDatabase can load all fused attacks
- [x] Tests validate all 6 fused attacks load correctly
- [x] `run_tests.sh` exits 0

## Example Fused Attacks

**Claw + Acid Fusion (e.g., "Toxic Slash"):**
```
attack_id: 201
attack_name: "Toxic Slash"
effect_type: "MELEE_SWIPE"
damage: 3.0 (stronger than Claw 2.0)
cooldown: 1.2
range: 1.8
knockback_magnitude: 120.0
color: Color(0.6, 0.5, 0.0)  # yellow-green (claw + acid)
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.0,
  "acid_dps": 0.4
}
```

**Acid + Carapace Fusion (e.g., "Corrosive Shell"):**
```
attack_id: 205
attack_name: "Corrosive Shell"
effect_type: "PROJECTILE_SPIT"
damage: 2.0
cooldown: 1.5
projectile_speed: 200.0
knockback_magnitude: 80.0
color: Color(0.3, 0.7, 0.1)  # acid-dominant with shell hint
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.5,
  "acid_dps": 0.5,
  "defense_bonus": 0.1  # from carapace
}
```

## Dependencies

- M11_core_1_attack_resource (attack data model)
- M12 attack design spec (cooldown/damage balance)

## Notes

- Balance fused attacks to be meaningfully different from base (design choice)
- Color should reflect both component mutations for visual clarity
- Can be created as .tres files manually or programmatically after initial data is defined

