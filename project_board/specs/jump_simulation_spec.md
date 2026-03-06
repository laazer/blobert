# Jump Simulation Specification
# M1-002 — jump_tuning.md
# SPEC-15 through SPEC-25
#
# Prerequisite specs: SPEC-1 through SPEC-14 (movement_controller.md / M1-001)
# Continuing numbering from SPEC-14.
#
# Files affected:
#   /Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd
#   /Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd
#   /Users/jacobbrandt/workspace/blobert/project.godot
#   /Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd
#   /Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd (migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd (migration only)

---

## Requirement SPEC-15: MovementState New Fields

### 1. Spec Summary

- **Description:** The `MovementState` inner class inside `movement_simulation.gd` gains two new typed fields: `coyote_timer: float` and `jump_consumed: bool`. These fields carry jump-related state across frames via the same immutable-input / fresh-output contract already established for `velocity` and `is_on_floor`. `simulate()` reads them from `prior_state` and writes computed values to the new `MovementState` it returns.
- **Constraints:**
  - Both fields must be declared inside the `class MovementState:` block in `movement_simulation.gd`, after the existing `is_on_floor` field.
  - `coyote_timer` type is `float`. Default value is `0.0`.
  - `jump_consumed` type is `bool`. Default value is `false`.
  - No other fields or methods are added to `MovementState` in this milestone.
  - `simulate()` must never mutate `prior_state.coyote_timer` or `prior_state.jump_consumed`. Both fields in `prior_state` must remain unchanged after `simulate()` returns (consistent with the existing immutability contract from AC-4.2).
  - GDScript must be statically typed throughout; no untyped variable declarations.
- **Assumptions:**
  - The existing `_make_state_with(vx, vy, on_floor)` helper in the test file constructs a `MovementState` and then sets fields directly. After SPEC-15, `coyote_timer` and `jump_consumed` on that constructed state will hold their declared defaults (0.0 and false respectively) unless the test explicitly sets them. This is correct default behavior and requires no change to the helper signature.
- **Scope / Context:** Applies exclusively to the `class MovementState:` block inside `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`. No other file is modified by this requirement alone.

### 2. Acceptance Criteria

- **AC-15.1:** `MovementState.new()` produces an object where `coyote_timer == 0.0` and `jump_consumed == false`, verifiable by direct field access immediately after construction with no intervening calls.
- **AC-15.2:** `coyote_timer` is declared with the GDScript type annotation `float` and the initializer `= 0.0`. The exact declaration line is `var coyote_timer: float = 0.0`.
- **AC-15.3:** `jump_consumed` is declared with the GDScript type annotation `bool` and the initializer `= false`. The exact declaration line is `var jump_consumed: bool = false`.
- **AC-15.4:** Both new fields appear in the `class MovementState:` block only, not at the outer `MovementSimulation` class scope.
- **AC-15.5:** After calling `simulate(prior_state, axis, false, false, delta)` with any valid inputs, `prior_state.coyote_timer` retains its original value and `prior_state.jump_consumed` retains its original value (no mutation of prior state).
- **AC-15.6:** `godot --headless --check-only` passes with no parse errors after adding these fields.
- **AC-15.7:** The total field count of `MovementState` after this change is exactly four: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`. No additional fields exist.

### 3. Risk & Ambiguity Analysis

- **Risk R-15.1 (additive change breaks existing tests):** Adding fields to `MovementState` with correct defaults does not change the output of existing `simulate()` calls for horizontal/gravity behavior. The existing test assertions on `velocity` and `is_on_floor` are unaffected. However, if an implementer accidentally removes an existing field default or reorders field declarations in a way that Godot parses differently, existing tests can fail silently. The acceptance criteria explicitly verify the total field count.
- **Risk R-15.2 (wrong placement):** Fields declared at the outer `MovementSimulation` scope instead of inside `class MovementState:` would still parse but would be inaccessible via `MovementState.new().coyote_timer`. AC-15.4 guards against this.
- **Risk R-15.3 (type annotation omitted):** GDScript allows untyped `var coyote_timer = 0.0`. The spec requires typed declarations per the existing codebase convention (SPEC-14). Missing annotations are a soft failure caught by `--check-only` only if the project enables strict typing; the test should verify field access returns the correct type.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-16: MovementSimulation New Configuration Parameters

### 1. Spec Summary

- **Description:** The `MovementSimulation` class (outer class in `movement_simulation.gd`) gains three new `var` declarations representing jump-tuning configuration: `jump_height`, `coyote_time`, and `jump_cut_velocity`. These follow the same convention as existing parameters (`max_speed`, `acceleration`, etc.): plain `var` with a `float` type annotation and an explicit default value. No `@export` annotation is used on `MovementSimulation` fields (it extends `RefCounted`, not `Node`).
- **Constraints:**
  - `jump_height: float = 120.0` — target apex height in pixels, used to derive the jump impulse at runtime.
  - `coyote_time: float = 0.1` — coyote window in seconds; the number of seconds after leaving a floor edge during which a jump is still permitted.
  - `jump_cut_velocity: float = -200.0` — minimum upward velocity cap in pixels per second (negative = upward in Godot 2D screen space). Must be a negative or zero float. A value of 0.0 means jump cut eliminates all upward velocity instantly.
  - All three are declared at the outer `MovementSimulation` class scope, not inside `MovementState`.
  - Parameter names must exactly match the identifiers `jump_height`, `coyote_time`, `jump_cut_velocity` — these names are referenced by `simulate()` (SPEC-18 through SPEC-20), by test files (Task 7/8), and by `player_controller.gd` (SPEC-23) indirectly. Any name mismatch will cause parse errors.
  - Undefined behavior is defined for: negative `jump_height` (produces negative impulse, character moves downward on "jump"), negative `coyote_time` (coyote timer decrements below 0.0; clamp to 0.0 prevents negative timer), positive `jump_cut_velocity` (clamp would apply unconditionally and pull velocity down, not up — this is a nonsensical configuration). These are configuration errors and are not required to produce specific results, but must not cause NaN, Inf, or crashes.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-002].
- **Scope / Context:** Applies to the outer `MovementSimulation` class body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`. The three new `var` declarations should appear after the existing five parameters and before `simulate()`, with doc-comment annotations consistent with the existing style.

### 2. Acceptance Criteria

- **AC-16.1:** `MovementSimulation.new().jump_height == 120.0` (tolerance EPSILON=1e-4).
- **AC-16.2:** `MovementSimulation.new().coyote_time == 0.1` (tolerance EPSILON=1e-4).
- **AC-16.3:** `MovementSimulation.new().jump_cut_velocity == -200.0` (tolerance EPSILON=1e-4).
- **AC-16.4:** Each parameter is declared with an explicit `float` type annotation. The exact declarations are:
  - `var jump_height: float = 120.0`
  - `var coyote_time: float = 0.1`
  - `var jump_cut_velocity: float = -200.0`
- **AC-16.5:** All three parameters are mutable at runtime: a test can assign `sim.jump_height = 60.0` and then call `simulate()` and observe a different jump impulse in the result.
- **AC-16.6:** `godot --headless --check-only` passes after adding these three declarations.
- **AC-16.7:** The total count of configuration `var` fields on `MovementSimulation` after this change is exactly eight: `max_speed`, `acceleration`, `friction`, `air_deceleration`, `gravity`, `jump_height`, `coyote_time`, `jump_cut_velocity`.

### 3. Risk & Ambiguity Analysis

- **Risk R-16.1 (sign convention for jump_cut_velocity):** `jump_cut_velocity = -200.0` is negative because Godot 2D screen space has Y increasing downward. Upward velocity is negative. An implementer unfamiliar with Godot's coordinate system might negate the value, making it positive and causing the jump cut to never trigger (since `velocity.y < 200.0` would always be true for downward-moving characters). The spec and AC-16.4 state the literal value `-200.0` to prevent this confusion.
- **Risk R-16.2 (jump_height unit confusion):** `jump_height` is in pixels, not tiles or world units. The formula in SPEC-18 converts it to an impulse. An implementer must not treat it as a velocity value directly.
- **Risk R-16.3 (coyote_time = 0.0 edge case):** Setting `coyote_time = 0.0` means the coyote window is zero seconds wide. After leaving the floor, `coyote_timer` is set to `coyote_time = 0.0` on the departure frame (since the previous frame had `is_on_floor = true`), and then on the very next frame (first airborne frame) it is decremented to `max(0.0, 0.0 - delta) = 0.0`. A jump on the first airborne frame checks `coyote_timer > 0.0`, which is false. Therefore, with `coyote_time = 0.0`, coyote jumps are never possible. This is the expected behavior and is documented here explicitly.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-17: simulate() Extended Signature

### 1. Spec Summary

- **Description:** The `simulate()` function signature is changed from the M1-001 form `func simulate(prior_state: MovementState, input_axis: float, delta: float) -> MovementState` to the new five-parameter form. The two new boolean parameters `jump_pressed` and `jump_just_pressed` are inserted between `input_axis` and `delta`. This is a breaking change to all existing call sites.
- **Constraints:**
  - New signature (exact): `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, delta: float) -> MovementState`
  - Parameter names must exactly match: `prior_state`, `input_axis`, `jump_pressed`, `jump_just_pressed`, `delta`.
  - All parameters must carry explicit GDScript type annotations as shown.
  - Return type annotation `-> MovementState` is retained.
  - The function remains a public method on `MovementSimulation`.
  - The function remains pure: no engine singletons, no Node references, no I/O. Fully testable headlessly.
  - `jump_pressed: bool` represents whether the jump input action is currently held down this frame (maps to `Input.is_action_pressed("jump")` in the controller).
  - `jump_just_pressed: bool` represents whether the jump input action was first pressed on this exact frame (maps to `Input.is_action_just_pressed("jump")` in the controller). `jump_just_pressed` is `true` for exactly one physics frame when the button transitions from released to pressed.
  - `jump_just_pressed` can only be `true` on frames where `jump_pressed` is also `true`. The spec does not require the simulation to validate or enforce this; it is guaranteed by the engine's input system and the controller layer. If `jump_just_pressed == true` and `jump_pressed == false` are passed simultaneously, behavior is defined by the logic in SPEC-18 through SPEC-21: the jump eligibility check uses only `jump_just_pressed` for the trigger, so a jump would fire but jump cut would immediately clamp if the velocity is above `jump_cut_velocity`. This edge case is not a valid runtime state and is not required to produce a meaningful result.
  - **Migration requirement:** Every existing call site that calls `simulate()` with three arguments must be updated to pass `false, false` for `jump_pressed` and `jump_just_pressed`. This preserves all existing behavior: no jump occurs, no coyote timer effect, no jump cut. The affected call sites are:
    - `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` (updated per SPEC-23)
    - `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd` (every `sim.simulate(state, axis, delta)` call becomes `sim.simulate(state, axis, false, false, delta)`)
    - `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd` (same pattern)
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-002].
- **Scope / Context:** The `func simulate(...)` declaration and body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, plus all call sites listed above.

### 2. Acceptance Criteria

- **AC-17.1:** The exact function declaration line is `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, delta: float) -> MovementState:`.
- **AC-17.2:** Calling `simulate(state, 0.0, false, false, 0.016)` (both booleans false) produces identical results to the old three-argument behavior: horizontal and gravity formulas operate as before, no jump impulse, no coyote timer change beyond the timer update rule, no jump cut.
- **AC-17.3:** `godot --headless --check-only` passes on the entire project after the signature change and all call-site migrations.
- **AC-17.4:** The existing 111 M1-001 tests (in `test_movement_simulation.gd` and `test_movement_simulation_adversarial.gd`) all pass after call-site migration, confirming no regression in horizontal/gravity behavior.
- **AC-17.5:** The function body retains all existing sanitization logic: `effective_delta = max(0.0, delta)`, NaN/Inf clamping on `input_axis`. New parameters `jump_pressed` and `jump_just_pressed` are not sanitized (they are booleans with no invalid values).

### 3. Risk & Ambiguity Analysis

- **Risk R-17.1 (call-site migration missed):** If any call site is not updated, `godot --headless --check-only` will report a parse or type error. The three files listed are the only known call sites; if additional scripts reference `simulate()`, they must also be updated.
- **Risk R-17.2 (parameter order confusion):** The order `jump_pressed, jump_just_pressed` (held before just-pressed) is the conventional Godot pattern. Reversing the order would cause the controller to pass `jump_just_pressed` where `jump_pressed` is expected, making jump cut never trigger (since the held signal would be used as the single-frame trigger). AC-17.1 specifies the exact order.
- **Risk R-17.3 (delta position):** `delta` remains the last parameter. An implementer might move it to match a different calling convention. AC-17.1 fixes the position.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-18: Jump Impulse Condition and Formula

### 1. Spec Summary

- **Description:** On a frame where jump eligibility conditions are met, `simulate()` applies a jump impulse to `result.velocity.y`. The impulse is computed from the configured `jump_height` and `gravity` parameters using the kinematic formula that derives the velocity required to reach a given apex height under constant gravity.
- **Constraints:**
  - Jump eligibility condition (all of the following must be true simultaneously):
    1. `jump_just_pressed == true`
    2. `prior_state.is_on_floor == true` OR `prior_state.coyote_timer > 0.0`
    3. `prior_state.jump_consumed == false`
  - When the condition is met, the result velocity on the Y axis is set as follows (before gravity is added):
    - `result.velocity.y = -sqrt(2.0 * gravity * jump_height)`
    - Where `gravity` is `self.gravity` (the `MovementSimulation` instance's configured parameter) and `jump_height` is `self.jump_height`.
    - The negative sign produces upward motion in Godot 2D screen space (Y increases downward).
  - After the impulse is set, gravity is added to `result.velocity.y` in the same frame (see SPEC-20 order-of-operations note and the existing SPEC-6 gravity rule):
    - `result.velocity.y = result.velocity.y + gravity * effective_delta`
    - This means on the jump frame, `result.velocity.y = -sqrt(2.0 * gravity * jump_height) + gravity * effective_delta`.
  - When the jump condition is NOT met, the jump impulse is not applied and `result.velocity.y` proceeds from `prior_state.velocity.y + gravity * effective_delta` as in M1-001.
  - Gravity applied on the jump frame uses the same `effective_delta` (clamped to `max(0.0, delta)`) as all other calculations.
  - The formula must use `self.gravity` and `self.jump_height` — not hardcoded constants. Changing `sim.jump_height` or `sim.gravity` must immediately change the derived impulse on the next jump.
  - If `gravity == 0.0` and `jump_height == 0.0`: `sqrt(0.0) = 0.0`, so the impulse is 0.0 and the result is numerically valid (no NaN).
  - If `gravity == 0.0` and `jump_height > 0.0`: `sqrt(2.0 * 0.0 * jump_height) = sqrt(0.0) = 0.0`, impulse is 0.0. Numerically valid.
  - If `gravity > 0.0` and `jump_height == 0.0`: `sqrt(0.0) = 0.0`, impulse is 0.0. Numerically valid.
- **Assumptions:** None beyond those in CHECKPOINTS.md [M1-002].
- **Scope / Context:** Inside the `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, specifically the vertical velocity computation block.

### 2. Acceptance Criteria

- **AC-18.1:** When `jump_just_pressed == true`, `prior_state.is_on_floor == true`, `prior_state.jump_consumed == false`, `gravity == 980.0`, `jump_height == 120.0`, `delta == 0.016`: `result.velocity.y` equals `-sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016`. Numerically: `-484.9742... + 15.68 = -469.2942...`. Verified within EPSILON=1e-4.
- **AC-18.2:** When `jump_just_pressed == false` (everything else identical to AC-18.1): `result.velocity.y == prior_state.velocity.y + gravity * delta` (standard gravity, no impulse). For `prior_state.velocity.y == 0.0`, `result.velocity.y == 15.68`.
- **AC-18.3:** When `jump_just_pressed == true` but `prior_state.jump_consumed == true`: no jump impulse is applied. `result.velocity.y == prior_state.velocity.y + gravity * delta`.
- **AC-18.4:** When `jump_just_pressed == true` but `prior_state.is_on_floor == false` AND `prior_state.coyote_timer == 0.0`: no jump impulse is applied. `result.velocity.y == prior_state.velocity.y + gravity * delta`.
- **AC-18.5:** Changing `sim.jump_height = 60.0` (all other defaults) produces `result.velocity.y = -sqrt(2.0 * 980.0 * 60.0) + 980.0 * 0.016 = -sqrt(117600.0) + 15.68 ≈ -343.1323 + 15.68 = -327.4523...` (verified within EPSILON=1e-4) when a valid jump fires.
- **AC-18.6:** With `gravity == 0.0` and `jump_height == 120.0` and a valid jump condition: `result.velocity.y == 0.0` (impulse is 0.0, gravity contribution is 0.0). No NaN or Inf in result.
- **AC-18.7:** The impulse formula uses the GDScript built-in `sqrt()` function — not a manual approximation or a hardcoded value.

### 3. Risk & Ambiguity Analysis

- **Risk R-18.1 (gravity applied before impulse):** If the implementation adds gravity to `prior_state.velocity.y` first and then adds the impulse, the result will differ by `gravity * delta` from what AC-18.1 specifies. The spec requires impulse to be set first, then gravity added. The acceptance criteria provide an exact numeric check.
- **Risk R-18.2 (impulse not negated):** A common error is to assign `result.velocity.y = sqrt(...)` without the negation, launching the character downward instead of upward. AC-18.1 requires a negative result.
- **Risk R-18.3 (using gravity from Godot's physics server instead of self.gravity):** The simulation must only use `self.gravity` (the `MovementSimulation` instance parameter). AC-18.5 verifies that changing `sim.jump_height` produces the expected result, and AC-18.6 verifies that `gravity == 0.0` produces zero impulse — both tests fail if a hardcoded value is used.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-19: Coyote Time Logic

### 1. Spec Summary

- **Description:** `simulate()` updates `result.coyote_timer` on every frame based on whether the player was on the floor in the prior state. The coyote timer provides a brief window to jump after walking off a ledge, without the player pressing jump before leaving the floor.
- **Constraints:**
  - **Timer update rule (applied every frame, before jump eligibility check):**
    - If `prior_state.is_on_floor == true`: `result.coyote_timer = self.coyote_time` (reset to the full window).
    - If `prior_state.is_on_floor == false`: `result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)` (decrement toward zero, clamp at zero).
  - The timer update must happen before the jump eligibility check (SPEC-18). This ensures that on the frame a coyote jump is triggered, the eligibility check reads the already-decremented timer from `prior_state.coyote_timer` (not `result.coyote_timer`). The eligibility check uses `prior_state.coyote_timer > 0.0`, not `result.coyote_timer`.
  - `result.coyote_timer` is always a value in the range `[0.0, self.coyote_time]` when `coyote_time >= 0.0`.
  - `effective_delta` is `max(0.0, delta)` (same sanitized value used throughout `simulate()`).
  - `prior_state.coyote_timer` is never mutated.
- **Assumptions:** See CHECKPOINTS.md [M1-002] — jump_consumed reset uses prior_state.is_on_floor, coyote_timer initial value is 0.0.
- **Scope / Context:** Inside the `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-19.1 (reset on floor):** When `prior_state.is_on_floor == true` and `prior_state.coyote_timer == 0.0`: `result.coyote_timer == self.coyote_time` (default 0.1). Verified within EPSILON=1e-4.
- **AC-19.2 (reset on floor regardless of prior timer value):** When `prior_state.is_on_floor == true` and `prior_state.coyote_timer == 0.05` (arbitrary mid-value): `result.coyote_timer == self.coyote_time` (0.1). The timer is always reset to the full window when on floor.
- **AC-19.3 (decrement when airborne):** When `prior_state.is_on_floor == false` and `prior_state.coyote_timer == 0.1` and `delta == 0.016`: `result.coyote_timer == max(0.0, 0.1 - 0.016) == 0.084` (verified within EPSILON=1e-4).
- **AC-19.4 (decrement clamps at zero, not negative):** When `prior_state.is_on_floor == false` and `prior_state.coyote_timer == 0.01` and `delta == 0.016` (step > remaining): `result.coyote_timer == 0.0` (not -0.006).
- **AC-19.5 (already zero stays zero):** When `prior_state.is_on_floor == false` and `prior_state.coyote_timer == 0.0` and any `delta > 0.0`: `result.coyote_timer == 0.0`.
- **AC-19.6 (coyote jump within window):** When `prior_state.is_on_floor == false`, `prior_state.coyote_timer == 0.05` (> 0.0), `jump_just_pressed == true`, `jump_consumed == false`: a jump impulse is applied (result.velocity.y equals the impulse formula result, not gravity-only).
- **AC-19.7 (coyote jump fails after window):** When `prior_state.is_on_floor == false`, `prior_state.coyote_timer == 0.0`, `jump_just_pressed == true`, `jump_consumed == false`: no jump impulse is applied. `result.velocity.y == prior_state.velocity.y + gravity * effective_delta`.
- **AC-19.8 (timer not mutated in prior_state):** After any `simulate()` call, `prior_state.coyote_timer` retains its original value.
- **AC-19.9 (custom coyote_time respected):** With `sim.coyote_time = 0.2`: when `prior_state.is_on_floor == true`, `result.coyote_timer == 0.2` (verified within EPSILON=1e-4).

### 3. Risk & Ambiguity Analysis

- **Risk R-19.1 (timer update order):** If the timer is updated after the eligibility check, the coyote jump window is off by one frame. The spec mandates: update timer first, then check eligibility using `prior_state.coyote_timer`. AC-19.6 and AC-19.7 provide observable numeric checks.
- **Risk R-19.2 (using result.coyote_timer in eligibility check instead of prior_state.coyote_timer):** This would give the player an extra frame of coyote time beyond what is configured. The spec is explicit that the eligibility check reads from `prior_state`.
- **Risk R-19.3 (coyote_timer == 0.0 boundary):** The eligibility condition uses strict greater-than (`> 0.0`), not greater-than-or-equal. A `coyote_timer` of exactly `0.0` means the window has expired and no jump is permitted. AC-19.7 explicitly tests this boundary.
- **Risk R-19.4 (negative coyote_time):** With `coyote_time < 0.0`, the reset rule sets `result.coyote_timer` to a negative value, and the decrement rule further decrements it. The eligibility check `> 0.0` would always fail. Behavior is undefined per the spec but must not produce NaN or Inf.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-20: Jump Cut Condition and Clamp

### 1. Spec Summary

- **Description:** Jump cut shortens the jump if the player releases the jump button while still ascending. When the jump button is not held and the character's computed upward velocity exceeds a configurable minimum, the upward velocity is clamped to that minimum. This gives the player control over jump height by releasing the button early.
- **Constraints:**
  - Jump cut applies to `result.velocity.y` after all other vertical velocity computation (impulse and gravity) is complete.
  - Jump cut condition: `jump_pressed == false` AND `result.velocity.y < self.jump_cut_velocity`.
  - Note: `jump_cut_velocity` defaults to `-200.0`. In Godot 2D screen space, negative velocity.y is upward. The condition `result.velocity.y < -200.0` means "currently moving upward faster than 200 px/s upward."
  - When the condition is true: `result.velocity.y = self.jump_cut_velocity`.
  - When the condition is false: `result.velocity.y` is unchanged by jump cut.
  - Jump cut does NOT apply when the player is falling (positive velocity.y): since `jump_cut_velocity` is negative (default -200.0) and falling velocity is positive, the condition `positive_value < -200.0` is always false.
  - Jump cut may apply on any frame where `jump_pressed == false`, including non-jump frames where the character is ascending due to a previous jump impulse.
  - Jump cut is evaluated after gravity is added to `result.velocity.y`.
  - The overall order within `simulate()` for vertical velocity is:
    1. Set `result.velocity.y = prior_state.velocity.y` (implicit in fresh state construction).
    2. If jump eligible: set `result.velocity.y = -sqrt(2.0 * gravity * jump_height)` (impulse).
    3. Add gravity: `result.velocity.y += gravity * effective_delta`.
    4. If jump cut condition: clamp `result.velocity.y = jump_cut_velocity`.
- **Assumptions:** See CHECKPOINTS.md [M1-002] — jump cut on falling velocity is intentionally a no-op per the condition being false.
- **Scope / Context:** Inside the `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, at the end of the vertical velocity computation block.

### 2. Acceptance Criteria

- **AC-20.1 (jump cut triggers):** When `jump_pressed == false` and `result.velocity.y == -469.0` (upward, faster than default -200.0): `result.velocity.y` is clamped to `self.jump_cut_velocity` (-200.0). Test setup: `prior_state.velocity.y` such that after gravity, result before cut is more negative than -200.0; `jump_pressed = false`.
- **AC-20.2 (jump cut exact formula):** With defaults: set `prior_state.velocity.y = -450.0`, `jump_pressed = false`, `jump_just_pressed = false`, `delta = 0.016`. After gravity: `result.velocity.y = -450.0 + 15.68 = -434.32`. Since `-434.32 < -200.0`: result is clamped to `-200.0`. `result.velocity.y == -200.0` (within EPSILON=1e-4).
- **AC-20.3 (jump cut does not apply when falling):** When `prior_state.velocity.y = 50.0` (falling), `jump_pressed = false`, `delta = 0.016`: after gravity `result.velocity.y = 50.0 + 15.68 = 65.68`. Since `65.68 < -200.0` is false: no clamp. `result.velocity.y == 65.68` (within EPSILON=1e-4).
- **AC-20.4 (jump cut does not apply when button held):** When `jump_pressed = true`, `prior_state.velocity.y = -450.0`, `delta = 0.016`: `result.velocity.y = -450.0 + 15.68 = -434.32`. Jump cut condition is false because `jump_pressed == true`. `result.velocity.y == -434.32` (within EPSILON=1e-4).
- **AC-20.5 (jump cut at boundary):** When `jump_pressed = false` and `result.velocity.y` (after gravity) equals exactly `self.jump_cut_velocity = -200.0`: condition is `(-200.0) < (-200.0)` which is false. No clamp. `result.velocity.y == -200.0` unchanged.
- **AC-20.6 (jump cut with custom jump_cut_velocity):** With `sim.jump_cut_velocity = -100.0`, `prior_state.velocity.y = -200.0`, `jump_pressed = false`, `delta = 0.016`: after gravity `result.velocity.y = -200.0 + 15.68 = -184.32`. Since `-184.32 < -100.0`: clamped to `-100.0`. `result.velocity.y == -100.0` (within EPSILON=1e-4).
- **AC-20.7 (jump cut with jump_cut_velocity = 0.0):** With `sim.jump_cut_velocity = 0.0`, `prior_state.velocity.y = -200.0`, `jump_pressed = false`, `delta = 0.016`: after gravity `result.velocity.y = -184.32`. Since `-184.32 < 0.0`: clamped to `0.0`. `result.velocity.y == 0.0` (within EPSILON=1e-4).
- **AC-20.8 (jump cut applied after gravity, not before):** After a jump impulse frame with gravity applied, result.velocity.y is `-469.29` approximately. Jump cut (if applicable) sees this post-gravity value, not the pre-gravity value. AC-20.2 verifies this sequencing.

### 3. Risk & Ambiguity Analysis

- **Risk R-20.1 (jump cut applied before gravity):** If the implementer applies jump cut before adding gravity, the clamped value would be `-200.0` and then gravity would bring it to `-200.0 + 15.68 = -184.32`, which is less-negative than the intended cap. The spec and AC-20.2 enforce gravity-then-cut ordering.
- **Risk R-20.2 (condition uses >= instead of >):** The spec uses strict less-than `<`. Using `<=` would also clamp when the velocity equals exactly `jump_cut_velocity`, which the spec (AC-20.5) defines as a no-op.
- **Risk R-20.3 (jump cut applied even when jump not in progress):** The condition is purely based on `jump_pressed` and `result.velocity.y`; it does not check `jump_consumed` or any other jump-state field. This means if the player holds the jump button continuously across frames and then releases it while still moving upward due to any cause, jump cut applies. This is the intended behavior — jump cut is a release-based velocity cap, not a single-jump mechanic.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-21: Double-Jump Prevention via jump_consumed

### 1. Spec Summary

- **Description:** The `jump_consumed` field on `MovementState` prevents a second jump being triggered on frames after the initial jump frame but before the player lands. Once a jump is applied, `jump_consumed` is set to `true` in the returned state. It is reset to `false` only when the player is on the floor in the prior state.
- **Constraints:**
  - When a jump impulse is applied (SPEC-18 conditions met): `result.jump_consumed = true`.
  - When no jump impulse is applied AND `prior_state.is_on_floor == true`: `result.jump_consumed = false` (reset on landing).
  - When no jump impulse is applied AND `prior_state.is_on_floor == false`: `result.jump_consumed = prior_state.jump_consumed` (carry forward unchanged).
  - The `jump_consumed` flag prevents the eligibility check from re-triggering on subsequent `jump_just_pressed` events (which are single-frame and cannot repeat within one continuous button press, but could repeat if the player releases and re-presses the button while airborne). With `jump_consumed = true`, condition 3 of SPEC-18 is false, so no second jump fires.
  - `prior_state.jump_consumed` is never mutated.
- **Assumptions:** See CHECKPOINTS.md [M1-002] — jump_consumed reset uses prior_state.is_on_floor.
- **Scope / Context:** Inside the `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-21.1 (set on jump):** When a jump impulse is applied (all SPEC-18 conditions met): `result.jump_consumed == true`.
- **AC-21.2 (prevents second jump airborne):** Frame sequence: (a) jump fires → `result.jump_consumed = true`; (b) next frame: `prior_state.jump_consumed = true`, `prior_state.is_on_floor = false`, `jump_just_pressed = true` → no jump impulse applied. `result.velocity.y == prior_state.velocity.y + gravity * delta` (gravity only). `result.jump_consumed == true` (carried forward).
- **AC-21.3 (reset on landing):** Frame sequence: (a) jump fires; (b) several airborne frames; (c) landing frame: `prior_state.is_on_floor = true` (engine has set this post-slide), `prior_state.jump_consumed = true` → `result.jump_consumed = false`. After landing, a new jump can fire on the next `jump_just_pressed` frame.
- **AC-21.4 (not reset when airborne and no jump):** When `prior_state.is_on_floor = false`, `prior_state.jump_consumed = true`, no jump conditions met: `result.jump_consumed == true` (unchanged).
- **AC-21.5 (no mutation of prior_state):** After any call to `simulate()`, `prior_state.jump_consumed` retains its original value.
- **AC-21.6 (default false allows first jump):** A freshly constructed `MovementState` has `jump_consumed = false`. The first jump on a fresh state (when on floor) fires correctly: `result.jump_consumed = true`.
- **AC-21.7 (release and re-press while airborne still blocked):** When `prior_state.is_on_floor = false`, `prior_state.jump_consumed = true`, `jump_just_pressed = true`: no jump fires. This prevents exploiting the release+re-press pattern to gain a second jump.

### 3. Risk & Ambiguity Analysis

- **Risk R-21.1 (reset on result.is_on_floor instead of prior_state.is_on_floor):** Since `result.is_on_floor` is a copy of `prior_state.is_on_floor` (AC-4.3), these are equivalent in value. However, the reset logic must read `prior_state.is_on_floor` for consistency with the rest of the function and to avoid confusion if this contract changes. The spec explicitly states `prior_state.is_on_floor`.
- **Risk R-21.2 (jump_consumed reset triggered by coyote jump):** A coyote jump is a valid jump (SPEC-18 condition 2 permits it). After a coyote jump, `result.jump_consumed = true`. This correctly prevents a second coyote jump on subsequent airborne frames.
- **Risk R-21.3 (jump_consumed not reset on floor when no jump was consumed):** If the player walks on the floor without jumping, `prior_state.jump_consumed` is `false`. The reset rule sets `result.jump_consumed = false` (no change). This is correct and harmless.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-22: project.godot — jump Input Action Registration

### 1. Spec Summary

- **Description:** The `jump` input action must be added to `/Users/jacobbrandt/workspace/blobert/project.godot` in the `[input]` section. The action is bound to the Space bar key using the same `Object(InputEventKey, ...)` object literal format already used for `move_left` and `move_right`. This makes `Input.is_action_pressed("jump")` and `Input.is_action_just_pressed("jump")` resolvable at runtime in `player_controller.gd`.
- **Constraints:**
  - Action name: `"jump"` (lowercase, no prefix).
  - Keyboard binding: Space bar. `physical_keycode = 32`. `keycode = 0`. `unicode = 32`.
  - The action entry must appear in the `[input]` section of `project.godot`, after the existing `move_right` entry.
  - The exact format must mirror the existing entries. Using the `move_left` entry as a reference, the `jump` entry contains one event (one Space bar binding). A second binding (e.g., gamepad button) is not required for Milestone 1.
  - `deadzone` must be present and set to `0.5`, consistent with the existing actions.
  - All other `Object(InputEventKey, ...)` fields must follow the same pattern as existing entries: `resource_local_to_scene:false`, `resource_name:""`, `device:-1`, `window_id:0`, all modifier flags `false`, `pressed:false`, `key_label:0`, `echo:false`, `script:null`.
  - After modification, `godot --headless --check-only` must pass (the project file must be parseable by the engine).
- **Assumptions:** No assumptions beyond those in CHECKPOINTS.md [M1-002] — physical_keycode 32 is Space bar.
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/project.godot`, `[input]` section only.

### 2. Acceptance Criteria

- **AC-22.1:** The `[input]` section of `project.godot` contains an entry with the key `jump` in the same object-literal dictionary format as `move_left` and `move_right`.
- **AC-22.2:** The `jump` entry's `events` array contains exactly one `Object(InputEventKey, ...)` literal with `physical_keycode:32`.
- **AC-22.3:** The `jump` entry's `deadzone` value is `0.5`.
- **AC-22.4:** `godot --headless --check-only` passes after this modification with no warnings or errors related to input actions.
- **AC-22.5:** At runtime in `player_controller.gd`, `Input.is_action_pressed("jump")` returns a valid bool (no "Input action not found" error).
- **AC-22.6:** The exact text block to append to the `[input]` section is:
  ```
  jump={
  "deadzone": 0.5,
  "events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"echo":false,"script":null)
  ]
  }
  ```
  The implementer must verify this format matches what the Godot 4.3 engine produces for a Space bar binding. If there is a discrepancy (e.g., different field ordering), the engine-generated format takes precedence.

### 3. Risk & Ambiguity Analysis

- **Risk R-22.1 (wrong physical_keycode):** Space bar has `physical_keycode = 32` and `keycode = 0` in Godot 4's `InputEventKey` when stored as a physical key binding. Using `keycode = 32` instead of `physical_keycode = 32` would still work on most keyboards but would break on non-US layouts. AC-22.2 specifies `physical_keycode`.
- **Risk R-22.2 (unicode value):** Space has unicode value 32. If `unicode = 0` is used (as for special keys like Left Arrow), the key will still be recognized but the unicode field would be technically incorrect. The spec provides the full literal in AC-22.6.
- **Risk R-22.3 (project.godot format sensitivity):** The `.godot` format is parsed by Godot's variant serializer. Field ordering within `Object(...)` literals must match what the engine expects. The format shown in AC-22.6 is derived from the existing `move_left`/`move_right` entries in the file, which are known to parse correctly.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-23: player_controller.gd — Jump Input Reading and Passing

### 1. Spec Summary

- **Description:** `player_controller.gd` is updated to read jump input from the engine's `Input` singleton and pass both jump booleans to the extended `simulate()` call. No movement logic is added to the controller; it remains a pure wiring layer.
- **Constraints:**
  - Two new local variables are read in `_physics_process()`, immediately after the existing `input_axis` read (Step 1):
    - `var jump_pressed: bool = Input.is_action_pressed("jump")`
    - `var jump_just_pressed: bool = Input.is_action_just_pressed("jump")`
  - Both variables are declared with explicit `bool` type annotations.
  - The `simulate()` call is updated from:
    `_simulation.simulate(_current_state, input_axis, delta)`
    to:
    `_simulation.simulate(_current_state, input_axis, jump_pressed, jump_just_pressed, delta)`
  - No other changes to `player_controller.gd` are made by this requirement.
  - `jump_pressed` and `jump_just_pressed` must be read in the same `_physics_process()` frame as `input_axis` and before `simulate()` is called. Reading them outside `_physics_process()` or after `move_and_slide()` is not permitted.
  - `_current_state` must also carry back the jump state fields. After `move_and_slide()`, the controller copies `_current_state.velocity = velocity`. After SPEC-15 adds `coyote_timer` and `jump_consumed` to `MovementState`, the controller must also copy these from `next_state` to `_current_state` so they persist across frames:
    - `_current_state.coyote_timer = next_state.coyote_timer`
    - `_current_state.jump_consumed = next_state.jump_consumed`
  - The `is_on_floor` update line (`_current_state.is_on_floor = is_on_floor()`) is unchanged and still occurs in Step 2, before `simulate()`.
  - No `@export` vars for `jump_height`, `coyote_time`, or `jump_cut_velocity` are added to `player_controller.gd`; configuration lives on the `_simulation` instance.
- **Assumptions:** No assumptions beyond those in CHECKPOINTS.md [M1-002].
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd`, `_physics_process()` function only.

### 2. Acceptance Criteria

- **AC-23.1:** `_physics_process()` contains the declarations `var jump_pressed: bool = Input.is_action_pressed("jump")` and `var jump_just_pressed: bool = Input.is_action_just_pressed("jump")`, appearing after the `input_axis` read and before the `simulate()` call.
- **AC-23.2:** The `simulate()` call in `_physics_process()` matches the new five-argument signature exactly: `_simulation.simulate(_current_state, input_axis, jump_pressed, jump_just_pressed, delta)`.
- **AC-23.3:** After `move_and_slide()`, the controller copies both new state fields back to `_current_state`:
  - `_current_state.coyote_timer = next_state.coyote_timer`
  - `_current_state.jump_consumed = next_state.jump_consumed`
- **AC-23.4:** `godot --headless --check-only` passes after these changes.
- **AC-23.5:** The controller contains no movement math, no jump impulse formulas, and no direct manipulation of `velocity.y` other than `velocity = next_state.velocity` and `_current_state.velocity = velocity` (the existing lines).
- **AC-23.6:** In-editor play (verified manually): pressing Space causes the character to jump; releasing Space mid-jump causes an earlier apex (jump cut); walking off a ledge and pressing Space within 0.1s still produces a jump (coyote time).

### 3. Risk & Ambiguity Analysis

- **Risk R-23.1 (jump state fields not copied back to _current_state):** If `coyote_timer` and `jump_consumed` are not copied from `next_state` to `_current_state` after each frame, every call to `simulate()` will receive a `_current_state` with stale (default) values for these fields. `coyote_timer` would always be 0.0, making coyote time never work. `jump_consumed` would always be false, making double-jump prevention never work. AC-23.3 explicitly requires these copy-back lines.
- **Risk R-23.2 (Input.is_action_just_pressed called after move_and_slide):** `is_action_just_pressed` is only true on the first frame the action is pressed. If it is read after `move_and_slide()` (which can take non-trivial time), the result would still be correct since both reads happen within the same `_physics_process()` call frame. However, the spec requires reading both before `simulate()` to match the execution order of the four-step pipeline.
- **Risk R-23.3 (jump_pressed and jump_just_pressed order reversed in simulate() call):** If the controller passes them in the wrong order (`jump_just_pressed, jump_pressed` instead of `jump_pressed, jump_just_pressed`), jumps would fire on every frame the button is held (using the held signal as the trigger). AC-23.2 specifies the exact argument order.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-24: Frame-Rate Independence of New Timer Logic

### 1. Spec Summary

- **Description:** All new timer-based logic in `simulate()` (specifically `coyote_timer` decrement) must be frame-rate independent: the behavior must be consistent regardless of physics tick rate. The jump impulse formula is frame-rate independent by nature (it produces the same velocity regardless of delta). Jump cut is also frame-rate independent (it is a threshold clamp, not a time-based operation). This requirement focuses on verifying that `coyote_timer` decrement behaves correctly at different delta values.
- **Constraints:**
  - `coyote_timer` decrement uses `effective_delta` (same delta-scaled value used for all other time-based calculations).
  - Two half-steps (`delta = coyote_time / 2` each) must produce the same `coyote_timer` result as one full step (`delta = coyote_time`) within EPSILON=1e-4, when starting from `coyote_timer = coyote_time` and airborne for both.
  - Specifically: `max(0.0, coyote_time - delta/2 - delta/2) == max(0.0, coyote_time - delta)`.
  - The jump impulse `velocity.y = -sqrt(2.0 * gravity * jump_height)` is inherently frame-rate independent because it is an instantaneous assignment, not a time-scaled accumulation. No frame-rate independence test is required for the impulse itself.
  - The `jump_consumed` flag transitions (`false → true` on jump, `true → false` on floor) are event-based, not time-based. They are inherently frame-rate independent.
- **Assumptions:** No assumptions beyond those in CHECKPOINTS.md [M1-002].
- **Scope / Context:** Tests in `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd`.

### 2. Acceptance Criteria

- **AC-24.1 (coyote_timer two half-steps):** Starting from `prior_state.coyote_timer = 0.1` (= `coyote_time`), airborne, no jump input:
  - Half-step path: `sim.simulate(state, 0.0, false, false, 0.05)` then `sim.simulate(result, 0.0, false, false, 0.05)`. Final `coyote_timer = 0.0`.
  - Full-step path: `sim.simulate(state, 0.0, false, false, 0.1)`. Final `coyote_timer = 0.0`.
  - Both produce `coyote_timer == 0.0` (clamped at zero after subtracting the full window).
- **AC-24.2 (coyote_timer partial decrement half-steps):** Starting from `prior_state.coyote_timer = 0.1`, airborne, `delta = 0.016`:
  - One step: `result.coyote_timer = max(0.0, 0.1 - 0.016) = 0.084`.
  - Two half-steps of `delta = 0.008` each: step 1 → `max(0.0, 0.1 - 0.008) = 0.092`; step 2 → `max(0.0, 0.092 - 0.008) = 0.084`. Both equal 0.084 (within EPSILON=1e-4). This holds because subtraction is linear.
- **AC-24.3 (jump impulse is frame-rate independent):** The impulse `result.velocity.y` immediately after the impulse formula (before gravity is added in the test) equals `-sqrt(2.0 * gravity * jump_height)` regardless of delta. Two calls with different deltas produce the same impulse (gravity contribution differs, but the impulse itself is constant).
- **AC-24.4 (existing SPEC-12 frame-rate independence tests still pass):** All frame-rate independence tests from M1-001 (`test_spec12_*` in `test_movement_simulation.gd`) continue to pass after the signature migration (passing `false, false` for the new parameters).

### 3. Risk & Ambiguity Analysis

- **Risk R-24.1 (coyote_timer not using effective_delta):** If the raw `delta` parameter (before the `max(0.0, delta)` clamp) is used for coyote timer decrement but `effective_delta` is used for gravity and horizontal calculations, negative delta would produce different behavior in the timer versus other calculations. The spec requires `effective_delta` throughout.
- **Risk R-24.2 (non-linear timer behavior):** Since `max(0.0, x - delta)` is a linear subtraction followed by a clamp, two half-steps always equal one full step as long as neither step crosses zero. AC-24.2 uses values that do not cross zero, ensuring the assertion is meaningful.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Requirement SPEC-25: Backward Compatibility — M1-001 Test Migration

### 1. Spec Summary

- **Description:** The signature change in SPEC-17 is a breaking change. All existing call sites with the three-argument form `simulate(state, axis, delta)` must be migrated to the five-argument form `simulate(state, axis, false, false, delta)`. Passing `false, false` for both jump parameters produces identical behavior to the old three-argument call: no jump fires, no coyote timer changes beyond its update rule, no jump cut applies. All 111 M1-001 tests must continue to pass after migration.
- **Constraints:**
  - Files requiring call-site migration:
    1. `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` — one call site in `_physics_process()`. This site is updated by SPEC-23 to the full jump-aware form (not to `false, false`). Migration here means the SPEC-23 update covers it.
    2. `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd` — all calls in test methods and in `run_all()` body (none directly, but all are in test function bodies). Grep for `sim.simulate(` to find all sites. Each three-argument call becomes five-argument with `false, false` inserted as 3rd and 4th arguments.
    3. `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd` — same pattern.
  - No test assertions in the existing files need to change. Only the `simulate()` call arguments change.
  - `_make_state_with(vx, vy, on_floor)` helper in `test_movement_simulation.gd` constructs a `MovementState` and sets three fields. After SPEC-15, the new fields default to `0.0` and `false`, which is the correct baseline for all existing horizontal/gravity tests. No change to the helper is required.
  - After migration, running `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` must exit with code 0 and all 111 pre-existing tests must pass.
  - The total test count after adding the new jump test suites (Tasks 7 and 8) will exceed 111. The 111 count refers specifically to the tests already passing at M1-001 completion.
- **Assumptions:** See CHECKPOINTS.md [M1-002] — Spec — existing test suite call sites.
- **Scope / Context:** `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd` and `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd` (call-site updates only); `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` (full update covered by SPEC-23).

### 2. Acceptance Criteria

- **AC-25.1:** Every call to `sim.simulate()` or `_simulation.simulate()` in `test_movement_simulation.gd` uses the five-argument form. No three-argument call remains. Verified by grep: `grep -n "simulate(" tests/test_movement_simulation.gd` shows no call with only three arguments between parentheses.
- **AC-25.2:** Every call to `sim.simulate()` in `test_movement_simulation_adversarial.gd` uses the five-argument form. Verified by the same grep pattern.
- **AC-25.3:** The updated test files parse without error under `godot --headless --check-only`.
- **AC-25.4:** Running `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` after migration exits with code 0. All existing test results are PASS.
- **AC-25.5:** No existing test assertion values change. Only the `simulate()` call argument list changes. Any test that was asserting `result.velocity.x == 12.8` continues to assert the same value.
- **AC-25.6:** The `_make_state_with(vx, vy, on_floor)` helper function in `test_movement_simulation.gd` is not modified. The new fields `coyote_timer` and `jump_consumed` are left at their defaults (0.0 and false) for all existing tests, which is the correct behavior for non-jump test scenarios.
- **AC-25.7 (smoke test — spec13 headless smoke):** The existing `test_spec13_headless_smoke()` test, which calls `sim.simulate(state, 1.0, delta)`, is migrated to `sim.simulate(state, 1.0, false, false, 0.016)`. After migration the test must still pass: `result != null` and `result.velocity.x > 0.0`.

### 3. Risk & Ambiguity Analysis

- **Risk R-25.1 (missed call site):** If a call site is missed, `godot --headless --check-only` will report a type mismatch or argument count error. The implementer must grep all GDScript files for `simulate(` to find every occurrence. Known files are listed above; if additional scripts call `simulate()` (e.g., a future tool or debug script), they also need migration.
- **Risk R-25.2 (wrong argument position):** Inserting `false, false` at positions 4 and 5 (after delta) instead of positions 3 and 4 (before delta) would cause a type error because `delta: float` would receive `false` (bool). The spec is explicit: the five-argument form is `(state, axis, jump_pressed, jump_just_pressed, delta)`.
- **Risk R-25.3 (test assertions on new fields):** Existing test assertions do not reference `coyote_timer` or `jump_consumed`. After migration, the returned `result` objects will have these fields set by the new logic (e.g., `result.coyote_timer = coyote_time` when on floor). Existing assertions only check `result.velocity` and `result.is_on_floor`, so there is no risk of false positives from the new fields.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-002].

---

## Summary: Spec Coverage Map

| SPEC ID  | Requirement                              | Affected File(s)                                      | Task(s) |
|----------|------------------------------------------|-------------------------------------------------------|---------|
| SPEC-15  | MovementState new fields                 | scripts/movement_simulation.gd                        | 3       |
| SPEC-16  | MovementSimulation new config params     | scripts/movement_simulation.gd                        | 4       |
| SPEC-17  | simulate() new signature (5 params)      | scripts/movement_simulation.gd + all call sites       | 5       |
| SPEC-18  | Jump impulse condition and formula       | scripts/movement_simulation.gd                        | 5       |
| SPEC-19  | Coyote time logic                        | scripts/movement_simulation.gd                        | 5       |
| SPEC-20  | Jump cut condition and clamp             | scripts/movement_simulation.gd                        | 5       |
| SPEC-21  | Double-jump prevention (jump_consumed)   | scripts/movement_simulation.gd                        | 5       |
| SPEC-22  | project.godot jump action registration   | project.godot                                         | 1       |
| SPEC-23  | player_controller.gd jump input wiring   | scripts/player_controller.gd                          | 6       |
| SPEC-24  | Frame-rate independence of timer logic   | tests/test_jump_simulation.gd                         | 7       |
| SPEC-25  | M1-001 test backward compatibility       | tests/test_movement_simulation.gd + adversarial + .gd | 5, 7    |

## Order of Operations Within simulate() (Normative)

The following execution order is normative for the `simulate()` body. Implementations that produce the correct observable outputs through an equivalent internal ordering are acceptable, but this order is the reference for all acceptance criteria:

1. Sanitize `effective_delta = max(0.0, delta)`.
2. Sanitize `input_axis` (NaN → 0.0, Inf → clamp to ±1.0).
3. Allocate `result: MovementState = MovementState.new()`.
4. **Coyote timer update** (SPEC-19):
   - If `prior_state.is_on_floor`: `result.coyote_timer = coyote_time`.
   - Else: `result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)`.
5. **Jump consumed carry-forward / reset** (SPEC-21, landing reset):
   - If `prior_state.is_on_floor`: `result.jump_consumed = false`.
   - Else: `result.jump_consumed = prior_state.jump_consumed`.
   (Note: this is overwritten in step 6 if a jump fires.)
6. **Jump eligibility and impulse** (SPEC-18):
   - If `jump_just_pressed AND (prior_state.is_on_floor OR prior_state.coyote_timer > 0.0) AND NOT prior_state.jump_consumed`:
     - `result.velocity.y = -sqrt(2.0 * gravity * jump_height)`.
     - `result.jump_consumed = true`.
   - Else: `result.velocity.y = prior_state.velocity.y`.
7. **Horizontal velocity** (SPEC-5, unchanged from M1-001).
8. **Gravity** (SPEC-6): `result.velocity.y += gravity * effective_delta`.
9. **Jump cut** (SPEC-20):
   - If `NOT jump_pressed AND result.velocity.y < jump_cut_velocity`: `result.velocity.y = jump_cut_velocity`.
10. **is_on_floor pass-through** (AC-4.3): `result.is_on_floor = prior_state.is_on_floor`.
11. Return `result`.
