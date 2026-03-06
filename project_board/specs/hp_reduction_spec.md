# HP Reduction on Detach Simulation Specification
# M1-006 — hp_reduction_on_detach.md
# SPEC-54 through SPEC-61
#
# Prerequisite specs: SPEC-1 through SPEC-53
#   SPEC-1  through SPEC-14: movement_controller.md / M1-001
#   SPEC-15 through SPEC-24: jump_tuning.md / M1-002
#   SPEC-25 through SPEC-36: wall_cling.md / M1-003
#   SPEC-37 through SPEC-45: basic_camera_follow.md / M1-004
#   SPEC-46 through SPEC-53: chunk_detach.md / M1-005
# Continuing numbering from SPEC-53.
#
# Files affected:
#   /Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd (modified)
#   /Users/jacobbrandt/workspace/blobert/scripts/player_controller.gd (modified)
#   /Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd (updated)
#
# Files NOT affected by this ticket:
#   /Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation.gd
#   /Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation_adversarial.gd
#   (Existing call-sites require no migration: current_hp has a default value; see SPEC-60)

---

## Requirement SPEC-54: `MovementState.current_hp` Field Declaration

### 1. Spec Summary

- **Description:** The `MovementState` inner class inside `movement_simulation.gd` gains a new field `current_hp: float` with a default initializer of `100.0`. This field is the 8th field declared in the class body, immediately after `has_chunk: bool = true` (the 7th field). The field represents the player's current hit points at the instant captured by this state object. Its value is determined by the simulation each frame and is carried forward or reduced according to SPEC-56 and SPEC-57.

- **Constraints:**
  1. The initializer must be the concrete float literal `100.0`. It must NOT be a computed expression, a reference to `max_hp`, or any other symbolic value.
  2. The type annotation must be `float` (not `int`, not `Variant`).
  3. The field must be declared as a plain `var` (no `@export`, no `@onready`, no `const`).
  4. The field must be the 8th and final field in `MovementState` at the time of this ticket; no other new fields are added to `MovementState` in M1-006.
  5. The declaration must be placed after `var has_chunk: bool = true` and before the end of the `MovementState` class body.

- **Assumptions:**
  1. `MovementState` is a GDScript inner class (`class MovementState:`) with no parent class other than the implicit `RefCounted`. It has no access to `MovementSimulation` member variables, including `max_hp`.
  2. The player starts every new session at full health; therefore, `100.0` is a suitable default matching the intended `max_hp` default.
  3. If the `max_hp` default is ever changed in `MovementSimulation`, the `current_hp` default in `MovementState` must be manually updated by the developer. This coupling is accepted and must be documented in the code comment block.

- **Scope / Context:** Applies exclusively to the `MovementState` inner class declaration inside `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`. No other file declares or initializes `current_hp` as part of this requirement.

### 2. Acceptance Criteria

- **AC-54.1:** The `MovementState` class body contains exactly the following field declaration (verbatim type, name, and initializer): `var current_hp: float = 100.0`
- **AC-54.2:** `current_hp` is the 8th field in the class body. The fields appear in this exact order: `velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`, `current_hp`.
- **AC-54.3:** `MovementSimulation.MovementState.new()` called with no arguments produces an instance where `current_hp == 100.0`. This verifies the default initializer is active and requires no migration of existing call-sites.
- **AC-54.4:** The `current_hp` field is readable and writable from outside the class. Example: `var s := MovementSimulation.MovementState.new(); s.current_hp = 75.0; assert(s.current_hp == 75.0)` succeeds.
- **AC-54.5:** Setting `current_hp` on a `MovementState` instance does not affect any other field on the same instance. Example: after `s.current_hp = 50.0`, `s.velocity`, `s.is_on_floor`, `s.coyote_timer`, `s.jump_consumed`, `s.is_wall_clinging`, `s.cling_timer`, and `s.has_chunk` all retain their initialized or previously assigned values.
- **AC-54.6:** The header comment block of `MovementState` in `movement_simulation.gd` is updated to include `# AC-54.1: current_hp: float = 100.0` (or equivalent annotation style matching the existing comment format), documenting that the default is a literal and not a reference to `max_hp`.

### 3. Risk & Ambiguity Analysis

- **Risk R-54.1 — Default coupling:** The literal `100.0` in `MovementState` and the default `100.0` of `max_hp` in `MovementSimulation` will silently diverge if one is changed without the other. Impact: a freshly constructed state could start at a value different from the actual maximum health. Mitigation: Document the coupling explicitly in the code comment (AC-54.6).
- **Risk R-54.2 — Field ordering:** If a future ticket inserts a new field between `has_chunk` and `current_hp`, the ordering invariant stated in AC-54.2 changes. This does not break functionality but would make AC-54.2 stale. Mitigation: AC-54.2 is scoped to M1-006 only.
- **Risk R-54.3 — Type collision:** A `float` field with a `100.0` literal is unambiguous in GDScript, but tools that inspect `MovementState` via reflection might conflate `current_hp` with an integer type if the literal is accidentally written `100` (without decimal). The literal must include a decimal point.

### 4. Clarifying Questions

None. All design decisions are resolved per CHECKPOINTS.md (M1-006 Planner — current_hp default value in MovementState constructor). No further clarification is required.

---

## Requirement SPEC-55: `MovementSimulation` Config Vars (`max_hp`, `hp_cost_per_detach`, `min_hp`)

### 1. Spec Summary

- **Description:** Three new configuration variables are added to the `MovementSimulation` class body, in the configuration parameters section. They are declared after `var wall_jump_horizontal_speed: float = 180.0` (the last pre-existing config var). Each is a plain `var` with a `float` type annotation and a concrete float literal default. Each must have a doc comment in the same style as existing config vars (double-hash `##` prefix).

  The three variables and their defaults are:
  - `var max_hp: float = 100.0`
  - `var hp_cost_per_detach: float = 25.0`
  - `var min_hp: float = 0.0`

- **Constraints:**
  1. All three must be `float` (not `int`, not `Variant`).
  2. All three must be plain `var` declarations (no `@export`, no `const`).
  3. They must appear together, in the order listed above, immediately after `var wall_jump_horizontal_speed: float = 180.0` in the config section.
  4. `max_hp` is informational only within this ticket's scope. `simulate()` does not enforce `max_hp` as an upper clamp on `current_hp` in M1-006. `max_hp` is provided for future use by UI systems, other game logic, and M1-007 (recall/regen), which may use it to cap HP restoration.
  5. `hp_cost_per_detach` is the amount subtracted from `prior_state.current_hp` on each detach frame (see SPEC-56). It must be a non-negative value for intended behavior; the spec does not prohibit a value of `0.0` (zero cost is valid — detach fires but HP does not change). Negative values produce HP gain on detach; that is undefined behavior for this ticket but is not blocked by the implementation.
  6. `min_hp` is the floor applied at the detach-reduction site (see SPEC-56 and SPEC-58). Values at or below `0.0` are valid. A negative `min_hp` allows `current_hp` to go below zero.

- **Assumptions:**
  1. The config section is defined by convention (not by any GDScript keyword). The three new vars are placed immediately below the last existing config var to maintain the grouped structure.
  2. `player_controller.gd` does not need new `@export` vars for `max_hp`, `hp_cost_per_detach`, or `min_hp` in this ticket. Inspector exposure is out of scope for M1-006.

- **Scope / Context:** Applies exclusively to the `MovementSimulation` class declaration in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`. The config comment block header referencing the AC ranges must also be updated to include the new AC range `AC-55.1 through AC-55.6`.

### 2. Acceptance Criteria

- **AC-55.1:** `MovementSimulation` has a field `max_hp` of type `float` with default value `100.0`. Verified by: `var sim := MovementSimulation.new(); assert(sim.max_hp == 100.0)`.
- **AC-55.2:** `MovementSimulation` has a field `hp_cost_per_detach` of type `float` with default value `25.0`. Verified by: `var sim := MovementSimulation.new(); assert(sim.hp_cost_per_detach == 25.0)`.
- **AC-55.3:** `MovementSimulation` has a field `min_hp` of type `float` with default value `0.0`. Verified by: `var sim := MovementSimulation.new(); assert(sim.min_hp == 0.0)`.
- **AC-55.4:** All three fields are independently mutable. After assigning `sim.max_hp = 200.0`, `sim.hp_cost_per_detach = 10.0`, `sim.min_hp = -5.0`, each field returns the assigned value independently of the others.
- **AC-55.5:** `max_hp` is not read anywhere inside `simulate()` in this ticket. The field exists on the class but the simulation body makes no reference to it for any clamping, comparison, or computation.
- **AC-55.6:** Each of the three vars has a doc comment (using `##` style matching existing config vars) that accurately describes its purpose and scope. The `max_hp` doc comment must note "informational only — not enforced as an upper clamp in simulate() for this ticket." The `hp_cost_per_detach` doc comment must note "subtracted from current_hp on each detach frame." The `min_hp` doc comment must note "floor applied via max() clamp at the detach reduction site only."

### 3. Risk & Ambiguity Analysis

- **Risk R-55.1 — max_hp not enforced:** A future implementer might assume `current_hp <= max_hp` always holds because `max_hp` is a config var on the same class. If a future ticket (e.g., M1-007) restores HP without clamping to `max_hp`, `current_hp` could exceed it. This is not a bug in M1-006 but could cause confusion. Mitigation: AC-55.5 and the doc comment in AC-55.6 explicitly state that `max_hp` is not enforced here.
- **Risk R-55.2 — Negative hp_cost_per_detach:** A negative `hp_cost_per_detach` causes the formula in SPEC-56 to increase `current_hp` on detach. This is not intended behavior but is not an error the spec prohibits. Mitigation: noted as undefined behavior in the Constraints section.
- **Risk R-55.3 — Negative min_hp:** A negative `min_hp` (e.g., `-10.0`) is explicitly permitted (see adversarial test case 13 in Task 3). The floor is wherever `min_hp` is set; there is no hard zero. This is a deliberate design choice and is not an error.

### 4. Clarifying Questions

None. All design decisions are resolved per CHECKPOINTS.md M1-006 entries. No further clarification is required.

---

## Requirement SPEC-56: `simulate()` Step 18 — HP Reduction Formula and Order of Operations

### 1. Spec Summary

- **Description:** `simulate()` gains a new step 18 that is appended immediately after step 17 (chunk detach, SPEC-48) and immediately before `return result`. Step 18 reads the `detach_eligible` local variable produced in step 17 (without re-evaluating the condition) and either reduces `result.current_hp` or carries it forward unchanged.

  The normative description of step 18:
  ```
  18. HP reduction (SPEC-56):
        if detach_eligible (from step 17):
            result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)
        else:
            result.current_hp = prior_state.current_hp
      Reads:  detach_eligible (local var from step 17), prior_state.current_hp, min_hp, hp_cost_per_detach
      Writes: result.current_hp only — no other fields affected
  ```

  The exact formula when detach fires:
  ```
  result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)
  ```

  The `max()` function here is GDScript's built-in `max(a, b)` which returns the larger of two floats. When `prior_state.current_hp - hp_cost_per_detach` is less than `min_hp`, the result is clamped to `min_hp`. When the subtraction result is greater than or equal to `min_hp`, the result is the subtracted value unchanged.

- **Constraints:**
  1. Step 18 must be placed after step 17 (`var detach_eligible: bool = ...` and the `if detach_eligible` / `else` block writing `result.has_chunk`) and before `return result`.
  2. Step 18 must reuse the local variable `detach_eligible` that was computed in step 17. The condition `detach_just_pressed and prior_state.has_chunk` must NOT be re-evaluated independently in step 18.
  3. The formula reads `prior_state.current_hp` (the value entering this frame), not `result.current_hp` (which is not yet set on the detach path at this point, and is meaningless on the non-detach path).
  4. The formula reads `min_hp` from the `MovementSimulation` instance (the config var defined in SPEC-55), not from any local variable or argument.
  5. The formula reads `hp_cost_per_detach` from the `MovementSimulation` instance (the config var defined in SPEC-55), not from any local variable or argument.
  6. Step 18 writes only `result.current_hp`. It does not read or write `result.velocity`, `result.is_on_floor`, `result.coyote_timer`, `result.jump_consumed`, `result.is_wall_clinging`, `result.cling_timer`, or `result.has_chunk`.
  7. Step 18 does not read or write `prior_state.velocity`, `prior_state.is_on_floor`, `prior_state.coyote_timer`, `prior_state.jump_consumed`, `prior_state.is_wall_clinging`, `prior_state.cling_timer`, or `prior_state.has_chunk` (beyond what is already captured in `detach_eligible` from step 17).
  8. The normative order-of-operations comment block at the top of `simulate()` must be updated to list 18 steps, with step 18 described in the same style as step 17.
  9. The spec coverage comment block at the top of `movement_simulation.gd` must be updated to include SPEC-54 through SPEC-59 (see SPEC-59 for the full set).

- **Assumptions:**
  1. `detach_eligible` is a named local variable (`var detach_eligible: bool = ...`) in the `simulate()` function body, introduced by step 17. It remains in scope for step 18 because both steps are co-located in the same `simulate()` function body.
  2. GDScript's `max()` built-in accepts two `float` arguments and returns a `float`. There is no risk of integer truncation.
  3. `simulate()` is a single function with no early returns between step 17 and `return result`. Any future refactor that introduces an early return after step 17 but before `return result` could bypass step 18 and is explicitly prohibited while this spec is in effect.

- **Scope / Context:** Applies to the `simulate()` function body in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`. The step 18 block must appear between the closing `else` branch of step 17 and the `return result` statement. The `simulate()` function signature does not change (see SPEC-59).

### 2. Acceptance Criteria

- **AC-56.1:** When `detach_eligible` is `true` (i.e., `prior_state.has_chunk == true` and `detach_just_pressed == true`), `result.current_hp` equals `max(sim.min_hp, prior_state.current_hp - sim.hp_cost_per_detach)` using the values of those fields at the time of the call.
  - Example: `prior_state.current_hp = 100.0`, `hp_cost_per_detach = 25.0`, `min_hp = 0.0` → `result.current_hp == 75.0`.
  - Example: `prior_state.current_hp = 10.0`, `hp_cost_per_detach = 25.0`, `min_hp = 0.0` → `result.current_hp == 0.0` (clamped).
- **AC-56.2:** When `detach_eligible` is `false` (either `prior_state.has_chunk == false` or `detach_just_pressed == false` or both), `result.current_hp` equals `prior_state.current_hp` exactly (plain carry-forward, no transformation). See SPEC-57 for the full carry-forward spec.
- **AC-56.3:** Step 18 fires on the same frame as step 17 (detach). A single `simulate()` call with `detach_just_pressed=true` and `prior_state.has_chunk=true` simultaneously produces `result.has_chunk == false` (step 17) AND `result.current_hp == max(min_hp, prior_state.current_hp - hp_cost_per_detach)` (step 18).
- **AC-56.4:** `result.current_hp` is not modified by any step other than step 18. All other fields (`velocity`, `is_on_floor`, `coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`) are unaffected by step 18.
  - Verification: a differential test comparing a detach frame and a non-detach frame (same prior_state and inputs except `detach_just_pressed`) shows all non-HP fields are identical across both results.
- **AC-56.5:** `prior_state.current_hp` is not modified by `simulate()`. Its value before and after the `simulate()` call are identical. (See also SPEC-61 AC-61.3.)
- **AC-56.6:** The `detach_eligible` variable used in step 18 is the exact same local variable computed in step 17. There is no second evaluation of `detach_just_pressed and prior_state.has_chunk` in step 18.
- **AC-56.7:** When `delta == 0.0` and `detach_eligible` is true, the formula still fires and produces the correct HP reduction. A zero delta affects only time-scaled fields; the HP formula is not delta-dependent.
- **AC-56.8:** With custom `hp_cost_per_detach = 10.0` and `prior_state.current_hp = 80.0` and `min_hp = 0.0`, `result.current_hp == 70.0`. This verifies the formula uses the current configured value rather than a hardcoded `25.0`.

### 3. Risk & Ambiguity Analysis

- **Risk R-56.1 — detach_eligible scope:** If step 17 is ever refactored into a helper function (`_apply_detach()`), the `detach_eligible` local variable will no longer be in scope for step 18. Steps 17 and 18 are architecturally coupled through the shared local. This is documented in the Constraints section and must be preserved in any future refactor.
- **Risk R-56.2 — result.current_hp read before write:** On the detach path, `result.current_hp` is read (via `prior_state.current_hp`) only indirectly — the read is on `prior_state`, not `result`. The `result` instance was allocated by `MovementState.new()` and has `current_hp == 100.0` by default. If any step between the allocation and step 18 were to write `result.current_hp`, step 18 would overwrite that value. This is not a current risk because no other step touches `result.current_hp`, but it is noted for future awareness.
- **Risk R-56.3 — Floating-point arithmetic:** The subtraction `prior_state.current_hp - hp_cost_per_detach` is standard IEEE 754 float arithmetic. With the default values (100.0 - 25.0 = 75.0), this is exact. With non-round values (e.g., 100.0 - 33.33 = 66.67000...), there may be minor floating-point imprecision. Tests must use `== ` assertions with default values (which are all exact) and allow epsilon-range comparisons with non-default fractional values.
- **Risk R-56.4 — max() argument order:** GDScript `max(a, b)` is commutative (`max(a, b) == max(b, a)`), so the argument order in the formula does not affect correctness. However, for readability and consistency with the spec, the order must be `max(min_hp, prior_state.current_hp - hp_cost_per_detach)`.

### 4. Clarifying Questions

None. All design decisions are resolved per CHECKPOINTS.md M1-006 Planner entries. No further clarification is required.

---

## Requirement SPEC-57: HP Carry-Forward When Detach Does Not Fire

### 1. Spec Summary

- **Description:** In step 18 of `simulate()`, when `detach_eligible` is `false`, `result.current_hp` is set to `prior_state.current_hp` via a plain assignment with no transformation, no clamping, and no arithmetic. This is the carry-forward path. It preserves the HP value across frames where no detach occurs, regardless of all other simulation inputs.

  The exact carry-forward expression:
  ```
  result.current_hp = prior_state.current_hp
  ```

- **Constraints:**
  1. The carry-forward assignment is a plain field-to-field copy. No `max()`, `min()`, `clamp()`, or any other function is applied.
  2. The carry-forward fires on every frame where `detach_eligible` is `false`. This includes: frames where `detach_just_pressed == false` (regardless of `has_chunk`), frames where `prior_state.has_chunk == false` (regardless of `detach_just_pressed`), and frames where both are false.
  3. The carry-forward does NOT enforce `max_hp` as an upper bound. If `prior_state.current_hp` is somehow greater than `max_hp` (e.g., set directly by a test), the carry-forward preserves that value without truncation. This is a deliberate design choice: the carry-forward path is purely transparent.
  4. The carry-forward does NOT enforce `min_hp` as a lower bound. If `prior_state.current_hp` is somehow below `min_hp` (e.g., set directly by a test, or `min_hp` was changed after a detach), the carry-forward preserves that value without adjustment.

- **Assumptions:**
  1. The only mechanism that can change `current_hp` downward within `simulate()` in this ticket is the reduction formula in step 18 (detach path). The carry-forward path is a transparent copy.
  2. HP recovery on recall (M1-007) will be implemented in a future ticket. Until then, `current_hp` can only decrease (via detach) or hold steady (via carry-forward). `simulate()` does not increase `current_hp` in M1-006.

- **Scope / Context:** Applies to the `else` branch of the `if detach_eligible:` block in step 18 of `simulate()` in `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd`.

### 2. Acceptance Criteria

- **AC-57.1:** When `detach_just_pressed == false` and `prior_state.has_chunk == true`, `result.current_hp == prior_state.current_hp` exactly. Example: `prior_state.current_hp = 75.0` → `result.current_hp == 75.0`.
- **AC-57.2:** When `detach_just_pressed == true` and `prior_state.has_chunk == false` (no-op detach — chunk already gone), `result.current_hp == prior_state.current_hp` exactly. Example: `prior_state.current_hp = 75.0` → `result.current_hp == 75.0`.
- **AC-57.3:** When `detach_just_pressed == false` and `prior_state.has_chunk == false`, `result.current_hp == prior_state.current_hp` exactly.
- **AC-57.4:** Carry-forward preserves `current_hp` values that are above `max_hp`. Example: `prior_state.current_hp = 200.0`, `max_hp = 100.0`, no detach → `result.current_hp == 200.0`.
- **AC-57.5:** Carry-forward preserves `current_hp` values that are below `min_hp`. Example: `prior_state.current_hp = -5.0`, `min_hp = 0.0`, no detach → `result.current_hp == -5.0`.
- **AC-57.6:** After four consecutive no-detach frames starting from `prior_state.current_hp = 60.0`, every frame's `result.current_hp == 60.0`. HP does not drift over time on carry-forward frames.

### 3. Risk & Ambiguity Analysis

- **Risk R-57.1 — Accidental clamp on carry-forward:** An implementer might reasonably add `max(min_hp, prior_state.current_hp)` to the carry-forward to "protect" the value. AC-57.4 and AC-57.5 explicitly test that no such clamping is applied. This spec must be read as prohibiting any transformation on the carry-forward path.
- **Risk R-57.2 — Drift over no-detach frames:** If the carry-forward assignment is accidentally placed inside a branch with a mathematical expression (e.g., `result.current_hp = prior_state.current_hp + 0.0 * effective_delta`), floating-point semantics guarantee no drift, but the spec's intent is simpler: a direct field copy.

### 4. Clarifying Questions

None. Resolved per CHECKPOINTS.md (M1-006 Planner — current_hp carry-forward: clamp or straight assignment). No further clarification is required.

---

## Requirement SPEC-58: HP Floor — `min_hp` Clamp Applied at Reduction Site Only

### 1. Spec Summary

- **Description:** The `min_hp` config var defines the minimum value that `result.current_hp` can take on a detach frame. It is applied exclusively at the reduction site (step 18, detach path) via the `max()` call in the formula `result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)`. It is not applied anywhere else in `simulate()`: not on the carry-forward path, not on MovementState construction, and not as a guard elsewhere.

  Key behavioral invariants:
  - `result.current_hp` can equal `min_hp` (the floor is inclusive, not exclusive).
  - `result.current_hp` cannot be less than `min_hp` as a result of the HP reduction formula in step 18.
  - Detach is NOT prevented when `prior_state.current_hp == min_hp`. The detach fires (step 17 sets `result.has_chunk = false`) and step 18 clamps HP to `min_hp` (HP stays at floor). Detach is gated only by `prior_state.has_chunk` (the chunk must be attached), not by HP level.
  - `simulate()` does not enforce `max_hp` as an upper clamp. `current_hp` can exceed `max_hp` if set externally.

- **Constraints:**
  1. `max(min_hp, ...)` in step 18 is the only location in `simulate()` where `min_hp` is read.
  2. The carry-forward path (SPEC-57) does not apply `min_hp`. If `prior_state.current_hp < min_hp` (e.g., `min_hp` was changed between frames or the value was set directly), carry-forward preserves the below-floor value unchanged.
  3. `min_hp` with default `0.0` means the floor is zero. A negative `min_hp` (e.g., `-10.0`) means the floor is negative, and HP can reach that negative value via detach.
  4. HP at exactly `min_hp` after a detach does not trigger any additional effects in M1-006 (death, inability to move, etc.). Those are future-ticket concerns.

- **Assumptions:**
  1. `min_hp` is a float and can be any value, including negative. The spec does not impose constraints on its legal range.
  2. The `max()` call produces exact IEEE 754 results for the default values (0.0, 75.0, 10.0, etc.) — no floating-point imprecision at these values.

- **Scope / Context:** Applies to the `if detach_eligible:` branch of step 18 in `simulate()`. Does not apply anywhere else.

### 2. Acceptance Criteria

- **AC-58.1:** When `prior_state.current_hp - hp_cost_per_detach >= min_hp`, `result.current_hp` equals the unmodified subtraction result. Example: `current_hp=100.0`, `cost=25.0`, `min_hp=0.0` → `result.current_hp == 75.0` (not clamped).
- **AC-58.2:** When `prior_state.current_hp - hp_cost_per_detach < min_hp`, `result.current_hp == min_hp`. Example: `current_hp=10.0`, `cost=25.0`, `min_hp=0.0` → `result.current_hp == 0.0`.
- **AC-58.3:** When `prior_state.current_hp == min_hp` and detach fires, `result.current_hp == min_hp` (HP stays at floor; detach still fires). Example: `current_hp=0.0`, `cost=25.0`, `min_hp=0.0` → `result.current_hp == 0.0` AND `result.has_chunk == false`.
- **AC-58.4:** When `prior_state.current_hp == min_hp` and detach fires, detach is not prevented. `result.has_chunk == false` regardless of HP level.
- **AC-58.5:** With `min_hp = -10.0` and `prior_state.current_hp = 5.0` and `hp_cost_per_detach = 25.0`, `result.current_hp == -10.0` (clamped to negative floor).
- **AC-58.6:** With `min_hp = -10.0` and `prior_state.current_hp = -5.0` and `hp_cost_per_detach = 3.0`, `result.current_hp == -8.0` (subtraction result above negative floor, not clamped).
- **AC-58.7:** With `hp_cost_per_detach = 9999.0` and `prior_state.current_hp = 100.0` and `min_hp = 0.0`, `result.current_hp == 0.0` (no underflow, no crash).
- **AC-58.8:** `min_hp` is not applied on carry-forward frames. Example: `prior_state.current_hp = -5.0`, `min_hp = 0.0`, no detach → `result.current_hp == -5.0` (carry-forward, AC-57.5).

### 3. Risk & Ambiguity Analysis

- **Risk R-58.1 — Detach-when-broke:** Some designs prevent detach when HP is at or below a threshold. This spec explicitly rejects that behavior (AC-58.3, AC-58.4). Detach is gated by `has_chunk` only. An implementer who adds an HP gate would break this spec.
- **Risk R-58.2 — Negative HP misinterpretation:** Allowing `min_hp` to be negative and HP to go negative may conflict with future systems that assume HP >= 0. This is a future-ticket risk and is explicitly accepted here.
- **Risk R-58.3 — max_hp as upper clamp:** The spec makes no provision for an upper clamp. If `prior_state.current_hp > max_hp` (e.g., after an external assignment), the formula does not correct it. This is intentional.

### 4. Clarifying Questions

None. Resolved by planner decision: "Detach is not prevented when current_hp == min_hp — explicitly excluded per design decision (clamp, not gate)."

---

## Requirement SPEC-59: `simulate()` Signature — Unchanged

### 1. Spec Summary

- **Description:** The `simulate()` function signature remains identical to its current form (established by SPEC-49 / M1-005). No new parameters are added, no parameters are removed, and no parameter positions change. Step 18 is implemented entirely using existing parameters (`prior_state`, `detach_just_pressed`) and the class's own config vars (`min_hp`, `hp_cost_per_detach`).

  The current (and unchanged) signature:
  ```gdscript
  func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float) -> MovementState:
  ```

- **Constraints:**
  1. The 8 parameters remain in their existing positions (1–8): `prior_state`, `input_axis`, `jump_pressed`, `jump_just_pressed`, `is_on_wall`, `wall_normal_x`, `detach_just_pressed`, `delta`.
  2. No new parameters are added before or after any existing parameter.
  3. The return type annotation (`-> MovementState`) is unchanged.
  4. All existing call-sites of `simulate()` — in `player_controller.gd` and all test files — remain valid without any migration.

- **Assumptions:**
  1. All existing call-sites already pass 8 arguments (migration to 8-arg was completed in M1-005 / SPEC-50). No call-site updates are needed for M1-006.
  2. New test files (SPEC-61) will also call `simulate()` with exactly 8 arguments. No call-site migration will be required when M1-007 lands unless SPEC for M1-007 changes the signature.

- **Scope / Context:** Applies to `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` function `simulate()`. All existing test files and `player_controller.gd` are implicitly in scope as call-sites that must not be broken.

### 2. Acceptance Criteria

- **AC-59.1:** The `simulate()` function declaration in `movement_simulation.gd` has exactly 8 parameters in the exact order listed above, with the exact type annotations shown.
- **AC-59.2:** All existing `simulate()` call-sites in `tests/test_movement_simulation.gd`, `tests/test_movement_simulation_adversarial.gd`, `tests/test_jump_simulation.gd`, `tests/test_jump_simulation_adversarial.gd`, `tests/test_wall_cling_simulation.gd`, `tests/test_wall_cling_simulation_adversarial.gd`, `tests/test_chunk_detach_simulation.gd`, `tests/test_chunk_detach_simulation_adversarial.gd`, and `scripts/player_controller.gd` remain syntactically and semantically valid after M1-006 is implemented. No call-site requires modification.
- **AC-59.3:** `godot --headless --check-only` passes on all files listed in AC-59.2 after M1-006 changes are applied, confirming no call-site argument-count mismatches.
- **AC-59.4:** All pre-existing tests (all test suites registered in `tests/run_tests.gd` as of the end of M1-005) continue to pass with zero regressions after M1-006 implementation.

### 3. Risk & Ambiguity Analysis

- **Risk R-59.1 — Signature drift between spec versions:** If a future planner adds a parameter to `simulate()` for M1-007 without updating this spec, a stale SPEC-59 would incorrectly block the change. This spec is explicitly scoped to M1-006.
- **Risk R-59.2 — Existing test files assume current_hp == 100.0:** Existing test files do not set `prior_state.current_hp` because the field did not exist before M1-006. After M1-006 implementation, every `MovementState.new()` will produce `current_hp == 100.0`. Tests that do not care about HP will silently receive `prior_state.current_hp = 100.0`. This is correct: AC-60.1 confirms the default is sufficient for non-HP tests.

### 4. Clarifying Questions

None. No clarification required.

---

## Requirement SPEC-60: Existing Test Call-Sites — No Migration Required

### 1. Spec Summary

- **Description:** All existing test files that call `simulate()` do not require any migration to accommodate the new `current_hp` field on `MovementState`. Because `current_hp: float = 100.0` has a default initializer, every existing `MovementState.new()` call (used to construct `prior_state` in tests) will automatically produce a state with `current_hp = 100.0`. The existing 8-argument `simulate()` signature is unchanged (SPEC-59). No new argument is added. No existing call-site needs to be updated.

  Tests that care about HP — i.e., tests in the new HP test files (SPEC-61) — must explicitly set `prior_state.current_hp` before calling `simulate()` to exercise non-default HP scenarios. Existing tests that do not set `prior_state.current_hp` will use the default `100.0`, which is correct for their purposes (they are not testing HP behavior).

- **Constraints:**
  1. No existing test file may be modified as part of M1-006 to add or change `current_hp` assignments. The only permitted modifications to existing files are: (a) updating `run_tests.gd` to register the new HP test suites (SPEC-61), and (b) updating `movement_simulation.gd` to implement the new fields and step 18.
  2. In a test that is explicitly testing HP behavior, `prior_state.current_hp` must be set explicitly to the intended starting value before calling `simulate()`. Relying on the default `100.0` in HP tests is a test design defect (the test would pass even with a wrong default).

- **Assumptions:**
  1. GDScript class field initializers are evaluated at construction time (`new()`). The initializer `current_hp: float = 100.0` is executed every time `MovementState.new()` is called, regardless of context.
  2. All 8 existing test files listed in SPEC-59 AC-59.2 were already written using the 8-argument `simulate()` signature (migration was completed in M1-005 per SPEC-50).

- **Scope / Context:** Applies to all test files existing as of the end of M1-005: `test_movement_simulation.gd`, `test_movement_simulation_adversarial.gd`, `test_jump_simulation.gd`, `test_jump_simulation_adversarial.gd`, `test_wall_cling_simulation.gd`, `test_wall_cling_simulation_adversarial.gd`, `test_chunk_detach_simulation.gd`, `test_chunk_detach_simulation_adversarial.gd`.

### 2. Acceptance Criteria

- **AC-60.1:** All 8 existing test files compile and run without modification after M1-006 implementation. No GDScript parse errors, no argument-count mismatches.
- **AC-60.2:** Every `MovementState.new()` call in the existing test files produces an instance with `current_hp == 100.0` automatically, without any explicit assignment.
- **AC-60.3:** All pre-existing test cases pass with zero regressions after M1-006 is implemented. The existing test assertions do not reference `current_hp` and therefore are not affected by the new field.
- **AC-60.4:** The new HP test files (SPEC-61) always set `prior_state.current_hp` explicitly to a non-default value in test cases whose subject is HP behavior, so the test does not silently rely on the default.

### 3. Risk & Ambiguity Analysis

- **Risk R-60.1 — Silent default masking:** An HP test that forgets to set `prior_state.current_hp` will operate with `100.0`. If the test then checks `result.current_hp == 75.0` (expecting a 25-cost reduction from 100.0), the test passes. But if the default is changed, the test could fail without any obvious connection to the change. Mitigation: AC-60.4 requires explicit `current_hp` assignment in all HP-subject tests.
- **Risk R-60.2 — Existing assertion on current_hp field absence:** No existing test asserts the count of fields on `MovementState` or iterates over them. However, if any test does something like `assert(prior_state.get_property_list().size() == 7)`, the addition of `current_hp` would cause it to fail. This is a hypothetical risk; the actual test files do not use such assertions.

### 4. Clarifying Questions

None. No clarification required.

---

## Requirement SPEC-61: New Test Files — Naming, Class Names, and Registration

### 1. Spec Summary

- **Description:** Two new test files are created for M1-006 HP reduction testing. They follow the exact same structural conventions as all prior test suites. Both must be registered in `tests/run_tests.gd` using the same load/new/run_all pattern as existing suites.

  **Primary test file:**
  - Path: `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd`
  - Class name: `HpReductionSimulationTests`
  - Extends: `Object`
  - Entry point: `func run_all() -> int:`
  - Covers: SPEC-54 through SPEC-60 (primary, non-adversarial cases)

  **Adversarial test file:**
  - Path: `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd`
  - Class name: `HpReductionSimulationAdversarialTests`
  - Extends: `Object`
  - Entry point: `func run_all() -> int:`
  - Covers: edge cases, boundary values, mutation scenarios, stress scenarios for SPEC-54 through SPEC-60

  **run_tests.gd registration:**
  - Both suites are appended to `tests/run_tests.gd` after the `ChunkDetachSimulationAdversarialTests` block and before the `# Summary` block.
  - Each suite follows the exact same pattern: `load()` → null-check with `push_error` and `quit(1)` → `new()` → `run_all()` → `total_failures += failures`.
  - The `load()` call for the primary suite uses the resource path `"res://tests/test_hp_reduction_simulation.gd"`.
  - The `load()` call for the adversarial suite uses the resource path `"res://tests/test_hp_reduction_simulation_adversarial.gd"`.

- **Constraints:**
  1. Both test files must use `class_name` declarations matching the class names above.
  2. Both test files must `extends Object` (same as all existing simulation test suites).
  3. The `run_all()` function must return an `int` (failure count): `0` means all tests in the suite passed; a positive integer means that many tests failed.
  4. Each test function must include an `# AC-N.M` comment referencing the specific acceptance criterion it covers.
  5. Both files must be syntactically valid GDScript. The `godot --headless --check-only` command must pass on both files.
  6. The primary test file must cover the 12 cases enumerated in Task 2 of the execution plan (see the ticket file, Task 2 section, cases 1–12).
  7. The adversarial test file must cover the 14 cases enumerated in Task 3 of the execution plan (see the ticket file, Task 3 section, cases 1–14).

- **Assumptions:**
  1. The `run_all()` contract (return int fail count, print per-test pass/fail) follows the established pattern from `test_chunk_detach_simulation.gd` and other existing test files.
  2. The `MovementSimulation` class is loaded via `preload("res://scripts/movement_simulation.gd")` or `load(...)` at the top of each new test file, following the same pattern as existing test files.
  3. Test helper functions (e.g., `assert_approx_equal`, `make_prior`) may be defined as private functions within the test file if they are needed for clarity. They do not need to be in a shared utility file.

- **Scope / Context:** Applies to the two new files listed above and to the modifications to `tests/run_tests.gd`. The new test files are owned by the Test Designer Agent (Tasks 2 and 3). The `run_tests.gd` registration is owned by the Core Simulation Agent (Task 5, which may be folded into Task 4).

### 2. Acceptance Criteria

- **AC-61.1:** The file `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd` exists after implementation.
- **AC-61.2:** The file `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd` exists after implementation.
- **AC-61.3:** Both files declare `class_name HpReductionSimulationTests` and `class_name HpReductionSimulationAdversarialTests` respectively, both `extends Object`.
- **AC-61.4:** Both files contain a `func run_all() -> int:` function.
- **AC-61.5:** `godot --headless --check-only` (or equivalent GDScript syntax validation) passes on both files.
- **AC-61.6:** `tests/run_tests.gd` registers both new suites in the `_initialize()` function, using the same `load` / null-check / `new` / `run_all` / `total_failures +=` pattern as all existing suites.
- **AC-61.7:** Running `godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd` executes both new HP suites and they are included in the total failure count.
- **AC-61.8:** The primary suite (`HpReductionSimulationTests`) contains at minimum 12 test cases corresponding to the 12 cases specified in Task 2 of the execution plan. Each test case has an `# AC-N.M` comment.
- **AC-61.9:** The adversarial suite (`HpReductionSimulationAdversarialTests`) contains at minimum 14 test cases corresponding to the 14 cases specified in Task 3 of the execution plan. Each test case has an `# AC-N.M` comment.
- **AC-61.10:** All tests in both new suites pass after M1-006 implementation is complete (zero failures in both suites).

### 3. Risk & Ambiguity Analysis

- **Risk R-61.1 — All 9 fields in adversarial case 1:** The adversarial suite must verify all 9 `MovementState` fields (including `current_hp`) on a single detach frame. Missing `current_hp` from this check would leave a gap between the primary and adversarial suites.
- **Risk R-61.2 — run_tests.gd insertion point:** If the new suites are accidentally appended after the `# Summary` print block, they will run after `quit()` is called and their results will not be reflected in the exit code. The insertion point must be before the `# Summary` block.
- **Risk R-61.3 — Class name cache in headless mode:** Godot's class name registry may not be warmed in headless `--check-only` mode. Using `preload()` rather than class name references for loading `MovementSimulation` is the safer pattern (matching the precedent from `test_chunk_detach_simulation.gd`).

### 4. Clarifying Questions

None. Naming conventions and registration pattern are fully established by prior test suites. No further clarification is required.

---

## Non-Functional Requirements (SPEC-61 Extension)

The following non-functional constraints apply to the M1-006 implementation as a whole. They do not introduce new behavior but constrain how the implementation must be written.

### NFR-61.A: Typed GDScript Throughout

**Description:** All new code introduced in M1-006 (field declarations, config vars, local variables, function bodies, and test files) must use GDScript static typing. No untyped `var` declarations where a type can be inferred or declared. No `Variant` where a concrete type is appropriate.

**Acceptance Criteria:**
- `var current_hp: float = 100.0` — typed.
- `var max_hp: float = 100.0`, `var hp_cost_per_detach: float = 25.0`, `var min_hp: float = 0.0` — all typed.
- Any local variables introduced in step 18 of `simulate()` are typed.
- Test file variables are typed (`var sim: MovementSimulation`, `var prior: MovementSimulation.MovementState`, etc.).

### NFR-61.B: No Movement Math in `player_controller.gd`

**Description:** The `current_hp` copy-back in `player_controller.gd` must follow the established pattern for other state fields (a plain field assignment: `_current_state.current_hp = next_state.current_hp`). No HP arithmetic, no clamping, no conditional logic based on HP value may appear in `player_controller.gd` in this ticket.

**Acceptance Criteria:**
- `player_controller.gd` contains exactly one new line for HP: `_current_state.current_hp = next_state.current_hp`, placed in the copy-back section of `_physics_process()`.
- No `if`, `max()`, `min()`, `clamp()`, or arithmetic operator is used in relation to `current_hp` in `player_controller.gd`.
- No HP-related `@export` vars are added to `player_controller.gd` in M1-006.

**Rationale:** All movement and HP computation belongs in `MovementSimulation`. The controller is strictly an integration layer. Precedent: all prior copy-backs (`coyote_timer`, `jump_consumed`, `is_wall_clinging`, `cling_timer`, `has_chunk`) are plain assignments.

### NFR-61.C: `prior_state` Immutability in `simulate()`

**Description:** `prior_state` must not be mutated at any point inside `simulate()`. This constraint applies to all existing steps and to the new step 18.

**Acceptance Criteria:**
- Step 18 reads `prior_state.current_hp` but does not assign to any field of `prior_state`.
- No other step in `simulate()` assigns to any field of `prior_state`.
- Verified by: before-and-after comparison of all 9 `prior_state` fields across a `simulate()` call with detach (AC-56.5, adversarial test case 11 in Task 3).

**Rationale:** `simulate()` is a pure function. The caller's state object must not be modified as a side effect. This was established in SPEC-4 and is extended to cover `current_hp` in M1-006.

---

## Summary Table

| SPEC | Subject | File(s) Affected | Key AC |
|------|---------|-----------------|--------|
| SPEC-54 | `MovementState.current_hp` field | `movement_simulation.gd` | AC-54.1, AC-54.2, AC-54.3 |
| SPEC-55 | `max_hp`, `hp_cost_per_detach`, `min_hp` config vars | `movement_simulation.gd` | AC-55.1, AC-55.2, AC-55.3 |
| SPEC-56 | HP reduction formula (step 18, detach path) | `movement_simulation.gd` | AC-56.1, AC-56.3, AC-56.6 |
| SPEC-57 | HP carry-forward (step 18, non-detach path) | `movement_simulation.gd` | AC-57.1, AC-57.2, AC-57.6 |
| SPEC-58 | `min_hp` floor — clamp site only | `movement_simulation.gd` | AC-58.2, AC-58.3, AC-58.4 |
| SPEC-59 | `simulate()` signature unchanged | `movement_simulation.gd`, all call-sites | AC-59.1, AC-59.2, AC-59.4 |
| SPEC-60 | No existing test migration required | All 8 existing test files | AC-60.1, AC-60.3 |
| SPEC-61 | New test file naming, class names, registration | `test_hp_reduction_simulation.gd`, `test_hp_reduction_simulation_adversarial.gd`, `run_tests.gd` | AC-61.1 through AC-61.10 |
