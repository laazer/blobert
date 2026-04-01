# TICKET: adhesion_carapace_fusion_attack

Title: Adhesion + Carapace fusion attack — armoured lunge slam

## Description

Fusing adhesion and carapace creates a charging slam that briefly makes the player invincible during the lunge. Blobert charges forward, is invulnerable mid-lunge, and on hit deals heavy damage with a large knockback. The invincibility window is unique to this fusion.

## Acceptance Criteria

- Pressing attack initiates a forward lunge along the X axis
- Player is invulnerable to damage for the duration of the lunge (immunity window)
- On enemy contact, enemy takes heavy damage and is knocked back significantly
- Lunge travels a fixed distance (configurable, default 5 units) even with no enemy hit
- Attack cooldown: 5.0s
- `run_tests.sh` exits 0

## Dependencies

- `fusion_attack_framework`
