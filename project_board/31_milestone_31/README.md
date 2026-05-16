# M31: Charge & Hold Mechanics

**Status:** Planning  
**Depends:** M11, M12, M30

## Overview

Formalize charge/hold ability mechanics from CarapaceHuskAttack into reusable player ability system. Abilities can accumulate damage/knockback/range based on button hold duration before release.

## Key Patterns from Codebase

- **CarapaceHuskAttack**: Charge speed, max charge distance, deceleration phase
- **Telegraph hold**: Minimum hold time before activation (ATS pattern, 0.3s floor)
- **Charge scaling**: Damage, knockback, range increase with charge level

## Tickets

- 01_attack_resource_charge_properties
- 02_charge_accumulation_system
- 03_charge_release_dispatch
- 04_verify_charge_feel_and_balance
