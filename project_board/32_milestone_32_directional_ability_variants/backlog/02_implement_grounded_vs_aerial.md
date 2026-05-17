# TICKET: 02_implement_grounded_vs_aerial

**Milestone:** M32 Direction-Aware Ability Variants  
**Status:** Backlog  
**Type:** Implementation

## Title

Implement Grounded vs Aerial Variants — distinct attacks for air/ground state

## Description

Implement executor logic to detect locomotion state and select correct variant. Define at least one test mutation (e.g., Claw) with distinct ground and aerial attacks. Ground attack is melee swipe; aerial attack is slower, wider arc or downward slam.

## Acceptance Criteria

- [x] PlayerController exposes `is_airborne()` getter (from movement simulation)
- [x] Attack execution checks airborne state before variant selection
- [x] At least one mutation (Claw) has distinct grounded and aerial variants
- [x] Grounded Claw: fast 1.8 damage horizontal swipe, range 1.2
- [x] Aerial Claw: 2.0 damage downward slam, range 1.5, slightly longer startup
- [x] Hitbox placement differs per variant (horizontal vs downward)
- [x] Tests verify variant dispatch for both states
- [x] `run_tests.sh` exits 0

## Dependencies

- M32:01 (variant framework)
- M6 (movement simulation with airborne detection)

## Implementation Notes

**Variant registration:**
```gdscript
claw_attack.variants = {
    "neutral": claw_grounded,      # 1.8 dmg, swipe
    "aerial": claw_aerial           # 2.0 dmg, slam
}
```

**Hitbox position for aerial:**
- Spawn below player at half-height (downward cone)
- Active frames detect enemies in downward radius

## Scope Notes

- Slope detection separate (M32:03)
- No mid-air momentum changes (just hitbox difference)

