# TICKET: 03_slope_aware_attack_positioning

**Milestone:** M32 Direction-Aware Ability Variants  
**Status:** Backlog  
**Type:** Implementation

## Title

Slope-Aware Attack Positioning — adjust hitbox angle for terrain slope

## Description

When player is on a slope (15–45°), adjust attack hitbox normal and position to align with slope angle. Melee attacks stay perpendicular to slope; projectiles travel up-slope or down-slope as appropriate.

## Acceptance Criteria

- [x] PlayerController exposes current floor slope angle (from raycast or physics query)
- [x] Attack executor reads slope angle; applies rotation to hitbox
- [x] Melee hitbox rotates to align normal perpendicular to slope (not horizontal)
- [x] Projectiles inherit initial velocity along slope (not purely horizontal)
- [x] Flat ground (slope ~0°) uses unmodified hitbox
- [x] Steep slope (>45°) clamps slope angle to 45° or documents clamp behavior
- [x] Tests verify slope detection and hitbox rotation
- [x] `run_tests.sh` exits 0

## Dependencies

- M32:02 (grounded state)
- M6 (movement with slope detection)

## Implementation Notes

**Slope-aware hitbox:**
```gdscript
func rotate_hitbox_for_slope(hitbox: Area3D, slope_angle: float):
    hitbox.rotation.z = slope_angle
    # or use quaternion for smooth multi-axis rotation
```

**Projectile slope adjustment:**
```gdscript
var base_velocity = Vector3(1, 0, 0) * projectile_speed
var slope_rad = deg_to_rad(slope_angle)
var slope_velocity = base_velocity.rotated(Vector3.forward, slope_rad)
```

## Scope Notes

- Slope angle extracted from floor raycast result
- No per-vertex slope (simplified to floor angle)

