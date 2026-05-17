# TICKET: 03_charge_release_dispatch

**Milestone:** M31 Charge & Hold Mechanics  
**Status:** Backlog  
**Type:** Implementation

## Title

Charge Release Dispatch — execute attack with charge-scaled multipliers

## Description

When charge is released, dispatch the attack with damage/knockback/range scaled by charge_level. AttackExecutor must apply multipliers derived from the charge attack resource properties, interpolating between base and max values.

## Acceptance Criteria

- [x] AttackResource extended with: `charge_damage_mult` (default 1.0→1.8), `charge_knockback_mult` (1.0→2.2), `charge_range_mult` (1.0→1.5)
- [x] On charge release, calculate effective damage: `base_damage * (1.0 + (charge_damage_mult - 1.0) * charge_level)`
- [x] Same scaling applied to knockback and range (or document alternative formula)
- [x] Charge-scaled attack executes with hitbox at correct range
- [x] Knockback direction respects charge (scaled, not redirected)
- [x] Tests verify linear interpolation of multipliers across charge range
- [x] `run_tests.sh` exits 0

## Dependencies

- M31:02 (charge accumulation)
- M30 (frame timing — use for charge attack startup/endlag)

## Implementation Notes

**Multiplier formula (example):**
```
effective_multiplier = 1.0 + (max_mult - 1.0) * charge_level
base_stat = resource.damage
final_stat = base_stat * effective_multiplier
```

**Knockback scaling preserves direction:**
```gdscript
func get_charged_knockback(base_knockback: Vector3, charge_level: float) -> Vector3:
    var mult = 1.0 + (charge_knockback_mult - 1.0) * charge_level
    return base_knockback * mult
```

## Scope Notes

- No momentum carry-over from charge (future optimization)
- Charge attack counts as single attack for cooldown (not multiple hits)

