# TICKET: 01_directional_variant_framework

**Milestone:** M32 Direction-Aware Ability Variants  
**Status:** Backlog  
**Type:** Implementation

## Title

Directional Variant Framework — data-driven attack variants by input direction

## Description

Single ability ID can have multiple variants based on input direction (up/down/left/right/neutral) and locomotion state (grounded/aerial). AttackResource extended to support variant mapping. Executor selects variant before dispatch.

## Acceptance Criteria

- [x] AttackResource supports optional `variants: Dictionary[String, AttackResource]` (keys: "neutral", "up", "down", "aerial")
- [x] Variant selection logic: check input direction, then locomotion state, fall back to "neutral"
- [x] PlayerController checks direction before executing attack; passes chosen variant to executor
- [x] Unknown variant key falls back to base (neutral) gracefully, no crash
- [x] Variants serialize/deserialize with base attack in `.tres` resource files
- [x] Tests verify variant selection for all input combinations
- [x] `run_tests.sh` exits 0

## Dependencies

- M11 (AttackResource)
- M32 core (player locomotion state detection)

## Implementation Notes

**Variant selection pseudocode:**
```gdscript
func select_variant(attack: AttackResource, input_direction: Vector2, is_airborne: bool) -> AttackResource:
    var variant_key: String
    
    if is_airborne:
        variant_key = "aerial"
    elif input_direction.y > 0.5:
        variant_key = "up"
    elif input_direction.y < -0.5:
        variant_key = "down"
    else:
        variant_key = "neutral"
    
    if attack.variants.has(variant_key):
        return attack.variants[variant_key]
    
    return attack  # fallback to base
```

## Scope Notes

- No directional walk/strafe in this ticket (M6 handles movement)
- Variants can share cooldown or have independent cooldowns (document choice)

