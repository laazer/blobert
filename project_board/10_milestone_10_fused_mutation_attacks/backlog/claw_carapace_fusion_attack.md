# TICKET: claw_carapace_fusion_attack

Title: Claw + Carapace fusion attack — armoured flurry charge

## Description

Fusing claw and carapace creates a charging flurry: Blobert charges forward and delivers rapid claw hits to every enemy along the path. Combines the multi-hit nature of claw with the movement of carapace's charge. Hits all enemies in a line — impossible with either base mutation.

## Acceptance Criteria

- Pressing attack initiates a forward charge along the X axis
- Every enemy along the charge path takes 3 rapid hits as Blobert passes through
- Charge travels a fixed distance (configurable, default 6 units)
- Enemies are hit in sequence; multiple enemies in the path all receive damage
- Attack cooldown: 4.0s
- `run_tests.sh` exits 0

## Dependencies

- `fusion_attack_framework`
