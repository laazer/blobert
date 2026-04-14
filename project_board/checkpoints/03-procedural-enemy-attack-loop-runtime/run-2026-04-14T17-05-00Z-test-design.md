# Scoped Checkpoint Log

Run: 2026-04-14T17-05-00Z-test-design  
Ticket: `project_board/10_milestone_10_procedural_enemies_in_level/in_progress/03_procedural_enemy_attack_loop_runtime.md`  
Stage: TEST_DESIGN

### [03_procedural_enemy_attack_loop_runtime] TEST_DESIGN — headless idle frames vs sync pump
**Would have asked:** Should multi-cycle attack tests rely on `SceneTree` idle/timer advancement (async `await`), or is a deterministic `_physics_process` + `AnimationPlayer.advance` pump acceptable under `run_tests.gd` synchronous `run_all()`?
**Assumption made:** Use the same sync integration style as `tests/scripts/enemy/test_attack_telegraph_system.gd`: attach nodes under `Engine.get_main_loop().root`, then pump `AcidSpitterRangedAttack._physics_process`, `EnemyAnimationController._physics_process`, and `AnimationPlayer.advance` with a bounded iteration cap. Completes telegraph via animation completion rather than requiring `SceneTreeTimer` ticks.
**Confidence:** High

### [03_procedural_enemy_attack_loop_runtime] TEST_DESIGN — `RunSceneAssembler` lifecycle in tests
**Would have asked:** Instantiating `RunSceneAssembler` runs `_ready()` → full run assembly if added to the tree; how should tests invoke `_spawn_generated_enemies_for_room` without duplicating spawn logic?
**Assumption made:** Construct `RunSceneAssembler` with `Script.new()`, assign `_enemy_visual_variant_selector` via `_build_enemy_visual_variant_selector()`, call `_spawn_generated_enemies_for_room`, then `free()` the assembler if it is not in the tree (orphan `Node` cleanup).
**Confidence:** High

### [03_procedural_enemy_attack_loop_runtime] TEST_DESIGN — strict host type vs duck typing
**Would have asked:** Should tests accept any duck-typed host that satisfies `get_esm()` + non-null attack `_enemy`, or require `EnemyInfection3D` explicitly?
**Assumption made:** Strictest defensible check aligned with ADR-M10-03-01: require `EnemyInfection3D` for integration tests that exercise M8 attack scripts, since those scripts cast `get_parent()` to `EnemyInfection3D` in `_ready()`.
**Confidence:** High
