# TICKET: 01_directional_variant_framework

**Milestone:** M15 Direction-Aware Ability Variants  
**Status:** Backlog  
**Type:** Implementation

## Title

Implement directional variant system for single ability ID

## Description

Formalize directional ability patterns from enemy attacks (signf() direction calculation, position-aware hitbox placement) into data-driven variant framework. Single attack_id can have:
- **Horizontal variant** (default): attack along X-axis (left/right)
- **Vertical variant**: attack along Y-axis (up/down)
- **Aerial variant**: different behavior when in air vs grounded
- **Slope variant** (optional): adjust positioning for terrain angle

Variants stored as child entries in AttackResource or separate keyed entries in AttackDatabase. PlayerController selects variant based on:
1. Current input direction (move_axis + jump state)
2. Current state (grounded, falling, wall-clinging)

## Acceptance Criteria

- [x] AttackResource supports variant definitions (horizontal/vertical/aerial keys)
- [x] Variant metadata (hitbox offset, range, angle) stored per variant
- [x] AttackDatabase.get_base_attack() enhanced to accept direction parameter
- [x] PlayerController detects input direction and selects appropriate variant
- [x] Falling/aerial state switches to aerial variant automatically
- [x] Wall-cling state supports wall-direction variants (attack into wall vs away)
- [x] Tests validate variant selection logic
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_core_1_attack_resource (extend)
- M11_core_3_attack_database_integration (enhance)
- M13_03_cancel_window_input_handling (directional input context)

## Data Structure

```gdscript
# AttackResource variants field (new)
variants: Dictionary[String, VariantData] = {
  "horizontal": VariantData(...),
  "vertical": VariantData(...),
  "aerial": VariantData(...)
}

class VariantData:
  effect_type: String      # Can override base
  hitbox_offset: Vector3   # Offset from player center
  damage_mult: float       # Damage multiplier vs base
  range_mult: float
  knockback_direction: String  # Can differ per variant
```

## Example: Claw with Variants

```gdscript
attack_id: 101
attack_name: "Claw Swipe"
effect_type: "MELEE_SWIPE"
damage: 2.0
variants: {
  "horizontal": {
    hitbox_offset: Vector3(1.5, 0.0, 0.0),
    damage_mult: 1.0,
    knockback_direction: "away"
  },
  "vertical": {
    hitbox_offset: Vector3(0.0, 1.5, 0.0),
    damage_mult: 0.8,  # Less damage upward
    knockback_direction: "away"
  },
  "aerial": {
    hitbox_offset: Vector3(1.2, 1.2, 0.0),
    damage_mult: 0.9,
    knockback_direction: "down"  # Different direction in air
  }
}
```

## Notes

- Variant selection happens in PlayerController._try_attack() before AttackExecutor.execute_attack()
- Preserve backward compatibility: attacks without variants use single hitbox/damage
- Coordinate with M18 aerial vs grounded mechanics

