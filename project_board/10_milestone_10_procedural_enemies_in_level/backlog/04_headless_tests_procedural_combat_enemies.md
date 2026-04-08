# TICKET: 04_headless_tests_procedural_combat_enemies

Title: Headless tests — procedural combat rooms contain loadable generated enemies

## Description

Add focused tests that **do not require** a full physics playthrough where the harness cannot support it. Prefer: load combat room `PackedScene`, find spawn roots or deferred spawn logic, assert expected generated enemy scene paths or `enemy_family` exports, and register in `tests/run_tests.gd` per existing patterns.

Optional second file: adversarial tests for missing markers, empty spawn lists, or invalid `res://` paths (must fail gracefully or error in a defined way).

## Acceptance Criteria

- New test module(s) under `tests/` exercise at least one combat room scene used in `RunSceneAssembler.POOL["combat"]` together with generated enemy scene paths.
- Tests follow project skip/physics patterns from `tests/scenes/levels/test_3d_scene.gd` where needed to avoid hangs.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.
- Tests reference this ticket path in a header comment: `project_board/10_milestone_10_procedural_enemies_in_level/backlog/04_headless_tests_procedural_combat_enemies.md`.

## Dependencies

- `02_wire_generated_enemies_combat_rooms` — stable scene paths and spawn contract to assert against
- `01_spec_procedural_enemy_spawn_attack_loop` (soft — tests should align with spec IDs if present)
