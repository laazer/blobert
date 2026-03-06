# Chunk Detach Simulation Specification
# M1-005 — chunk_detach.md
# SPEC-46 through SPEC-53
#
# Prerequisite specs: SPEC-1 through SPEC-45
#   SPEC-1  through SPEC-14: movement_controller.md / M1-001
#   SPEC-15 through SPEC-24: jump_tuning.md / M1-002
#   SPEC-25 through SPEC-36: wall_cling.md / M1-003
#   SPEC-37 through SPEC-45: basic_camera_follow.md / M1-004
# Continuing numbering from SPEC-45.
#
# Files affected:
#   /Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd (modified)
#   /Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd (modified)
#   /Users/jacobbrandt/workspace/blobert/scenes/chunk.tscn (new)
#   /Users/jacobbrandt/workspace/blobert/project.godot (modified)
#   /Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation_adversarial.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd (updated)
#   /Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd (call-site migration only)
#   /Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation_adversarial.gd (call-site migration only)

---

## Requirement SPEC-46: MovementState `has_chunk` Field Declaration

### 1. Spec Summary

- **Description:** A new typed field `has_chunk: bool = true` is added to the `MovementState` inner class inside `scripts/movement_simulation.gd`. This field represents whether the player body currently has a chunk attached. It follows the same declaration pattern as all existing `MovementState` fields: typed, explicitly defaulted, declared as a bare `var` (no `@export`). `MovementState.new()` called with no arguments must produce a `MovementState` instance where `has_chunk` equals `true`. The total number of fields in `MovementState` becomes seven: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`.
- **Constraints:**
  - The field must be declared `var has_chunk: bool = true` (explicit type annotation `bool`, explicit initializer `true`).
  - The field is the last declaration in the `MovementState` class body, after `cling_timer`.
  - No `@export` annotation. `MovementState` is not a Node; inspector exposure does not apply.
  - No `@onready` annotation. This is a plain value field.
  - The field name is exactly `has_chunk` — no alternative names (`chunk_attached`, `is_holding_chunk`, etc.) are acceptable because downstream tickets M1-006 and M1-007 reference this field by name.
  - The `MovementState` inner class comment block at the top of the class (lines beginning `# AC-`) must be extended with the line: `# AC-46.1: has_chunk: bool = true`.
- **Assumptions:** No assumptions. All constraints are fully specified by the planner and confirmed by the execution plan.
- **Scope / Context:** Applies exclusively to the `MovementState` inner class inside `scripts/movement_simulation.gd`. Does not affect any other class, file, or scene. The field is read by `simulate()` (as `prior_state.has_chunk`) and written to the returned `result` by the detach step (SPEC-48). The field is also copied back by `player_controller.gd` (SPEC-52). Does not apply to `camera_follow.gd`, `run_tests.gd`, or any other file.

### 2. Acceptance Criteria

- **AC-46.1:** The `MovementState` class body contains the declaration `var has_chunk: bool = true` with explicit type and explicit default. No other form is acceptable.
- **AC-46.2:** `MovementState.new()` called with no arguments produces an instance where `has_chunk == true`. Example: `var s := MovementSimulation.MovementState.new(); assert(s.has_chunk == true)`.
- **AC-46.3:** `has_chunk` is the seventh and final field in `MovementState`. The field ordering from first to last is: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`.
- **AC-46.4:** `godot --headless --check-only` run against `scripts/movement_simulation.gd` produces zero diagnostics after this change.
- **AC-46.5:** All prior tests (test_movement_simulation.gd, test_movement_simulation_adversarial.gd, test_jump_simulation.gd, test_jump_simulation_adversarial.gd, test_wall_cling_simulation.gd, test_wall_cling_simulation_adversarial.gd) continue to pass after this change with no modification to their assertion values. (The `has_chunk` field is added with a default; existing tests that do not reference it are unaffected.)

### 3. Risk and Ambiguity Analysis

- **R-46.1 Field ordering.** GDScript field declaration order in an inner class does not affect runtime behavior, but the spec requires `has_chunk` to be last. An implementer who inserts it elsewhere (e.g., after `velocity`) satisfies the functional requirement but violates this structural constraint, which matters for diff readability and consistency with the spec comment block.
- **R-46.2 Missing type annotation.** A declaration like `var has_chunk = true` (without `: bool`) would violate SPEC-53 NF-01 (all new variables explicitly typed). GDScript will infer `bool` from the literal `true`, but the explicit annotation is required.
- **R-46.3 Default value false.** If an implementer accidentally writes `var has_chunk: bool = false`, all existing sessions start as "detached," which is semantically wrong and will break SPEC-47 and SPEC-52 spawn logic.

### 4. Clarifying Questions

None. All constraints are fully specified.

---

## Requirement SPEC-47: `has_chunk` Default Value Semantics

### 1. Spec Summary

- **Description:** `has_chunk = true` means the player body currently holds the chunk (chunk is attached and not yet in the world as a separate entity). `has_chunk = false` means the chunk has been detached and exists as a separate `RigidBody2D` node in the scene tree (or was detached at some point and never recalled). This is a semantic convention that all agents must follow consistently. The simulation itself never sets `has_chunk = true` — the only transition to `true` is the recall mechanic (M1-007), which is out of scope for this ticket. The simulation can only set `has_chunk = false` (via the detach step, SPEC-48) or carry the existing value forward (no change to `has_chunk`).
- **Constraints:**
  - The simulation's `simulate()` function must never assign `result.has_chunk = true` in any code path. It may only assign `result.has_chunk = false` (detach case) or `result.has_chunk = prior_state.has_chunk` (carry-forward case).
  - The initial `MovementState` created by `_ready()` in `player_controller.gd` inherits the field default, producing `has_chunk = true` on the first frame — the player begins holding the chunk.
  - No future spec item in SPEC-46 through SPEC-53 may add logic that sets `has_chunk = true` inside `simulate()`.
  - The field value `false` is terminal within this ticket's scope: once set to `false`, no simulation logic in this ticket returns it to `true`.
- **Assumptions:** The recall transition (`has_chunk: false → true`) is fully owned by M1-007 and is outside the scope of this spec. This assumption is logged in CHECKPOINTS.md.
- **Scope / Context:** Applies to the semantic interpretation of `has_chunk` across all files in this ticket. Any agent reading `has_chunk` from a `MovementState` (in test files, in `player_controller.gd`, in `simulate()`) must treat `true` as "chunk is attached" and `false` as "chunk is detached."

### 2. Acceptance Criteria

- **AC-47.1:** A freshly allocated `MovementState` (via `.new()`) has `has_chunk == true`. Example: `var s := MovementSimulation.MovementState.new(); assert(s.has_chunk == true)`.
- **AC-47.2:** After calling `simulate()` with `detach_just_pressed = false` and any `prior_state` (regardless of `prior_state.has_chunk`), `result.has_chunk == prior_state.has_chunk` (value carried forward, not forced to `true`). Example: if `prior_state.has_chunk == false` and `detach_just_pressed == false`, then `result.has_chunk == false`.
- **AC-47.3:** No code path inside `simulate()` assigns `result.has_chunk = true` unconditionally or sets it to a hardcoded `true`. The only source of `true` in `has_chunk` is the field initializer on `MovementState`.
- **AC-47.4:** `prior_state.has_chunk` is never mutated by `simulate()`. The prior_state passed to `simulate()` retains its original `has_chunk` value after the call completes (immutability contract inherited from all prior `MovementState` fields).

### 3. Risk and Ambiguity Analysis

- **R-47.1 Accidental recall in simulation.** An implementer adding logic for "re-attach on floor" or similar might accidentally add `result.has_chunk = true` in a grounded branch. This must not happen; SPEC-47 explicitly restricts simulation from ever setting `has_chunk = true`.
- **R-47.2 Confusion with pass-through pattern.** `is_on_floor` is a pure pass-through (always written from `prior_state.is_on_floor`). `has_chunk` is similar but not identical: it carries forward in the no-detach case and transitions to `false` in the detach case. An implementer who treats `has_chunk` as a pure pass-through would miss the detach case.

### 4. Clarifying Questions

None. The "recall is M1-007" constraint is confirmed by the ticket's execution plan.

---

## Requirement SPEC-48: Detach Step — Condition, Result, and Order of Operations

### 1. Spec Summary

- **Description:** A new final step is appended to `simulate()` in `movement_simulation.gd`, after the existing step 16 (`is_on_floor` pass-through, currently the last step). This step evaluates whether a detach should occur this frame and sets `result.has_chunk` accordingly. The complete logic for this step is:

  ```
  detach_eligible: bool = detach_just_pressed AND prior_state.has_chunk
  if detach_eligible:
      result.has_chunk = false
  else:
      result.has_chunk = prior_state.has_chunk   # carry-forward
  ```

  This step reads only `detach_just_pressed` (the new 7th argument) and `prior_state.has_chunk`. It writes only `result.has_chunk`. No other simulation fields (`velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`) are read or written in this step.

- **Constraints:**
  - This step is step 17 in the normative order of operations. The existing step numbering (1 through 16) is preserved; this step is appended as step 17.
  - The step must be positioned after step 16 (`is_on_floor` pass-through) in the `simulate()` function body.
  - The `detach_eligible` intermediate variable must be typed `bool` (e.g., `var detach_eligible: bool = ...`).
  - The carry-forward branch (`result.has_chunk = prior_state.has_chunk`) must execute on every non-detach frame, including frames where `detach_just_pressed = true` but `prior_state.has_chunk = false` (no-op: carrying forward `false` is still an explicit assignment).
  - `result.has_chunk` must be explicitly set on every code path in this step. There must be no uninitialized path where `result.has_chunk` retains the default `true` from `MovementState.new()` on a frame where `prior_state.has_chunk = false` and `detach_just_pressed = false`. The carry-forward assignment handles this.
  - The normative order-of-operations comment block at the top of `simulate()` must be updated to document step 17.
  - The SPEC comment block at the top of `movement_simulation.gd` must be updated to add `SPEC-48 — Detach step (appended after is_on_floor pass-through)`.
- **Assumptions:** No assumptions. Execution plan specifies the exact logic.
- **Scope / Context:** Applies exclusively to `scripts/movement_simulation.gd`, `simulate()` function body. The step is headlessly testable (no engine references).

### 2. Acceptance Criteria

- **AC-48.1 Detach fires:** When `prior_state.has_chunk = true` AND `detach_just_pressed = true`, `result.has_chunk == false`. Example:
  ```
  prior.has_chunk = true
  result = sim.simulate(prior, 0.0, false, false, false, 0.0, true, 0.016)
  assert(result.has_chunk == false)
  ```
- **AC-48.2 No-op when already detached:** When `prior_state.has_chunk = false` AND `detach_just_pressed = true`, `result.has_chunk == false` (carry-forward of `false`; not an error or state corruption). Example:
  ```
  prior.has_chunk = false
  result = sim.simulate(prior, 0.0, false, false, false, 0.0, true, 0.016)
  assert(result.has_chunk == false)
  ```
- **AC-48.3 Carry-forward when not pressed:** When `detach_just_pressed = false` and `prior_state.has_chunk = true`, `result.has_chunk == true`. Example:
  ```
  prior.has_chunk = true
  result = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
  assert(result.has_chunk == true)
  ```
- **AC-48.4 Carry-forward preserves false:** When `detach_just_pressed = false` and `prior_state.has_chunk = false`, `result.has_chunk == false`. (Ensures no accidental recall.)
- **AC-48.5 No velocity mutation:** Regardless of `detach_just_pressed` value, `result.velocity` is identical to what it would have been without the detach step. Detach does not alter `velocity.x`, `velocity.y`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, or `cling_timer`.
- **AC-48.6 Position in order of operations:** The detach step code appears after the `is_on_floor` pass-through assignment (`result.is_on_floor = prior_state.is_on_floor`) and before the `return result` statement.
- **AC-48.7 Delta zero with detach:** When `delta = 0.0` and `detach_just_pressed = true` and `prior_state.has_chunk = true`, `result.has_chunk == false`. (Detach is input-driven, not time-driven; zero delta does not suppress it.)
- **AC-48.8 Prior state immutability:** After calling `simulate()` with any combination of inputs, `prior_state.has_chunk` retains its value from before the call.

### 3. Risk and Ambiguity Analysis

- **R-48.1 Step ordering ambiguity.** The comment block in `movement_simulation.gd` currently documents steps 1–15 in the `simulate()` comment header and has 16 code steps in the body (step 16 is `is_on_floor` pass-through). The new detach step is step 17 in the body; the comment header must also be updated to list 17 steps total. Failing to update the comment header is not a runtime error but violates the documentation contract.
- **R-48.2 Result default value.** `MovementState.new()` produces `has_chunk = true`. If the carry-forward branch is accidentally omitted (e.g., only the `if detach_eligible` branch is written), non-detach frames where `prior_state.has_chunk = false` would incorrectly produce `result.has_chunk = true` (the default). Both branches of the if/else must be present.
- **R-48.3 Wrong step placement.** If detach step is placed before the `is_on_floor` pass-through (step 16) or before gravity (step 14), the result is functionally identical for this ticket (detach does not interact with those fields) but violates the normative order. The spec requires it to be the final step.
- **R-48.4 Detach as held action.** Using `detach_pressed` (held) instead of `detach_just_pressed` (edge trigger) would cause repeated detach-attempts every frame, which is a no-op after the first but is semantically wrong. The parameter is `detach_just_pressed: bool` per SPEC-49.

### 4. Clarifying Questions

None. The exact logic is fully specified.

---

## Requirement SPEC-49: `simulate()` 8-Argument Signature

### 1. Spec Summary

- **Description:** The `simulate()` function in `movement_simulation.gd` is extended from 7 to 8 arguments. The new 7th positional argument is `detach_just_pressed: bool`, inserted between `wall_normal_x: float` (formerly the 6th argument) and `delta: float` (formerly the 6th, now the 8th argument). `delta` must remain the final parameter.

  The complete new signature is:
  ```gdscript
  func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float) -> MovementState:
  ```

  Every parameter must have an explicit GDScript type annotation. The return type annotation `-> MovementState` is required. No default parameter values are permitted on any argument.

- **Constraints:**
  - Parameter names must match exactly: `prior_state`, `input_axis`, `jump_pressed`, `jump_just_pressed`, `is_on_wall`, `wall_normal_x`, `detach_just_pressed`, `delta`. No abbreviations or renames.
  - Parameter types must match exactly: `MovementState`, `float`, `bool`, `bool`, `bool`, `float`, `bool`, `float`.
  - `delta` remains the last argument. Any implementation that places `detach_just_pressed` after `delta` is incorrect and will cause all call-site migrations to fail.
  - The function remains `func simulate(...)` with no `static` keyword. It is an instance method on `MovementSimulation`.
  - The return type annotation `-> MovementState` must be present.
  - The parameter `detach_just_pressed` represents a single-frame edge trigger: the caller passes `Input.is_action_just_pressed("detach")`. There is no `detach_pressed` (held) parameter; detach is not a held action.
  - `detach_just_pressed` has no effect on velocity, coyote state, jump state, or wall cling state. Its only effect is on `result.has_chunk` (via SPEC-48 logic).
- **Assumptions:** No assumptions. The exact signature is given by the execution plan.
- **Scope / Context:** Applies to `scripts/movement_simulation.gd`, function declaration line only. The change to the function body (the detach step logic) is specified by SPEC-48. This spec item covers only the signature declaration itself.

### 2. Acceptance Criteria

- **AC-49.1:** The function declaration in `movement_simulation.gd` reads exactly:
  ```gdscript
  func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float) -> MovementState:
  ```
  Whitespace differences (spaces vs. newlines between parameters) are acceptable; all other characters must match.
- **AC-49.2:** The `detach_just_pressed` parameter is the 7th positional argument (index 6, zero-based). A call passing `false` as the 7th argument (before `delta`) must compile and run without error.
- **AC-49.3:** `delta` is the 8th and final positional argument. A call passing a `float` as the 8th argument (for `delta`) must compile and run.
- **AC-49.4:** `godot --headless --check-only` produces zero diagnostics on `movement_simulation.gd` after the signature change.
- **AC-49.5:** Calling `simulate()` with exactly 8 arguments (in the order matching the new signature) succeeds. Calling it with 7 arguments produces a GDScript parse or runtime error (argument count mismatch). This confirms the signature change is in effect.
- **AC-49.6:** The SPEC comment block at the top of `movement_simulation.gd` is updated to include a line `#   SPEC-49 — simulate() 8-argument signature with detach_just_pressed: bool`.

### 3. Risk and Ambiguity Analysis

- **R-49.1 Positional argument order.** The most likely error is placing `detach_just_pressed` after `delta` instead of before it. This would compile and run but produce wrong behavior: callers passing `false, 0.016` would have `detach_just_pressed = 0.016` (type mismatch — GDScript may coerce float to bool; `0.016` is truthy). All call-site migrations must be verified against the exact positional order.
- **R-49.2 Missing return type annotation.** GDScript does not require `-> MovementState` but SPEC-53 NF-01 requires all variables and return types to be explicitly typed. Omitting it is a non-functional spec violation.
- **R-49.3 Default argument value.** Adding `detach_just_pressed: bool = false` as a default would silently allow callers to omit the argument, which prevents detection of missed call-site migrations. The spec requires no default values; all callers must pass the argument explicitly.

### 4. Clarifying Questions

None. The exact signature is given by the execution plan.

---

## Requirement SPEC-50: Call-Site Migration — Insert `false` Before `delta`

### 1. Spec Summary

- **Description:** Every existing call to `simulate()` in the codebase must be updated to pass `false` as the new 7th positional argument (`detach_just_pressed`) before the existing `delta` argument. No assertion values change in any existing test. Only the argument list length changes from 7 to 8. This follows the identical pattern established by SPEC-27 (adding `is_on_wall, wall_normal_x` — inserts `false, 0.0` before `delta`) and SPEC-35 (adding `jump_pressed, jump_just_pressed` — inserts `false, false` before prior parameters).

  The complete list of files requiring call-site migration is:
  1. `/Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd` — one call site in `_physics_process()` (Task 5 inserts placeholder `false`; Task 7 replaces with real input)
  2. `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation.gd`
  3. `/Users/jacobbrandt/workspace/blobert/tests/test_movement_simulation_adversarial.gd`
  4. `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation.gd`
  5. `/Users/jacobbrandt/workspace/blobert/tests/test_jump_simulation_adversarial.gd`
  6. `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation.gd`
  7. `/Users/jacobbrandt/workspace/blobert/tests/test_wall_cling_simulation_adversarial.gd`

  Note: `tests/test_camera_follow.gd` and `tests/test_camera_follow_adversarial.gd` do not call `simulate()` and require no changes.

- **Constraints:**
  - Every `simulate(` call across all seven files above must be updated. Missing even one call site will cause a GDScript argument-count error at runtime.
  - The new argument is `false` (the `bool` literal). It is inserted at position 7 (before `delta`). No other arguments move, are renamed, or have their values changed.
  - Assertion values (expected `velocity`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `is_on_floor`) in existing tests do not change. Only the simulate() call argument lists change.
  - The implementer must grep for `simulate(` across `scripts/` and `tests/` before declaring migration complete, to confirm no call sites are missed.
  - `tests/run_tests.gd` does not call `simulate()` directly; it orchestrates suite execution. It requires no changes for this migration (it will require changes for suite registration, handled in Task 8).
- **Assumptions:** `tests/test_camera_follow.gd` and `tests/test_camera_follow_adversarial.gd` do not call `simulate()`. This is confirmed by inspecting those files before writing the migration. If any additional test files calling `simulate()` exist that are not listed above, they must also be migrated.
- **Scope / Context:** Call-site migration only. No new tests are added in this task; no assertion values change. The only valid change per file is the insertion of `false` as the 7th argument in every `simulate()` call.

### 2. Acceptance Criteria

- **AC-50.1:** After migration, every call to `simulate()` in every file in the codebase passes exactly 8 arguments. Zero 7-argument (or fewer) calls to `simulate()` remain.
- **AC-50.2:** The 7th argument in every migrated call is the `bool` literal `false` (or, after Task 7 for `player_controller.gd`, the local variable `detach_just_pressed`).
- **AC-50.3:** `godot --headless --check-only` run against all seven migrated files produces zero diagnostics.
- **AC-50.4:** The full test suite (`godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd`) exits with code 0 after migration, confirming no assertion values were accidentally changed.
- **AC-50.5:** Grep for `simulate(` in `scripts/` and `tests/` returns only calls with 8 arguments. Example command: `rg "simulate\(" scripts/ tests/` — each matching line must have 8 comma-separated arguments between the outer parentheses.
- **AC-50.6:** `test_camera_follow.gd` and `test_camera_follow_adversarial.gd` are not modified (they contain no `simulate()` calls).

### 3. Risk and Ambiguity Analysis

- **R-50.1 Missed call site.** A multi-line `simulate(` call (where arguments span multiple lines) may be harder to find with a simple text search. The implementer must use `rg "simulate\("` (ripgrep) rather than a simple `grep`, and must manually verify each match.
- **R-50.2 Wrong position.** Inserting `false` as the 8th argument (after `delta`) rather than the 7th (before `delta`) compiles but produces wrong results: `delta = false` is a type mismatch. GDScript may silently coerce `false` to `0.0` for `delta`, breaking all frame-rate-dependent assertions.
- **R-50.3 Test files added after this spec was written.** If any new test file calling `simulate()` is created between this spec and the implementation, it must also be migrated. The grep verification step (AC-50.5) catches this.
- **R-50.4 player_controller.gd two-phase migration.** Task 5 inserts `false` as a placeholder; Task 7 replaces `false` with `detach_just_pressed`. Both phases produce valid 8-argument calls. Task 5 must not leave a 7-argument call; Task 7 must not accidentally add a 9th argument.

### 4. Clarifying Questions

None. The migration pattern is identical to SPEC-27 and SPEC-35 and is fully specified.

---

## Requirement SPEC-51: `detach` Input Action in `project.godot`

### 1. Spec Summary

- **Description:** A new input action named `"detach"` is added to the `[input]` section of `/Users/jacobbrandt/workspace/blobert/project.godot`. The action must be bound to at minimum the physical E key (physical_keycode 69). An optional second binding to the left mouse button (InputEventMouseButton, button_index = 1) may also be added but is not required. The action is read by `player_controller.gd` using `Input.is_action_just_pressed("detach")`.

  The exact `project.godot` entry format follows the established pattern of the existing `jump` action in the same file. The action name must be lowercase with no spaces: `"detach"` (not `"Detach"`, not `"DETACH"`, not `"detach_chunk"`).

- **Constraints:**
  - The action name in `project.godot` must be exactly `detach` (the string value used in quotes in the `[input]` section key).
  - The E key binding must use `physical_keycode = 69`. This is the physical key code for the E key in Godot 4's `InputEventKey` format.
  - The `[input]` section entry must follow the exact serialization format Godot uses for input actions. The implementer must read the existing `[input]` section of `project.godot` before writing the new entry, and must match the format exactly (including `InputEventKey` wrapper, `device = -1` for any device, `keycode = 0` alongside `physical_keycode`). Deviating from the format may cause Godot to silently ignore the action.
  - If a left mouse button binding is added, the entry must use `InputEventMouseButton` with `button_index = 1` and follow the same format as any existing mouse bindings in the file (or, if none exist, the standard Godot 4 serialization format for mouse buttons).
  - Adding the `detach` action must not remove, rename, or modify any existing input actions (`move_left`, `move_right`, `jump`, or any others).
- **Assumptions:** The `project.godot` file already has a `[input]` section with at least the `jump` action defined, which serves as the format reference. This is confirmed by the existing codebase.
- **Scope / Context:** Applies exclusively to `/Users/jacobbrandt/workspace/blobert/project.godot`. No other file is changed by this spec item. The action name `"detach"` must match exactly what `player_controller.gd` passes to `Input.is_action_just_pressed()`.

### 2. Acceptance Criteria

- **AC-51.1:** `project.godot` contains an `[input]` section entry with key `detach` and at least one binding to `physical_keycode = 69` (E key).
- **AC-51.2:** The action name is exactly `detach` (lowercase, no spaces, no underscores, no extra characters).
- **AC-51.3:** `godot --headless --check-only` run against the project produces zero diagnostics after this change.
- **AC-51.4:** The Godot editor (when opened) shows the `detach` action in the Input Map under Project Settings with at least one E key binding.
- **AC-51.5:** No existing input action (`move_left`, `move_right`, `jump`) is removed or modified.
- **AC-51.6:** The format of the new `detach` entry in `project.godot` matches the format of the existing `jump` entry (same wrapper types, same field names, same field order). Example: if `jump` uses `InputEventKey "{ \"device\": -1, \"window_id\": 0, \"alt_pressed\": false, \"shift_pressed\": false, \"ctrl_pressed\": false, \"meta_pressed\": false, \"pressed\": false, \"keycode\": 0, \"physical_keycode\": 32, ... }"`, then `detach` must use the identical structure with `physical_keycode = 69`.

### 3. Risk and Ambiguity Analysis

- **R-51.1 Format mismatch.** `project.godot` uses a specific Godot resource serialization format for input actions. Hand-editing it incorrectly (e.g., wrong indentation, missing fields, wrong field order) may cause Godot to silently discard the action or produce a parse warning. The implementer must read the existing `jump` entry first and mirror its format exactly.
- **R-51.2 Keycode vs. physical_keycode.** Godot 4 distinguishes `keycode` (layout-dependent) from `physical_keycode` (physical key position). The spec requires `physical_keycode = 69`. An implementation using only `keycode = 69` would bind to a layout-specific E key rather than the physical E position. Both should be set (with `keycode = 0` and `physical_keycode = 69`) following the established pattern.
- **R-51.3 Action name string quoting.** In `project.godot`, action names are the keys on the left side of `=` in the `[input]` section. The key must be `detach` without quotes in the file (Godot's `.ini`-style serialization uses unquoted keys). Quoting it incorrectly would create an action with a different name.
- **R-51.4 Mouse button binding is optional.** The spec allows but does not require the mouse button binding. Test agents must not assert the presence of a mouse button binding. The E key binding is the only mandatory binding.

### 4. Clarifying Questions

None. The E key physical_keycode (69) and action name (`detach`) are confirmed by the execution plan.

---

## Requirement SPEC-52: Engine Integration — `player_controller.gd` Changes and Chunk Spawn

### 1. Spec Summary

- **Description:** `player_controller.gd` must be modified to wire the detach mechanic into the physics loop. The changes are:

  1. A new member variable `var _chunk_node: RigidBody2D = null` is declared (after the existing member variables).
  2. In `_physics_process()` Step 1 (input reading), a new local variable `var detach_just_pressed: bool = Input.is_action_just_pressed("detach")` is read immediately after the existing jump input reads.
  3. The `simulate()` call is updated to pass `detach_just_pressed` as the 7th argument (before `delta`).
  4. After `move_and_slide()`, `next_state.has_chunk` is copied back to `_current_state.has_chunk`, following the same copy-back pattern as `coyote_timer`, `jump_consumed`, `is_wall_clinging`, and `cling_timer`.
  5. After the copy-backs, a transition check determines whether the chunk was just detached this frame. The condition is: `prior_state.has_chunk == true AND next_state.has_chunk == false` (i.e., `has_chunk` transitioned from `true` to `false` this frame). When this condition is true:
     - Load `scenes/chunk.tscn` via `preload("res://scenes/chunk.tscn")` (or a constant declared at the top of the file).
     - Instantiate the scene: `var chunk_instance: RigidBody2D = preload("res://scenes/chunk.tscn").instantiate()`.
     - Set `chunk_instance.global_position = self.global_position`.
     - Add the instance to the scene as a sibling of the player: `get_parent().add_child(chunk_instance)`.
     - Store the reference: `_chunk_node = chunk_instance`.
  6. `_chunk_node` must be null-safe checked before any access (any code that reads or calls methods on `_chunk_node` must be guarded with `if _chunk_node != null`).

  The `scenes/chunk.tscn` scene (specified below) must also be created as part of this ticket's implementation.

  `scenes/chunk.tscn` specification:
  - Root node type: `RigidBody2D` with node name `Chunk`.
  - Root node property: `freeze = true` (the chunk does not move under physics simulation; it is a static marker in M1).
  - One child node: `CollisionShape2D` with a `CircleShape2D` resource, radius `8.0`.
  - No script attached to the root node.
  - The scene file format follows the existing `.tscn` format used by `scenes/test_movement.tscn`.

- **Constraints:**
  - `_chunk_node` is typed `RigidBody2D` (not `Node` or untyped) per SPEC-53 NF-01.
  - `_chunk_node` defaults to `null`.
  - The chunk node is added as a child of `get_parent()` (the player's parent node in the scene tree), NOT as a child of `self` (the player). Adding it as a child of `self` would make it move with the player.
  - The chunk's `global_position` is set to the player's `global_position` at the moment of detach — the current physics frame.
  - No movement math is added to `player_controller.gd`. The transition detection (`prior_state.has_chunk == true AND next_state.has_chunk == false`) is a state comparison, not movement math.
  - The `prior_state` used in the transition check is the `_current_state` before the `simulate()` call (i.e., the `has_chunk` value from the frame's start, not the value after copying `next_state.has_chunk` back). The implementer must capture `var prior_had_chunk: bool = _current_state.has_chunk` before overwriting `_current_state.has_chunk`, or perform the transition check before the copy-back.
  - The `preload` for `chunk.tscn` may be declared as a constant at the top of `player_controller.gd` (following the `MovementSimulation` preload pattern) or inline at the spawn site. Both are acceptable.
  - `chunk.tscn` root must be `RigidBody2D`, not `Node2D`, `CharacterBody2D`, or `Area2D`.
  - `freeze = true` must be set on the `RigidBody2D` root in the scene file (not applied in code), so the chunk does not move immediately upon spawning.
- **Assumptions:**
  - A5.1: No chunk-removal logic (recalling the chunk) is implemented in this ticket. `_chunk_node` is set once (on detach) and not cleared. Clearing `_chunk_node` and removing the node from the tree is the responsibility of M1-007 (recall).
  - A5.2: The player starts each play session with `has_chunk = true` (from the `MovementState` default). The transition check on the very first frame (before any detach) evaluates `prior.has_chunk == true AND next.has_chunk == false`; since no detach occurs on the first frame, the condition is false and no chunk is spawned.
  - A5.3: If the player presses detach when `has_chunk` is already `false` (e.g., after already detaching), the simulation produces `next_state.has_chunk = false` (carry-forward) and `prior_state.has_chunk` is also `false`; the transition condition is false, so no duplicate chunk is spawned.
- **Scope / Context:** Applies to `scripts/player_controller.gd` (modified) and `scenes/chunk.tscn` (new). Does not affect `movement_simulation.gd` (that file's changes are covered by SPEC-46 through SPEC-49).

### 2. Acceptance Criteria

- **AC-52.1 Member variable declaration:** `player_controller.gd` contains `var _chunk_node: RigidBody2D = null` as a class-level member variable (not a local variable inside a function).
- **AC-52.2 Input read:** Inside `_physics_process()`, the line `var detach_just_pressed: bool = Input.is_action_just_pressed("detach")` appears in Step 1 (input reading), after the existing `jump_pressed` and `jump_just_pressed` reads, before the `_current_state.is_on_floor` update.
- **AC-52.3 simulate() call updated:** The `simulate()` call in `_physics_process()` passes `detach_just_pressed` as the 7th argument (before `delta`). The call passes 8 arguments total.
- **AC-52.4 Copy-back:** After `move_and_slide()`, the line `_current_state.has_chunk = next_state.has_chunk` appears in the copy-back section, alongside the existing `_current_state.coyote_timer`, `_current_state.jump_consumed`, `_current_state.is_wall_clinging`, and `_current_state.cling_timer` copy-backs.
- **AC-52.5 Transition condition:** The chunk spawn logic fires when and only when `prior_state.has_chunk` was `true` at the start of the frame AND `next_state.has_chunk` is `false`. Example: on the first frame where detach fires, the chunk is spawned. On every subsequent frame (where `prior_state.has_chunk` is already `false`), the chunk is not re-spawned.
- **AC-52.6 Spawn position:** The spawned chunk's `global_position` equals the player's `global_position` at the moment of the spawn call.
- **AC-52.7 Spawn parent:** The chunk is added via `get_parent().add_child(chunk_instance)` — it is a sibling of the player, not a child. (A child would move with the player.)
- **AC-52.8 Reference stored:** After spawning, `_chunk_node` holds a reference to the spawned `RigidBody2D` instance (not null).
- **AC-52.9 Null safety:** Any access to `_chunk_node`'s properties or methods (other than assignment) is guarded by `if _chunk_node != null`.
- **AC-52.10 No duplicate spawn:** Pressing detach when `has_chunk` is already `false` does not spawn a second chunk. (Because `prior_state.has_chunk` will be `false` and the transition condition will be false.)
- **AC-52.11 chunk.tscn root type:** `scenes/chunk.tscn` has a `RigidBody2D` as its root node with node name `Chunk`.
- **AC-52.12 chunk.tscn freeze:** The `RigidBody2D` root in `scenes/chunk.tscn` has `freeze = true` set in the scene file.
- **AC-52.13 chunk.tscn collision shape:** `scenes/chunk.tscn` contains a `CollisionShape2D` child with a `CircleShape2D` resource whose `radius` property is `8.0`.
- **AC-52.14 Static QA:** `godot --headless --check-only` produces zero diagnostics on `player_controller.gd` after all changes.

### 3. Risk and Ambiguity Analysis

- **R-52.1 Chunk added to self vs. get_parent().** The most consequential implementation error is `self.add_child(chunk_instance)` instead of `get_parent().add_child(chunk_instance)`. A child of the player moves with the player (inherits transform). This would make the "detached" chunk visually stuck to the player. The spec explicitly requires `get_parent().add_child()`.
- **R-52.2 Transition check order vs. copy-back order.** The transition check must compare `_current_state.has_chunk` (the prior value) against `next_state.has_chunk`. If the copy-back `_current_state.has_chunk = next_state.has_chunk` runs before the transition check, the prior value is overwritten and the condition `prior.has_chunk != next.has_chunk` can never be true. The implementer must either perform the check before the copy-back or save `prior_had_chunk` before the copy-back.
- **R-52.3 Duplicate chunk on repeated detach press.** If the transition condition is written as `next_state.has_chunk == false` (without checking the prior value), it will fire every frame after detach — spawning many chunks. Both conditions (`prior == true AND next == false`) are required.
- **R-52.4 chunk.tscn format.** Writing `chunk.tscn` by hand requires exact adherence to Godot's `.tscn` serialization format. The implementer must read `scenes/test_movement.tscn` as a format reference before writing. An invalid format causes Godot to fail to load the scene, crashing the spawn call.
- **R-52.5 radius value.** The spec requires radius `8.0`. The planner context mentions both `10` and `8.0` in different sections. The authoritative value in the execution plan (Task 7 output column) is `8.0`. This spec uses `8.0`.
- **R-52.6 freeze property name.** In Godot 4, the `RigidBody2D` freeze property is `freeze` (not `freeze_mode` or `sleeping`). In `.tscn` format it is serialized as `freeze = true`. The implementer must verify the exact property name.
- **R-52.7 No movement math.** The spawn logic (load scene, set position, add child) is presentation code, not movement math. This is permitted in `player_controller.gd`. However, the implementer must not add any velocity calculation, impulse formula, or timer logic to the controller as part of this change.

### 4. Clarifying Questions

None. The execution plan specifies all required behavior. The radius discrepancy (10 vs. 8.0) is resolved in favor of 8.0 as documented in this spec; this resolution is logged in CHECKPOINTS.md.

---

## Requirement SPEC-53: Non-Functional Requirements

### 1. Spec Summary

- **Description:** All code changes introduced by this ticket must comply with the following non-functional requirements. These requirements apply across all modified and new files: `movement_simulation.gd`, `player_controller.gd`, `chunk.tscn`, and all new or migrated test files.

  - **NF-01 Explicit types on all new variables:** Every new `var` declaration introduced by this ticket (in any `.gd` file) must have an explicit GDScript type annotation. Examples: `var has_chunk: bool = true`, `var detach_just_pressed: bool`, `var detach_eligible: bool`, `var _chunk_node: RigidBody2D = null`. Untyped declarations (`var x = ...`) are not permitted for any new variable.
  - **NF-02 Explicit defaults on all new member variables:** Every new class-level member variable must have an explicit default value in its declaration. `var has_chunk: bool = true` and `var _chunk_node: RigidBody2D = null` both satisfy this. A declaration like `var _chunk_node: RigidBody2D` (no default) does not.
  - **NF-03 No movement math in player_controller.gd:** No velocity formula, impulse calculation, or physics arithmetic may be added to `player_controller.gd` as part of this ticket. The transition check (`prior_state.has_chunk == true AND next_state.has_chunk == false`) is a state comparison, not movement math. The spawn call (`chunk_instance.global_position = self.global_position`) is position assignment, not movement math. Both are permitted.
  - **NF-04 simulate() must not reference engine nodes or singletons:** The `simulate()` function and the `MovementSimulation` class as a whole must not call `Input`, `ProjectSettings`, `get_tree()`, `get_node()`, `preload()`, or any other engine API. `detach_just_pressed` is a plain `bool` parameter passed in by the caller; the function never calls `Input` directly. This constraint was already satisfied for all prior parameters and must remain satisfied after SPEC-48 and SPEC-49 additions.
  - **NF-05 No dead code:** Every new field and parameter introduced by this ticket must be used in at least one code path in the modified files. Specifically: `has_chunk` is used in `simulate()` (read from `prior_state`, written to `result`) and in `player_controller.gd` (copied back, used in transition check); `detach_just_pressed` is used in `simulate()` (read in detach step); `_chunk_node` is used in `player_controller.gd` (assigned on spawn, null-checked before access).
  - **NF-06 Zero godot --headless --check-only diagnostics:** Running `godot --headless --check-only` against any modified `.gd` file must produce zero errors, zero warnings.

- **Constraints:**
  - NF-01 through NF-06 apply retroactively to all new lines of code in all files touched by this ticket.
  - Violation of NF-06 is a hard blocker: the ticket must not advance to STATIC_QA stage with any open diagnostic.
  - NF-04 is architectural: it preserves headless testability of `movement_simulation.gd`. Any engine API call in `movement_simulation.gd` would require a running Godot project to test and would break all existing headless tests.
- **Assumptions:** No assumptions. These non-functional requirements are inherited from the project-wide coding standards established in SPEC-1 through SPEC-14 and carried forward by all subsequent specs.
- **Scope / Context:** Applies to all `.gd` files modified or created by this ticket. Does not apply to `chunk.tscn` (a scene file, not a GDScript file), except that the scene file itself must be loadable without errors.

### 2. Acceptance Criteria

- **AC-53.1 NF-01 — Typed variables:** A static scan of all new `var` declarations in modified `.gd` files shows zero untyped declarations. Each new `var` has `: <Type>` before the `=` or end of the declaration.
- **AC-53.2 NF-02 — Default values:** Each new class-level `var` declaration has an explicit `= <value>` initializer. Local variables inside functions may be initialized on assignment (e.g., `var x: bool = some_call()`) and are also considered to satisfy this requirement.
- **AC-53.3 NF-03 — No movement math in controller:** A review of all new lines added to `player_controller.gd` shows zero arithmetic operators (`+`, `-`, `*`, `/`, `sqrt`, `abs`, `move_toward`, `lerp`) applied to velocity or timer values. Position assignment (`chunk_instance.global_position = self.global_position`) does not involve arithmetic and is permitted.
- **AC-53.4 NF-04 — No engine calls in simulate():** A scan of `movement_simulation.gd` shows zero calls to `Input`, `ProjectSettings`, `get_tree`, `get_node`, `preload`, `load`, or any other engine singleton or scene-tree API. The entire file remains headlessly instantiable without a running Godot project.
- **AC-53.5 NF-05 — No dead code:** All of the following are used in at least one reachable code path: `MovementState.has_chunk`, `simulate()` parameter `detach_just_pressed`, `PlayerController._chunk_node`. None is declared but never read or written beyond its own declaration.
- **AC-53.6 NF-06 — Zero diagnostics:** `godot --headless --check-only` run on `movement_simulation.gd`, `player_controller.gd`, and all new/migrated test files produces zero output (exit code 0, no warnings, no errors).

### 3. Risk and Ambiguity Analysis

- **R-53.1 Type inference vs. explicit annotation.** GDScript infers types from literals (e.g., `var x = true` infers `bool`). The spec requires explicit annotations. An automated linter may pass on inferred types; a manual review step is needed to catch missing annotations.
- **R-53.2 NF-03 interpretation.** "No movement math" means no physics formulas. Setting `chunk_instance.global_position = self.global_position` is position assignment and is explicitly permitted. An over-strict interpretation that blocks all arithmetic in the controller would prevent legitimate position math in future tickets; this spec clarifies it applies only to velocity/timer/impulse arithmetic.
- **R-53.3 NF-04 engine call detection.** The `preload("res://scenes/chunk.tscn")` call in `player_controller.gd` is an engine API call. It is correct in `player_controller.gd` (which is a Node subclass, not the pure simulation). NF-04 prohibits engine calls in `movement_simulation.gd` only. `player_controller.gd` may freely use engine APIs.
- **R-53.4 godot binary path.** On the development machine, `godot` may not be on PATH. Per CHECKPOINTS.md [M1-001], the binary path is `/Applications/Godot.app/Contents/MacOS/Godot`. Agents running the `--check-only` validation must use the full path if `godot` is not found on PATH.

### 4. Clarifying Questions

None. These requirements are fully inherited from project-wide standards.

---

## Cross-Reference: Normative Order of Operations for `simulate()` after SPEC-48

The complete 17-step order of operations for `simulate()` after all SPEC-46 through SPEC-53 changes are applied:

```
Step  1: Compute effective_delta = max(0.0, delta)
Step  2: Sanitize input_axis (NaN → 0.0; clamp to ±1.0)
Step  3: Sanitize wall_normal_x (NaN → 0.0; clamp to ±1.0)
Step  4: Compute pressing_toward_wall = (safe_axis * safe_wall_normal_x) < 0.0
Step  5: Allocate result: MovementState = MovementState.new()
Step  6: Coyote timer update
Step  7: jump_consumed carry-forward / landing reset
Step  8: Cling eligibility evaluation
Step  9: Cling state update (is_wall_clinging, cling_timer)
Step 10: Wall jump eligibility evaluation
Step 11: Regular jump eligibility evaluation
Step 12: Apply jump path (regular > wall > none)
Step 13: Horizontal velocity (Cases 1–4; skipped when wall jump fired)
Step 14: Gravity (reduced if is_wall_clinging)
Step 15: Jump cut
Step 16: is_on_floor pass-through
Step 17: Detach step (NEW — SPEC-48)
         detach_eligible = detach_just_pressed AND prior_state.has_chunk
         if detach_eligible: result.has_chunk = false
         else: result.has_chunk = prior_state.has_chunk
```

Note: The prior comment block in `movement_simulation.gd` documents 15 steps (labeled 1–15 in the block, with step 16 visible in code but unlabeled in the header comment). After this ticket, the header comment must document all 17 steps.

---

## File Change Summary

| File | Change Type | SPEC Coverage |
|------|-------------|---------------|
| `scripts/movement_simulation.gd` | Modified | SPEC-46, SPEC-47, SPEC-48, SPEC-49 |
| `scripts/player_controller.gd` | Modified | SPEC-50 (migration), SPEC-52 |
| `project.godot` | Modified | SPEC-51 |
| `scenes/chunk.tscn` | New | SPEC-52 |
| `tests/test_chunk_detach_simulation.gd` | New | SPEC-46 through SPEC-53 (headless-testable ACs) |
| `tests/test_chunk_detach_simulation_adversarial.gd` | New | SPEC-48 adversarial cases |
| `tests/run_tests.gd` | Updated | Registration of new suites |
| `tests/test_movement_simulation.gd` | Migration only | SPEC-50 |
| `tests/test_movement_simulation_adversarial.gd` | Migration only | SPEC-50 |
| `tests/test_jump_simulation.gd` | Migration only | SPEC-50 |
| `tests/test_jump_simulation_adversarial.gd` | Migration only | SPEC-50 |
| `tests/test_wall_cling_simulation.gd` | Migration only | SPEC-50 |
| `tests/test_wall_cling_simulation_adversarial.gd` | Migration only | SPEC-50 |
