# Spec: Headless tests for procedural combat-room generated enemies (M10-04)

Status: Approved for TEST_DESIGN handoff  
Ticket: `project_board/10_milestone_10_procedural_enemies_in_level/backlog/04_headless_tests_procedural_combat_enemies.md`  
Owner: Spec Agent  
Revision: 1

## Scope and Dependency Traceability

This specification defines deterministic, headless test contracts that validate combat rooms load generated enemy scenes without requiring full physics gameplay simulation.

Dependency alignment:
- `02_wire_generated_enemies_combat_rooms` (completed runtime wiring contract; authoritative for combat-room declaration + generated-scene integration).
- `01_spec_procedural_enemy_spawn_attack_loop` (foundational contract for declaration schema, anchor semantics, and deterministic validation hooks).

Authoritative baseline paths for test design:
- `scripts/system/run_scene_assembler.gd`
- `scenes/rooms/room_combat_*.tscn`
- `scenes/enemies/generated/*.tscn`
- `tests/scenes/levels/test_3d_scene.gd`
- `tests/run_tests.gd`

---

### Requirement HTPCE-R1 — Headless coverage target and combat-room selection contract

#### 1. Spec Summary
- **Description:** The test suite must include at least one deterministic headless test module that targets at least one combat room scene currently reachable through `RunSceneAssembler.POOL["combat"]`.
- **Constraints:** Coverage is minimum-one-room for ticket acceptance; selecting more than one room is allowed but not required.
- **Assumptions:** The combat pool remains the authoritative room source for this milestone.
- **Scope:** Scene selection logic and room fixture inputs used by new tests under `tests/`.

#### 2. Acceptance Criteria
- AC-HTPCE-R1.1: At least one test case resolves a concrete combat room path from the assembler combat pool contract.
- AC-HTPCE-R1.2: The resolved room path is loaded as a `PackedScene` in headless mode without requiring editor/manual interaction.
- AC-HTPCE-R1.3: The selected room fixture is stable (hard-coded in test with explicit path comment or discovered via deterministic contract helper).
- AC-HTPCE-R1.4: Test file header includes the exact ticket path string required by ticket AC.

#### 3. Risk & Ambiguity Analysis
- **Risk:** If pool contents change later, hard-coded room selection can become stale.
- **Risk:** Dynamic scene discovery can hide regressions if fallback selection logic is too permissive.
- **Ambiguity resolved:** Ticket requires at least one combat room, not all combat rooms, for acceptance.

#### 4. Clarifying Questions
- Should this ticket require full pool-wide room coverage now?  
  Resolved for this ticket: no; minimum one deterministic combat room is mandatory.

---

### Requirement HTPCE-R2 — Generated enemy declaration assertion contract

#### 1. Spec Summary
- **Description:** Headless tests must assert that the targeted combat room(s) expose runtime-spawn declarations that resolve to generated enemy scene paths and/or deterministic `enemy_family` contracts.
- **Constraints:** Tests must validate procedural generated-enemy wiring; they must not rely on legacy embedded enemy nodes as authoritative evidence.
- **Assumptions:** Room declaration and runtime helper seams from M10-02 are present and callable from tests.
- **Scope:** Assertions on declaration payload shape, generated path validity, and family-level mapping invariants.

#### 2. Acceptance Criteria
- AC-HTPCE-R2.1: Test asserts each checked declaration entry has required identity fields (`enemy_family` or equivalent canonical family key).
- AC-HTPCE-R2.2: Test asserts generated scene path value is under generated root and has `.tscn` resource extension.
- AC-HTPCE-R2.3: Test asserts generated scene path exists and is loadable (`ResourceLoader.exists`/equivalent deterministic check).
- AC-HTPCE-R2.4: If implementation resolves by family instead of explicit path, test asserts deterministic family-to-generated-scene resolution contract.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Runtime can satisfy family declaration while generated path is broken, causing false confidence if existence is not asserted.
- **Risk:** Family-only assertions can be too weak if scene path validation is omitted.
- **Ambiguity resolved:** Both path-level and family-level assertions are valid as long as deterministic and traceable to generated assets.

#### 4. Clarifying Questions
- Should tests require both family and path assertions in every case?  
  Resolved for this ticket: at least one deterministic generated-path assertion is required; family assertions are also required where family contract is the authoritative seam.

---

### Requirement HTPCE-R3 — Headless execution limits and skip policy

#### 1. Spec Summary
- **Description:** Tests must follow existing headless harness patterns to avoid hangs and unsupported full-physics simulation while still asserting meaningful runtime contracts.
- **Constraints:** Skips are allowed only for explicitly unsupported harness behavior and must include documented reason strings tied to deterministic conditions.
- **Assumptions:** Existing patterns in `tests/scenes/levels/test_3d_scene.gd` are the project-approved reference.
- **Scope:** Frame pumping bounds, deferred-call handling, skip criteria, and anti-hang behavior in new test modules.

#### 2. Acceptance Criteria
- AC-HTPCE-R3.1: Test runtime uses bounded waits/frame advancement; no unbounded polling loops.
- AC-HTPCE-R3.2: Any skip is conditioned on explicit, deterministic precondition checks (not broad environment checks).
- AC-HTPCE-R3.3: Skip message states why assertion is unsupported in headless harness and identifies fallback assertion retained.
- AC-HTPCE-R3.4: Core contract assertions (generated room/declaration validity) remain non-skipped in default CI path.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Overuse of skips can silently convert hard regressions into non-actionable pass results.
- **Risk:** Unbounded frame waits can deadlock `godot --headless` and violate CI timeout requirements.
- **Ambiguity resolved:** Skip behavior is narrow and declarative, never a substitute for required deterministic assertions.

#### 4. Clarifying Questions
- Can tests skip all spawn assertions if physics hooks are unavailable?  
  Resolved for this ticket: no; only physics-dependent behavior may be skipped, not declaration/path contract assertions.

---

### Requirement HTPCE-R4 — Malformed input and adversarial behavior contract

#### 1. Spec Summary
- **Description:** Optional adversarial tests define expected behavior for malformed combat-room spawn inputs (missing markers, empty spawn lists, invalid `res://` paths).
- **Constraints:** Behavior must be fail-closed per spawn entry and non-crashing for room/run assembly unless dependency spec explicitly mandates hard failure.
- **Assumptions:** M10 runtime contract tolerates partial spawn failures with actionable diagnostics.
- **Scope:** Optional second test module under `tests/` targeting malformed declaration scenarios.

#### 2. Acceptance Criteria
- AC-HTPCE-R4.1: Missing spawn markers produce deterministic fallback or explicit structured failure result per current runtime contract.
- AC-HTPCE-R4.2: Empty spawn declaration list yields zero spawned enemies and no process crash.
- AC-HTPCE-R4.3: Invalid generated scene path (`res://...` non-existent) yields defined error/warning and skips only the invalid spawn entry.
- AC-HTPCE-R4.4: Adversarial expectations are deterministic and independently verifiable in headless CI.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Undefined malformed behavior can lead to flaky tests or implementation/test disagreement.
- **Risk:** Hard-crash expectations for malformed input can create fragile content pipelines.
- **Ambiguity resolved:** For this ticket, malformed spawn inputs are treated as recoverable per-entry failures unless upstream contract is explicitly hard-fail.

#### 4. Clarifying Questions
- Should invalid `res://` paths hard-fail the entire run for immediate visibility?  
  Resolved for this ticket: no; fail-closed per entry with explicit diagnostic is the required behavior.

---

### Requirement HTPCE-R5 — Test runner integration and traceability

#### 1. Spec Summary
- **Description:** New tests must be discoverable and executed by repository-standard test entrypoints, including registration in `tests/run_tests.gd` following project conventions.
- **Constraints:** Test naming and grouping must avoid accidental exclusion from headless suite.
- **Assumptions:** `tests/run_tests.gd` remains explicit-registration based for the targeted suite.
- **Scope:** Test file placement, registration wiring, and ticket/spec trace comments.

#### 2. Acceptance Criteria
- AC-HTPCE-R5.1: New test module path is under `tests/` and follows established naming conventions.
- AC-HTPCE-R5.2: `tests/run_tests.gd` includes registration entry for new module(s), matching existing patterns.
- AC-HTPCE-R5.3: New tests include trace comments mapping each major assertion to `HTPCE-R*` requirements.
- AC-HTPCE-R5.4: Test header comment includes required ticket path literal.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Unregistered tests create false CI confidence.
- **Risk:** Missing traceability slows AC gate review and weakens defect triage.
- **Ambiguity resolved:** Registration in `tests/run_tests.gd` is mandatory, not optional discovery.

#### 4. Clarifying Questions
- Can this ticket rely on implicit test discovery only?  
  Resolved for this ticket: no; explicit registration is required.

---

### Requirement HTPCE-R6 — Non-functional requirements (determinism, robustness, CI gate)

#### 1. Spec Summary
- **Description:** Headless tests must be deterministic, bounded, and robust to malformed content while preserving strict CI acceptance gate behavior.
- **Constraints:** Acceptance gate remains `timeout 300 ci/scripts/run_tests.sh` exit 0.
- **Assumptions:** Unrelated external failures are treated as blockers and documented explicitly by downstream agents.
- **Scope:** End-to-end validation obligations for TEST_DESIGN, TEST_BREAK, and implementation handoff.

#### 2. Acceptance Criteria
- AC-HTPCE-R6.1: Repeated runs with identical repository state produce identical test outcomes (no nondeterministic pass/fail flips).
- AC-HTPCE-R6.2: No new test introduces unbounded wait or heavy physics dependency that increases hang risk in headless CI.
- AC-HTPCE-R6.3: Malformed declaration/path cases produce stable, defined assertions (graceful handling) rather than nondeterministic crashes.
- AC-HTPCE-R6.4: `timeout 300 ci/scripts/run_tests.sh` is the required final validation command and must exit 0 for ticket closure.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Existing unrelated flaky tests can obscure ticket-specific signal.
- **Risk:** Determinism can degrade if tests depend on timing jitter or global mutable state.
- **Ambiguity resolved:** Unrelated failures do not change this ticket’s acceptance requirement; they must be documented as explicit blockers when present.

#### 4. Clarifying Questions
- If full suite fails for unrelated reasons, can ticket still close?  
  Resolved for this ticket: no; closure requires explicit green full-suite evidence or blocked state documentation by downstream agents.

---

## Acceptable Skip Criteria (Binding for Test Designer)

Skips are allowed only when all conditions are met:
1. The skipped assertion is strictly physics-simulation dependent and cannot be deterministically validated in current headless harness.
2. A non-skipped assertion still validates declaration/path/family contract for the same scenario.
3. Skip branch includes explicit reason string naming missing harness capability.
4. Skip condition is deterministic (based on checked runtime capability/seam), not timing or random behavior.

Not allowed:
- Skipping declaration schema validation.
- Skipping generated scene path existence/loadability checks.
- Blanket file-level skip due to “headless instability.”

## Malformed Input Expected Behavior Matrix (Binding)

- Missing enemy spawn markers: deterministic fallback spawn contract or explicit defined failure object/warning (non-crash).
- Empty spawn declarations: zero spawn outcome, test asserts stable no-crash behavior.
- Invalid generated scene path: per-entry skip/failure with explicit diagnostic containing room and offending path.
- Unknown enemy family in declaration: deterministic no-spawn outcome with explicit warning and continued room assembly.

## AC Mapping to Ticket Acceptance Criteria

- Ticket AC-1 (new tests under `tests/` for at least one combat room + generated path assertions): HTPCE-R1, HTPCE-R2, HTPCE-R5.
- Ticket AC-2 (follow skip/physics patterns): HTPCE-R3.
- Ticket AC-3 (`timeout 300 ci/scripts/run_tests.sh` exits 0): HTPCE-R6.
- Ticket AC-4 (header comment includes ticket path): HTPCE-R1.4, HTPCE-R5.4.
