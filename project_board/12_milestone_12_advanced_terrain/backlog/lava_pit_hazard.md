# TICKET: lava_pit_hazard

Title: Lava pit hazard — continuous burn damage, carapace mutation reduces damage

## Description

Create a lava pit scene: a floor-level area that continuously deals burn damage to the player while standing in it. The carapace mutation reduces damage taken by 75%. Lava pits are placeable in room templates.

## Acceptance Criteria

- `scenes/hazards/lava_pit.tscn` exists and is a self-contained placeable scene
- Player takes 5 damage per second while inside lava pit Area3D
- Player with active carapace mutation takes 1.25 damage per second (75% reduction)
- Damage ticks every 0.5s (not every frame)
- Lava pit has a distinct glowing/hot visual
- Scene can be placed in any room template without code changes
- `run_tests.sh` exits 0

## Dependencies

- M4 (Prototype Level) — collision and physics baseline
