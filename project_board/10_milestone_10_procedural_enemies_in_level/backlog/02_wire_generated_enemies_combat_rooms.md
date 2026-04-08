# TICKET: 02_wire_generated_enemies_combat_rooms

Title: Wire generated enemy scenes into combat room templates for procedural runs

## Description

Combat rooms loaded by `RunSceneAssembler` (`res://scenes/rooms/room_combat_*.tscn`) must spawn **game-ready generated enemy scenes** from `res://scenes/enemies/generated/` (or the current canonical output of `generate_enemy_scenes.gd`), not ad-hoc placeholders. Placement uses existing room conventions (e.g. `Marker3D` spawn anchors or documented node paths) so enemies appear at stable positions when the room is instantiated during a run.

Define which **enemy_id / family** each combat template uses (at least one variant per family intended for M10), and ensure instances are `EnemyInfection3D` (or the agreed wrapper) with correct collision layers, `enemy_family`, `mutation_drop`, and animation root wiring consistent with M5/M7.

## Acceptance Criteria

- At least one `room_combat_*.tscn` used in `RunSceneAssembler.POOL["combat"]` instantiates enemies from **generated** `.tscn` paths (not legacy generic enemy stubs), or a small documented spawn helper under the room root achieves the same at `_ready()`.
- Spawned enemies load without error when the full run sequence is started from the main game path (no editor-only manual instance requirement).
- `enemy_id` / `enemy_family` / `mutation_drop` match the generated scene contract used elsewhere (see `tests/scenes/enemies/` patterns).
- `timeout 300 ci/scripts/run_tests.sh` exits 0 (new or updated tests as needed).

## Dependencies

- `01_spec_procedural_enemy_spawn_attack_loop` (soft if spec and impl are parallelized — prefer spec first)
- M5 — generated scenes and `EnemyBase` metadata
- M6 — `RunSceneAssembler` / room pool
- M9 — coordinate mesh/material readiness (soft; wiring may land before final art)
