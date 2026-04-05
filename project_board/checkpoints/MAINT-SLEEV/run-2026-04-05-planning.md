# MAINT-SLEEV — sandbox_scene_legacy_external_enemy_visuals

Run started 2026-04-05 (autopilot maintenance backlog).

## Checkpoint (Planner Agent — 2026-04-05)

**Exploration summary**

- `scenes/levels/sandbox/test_movement_3d.tscn`: root `TestMovement3D`; four instances of `enemy_infection_3d.tscn` (`AdhesionBugEnemy`, `AcidSpitterEnemy`, `ClawCrawlerEnemy`, `CarapaceHuskEnemy`) each set `mutation_drop` and `model_scene` to one of four `res://assets/enemies/generated_glb/*_animated_00.glb` PackedScenes (`ext_resource` ids 7–10). Same structure otherwise: `SceneVariantController`, `InfectionInteractionHandler`, `WorldEnvironment`, light, floor, `SpawnPosition`, `InfectionUI` (`game_ui.tscn`), `RespawnZone`, `Player3D`.
- `scenes/enemy/enemy_infection_3d.tscn`: default child `EnemyVisual` instances `res://assets/Models/gobot/model/gobot.glb` (third-party mesh).
- `scripts/enemy/enemy_infection_3d.gd`: `@export var model_scene: PackedScene = null`; in `_ready`, if `model_scene != null`, deferred `_swap_model_scene()` removes `EnemyVisual` and instantiates `model_scene` as new `EnemyVisual`; else deferred `_wire_and_notify_animation()` only.

**Outcome**

- Added `## Execution Plan` table to the ticket (tasks 1–5: Spec → Test Designer → Test Breaker → Implementation Generalist → Static QA / gatekeeper).
- Workflow: Stage `SPECIFICATION`, Revision `2`, Last Updated By `Planner Agent`, Next `Spec Agent`, Status `Proceed`.

**Log:** `project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md`
