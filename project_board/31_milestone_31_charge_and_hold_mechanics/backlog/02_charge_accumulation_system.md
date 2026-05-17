# TICKET: 02_charge_accumulation_system

**Milestone:** M31 Charge & Hold Mechanics  
**Status:** Backlog  
**Type:** Implementation

## Title

Charge Accumulation System — button hold detection and charge level scaling

## Description

Implement charge meter that accumulates while button is held. Charge level (0.0–1.0) determines damage/knockback/range multipliers applied to the attack. Must detect minimum hold time (telegraph window) before charge becomes "active" and visible.

## Acceptance Criteria

- [x] Pressing attack button + holding starts a charge meter
- [x] Charge accumulates per frame: `charge_level = min(hold_duration / max_charge_time, 1.0)`
- [x] Minimum hold time before charge is active (default ~0.3s, exported)
- [x] Charge level visible in UI during hold (M37 integration)
- [x] Holding past max_charge_time caps at 1.0 (no overshoot)
- [x] Releasing button during hold triggers charge dispatch (M31:03)
- [x] Button released outside min_hold_time cancels charge (attack doesn't fire)
- [x] Tests verify accumulation rate and min/max bounds
- [x] `run_tests.sh` exits 0

## Dependencies

- M31:01 (AttackResource charge properties)
- M30 (frame timing — optional but recommended for cancel window integration)

## Implementation Notes

**GDScript pseudocode:**
```gdscript
var charge_level: float = 0.0
var hold_start_time: float = 0.0
var is_charging: bool = false

func _process(delta):
    if Input.is_action_pressed("attack"):
        if not is_charging:
            hold_start_time = get_tree().get_elapsed_time()
            is_charging = true
        
        var hold_duration = get_tree().get_elapsed_time() - hold_start_time
        charge_level = min(hold_duration / max_charge_time, 1.0)
        
        if hold_duration >= min_hold_time:
            show_charge_meter(charge_level)
    
    elif is_charging:
        if hold_duration >= min_hold_time:
            dispatch_charged_attack(charge_level)
        is_charging = false
        charge_level = 0.0
```

## Scope Notes

- No visual charge bar filling (M37 owns UI)
- No audio feedback for charge milestones (future)

