# M30: Attack Frame Timing & Cancel Windows

**Status:** Planning  
**Depends:** M11, M12

## Overview

Formalize attack frame timing patterns found in enemy attacks into reusable components for player abilities. Extend AttackResource with startup/active/endlag frames and implement cancel window logic for responsive combos.

## Key Concepts

- **Startup frames**: Windupphase before damage applies (telegraph)
- **Active frames**: Damage/effect window when hitbox is live
- **Endlag frames**: Recovery time after attack ends
- **Cancel windows**: Frames during which input can transition to next action
- **Frame data**: Declarative attack timing metadata

## Tickets

- 01_attack_resource_frame_data_extension
- 02_attack_executor_frame_window_dispatch
- 03_cancel_window_input_handling
- 04_verify_frame_timing_and_combos

