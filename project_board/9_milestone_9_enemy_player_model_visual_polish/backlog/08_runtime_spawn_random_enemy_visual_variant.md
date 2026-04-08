# TICKET: 08_runtime_spawn_random_enemy_visual_variant

Title: Runtime — random visual variant per enemy type among active in-use versions

## Description

When spawning an enemy of a given **type/family**, choose **uniformly or weighted-random** among **in-use** version entries in the registry (same `EnemyBase` / collision / animation contract; different GLB/visual only). If exactly one version exists, behavior matches today. Integrate at the **single spawn choke point** used by procedural runs and sandbox (coordinate with M10 `02_wire_generated_enemies_combat_rooms` and follow-on spawn helpers).

## Acceptance Criteria

- Two consecutive spawns of the same type can yield different visuals when multiple versions are registered (manual or automated note).
- Draft models never selected.
- `timeout 300 ci/scripts/run_tests.sh` exits 0 (unit or scene test where feasible).

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `05_editor_ui_game_model_selection` (registry must hold version lists)
- M10 — `02_wire_generated_enemies_combat_rooms` (soft; sandbox can prove behavior first)
