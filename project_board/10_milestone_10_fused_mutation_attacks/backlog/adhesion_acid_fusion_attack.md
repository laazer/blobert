# TICKET: adhesion_acid_fusion_attack

Title: Adhesion + Acid fusion attack — sticky acid puddle

## Description

Fusing adhesion and acid creates an attack that fires a projectile landing as an acid puddle that also roots enemies standing in it. Combines immobilisation from adhesion with sustained damage from acid — neither base mutation alone can do both simultaneously.

## Acceptance Criteria

- Firing the attack launches a projectile that lands and creates a 2-unit radius acid puddle on the ground
- Enemies within the puddle radius are rooted (movement = 0) for as long as they remain in it
- Puddle deals DoT to enemies within it every 0.5s for its duration (5.0s)
- Puddle is visually distinct (acid + sticky colour blend)
- Attack cooldown: 4.0s
- `run_tests.sh` exits 0

## Dependencies

- `fusion_attack_framework`
