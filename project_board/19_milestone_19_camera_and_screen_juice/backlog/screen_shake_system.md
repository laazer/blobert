# TICKET: screen_shake_system

**Milestone:** M19 Camera and Screen Juice  
**Status:** Backlog  
**Type:** Implementation (Camera/Game Feel)

## Title

Screen shake system — trauma-based camera shake with decay

## Description

Implement trauma-based screen shake on Camera3D. Trauma value (0.0–1.0) accumulates from game events (damage, impacts, deaths) and decays over time. Shake = trauma². All parameters exported and tunable.

## Acceptance Criteria

- [x] Script: `scripts/camera/screen_shake.gd` attached to Camera3D
- [x] Trauma (0.0–1.0): `add_trauma(amount)`
- [x] Shake magnitude: trauma² (quadratic scaling)
- [x] Decay rate: configurable (default 1.0/sec)
- [x] Offset: X and Y position displacement (max 0.3 units exported)
- [x] Triggers: player damage, enemy death, impacts
- [x] No jitter when trauma = 0
- [x] All M1 camera tests pass, `run_tests.sh` exits 0

## Implementation

```gdscript
extends Camera3D
class_name ScreenShake

var trauma: float = 0.0
@export var max_shake: float = 0.3
@export var trauma_decay: float = 1.0

func add_trauma(amount: float):
    trauma = min(trauma + amount, 1.0)

func _process(delta):
    trauma = max(trauma - trauma_decay * delta, 0.0)
    var shake_mag = trauma * trauma
    offset = Vector3(
        randf_range(-shake_mag, shake_mag) * max_shake,
        randf_range(-shake_mag, shake_mag) * max_shake,
        0
    )
```

## Dependencies

- M1 (Camera system)

## Notes

- Trauma² provides good feel scaling (small trauma barely shakes)
- Decay makes shake naturally settle
- Offset (not rotation) feels better for 2.5D

## Dependencies

- M1 (basic camera follow must exist)
