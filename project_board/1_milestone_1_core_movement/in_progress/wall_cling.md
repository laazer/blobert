# Wall cling

**Epic:** Milestone 1 – Core Movement Prototype
**Status:** In Progress

---

## Description

Allow the slime to cling to walls when touching them (e.g. during fall or after jump), with optional slide-down or fixed cling duration so wall movement is readable and controllable.

## Acceptance criteria

- [ ] Slime sticks to wall when touching it in air (detection and state)
- [ ] Cling duration or slide speed is configurable; behavior is predictable
- [ ] Player can leave wall (e.g. jump off or fall) without getting stuck
- [ ] Works with existing movement and jump

---

## Dependencies

- M1-001 (movement_controller) — COMPLETE
- M1-002 (jump_tuning) — COMPLETE

---

## Execution Plan

### Overview

Wall cling extends the existing pure-simulation architecture in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` and the engine-integration layer in `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd`. The implementation follows the established pattern from M1-001 and M1-002: simulation logic lives in the pure class, engine contacts (wall detection) are read in the controller and passed as parameters.

**Chosen mechanism:** Slide-down with reduced gravity (`cling_gravity_scale` multiplier) plus a `max_cling_time` safety cap. A new spec file is written at SPEC-25 through SPEC-36, continuing the existing numbering.

**Cling logic summary (normative order of operations added to simulate()):**
1. Existing steps 1–5 run unchanged (delta sanitize, axis sanitize, result alloc, coyote timer, jump_consumed carry).
2. NEW — Wall cling eligibility and state update (between existing steps 5 and 6).
3. Existing step 6 (jump / wall-jump eligibility and impulse) — wall jump replaces the regular jump condition when `prior_state.is_wall_clinging` is true and jump is just pressed.
4. Existing steps 7–10 run, with gravity modified to `gravity * cling_gravity_scale` when `result.is_wall_clinging` is true and a wall jump did not fire.

**Key formulas:**
- Pressing toward wall: `(input_axis * wall_normal_x) < 0.0`
- Cling active: `is_on_wall AND NOT is_on_floor AND pressing_toward_wall AND NOT jump_consumed AND cling_timer < max_cling_time`
- Cling gravity: `gravity * cling_gravity_scale * effective_delta` replaces `gravity * effective_delta` in step 8 when clinging
- Wall jump vertical: `-sqrt(2.0 * gravity * wall_jump_height)` then `+ gravity * effective_delta`
- Wall jump horizontal: `wall_normal_x * wall_jump_horizontal_speed` (wall_normal_x points away from wall)

---

### Task Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|----------------|--------------|-----------------|-------------------|
| 1 | Write wall cling simulation spec (SPEC-25 through SPEC-36) | Spec Agent | This execution plan; `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`; `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/jump_simulation_spec.md` (format reference) | New file `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md` containing all SPEC items with acceptance criteria, constraints, and risk analysis | None | File exists; covers SPEC-25 through SPEC-36; every spec item has numbered AC entries; every field and parameter has an exact GDScript declaration line specified | Spec Agent must not deviate from the simulate() signature extension described in this plan without logging a checkpoint |
| 2 | Design wall cling unit tests | Test Design Agent | `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md`; existing test files at `/Users/jacobbrandt/workspace/blobert/tests/` as style reference | New file `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd`; updated `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` to include new suite; updated call sites in all existing test files to pass the two new simulate() parameters | Task 1 | Test file parses under `godot --headless --check-only`; all existing suites still referenced in run_tests.gd; tests cover all AC items from SPEC-25–36; tests are FAILING (red) because implementation does not yet exist | All existing `simulate()` call sites in test files must be updated to add `false, 0.0` for `is_on_wall` and `wall_normal_x` |
| 3 | Break the wall cling tests (adversarial) | Test Breaker Agent | `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md`; `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd` | New file `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation_adversarial.gd`; updated `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` to include adversarial suite | Task 2 | Adversarial file parses; added to runner; covers boundary values for all new float params (0.0, negative, very large), NaN/Inf wall_normal_x, pressing_toward_wall boundary (input_axis * wall_normal_x == 0.0 exactly), cling_timer at exact max_cling_time, wall jump with jump_consumed=true (must be blocked) | Same call-site migration applies here; adversarial file must not import or depend on the non-adversarial suite |
| 4 | Implement wall cling in movement_simulation.gd | Generalist Agent | `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md`; `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` | Modified `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` with: (a) two new MovementState fields, (b) four new config parameters, (c) extended simulate() signature, (d) wall cling and wall jump logic inserted at the correct order-of-operations positions | Task 3 | `godot --headless --check-only` passes; all tests in all four existing suites still pass; all wall cling tests from Tasks 2–3 now pass; zero regression in jump or movement behavior | Must not mutate prior_state; must preserve all existing SPEC-1 through SPEC-24 behaviors; must not introduce any engine singletons or Node references |
| 5 | Update player_controller.gd for wall detection | Generalist Agent | `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md`; `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd`; Task 4 output | Modified `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` with: (a) wall cling config @export vars mirrored from simulation, (b) `is_on_wall()` and `get_wall_normal().x` reads in `_physics_process()`, (c) updated `simulate()` call with new parameters, (d) `is_wall_clinging` and `cling_timer` carried forward in `_current_state` after each frame | Task 4 | `godot --headless --check-only` passes on player_controller.gd; simulate() call passes all 7 parameters in the correct order; new @export vars copied to `_simulation` in `_ready()`; `_current_state.is_wall_clinging` and `_current_state.cling_timer` are updated after each frame identically to the coyote_timer pattern | `get_wall_normal()` returns Vector2.ZERO when not on wall; controller must guard `.x` access only when `is_on_wall()` is true, passing `0.0` otherwise |
| 6 | Static QA review | Static QA Agent | All modified and new `.gd` files from Tasks 4–5 | QA report; any issues filed back as blocking or non-blocking | Task 5 | All critical and warning issues resolved; `godot --headless --check-only` passes on all project files; typed GDScript throughout; no untyped var declarations in new code | |
| 7 | Full integration test run | Generalist Agent | All files from Tasks 4–6; Godot binary at `/Applications/Godot.app/Contents/MacOS/Godot` | Terminal output of `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` showing all suites passing; exit code 0 | Task 6 | Exit code 0; all suites listed as passing; failure count = 0; no parse errors in output | If any suite fails, the implementer must diagnose and fix before advancing the ticket |

---

### New Files

| File | Owner | Purpose |
|------|-------|---------|
| `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md` | Spec Agent (Task 1) | Normative spec covering SPEC-25 through SPEC-36 |
| `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd` | Test Design Agent (Task 2) | Unit tests for wall cling simulation behavior |
| `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation_adversarial.gd` | Test Breaker Agent (Task 3) | Adversarial/boundary tests for wall cling |

---

### Modified Files

| File | Modifying Task(s) | Change Summary |
|------|--------------------|----------------|
| `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` | Task 4 | New MovementState fields; new config vars; extended simulate() signature; wall cling and wall jump logic |
| `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` | Task 5 | Wall detection reads; extended simulate() call; state carry-forward; new @export vars |
| `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` | Tasks 2, 3 | Register two new test suites |
| `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd` | Task 2 | Migrate simulate() call sites to 7-arg signature |
| `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd` | Task 2 | Migrate simulate() call sites to 7-arg signature |
| `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd` | Task 2 | Migrate simulate() call sites to 7-arg signature |
| `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd` | Task 2 | Migrate simulate() call sites to 7-arg signature |

---

### Spec Items to Cover (SPEC-25 through SPEC-36)

| SPEC # | Topic |
|--------|-------|
| SPEC-25 | MovementState new fields: `is_wall_clinging: bool`, `cling_timer: float` |
| SPEC-26 | New config parameters: `cling_gravity_scale`, `max_cling_time`, `wall_jump_height`, `wall_jump_horizontal_speed` |
| SPEC-27 | simulate() extended signature: `is_on_wall: bool`, `wall_normal_x: float` as new parameters (positions 5 and 6, before `delta`) |
| SPEC-28 | Pressing-toward-wall detection formula: `(input_axis * wall_normal_x) < 0.0` |
| SPEC-29 | Cling eligibility: `is_on_wall AND NOT is_on_floor AND pressing_toward_wall AND NOT prior_state.jump_consumed AND prior_state.cling_timer < max_cling_time` |
| SPEC-30 | Cling state update: `result.is_wall_clinging = eligible_for_cling`; `result.cling_timer = prior_state.cling_timer + effective_delta` when clinging, else `0.0` |
| SPEC-31 | Cling gravity: when `result.is_wall_clinging` and no wall jump fired, apply `gravity * cling_gravity_scale * effective_delta` instead of `gravity * effective_delta` in the gravity step |
| SPEC-32 | Wall jump eligibility: `jump_just_pressed AND prior_state.is_wall_clinging AND NOT prior_state.jump_consumed` |
| SPEC-33 | Wall jump impulse: `result.velocity.y = -sqrt(2.0 * gravity * wall_jump_height)`; `result.velocity.x = wall_normal_x * wall_jump_horizontal_speed`; `result.jump_consumed = true`; `result.is_wall_clinging = false` |
| SPEC-34 | Order of operations: wall cling state update (SPEC-29–30) runs before jump eligibility (SPEC-32–33); wall jump overrides cling gravity; normal jump takes precedence over wall jump when player is on floor |
| SPEC-35 | Call-site migration: all existing test files update simulate() calls from 5-arg to 7-arg by appending `false, 0.0` before `delta` |
| SPEC-36 | Frame-rate independence: `cling_timer` increments by `effective_delta`; cling gravity scaled by `effective_delta`; wall jump impulse formula is frame-rate independent |

---

### Risks and Assumptions

- **R1 (signature churn):** Extending simulate() to 7 arguments requires updating call sites in 4 existing test files, run_tests.gd context (runner itself does not call simulate()), and player_controller.gd. If any call site is missed, `godot --headless --check-only` will catch the parse error. The Task 2 agent (Test Design) is responsible for migrating all existing test call sites as part of its output.
- **R2 (wall normal edge cases):** `get_wall_normal()` in Godot 4 returns Vector2.ZERO when not on a wall. The controller must gate the `.x` read behind `is_on_wall()`, passing `0.0` when false. If `wall_normal_x == 0.0`, `(input_axis * 0.0) < 0.0` evaluates to `false`, so cling eligibility is correctly blocked — this is a safe default.
- **R3 (jump_consumed shared between jump and wall jump):** Using the same `jump_consumed` flag means a player who has already jumped cannot wall-jump until they land. This is intentional for M1 scope and logged as assumption [M1-003] Planner checkpoint.
- **R4 (cling timer and max_cling_time=0.0):** If `max_cling_time = 0.0`, the condition `prior_state.cling_timer < max_cling_time` is `0.0 < 0.0 = false`, so cling is immediately blocked on the first frame. This disables wall cling entirely when max_cling_time is zero. Spec must document this behavior explicitly.
- **R5 (cling_gravity_scale=0.0 produces zero gravity):** Valid config — player hovers on the wall with no slide. Spec must document as defined behavior.
- **R6 (wall jump horizontal direction):** `wall_normal_x` from Godot's `get_wall_normal().x` points away from the wall. A wall to the right has `wall_normal_x < 0` (pointing left, away from wall). Multiplying by `wall_jump_horizontal_speed` (positive) gives a leftward impulse — correct. The spec must clarify the sign convention explicitly to avoid implementer error.

---

## Specification

Full specification written to `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md`.

### Summary of SPEC-25 through SPEC-36

| SPEC # | Topic | Key AC Count |
|--------|-------|-------------|
| SPEC-25 | MovementState new fields: `var is_wall_clinging: bool = false`, `var cling_timer: float = 0.0` | 7 |
| SPEC-26 | New config params: `cling_gravity_scale=0.1`, `max_cling_time=1.5`, `wall_jump_height=100.0`, `wall_jump_horizontal_speed=180.0` | 8 |
| SPEC-27 | simulate() new signature: 7-arg form with `is_on_wall: bool`, `wall_normal_x: float` as params 5 and 6 (before `delta`); call-site migration in 5 files | 6 |
| SPEC-28 | Pressing-toward-wall: `(safe_axis * wall_normal_x) < 0.0`; strict less-than; uses sanitized axis; wall_normal_x=0.0 always false | 7 |
| SPEC-29 | Cling eligibility: 5-condition boolean (`eligible_for_cling`); all conditions read from `prior_state`; `cling_timer < max_cling_time` is strict | 8 |
| SPEC-30 | Cling state update: `result.is_wall_clinging = eligible_for_cling`; `result.cling_timer = prior_state.cling_timer + effective_delta` or `0.0`; immediate reset on non-cling | 7 |
| SPEC-31 | Cling gravity: `gravity * cling_gravity_scale * effective_delta` when `result.is_wall_clinging`; wall jump frame uses normal gravity because step 6b sets `result.is_wall_clinging=false` | 7 |
| SPEC-32 | Wall jump eligibility: `jump_just_pressed AND prior_state.is_wall_clinging AND NOT prior_state.jump_consumed`; regular jump takes priority; reads `prior_state`, not `result` | 6 |
| SPEC-33 | Wall jump impulse: `result.velocity.y = -sqrt(2*gravity*wall_jump_height) + gravity*delta`; `result.velocity.x = wall_normal_x * wall_jump_horizontal_speed`; sets `jump_consumed=true`, `is_wall_clinging=false`; step 7 skipped | 9 |
| SPEC-34 | Normative 11-step order of operations; regular jump beats wall jump; step 7 skipped on wall jump; `result.is_wall_clinging` at gravity step is the sole cling gravity gate | 7 |
| SPEC-35 | Call-site migration: 4 test files gain `false, 0.0` as 5th and 6th args before `delta`; literals only; no assertion values change | 6 |
| SPEC-36 | Frame-rate independence: `cling_timer` uses `effective_delta`; cling gravity uses `effective_delta`; wall jump impulses are velocity assignments (not delta-scaled) | 5 |

### Critical design decisions encoded in spec

1. **Cling requires pressing toward wall continuously.** Releasing the stick or pressing away exits cling immediately (SPEC-29, SPEC-28).
2. **Wall jump reads `prior_state.is_wall_clinging`, not current frame eligibility.** At least one frame of confirmed cling is required before a wall jump is available (SPEC-32).
3. **`jump_consumed` blocks both cling and wall jump.** A player who regular-jumped mid-air cannot cling. Intentional M1 constraint (SPEC-29 AC-29.5, SPEC-32 AC-32.4).
4. **Wall jump horizontal replaces step 7 entirely.** The acceleration/friction formula does not run on wall jump frames (SPEC-34 AC-34.2).
5. **`result.is_wall_clinging=false` set by wall jump makes cling gravity self-excluding.** No separate "wall jump fired" flag is needed in the gravity step (SPEC-31).
6. **`max_cling_time=0.0` disables cling entirely** via strict `<` comparison (SPEC-29 AC-29.7, SPEC-26 R-26.2).
7. **`cling_gravity_scale=0.0` is valid** and produces player hover with no slide (SPEC-31 AC-31.3, SPEC-26 R-26.1).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_DESIGN

## Revision
3

## Last Updated By
Spec Agent

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
Test Designer Agent

## Required Input Schema
```json
{
  "spec_file": "/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/wall_cling_spec.md",
  "existing_tests_reference": "/Users/jacobbrandt/workspace/blobert/tests/",
  "output_test_file": "/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd",
  "runner_file": "/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd",
  "files_to_migrate": [
    "/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd",
    "/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd",
    "/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd",
    "/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd"
  ]
}
```

## Status
Proceed

## Reason
Specification complete. SPEC-25 through SPEC-36 written to wall_cling_spec.md. All design decisions encoded with numbered acceptance criteria, formulas, risk analysis, and concrete numeric examples. Test Designer Agent should write test_wall_cling_simulation.gd covering all AC items, migrate the 4 existing test files from 5-arg to 7-arg simulate() calls, and update run_tests.gd. Tests must be FAILING (red) at handoff since implementation does not yet exist.
