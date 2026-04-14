# TICKET: 01_spec_procedural_enemy_spawn_attack_loop

Title: Specification — procedural enemy spawn points, scene selection, and attack-loop contract

## Description

Author `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md` that locks contracts before large implementation churn:

- How combat rooms declare **which** generated `.tscn`(s) to spawn (per-room list vs shared registry vs export from room template data).
- **Spawn anchor** naming and transform rules (Marker3D paths, floor height, Z=0 convention).
- Interaction with **RoomChainGenerator** / `RunSceneAssembler` — what is static in `.tscn` vs filled at runtime.
- **Attack loop** expectations per family (aggro range, cooldown bounds, relationship to `EnemyStateMachine` states WEAKENED/INFECTED).
- **Test plan** hooks for headless validation (minimal scene tree checks, file existence, optional physics-skipped patterns).

## Acceptance Criteria

- Spec file exists at `project_board/specs/procedural_enemy_spawn_attack_loop_spec.md`.
- Spec references current code paths (`run_scene_assembler.gd`, combat room scenes, `scenes/enemies/generated/`, enemy attack entry points).
- Ambiguities called out with ADR-style decisions where the repo already chose an approach.
- Downstream tickets (`02_wire_generated_enemies_combat_rooms`, `03_procedural_enemy_attack_loop_runtime`) can be implemented without re-negotiating spawn/attack contracts.

## Dependencies

- M5 / M6 / M8 — existing behavior to document
