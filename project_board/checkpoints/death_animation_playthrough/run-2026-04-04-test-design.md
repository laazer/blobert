# Checkpoint log — death_animation_playthrough — run-2026-04-04-test-design

### [death_animation_playthrough] TEST_DESIGN — suite layout
**Assumption made:** Primary coverage split across `tests/scenes/enemies/test_death_animation_playthrough.gd` (generated scenes + real `EnemyStateMachine` via `EnemyAnimationController.setup`), `tests/scripts/enemy/test_death_animation_playthrough_infection.gd` (chunk / handler / unload smoke), and `test_enemy_animation_controller.gd` EAC-23 for DAP-2.1 latch vs state flip.
**Confidence:** High

### [death_animation_playthrough] TEST_DESIGN — DAP-1.6 vs InfectionUI
**Would have asked:** Headless tests cannot rely on deferred `_ready` after `add_child` to `SceneTree` without idling the main loop; `InfectionInteractionHandler` needs `_inventory` before `get_mutation_inventory()` works.
**Assumption made:** DAP-1.4/1.5 use detached handler + manual `_ready()` (same pattern as `test_soft_death_and_restart.gd` `_make_iih_ready`). DAP-1.6 asserts `InfectionAbsorbResolver.can_absorb(dead_esm) == false`, matching the predicate used in `_process` for `set_absorb_available`.
**Confidence:** High

### [death_animation_playthrough] TEST_DESIGN — `run_tests.gd` outcome
**Assumption made:** Expected red: DAP-1.1 (no `queue_free` after Death) × four family scenes; DAP-1.2 (collision not cleared). Infection-side tests green against current code.
**Confidence:** High
