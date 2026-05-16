# TICKET: 01_attack_resource_charge_properties

**Milestone:** M14 Charge & Hold Mechanics  
**Status:** Backlog  
**Type:** Implementation

## Title

Extend AttackResource with charge scaling properties

## Description

Extend AttackResource to support chargeable abilities (pattern from CarapaceHuskAttack). Add properties for charge accumulation and damage/knockback/range scaling curves.

Properties:
- `is_chargeable: bool` — ability can be held to charge
- `charge_min_duration: float` — minimum hold time before release (0.3s floor from ATS)
- `charge_max_duration: float` — max charge accumulation time
- `charge_damage_mult_curve: Curve` — damage multiplier vs charge progress (0.0 = no charge, 1.0 = full charge)
- `charge_knockback_mult_curve: Curve` — knockback scale vs charge
- `charge_range_mult_curve: Curve` — range scale vs charge (optional)
- `charge_speed: float` — how fast charge accumulates (charge units per second)

## Acceptance Criteria

- [x] AttackResource extended with chargeable properties (all typed, exported)
- [x] Curve properties support smooth scaling functions
- [x] Example: Carapace charge attack defined with realistic curves
- [x] Documentation explains charge semantics
- [x] Tests validate property access and curve evaluation
- [x] `run_tests.sh` exits 0

## Example: Carapace Charge

```gdscript
attack_id: 103
attack_name: "Carapace Charge"
effect_type: "MELEE_CHARGE"
is_chargeable: true
charge_min_duration: 0.3
charge_max_duration: 1.5
damage: 3.0  # Base damage at full charge
charge_damage_mult_curve: Curve([
  Vector2(0.0, 0.5),   # 50% damage at no charge
  Vector2(0.5, 0.8),   # 80% at half charge
  Vector2(1.0, 1.0)    # 100% at full charge
])
charge_knockback_mult_curve: Curve([
  Vector2(0.0, 0.3),
  Vector2(1.0, 1.0)
])
charge_range_mult_curve: Curve([
  Vector2(0.0, 0.8),
  Vector2(1.0, 1.5)
])
charge_speed: 1.0
cooldown: 1.2
```

## Dependencies

- M11_core_1_attack_resource (extend existing)
- M13_01_attack_resource_frame_data_extension (coordinate timing)

## Notes

- Charge curves allow non-linear scaling (e.g., rapid early gain, plateau late)
- Integration with M16 input buffering: don't lose charge on missed buffer window
- Integration with M20 UI: charge meter reflects current accumulation

