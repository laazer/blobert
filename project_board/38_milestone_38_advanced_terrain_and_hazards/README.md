# M38: Advanced Terrain & Hazards

**Status:** Planning  
**Depends:** M4 (Prototype Level)

## Overview

Formalize 8 procedurally-generated platform and hazard types from asset pipeline into first-class Godot scenes with behavior contracts. Support moving platforms, crumbling platforms, traps (spike, fire), ramps, and slope-aware navigation.

## Key Systems

- **8 platform/hazard types**: FlatPlatform, MovingPlatform, CrumblingPlatform, SolidWall, CrenellatedWall, SpikeTrap, FireTrap, Checkpoint
- **Moving platform API**: Speed, range, axis (extracted from asset metadata)
- **Hazard interactions**: Damage, cooldown, trigger conditions, particle effects
- **Slope support**: Angled platforms (15–45°) for vertical navigation
- **Mutation interactions**: Immunity, resistance, bonuses per hazard type

## Tickets

- 01_formalize_platform_types
- 02_moving_platform_controller
- 03_hazard_interaction_system
- 04_slope_and_ramp_support

