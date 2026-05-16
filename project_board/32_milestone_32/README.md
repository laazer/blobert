# M32: Direction-Aware Ability Variants

**Status:** Planning  
**Depends:** M11-M31

## Overview

Single ability ID responds differently based on input direction and state (grounded/aerial). Extract directional patterns from enemy attacks (signf(), hitbox placement) into data-driven variant system.

## Key Patterns

- **Horizontal attacks**: adjusted for facing direction
- **Vertical attacks**: different from horizontal (slash vs upward swipe)
- **Aerial variants**: same ability behaves differently in air vs grounded
- **Slope awareness**: attacks adjust for terrain angle

## Tickets

- 01_directional_variant_framework
- 02_implement_grounded_vs_aerial
- 03_slope_aware_attack_positioning
- 04_verify_directional_responsiveness
