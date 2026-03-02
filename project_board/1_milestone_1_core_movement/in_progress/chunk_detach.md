# Chunk detach

**Epic:** Milestone 1 – Core Movement Prototype
**Status:** In Progress

---

## Description

Implement the mechanic where the slime can detach a chunk (e.g. on input). The chunk becomes a separate entity in the world; the main body and chunk are both represented and can be moved/used later.

## Acceptance criteria

- [ ] Detach input triggers chunk separation from main slime body
- [ ] Detached chunk exists in world as its own object (position, collision if needed)
- [ ] Main body state updates (e.g. "has chunk" flag) so recall and HP can hook in
- [ ] No crash or undefined state when detaching; behavior is deterministic

---

## Dependencies

- M1-001 (movement_controller) — COMPLETE

---

## Execution Plan

### Overview

The chunk detach feature has two clearly separated concerns:

1. **Core Simulation** — `has_chunk: bool` flag added to `MovementState`; detach eligibility and state transition logic added to `simulate()`. Pure GDScript, no engine dependencies, headlessly testable.

2. **Engine Integration / Presentation** — `scenes/chunk.tscn` scene created; `player_controller.gd` reads `next_state.has_chunk` and spawns or removes the chunk node in `_physics_process()`.

SPEC numbers: SPEC-46 through SPEC-53 (8 specs). Test files: `tests/test_chunk_detach_simulation.gd` + adversarial companion. Runner updated: `tests/run_tests.gd`.

---

### Normative Order of Operations Addition

Detach is appended as a new final step to `simulate()` after the existing `is_on_floor` pass-through (currently the last step). The complete new step:

```
SPEC-48 — Detach step (appended after is_on_floor pass-through):
  detach_eligible = detach_just_pressed AND prior_state.has_chunk
  if detach_eligible:
      result.has_chunk = false
  else:
      result.has_chunk = prior_state.has_chunk   # carry-forward
```

- Detach does not affect velocity, jump state, cling state, or any other field.
- When `prior_state.has_chunk == false`, `detach_just_pressed` is a no-op (deterministic, no crash).
- `result.has_chunk` is always explicitly set (no uninitialized path).

---

### simulate() Signature Change

Current (7 args):
```
simulate(prior_state, input_axis, jump_pressed, jump_just_pressed, is_on_wall, wall_normal_x, delta)
```

New (8 args):
```
simulate(prior_state, input_axis, jump_pressed, jump_just_pressed, is_on_wall, wall_normal_x, detach_just_pressed, delta)
```

All existing call sites pass `false` for `detach_just_pressed` (same migration pattern as SPEC-27 and SPEC-35 for prior signature extensions).

---

### Task Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|-----------------|---------------------|
| 1 | Write chunk detach spec (`chunk_detach_spec.md`) | Spec Agent | This execution plan; existing `movement_simulation.gd` (SPEC-1 through SPEC-36 as reference); `agent_context/agents/common_assets/ticket_template_v2.md` | `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/chunk_detach_spec.md` containing SPEC-46 through SPEC-53 as defined below | None | Spec file exists; all 8 SPEC items defined with typed acceptance criteria; SPEC-46 defines `has_chunk` field; SPEC-47 defines default value; SPEC-48 defines detach step; SPEC-49 defines simulate() 8-arg signature; SPEC-50 defines call-site migration; SPEC-51 defines `detach` input action in project.godot; SPEC-52 defines controller wiring; SPEC-53 defines non-functional requirements | Spec Agent must not introduce new SPEC numbers below 46 or above 53 without logging a checkpoint |
| 2 | Design headless unit tests for SPEC-46 through SPEC-53 | Test Design Agent | `chunk_detach_spec.md` from Task 1; existing test files (e.g. `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd`) as structural reference | `/Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation.gd` — class `ChunkDetachSimulationTests extends Object` with `func run_all() -> int` | Task 1 | Test file exists and covers all AC items from SPEC-46 through SPEC-53 that are headlessly verifiable; file parses under `godot --headless --check-only`; at least one test per SPEC item | Tests must use 8-arg simulate() signature; must pass `false` for `detach_just_pressed` in non-detach tests; EPSILON = 1e-4 for float comparisons |
| 3 | Write adversarial tests for chunk detach simulation | Test Breaker Agent | `chunk_detach_spec.md` from Task 1; `tests/test_chunk_detach_simulation.gd` from Task 2 | `/Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation_adversarial.gd` — class `ChunkDetachSimulationAdversarialTests extends Object` with `func run_all() -> int` | Task 2 | Adversarial file exists; covers boundary cases: detach when `has_chunk=false` (no-op), consecutive detach presses, has_chunk carry-forward across multiple no-detach frames, prior_state immutability (has_chunk field not mutated), delta=0.0 with detach, detach on floor vs. airborne (same behavior expected — detach is input-only, no physics condition) | See checkpoint [M1-005] entries for anticipated adversarial questions |
| 4 | Implement `has_chunk` in `MovementState` and detach logic in `simulate()` | Core Simulation Agent | `chunk_detach_spec.md` from Task 1; `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` (read first); test files from Tasks 2 and 3 | Modified `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`: (a) `has_chunk: bool = true` added to `MovementState`; (b) `simulate()` signature extended to 8 args; (c) detach step appended as final step; (d) all existing call sites in the file (none — simulate() is not called from within itself) updated; SPEC comment block at top of file updated | Tasks 1, 2, 3 | All tests from Tasks 2 and 3 pass (exit code 0 from headless runner); `godot --headless --check-only` produces zero errors on `scripts/movement_simulation.gd`; `has_chunk` defaults to `true`; detach sets `has_chunk = false` only when `prior_state.has_chunk == true AND detach_just_pressed == true`; no-op when `has_chunk == false` | Must not mutate prior_state; must update SPEC comment block at file top to include SPEC-46, SPEC-47, SPEC-48, SPEC-49; existing 15-step normative order documentation must be extended to 16 steps |
| 5 | Migrate all existing simulate() call sites to 8-arg signature | Core Simulation Agent | Modified `movement_simulation.gd` from Task 4; all test files in `/Users/jacobbrandt/workspace/blobert/tests/`; `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` | Updated test files: `test_movement_simulation.gd`, `test_movement_simulation_adversarial.gd`, `test_jump_simulation.gd`, `test_jump_simulation_adversarial.gd`, `test_wall_cling_simulation.gd`, `test_wall_cling_simulation_adversarial.gd` — all `simulate()` calls gain `false` as the new 7th positional argument (before `delta`); `player_controller.gd` updated with placeholder `false` for `detach_just_pressed` (Engine Integration Agent will replace with real input in Task 7) | Task 4 | `godot --headless --check-only` produces zero parse errors across all files; headless test runner exits 0 (all prior tests still pass after migration) | Follow exact migration pattern from SPEC-27 (added `false, 0.0` for wall inputs) and SPEC-35 (added `false, false` for jump inputs); no assertion values change; only argument lists change |
| 6 | Add `detach` input action to `project.godot` | Core Simulation Agent | `/Users/jacobbrandt/workspace/blobert/project.godot` (read first) | Modified `project.godot` with `detach` input action bound to key E (physical_keycode 69) and/or left mouse button | Task 4 | `godot --headless --check-only` passes; `detach` action present in `[input]` section of `project.godot`; binding matches SPEC-51 | Follow existing pattern for `jump` action in `project.godot`; if left mouse button is added, use `InputEventMouseButton` entry with `button_index = 1` |
| 7 | Create `scenes/chunk.tscn` and wire detach into `player_controller.gd` | Engine Integration Agent | `chunk_detach_spec.md` from Task 1; `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` (read first); `/Users/jacobbrandt/workspace/blobert/scenes/test_movement.tscn` (read first); all modified files from Tasks 4, 5, 6 | (a) `/Users/jacobbrandt/workspace/blobert/scenes/chunk.tscn` — minimal `RigidBody2D` scene with `freeze = true`, one `CollisionShape2D` child (CircleShape2D radius=8.0); (b) modified `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` — reads `Input.is_action_just_pressed("detach")`, passes `detach_just_pressed` to `simulate()`, copies `next_state.has_chunk` back to `_current_state.has_chunk`, spawns/removes chunk node based on transition `true→false`; (c) chunk node variable `_chunk_node` tracked on the controller | Tasks 4, 5, 6 | `godot --headless --check-only` passes on `player_controller.gd` and `chunk.tscn`; `_current_state.has_chunk` is copied back each frame; chunk node is spawned at `global_position` when `has_chunk` transitions from `true` to `false`; chunk node is freed when `has_chunk` transitions from `false` to `true` (anticipating M1-007 recall) or is already null-safe checked | Engine Integration Agent must read `player_controller.gd` before writing; chunk spawn uses `add_child()` on the scene root or parent node — must not add to the player itself (would move with player); chunk is spawned at player's `global_position` at detach frame |
| 8 | Register new test suites in `run_tests.gd` and verify full suite passes | Engine Integration Agent | `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` (read first); `tests/test_chunk_detach_simulation.gd` and `tests/test_chunk_detach_simulation_adversarial.gd` from Tasks 2 and 3 | Modified `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` with two new suite blocks for `ChunkDetachSimulationTests` and `ChunkDetachSimulationAdversarialTests`; headless test run exits 0 | Tasks 2, 3, 4, 5, 6, 7 | `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` exits with code 0; all prior suites still pass; new suites print suite name and pass/fail counts | Follow exact registration pattern from prior suites in `run_tests.gd` |
| 9 | Static QA review of all modified files | Static QA Agent | All modified `.gd` files: `movement_simulation.gd`, `player_controller.gd`, `test_chunk_detach_simulation.gd`, `test_chunk_detach_simulation_adversarial.gd`, `run_tests.gd`, and any migrated test files | Static QA report; any critical/warning issues resolved in-place | Tasks 4, 5, 6, 7, 8 | `godot --headless --check-only` exits 0 across all files; no untyped variables; no unused variables; no missing return types; SPEC-53 non-functional requirements all met | Same QA checklist as prior tickets; focus on: (a) `has_chunk` field is typed `bool`, (b) `detach_just_pressed` parameter is typed `bool`, (c) no movement math in `player_controller.gd` for detach logic |

---

### Spec Items Reference (for Spec Agent — Task 1)

The Spec Agent must produce `chunk_detach_spec.md` containing exactly these 8 SPEC items. Each item follows the established format from `wall_cling_spec.md` and `camera_follow_spec.md`.

**SPEC-46: MovementState `has_chunk` field**
New field `has_chunk: bool = true` added to `MovementState` inner class in `movement_simulation.gd`. Default `true` means the player starts holding a chunk. `MovementState.new()` with no arguments produces `has_chunk = true`. Total `MovementState` field count is now seven: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`.

**SPEC-47: `has_chunk` default and semantics**
`has_chunk = true` means the player body currently holds the chunk (not yet detached). `has_chunk = false` means the chunk has been detached and exists as a separate world entity. The simulation never re-sets `has_chunk = true`; recall (M1-007) is responsible for that transition.

**SPEC-48: Detach step — order of operations**
Appended as the final step of `simulate()` after the `is_on_floor` pass-through. Logic:
- `detach_eligible: bool = detach_just_pressed AND prior_state.has_chunk`
- If `detach_eligible`: `result.has_chunk = false`
- Else: `result.has_chunk = prior_state.has_chunk` (carry-forward)
No other fields are read or written in this step. Detach does not modify velocity, is_on_floor, coyote_timer, jump_consumed, is_wall_clinging, or cling_timer.

**SPEC-49: `simulate()` 8-argument signature**
Exact new signature:
```gdscript
func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float) -> MovementState:
```
`detach_just_pressed` is the 7th positional parameter (before `delta`). It is a single-frame edge trigger — the caller passes `Input.is_action_just_pressed("detach")`. There is no `detach_pressed` parameter; detach is not a held action.

**SPEC-50: Call-site migration**
Every existing call to `simulate()` in test files and `player_controller.gd` must be updated to pass `false` as the new 7th argument `detach_just_pressed`. This follows the same pattern as SPEC-27 (adding `is_on_wall, wall_normal_x`) and SPEC-35 (adding `jump_pressed, jump_just_pressed`). No assertion values in existing tests change. Only argument list length changes.

**SPEC-51: `detach` input action in `project.godot`**
A new input action `"detach"` must be added to `project.godot`. Minimum binding: physical_keycode 69 (E key). Optional additional binding: left mouse button (`InputEventMouseButton`, `button_index = 1`). This action is read by `player_controller.gd` as `Input.is_action_just_pressed("detach")`.

**SPEC-52: Engine integration — chunk spawn and controller wiring**
`player_controller.gd` must:
1. Declare `var _chunk_node: RigidBody2D = null` as a member variable.
2. In `_physics_process()` Step 1 (input reading), read `var detach_just_pressed: bool = Input.is_action_just_pressed("detach")`.
3. Pass `detach_just_pressed` as the 7th argument to `_simulation.simulate(...)`.
4. Copy `next_state.has_chunk` back to `_current_state.has_chunk` after the slide (following the same pattern as `_current_state.is_wall_clinging = next_state.is_wall_clinging`).
5. When `prior_state.has_chunk == true AND next_state.has_chunk == false`: instantiate `scenes/chunk.tscn`, set its `global_position` to `self.global_position`, add it as a child of `get_parent()` (not of self), store reference in `_chunk_node`.
6. `_chunk_node` is null-safe checked before any access (guard: `if _chunk_node != null`).
`scenes/chunk.tscn` contains a root `RigidBody2D` with `freeze = true` and one `CollisionShape2D` child (CircleShape2D, radius=8.0).

**SPEC-53: Non-functional requirements**
- All new variables typed with explicit defaults (NF-01, NF-02).
- No movement math added to `player_controller.gd` for detach logic (NF-03).
- `simulate()` does not reference any engine Node or singleton (NF-04).
- No dead code — `has_chunk` and `detach_just_pressed` are used in at least one code path each (NF-05).
- Zero `godot --headless --check-only` diagnostics across all modified files (NF-06).

---

### Risks and Assumptions

| Risk | Mitigation |
|------|-----------|
| Call-site migration misses a test file or leaves a stale 7-arg call, causing parse errors | Task 5 explicitly lists all 6 test files; agent must `grep` for `simulate(` across `tests/` before finishing |
| Chunk node added as child of player node (moves with player instead of staying in place) | SPEC-52 explicitly requires `get_parent()` as the add_child target, not `self` |
| `has_chunk` not copied back in controller, causing it to reset to default each frame | SPEC-52 item 4 and Task 7 success criteria explicitly require the copy-back |
| `detach_just_pressed` parameter placed after `delta` instead of before it (wrong position) | SPEC-49 gives the exact signature; agents must match positional order exactly |
| Godot binary not on PATH for test verification | Use `/Applications/Godot.app/Contents/MacOS/Godot` per CHECKPOINTS.md [M1-001] Engine Integration Agent checkpoint |
| chunk.tscn hand-written with invalid format causes parse error | Follow existing `test_movement.tscn` as format reference; root node must be RigidBody2D not Node2D |

---

## Specification

**Spec file:** `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/chunk_detach_spec.md`

**Coverage:** SPEC-46 through SPEC-53

### SPEC-46 Summary: MovementState `has_chunk` Field Declaration
Add `var has_chunk: bool = true` as the 7th and final field of `MovementState` in `movement_simulation.gd`. `MovementState.new()` produces `has_chunk == true`. Field must be explicitly typed with explicit default. No `@export`.

### SPEC-47 Summary: `has_chunk` Default Value Semantics
`true` = chunk attached (default, player starts holding chunk). `false` = chunk detached (in world as separate entity). `simulate()` never assigns `result.has_chunk = true` in any code path. Only the field initializer can produce `true`. M1-007 (recall) owns the `false → true` transition; it is out of scope for this ticket. `prior_state.has_chunk` is never mutated by `simulate()`.

### SPEC-48 Summary: Detach Step — Condition, Result, and Order of Operations
New step 17 appended to `simulate()` after `is_on_floor` pass-through (step 16). Logic: `detach_eligible = detach_just_pressed AND prior_state.has_chunk`. If eligible: `result.has_chunk = false`. Else: `result.has_chunk = prior_state.has_chunk`. This step reads only `detach_just_pressed` and `prior_state.has_chunk`; it writes only `result.has_chunk`. No velocity or other fields are affected. `result.has_chunk` is explicitly set on every code path (no uninitialized path). Normative order-of-operations comment block must be updated to 17 steps.

### SPEC-49 Summary: `simulate()` 8-Argument Signature
Exact signature: `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float) -> MovementState:`. `detach_just_pressed` is position 7 (before `delta`). All parameters explicitly typed. No default parameter values. Return type annotation required.

### SPEC-50 Summary: Call-Site Migration
All existing `simulate()` calls in 7 files must insert `false` as the 7th argument before `delta`. Files: `player_controller.gd`, `test_movement_simulation.gd`, `test_movement_simulation_adversarial.gd`, `test_jump_simulation.gd`, `test_jump_simulation_adversarial.gd`, `test_wall_cling_simulation.gd`, `test_wall_cling_simulation_adversarial.gd`. No assertion values change. Grep verification required before declaring migration complete.

### SPEC-51 Summary: `detach` Input Action in `project.godot`
Add action `"detach"` to `[input]` section with minimum binding: `physical_keycode = 69` (E key). Action name must be exactly `detach`. Format must match the existing `jump` action entry. No existing actions may be modified.

### SPEC-52 Summary: `player_controller.gd` Changes and `scenes/chunk.tscn`
Controller changes: (1) `var _chunk_node: RigidBody2D = null` member variable; (2) read `var detach_just_pressed: bool = Input.is_action_just_pressed("detach")` in Step 1; (3) pass to `simulate()` as 7th arg; (4) copy-back `_current_state.has_chunk = next_state.has_chunk`; (5) on `prior.has_chunk == true AND next.has_chunk == false`: instantiate `chunk.tscn`, set `global_position`, `get_parent().add_child()`, store in `_chunk_node`; (6) null-safe `_chunk_node` access. `chunk.tscn`: root `RigidBody2D` named `Chunk`, `freeze = true`, one `CollisionShape2D` child (CircleShape2D radius=8.0), no script.

### SPEC-53 Summary: Non-Functional Requirements
NF-01: All new vars explicitly typed. NF-02: All new class-level vars have explicit defaults. NF-03: No movement math in `player_controller.gd` for detach logic. NF-04: `simulate()` and `MovementSimulation` contain zero engine API calls. NF-05: No dead code — all new fields and parameters used in at least one code path. NF-06: Zero `godot --headless --check-only` diagnostics on all modified files.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_BACKEND

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Core Simulation Agent

## Required Input Schema
```json
{
  "spec_file_path": "/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/chunk_detach_spec.md",
  "spec_range": "SPEC-46 through SPEC-53",
  "primary_test_file": "/Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation.gd",
  "adversarial_output": "/Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation_adversarial.gd",
  "reference_adversarial": "/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation_adversarial.gd"
}
```

## Status
Proceed

## Reason
Adversarial test suite complete. `tests/test_chunk_detach_simulation_adversarial.gd` written as `ChunkDetachSimulationAdversarialTests` with 30 tests covering 15 adversarial gaps (GAP-01 through GAP-15) not covered by the 37-test primary suite. Gap coverage: detach+jump same frame (all 7 fields), detach+wall jump same frame, detach on landing transition frame, rapid no-op detach stability, delta=0.0 all-7-field verification, very large delta, full 7-field prior_state immutability, config mutation isolation, two-instance isolation, 100-iteration no-op stability, normal movement unaffected in active scenarios, coyote window, jump_consumed=true coexistence, active cling carry-forward, and sequential detach press edge-trigger semantics. `tests/run_tests.gd` updated with ChunkDetachSimulationAdversarialTests suite block. All 15 checkpoint decisions logged to CHECKPOINTS.md ([M1-005] Test Breaker — TB-CD-001 through TB-CD-015). Core Simulation Agent should now implement `has_chunk` field and detach step in `movement_simulation.gd` per SPEC-46 through SPEC-49, then migrate all call sites (SPEC-50), then add input action (SPEC-51).
