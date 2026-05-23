# M11-02 — Test Break run

**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/02_physics_frame_order.md`  
**Stage:** TEST_BREAK → IMPLEMENTATION_GENERALIST  
**Agent:** Test Breaker Agent  
**Date:** 2026-05-23

## Deliverables

| Artifact | Path |
|----------|------|
| Adversarial behavioral tests | `tests/scripts/player/test_player_physics_frame_order_adversarial.gd` |
| Primary suite (unchanged) | `tests/scripts/player/test_player_physics_frame_order.gd` |
| Spec | `project_board/specs/player_physics_frame_order_spec.md` |

## Adversarial coverage matrix

| Test ID | Dimension | Vulnerability probed |
|---------|-----------|----------------------|
| TB-PFO-001 | Boundary | Buffer expiry at 0.1s — landing after timer exhausted must not jump |
| TB-PFO-002 | Boundary | Buffer still valid one frame before expiry (short fall) |
| TB-PFO-003 | Invalid config | Negative `jump_buffer_time` treated as disabled |
| TB-PFO-004 | Assumption | `enemy_movement_root` suppresses buffer accumulation (EC-10) |
| TB-PFO-005 | Boundary | Coyote denied after 0.1s airborne without press |
| TB-PFO-006 | Combinatorial | Coyote jump + buffer must not double-jump on landing (EC-11) |
| TB-PFO-007 | Combinatorial | Double air-press within buffer window → single landing jump |
| TB-PFO-008 | Assumption | Grounded single press → single upward impulse (PFO-5.4) |
| TB-PFO-009 | Mutation | Mask must be ground-only every ascending frame (EC-12 partial) |
| TB-PFO-010 | Boundary | Mask includes one-way at vy≤0 on floor (EC-6 / apex) |
| TB-PFO-011 | Order | Mask full while falling toward one-way before land |
| TB-PFO-012 | Reorder regression | Ascending pass-through — no stall below one-way lip (EC-12) |

`# CHECKPOINT` markers: TB-PFO-002 (frame-count boundary vs wall-clock 0.1s).

## Test run evidence (RED)

Command:

```bash
timeout 300 godot --headless --path . -s tests/run_tests.gd
```

Primary suite excerpt:

```
--- test_player_physics_frame_order.gd ---
  FAIL: pfo3_export_default — @export jump_buffer_time missing on PlayerController3D
  ...
  Results: 0 passed, 13 failed
```

Adversarial suite excerpt:

```
--- test_player_physics_frame_order_adversarial.gd ---
  FAIL: tb_pfo_001 — jump_buffer_time export missing
  FAIL: tb_pfo_002 — jump_buffer_time export missing
  FAIL: tb_pfo_003 — jump_buffer_time export missing
  FAIL: tb_pfo_004 — jump_buffer_time export missing
  FAIL: tb_pfo_005 — player did not settle
  FAIL: tb_pfo_006 — jump_buffer_time export missing
  FAIL: tb_pfo_007 — jump_buffer_time export missing
  FAIL: tb_pfo_008 — jump_buffer_time export missing
  FAIL: tb_pfo_009 — get_one_way_collision_mask() missing
  FAIL: tb_pfo_010 — get_one_way_collision_mask() missing
  FAIL: tb_pfo_011 — get_one_way_collision_mask() missing
  FAIL: tb_pfo_012 — get_one_way_collision_mask() missing

  Results: 0 passed, 12 failed
```

**Combined RED:** 25 failures (13 primary + 12 adversarial). All runtime behavior asserts; no prose/markdown contracts.

## Implementation notes for Gameplay Systems Agent

1. Implement PFO-2 pipeline steps with private methods per PFO-10.
2. Add `jump_buffer_time` export + `_jump_buffer_timer`; clear on `reset_hp()` / `reset_position()`.
3. Add `get_one_way_collision_mask()` test accessor; mask from post-dispatch `velocity.y` before `move_and_slide()`.
4. Create `scenes/levels/sandbox/test_one_way_platform_3d.tscn` fixture (PFO-11).
5. Declare physics layer names in `project.godot` (PFO-6).
6. TB-PFO-005 settle failure may resolve once harness collision state is stable post-refactor; primary `pfo4_coyote` also failed settle in current tree.

## Handoff

Stage → `IMPLEMENTATION_GENERALIST`; Next → Gameplay Systems Agent.
