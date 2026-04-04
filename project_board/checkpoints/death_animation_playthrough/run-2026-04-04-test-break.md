# Checkpoint log — death_animation_playthrough — run-2026-04-04-test-break

**Agent:** Test Breaker Agent  
**Scope:** Adversarial suite extension per execution plan task 3 (double events, missing clip, freed `AnimationPlayer`, concurrent completion signals, mini-boss naming).

### Delivered

- New suite: `tests/scenes/enemies/test_death_animation_playthrough_adversarial.gd` (auto-discovered by `tests/run_tests.gd`).
- Tests marked `# CHECKPOINT` tie to planning / execution-plan themes (double lifecycle, freed nodes, missing clip, concurrent signals, mini-boss parity).

### Assumption made

- **Handler `_ready()`:** `InfectionInteractionHandler._ready()` still calls `get_tree()` on an orphan node (engine error at default level); existing pattern from `test_soft_death_and_restart.gd` retained. Implementer may later guard with `is_inside_tree()` outside this ticket.
- **Concurrent signal demo:** `RefCounted` inner class + `signal` + `Array` capture for lambdas (plain `int` capture did not increment in headless Godot 4.6.1).

### Test outcome (pre-implementation)

- `timeout 180 godot --headless --path . -s tests/run_tests.gd` → **7** failing assertions, all expected until engine-integration implements DAP-1.1 / DAP-1.2 (post–`Death` `queue_free`, collision clear): six from `test_death_animation_playthrough.gd`, one from `test_adv_mini_boss_name_death_queue_after_animation` (CHECKPOINT mini-boss).
- Missing-clip adversarial test triggers engine **ERROR** `Animation not found: Death` on first `play()` — documents spec DAP-2 / WAGS dependency; assertions still pass (no hang/crash in loop).

### Confidence

High on coverage matrix rows; medium on long-term cleanliness of IIH orphan `_ready()` log noise (gameplay guard vs test harness).
