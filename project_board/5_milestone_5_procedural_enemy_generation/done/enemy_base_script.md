# TICKET: enemy_base_script
Title: Implement enemy_base.gd shared script
Project: blobert
Created By: Human
Created On: 2026-03-21

---

## Description

Create `scripts/enemies/enemy_base.gd` (new directory `enemies/`, distinct from existing `scripts/enemy/`) that all procedurally generated enemies share. The script must attach cleanly to CharacterBody3D roots created by `scripts/asset_generation/load_assets.gd`. It exposes `enemy_id`, `enemy_family`, and `mutation_drop` as `@export` String vars and defines a `State` enum with values `NORMAL`, `WEAKENED`, `INFECTED`. It provides stub hooks for state transitions so the existing `EnemyStateMachine` (in `scripts/enemy/enemy_state_machine.gd`) can drive transitions into this script via external coordination.

### Context

- `scripts/enemies/enemy_base.gd` does NOT exist yet — this ticket creates it.
- The existing enemy (`scripts/enemy/enemy_infection_3d.gd`) extends `BasePhysicsEntity3D` and is unaffected; it uses `scripts/enemy/` not `scripts/enemies/`.
- `scripts/asset_generation/load_assets.gd` references `res://scripts/enemies/enemy_base.gd` as `DEFAULT_ENEMY_SCRIPT` and calls `root.set_script(script_res)` on a CharacterBody3D root. It also calls `root.set("enemy_id", ...)`, `root.set("enemy_family", ...)`, and `root.set("mutation_drop", ...)` — these must resolve to the @export vars.
- No existing tests or source files may be modified. No regressions to the current test suite.

---

## Acceptance Criteria

- `scripts/enemies/enemy_base.gd` exists and parses without errors in Godot 4 headless.
- Script extends CharacterBody3D and has `class_name EnemyBase`.
- Three `@export var` declarations: `enemy_id: String`, `enemy_family: String`, `mutation_drop: String` — all default to `""`.
- `enum State { NORMAL, WEAKENED, INFECTED }` is defined on the script.
- `NORMAL == 0`, `WEAKENED == 1`, `INFECTED == 2` (default GDScript enum ordering).
- `var current_state: State = State.NORMAL` is a readable instance variable.
- `func set_base_state(state: State) -> void` assigns `current_state` and is callable.
- `func get_base_state() -> State` returns `current_state` and is callable.
- Script attaches cleanly to a CharacterBody3D in headless mode (no crash, no parse error).
- `root.set("enemy_id", "foo")` on an EnemyBase-scripted CharacterBody3D correctly sets the exported property.
- Existing test suite passes with zero regressions (`run_tests.sh` exits 0).

---

## Dependencies

- None (no existing script is modified; no other ticket must complete first).

---

## Execution Plan

### Task 1 — Specification (Spec Agent)

**Objective:** Produce a complete formal spec for `enemy_base.gd` covering all exported vars, the State enum, state transition hooks, integration contract with load_assets.gd, and headless testability constraints.

**Input:**
- This ticket.
- `scripts/asset_generation/load_assets.gd` — shows how the script is attached and which properties are set via `root.set(...)`.
- `scripts/enemy/enemy_state_machine.gd` — existing state machine whose string states map to the base script's enum.
- `scripts/enemy/enemy_infection_3d.gd` — existing enemy; defines the parallel class hierarchy this ticket must not collide with.
- `scripts/player/base_physics_entity_3d.gd` — existing CharacterBody3D base; confirm no class_name collision.
- `tests/scripts/player/test_base_physics_entity_3d.gd` — confirms CharacterBody3D.new() is headlessly safe.

**Expected Output:** A spec document at `agent_context/projects/blobert/enemy_base_script_spec.md` (or equivalent spec folder) that defines:
1. Class declaration: `class_name EnemyBase extends CharacterBody3D`.
2. Exported vars with exact types and defaults.
3. State enum with explicit integer values.
4. `current_state` var declaration.
5. `set_base_state` and `get_base_state` signatures and contracts.
6. Integration contract with load_assets.gd (property set via `root.set()`).
7. Non-functional requirements: no Node dependencies in pure logic paths, no _physics_process override (leave to subclasses), no autoload dependency.
8. Headless test constraints: CharacterBody3D.new() safe, export vars readable without scene tree.

**Dependencies:** None.

**Success Criteria:** Spec document exists; all Acceptance Criteria above are traceable to a spec section; no ambiguity about enum integer values or export var defaults.

**Risks / Assumptions:**
- Assumption: `set_base_state` / `get_base_state` naming is appropriate; the spec may rename to `apply_state` / `query_state` if naming conflicts with any Godot built-in — Spec Agent must verify.
- Assumption: No _physics_process needed on the base script; existing CharacterBody3D physics are handled by load_assets.gd-generated scenes or future subclasses.

---

### Task 2 — Test Design (Test Designer Agent)

**Objective:** Write the primary headless test file `tests/scripts/enemy/test_enemy_base.gd` covering all Acceptance Criteria in a red-phase-first (tests fail before implementation).

**Input:**
- Spec document from Task 1.
- `tests/scripts/enemy/test_enemy_state_machine.gd` — test file pattern to match exactly (class extends Object, `_pass`/`_fail` helpers, `run_all() -> int`).
- `tests/scripts/player/test_base_physics_entity_3d.gd` — shows headless CharacterBody3D instantiation pattern.
- This ticket's Acceptance Criteria.

**Expected Output:** `tests/scripts/enemy/test_enemy_base.gd` with tests covering:

| Test ID | Assertion |
|---------|-----------|
| EB-STRUCT-1 | Script file loads without parse error (load() returns non-null GDScript) |
| EB-STRUCT-2 | CharacterBody3D.new() + set_script(enemy_base_script) does not crash |
| EB-STRUCT-3 | Scripted node is instance of CharacterBody3D |
| EB-EXPORT-1 | enemy_id property exists and defaults to "" |
| EB-EXPORT-2 | enemy_family property exists and defaults to "" |
| EB-EXPORT-3 | mutation_drop property exists and defaults to "" |
| EB-EXPORT-4 | root.set("enemy_id", "acid_spitter_00") correctly sets the property (reads back via root.get or root.enemy_id) |
| EB-EXPORT-5 | root.set("enemy_family", "acid_spitter") correctly sets the property |
| EB-EXPORT-6 | root.set("mutation_drop", "acid") correctly sets the property |
| EB-ENUM-1 | State.NORMAL == 0 |
| EB-ENUM-2 | State.WEAKENED == 1 |
| EB-ENUM-3 | State.INFECTED == 2 |
| EB-ENUM-4 | EnemyBase enum has exactly 3 values (not more, not fewer) |
| EB-STATE-1 | current_state defaults to State.NORMAL on fresh instance |
| EB-STATE-2 | set_base_state(State.WEAKENED) transitions current_state to WEAKENED |
| EB-STATE-3 | set_base_state(State.INFECTED) transitions current_state to INFECTED |
| EB-STATE-4 | set_base_state(State.NORMAL) transitions current_state back to NORMAL from INFECTED |
| EB-STATE-5 | get_base_state() returns current_state correctly after each transition |
| EB-ISOLATE-1 | Two separate EnemyBase instances have independent current_state (mutating one does not affect the other) |

Tests must be RED before the file exists and GREEN after implementation. Test file must be discoverable by `run_tests.gd` (starts with `test_`, defines `run_all() -> int`).

**Dependencies:** Task 1 (spec).

**Success Criteria:** Test file exists; all tests fail when `scripts/enemies/enemy_base.gd` does not exist (red phase); each test has a unique assertion name string matching `EB-*` prefix.

**Risks / Assumptions:**
- EB-ENUM-4 requires iterating the enum dictionary; the spec must confirm GDScript exposes `EnemyBase.State` as an accessible dictionary.
- If CharacterBody3D.new() + set_script requires the script to be a loaded Resource (not a new() instance), the test must use `load("res://scripts/enemies/enemy_base.gd")` — confirm with spec.

---

### Task 3 — Test Breaker (Test Breaker Agent)

**Objective:** Write adversarial extension `tests/scripts/enemy/test_enemy_base_adversarial.gd` that exercises boundary conditions and failure modes not covered by the primary suite.

**Input:**
- Spec document from Task 1.
- Primary test file from Task 2.
- Acceptance Criteria.

**Expected Output:** `tests/scripts/enemy/test_enemy_base_adversarial.gd` with adversarial cases including at minimum:

| ADV ID | Adversarial Case |
|--------|-----------------|
| ADV-EB-01 | set_base_state called with an out-of-range integer cast to State — must not corrupt current_state beyond defined enum values |
| ADV-EB-02 | Two rapid set_base_state calls (WEAKENED then INFECTED) — final state must be INFECTED, not intermediate stuck at WEAKENED |
| ADV-EB-03 | enemy_id set to a very long string (256+ chars) — no crash, property stores and returns the full string |
| ADV-EB-04 | mutation_drop set to "unknown" (the load_assets.gd default for unmapped families) — correctly stored and returned |
| ADV-EB-05 | Three separate EnemyBase instances all in different states simultaneously — each returns its own current_state independently |
| ADV-EB-06 | set_base_state called before any export vars are set — no crash, current_state transitions correctly |
| ADV-EB-07 | get_base_state() called on a fresh (default-state) instance returns State.NORMAL == 0 (not null, not -1) |
| ADV-EB-08 | root.set("enemy_id", "") — empty string is a valid assignment; property returns "" not null |

**Dependencies:** Task 2 (primary tests).

**Success Criteria:** Adversarial file exists, all cases are red before implementation, each adversarial test has unique assertion name with `ADV-EB-*` prefix.

**Risks / Assumptions:**
- ADV-EB-01 depends on GDScript enum cast behavior at runtime; spec must document the expected behavior (clamp, wrap, or pass-through).

---

### Task 4 — Implementation (Core Simulation Agent)

**Objective:** Create `scripts/enemies/enemy_base.gd` such that all primary and adversarial tests pass.

**Input:**
- Spec document from Task 1.
- Primary test file from Task 2.
- Adversarial test file from Task 3.
- `scripts/asset_generation/load_assets.gd` lines 130–144 — exact property names used in `root.set(...)` calls.
- `scripts/enemy/enemy_state_machine.gd` — read for context only; do not modify.
- `scripts/player/base_physics_entity_3d.gd` — confirm no class_name collision.

**Expected Output:** `scripts/enemies/enemy_base.gd` implementing exactly:
- `class_name EnemyBase`
- `extends CharacterBody3D`
- `@export var enemy_id: String = ""`
- `@export var enemy_family: String = ""`
- `@export var mutation_drop: String = ""`
- `enum State { NORMAL, WEAKENED, INFECTED }`
- `var current_state: State = State.NORMAL`
- `func set_base_state(state: State) -> void`
- `func get_base_state() -> State`
- No _physics_process override on the base (leave to subclasses or scene-level scripts).
- No autoload dependencies.
- No import of EnemyStateMachine (the base is independent; coordination is done by higher-level scripts).

**Dependencies:** Tasks 1, 2, 3.

**Success Criteria:** `run_tests.sh` exits 0. All EB-* and ADV-EB-* tests pass. No existing test regressions. Script file is at the exact path `scripts/enemies/enemy_base.gd`.

**Risks / Assumptions:**
- The `scripts/enemies/` directory does not exist yet; the agent must create it.
- Assumption: No _physics_process is needed on the base. If the test suite or spec discovers a need, this must be escalated to Planner before adding it.

---

### Task 5 — GDScript Static QA (Static QA Agent)

**Objective:** Review `scripts/enemies/enemy_base.gd` for GDScript style conformance, type safety, and absence of warnings.

**Input:**
- `scripts/enemies/enemy_base.gd` from Task 4.
- `scripts/enemy/enemy_infection_3d.gd` and `scripts/enemy/enemy_state_machine.gd` — style reference.
- `CLAUDE.md` project coding conventions.

**Expected Output:** A written review report (inline ticket comment or escalation note) AND any corrected version of the script if issues are found. Issues to check:
1. All vars and parameters are statically typed.
2. No implicit Any types or untyped returns.
3. No GDScript warnings (unused vars, shadowed vars, narrowing casts).
4. File header comment follows the `# script_name.gd\n#\n# <description>` pattern.
5. No dead code, no TODO comments, no superfluous blank lines beyond project conventions.
6. `class_name EnemyBase` appears before `extends`.

**Dependencies:** Task 4.

**Success Criteria:** Either "no issues found" or corrected script is produced and `run_tests.sh` still exits 0 after any corrections.

**Risks:** GDScript `enum State` integer value access — spec must confirm the correct GDScript syntax for reading enum int values in tests (e.g., `EnemyBase.State.NORMAL` vs `EnemyBase.State.values()[0]`).

---

### Task 6 — Acceptance Criteria Gatekeeper (AC Gatekeeper Agent)

**Objective:** Verify every Acceptance Criterion is met by running the test suite and inspecting the implementation file.

**Input:**
- `scripts/enemies/enemy_base.gd` from Tasks 4–5.
- All test files from Tasks 2–3.
- `run_tests.sh` output.
- This ticket's Acceptance Criteria list.

**Expected Output:**
- Evidence that `run_tests.sh` exits 0.
- Per-AC sign-off: each bullet in the Acceptance Criteria section above is checked against test assertions or direct file inspection.
- If any AC is unmet: set ticket Stage to BLOCKED, document the gap in Blocking Issues.
- If all ACs met: set Stage to COMPLETE, move ticket to `project_board/5_milestone_5_procedural_enemy_generation/done/enemy_base_script.md`.

**Dependencies:** Tasks 4, 5.

**Success Criteria:** All ACs checked; ticket moves to COMPLETE or is escalated with precise gap description.

---

## Notes

- Output path is `scripts/enemies/enemy_base.gd` (`enemies/` plural, NOT `enemy/`).
- `scripts/asset_generation/load_assets.gd` already references `res://scripts/enemies/enemy_base.gd` and skips attaching if missing — no changes to that file are needed.
- The existing `EnemyInfection3D` hierarchy (`BasePhysicsEntity3D → CharacterBody3D`) is untouched. `EnemyBase` is a parallel hierarchy for procedurally generated scenes only.
- Tests must use `load("res://scripts/enemies/enemy_base.gd")` + CharacterBody3D.new() + set_script() pattern, NOT `EnemyBase.new()` directly — the latter requires the script to already be in the class cache before the test runner initializes.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
6

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PASSED — run_tests.sh 253/253 passed, 0 failed (2026-03-21)
- Static QA: PASSED — no CRITICAL, no WARNING, no INFO issues found
- Integration: PASSED — full test suite exits 0, zero regressions

## Blocking Issues
- None

## Escalation Notes
- None

## AC Sign-Off

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| `scripts/enemies/enemy_base.gd` exists and parses without errors | PASS | EB-LOAD-1: load() returns non-null GDScript |
| Script extends CharacterBody3D and has `class_name EnemyBase` | PASS | EB-LOAD-2 (is CharacterBody3D); ADV-EB-07 (source contains "extends CharacterBody3D"); ADV-EB-08 (source contains "class_name EnemyBase") |
| `@export var enemy_id: String` defaults to `""` | PASS | EB-EXPORT-1 |
| `@export var enemy_family: String` defaults to `""` | PASS | EB-EXPORT-2 |
| `@export var mutation_drop: String` defaults to `""` | PASS | EB-EXPORT-3 |
| `enum State { NORMAL, WEAKENED, INFECTED }` defined | PASS | EB-ENUM-1 through EB-ENUM-5; ADV-EB-06 (State.keys() returns Array) |
| `NORMAL == 0`, `WEAKENED == 1`, `INFECTED == 2` | PASS | EB-ENUM-2, EB-ENUM-3, EB-ENUM-4 |
| `var current_state: State = State.NORMAL` readable | PASS | EB-STATE-1 (defaults to 0) |
| `set_base_state(state: State) -> void` callable | PASS | EB-STATE-2, EB-STATE-3, EB-STATE-4 |
| `get_base_state() -> State` callable | PASS | EB-STATE-2 through EB-STATE-4; ADV-EB-05 (returns TYPE_INT) |
| Script attaches cleanly to CharacterBody3D headlessly | PASS | EB-LOAD-2 (no crash, no parse error) |
| `root.set("enemy_id", "foo")` sets the exported property | PASS | EB-EXPORT-4, EB-INTEGRATE-1, ADV-EB-02 |
| Existing test suite passes with zero regressions | PASS | run_tests.sh: 253 passed, 0 failed |

---

# NEXT ACTION

## Next Responsible Agent
Human

## Status
Proceed

## Reason
All 11 Acceptance Criteria verified by headless test execution (run_tests.sh 253/253 passed). Static QA found no issues. Ticket is COMPLETE. Moved to done/.
