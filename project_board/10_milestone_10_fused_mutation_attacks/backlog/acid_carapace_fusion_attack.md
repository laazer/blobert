# TICKET: acid_carapace_fusion_attack

Title: Acid + Carapace fusion attack — corrosive slam

## Description

Fusing acid and carapace creates a ground slam that leaves a persistent acid pool at the impact point. Combines the area denial of acid with the impact force of carapace. Enemies knocked into the pool take immediate knockback AND start taking DoT.

## Acceptance Criteria

- Pressing attack triggers a ground slam (same radius as base carapace slam)
- On impact, an acid pool spawns at the slam point and persists for 6.0s
- Enemies hit by the slam are knocked into/toward the pool
- Enemies in the pool take DoT every 0.5s
- Attack cooldown: 4.5s
- `run_tests.sh` exits 0

## Dependencies

- `fusion_attack_framework`
