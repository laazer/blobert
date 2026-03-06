# Wall Cling Simulation Specification
# M1-003 — wall_cling.md
# SPEC-25 through SPEC-36
#
# Prerequisite specs: SPEC-1 through SPEC-24
#   SPEC-1  through SPEC-14: movement_controller.md / M1-001
#   SPEC-15 through SPEC-24: jump_tuning.md / M1-002
# Continuing numbering from SPEC-24.
#
# Files affected:
#   /Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd (modified)
#   /Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd (modified)
#   /Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation_adversarial.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd (updated)
#   /Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd (call-site migration only)

---

## Requirement SPEC-25: MovementState New Fields

### 1. Spec Summary

- **Description:** The `MovementState` inner class inside `movement_simulation.gd` gains two new typed fields: `is_wall_clinging: bool` and `cling_timer: float`. These fields carry wall-cling state across frames under the same immutable-input / fresh-output contract already established for all prior `MovementState` fields. `simulate()` reads them from `prior_state` and writes computed values into the new `MovementState` it returns.
- **Constraints:**
  - Both fields must be declared inside the `class MovementState:` block in `movement_simulation.gd`, after the existing four fields (`velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`).
  - `is_wall_clinging` type is `bool`. Default value is `false`.
  - `cling_timer` type is `float`. Default value is `0.0`.
  - No other fields or methods are added to `MovementState` in this milestone.
  - `simulate()` must never mutate `prior_state.is_wall_clinging` or `prior_state.cling_timer`. Both fields in `prior_state` must remain unchanged after `simulate()` returns (consistent with the existing immutability contract from AC-4.2 and AC-15.5).
  - GDScript must be statically typed throughout; no untyped variable declarations.
  - Exact declaration lines (one per field, no other syntax):
    - `var is_wall_clinging: bool = false`
    - `var cling_timer: float = 0.0`
- **Assumptions:** The existing `_make_state_with` test helper constructs a `MovementState` and sets fields directly. After SPEC-25, `is_wall_clinging` and `cling_timer` on that constructed state will hold their declared defaults (`false` and `0.0` respectively) unless the test explicitly sets them. This is the correct default behavior and requires no change to the existing helper signature.
- **Scope / Context:** Applies exclusively to the `class MovementState:` block inside `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`. No other file is modified by this requirement alone.

### 2. Acceptance Criteria

- **AC-25.1:** `MovementState.new()` produces an object where `is_wall_clinging == false` and `cling_timer == 0.0`, verifiable by direct field access immediately after construction with no intervening calls.
- **AC-25.2:** `is_wall_clinging` is declared with the GDScript type annotation `bool` and the initializer `= false`. The exact declaration line is `var is_wall_clinging: bool = false`.
- **AC-25.3:** `cling_timer` is declared with the GDScript type annotation `float` and the initializer `= 0.0`. The exact declaration line is `var cling_timer: float = 0.0`.
- **AC-25.4:** Both new fields appear in the `class MovementState:` block only, not at the outer `MovementSimulation` class scope.
- **AC-25.5:** After calling `simulate(prior_state, 0.0, false, false, false, 0.0, delta)` with any valid inputs, `prior_state.is_wall_clinging` retains its original value and `prior_state.cling_timer` retains its original value (no mutation of prior state).
- **AC-25.6:** `godot --headless --check-only` passes with no parse errors after adding these fields.
- **AC-25.7:** The total field count of `MovementState` after this change is exactly six: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`. No additional fields exist.

### 3. Risk & Ambiguity Analysis

- **Risk R-25.1 (additive change breaks existing tests):** Adding fields with correct defaults does not change the output of existing `simulate()` calls for horizontal, gravity, or jump behavior when `is_on_wall=false` and `wall_normal_x=0.0` are passed. However, if an implementer accidentally removes an existing field default or reorders field declarations, existing tests can fail silently. AC-25.7 guards against this by explicitly verifying the total field count.
- **Risk R-25.2 (wrong placement):** Fields declared at the outer `MovementSimulation` scope instead of inside `class MovementState:` would still parse but would be inaccessible via `MovementState.new().is_wall_clinging`. AC-25.4 guards against this.
- **Risk R-25.3 (type annotation omitted):** GDScript permits untyped `var is_wall_clinging = false`. The spec requires typed declarations per the established codebase convention (SPEC-14). Missing annotations are a static analysis failure in strict mode; tests should verify field access returns the correct type by asserting the typeof() or using typed access patterns.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-26: New Configuration Parameters

### 1. Spec Summary

- **Description:** The `MovementSimulation` class (outer class in `movement_simulation.gd`) gains four new `var` declarations representing wall-cling and wall-jump configuration: `cling_gravity_scale`, `max_cling_time`, `wall_jump_height`, and `wall_jump_horizontal_speed`. These follow the same convention as existing parameters: plain `var` with a `float` type annotation and an explicit default value. No `@export` annotation is used on `MovementSimulation` fields (it extends `RefCounted`, not `Node`). Inspector-facing `@export` declarations are applied on `PlayerController` (a Node), which mirrors these values to the simulation instance.
- **Constraints:**
  - `cling_gravity_scale: float = 0.1` — multiplier applied to `gravity` while the player is wall-clinging. A value of `1.0` produces normal gravity (no cling effect). A value of `0.0` produces zero gravity while clinging (full hover). Values between `0.0` and `1.0` produce a slow downward slide. Negative values are undefined behavior.
  - `max_cling_time: float = 1.5` — maximum continuous wall-cling duration in seconds. When `prior_state.cling_timer >= max_cling_time`, cling eligibility is blocked and the player falls at normal gravity. A value of `0.0` disables wall cling entirely (see Risk R-26.3).
  - `wall_jump_height: float = 100.0` — target apex height in pixels for the wall jump vertical component. Uses the same kinematic formula as regular jump: `impulse_y = -sqrt(2.0 * gravity * wall_jump_height)`. A value of `0.0` produces a zero vertical impulse. Negative values are undefined behavior.
  - `wall_jump_horizontal_speed: float = 180.0` — horizontal impulse magnitude in pixels per second applied during a wall jump. Direction is determined by `wall_normal_x` (see SPEC-33). A value of `0.0` produces a purely vertical wall jump. Negative values are undefined behavior.
  - All four are declared at the outer `MovementSimulation` class scope, not inside `MovementState`.
  - Parameter names must exactly match the identifiers `cling_gravity_scale`, `max_cling_time`, `wall_jump_height`, `wall_jump_horizontal_speed`. These names are referenced directly by `simulate()` (SPEC-31, SPEC-33), by test files, and by `player_controller.gd`. Any name mismatch causes parse errors.
  - All four declarations appear after the existing eight configuration parameters and before `simulate()`, with doc-comment annotations consistent with the existing style.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** Applies to the outer `MovementSimulation` class body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-26.1:** `MovementSimulation.new().cling_gravity_scale` equals `0.1` (tolerance EPSILON=1e-4).
- **AC-26.2:** `MovementSimulation.new().max_cling_time` equals `1.5` (tolerance EPSILON=1e-4).
- **AC-26.3:** `MovementSimulation.new().wall_jump_height` equals `100.0` (tolerance EPSILON=1e-4).
- **AC-26.4:** `MovementSimulation.new().wall_jump_horizontal_speed` equals `180.0` (tolerance EPSILON=1e-4).
- **AC-26.5:** Each parameter is declared with an explicit `float` type annotation. The exact declarations are:
  - `var cling_gravity_scale: float = 0.1`
  - `var max_cling_time: float = 1.5`
  - `var wall_jump_height: float = 100.0`
  - `var wall_jump_horizontal_speed: float = 180.0`
- **AC-26.6:** All four parameters are mutable at runtime: a test can assign `sim.cling_gravity_scale = 0.5` and then call `simulate()` with a clinging state and observe a different gravity contribution in the result.
- **AC-26.7:** `godot --headless --check-only` passes after adding these four declarations.
- **AC-26.8:** The total count of configuration `var` fields on `MovementSimulation` after this change is exactly twelve: `max_speed`, `acceleration`, `friction`, `air_deceleration`, `gravity`, `jump_height`, `coyote_time`, `jump_cut_velocity`, `cling_gravity_scale`, `max_cling_time`, `wall_jump_height`, `wall_jump_horizontal_speed`.

### 3. Risk & Ambiguity Analysis

- **Risk R-26.1 (cling_gravity_scale=0.0 behavior):** Setting `cling_gravity_scale=0.0` causes `gravity * 0.0 * effective_delta = 0.0` gravity contribution while clinging. The player effectively hovers on the wall with no downward slide. This is defined behavior (documented explicitly) — the player must still exit via pressing away, releasing input, or a wall jump. It is not a bug; the parameter is simply tuned to zero. Test files must include this case.
- **Risk R-26.2 (max_cling_time=0.0 disables cling entirely):** When `max_cling_time = 0.0`, the cling eligibility condition includes `prior_state.cling_timer < max_cling_time`, which evaluates to `0.0 < 0.0 = false` on the very first frame of contact. Wall cling is effectively disabled. This is defined behavior. See SPEC-29 AC-29.5 for the exact test.
- **Risk R-26.3 (wall_jump_height negative):** Negative `wall_jump_height` is undefined behavior per this spec. The implementation must guard against `sqrt(negative)` producing NaN using the same pattern as the existing jump impulse guard: `wall_jump_height if wall_jump_height > 0.0 else 0.0`. Test files must assert only finiteness for negative values.
- **Risk R-26.4 (wall_jump_horizontal_speed sign confusion):** `wall_jump_horizontal_speed` is always positive in the default configuration. The direction of horizontal travel during a wall jump is determined by multiplying this value by `wall_normal_x` (SPEC-33), not by a sign on this parameter itself. An implementer who uses a negative default here will reverse the wall jump direction. AC-26.4 specifies the literal positive value `180.0`.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-27: simulate() Extended Signature

### 1. Spec Summary

- **Description:** The `simulate()` function signature is changed from the M1-002 five-parameter form to a new seven-parameter form. Two new parameters, `is_on_wall: bool` and `wall_normal_x: float`, are inserted between `jump_just_pressed` and `delta`. This is a breaking change to all existing call sites. The function remains pure: no engine singletons, no Node references, no I/O. Fully testable headlessly.
- **Constraints:**
  - New signature (exact): `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, delta: float) -> MovementState:`
  - Parameter names must exactly match: `prior_state`, `input_axis`, `jump_pressed`, `jump_just_pressed`, `is_on_wall`, `wall_normal_x`, `delta`.
  - All parameters must carry explicit GDScript type annotations as shown.
  - Return type annotation `-> MovementState` is retained.
  - `is_on_wall: bool` — true when the character's collision body is in contact with a wall on the current physics frame, as reported by the engine's `CharacterBody2D.is_on_wall()`. In the controller, this value is read after `move_and_slide()`. In tests, it is passed directly as a literal.
  - `wall_normal_x: float` — the X component of the wall's outward-facing surface normal, as reported by `CharacterBody2D.get_wall_normal().x`. The wall normal points away from the wall surface (into open space). Convention: a wall to the right of the character has a normal pointing left (negative X); a wall to the left has a normal pointing right (positive X). When `is_on_wall == false`, `wall_normal_x` must be passed as `0.0`. The simulation does not validate this; behavior when `is_on_wall == false` and `wall_normal_x != 0.0` is not guaranteed.
  - `delta: float` remains the last parameter. Its position does not change relative to `prior_state`.
  - Migration requirement: every existing call site that calls `simulate()` with five arguments must be updated to pass `false, 0.0` for `is_on_wall` and `wall_normal_x` (in that order, before `delta`). The affected files and replacement pattern are:
    - `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` — updated per the player controller spec (Task 5 of the execution plan). Old call: `_simulation.simulate(_current_state, axis, jump_pressed, jump_just_pressed, delta)`. New call: `_simulation.simulate(_current_state, axis, jump_pressed, jump_just_pressed, is_on_wall(), get_wall_normal().x if is_on_wall() else 0.0, delta)`.
    - `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd` — every `sim.simulate(state, axis, false, false, delta)` becomes `sim.simulate(state, axis, false, false, false, 0.0, delta)`.
    - `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd` — same pattern.
    - `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd` — same pattern.
    - `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd` — same pattern.
  - The function body retains all existing sanitization logic: `effective_delta = max(0.0, delta)`, NaN/Inf clamping on `input_axis`. New parameters `is_on_wall` and `wall_normal_x` are not sanitized. `wall_normal_x` with NaN or Inf is undefined behavior; test files cover this in the adversarial suite.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** The `func simulate(...)` declaration and body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, plus all call sites listed above.

### 2. Acceptance Criteria

- **AC-27.1:** The exact function declaration line is `func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, delta: float) -> MovementState:`.
- **AC-27.2:** Calling `simulate(state, 0.0, false, false, false, 0.0, 0.016)` (all new parameters at safe defaults) produces results identical to the prior five-argument behavior: horizontal and gravity formulas operate as before, no jump impulse, no wall cling, no coyote timer change beyond the timer update rule, no jump cut. This verifies backward compatibility.
- **AC-27.3:** `godot --headless --check-only` passes on the entire project after the signature change and all call-site migrations in all five affected files.
- **AC-27.4:** The existing tests in `test_movement_simulation.gd`, `test_movement_simulation_adversarial.gd`, `test_jump_simulation.gd`, and `test_jump_simulation_adversarial.gd` all pass after call-site migration with `false, 0.0` inserted as the fifth and sixth arguments before `delta`, confirming no regression in horizontal, gravity, or jump behavior.
- **AC-27.5:** The function body retains all existing sanitization: `effective_delta = max(0.0, delta)`, NaN detection on `input_axis`, Inf clamping on `input_axis`.
- **AC-27.6:** `is_on_wall` and `wall_normal_x` are not sanitized within `simulate()`. They are passed through to the wall cling logic as-is.

### 3. Risk & Ambiguity Analysis

- **Risk R-27.1 (call-site migration missed):** If any call site is not updated, `godot --headless --check-only` will report a parse or type error. The five files listed are the only known call sites. If additional scripts reference `simulate()`, they must also be updated. The Test Designer Agent is responsible for migrating all four test files; the Generalist Agent (Task 5) is responsible for migrating `player_controller.gd`.
- **Risk R-27.2 (parameter order confusion):** The new parameters are inserted between `jump_just_pressed` and `delta` — not appended at the end. An implementer who appends them after `delta` will create a different signature that does not match the spec. AC-27.1 specifies the exact order.
- **Risk R-27.3 (wall_normal_x when not on wall):** Godot's `get_wall_normal()` returns `Vector2.ZERO` when `is_on_wall()` is false. If the controller passes `get_wall_normal().x` without guarding, it passes `0.0` (which is safe — see SPEC-28). The spec requires the controller to explicitly guard with `is_on_wall() else 0.0` for clarity and correctness.
- **Risk R-27.4 (test migration with jump_pressed=true):** Some existing tests in `test_jump_simulation.gd` and `test_jump_simulation_adversarial.gd` pass `jump_pressed=true` to suppress jump cut. These calls gain `false, 0.0` as the new fifth and sixth arguments. The migration must preserve the existing `jump_pressed` and `jump_just_pressed` values unchanged; only the two new parameters are added.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-28: Pressing-Toward-Wall Detection Formula

### 1. Spec Summary

- **Description:** The simulation must compute, on each frame, whether the player's directional input is oriented toward the wall. This determination is a prerequisite for cling eligibility (SPEC-29) and must be computed from `input_axis` and `wall_normal_x` using pure arithmetic with no engine dependency.
- **Constraints:**
  - Formula: `var pressing_toward_wall: bool = (input_axis * wall_normal_x) < 0.0`
  - `input_axis` used in this formula is the sanitized value (`safe_axis`) produced in simulation step 2, not the raw parameter.
  - `wall_normal_x` is used as-is (no sanitization).
  - Sign convention for `wall_normal_x`: Godot 4's `CharacterBody2D.get_wall_normal()` returns a vector pointing away from the wall surface (outward). For a wall to the right of the character, the normal points left: `wall_normal_x < 0`. For a wall to the left, the normal points right: `wall_normal_x > 0`.
  - Derivation of the formula: if the wall is to the right (`wall_normal_x < 0`) and the player presses right (`input_axis > 0`), then `input_axis * wall_normal_x = positive * negative = negative < 0.0` — the player is pressing toward the wall (true). If the player presses left (`input_axis < 0`) away from the wall, `negative * negative = positive > 0.0` — not toward the wall (false). If `input_axis == 0.0`, the product is `0.0`, which is not less than `0.0`, so no directional input is treated as "not pressing toward" (exits cling).
  - When `wall_normal_x == 0.0` (passed when `is_on_wall == false`): `input_axis * 0.0 = 0.0 < 0.0` is always false, so cling is always blocked. This is the safe default behavior.
  - The exact local variable name used in the implementation must be `pressing_toward_wall` (referenced by SPEC-29 eligibility condition).
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** Inside the `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`, specifically in the new wall cling step (step 5.5, between existing steps 5 and 6 per the normative order of operations).

### 2. Acceptance Criteria

- **AC-28.1:** When `input_axis = 1.0` (right) and `wall_normal_x = -1.0` (wall to the right, normal pointing left): `pressing_toward_wall` is `true`. Product: `1.0 * -1.0 = -1.0 < 0.0`.
- **AC-28.2:** When `input_axis = -1.0` (left) and `wall_normal_x = 1.0` (wall to the left, normal pointing right): `pressing_toward_wall` is `true`. Product: `-1.0 * 1.0 = -1.0 < 0.0`.
- **AC-28.3:** When `input_axis = -1.0` (pressing left/away) and `wall_normal_x = -1.0` (wall to the right): `pressing_toward_wall` is `false`. Product: `-1.0 * -1.0 = 1.0 > 0.0`.
- **AC-28.4:** When `input_axis = 0.0` (no input) and `wall_normal_x = -1.0`: `pressing_toward_wall` is `false`. Product: `0.0 * -1.0 = 0.0`, which is not `< 0.0`.
- **AC-28.5:** When `wall_normal_x = 0.0` (not on wall default): `pressing_toward_wall` is always `false` regardless of `input_axis` value, because any finite value multiplied by `0.0` is `0.0`, and `0.0 < 0.0` is false.
- **AC-28.6:** When `input_axis * wall_normal_x == 0.0` exactly (the strict boundary): `pressing_toward_wall` is `false`. The formula uses strict `< 0.0`, not `<= 0.0`.
- **AC-28.7:** The sanitized `safe_axis` value (not the raw `input_axis` parameter) is used in the product. This means `input_axis = NaN` is treated as `safe_axis = 0.0`, producing `pressing_toward_wall = false`.

### 3. Risk & Ambiguity Analysis

- **Risk R-28.1 (using raw input_axis instead of safe_axis):** If the implementation uses the raw `input_axis` parameter instead of the sanitized `safe_axis`, NaN input would produce NaN in the product, and `NaN < 0.0` is `false` in IEEE-754 — which happens to produce the correct behavior (false). However, the spec requires `safe_axis` for consistency and correctness. AC-28.7 explicitly addresses this.
- **Risk R-28.2 (sign convention misunderstood):** An implementer unfamiliar with Godot's wall normal convention might assume the normal points toward the wall (inward), which would reverse all cling logic. The spec provides four concrete examples (AC-28.1 through AC-28.4) with explicit product values to eliminate ambiguity.
- **Risk R-28.3 (boundary at exactly zero):** The strict `< 0.0` (not `<= 0.0`) means that when `input_axis * wall_normal_x` is exactly zero — from zero input axis, zero wall normal, or one value being zero — `pressing_toward_wall` is false. This is the deliberate design choice documented in AC-28.6 and Risk R4 of the execution plan.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-29: Cling Eligibility Condition

### 1. Spec Summary

- **Description:** On each frame, `simulate()` evaluates whether the player is eligible for wall cling. Eligibility is a boolean computed from five conditions that must all be true simultaneously. This boolean drives the state update in SPEC-30 and the gravity modification in SPEC-31.
- **Constraints:**
  - Full eligibility condition (all five must be true simultaneously):
    1. `is_on_wall == true` (the character's body is touching a wall this frame).
    2. `NOT prior_state.is_on_floor` (the character is not on the floor; being grounded takes precedence and disables cling).
    3. `pressing_toward_wall == true` (SPEC-28 formula; player is actively pressing toward the wall).
    4. `NOT prior_state.jump_consumed` (the jump-consumed flag is clear; a player who has already consumed their jump cannot begin clinging on that airborne phase).
    5. `prior_state.cling_timer < max_cling_time` (the cling duration has not yet expired; prevents permanent clinging).
  - All five conditions use `prior_state` fields, not `result` fields, consistent with the existing pattern where eligibility reads the incoming state before this frame's updates are written.
  - The exact local variable name for the boolean result is `eligible_for_cling`.
  - The condition is evaluated after the `pressing_toward_wall` variable is computed (step 5.5 per normative order of operations) and before the jump eligibility check (step 6).
  - If any condition is false, `eligible_for_cling = false`.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** Inside the `simulate()` function body, in the wall cling state update block between existing steps 5 and 6.

### 2. Acceptance Criteria

- **AC-29.1:** When all five conditions are true (`is_on_wall=true`, `prior.is_on_floor=false`, `pressing_toward_wall=true`, `prior.jump_consumed=false`, `prior.cling_timer=0.0` with `max_cling_time=1.5`): `eligible_for_cling = true` and `result.is_wall_clinging = true`.
- **AC-29.2:** When `is_on_wall=false` (all other conditions true): `eligible_for_cling = false` and `result.is_wall_clinging = false`. The character is not on a wall.
- **AC-29.3:** When `prior_state.is_on_floor=true` (all other conditions true, meaning player is both on floor and on wall — a corner): `eligible_for_cling = false` and `result.is_wall_clinging = false`. Ground contact takes precedence.
- **AC-29.4:** When `pressing_toward_wall=false` (all other conditions true, player releases or presses away): `eligible_for_cling = false` and `result.is_wall_clinging = false`. The cling exits.
- **AC-29.5:** When `prior_state.jump_consumed=true` (all other conditions true): `eligible_for_cling = false` and `result.is_wall_clinging = false`. A player who consumed their jump cannot begin a new cling.
- **AC-29.6:** When `prior_state.cling_timer >= max_cling_time` (all other conditions true, timer expired): `eligible_for_cling = false` and `result.is_wall_clinging = false`. The cling duration cap has been reached.
- **AC-29.7:** When `max_cling_time = 0.0` and `prior_state.cling_timer = 0.0` (all other conditions true): `eligible_for_cling = false` and `result.is_wall_clinging = false`. The strict `<` ensures `0.0 < 0.0` is false, effectively disabling wall cling when `max_cling_time = 0.0`.
- **AC-29.8:** When `prior_state.cling_timer` is exactly one `effective_delta` less than `max_cling_time` (the last eligible frame, e.g. `cling_timer = 1.5 - 0.016 = 1.484` with `max_cling_time = 1.5`): `eligible_for_cling = true` and `result.is_wall_clinging = true`. The timer has not yet exceeded the cap.

### 3. Risk & Ambiguity Analysis

- **Risk R-29.1 (condition 4 blocks normal wall cling after a regular jump):** A player who jumps from the floor (consuming `jump_consumed`) and lands against a wall mid-air cannot enter wall cling because `prior_state.jump_consumed=true`. This is an intentional design decision (logged in CHECKPOINTS.md [M1-003] "Wall jump vs. regular jump interaction"). Players must land on a floor to reset `jump_consumed` before they can wall-cling again. If this behavior is undesirable, it requires a dedicated `wall_jump_consumed` flag in a future milestone.
- **Risk R-29.2 (strict vs. inclusive timer comparison):** Using `<` (strict less-than) for condition 5 means the timer must be strictly less than `max_cling_time`. When `cling_timer == max_cling_time` exactly, cling is not eligible. This avoids off-by-one ambiguity at the boundary and is consistent with how Godot's `coyote_timer > 0.0` uses a strict comparison.
- **Risk R-29.3 (ordering with jump eligibility):** Cling eligibility is evaluated before jump eligibility. The `eligible_for_cling` result is needed by SPEC-31 (cling gravity) which must be decided before the gravity step. The jump eligibility check (step 6) reads from `prior_state` fields and does not depend on `eligible_for_cling` except in the wall jump path (SPEC-32), which reads `prior_state.is_wall_clinging` — the value from the prior frame, not the current `eligible_for_cling`. See SPEC-34 for the normative order.
- **Risk R-29.4 (is_on_floor AND is_on_wall simultaneously):** In Godot 4, a CharacterBody2D at a convex corner can briefly report both `is_on_floor()` and `is_on_wall()` as true in the same physics frame. Condition 2 (`NOT prior_state.is_on_floor`) handles this case correctly by giving ground contact priority over wall contact.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-30: Cling State Update

### 1. Spec Summary

- **Description:** After computing `eligible_for_cling` (SPEC-29), `simulate()` writes the new wall cling state into `result.is_wall_clinging` and `result.cling_timer`. These fields form the per-frame output of the cling state machine and are read as `prior_state.is_wall_clinging` and `prior_state.cling_timer` on the next frame.
- **Constraints:**
  - `result.is_wall_clinging = eligible_for_cling` — the clinging flag on the result directly mirrors the eligibility boolean computed this frame.
  - `result.cling_timer` update rule:
    - If `eligible_for_cling == true`: `result.cling_timer = prior_state.cling_timer + effective_delta` — the timer accumulates by one physics timestep.
    - If `eligible_for_cling == false`: `result.cling_timer = 0.0` — the timer resets immediately.
  - There is no gradual decay of `cling_timer`; it is either accumulating (while clinging) or zero (when not clinging).
  - `effective_delta` is `max(0.0, delta)` — the same sanitized value used throughout `simulate()`.
  - `prior_state.cling_timer` and `prior_state.is_wall_clinging` must not be mutated.
  - The state update runs before the jump eligibility check (step 6), after the `pressing_toward_wall` and `eligible_for_cling` computations.
- **Assumptions:** The per-frame cling timer increment approach means that on the first frame of contact (`prior_state.cling_timer = 0.0`), the result timer is `0.0 + effective_delta`. On subsequent frames it continues to accumulate. The cling_timer value in `result` on the frame cling becomes ineligible is always `0.0` (immediate reset), not the accumulated value from the prior frame.
- **Scope / Context:** Inside the `simulate()` function body, in the wall cling state update block (step 5.5).

### 2. Acceptance Criteria

- **AC-30.1:** When `eligible_for_cling=true` and `prior_state.cling_timer=0.0` and `delta=0.016`: `result.is_wall_clinging=true` and `result.cling_timer=0.016` (tolerance EPSILON=1e-4).
- **AC-30.2:** When `eligible_for_cling=true` and `prior_state.cling_timer=0.5` and `delta=0.016`: `result.cling_timer=0.516` (tolerance EPSILON=1e-4). The timer accumulates from the prior value.
- **AC-30.3:** When `eligible_for_cling=false` (for any reason): `result.is_wall_clinging=false` and `result.cling_timer=0.0`, regardless of what `prior_state.cling_timer` was.
- **AC-30.4:** On the frame cling expires (when `prior_state.cling_timer >= max_cling_time` causes `eligible_for_cling=false`): `result.cling_timer=0.0` and `result.is_wall_clinging=false`. The timer does not accumulate on or beyond the expiry frame.
- **AC-30.5:** After `simulate()` returns, `prior_state.is_wall_clinging` retains its original value and `prior_state.cling_timer` retains its original value (no mutation of prior state).
- **AC-30.6:** When `delta=0.0` and `eligible_for_cling=true` and `prior_state.cling_timer=0.3`: `result.cling_timer=0.3` (timer does not change when delta is zero, since `effective_delta=0.0`). This is consistent with the existing delta=0 no-change invariant.
- **AC-30.7:** When `delta < 0.0` (e.g. `delta=-0.016`) and `eligible_for_cling=true` and `prior_state.cling_timer=0.3`: `effective_delta = max(0.0, -0.016) = 0.0`, so `result.cling_timer=0.3`. Negative delta does not decrease the timer.

### 3. Risk & Ambiguity Analysis

- **Risk R-30.1 (timer accumulation vs. cling_timer read for eligibility):** SPEC-29 condition 5 reads `prior_state.cling_timer < max_cling_time`. SPEC-30 writes `result.cling_timer`. Since eligibility uses `prior_state`, the accumulation written to `result` in SPEC-30 does not retroactively affect the current frame's eligibility — it only affects the next frame's eligibility check. This ordering is deliberate and consistent with the coyote timer pattern.
- **Risk R-30.2 (timer not resetting when not clinging):** If an implementation carries `cling_timer` forward instead of resetting to `0.0` when not clinging, subsequent cling sessions will start with a non-zero timer, reducing the available cling window on the next wall contact. AC-30.3 explicitly verifies the reset to zero.
- **Risk R-30.3 (result.cling_timer > max_cling_time on the accumulation frame):** When `prior_state.cling_timer` is close to `max_cling_time`, the accumulated `result.cling_timer` may exceed `max_cling_time`. This is acceptable — the check in SPEC-29 uses `prior_state.cling_timer < max_cling_time`, not `result.cling_timer`. On the next frame, `prior_state.cling_timer` will be the accumulated (possibly > max) value, which causes `eligible_for_cling=false` and immediately resets `result.cling_timer=0.0`. The timer is not clamped.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-31: Cling Gravity Modification

### 1. Spec Summary

- **Description:** When `result.is_wall_clinging` is true and a wall jump did not fire on the current frame, the gravity contribution to `result.velocity.y` in step 8 is scaled by `cling_gravity_scale` instead of the normal value. This causes a slow downward slide while clinging.
- **Constraints:**
  - Normal gravity formula (existing step 8, from SPEC-6): `result.velocity.y += gravity * effective_delta`
  - Modified cling gravity formula: `result.velocity.y += gravity * cling_gravity_scale * effective_delta`
  - The modification applies if and only if **both** of the following are true:
    1. `result.is_wall_clinging == true` (the player is clinging this frame, per SPEC-30).
    2. A wall jump did not fire this frame (see SPEC-33; the wall jump sets `result.is_wall_clinging = false`, so this condition is automatically satisfied by condition 1 — if wall jump fires, `result.is_wall_clinging` is `false` and the cling gravity branch is not taken).
  - Because a wall jump sets `result.is_wall_clinging = false` before the gravity step, checking `result.is_wall_clinging` in the gravity step is sufficient to determine whether to apply cling gravity. No separate "wall jump fired" flag is needed.
  - When `cling_gravity_scale = 1.0`: `gravity * 1.0 * effective_delta = gravity * effective_delta` — identical to normal gravity. No cling effect.
  - When `cling_gravity_scale = 0.0`: `gravity * 0.0 * effective_delta = 0.0` — the player hovers with no downward slide.
  - `cling_gravity_scale` must be the `MovementSimulation` instance's configured parameter (`self.cling_gravity_scale`), not a hardcoded constant.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** Inside the `simulate()` function body at step 8 (the gravity application step).

### 2. Acceptance Criteria

- **AC-31.1:** When `result.is_wall_clinging=true` (eligible cling, no wall jump), `gravity=980.0`, `cling_gravity_scale=0.1`, `delta=0.016`, and `result.velocity.y` before the gravity step is `50.0`: `result.velocity.y` after the gravity step is `50.0 + 980.0 * 0.1 * 0.016 = 50.0 + 1.568 = 51.568` (tolerance EPSILON=1e-4).
- **AC-31.2:** When `result.is_wall_clinging=false` (not clinging), same parameters: `result.velocity.y` after the gravity step is `50.0 + 980.0 * 0.016 = 50.0 + 15.68 = 65.68` (tolerance EPSILON=1e-4). Normal gravity applies.
- **AC-31.3:** When `cling_gravity_scale=0.0` and `result.is_wall_clinging=true`: gravity contribution is `980.0 * 0.0 * 0.016 = 0.0`. `result.velocity.y` does not change in the gravity step. The player hovers.
- **AC-31.4:** When `cling_gravity_scale=1.0` and `result.is_wall_clinging=true`: gravity contribution is `980.0 * 1.0 * 0.016 = 15.68`. This equals normal gravity — no cling reduction.
- **AC-31.5:** Changing `sim.cling_gravity_scale = 0.5` at runtime produces a gravity contribution of `980.0 * 0.5 * 0.016 = 7.84` on a clinging frame. This verifies the parameter is read from the instance and not hardcoded.
- **AC-31.6:** When a wall jump fires on the current frame (which sets `result.is_wall_clinging = false` before the gravity step), the gravity contribution is the normal `gravity * effective_delta`, not the scaled value. Wall jump frames are not subject to cling gravity.
- **AC-31.7:** When `delta=0.0`, the gravity contribution is `0.0` regardless of `result.is_wall_clinging` or `cling_gravity_scale`. The no-change-at-zero-delta invariant holds.

### 3. Risk & Ambiguity Analysis

- **Risk R-31.1 (wall jump frame gravity scale):** Because the wall jump step (SPEC-33) sets `result.is_wall_clinging = false` before the gravity step, the gravity check (`if result.is_wall_clinging`) correctly selects normal gravity on the wall jump frame. Implementations that check a separate `wall_jump_fired` flag or cache `eligible_for_cling` before the wall jump step can get this wrong. The spec specifies `result.is_wall_clinging` at the gravity step as the single source of truth.
- **Risk R-31.2 (cling_gravity_scale applied to entire velocity, not just addition):** The spec modifies only the per-frame gravity addition (`+= ...`), not the entire `result.velocity.y`. The player's accumulated downward velocity from prior frames (e.g. a long fall before touching a wall) is not scaled. Only the incremental gravity contribution of the current frame is reduced. This means a player arriving at a wall with high downward velocity will still have that high velocity initially; the cling gravity slows the acceleration, not the current velocity.
- **Risk R-31.3 (cling_gravity_scale > 1.0):** Values greater than `1.0` produce a gravity effect stronger than normal during a cling. This is not explicitly undefined behavior but is a nonsensical game configuration. The spec does not restrict the range above `1.0`. Implementations must not clamp `cling_gravity_scale` to `[0.0, 1.0]` — the parameter is a raw multiplier.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-32: Wall Jump Eligibility

### 1. Spec Summary

- **Description:** A wall jump is eligible when the player presses the jump button for the first time on a frame while actively clinging to a wall (as recorded in `prior_state.is_wall_clinging`), and has not already consumed their jump this airborne phase. Wall jump eligibility is evaluated in step 6 (the existing jump eligibility step), as an alternative branch to the regular floor/coyote jump.
- **Constraints:**
  - Wall jump eligibility condition (all three must be true simultaneously):
    1. `jump_just_pressed == true` (fresh jump button press on this frame; not held from a prior frame).
    2. `prior_state.is_wall_clinging == true` (the player was actively clinging on the prior frame).
    3. `NOT prior_state.jump_consumed` (the jump-consumed flag is clear).
  - This condition uses `prior_state.is_wall_clinging`, not `result.is_wall_clinging` or `eligible_for_cling`. This means:
    - If the player was clinging on frame N-1, they can wall-jump on frame N even if on frame N they release the directional input (which would make `eligible_for_cling=false` on frame N). The prior frame's cling state is the trigger.
    - If the player was not clinging on frame N-1 (first frame of wall contact), a wall jump is not available on frame N even if `eligible_for_cling=true` for frame N. Wall jump requires at least one prior frame of confirmed cling.
  - Wall jump eligibility is evaluated only when the regular jump condition fails. The precedence order (SPEC-34) is: (1) regular jump from floor/coyote takes absolute priority, (2) wall jump as a secondary option. If a player is both on the floor and clinging (a corner), the regular jump fires.
  - The exact local variable name for the wall jump eligibility boolean is `wall_jump_eligible`.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** Inside the `simulate()` function body at step 6 (jump eligibility and impulse), evaluated after regular jump eligibility is checked.

### 2. Acceptance Criteria

- **AC-32.1:** When `jump_just_pressed=true`, `prior_state.is_wall_clinging=true`, `prior_state.jump_consumed=false`: `wall_jump_eligible=true` and the wall jump impulse fires (SPEC-33).
- **AC-32.2:** When `jump_just_pressed=false` (all other conditions true): `wall_jump_eligible=false` and no wall jump fires.
- **AC-32.3:** When `prior_state.is_wall_clinging=false` (not clinging on prior frame, even if `eligible_for_cling=true` on this frame): `wall_jump_eligible=false` and no wall jump fires.
- **AC-32.4:** When `prior_state.jump_consumed=true` (all other conditions true): `wall_jump_eligible=false` and no wall jump fires.
- **AC-32.5:** When `prior_state.is_on_floor=true` AND `prior_state.is_wall_clinging=true` AND `jump_just_pressed=true` AND `prior_state.jump_consumed=false`: the regular jump fires (not the wall jump), because regular jump eligibility is checked and takes priority. `result.velocity.y = -sqrt(2.0 * gravity * jump_height) + gravity * effective_delta`. `result.velocity.x` is determined by the horizontal movement formula, not the wall jump formula.
- **AC-32.6:** When `prior_state.is_wall_clinging=true` but `prior_state.is_on_wall=false` is implied by the transition (i.e. the player was clinging last frame but the wall is no longer there this frame — `is_on_wall=false` this frame): `wall_jump_eligible` still evaluates based solely on `prior_state.is_wall_clinging`. A wall jump can fire even on the first frame the player leaves the wall, if the prior frame had active cling.

### 3. Risk & Ambiguity Analysis

- **Risk R-32.1 (using result.is_wall_clinging vs. prior_state.is_wall_clinging):** The wall jump condition reads `prior_state.is_wall_clinging`. Using `result.is_wall_clinging` (which reflects the current frame's eligibility) instead would block wall jump on frames where the player releases directional input toward the wall — requiring the player to hold the direction and press jump simultaneously, which is harder. The spec intentionally uses `prior_state` to allow a brief input window. AC-32.3 verifies this distinction.
- **Risk R-32.2 (wall jump eligibility conflicts with first-frame cling):** On the very first frame of wall contact, `prior_state.is_wall_clinging=false` (the player was not clinging on the frame before they hit the wall). A wall jump cannot fire on this frame. The player must cling for at least one complete physics frame before a wall jump is available. This is a deliberate design consequence of reading `prior_state`.
- **Risk R-32.3 (jump_consumed already true from regular jump before wall):** If a player regular-jumps and then hits a wall mid-air, `prior_state.jump_consumed=true`. Condition 3 blocks the wall jump. The player must land to reset `jump_consumed` before wall jumping. This is the intentional M1 constraint documented in CHECKPOINTS.md [M1-003].

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-33: Wall Jump Impulse

### 1. Spec Summary

- **Description:** When wall jump eligibility is met (SPEC-32), `simulate()` applies a two-component impulse: a vertical component using the same kinematic formula as the regular jump (with `wall_jump_height` instead of `jump_height`), and a horizontal component directed away from the wall surface. The wall jump simultaneously overrides both velocity components and terminates the cling state.
- **Constraints:**
  - Vertical impulse (before gravity is added in step 8):
    - `result.velocity.y = -sqrt(2.0 * gravity * wall_jump_height)`
    - Guard: if `wall_jump_height <= 0.0`, use `0.0` to prevent `sqrt(negative)` NaN. Exact guard: `var safe_wall_jump_height: float = wall_jump_height if wall_jump_height > 0.0 else 0.0`
    - Gravity is added after this impulse in step 8 (the same `gravity * effective_delta` as any other frame). On the wall jump frame: `result.velocity.y = -sqrt(2.0 * gravity * safe_wall_jump_height) + gravity * effective_delta`.
  - Horizontal impulse (replaces the horizontal velocity computation in step 7 for this frame):
    - `result.velocity.x = wall_normal_x * wall_jump_horizontal_speed`
    - `wall_normal_x` is the `wall_normal_x` parameter passed to `simulate()` this frame (the outward-facing wall normal X component).
    - `wall_jump_horizontal_speed` is `self.wall_jump_horizontal_speed` (the `MovementSimulation` instance parameter, default 180.0, always positive).
    - Sign behavior: if `wall_normal_x = -1.0` (wall to the right), then `result.velocity.x = -1.0 * 180.0 = -180.0` (pushing left, away from the wall). If `wall_normal_x = 1.0` (wall to the left), then `result.velocity.x = 1.0 * 180.0 = 180.0` (pushing right, away from the wall).
  - After applying the wall jump impulse:
    - `result.jump_consumed = true` — shared flag is consumed, preventing any further jump until the player lands.
    - `result.is_wall_clinging = false` — the cling state is terminated on the wall jump frame. This also ensures SPEC-31's gravity step applies normal gravity (not cling gravity) on the wall jump frame.
  - The horizontal velocity set by the wall jump (step 7 override) is the final horizontal velocity for this frame; the normal horizontal movement formulas in step 7 do not apply on wall jump frames.
  - The jump cut check (step 9) still applies on the wall jump frame, because `jump_pressed` may be false (tap-and-release jump). This is consistent with the existing regular jump behavior. In practice, if the player taps jump, the vertical component may be cut to `jump_cut_velocity`.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** Inside the `simulate()` function body at step 6 (jump eligibility and impulse) for the vertical component, and at step 7 (horizontal velocity) for the horizontal component.

### 2. Acceptance Criteria

- **AC-33.1:** When wall jump fires with `gravity=980.0`, `wall_jump_height=100.0`, `wall_normal_x=-1.0`, `wall_jump_horizontal_speed=180.0`, `delta=0.016`: `result.velocity.y = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016`. Computed: `-sqrt(196000.0) + 15.68 = -442.7189... + 15.68 = -427.0389...` (tolerance EPSILON=1e-4). `result.velocity.x = -1.0 * 180.0 = -180.0` (tolerance EPSILON=1e-4).
- **AC-33.2:** When wall jump fires with `wall_normal_x=1.0` (wall to the left): `result.velocity.x = 1.0 * 180.0 = 180.0`. The player is launched to the right.
- **AC-33.3:** After wall jump fires: `result.jump_consumed = true` and `result.is_wall_clinging = false`.
- **AC-33.4:** After wall jump fires: `prior_state.is_wall_clinging` and `prior_state.jump_consumed` are not mutated (immutability invariant).
- **AC-33.5:** When `wall_jump_height = 0.0`: `result.velocity.y = -sqrt(0.0) + gravity * effective_delta = 0.0 + 15.68 = 15.68`. No NaN. `result.jump_consumed = true` (zero-height wall jump still consumes the flag).
- **AC-33.6:** Changing `sim.wall_jump_horizontal_speed = 250.0` at runtime: when wall jump fires with `wall_normal_x = -1.0`, `result.velocity.x = -1.0 * 250.0 = -250.0`. Verifies the parameter is read from the instance.
- **AC-33.7:** Changing `sim.wall_jump_height = 50.0` at runtime: `result.velocity.y = -sqrt(2.0 * 980.0 * 50.0) + 980.0 * 0.016 = -sqrt(98000.0) + 15.68 ≈ -313.05 + 15.68 = -297.37` (tolerance EPSILON=1e-4). Verifies the parameter is read from the instance.
- **AC-33.8:** When the wall jump fires and `jump_pressed=false` (tap-and-release): the jump cut check (step 9) applies. If `result.velocity.y < jump_cut_velocity` after impulse + gravity, `result.velocity.y` is clamped to `jump_cut_velocity`. Example with `jump_cut_velocity=-200.0`: `result.velocity.y ≈ -427.04 < -200.0`, so `result.velocity.y = -200.0`.
- **AC-33.9:** When the wall jump fires and `jump_pressed=true` (held): the jump cut check does not trigger (`NOT jump_pressed` is false). `result.velocity.y` retains the full impulse + gravity value from AC-33.1.

### 3. Risk & Ambiguity Analysis

- **Risk R-33.1 (horizontal impulse direction):** The horizontal component is `wall_normal_x * wall_jump_horizontal_speed`. Since `wall_normal_x` from Godot's `get_wall_normal()` points away from the wall (outward), this naturally launches the player away from the wall. An implementer who multiplies by `-wall_normal_x` instead would launch the player into the wall. AC-33.1 and AC-33.2 provide concrete sign-verified examples.
- **Risk R-33.2 (wall jump overrides horizontal step 7):** The horizontal impulse from the wall jump replaces the entire step 7 horizontal calculation for that frame. An implementation that applies step 7 first and then adds the wall jump impulse on top would produce an incorrect result (e.g., acceleration toward a target plus the wall jump impulse). The spec requires the wall jump to set `result.velocity.x` directly, not additively. The wall jump fires in step 6 context and step 7 is skipped for this frame.
- **Risk R-33.3 (jump cut on wall jump frame):** The jump cut step (step 9) applies unconditionally if `NOT jump_pressed`. On a tapped wall jump, the full impulse will immediately be cut to `jump_cut_velocity`. AC-33.8 documents this as the correct and expected behavior — it is consistent with how regular jumps work and allows variable-height wall jumps.
- **Risk R-33.4 (sqrt NaN guard for wall_jump_height):** The same guard as the regular jump is required: `wall_jump_height if wall_jump_height > 0.0 else 0.0`. Without this guard, negative `wall_jump_height` produces `sqrt(negative)` = NaN on some platforms, corrupting `result.velocity.y`. AC-33.5 tests zero height; adversarial tests cover negative height.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-34: Order of Operations (Normative)

### 1. Spec Summary

- **Description:** The complete normative order of operations for `simulate()` after M1-003 is defined here. This extends the existing 10-step order from M1-001 and M1-002 by inserting wall cling logic as step 5.5 and modifying step 6 (jump eligibility) and step 8 (gravity) to handle wall jump and cling gravity respectively.
- **Constraints:**
  - The complete order is:
    1. Compute `effective_delta = max(0.0, delta)`.
    2. Sanitize `input_axis` (NaN → 0.0; Inf/-Inf → clamp ±1.0) → `safe_axis`.
    3. Allocate `result: MovementState = MovementState.new()`.
    4. Coyote timer update (SPEC-19): if `prior_state.is_on_floor` → `result.coyote_timer = coyote_time`; else → `result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)`.
    5. jump_consumed carry-forward / landing reset (SPEC-21): if `prior_state.is_on_floor` → `result.jump_consumed = false`; else → `result.jump_consumed = prior_state.jump_consumed`.
    5.5. NEW — Wall cling state update (SPEC-28, SPEC-29, SPEC-30):
       a. Compute `pressing_toward_wall = (safe_axis * wall_normal_x) < 0.0`.
       b. Compute `eligible_for_cling = is_on_wall AND NOT prior_state.is_on_floor AND pressing_toward_wall AND NOT prior_state.jump_consumed AND prior_state.cling_timer < max_cling_time`.
       c. Set `result.is_wall_clinging = eligible_for_cling`.
       d. Set `result.cling_timer`: if `eligible_for_cling` → `prior_state.cling_timer + effective_delta`; else → `0.0`.
    6. Jump / wall jump eligibility and impulse:
       a. Check regular jump eligibility: `eligible = jump_just_pressed AND (prior_state.is_on_floor OR prior_state.coyote_timer > 0.0) AND NOT prior_state.jump_consumed`. If eligible: set `result.velocity.y = -sqrt(2.0 * gravity * safe_jump_height)`; set `result.jump_consumed = true`. Go to step 7.
       b. If NOT regular jump eligible: check wall jump eligibility (SPEC-32): `wall_jump_eligible = jump_just_pressed AND prior_state.is_wall_clinging AND NOT prior_state.jump_consumed`. If `wall_jump_eligible`: set `result.velocity.y = -sqrt(2.0 * gravity * safe_wall_jump_height)`; set `result.velocity.x = wall_normal_x * wall_jump_horizontal_speed`; set `result.jump_consumed = true`; set `result.is_wall_clinging = false`. Go to step 9 (bypass normal horizontal step 7 since x is already set).
       c. If neither jump eligible: `result.velocity.y = prior_state.velocity.y`.
    7. Horizontal velocity (SPEC-5, cases 1-4) — **skipped if wall jump fired in step 6b**. Otherwise applies normally.
    8. Gravity: if `result.is_wall_clinging == true` → `result.velocity.y += gravity * cling_gravity_scale * effective_delta`; else → `result.velocity.y += gravity * effective_delta`.
    9. Jump cut (SPEC-20): if `NOT jump_pressed AND result.velocity.y < jump_cut_velocity` → `result.velocity.y = jump_cut_velocity`.
    10. `result.is_on_floor = prior_state.is_on_floor` (pass-through, AC-4.3).
    11. Return `result`.
  - The step numbering 5.5 is a naming convention in this spec; the implementation may use any internal variable or code organization as long as the logical order is preserved.
  - Step 6a (regular jump) takes absolute priority over step 6b (wall jump). Both cannot fire on the same frame.
  - Step 6b sets `result.velocity.x` directly. Steps 7 (horizontal formula) must not overwrite this value when step 6b has fired. The implementation must track whether a wall jump fired and skip the horizontal computation accordingly, or structure the code so step 7 is inside the `else` branch of the wall jump condition.
  - All reads of `prior_state` fields in steps 4 through 6 use the values from the function parameter (the incoming state), never `result` fields.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-003].
- **Scope / Context:** The entire `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-34.1:** On a frame where regular jump fires (`prior_state.is_on_floor=true`, `jump_just_pressed=true`, `prior_state.jump_consumed=false`), even if `prior_state.is_wall_clinging=true` and `is_on_wall=true`: `result.velocity.y` uses `jump_height` (not `wall_jump_height`); `result.velocity.x` uses the horizontal movement formula (not the wall jump horizontal impulse). Regular jump takes precedence.
- **AC-34.2:** On a frame where a wall jump fires (`jump_just_pressed=true`, `prior_state.is_wall_clinging=true`, `prior_state.jump_consumed=false`, `prior_state.is_on_floor=false`): `result.velocity.x = wall_normal_x * wall_jump_horizontal_speed` (not the acceleration/friction formula). The horizontal movement formula does not apply.
- **AC-34.3:** On a wall jump frame, `result.is_wall_clinging = false` and the gravity step applies `gravity * effective_delta` (normal gravity, not cling gravity).
- **AC-34.4:** On a cling frame where no jump fires: coyote timer is updated before cling eligibility is evaluated, and jump eligibility check (step 6) reads `prior_state.coyote_timer` (not `result.coyote_timer`). This ordering is preserved from the M1-002 spec.
- **AC-34.5:** On a wall jump frame, the jump cut check (step 9) still applies. The wall jump vertical impulse can be cut by releasing the jump button.
- **AC-34.6:** When `is_on_wall=false` and `wall_normal_x=0.0` (no wall contact), the behavior of `simulate()` is identical to calling the M1-002 five-argument version with the same non-wall inputs. All existing SPEC-1 through SPEC-24 behaviors are preserved.
- **AC-34.7:** `result.is_on_floor = prior_state.is_on_floor` (step 10 pass-through) is not affected by any wall cling logic. It retains its M1-001 behavior.

### 3. Risk & Ambiguity Analysis

- **Risk R-34.1 (horizontal step 7 running after wall jump):** If step 7 is not skipped after a wall jump, the horizontal velocity set by the wall jump (`wall_normal_x * wall_jump_horizontal_speed`) is overwritten by the acceleration/friction formula on the same frame. This is a subtle structural error that AC-34.2 directly tests. The implementation must ensure step 7 is guarded by a branch that excludes the wall jump case.
- **Risk R-34.2 (coyote timer interacting with cling):** The coyote timer update (step 4) runs unconditionally before cling eligibility (step 5.5). While the player is clinging (`is_on_wall=true`, `is_on_floor=false`), the coyote timer decrements each frame. If a player was on the floor and then immediately clings a wall, the coyote timer may still be positive and could allow a regular floor jump to fire (step 6a) on the same frame as the first cling attempt. This is correct behavior per the order-of-operations: step 6a reads `prior_state.coyote_timer`, not the current cling state.
- **Risk R-34.3 (eligible_for_cling vs. result.is_wall_clinging after step 6b):** Step 6b sets `result.is_wall_clinging = false`. This overrides the value set in step 5.5c (which set it to `eligible_for_cling`). Implementations must not cache `eligible_for_cling` and re-apply it after step 6 — the step 6b assignment is final.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-35: Call-Site Migration (5-arg to 7-arg)

### 1. Spec Summary

- **Description:** Every existing call to `simulate()` across all four test files must be updated from the 5-argument M1-002 signature to the new 7-argument signature (SPEC-27). The two new arguments `is_on_wall: bool` and `wall_normal_x: float` must be inserted as the fifth and sixth arguments (before `delta`), with the values `false` and `0.0` respectively. This preserves all existing test behavior: no wall cling, no wall jump, no cling gravity modification, no cling state update.
- **Constraints:**
  - Affected files (migration only; test logic and assertion values are not changed):
    - `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd`
    - `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd`
    - `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd`
    - `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd`
  - Exact replacement pattern: every occurrence of `sim.simulate(state, <expr>, <bool>, <bool>, delta)` becomes `sim.simulate(state, <expr>, <bool>, <bool>, false, 0.0, delta)`.
  - The new arguments are always the literals `false` and `0.0` — not variables, not expressions, not computed values — in the migrated existing tests. (New wall cling tests in SPEC-25 through SPEC-34 will use real values.)
  - Assertion values, test names, helper function signatures, and all other code in the four files must not change.
  - The `_make_state_with` helper is not modified.
  - After migration, all existing tests in all four files must pass against the updated `simulate()` implementation. Zero regressions are acceptable.
  - The `run_tests.gd` runner does not call `simulate()` directly and requires no changes for this SPEC item (it is updated separately per Task 2/3 to add new suites).
  - This migration is the responsibility of the Test Designer Agent (Task 2 in the execution plan).
- **Assumptions:** All four test files currently have only 5-argument calls to `simulate()`. No file already contains 7-argument calls. If any call site with a different argument count is found, it must be escalated to the Planner rather than silently fixed.
- **Scope / Context:** Four test files listed above; no production code files.

### 2. Acceptance Criteria

- **AC-35.1:** After migration, `godot --headless --check-only` passes with no parse errors on all four test files.
- **AC-35.2:** After migration, running the full test suite (all suites in `run_tests.gd`) produces the same pass count as before migration: all existing tests pass, zero regressions.
- **AC-35.3:** No `simulate()` call in the four test files retains fewer than 7 arguments. Any 5-argument call is a migration failure.
- **AC-35.4:** The new fifth and sixth arguments are exactly the literal `false` and `0.0` (in that order) in all migrated calls in the four files. No other values are used in the migration of existing calls.
- **AC-35.5:** The `_make_state_with` helper function signature is unchanged. It still accepts `(vx, vy, on_floor)` with no additional parameters.
- **AC-35.6:** No test names, assertion messages, assertion values, or comment text in the four files is altered by the migration.

### 3. Risk & Ambiguity Analysis

- **Risk R-35.1 (missed call sites):** If any `simulate()` call in the four files is not updated, `godot --headless --check-only` will report a type error (argument count mismatch). Systematic search via grep for `sim.simulate(` in all four files should catch all instances.
- **Risk R-35.2 (existing jump tests with jump_pressed=true):** Some existing tests in `test_jump_simulation.gd` and `test_jump_simulation_adversarial.gd` pass `jump_pressed=true` as the third argument (to suppress jump cut). These tests become `sim.simulate(state, axis, true, <bool>, false, 0.0, delta)`. The `jump_pressed=true` value must be preserved — only the two new arguments are added. The migration must not accidentally flip this value to false.
- **Risk R-35.3 (argument count verification method):** Godot's `--check-only` validates argument counts for statically typed functions. Since `simulate()` is typed with explicit type annotations, a call with the wrong number of arguments will produce a parse error. The Test Designer Agent should verify this check passes after migration before proceeding.

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Requirement SPEC-36: Frame-Rate Independence

### 1. Spec Summary

- **Description:** All new time-dependent computations introduced by M1-003 must be frame-rate independent: results must not depend on the physics tick rate. This extends the existing frame-rate independence requirement (SPEC-12, SPEC-24) to the wall cling and wall jump mechanics.
- **Constraints:**
  - `cling_timer` increments by `effective_delta` each clinging frame. Over N frames of cling duration D, the accumulated timer is `sum(effective_delta_i)` across all frames. This equals the elapsed real time regardless of frame rate, making the max cling duration consistent across frame rates.
  - Cling gravity formula: `gravity * cling_gravity_scale * effective_delta` — the `effective_delta` scaling ensures the gravitational contribution per frame scales correctly with the timestep. A player clinging for 1 second accumulates the same downward velocity regardless of whether that second is 60 frames at 0.016667s each or 30 frames at 0.033333s each.
  - Wall jump vertical impulse: `-sqrt(2.0 * gravity * wall_jump_height)` is a velocity, not an acceleration. It is applied once, in full, on the jump frame. It is frame-rate independent because it is not multiplied by `delta`. The `gravity * effective_delta` added after it (step 8) is already frame-rate independent per SPEC-12.
  - Wall jump horizontal impulse: `wall_normal_x * wall_jump_horizontal_speed` is also a direct velocity assignment, not scaled by `delta`. It is frame-rate independent by the same argument.
  - No new time-dependent value is computed using `delta` directly (unscaled) in a way that would produce different results at different frame rates.
  - `effective_delta = max(0.0, delta)` is used throughout, as established by SPEC-12.
- **Assumptions:** Frame-rate independence of wall jump impulses is verified by the same "two half-steps vs. one full step" methodology established in SPEC-12 and SPEC-24, applied to the cling timer accumulation and cling gravity formulas.
- **Scope / Context:** All new computations in the `simulate()` function body introduced by SPEC-28 through SPEC-33.

### 2. Acceptance Criteria

- **AC-36.1:** `cling_timer` accumulation at two half-steps equals accumulation at one full step. Given `prior_state.cling_timer=0.0`, `delta=0.016`: one full step produces `result.cling_timer=0.016`. Two half-steps (`delta=0.008` each): first step produces `cling_timer=0.008`, second step produces `cling_timer=0.016`. Results match within EPSILON=1e-4.
- **AC-36.2:** Cling gravity accumulation at two half-steps equals accumulation at one full step. Given `gravity=980.0`, `cling_gravity_scale=0.1`, starting `velocity.y=0.0`, `delta=0.016`: one full step produces `delta_vy = 980.0 * 0.1 * 0.016 = 1.568`. Two half-steps: each produces `980.0 * 0.1 * 0.008 = 0.784`; total = `1.568`. Results match within EPSILON=1e-4.
- **AC-36.3:** Wall jump vertical impulse (`-sqrt(2.0 * gravity * wall_jump_height)`) is frame-rate independent by design: the impulse value is identical regardless of `delta`. At `gravity=980.0`, `wall_jump_height=100.0`: impulse = `-sqrt(196000.0) ≈ -442.719...` at any delta value. The per-frame gravity addition `gravity * effective_delta` is independently frame-rate independent per SPEC-12 AC-12.3.
- **AC-36.4:** Wall jump horizontal impulse (`wall_normal_x * wall_jump_horizontal_speed`) is frame-rate independent: the velocity assigned is identical regardless of `delta`. At `wall_normal_x=-1.0`, `wall_jump_horizontal_speed=180.0`: `result.velocity.x = -180.0` regardless of delta.
- **AC-36.5:** At `delta=0.0` (zero timestep), all new computations produce no-change behavior: `cling_timer` does not increment (adds `0.0`), cling gravity contributes `0.0`, wall jump impulses are still applied at full magnitude (impulses are velocity assignments, not delta-scaled). This is consistent with the existing AC-4.4 delta=0.0 invariant for velocity changes that are acceleration-based.

### 3. Risk & Ambiguity Analysis

- **Risk R-36.1 (cling_timer not using effective_delta):** If the implementation uses raw `delta` instead of `effective_delta = max(0.0, delta)` for the cling timer increment, a negative delta would decrement the timer, corrupting state. AC-30.7 (from SPEC-30) verifies this edge case, and the frame-rate independence tests in this spec provide additional verification.
- **Risk R-36.2 (wall jump impulse accidentally scaled by delta):** A common implementation error is to multiply the wall jump impulse by `delta` (treating it as an acceleration rather than a velocity). This would produce tiny impulses at low frame rates and large impulses at high frame rates. AC-36.3 and AC-36.4 verify the impulse is frame-rate independent by checking that the same impulse is produced regardless of delta.
- **Risk R-36.3 (cling gravity half-step vs. full-step equality):** Unlike impulses, the cling gravity formula uses `effective_delta`. The half-step test (AC-36.2) verifies that `(gravity * cling_gravity_scale * half_delta) * 2 == gravity * cling_gravity_scale * full_delta`. This is guaranteed by simple arithmetic but should be tested explicitly to catch cases where the implementation applies gravity differently (e.g., squaring delta or using a nonlinear formula).

### 4. Clarifying Questions

None. All ambiguities are resolved via CHECKPOINTS.md entries [M1-003].

---

## Summary: Normative Spec Item Index

| SPEC # | Topic | Key Files |
|--------|-------|-----------|
| SPEC-25 | MovementState new fields: `is_wall_clinging: bool`, `cling_timer: float` | `movement_simulation.gd` |
| SPEC-26 | New config parameters: `cling_gravity_scale`, `max_cling_time`, `wall_jump_height`, `wall_jump_horizontal_speed` | `movement_simulation.gd` |
| SPEC-27 | simulate() extended signature: `is_on_wall: bool`, `wall_normal_x: float` as new params 5 and 6 (before `delta`) | `movement_simulation.gd`, all call sites |
| SPEC-28 | Pressing-toward-wall detection: `(safe_axis * wall_normal_x) < 0.0` | `movement_simulation.gd` |
| SPEC-29 | Cling eligibility: 5-condition boolean, using `prior_state` fields | `movement_simulation.gd` |
| SPEC-30 | Cling state update: `result.is_wall_clinging` and `result.cling_timer` write rules | `movement_simulation.gd` |
| SPEC-31 | Cling gravity: `gravity * cling_gravity_scale * effective_delta` when clinging and no wall jump | `movement_simulation.gd` |
| SPEC-32 | Wall jump eligibility: `jump_just_pressed AND prior_state.is_wall_clinging AND NOT prior_state.jump_consumed` | `movement_simulation.gd` |
| SPEC-33 | Wall jump impulse: vertical kinematic formula, horizontal `wall_normal_x * wall_jump_horizontal_speed`, `jump_consumed=true`, `is_wall_clinging=false` | `movement_simulation.gd` |
| SPEC-34 | Order of operations: complete normative 11-step sequence for M1-003 | `movement_simulation.gd` |
| SPEC-35 | Call-site migration: all 4 existing test files updated from 5-arg to 7-arg with `false, 0.0` | 4 test files |
| SPEC-36 | Frame-rate independence: `cling_timer` and cling gravity use `effective_delta`; wall jump impulses are velocity assignments | `movement_simulation.gd` |
