# TICKET: 04_attack_resource

**Milestone:** M11 Base Mutation Attacks (Core Foundation)  
**Status:** Ready  
**Type:** Implementation

## Title

Implement AttackResource Godot resource class

## Description

Create the data model for all attacks (base and fused). AttackResource is a Godot Resource that defines:
- Effect type (MELEE_SWIPE, PROJECTILE_SPIT, etc.)
- Core parameters (damage, cooldown, range, knockback)
- Visual feedback (color, VFX scale)
- Extensible modifiers (poison duration, acid DPS, etc.)

This is the foundation for data-driven attack dispatch — no code changes to handlers needed for new attacks.

## Acceptance Criteria

- [x] `AttackResource` class created (`scripts/attacks/attack_resource.gd`)
- [x] All properties exported and typed:
  - `attack_id: int`
  - `attack_name: String`
  - `effect_type: String` (enum-like: "MELEE_SWIPE", "PROJECTILE_SPIT", etc.)
  - `damage: float`
  - `cooldown: float`
  - `range: float`
  - `startup_frames: int`
  - `knockback_magnitude: float`
  - `knockback_direction: String` ("away", "toward", "none")
  - `projectile_speed: float` (if applicable)
  - `color: Color`
  - `vfx_scale: float`
  - `modifiers: Dictionary` (extensible key-value pairs)
- [x] Class documented with examples (Claw, Acid, Carapace, Adhesion)
- [x] Modifiers system documented (poison, acid, slow, etc.)
- [x] Tests validate property access and serialization
- [x] `run_tests.sh` exits 0

## Dependencies

- None (foundational)

## Example Resource Properties

**Claw Swipe:**
```
attack_id: 101
attack_name: "Claw Swipe"
effect_type: "MELEE_SWIPE"
damage: 2.0
cooldown: 0.8
range: 1.5
knockback_magnitude: 100.0
knockback_direction: "away"
color: Color(0.8, 0.2, 0.1)
modifiers: {}
```

**Acid Spit:**
```
attack_id: 102
attack_name: "Acid Spit"
effect_type: "PROJECTILE_SPIT"
damage: 1.5
cooldown: 1.2
projectile_speed: 250.0
knockback_magnitude: 50.0
color: Color(0.2, 0.8, 0.1)
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.0,
  "acid_dps": 0.3
}
```

## Notes

- Resource can be instantiated in code or created as .tres files (decide later)
- Modifiers are schemaless (any key-value pair allowed) for flexibility
- Future: charge scaling can be added as optional `is_chargeable` and `max_charge_mult`
