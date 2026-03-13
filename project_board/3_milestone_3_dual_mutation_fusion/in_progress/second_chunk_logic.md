# Second chunk logic

**Epic:** Milestone 3 – Dual Mutation + Fusion
**Status:** In Progress

---

## Description

Extend chunk system to support a second chunk: two chunks can be detached/recalled independently, each carrying or linking to a mutation slot for fusion.

## Acceptance criteria

- [ ] Second chunk can be detached and recalled like the first
- [ ] Both chunks can exist in world at same time with correct state
- [ ] HP and recall rules apply per chunk (or as designed)
- [ ] No state corruption when mixing one-chunk and two-chunk flows
- [ ] Second-chunk behavior is human-playable in-editor: both chunks and their roles are visible and understandable without debug overlays

---

## Execution Plan

### Overview

The existing system has one chunk lifecycle managed by `PlayerController3D` and tracked via `MovementSimulation.MovementState.has_chunk`. This plan extends that system to a second, fully independent chunk (`has_chunk_2`) using the same patterns established for chunk 1.

**Key architectural decisions (see CHECKPOINTS.md for full log):**
- New input action `detach_2` (dedicated, not multiplexed with `detach`)
- `has_chunk_2: bool = true` added to `MovementState`
- `simulate()` extended to 9 args: `detach_2_just_pressed: bool = false` as 8th positional arg (before `delta`); default value preserves all existing 8-arg call sites
- Second chunk reuses `chunk_3d.tscn`; distinct visuals are deferred to `visual_clarity_hybrid_state.md`
- HP cost for chunk 2 detach/recall is symmetric with chunk 1 (uses same `hp_cost_per_detach`)
- No mutation slot wiring in this ticket; slot linkage belongs to `fusion_rules_and_hybrid.md`
- Both chunks may be in the world simultaneously (not sequentially gated)

---

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Register `detach_2` input action in project.godot | Spec Agent | `project.godot` (existing `detach` binding at key E/keycode 69); CHECKPOINTS.md second_chunk_logic entries | `project.godot` updated with `detach_2` action bound to a new key (recommended: Q, physical_keycode 81); spec document `second_chunk_logic_spec.md` created at `agent_context/projects/blobert/specs/second_chunk_logic_spec.md` | None | `detach_2` action exists in input map and is distinct from `detach`; spec document covers all SPEC items (see below) | Risk: key conflict with existing bindings; Assumption: Q is unbound |
| 2 | Extend MovementState with `has_chunk_2` field and extend `simulate()` to 9 args | Spec Agent | `scripts/movement_simulation.gd`, spec doc from Task 1 | Spec document updated with: SPEC-SCL-1 (has_chunk_2 field, default true), SPEC-SCL-2 (detach_2 step in simulate, step 19), SPEC-SCL-3 (9-arg signature with detach_2_just_pressed default false), SPEC-SCL-4 (HP cost step for chunk 2), SPEC-SCL-5 (simulate() never sets has_chunk_2=true) | Task 1 | Spec precisely mirrors the has_chunk/detach_just_pressed pattern from SPEC-46 through SPEC-49 | Risk: spec gap on order-of-operations for step 19 relative to step 17/18; must be explicit |
| 3 | Design primary headless tests for second chunk detach/recall simulation | Test Design Agent | Spec from Tasks 1-2; `tests/chunk/test_chunk_detach_simulation.gd` (pattern reference) | New test file `tests/chunk/test_second_chunk_simulation.gd` with primary tests covering: has_chunk_2 default true, detach_2 fires when pressed + has_chunk_2=true, detach_2 no-op when has_chunk_2=false, carry-forward across frames, HP cost on detach_2, has_chunk_2 independent of has_chunk (both can be false simultaneously), simulate() 9-arg signature callable | Tasks 1-2 | Test file registered in `tests/run_tests.gd`; all tests pass with correct semantics described | Risk: 9-arg signature may require updating all existing simulate() call sites in tests if default arg is not supported as expected |
| 4 | Design adversarial tests for second chunk simulation | Test Breaker Agent | Spec from Tasks 1-2; primary tests from Task 3; existing adversarial patterns in `tests/chunk/test_chunk_detach_simulation_adversarial.gd` | New file `tests/chunk/test_second_chunk_simulation_adversarial.gd` with adversarial tests covering: independence of has_chunk and has_chunk_2 under all presses; simultaneous detach of both on same frame; HP floor clamp with both chunks detached in sequence; determinism; prior_state immutability for has_chunk_2 | Task 3 | Adversarial suite registered in run_tests.gd; all passing when implementation is correct; at least one test designed to fail on incorrect implementation | Assumption: existing detach tests continue to pass unchanged |
| 5 | Implement `has_chunk_2` in MovementState and extend simulate() to 9 args | Core Simulation Agent | Spec from Tasks 1-2; tests from Tasks 3-4; `scripts/movement_simulation.gd` | Updated `scripts/movement_simulation.gd` with: `has_chunk_2: bool = true` in MovementState; `detach_2_just_pressed: bool = false` as 8th positional arg to simulate(); step 19 (detach_2 logic) and step 20 (HP cost for detach_2) added; all existing 8-arg call sites continue to work via default value | Tasks 3-4 | All existing tests pass; new tests from Tasks 3-4 pass; `timeout 120 godot --headless --check-only` passes | Risk: GDScript default parameters on methods — confirm they work as expected for existing test call sites |
| 6 | Implement second chunk scene tracking in PlayerController3D | Gameplay Systems Agent | Spec from Tasks 1-2; updated movement_simulation.gd from Task 5; `scripts/player_controller_3d.gd` | Updated `scripts/player_controller_3d.gd` with: `_chunk_node_2: RigidBody3D = null`; `_recall_in_progress_2: bool = false`; `_recall_timer_2: float = 0.0`; reads `detach_2` input action; detaches/recalls chunk 2 following the same logic as chunk 1 (same lob parameters, same recall travel time, same HP restoration formula); both `_chunk_node` and `_chunk_node_2` can be non-null simultaneously | Task 5 | `has_chunk()` and new `has_chunk_2()` public methods return correct values; detach and recall signals for chunk 2 are emitted; existing chunk 1 behavior is unaffected | Risk: recall timing collision (both recall in-progress simultaneously); Assumption: independent timers handle this cleanly |
| 7 | Add `detach_2` signal and public API to PlayerController3D | Gameplay Systems Agent | Updated player_controller_3d.gd from Task 6 | Signals `detach_2_fired(player_position: Vector3, chunk_position: Vector3)`, `recall_2_started(...)`, `chunk_2_reabsorbed(...)` added; `has_chunk_2() -> bool` public method added | Task 6 | Signals emitted on correct events; has_chunk_2() returns true when chunk 2 is attached, false when detached | Assumption: signal naming convention matches existing chunk 1 signals exactly |
| 8 | Design controller-level integration tests for dual chunk | Test Design Agent | Tasks 6-7 outputs; existing `tests/chunk/test_chunk_recall_simulation.gd` as pattern; `tests/scene/test_3d_scene.gd` | New test file `tests/chunk/test_dual_chunk_controller.gd` covering: detach chunk 1 then detach chunk 2 (both out simultaneously); recall chunk 1 while chunk 2 is detached; recall chunk 2 while chunk 1 is detached; HP balance across dual detach+recall cycle; chunk node cleanup on recall; no state corruption across mixed flows | Tasks 6-7 | File registered in run_tests.gd; tests are deterministic and pass | Risk: controller tests require scene tree; follow Pattern B (inject _recall_in_progress_2 directly) for timer-driven paths |
| 9 | Verify syntax and run full test suite | Static QA Agent | All modified files from Tasks 5-7; test files from Tasks 3-4, 8 | `timeout 120 godot --headless --check-only` — 0 errors; `timeout 300 godot --headless -s tests/run_tests.gd` — 0 failures | Tasks 5-8 | All pre-existing tests still pass; all new second_chunk tests pass | Risk: run_tests.gd registration omission; must verify all new files are included |
| 10 | Verify human playability in test_movement_3d.tscn | Integration Agent | Updated player scene; in-editor test run | Commit-ready repo state; playtest notes confirming: both chunks can be detached and recalled independently; correct visual and state feedback; no debug overlays required to understand dual-chunk behavior | Task 9 | AC 1-5 all checkable manually; no crashes or state corruption observed | Risk: `detach_2` key binding may conflict with Godot editor shortcuts; Assumption: Q is safe |

### Spec Items (for Spec Agent to define in `second_chunk_logic_spec.md`)

- **SPEC-SCL-1** — `MovementState.has_chunk_2: bool = true` (mirrors SPEC-46)
- **SPEC-SCL-2** — `has_chunk_2` default semantics: true=attached, false=detached; simulate() never sets has_chunk_2=true (mirrors SPEC-47)
- **SPEC-SCL-3** — Detach step 2: `detach_2_eligible = detach_2_just_pressed AND prior.has_chunk_2`; carry-forward otherwise; no other fields affected (mirrors SPEC-48)
- **SPEC-SCL-4** — simulate() 9-argument signature: `detach_2_just_pressed: bool = false` as 8th positional arg before delta (mirrors SPEC-49); default value preserves 8-arg call sites (mirrors SPEC-50)
- **SPEC-SCL-5** — HP reduction step 2 (step 20): identical formula to step 18 but conditioned on detach_2_eligible (mirrors SPEC-56/58)
- **SPEC-SCL-6** — Independence invariant: has_chunk and has_chunk_2 are fully independent; any combination of true/false is valid
- **SPEC-SCL-7** — `detach_2` input action: added to project.godot; distinct key from `detach`; same "press = detach OR recall" dual-mode routing as chunk 1
- **SPEC-SCL-8** — Controller fields: `_chunk_node_2`, `_recall_in_progress_2`, `_recall_timer_2` (mirrors existing chunk 1 fields)
- **SPEC-SCL-9** — Non-functional: no engine API in simulate(); all new fields typed; no dead code

### Notes

- All absolute file paths relevant to this plan:
  - `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`
  - `/Users/jacobbrandt/workspace/blobert/scripts/player_controller_3d.gd`
  - `/Users/jacobbrandt/workspace/blobert/project.godot`
  - `/Users/jacobbrandt/workspace/blobert/tests/chunk/test_chunk_detach_simulation.gd` (pattern reference)
  - `/Users/jacobbrandt/workspace/blobert/tests/chunk/test_chunk_recall_simulation.gd` (pattern reference)
  - `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` (must register new test files)
  - New files to create: `tests/chunk/test_second_chunk_simulation.gd`, `tests/chunk/test_second_chunk_simulation_adversarial.gd`, `tests/chunk/test_dual_chunk_controller.gd`, `agent_context/projects/blobert/specs/second_chunk_logic_spec.md`

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
10

## Last Updated By
Human (Claude Code assisted)

## Validation Status
- Tests: CONFIRMED PASS. `timeout 300 godot -s tests/run_tests.gd` run on 2026-03-13. Result: 408 passed, 0 failed across all suites. Includes test_dual_chunk_controller.gd (10/10), test_second_chunk_simulation.gd (57/57), test_second_chunk_simulation_adversarial.gd (24/24). BLOCK-1 resolved.
- Static QA: CONFIRMED — No syntax errors. Note: `--check-only` hangs in Godot 4.6.1 headless because it initializes the main scene (known engine behavior in this project). Full test suite run above serves as runtime + parse verification — no GDScript errors were reported during execution. BLOCK-2 resolved.
- Integration: Pending. No playtest notes exist. Task 10 from the Execution Plan (in-editor human playability verification) has not been performed. AC5 requires a human to run the scene in-editor, observe both chunks detaching and recalling independently without debug overlays, and document that result. This has not occurred.
- Spec: Complete. See `project_board/3_milestone_3_dual_mutation_fusion/specs/second_chunk_logic_spec.md`. Covers SPEC-SCL-1 through SPEC-SCL-9.

## Implementation Summary (Tasks 5, 6, 7 complete)
### Task 5 (Core Simulation Agent — already complete):
- Added `has_chunk_2: bool = true` to `MovementState` inner class in `scripts/movement/movement_simulation.gd`
- Extended `simulate()` to 9 arguments: `detach_2_just_pressed: bool = false` as 9th and final positional arg after `delta: float`
- Added steps 19 and 20 for chunk 2 detach and HP reduction
- All existing 8-arg `simulate()` call sites continue to work via default value of the 9th arg

### Tasks 6 and 7 (Gameplay Systems Agent):
- Added `_chunk_node_2: RigidBody3D = null`, `_recall_in_progress_2: bool = false`, `_recall_timer_2: float = 0.0` fields to `PlayerController3D`
- Added signals: `detach_2_fired(player_position, chunk_position)`, `recall_2_started(player_position, chunk_position)`, `chunk_2_reabsorbed(player_position)`
- Added `has_chunk_2() -> bool` public method: returns `_chunk_node_2 == null`
- Reads `Input.is_action_just_pressed("detach_2")` and passes as 9th arg to `simulate()`
- Detach chunk 2 logic mirrors chunk 1: same lob parameters, same spawn offset, same scene
- Recall chunk 2 logic mirrors chunk 1: same travel time (`_RECALL_TRAVEL_TIME`), same HP restoration formula
- Both `_chunk_node` and `_chunk_node_2` can be non-null simultaneously (independent timers)
- Created `tests/chunk/test_dual_chunk_controller.gd` with 10 tests covering dual-chunk flows

## Blocking Issues
- BLOCK-3 (AC5): Manual in-editor playability verification has not been performed. AC5 requires a human to open `test_movement_3d.tscn`, play the scene, detach and recall both chunks independently, confirm both chunks and their roles are visually understandable without debug overlays, and document playtest notes. No such notes exist. This is an inherently manual check that cannot be substituted by automated tests.

## Escalation Notes
- SPEC-SCL-4 clarification: detach_2_just_pressed is the 9th (last) positional arg in simulate(), after delta, due to GDScript 4 constraint that optional parameters must follow required parameters.
- Test Designer checkpoint: two decisions logged in CHECKPOINTS.md under [second_chunk_logic].
- Test Breaker checkpoints: three decisions logged in CHECKPOINTS.md under [second_chunk_logic] (HP order-of-operations, cross-contamination, prior-state immutability).
- Gameplay Systems checkpoint: test_dual_chunk_controller.gd created by this agent (see CHECKPOINTS.md) since it is required for test suite completeness and was unambiguously scoped to this ticket.
- AC Gatekeeper (Revision 9): Stage held at INTEGRATION. Three blocking issues documented. Implementation appears structurally complete but no confirmed test run or in-editor playtest is on record. All three blocks must be resolved and documented in Validation Status before this ticket may advance to COMPLETE.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/3_milestone_3_dual_mutation_fusion/in_progress/second_chunk_logic.md",
  "required_actions": [
    "Open test_movement_3d.tscn in-editor; detach and recall both chunks independently; confirm both chunks and their roles are visually clear without debug overlays; document playtest notes in Validation Status (resolves AC5 / BLOCK-3)"
  ]
}
```

## Status
Needs Attention

## Reason
BLOCK-1 and BLOCK-2 resolved: full test suite confirmed 408 passed, 0 failed on 2026-03-13. Only BLOCK-3 (AC5) remains: human in-editor playtest of dual-chunk detach/recall in test_movement_3d.tscn has not been performed. Once playtest notes are documented in Validation Status, ticket may advance to COMPLETE.
