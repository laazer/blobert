# TICKET: 02_physics_frame_order

**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Status:** Ready  
**Type:** Refactor (M1 code)

## Title

Document and validate physics frame execution order in PlayerController3D

## Description

Implicit frame order in `_physics_process` must be explicit and validated. Attacks need to know:
- When jump buffer/coyote time checks happen
- When collision masks update (one-way platforms)
- When renderer syncs (must be AFTER all game state updates)

Add explicit frame-order documentation and ensure execution follows:
1. State machine update (advance state_timer)
2. Timer updates (coyote, jump buffer, iframes)
3. State handler (input checks, physics apply)
4. Collision mask update (one-way platforms)
5. Renderer sync (read-only from controller)
6. move_and_slide()

Also implement and document:
- **Jump Buffer (0.1s):** Player can queue jump up to 0.1s before landing
- **Coyote Time (0.1s):** Player can jump up to 0.1s after walking off platform

## Acceptance Criteria

- [ ] Frame-order execution documented (in-code comments + explicit sequence)
- [ ] Jump buffer timer implemented and tested: jump queued before landing is executable
- [ ] Coyote time timer implemented and tested: jump executable 0.1s after leaving ground
- [ ] One-way platform collision mask updates correctly (up = exclude one-way, down = include)
- [ ] Renderer sync happens after ALL game state updates (not mid-frame)
- [ ] All M1 tests still pass
- [ ] `run_tests.sh` exits 0

## Dependencies

- M11_prereq_1_player_state_machine (must add state timer first)

## Test Examples

```
Jump buffer: Player is on ground, hits jump button, lands before 0.1s expires → jump executes on landing
Coyote time: Player walks off platform, has 0.1s to press jump and still jump successfully
One-way platforms: From below, player passes through. From above, player lands on it.
```

## Notes

- Coyote time and jump buffer are optional polish, but recommended for responsive feel
- If M1 already has these, just document them; if not, add them
- Frame order changes must not break existing M1 behavior

---

## Execution Plan

**Ticket ID:** M11-02  
**Planning revision:** 2  
**Date:** 2026-05-23  
**Next agent:** Spec Agent (Task 1)

### Executive Summary

Make `_physics_process` in `PlayerController3D` follow a frozen, documented six-step frame contract: gameplay FSM tick → controller timers (jump buffer; coyote documented with sim) → kinematic dispatch (`MovementSimulation.simulate`) → one-way collision mask → renderer/visual sync (read-only) → `move_and_slide()`. Add **jump buffer** (0.1s) at the controller boundary; keep **coyote time** behavior in `MovementSimulation` unless spec proves a controller move is required for ordering. No M1 gameplay regression; behavior-based Godot tests are the contract.

### Dependency Matrix

| Dependency | Folder / State | Blocks M11-02? | Notes |
|------------|----------------|----------------|-------|
| M11-01 player state machine | `done/01_player_state_machine.md` | **No** (satisfied) | `PlayerStateMachine.update(delta)` + `sync_from_context` wired |
| `player_physics_frame_order` spec | **Absent** | N/A | Greenfield: `agent_context/agents/2_spec/player_physics_frame_order_spec.md` |
| Frame-order / jump-buffer tests | **Absent** (`tests/**/*frame*order*` none) | N/A | Greenfield under `tests/scripts/player/` |
| One-way physics layers | **Undeclared** in `project.godot` | **WARN** | No `layer_names` / one-way bit today; spec must freeze bit layout + test fixture |
| Branch `run_tests.sh` green | M11-01 gatekeeper: exit 1 (18 unrelated Godot failures) | **WARN** (AC only) | Does not block SPECIFICATION; blocks COMPLETE |

**Umbrella ticket:** No. **Cycles:** None.

### Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | `player_physics_frame_order_spec.md`; spec exit `--type generic` |
| Test design | Test Designer Agent | 1 | Controller frame-order + jump buffer + coyote + one-way tests |
| Test break | Test Breaker Agent | 1 | Timer edges, mask flip at vy=0, reorder regressions |
| Implementation | Gameplay Systems Agent | 1–2 | Reorder `_physics_process`; buffer; mask; renderer push |
| Static QA | GDScript Reviewer | 1 | `task hooks:gd-review` on changed `.gd` |
| Learning | Learning Agent | 1 | `LEARNINGS.md` append |
| AC gatekeeper | AC Gatekeeper | 1 | AC matrix; `run_tests.sh` exit 0; commit/push before COMPLETE |

**Total:** 7–8 agent runs

### Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author normative spec: numbered `_physics_process` contract (6 steps), jump buffer semantics (0.1s `@export`), coyote ownership (sim vs controller), effective `jump_just_pressed` contract into `simulate()`, one-way layer bit map + mask rules (vy>0 exclude, vy≤0 include), renderer sync targets (`SlimeVisualState`, `PlayerExportAnimationController3D` / future attack VFX), post-`move_and_slide` FSM `sync_from_context` rule, M11-01 hook preservation | Spec Agent | Ticket AC; `player_controller_3d.gd`; `movement_simulation.gd`; `INTEGRATION_ROADMAP.md` Pattern 2; M11-01 spec hook note | `agent_context/agents/2_spec/player_physics_frame_order_spec.md` | — | `spec_completeness_check.py` PASS (`--type generic`); every AC maps to spec section | **Risk:** One-way layers greenfield — spec must define bits + sandbox fixture path. **Assume:** coyote stays in sim unless reorder requires controller decrement |
| 2 | Write headless tests: jump buffer (press before land → jump on land), coyote at controller boundary (walk off + press within 0.1s), frame-order observables (e.g. mask applied before `move_and_slide`, state committed before renderer hook) without prose/markdown asserts | Test Designer Agent | Approved spec Task 1 | `tests/scripts/player/test_player_physics_frame_order.gd` (+ focused helpers if needed) | 1 | Tests fail (red) before implementation; assert runtime only | **Risk:** Call-order tests invalid unless spec defines observable contract |
| 3 | Adversarial tests: buffer expiry at 0.1s boundary, coyote+consumed interaction, mask flip when vy crosses 0, double jump via buffer, `move_and_slide` before mask regression | Test Breaker Agent | Spec + Task 2 | `tests/scripts/player/test_player_physics_frame_order_adversarial.gd` | 2 | New failures encode conservative assumptions; `# CHECKPOINT` where ambiguous | **Assume:** strictest defensible timer boundaries |
| 4 | Implement controller frame pipeline: extract private steps (`_tick_timers`, `_dispatch_movement`, `_update_one_way_collision_mask`, `_sync_renderer_from_state`), reorder so `move_and_slide()` is last; add `jump_buffer_time` export + timer; feed buffered jump into `simulate()` | Gameplay Systems Agent | Spec; red tests | Updated `scripts/player/player_controller_3d.gd` | 3 | Task 2–3 tests PASS; in-code step comments match spec | **Risk:** Large diff — no unrelated refactors |
| 5 | One-way platform support per spec: `project.godot` layer names (if required), player baseline `collision_mask`, mask update from velocity.y; minimal sandbox/platform scene for tests | Gameplay Systems Agent | Spec COL/one-way section | Layer config + test scene path documented in spec | 4 | One-way AC tests PASS (pass-through from below, land from above) | **Risk:** No production one-way geometry yet — fixture-driven tests |
| 6 | Renderer one-way sync: controller pushes read-only snapshot to visual/animation nodes after state commit, before `move_and_slide()`; no renderer→controller writes | Gameplay Systems Agent | Spec renderer section | Updated `slime_visual_state.gd` / animation wiring only if spec requires | 4 | Renderer sync AC met; animation uses post-dispatch state | **Assume:** may centralize in one `_sync_renderer_from_state()` |
| 7 | Regression: existing jump/coyote sim tests unchanged; optional controller integration tests if spec mandates | Gameplay Systems Agent | `tests/scripts/movement/test_jump_simulation*.gd` | No regressions in movement suite | 4–6 | `godot --headless -s tests/run_tests.gd` player/movement paths green | **Risk:** Buffer changes jump timing — spec defines parity cases |
| 8 | Full suite + GDScript review | GDScript Reviewer (Static QA) | Tasks 4–7 | `run_tests.sh` evidence; review clean | 7 | `timeout 300 ci/scripts/run_tests.sh` → 0; no high-priority blockers | **WARN:** branch may still have unrelated failures from M11-01 gatekeeper |
| 9 | Extract learnings (frame contract, buffer vs sim timers, one-way mask) | Learning Agent | Implementation | `LEARNINGS.md` append | 8 | Entry references M11-02 | — |
| 10 | AC gatekeeper: verify AC, git clean + pushed | AC Gatekeeper | Ticket AC; test evidence | Stage COMPLETE; ticket → `done/` | 9 | All AC met; commit/push verified | Mandatory per workflow |
| 11 | Orchestrator: run `planner_to_spec` … `learning_to_ac_gatekeeper` gates each transition | Autopilot Orchestrator | Checkpoint artifacts | Gate PASS logs in `project_board/checkpoints/M11-02/` | Per stage | No skip on exit 1 | `mandatory_workflow_gates_v1.md` |

### Notes

- **Non-breaking refactor:** M1 jump/coyote/wall-cling feel preserved unless spec documents intentional buffer polish.
- **Coyote:** Already in `MovementSimulation` (`coyote_time` export on controller). Spec documents whether timer decrement stays in `simulate()` step 3 or moves to step 2.
- **Jump buffer:** Net-new; default 0.1s; must not duplicate coyote logic inside sim.
- **Downstream:** M11 attack tickets depend on stable frame phase for input gating and hitbox queries.
- **Reference read-only:** `reference_projects/`, `3D-Platformer-Kit/`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- M11-01 dependency satisfied (`done/01_player_state_machine.md`).
- Planning complete (revision 2): execution plan embedded; handoff to Spec Agent.
- **WARN:** Branch `run_tests.sh` may still exit 1 from unrelated failures (see M11-01 ac-gatekeeper); does not block spec work; blocks COMPLETE until green.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "spec_path": "project_board/specs/player_physics_frame_order_spec.md",
  "ticket_path": "project_board/11_milestone_11_base_mutation_attacks/in_progress/02_physics_frame_order.md",
  "primary_test_file": "tests/scripts/player/test_player_physics_frame_order.gd",
  "adversarial_test_file": "tests/scripts/player/test_player_physics_frame_order_adversarial.gd",
  "checkpoint_log": "project_board/checkpoints/M11-02/2026-05-23T-test-design-run.md",
  "red_evidence": "13/13 failures in test_player_physics_frame_order.gd"
}
```

## Status
Proceed

## Reason
Primary PFO behavioral tests authored and RED (13 failures). Handoff to Test Breaker for adversarial suite and boundary cases.
