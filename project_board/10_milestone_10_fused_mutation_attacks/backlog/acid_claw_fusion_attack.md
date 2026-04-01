# TICKET: acid_claw_fusion_attack

Title: Acid + Claw fusion attack — venomous shred

## Description

Fusing acid and claw creates a rapid melee attack that applies an acid DoT on every hit. Each claw swipe in the combo poisons the enemy, stacking DoT instances. Rewards staying in melee range for sustained damage.

## Acceptance Criteria

- Pressing attack fires a 3-hit melee combo (all hits at close range)
- Each hit applies a separate acid DoT instance (stacking, unlike base acid attack)
- 3 DoT stacks active simultaneously deal noticeably more damage than a single stack
- Attack cooldown: 2.0s
- `run_tests.sh` exits 0

## Dependencies

- `fusion_attack_framework`
