# TICKET: adhesion_claw_fusion_attack

Title: Adhesion + Claw fusion attack — grapple and shred

## Description

Fusing adhesion and claw creates a grapple attack: Blobert fires a sticky tendril that pulls the first enemy toward the player, then immediately applies a multi-hit shred on arrival. The pull + instant melee combo is impossible with either base mutation alone.

## Acceptance Criteria

- Pressing attack fires a tendril projectile
- On enemy hit, enemy is pulled to within melee range of the player over 0.4s
- On arrival, 3 rapid claw hits are applied automatically (no additional input)
- Enemy takes all 3 hits unless it dies first
- Attack cooldown: 3.5s
- `run_tests.sh` exits 0

## Dependencies

- `fusion_attack_framework`
