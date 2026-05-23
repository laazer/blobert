# M11-02 — Test Design run

**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/02_physics_frame_order.md`  
**Stage:** TEST_DESIGN → TEST_BREAK  
**Agent:** Test Designer Agent  
**Date:** 2026-05-23

## Deliverables

| Artifact | Path |
|----------|------|
| Primary behavioral tests | `tests/scripts/player/test_player_physics_frame_order.gd` |
| Spec | `project_board/specs/player_physics_frame_order_spec.md` |

Adversarial suite (`test_player_physics_frame_order_adversarial.gd`) deferred to Test Breaker per execution plan Task 3.

## Test run evidence (RED)

Command:

```bash
timeout 300 godot --headless --path . -s tests/run_tests.gd
```

Suite excerpt (`test_player_physics_frame_order.gd`):

```
--- test_player_physics_frame_order.gd ---
  FAIL: pfo3_export_default — @export jump_buffer_time missing on PlayerController3D
  FAIL: pfo3_reset_clears_buffer — jump_buffer_time export missing
  FAIL: pfo3_buffer_landing_jump — jump_buffer_time export missing
  FAIL: pfo9_buffer_disabled_at_zero — jump_buffer_time export missing
  FAIL: pfo4_coyote_off_ledge — (settle / coyote — see run)
  FAIL: pfo7_mask_accessor — get_one_way_collision_mask() missing
  FAIL: pfo7_mask_ascending — get_one_way_collision_mask() missing
  FAIL: pfo7_mask_descending — get_one_way_collision_mask() missing
  FAIL: pfo7_pass_through_below — get_one_way_collision_mask() missing
  FAIL: pfo7_is_on_floor_true_after_falling_onto_one_way_platform — expected true, got false
  FAIL: pfo11_fixture_exists — fixture scene missing
  FAIL: pfo11_fixture_nodes — fixture scene missing
  FAIL: pfo10_method_func _tick_controller_timers — missing in player_controller_3d.gd

  Results: 0 passed, 13 failed
```

**Interpretation:** All primary contract tests are RED against current `PlayerController3D` (no jump buffer, no one-way mask pipeline, no fixture scene, no extracted step methods). Integration harness uses `test_movement_3d.tscn` for reliable headless physics.

## Spec ↔ test traceability

| Spec | Tests |
|------|-------|
| PFO-3 / AC-PFO-3.1–3.4 | `test_pfo3_*`, `test_pfo9_*` |
| PFO-4 / AC-PFO-4.3 | `test_pfo4_coyote_jump_within_window_after_walking_off_ledge` |
| PFO-7 / AC-PFO-7.1–7.5 | `test_pfo7_*` |
| PFO-10 / AC-PFO-10.1 | `test_pfo10_private_pipeline_methods_declared` |
| PFO-11 / AC-PFO-11.1–11.2 | `test_pfo11_*` |

## Handoff notes for Test Breaker

- Add `tests/scripts/player/test_player_physics_frame_order_adversarial.gd` per spec Test Strategy (buffer expiry, mask at vy==0, buffer+coyote, reorder regressions).
- Mark conservative assumptions with `# CHECKPOINT` where spec is silent.
- Do not add prose/markdown asserts; runtime only.
