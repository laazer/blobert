# HP reduction on detach

**Epic:** Milestone 1 – Core Movement Prototype
**Status:** In Progress

---

## Description

When the slime detaches a chunk, reduce the player's current HP by a defined amount (or percentage) so detach has a clear cost and ties into the infection/mutation loop later.

## Acceptance criteria

- [ ] HP decreases by configured amount/percentage when chunk is detached
- [ ] HP does not go below minimum (e.g. 0 or 1) if design specifies a floor
- [ ] HP state is consistent with chunk state (detached vs reabsorbed)
- [ ] No exploit (e.g. repeated detach/recall for unintended HP gain)
- [ ] Mechanic is human-playable in-editor: HP values and any related UI are visible and clearly reflect detach events without relying on debug overlays

---

## Dependencies

- M1-005 (chunk_detach) — COMPLETE

---

## Execution Plan

### Overview

HP reduction on detach is a pure simulation change. The `simulate()` signature does not change. No new input actions are required. The work touches three layers:

1. `MovementState` inner class — add `current_hp: float` field (8th field)
2. `MovementSimulation` config vars — add `max_hp`, `hp_cost_per_detach`, `min_hp`
3. `simulate()` body — add step 18 (HP reduction) immediately after step 17 (chunk detach)

Test files must be updated to populate `current_hp` in prior_state for all calls that rely on the new field, and new HP-specific test files must be created.

### SPEC Numbers

Continuing from SPEC-53. HP reduction specs start at SPEC-54.

- SPEC-54 — `MovementState.current_hp` field declaration and default
- SPEC-55 — `MovementSimulation` config vars: `max_hp`, `hp_cost_per_detach`, `min_hp`
- SPEC-56 — simulate() step 18: HP reduction formula and order of operations
- SPEC-57 — HP carry-forward when detach does not fire
- SPEC-58 — HP floor clamp (`min_hp`) applied at reduction site only
- SPEC-59 — simulate() signature unchanged (no new parameters)
- SPEC-60 — `current_hp` in existing test call-sites: default field value is sufficient; no migration of call-sites required (field has a default)
- SPEC-61 — New test file naming and registration

### Normative Step 18 Description

Step 18 is appended immediately after step 17 (chunk detach) as the final step of `simulate()`.

```
18. HP reduction (SPEC-56):
      if detach_eligible (from step 17):
          result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)
      else:
          result.current_hp = prior_state.current_hp
    Reads:  detach_eligible (local var from step 17), prior_state.current_hp, min_hp, hp_cost_per_detach
    Writes: result.current_hp only — no other fields affected
```

Key invariants:
- `detach_eligible` is the exact local variable computed in step 17; it is not re-evaluated.
- HP reduction uses `prior_state.current_hp` (the value entering this frame), not `result.current_hp` (which is unset at this point in the no-detach path).
- The clamp lower-bound (`max(min_hp, ...)`) is applied only here, not on carry-forward.
- `simulate()` never increases `current_hp` — that is M1-007's responsibility.

### Task Breakdown

#### Task 1 — Write Spec (`hp_reduction_spec.md`)
**Agent:** Spec Agent
**Input:**
- This execution plan (all SPEC numbers, field names, formulas, and invariants above)
- `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` (current state, step 17 as precedent)
- `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/CHECKPOINTS.md` (M1-006 entries for decisions already made)

**Output:** `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/hp_reduction_spec.md`

The spec file must cover, at minimum:

- **SPEC-54** — `MovementState` inner class: new field `current_hp: float = 100.0`. Default is a concrete literal (not a computed reference to `max_hp`). This is the 8th field. Document the coupling: if `max_hp` default changes, `current_hp` default must be updated manually.
- **SPEC-55** — Three new config vars on `MovementSimulation`:
  - `var max_hp: float = 100.0` — maximum HP ceiling; not enforced as an upper clamp in simulate() for this ticket; informational for UI/other systems
  - `var hp_cost_per_detach: float = 25.0` — amount subtracted from `current_hp` on each detach
  - `var min_hp: float = 0.0` — floor applied via clamp at reduction site; HP cannot go below this value
- **SPEC-56** — simulate() step 18 (HP reduction): exact formula, exact reads/writes, exact ordering (after step 17, before `return result`). Reuses `detach_eligible` local variable from step 17. Formula: `result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)`.
- **SPEC-57** — HP carry-forward (no detach): `result.current_hp = prior_state.current_hp` — plain assignment, no clamp.
- **SPEC-58** — HP floor semantics: clamp is applied at reduction site only. HP can equal `min_hp` but never go below it. Detach is not prevented when `current_hp == min_hp`; HP simply stays at floor.
- **SPEC-59** — simulate() signature is unchanged. No new parameters. All 8 existing parameters remain in their existing positions.
- **SPEC-60** — Existing test files: no call-site migration required. The new `current_hp` field has a default value of `100.0`; all existing `MovementState.new()` calls produce a state with `current_hp = 100.0` automatically. Tests that care about HP must set `prior_state.current_hp` explicitly.
- **SPEC-61** — New test files: `tests/test_hp_reduction_simulation.gd` (class `HpReductionSimulationTests`) and `tests/test_hp_reduction_simulation_adversarial.gd` (class `HpReductionSimulationAdversarialTests`). Both must be registered in `tests/run_tests.gd`.

Each SPEC item must include: Summary, Acceptance Criteria (AC-N.M format), Reads/Writes where applicable, and a "rationale" note.

**Dependencies:** None (first task)
**Success Criteria:** File `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/hp_reduction_spec.md` exists, contains all 8 SPEC items (SPEC-54 through SPEC-61), all ACs are numbered, and no item is missing a Reads/Writes section where applicable.

---

#### Task 2 — Design Primary Tests (`tests/test_hp_reduction_simulation.gd`)
**Agent:** Test Design Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/hp_reduction_spec.md` (from Task 1)
- `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` (current state)
- `/Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation.gd` (structural precedent)

**Output:** `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd`

Must cover at minimum:
1. HP decreases by `hp_cost_per_detach` on a detach frame (has_chunk=true, detach_just_pressed=true)
2. HP does not go below `min_hp` (0.0) when cost would push it negative
3. HP at exactly `min_hp` stays at `min_hp` after detach (floor is inclusive, not exclusive)
4. HP carries forward unchanged when detach does not fire (has_chunk=false, detach_just_pressed=true — no-op)
5. HP carries forward unchanged when detach_just_pressed=false regardless of has_chunk
6. Non-detach fields (velocity.x, velocity.y, is_on_floor, coyote_timer, jump_consumed, is_wall_clinging, cling_timer, has_chunk) are unaffected by HP step — use differential test (detach vs. no-detach)
7. prior_state.current_hp is not mutated by simulate()
8. delta=0.0 with detach: HP still reduces; all other time-driven fields are unchanged
9. Custom hp_cost_per_detach value (non-default): verify formula uses configured value
10. Custom min_hp value (non-default): verify floor is respected with custom floor
11. max_hp config var has no effect on HP reduction (HP can go below max_hp — max_hp is not a cap in this ticket)
12. Two consecutive detach frames with has_chunk=true on frame 1 (transitions false) and detach_just_pressed=true on frame 2 — frame 2 is no-op (has_chunk already false), HP does not change on frame 2

Each test must include an `# AC-N.M` comment referencing the specific acceptance criterion it covers.

**Dependencies:** Task 1
**Success Criteria:** File `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd` exists, contains all 12+ test cases as described, each references at least one AC number, and the file is syntactically valid GDScript (can be parsed headlessly).

---

#### Task 3 — Design Adversarial Tests (`tests/test_hp_reduction_simulation_adversarial.gd`)
**Agent:** Test Design Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/hp_reduction_spec.md` (from Task 1)
- `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd` (from Task 2, for coverage gap analysis)
- `/Users/jacobbrandt/workspace/blobert/tests/test_chunk_detach_simulation_adversarial.gd` (structural precedent)

**Output:** `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd`

Must cover at minimum:
1. All 9 MovementState fields (velocity.x, velocity.y, is_on_floor, coyote_timer, jump_consumed, is_wall_clinging, cling_timer, has_chunk, current_hp) verified on a single detach frame
2. HP + jump same frame: regular jump fires AND HP reduces simultaneously; both results correct
3. HP + wall jump same frame: wall jump fires AND HP reduces simultaneously
4. HP reduction during active wall cling: cling fields carry forward identically (differential)
5. HP at `hp_cost_per_detach - epsilon` (just above zero cost): verify floor clamp at 0.0
6. HP exactly at `hp_cost_per_detach`: result is exactly `min_hp` (0.0)
7. HP far below cost (prior_state.current_hp = 1.0, cost = 25.0): result is clamped to min_hp
8. Instance isolation: two separate MovementSimulation instances — HP reduction in one does not affect the other
9. Config mutation: mutate all 12 pre-existing config vars to extreme values; verify HP reduction still applies `hp_cost_per_detach` correctly (only the three new HP config vars control HP behavior)
10. 50-frame stability: 50 consecutive no-detach frames; current_hp remains constant (no drift)
11. prior_state immutability: all 9 fields verified before and after simulate() call with detach
12. hp_cost_per_detach=0.0: detach fires but HP stays unchanged (zero cost is valid)
13. min_hp=negative value (e.g. -10.0): HP can go to -10.0 if cost pushes it there (min_hp is the floor, not a hard zero)
14. Large hp_cost_per_detach (e.g. 9999.0): HP clamps to min_hp (0.0) — no underflow or crash

**Dependencies:** Tasks 1 and 2
**Success Criteria:** File `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd` exists, contains all 14+ adversarial cases, and is syntactically valid GDScript.

---

#### Task 4 — Implement Core Simulation Changes (`movement_simulation.gd`)
**Agent:** Core Simulation Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/hp_reduction_spec.md` (from Task 1)
- `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd` (from Task 2)
- `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd` (from Task 3)
- `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` (to be modified)

**Changes required:**

1. `MovementState` inner class: add `var current_hp: float = 100.0` as the 8th field, after `has_chunk`. Update the header comment block to reference SPEC-54 and AC-54.1.

2. `MovementSimulation` config vars: add three new vars in the config section, after `wall_jump_horizontal_speed`:
   ```
   var max_hp: float = 100.0
   var hp_cost_per_detach: float = 25.0
   var min_hp: float = 0.0
   ```
   Each must have a doc comment matching the style of existing config vars.

3. `simulate()` normative order comment block: update to list 18 steps (add step 18 description after step 17).

4. `simulate()` body: append step 18 immediately after step 17, before `return result`:
   ```gdscript
   # --- 18. HP reduction (SPEC-56) ---
   if detach_eligible:
       result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)
   else:
       result.current_hp = prior_state.current_hp
   ```

5. Update the spec coverage comment block at the top of the file to include:
   ```
   #   SPEC-54 — MovementState new field: current_hp
   #   SPEC-55 — MovementSimulation new config parameters: max_hp, hp_cost_per_detach, min_hp
   #   SPEC-56 — HP reduction step (step 18): formula and order of operations
   #   SPEC-57 — HP carry-forward when detach does not fire
   #   SPEC-58 — HP floor clamp (min_hp) applied at reduction site only
   #   SPEC-59 — simulate() signature unchanged
   ```

6. Run all tests headlessly and confirm zero failures before committing:
   ```
   godot --headless -- --run-tests
   ```
   (or the equivalent test runner invocation used by prior agents — check `tests/run_tests.gd` for the entry point)

**No other files** may be modified in this task. `player_controller.gd` does not need changes (HP is a pure simulation field; the controller reads `_current_state.current_hp` for UI/game logic in a future ticket).

**Dependencies:** Tasks 1, 2, 3
**Success Criteria:**
- `/Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd` has `current_hp` field on `MovementState`
- Three new config vars present with correct defaults
- Step 18 present in `simulate()` body using `detach_eligible` local var
- All existing tests still pass (no regressions)
- New HP test files pass (from Tasks 2 and 3)
- `tests/run_tests.gd` has both new HP test files registered
- Changes committed to git with message: `Implement HP reduction on detach (M1-006, SPEC-54–SPEC-59)`

---

#### Task 5 — Register New Test Files in run_tests.gd
**Agent:** Core Simulation Agent
**Input:**
- `/Users/jacobbrandt/workspace/blobert/tests/run_tests.gd` (to be modified)
- `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd` (from Task 2)
- `/Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd` (from Task 3)

**Changes required:**
- Register `HpReductionSimulationTests` and `HpReductionSimulationAdversarialTests` in `run_tests.gd` following the exact same pattern as existing test suite registrations.

**Note:** This task may be folded into Task 4 if the Core Simulation Agent finds it natural to do so atomically. It is listed separately to ensure it is not forgotten.

**Dependencies:** Tasks 2, 3, 4
**Success Criteria:** Running `godot --headless -- --run-tests` (or equivalent) executes HP test suites and all tests pass.

---

### Risks and Assumptions

| Risk | Mitigation |
|------|-----------|
| `MovementState.new()` calls in existing tests will silently use `current_hp = 100.0` — tests that do not set `prior_state.current_hp` will get default 100.0. This is correct but could mask tests that should set a specific HP value. | Test Design agent must explicitly set `prior_state.current_hp` in any test where HP is the subject under test (Tasks 2 and 3). |
| `detach_eligible` is a local variable scoped inside `simulate()`. If step 17 is ever refactored to a helper function, step 18 will break. | Document in the spec that steps 17 and 18 are co-located in `simulate()` and share the `detach_eligible` local. Any future refactor must preserve this sharing. |
| `max_hp` is added as a config var but is not enforced anywhere in this ticket. A future agent might assume `current_hp` is always <= `max_hp` and write a defensive assert that fails. | Spec must explicitly document that `max_hp` is informational only in this ticket's scope. |
| The normative order comment in `simulate()` currently states 17 steps. Step 18 must be added; if the comment is not updated the spec coverage will be misleading. | Task 4 explicitly requires updating the comment block. |

---

### Out of Scope

- HP regeneration on chunk recall — M1-007
- HP display / UI — future ticket
- HP at zero causing death or state change — future ticket
- Preventing detach when `current_hp == min_hp` — explicitly excluded per design decision (clamp, not gate)
- `max_hp` enforcement as an upper clamp — future ticket (M1-007 recall may restore HP up to max_hp)

---

## Specification

Spec file: `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/hp_reduction_spec.md`

### SPEC-54 Summary: `MovementState.current_hp` Field
Add `var current_hp: float = 100.0` as the 8th field of `MovementState` (after `has_chunk`). The initializer is a concrete literal `100.0`, not a reference to `max_hp`. Coupling: if `max_hp` default changes, this literal must be updated manually.

Key ACs: AC-54.1 (exact declaration), AC-54.2 (8th field position), AC-54.3 (default via new()), AC-54.6 (comment updated).

### SPEC-55 Summary: Three New Config Vars
Add after `wall_jump_horizontal_speed`:
- `var max_hp: float = 100.0` — informational only; not enforced as upper clamp in simulate()
- `var hp_cost_per_detach: float = 25.0` — amount subtracted per detach frame
- `var min_hp: float = 0.0` — floor applied at reduction site only

Key ACs: AC-55.1–55.3 (defaults), AC-55.5 (max_hp not read in simulate()), AC-55.6 (doc comments).

### SPEC-56 Summary: Step 18 HP Reduction Formula
Appended after step 17, before `return result`. Reuses `detach_eligible` local from step 17.
- Detach path: `result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)`
- Non-detach path: see SPEC-57

Reads: `detach_eligible`, `prior_state.current_hp`, `min_hp`, `hp_cost_per_detach`. Writes: `result.current_hp` only.

Key ACs: AC-56.1 (formula correct), AC-56.3 (same frame as detach), AC-56.4 (no other fields affected), AC-56.6 (detach_eligible reused).

### SPEC-57 Summary: HP Carry-Forward (Non-Detach Path)
When `detach_eligible` is false: `result.current_hp = prior_state.current_hp`. Plain assignment only — no clamping, no arithmetic. Preserves values outside [min_hp, max_hp] range unchanged.

Key ACs: AC-57.1–57.3 (all non-detach cases), AC-57.4–57.5 (no clamping on carry-forward).

### SPEC-58 Summary: HP Floor Clamp at Reduction Site Only
`min_hp` is applied via `max()` exclusively in step 18's detach path. HP can equal `min_hp` (inclusive floor). Detach is not gated by HP level. Negative `min_hp` is valid (allows negative HP).

Key ACs: AC-58.2 (clamped below floor), AC-58.3 (at floor stays at floor), AC-58.4 (detach not prevented by HP), AC-58.7 (large cost clamped safely).

### SPEC-59 Summary: Signature Unchanged
`simulate()` retains exactly 8 parameters in existing positions. No new parameters. All existing call-sites remain valid without modification.

Key ACs: AC-59.1 (signature exact), AC-59.2 (all call-sites valid), AC-59.4 (no regressions).

### SPEC-60 Summary: No Existing Test Migration
Existing 8 test files require no changes. `current_hp: float = 100.0` default means `MovementState.new()` auto-initializes to full HP. New HP tests must set `prior_state.current_hp` explicitly.

Key ACs: AC-60.1 (existing tests compile), AC-60.3 (no regressions), AC-60.4 (HP tests set explicit values).

### SPEC-61 Summary: New Test Files and Registration
- Primary: `tests/test_hp_reduction_simulation.gd` — class `HpReductionSimulationTests extends Object` — 12+ cases
- Adversarial: `tests/test_hp_reduction_simulation_adversarial.gd` — class `HpReductionSimulationAdversarialTests extends Object` — 14+ cases
- Both registered in `tests/run_tests.gd` following existing suite pattern (load/null-check/new/run_all/total_failures+=)

Key ACs: AC-61.1–61.2 (files exist), AC-61.3–61.4 (class structure), AC-61.5 (valid GDScript), AC-61.6–61.7 (registered and executed), AC-61.8–61.10 (test counts and all pass).

Non-functional requirements covered:
- NFR-61.A: Typed GDScript throughout all new code
- NFR-61.B: `player_controller.gd` copy-back is `_current_state.current_hp = next_state.current_hp` — no arithmetic, no conditional, no new @export
- NFR-61.C: `prior_state` immutability — all 9 fields unmodified by simulate()

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
  "spec_file_path": "string — absolute path: /Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/hp_reduction_spec.md",
  "primary_test_path": "string — /Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation.gd",
  "adversarial_test_path": "string — /Users/jacobbrandt/workspace/blobert/tests/test_hp_reduction_simulation_adversarial.gd",
  "simulation_path": "string — /Users/jacobbrandt/workspace/blobert/scripts/movement_simulation.gd",
  "run_tests_path": "string — /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd"
}
```

## Status
Proceed

## Reason
Test Breaker Agent wrote `tests/test_hp_reduction_simulation_adversarial.gd` (class HpReductionSimulationAdversarialTests, 26 adversarial gap tests covering all 14 required Task 3 cases plus 12 additional adversarial scenarios). The adversarial suite block in `tests/run_tests.gd` has been uncommented and activated. All test files are now registered and ready to be executed. One logic error in GAP-08 (incorrect expected value of 0.0 instead of 1.0 for cost=99.0) was identified and corrected before registration. CHECKPOINT decisions logged in CHECKPOINTS.md: negative cost behavior (GAP-17), NaN propagation (GAP-16), below-floor carry-forward (GAP-22). Core Simulation Agent must: (1) add `current_hp: float = 100.0` field to MovementState inner class (8th field, after has_chunk); (2) add three config vars (max_hp, hp_cost_per_detach, min_hp) to MovementSimulation; (3) implement step 18 in simulate() body using detach_eligible local var; (4) run all tests headlessly and confirm zero failures; (5) commit with message per spec.
