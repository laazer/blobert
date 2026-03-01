# Jump tuning

**Epic:** Milestone 1 – Core Movement Prototype
**Status:** In Progress

---

## Description

Add jump input and tune jump height, coyote time, and optional jump cut so the slime's jump feels good and predictable.

## Acceptance criteria

- [ ] Single jump from ground with configurable height/gravity
- [ ] Coyote time (brief window to jump after leaving ledge) implemented and tunable
- [ ] Optional: jump cut on release so variable height feels good
- [ ] No double jump unless specified in design

---

## Dependencies

- M1-001 (movement_controller) — COMPLETE

---

## Execution Plan

### Overview

This ticket extends the existing pure-simulation / engine-integration architecture established in M1-001. All jump mechanics live in the simulation layer (`movement_simulation.gd`); engine input reading lives in `player_controller.gd`. The `jump` input action (Space bar) is added to `project.godot`. A new headless test suite (`tests/test_jump_simulation.gd`) covers all simulation-layer behaviors.

### Architecture Decisions (resolved as checkpoints — see CHECKPOINTS.md entries [M1-002])

- Jump state fields (`coyote_timer: float`, `jump_consumed: bool`) are added to the existing `MovementState` inner class in `movement_simulation.gd`.
- `simulate()` signature is extended to: `simulate(prior_state, input_axis, jump_pressed, jump_just_pressed, delta) -> MovementState`.
- Default jump height: `120.0` pixels. Impulse derived at runtime as `sqrt(2 * gravity * jump_height)` applied as a negative `velocity.y`.
- Coyote time stored as a float seconds counter on `MovementState`; configurable window `coyote_time: float = 0.1` on `MovementSimulation`.
- Jump cut minimum upward velocity: `jump_cut_velocity: float = -200.0` on `MovementSimulation`.
- New test file: `tests/test_jump_simulation.gd`; existing `tests/run_tests.gd` updated to include it.
- Jump input: `Input.is_action_pressed("jump")` + `Input.is_action_just_pressed("jump")` in `player_controller.gd`.

### Key formulas

- **Jump impulse:** `velocity.y = -sqrt(2.0 * gravity * jump_height)`
  - At gravity=980, jump_height=120: impulse ≈ -484.97 px/s
- **Coyote eligibility:** player may jump if `jump_just_pressed` AND (`prior_state.is_on_floor` OR `prior_state.coyote_timer > 0.0`) AND NOT `prior_state.jump_consumed`
- **Coyote timer update:**
  - If `prior_state.is_on_floor`: reset to `coyote_time`
  - Else: decrement by `delta`, clamped to `0.0`
- **Jump consumed:** set `true` on the frame a jump is applied; reset to `false` when `is_on_floor` becomes `true`
- **Jump cut:** if `NOT jump_pressed` AND `result.velocity.y < jump_cut_velocity`: clamp `result.velocity.y = jump_cut_velocity`

---

### Task Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|----------------|--------------|-----------------|---------------------|
| 1 | Register `jump` input action in `project.godot` | Spec Agent | `project.godot` at `/Users/jacobbrandt/workspace/blobert/project.godot`; Space bar physical keycode = `32` | `project.godot` updated with a `jump` action bound to Space bar (physical_keycode=32), following the same object-literal format as `move_left`/`move_right` | None | `godot --headless --check-only` passes; `Input.is_action_pressed("jump")` is resolvable at runtime | Wrong keycode format breaks input; must mirror existing action format exactly |
| 2 | Write jump simulation specification | Spec Agent | `scripts/movement_simulation.gd`, `scripts/player_controller.gd`, execution plan above, CHECKPOINTS.md [M1-002] entries | Specification document covering: (a) new `MovementState` fields, (b) new `MovementSimulation` config parameters, (c) extended `simulate()` signature and all acceptance-criteria behaviors as numbered SPEC items with exact formulas and AC sub-items | Task 1 | Spec document exists at `agent_context/projects/blobert/specs/jump_simulation_spec.md`; all four acceptance criteria are covered by at least one SPEC item with measurable AC | Spec may conflict with existing SPEC numbering — use SPEC-15 onward; coyote timer edge cases (exact-zero) must be explicit |
| 3 | Extend `MovementState` with jump fields | Implementation Agent (Generalist) | Spec from Task 2; `scripts/movement_simulation.gd` | `MovementState` inner class gains two new typed fields: `coyote_timer: float = 0.0` and `jump_consumed: bool = false`. No other changes in this task. | Task 2 | `godot --headless --check-only` passes; `MovementState.new()` produces `coyote_timer == 0.0` and `jump_consumed == false`; existing tests in `tests/run_tests.gd` still pass (no regressions) | Adding fields to `MovementState` must not break existing test assertions on `velocity` or `is_on_floor`; field defaults must match spec |
| 4 | Add jump config parameters to `MovementSimulation` | Implementation Agent (Generalist) | Spec from Task 2; `scripts/movement_simulation.gd` after Task 3 | `MovementSimulation` class gains three new `var` declarations: `jump_height: float = 120.0`, `coyote_time: float = 0.1`, `jump_cut_velocity: float = -200.0`. No other changes. | Task 3 | `godot --headless --check-only` passes; parameters are accessible and have correct defaults when `MovementSimulation.new()` is called; existing tests still pass | Parameter naming must match what Task 5 (simulate() extension) and Task 6 (tests) reference exactly |
| 5 | Extend `simulate()` with jump logic | Implementation Agent (Generalist) | Spec from Task 2; `scripts/movement_simulation.gd` after Task 4; key formulas from execution plan above | `simulate()` signature changed to `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, delta: float) -> MovementState`. Implementation adds: (a) coyote timer update, (b) jump eligibility check and impulse application, (c) jump_consumed flag management, (d) jump cut application. Gravity and horizontal movement logic unchanged. | Task 4 | `godot --headless --check-only` passes; all four acceptance criteria are exercised by the implementation; existing horizontal/gravity behaviors are unaffected (existing tests still pass after caller sites updated in Task 6) | Signature change will break `player_controller.gd` caller — Task 6 updates the controller. Test file must be updated in Task 7. Order of operations within `simulate()` matters: coyote timer update must happen before jump eligibility check; gravity must apply after jump impulse on the same frame |
| 6 | Update `player_controller.gd` to pass jump input | Implementation Agent (Generalist) | `scripts/player_controller.gd`; `scripts/movement_simulation.gd` after Task 5 | `_physics_process()` reads `jump_pressed = Input.is_action_pressed("jump")` and `jump_just_pressed = Input.is_action_just_pressed("jump")`; both are passed to the updated `simulate()` call. No other changes to the controller. | Task 5 | `godot --headless --check-only` passes; player can jump in-editor play when Space is pressed; no double-jump occurs; coyote jump works when walking off a ledge | Input.is_action_just_pressed must be read in the same `_physics_process` frame as move_and_slide — already guaranteed by existing pipeline structure |
| 7 | Write jump simulation unit tests | Test Design Agent | Spec from Task 2; `scripts/movement_simulation.gd` after Task 5; `tests/test_movement_simulation.gd` as style reference | New file `tests/test_jump_simulation.gd` with `class_name JumpSimulationTests extends Object`. Must cover: (a) jump impulse applied on just_pressed from floor, (b) no jump when jump_consumed=true, (c) coyote timer decrements correctly, (d) coyote jump succeeds within window, (e) coyote jump fails after window expires, (f) jump_consumed resets on landing, (g) jump cut clamps upward velocity when button released, (h) jump cut does not affect downward velocity, (i) gravity still applies on jump frame, (j) no double jump (jump_consumed blocks second press) | Task 5 | Test file passes `godot --headless --check-only`; all test cases are named, documented, and assert specific numeric outputs using EPSILON=1e-4; `run_all() -> int` entry point returns total failure count | Tests must instantiate `MovementSimulation` directly and construct `MovementState` manually — no engine input or Node references |
| 8 | Write adversarial jump tests | Test Breaker Agent | Spec from Task 2; `tests/test_jump_simulation.gd` from Task 7; `tests/test_movement_simulation_adversarial.gd` as style reference | New file `tests/test_jump_simulation_adversarial.gd` with `class_name JumpSimulationAdversarialTests extends Object`. Must cover: (a) jump on first frame (coyote_timer=0.0, is_on_floor=true), (b) simultaneous jump_just_pressed + jump_consumed=true (no jump), (c) coyote_timer exactly 0.0 (boundary — no jump allowed), (d) coyote_timer set to coyote_time (maximum — jump allowed), (e) jump_cut_velocity=0.0 (edge config), (f) gravity=0.0 with jump (impulse formula must not produce NaN), (g) prior_state not mutated by simulate() for new fields (coyote_timer, jump_consumed) | Task 7 | All adversarial tests pass `godot --headless --check-only`; boundary cases at exactly `coyote_timer == 0.0` are explicitly tested; `run_all() -> int` entry point exists | The `gravity=0.0` + jump case requires careful formula handling: `sqrt(0)` = 0.0, which is valid (no impulse). Test must assert `velocity.y == 0.0` after a "jump" with zero gravity and zero height |
| 9 | Register new test suites in `tests/run_tests.gd` | Implementation Agent (Generalist) | `tests/run_tests.gd`; `tests/test_jump_simulation.gd` from Task 7; `tests/test_jump_simulation_adversarial.gd` from Task 8 | `run_tests.gd` updated with two new load/new/run_all blocks following the existing pattern. Suite names: `JumpSimulationTests`, `JumpSimulationAdversarialTests`. | Tasks 7 and 8 | `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` exits 0 with all suites passing; output includes suite headers for both new suites | Runner must not break if a suite file is missing — add null-check guard matching the existing pattern |
| 10 | Run full test suite and verify no regressions | Static QA Agent | `tests/run_tests.gd` and all test files; Godot binary at `/Applications/Godot.app/Contents/MacOS/Godot` | Terminal output showing all tests passing (exit code 0); count of passing tests reported; any failures investigated and resolved | Tasks 3-9 complete | Exit code 0; all previously passing tests (111 from M1-001) still pass; all new jump tests pass; `godot --headless --check-only` also passes | If M1-001 tests fail after signature change, the `simulate()` call in test files must also be updated; this is expected and in scope for this task |

### File Ownership Summary

| File | Change Type | Owning Tasks |
|------|-------------|-------------|
| `/Users/jacobbrandt/workspace/blobert/project.godot` | Modify — add `jump` action | Task 1 |
| `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/jump_simulation_spec.md` | Create | Task 2 |
| `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` | Modify — new fields, new params, extended simulate() | Tasks 3, 4, 5 |
| `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` | Modify — read jump input, update simulate() call | Task 6 |
| `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd` | Create | Task 7 |
| `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd` | Create | Task 8 |
| `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` | Modify — register new suites | Task 9 |

### Verification Command

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
```

Expected: exit code 0, all test suites pass.

---

## Specification

### Overview

Specification for the jump tuning feature (M1-002). Continues SPEC numbering from M1-001 (SPEC-1 through SPEC-14). Full spec document at `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/jump_simulation_spec.md`.

All ambiguities resolved and logged to `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/CHECKPOINTS.md` under entries `[M1-002] Spec — *`.

---

### Requirement SPEC-15: MovementState New Fields

#### 1. Spec Summary
- **Description:** The `MovementState` inner class in `movement_simulation.gd` gains two new typed fields carrying jump state across frames. `simulate()` reads them from `prior_state` as read-only inputs and writes computed values to the returned `MovementState`. The immutability contract from AC-4.2 extends to these new fields.
- **Constraints:** `coyote_timer: float = 0.0` and `jump_consumed: bool = false` declared inside `class MovementState:` after `is_on_floor`. Total field count becomes four. Both fields in `prior_state` must not be mutated by `simulate()`.
- **Assumptions:** Existing `_make_state_with()` helpers in test files leave new fields at defaults (0.0 / false), which is correct for all non-jump test scenarios.
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, `class MovementState:` block only.

#### 2. Acceptance Criteria
- **AC-15.1:** `MovementState.new().coyote_timer == 0.0` and `MovementState.new().jump_consumed == false`.
- **AC-15.2:** Exact declaration: `var coyote_timer: float = 0.0`.
- **AC-15.3:** Exact declaration: `var jump_consumed: bool = false`.
- **AC-15.4:** Both fields are declared inside `class MovementState:`, not at outer `MovementSimulation` scope.
- **AC-15.5:** After `simulate()` returns, `prior_state.coyote_timer` and `prior_state.jump_consumed` are unchanged.
- **AC-15.6:** `godot --headless --check-only` passes.
- **AC-15.7:** `MovementState` has exactly four fields: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`.

#### 3. Risk & Ambiguity Analysis
- Wrong placement at outer class scope is a silent error (AC-15.4 guards it). Additive change does not break existing tests if defaults are correct.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-16: MovementSimulation New Configuration Parameters

#### 1. Spec Summary
- **Description:** Three new `var` declarations on the outer `MovementSimulation` class expose jump-tuning configuration. They follow the existing naming and typing convention (plain `var`, `float`, explicit default).
- **Constraints:** `jump_height: float = 120.0`, `coyote_time: float = 0.1`, `jump_cut_velocity: float = -200.0`. Declared at outer class scope after existing five parameters. Negative `jump_cut_velocity` is intentional (upward velocity in Godot 2D screen space). Total config var count becomes eight.
- **Assumptions:** No assumptions beyond CHECKPOINTS.md [M1-002].
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, outer class body, between existing parameters and `simulate()`.

#### 2. Acceptance Criteria
- **AC-16.1:** `MovementSimulation.new().jump_height == 120.0` (EPSILON=1e-4).
- **AC-16.2:** `MovementSimulation.new().coyote_time == 0.1` (EPSILON=1e-4).
- **AC-16.3:** `MovementSimulation.new().jump_cut_velocity == -200.0` (EPSILON=1e-4).
- **AC-16.4:** Exact declarations: `var jump_height: float = 120.0`, `var coyote_time: float = 0.1`, `var jump_cut_velocity: float = -200.0`.
- **AC-16.5:** All three parameters are mutable at runtime and affect `simulate()` output.
- **AC-16.6:** `godot --headless --check-only` passes.
- **AC-16.7:** `MovementSimulation` has exactly eight configuration `var` fields after this change.

#### 3. Risk & Ambiguity Analysis
- Sign convention for `jump_cut_velocity`: must be `-200.0` (negative = upward). `coyote_time = 0.0` means no coyote window — expected behavior documented in spec.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-17: simulate() Extended Signature

#### 1. Spec Summary
- **Description:** `simulate()` signature changes from 3 to 5 parameters by inserting `jump_pressed: bool` and `jump_just_pressed: bool` between `input_axis` and `delta`. This is a breaking change requiring migration of all existing call sites.
- **Constraints:** Exact new signature: `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, delta: float) -> MovementState`. All existing call sites migrated to pass `false, false` for the new parameters. Migration targets: `player_controller.gd` (updated by SPEC-23), `test_movement_simulation.gd`, `test_movement_simulation_adversarial.gd`.
- **Assumptions:** `jump_just_pressed == true` with `jump_pressed == false` simultaneously is not a valid runtime state; the spec does not require handling it specially.
- **Scope / Context:** `func simulate()` declaration in `movement_simulation.gd` and all call sites.

#### 2. Acceptance Criteria
- **AC-17.1:** Exact signature line: `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, delta: float) -> MovementState:`.
- **AC-17.2:** `simulate(state, 0.0, false, false, 0.016)` produces identical results to the old three-argument behavior.
- **AC-17.3:** `godot --headless --check-only` passes after signature change and all call-site migrations.
- **AC-17.4:** All 111 M1-001 tests pass after call-site migration.
- **AC-17.5:** Existing sanitization logic (`effective_delta`, NaN/Inf clamp on `input_axis`) is retained.

#### 3. Risk & Ambiguity Analysis
- Missed call site causes parse error caught by `--check-only`. Wrong parameter order causes type error. `delta` must remain last.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-18: Jump Impulse Condition and Formula

#### 1. Spec Summary
- **Description:** When three conditions are simultaneously true — `jump_just_pressed`, floor or coyote eligibility, and `jump_consumed == false` — `simulate()` applies a jump impulse to `result.velocity.y` using the kinematic peak-height formula. Gravity is added afterward on the same frame.
- **Constraints:** Eligibility: `jump_just_pressed == true` AND (`prior_state.is_on_floor == true` OR `prior_state.coyote_timer > 0.0`) AND `prior_state.jump_consumed == false`. Impulse: `result.velocity.y = -sqrt(2.0 * gravity * jump_height)`. Then gravity adds: `result.velocity.y += gravity * effective_delta`. Formula uses `self.gravity` and `self.jump_height` (not hardcoded). `sqrt(0.0)` is valid (produces 0.0 impulse).
- **Assumptions:** Impulse is set before gravity in the same frame.
- **Scope / Context:** Vertical velocity computation block inside `simulate()`.

#### 2. Acceptance Criteria
- **AC-18.1:** At defaults (gravity=980, jump_height=120, delta=0.016), valid jump from floor: `result.velocity.y ≈ -484.9742 + 15.68 = -469.2942` (EPSILON=1e-4). Computed as `-sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016`.
- **AC-18.2:** `jump_just_pressed == false`, all else equal: `result.velocity.y == prior_state.velocity.y + gravity * delta` (no impulse).
- **AC-18.3:** `jump_just_pressed == true`, `jump_consumed == true`: no impulse. `result.velocity.y == prior_state.velocity.y + gravity * delta`.
- **AC-18.4:** `jump_just_pressed == true`, airborne, `coyote_timer == 0.0`: no impulse. `result.velocity.y == prior_state.velocity.y + gravity * delta`.
- **AC-18.5:** `sim.jump_height = 60.0`: `result.velocity.y ≈ -sqrt(117600.0) + 15.68 ≈ -327.4523` (EPSILON=1e-4) on valid jump.
- **AC-18.6:** `gravity == 0.0`, `jump_height == 120.0`, valid jump: `result.velocity.y == 0.0`. No NaN or Inf.
- **AC-18.7:** The formula uses GDScript built-in `sqrt()`.

#### 3. Risk & Ambiguity Analysis
- Gravity before impulse produces a different (wrong) value. Missing negation launches character downward. Hardcoded gravity/height fails AC-18.5 and AC-18.6.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-19: Coyote Time Logic

#### 1. Spec Summary
- **Description:** `simulate()` updates `result.coyote_timer` on every frame: reset to `coyote_time` when the prior state was on the floor; decrement by delta (clamped to zero) when airborne. The eligibility check for a coyote jump reads `prior_state.coyote_timer > 0.0` (strict greater-than). Timer update happens before eligibility check.
- **Constraints:** Reset rule: `prior_state.is_on_floor == true` → `result.coyote_timer = self.coyote_time`. Decrement rule: `prior_state.is_on_floor == false` → `result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)`. Eligibility uses `prior_state.coyote_timer`, not `result.coyote_timer`. `prior_state.coyote_timer` is never mutated.
- **Assumptions:** coyote_timer initial value is 0.0; on first airborne frame after landing `prior_state.is_on_floor` is true so timer is set to coyote_time.
- **Scope / Context:** `simulate()` body, before jump eligibility check.

#### 2. Acceptance Criteria
- **AC-19.1:** `prior_state.is_on_floor == true`, `prior_state.coyote_timer == 0.0`: `result.coyote_timer == 0.1` (EPSILON=1e-4).
- **AC-19.2:** `prior_state.is_on_floor == true`, `prior_state.coyote_timer == 0.05`: `result.coyote_timer == 0.1` (always reset to full window).
- **AC-19.3:** Airborne, `prior_state.coyote_timer == 0.1`, `delta == 0.016`: `result.coyote_timer == 0.084` (EPSILON=1e-4).
- **AC-19.4:** Airborne, `prior_state.coyote_timer == 0.01`, `delta == 0.016`: `result.coyote_timer == 0.0` (clamped, not -0.006).
- **AC-19.5:** Airborne, `prior_state.coyote_timer == 0.0`, any `delta > 0`: `result.coyote_timer == 0.0`.
- **AC-19.6:** Airborne, `prior_state.coyote_timer == 0.05`, `jump_just_pressed == true`, `jump_consumed == false`: jump impulse applied.
- **AC-19.7:** Airborne, `prior_state.coyote_timer == 0.0`, `jump_just_pressed == true`, `jump_consumed == false`: no impulse applied. `result.velocity.y == prior_state.velocity.y + gravity * effective_delta`.
- **AC-19.8:** `prior_state.coyote_timer` unchanged after `simulate()` returns.
- **AC-19.9:** `sim.coyote_time = 0.2`: floor reset produces `result.coyote_timer == 0.2`.

#### 3. Risk & Ambiguity Analysis
- Timer update after eligibility check gives player one extra frame (off-by-one). Using `result.coyote_timer` in eligibility check also gives extra frame. `coyote_timer == 0.0` boundary is strict less-than, not less-than-or-equal.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-20: Jump Cut Condition and Clamp

#### 1. Spec Summary
- **Description:** After all vertical velocity computation (impulse + gravity), if the jump button is not held and the character is ascending faster than `jump_cut_velocity`, the velocity is clamped to `jump_cut_velocity`. This gives the player variable jump height by releasing the button early.
- **Constraints:** Condition: `jump_pressed == false` AND `result.velocity.y < self.jump_cut_velocity`. Action: `result.velocity.y = self.jump_cut_velocity`. Applied after gravity. Does not apply when falling (positive velocity.y cannot be less than -200.0). Does not apply when `jump_pressed == true`.
- **Assumptions:** jump_cut_velocity is -200.0 by default (negative = upward). Clamp on exact boundary (`== jump_cut_velocity`) is a no-op per strict less-than condition.
- **Scope / Context:** End of vertical velocity block in `simulate()`, after gravity addition.

#### 2. Acceptance Criteria
- **AC-20.1:** `jump_pressed == false`, `result.velocity.y` after gravity is more negative than `jump_cut_velocity`: result clamped to `jump_cut_velocity`.
- **AC-20.2:** `prior_state.velocity.y = -450.0`, `jump_pressed = false`, `delta = 0.016`: after gravity `-434.32 < -200.0` → `result.velocity.y == -200.0` (EPSILON=1e-4).
- **AC-20.3:** `prior_state.velocity.y = 50.0` (falling), `jump_pressed = false`, `delta = 0.016`: `65.68 < -200.0` is false → `result.velocity.y == 65.68` (EPSILON=1e-4). No clamp.
- **AC-20.4:** `jump_pressed = true`, `prior_state.velocity.y = -450.0`, `delta = 0.016`: no clamp (button held). `result.velocity.y == -434.32` (EPSILON=1e-4).
- **AC-20.5:** `result.velocity.y` after gravity exactly equals `jump_cut_velocity = -200.0`: no clamp (strict less-than). `result.velocity.y == -200.0`.
- **AC-20.6:** `sim.jump_cut_velocity = -100.0`, `prior_state.velocity.y = -200.0`, `jump_pressed = false`, `delta = 0.016`: `-184.32 < -100.0` → clamped to `-100.0` (EPSILON=1e-4).
- **AC-20.7:** `sim.jump_cut_velocity = 0.0`, `prior_state.velocity.y = -200.0`, `jump_pressed = false`, `delta = 0.016`: `-184.32 < 0.0` → clamped to `0.0` (EPSILON=1e-4).
- **AC-20.8:** Jump cut evaluates `result.velocity.y` after gravity has been added (not before).

#### 3. Risk & Ambiguity Analysis
- Applying jump cut before gravity produces a slightly incorrect cap. Condition with `>=` instead of `>` changes boundary behavior. Jump cut does not require jump to have just fired — it applies any frame the button is released while ascending.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-21: Double-Jump Prevention via jump_consumed

#### 1. Spec Summary
- **Description:** `jump_consumed` prevents repeated jumps during a single airborne phase. It is set `true` when a jump fires and reset `false` when the player is on the floor in the prior state (i.e., on landing or while grounded).
- **Constraints:** On jump: `result.jump_consumed = true`. On grounded prior state with no jump: `result.jump_consumed = false`. On airborne prior state with no jump: `result.jump_consumed = prior_state.jump_consumed`. `prior_state.jump_consumed` is never mutated.
- **Assumptions:** jump_consumed reset uses `prior_state.is_on_floor`, not `result.is_on_floor` (same value, but reads from prior_state for consistency).
- **Scope / Context:** `simulate()` body, jump_consumed assignment logic.

#### 2. Acceptance Criteria
- **AC-21.1:** Jump fires → `result.jump_consumed == true`.
- **AC-21.2:** Frame after jump: `prior_state.jump_consumed = true`, `is_on_floor = false`, `jump_just_pressed = true` → no jump. `result.velocity.y == prior_state.velocity.y + gravity * delta`. `result.jump_consumed == true`.
- **AC-21.3:** Landing frame: `prior_state.is_on_floor = true`, `prior_state.jump_consumed = true` → `result.jump_consumed == false`.
- **AC-21.4:** Airborne, `prior_state.jump_consumed = true`, no jump → `result.jump_consumed == true` (carried forward).
- **AC-21.5:** `prior_state.jump_consumed` unchanged after `simulate()`.
- **AC-21.6:** Fresh `MovementState` has `jump_consumed = false`; first jump fires correctly, produces `result.jump_consumed = true`.
- **AC-21.7:** Airborne, `jump_consumed = true`, button released then re-pressed (`jump_just_pressed = true`): no jump. Double-jump blocked.

#### 3. Risk & Ambiguity Analysis
- Resetting on `result.is_on_floor` vs `prior_state.is_on_floor` has the same effect (they are equal) but reading prior_state is consistent with function contract. Coyote jump correctly sets `jump_consumed = true` preventing a follow-up coyote attempt.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-22: project.godot — jump Input Action Registration

#### 1. Spec Summary
- **Description:** The `jump` input action is added to `project.godot`'s `[input]` section, bound to Space bar (physical_keycode=32), in the same object-literal format as existing actions.
- **Constraints:** Action name: `"jump"`. `physical_keycode = 32`, `unicode = 32`, `keycode = 0`. `deadzone = 0.5`. One event per action. All other fields mirror the existing `move_left` entry format. Added after the `move_right` entry.
- **Assumptions:** physical_keycode 32 = Space bar in Godot 4.
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/project.godot`, `[input]` section.

#### 2. Acceptance Criteria
- **AC-22.1:** `[input]` section contains a `jump` entry in object-literal dictionary format.
- **AC-22.2:** The single event has `physical_keycode:32`.
- **AC-22.3:** `deadzone` is `0.5`.
- **AC-22.4:** `godot --headless --check-only` passes.
- **AC-22.5:** `Input.is_action_pressed("jump")` resolves without error at runtime.
- **AC-22.6:** Exact text block to add (Godot 4.3 format):
  ```
  jump={
  "deadzone": 0.5,
  "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"echo":false,"script":null)
  ]
  }
  ```

#### 3. Risk & Ambiguity Analysis
- `keycode` vs `physical_keycode` — must use `physical_keycode = 32`. Wrong format (e.g., keycode=32) still works but is non-physical. Engine-generated format takes precedence over AC-22.6 if there is a discrepancy.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-23: player_controller.gd — Jump Input Reading and Passing

#### 1. Spec Summary
- **Description:** `player_controller.gd`'s `_physics_process()` is updated to read two jump input booleans and pass them to the extended `simulate()` call. The new fields `coyote_timer` and `jump_consumed` from `next_state` must be copied back to `_current_state` after each frame so they persist across frames.
- **Constraints:** `var jump_pressed: bool = Input.is_action_pressed("jump")` and `var jump_just_pressed: bool = Input.is_action_just_pressed("jump")` read in Step 1, after `input_axis`. `simulate()` call updated to five arguments. After `move_and_slide()`, copy `_current_state.coyote_timer = next_state.coyote_timer` and `_current_state.jump_consumed = next_state.jump_consumed`. No movement logic added to controller.
- **Assumptions:** No assumptions beyond CHECKPOINTS.md [M1-002].
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd`, `_physics_process()` only.

#### 2. Acceptance Criteria
- **AC-23.1:** `jump_pressed` and `jump_just_pressed` declared with `bool` type, read before `simulate()` call.
- **AC-23.2:** `simulate()` call: `_simulation.simulate(_current_state, input_axis, jump_pressed, jump_just_pressed, delta)`.
- **AC-23.3:** After `move_and_slide()`: `_current_state.coyote_timer = next_state.coyote_timer` and `_current_state.jump_consumed = next_state.jump_consumed`.
- **AC-23.4:** `godot --headless --check-only` passes.
- **AC-23.5:** Controller contains no movement math, no jump formulas, no direct `velocity.y` manipulation beyond existing lines.
- **AC-23.6:** In-editor play (manual): Space causes jump; releasing early produces shorter jump; coyote jump works within 0.1s after walking off ledge.

#### 3. Risk & Ambiguity Analysis
- Not copying `coyote_timer`/`jump_consumed` back to `_current_state` silently breaks coyote time and double-jump prevention (both always see stale default values). This is the most likely implementation error.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-24: Frame-Rate Independence of New Timer Logic

#### 1. Spec Summary
- **Description:** `coyote_timer` decrement is frame-rate independent via `effective_delta`. The jump impulse is inherently frame-rate independent (instantaneous assignment). Jump cut is a threshold clamp (not time-based). `jump_consumed` flag transitions are event-based.
- **Constraints:** `effective_delta` is used for timer decrement. Two half-steps equal one full step within EPSILON=1e-4 for the decrement operation (linear subtraction is perfectly frame-rate independent). Existing SPEC-12 frame-rate tests must pass after call-site migration.
- **Assumptions:** No assumptions beyond CHECKPOINTS.md [M1-002].
- **Scope / Context:** Tests in `test_jump_simulation.gd`.

#### 2. Acceptance Criteria
- **AC-24.1:** Two half-steps of `delta = 0.05` from `coyote_timer = 0.1` produce same result (`0.0`) as one full step of `delta = 0.1`.
- **AC-24.2:** Two half-steps of `delta = 0.008` from `coyote_timer = 0.1` produce `0.084`; one full step of `delta = 0.016` from `coyote_timer = 0.1` also produces `0.084`. Both within EPSILON=1e-4.
- **AC-24.3:** Jump impulse value (`-sqrt(2.0 * gravity * jump_height)`) is the same regardless of delta (it is an assignment, not scaled by delta).
- **AC-24.4:** All existing SPEC-12 frame-rate independence tests pass after call-site migration.

#### 3. Risk & Ambiguity Analysis
- Using raw `delta` instead of `effective_delta` for timer decrement causes different behavior with negative delta. Since decrement is linear, no overshoot risk exists in the test range.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Requirement SPEC-25: Backward Compatibility — M1-001 Test Migration

#### 1. Spec Summary
- **Description:** The signature change in SPEC-17 is a breaking change. All existing three-argument `simulate()` call sites in test files are migrated to five-argument form with `false, false` for the new parameters. All 111 pre-existing M1-001 tests must continue to pass unchanged. No assertion values change.
- **Constraints:** Migration targets: `test_movement_simulation.gd` and `test_movement_simulation_adversarial.gd` — every `sim.simulate(state, axis, delta)` becomes `sim.simulate(state, axis, false, false, delta)`. `player_controller.gd` is updated by SPEC-23 (not to `false, false`). `_make_state_with()` helper is not modified. New fields default to 0.0/false in all migrated tests, which is the correct non-jump baseline.
- **Assumptions:** See CHECKPOINTS.md [M1-002] — Spec — existing test suite call sites.
- **Scope / Context:** `test_movement_simulation.gd` and `test_movement_simulation_adversarial.gd`, call-site argument lists only.

#### 2. Acceptance Criteria
- **AC-25.1:** No three-argument `simulate()` call remains in `test_movement_simulation.gd` (verified by grep).
- **AC-25.2:** No three-argument `simulate()` call remains in `test_movement_simulation_adversarial.gd` (verified by grep).
- **AC-25.3:** Both files parse without error under `godot --headless --check-only`.
- **AC-25.4:** `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` exits with code 0; all 111 pre-existing tests pass.
- **AC-25.5:** No assertion values are changed in the migrated files. Only argument lists are changed.
- **AC-25.6:** `_make_state_with(vx, vy, on_floor)` helper is not modified.
- **AC-25.7:** `test_spec13_headless_smoke()` migrated to `sim.simulate(state, 1.0, false, false, 0.016)` and continues to pass.

#### 3. Risk & Ambiguity Analysis
- Missed call site causes `godot --headless --check-only` parse error. Wrong argument position (inserting at positions 4-5 instead of 3-4) causes type mismatch on `delta`. New fields in result objects have default values (coyote_timer reset to 0.1 when on_floor=true, etc.) that do not affect any existing assertions since no existing assertion reads those fields.

#### 4. Clarifying Questions
None. All ambiguities logged in CHECKPOINTS.md [M1-002].

---

### Order of Operations Within simulate() (Normative Summary)

The following sequence is normative. All acceptance criteria are consistent with this order:

1. Sanitize `effective_delta = max(0.0, delta)`.
2. Sanitize `input_axis` (NaN → 0.0, Inf → clamp ±1.0).
3. Allocate `result: MovementState = MovementState.new()`.
4. Coyote timer update (SPEC-19): reset if on floor, else decrement clamped to 0.
5. jump_consumed carry-forward / landing reset (SPEC-21): false if on floor, else carry from prior.
6. Jump eligibility and impulse (SPEC-18): if eligible, set `result.velocity.y = -sqrt(2*gravity*jump_height)` and `result.jump_consumed = true`; else `result.velocity.y = prior_state.velocity.y`.
7. Horizontal velocity (SPEC-5, unchanged from M1-001).
8. Gravity (SPEC-6): `result.velocity.y += gravity * effective_delta`.
9. Jump cut (SPEC-20): if `NOT jump_pressed AND result.velocity.y < jump_cut_velocity`, clamp.
10. is_on_floor pass-through (AC-4.3): `result.is_on_floor = prior_state.is_on_floor`.
11. Return `result`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Engine Integration Agent

## Validation Status
- Tests: PASS — 243 total (53 movement + 58 movement adversarial + 57 jump + 75 jump adversarial), exit code 0
- Static QA: PASS — godot --headless --import succeeds, no parse errors
- Integration: PASS — project.godot, player_controller.gd, and all test files consistent

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason
Engine Integration Agent completed Tasks 6, 9, 10: (1) project.godot updated with jump input action bound to Space bar (physical_keycode=32), deadzone=0.5, Godot 4.3 object-literal format — SPEC-22; (2) player_controller.gd updated to read jump_pressed and jump_just_pressed each physics frame, pass both to 5-arg simulate(), copy coyote_timer and jump_consumed back to _current_state after slide, and expose jump_height/coyote_time/jump_cut_velocity as @export vars copied to simulation in _ready() — SPEC-23; (3) four test bugs fixed: tb007 gravity test migrated with jump_pressed=true to suppress jump cut; spec16/AC-16.5 impulse test corrected to use jump_pressed=true; TB-J-011 and TB-J-012c expected values corrected to reflect that SPEC-18 eligibility reads prior_state.jump_consumed not result.jump_consumed (same-frame re-jump is blocked when prior consumed=true). All decisions logged to CHECKPOINTS.md under [M1-002] Engine Integration Agent entries. Full test suite: 243 tests, 0 failures, exit code 0.
