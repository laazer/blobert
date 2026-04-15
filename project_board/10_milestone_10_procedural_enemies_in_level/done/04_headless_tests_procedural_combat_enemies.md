# TICKET: 04_headless_tests_procedural_combat_enemies

Title: Headless tests — procedural combat rooms contain loadable generated enemies
Project: milestone_10_procedural_enemies_in_level
Created By: Human
Created On: 2026-04-15

## Description

Add focused tests that **do not require** a full physics playthrough where the harness cannot support it. Prefer: load combat room `PackedScene`, find spawn roots or deferred spawn logic, assert expected generated enemy scene paths or `enemy_family` exports, and register in `tests/run_tests.gd` per existing patterns.

Optional second file: adversarial tests for missing markers, empty spawn lists, or invalid `res://` paths (must fail gracefully or error in a defined way).

## Acceptance Criteria

- New test module(s) under `tests/` exercise at least one combat room scene used in `RunSceneAssembler.POOL["combat"]` together with generated enemy scene paths.
- Tests follow project skip/physics patterns from `tests/scenes/levels/test_3d_scene.gd` where needed to avoid hangs.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.
- Tests reference this ticket path in a header comment: `project_board/10_milestone_10_procedural_enemies_in_level/backlog/04_headless_tests_procedural_combat_enemies.md`.

## Dependencies

- `02_wire_generated_enemies_combat_rooms` — stable scene paths and spawn contract to assert against
- `01_spec_procedural_enemy_spawn_attack_loop` (soft — tests should align with spec IDs if present)

## Functional and Non-Functional Specification

- `project_board/specs/headless_tests_procedural_combat_enemies_spec.md` (requirements `HTPCE-R1..R6`, skip policy, malformed-input matrix, AC traceability)

---

## Planning Decomposition

# Project: Headless Procedural Combat Enemy Tests
**Description:** Define, implement, harden, and validate deterministic headless tests that prove procedural combat rooms contain loadable generated enemies without requiring unsupported full-physics playthroughs.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author formal testability specification and requirement IDs for this ticket using existing M10 contracts. | Spec Agent | Ticket AC/dependencies, `02_wire_generated_enemies_combat_rooms`, `01_spec_procedural_enemy_spawn_attack_loop`, existing room/runtime contracts under `tests/system/`. | Spec document in `project_board/specs/` with requirement IDs, deterministic pass/fail rules, and explicit handling of headless limitations. | None | Spec maps every AC to objective checks and names required fixtures/rooms. | Risk: ambiguous authority between scene-path and `enemy_family` assertions. Assumption: both are valid if deterministic and traceable to spec IDs. |
| 2 | Write primary headless contract tests for at least one combat room in `RunSceneAssembler.POOL["combat"]`, including registration in `tests/run_tests.gd`. | Test Designer Agent | Approved spec, selected combat room scenes, existing test harness patterns (`tests/scenes/levels/test_3d_scene.gd`). | New deterministic test module(s) under `tests/` with ticket header reference and spec-trace comments. | 1 | New tests fail pre-implementation or pass if already satisfied; no hangs; test modules are discoverable by runner. | Risk: room load path or deferred spawn timing may be nondeterministic. Assumption: harness can gate via bounded frame pumping and skips only when spec-authorized. |
| 3 | Add adversarial headless tests for malformed spawn declarations and invalid generated enemy references. | Test Breaker Agent | Spec and primary tests from Task 2. | Additional adversarial test file(s) validating defined graceful-failure behavior for missing markers, empty spawn lists, invalid `res://` paths. | 2 | Adversarial tests expose mutation gaps while remaining deterministic in headless CI. | Risk: current behavior may be undefined for malformed inputs. Assumption: spec will define fail-closed or explicit error expectation per case. |
| 4 | Implement minimal runtime/test-harness adjustments needed to satisfy new contract and adversarial suites without introducing physics-only coupling. | Engine Integration Agent | Failing tests from Tasks 2-3, existing combat-room spawn pipeline and assembler code. | Code changes limited to production/test seam areas required for deterministic load/assert behavior; no one-off room scripts. | 3 | All ticket tests pass locally; behavior remains aligned with M8 attack plumbing and M10 spawn contract. | Risk: fixing determinism can regress existing room-template tests. Assumption: no contractual rollback of procedural canonical path from ticket 02. |
| 5 | Execute static QA and full suite validation with explicit evidence capture. | Generalist Agent | Updated code/tests, project test commands. | Validation evidence for `timeout 300 ci/scripts/run_tests.sh` plus any focused suite(s), with failures triaged or resolved. | 4 | Command exits 0 and ticket Validation Status can cite objective outputs. | Risk: unrelated flaky tests can mask ticket signal. Assumption: only ticket-caused failures block advancement; unrelated failures are documented with proof. |
| 6 | Perform acceptance gate and close ticket lifecycle transition when AC evidence is complete. | acceptance-criteria-gatekeeper | Ticket state, validation evidence, spec/test traceability. | Ticket advanced to terminal state per workflow if all ACs met, with complete Validation Status narrative. | 5 | ACs are explicitly proven, stage transition valid, and handoff path unambiguous. | Risk: evidence gaps between spec IDs and final assertions. Assumption: each AC must cite concrete test names and command outcomes before closure. |

## Notes
- Tasks are sequential and independently executable once dependencies are met.
- No human clarification requested in autonomous mode; assumptions are logged in scoped checkpoint per protocol.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PASS (`timeout 300 godot --headless -s tests/run_tests.gd` exit 0 on 2026-04-15 after Stage 5b reviewer fixes).
- Tests: PASS (`timeout 300 ci/scripts/run_tests.sh` exit 0 on 2026-04-15 after Stage 5b reviewer fixes).
- Static QA: PASS (ReadLints clean for `tests/system/test_headless_procedural_combat_enemies_contract.gd`).
- AC evidence: `tests/system/test_headless_procedural_combat_enemies_contract.gd` is a new `tests/` module exercising combat rooms from `RunSceneAssembler.POOL["combat"]` and generated enemy scene-path resolution/loadability (`HTPCE-T-01..T-04`), and includes the required ticket-path header comment.
- AC evidence: headless safety/skip pattern intent is explicitly encoded by bounded frame pumping with strict upper bound checks (`HTPCE-T-05`) to avoid unsupported full-physics hangs.
- Integration: Ticket ACs are fully evidenced by automated tests and documented assertions; no additional runtime-manual checklist item is required by this ticket's AC set.

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
{
  "ticket_path": "project_board/10_milestone_10_procedural_enemies_in_level/done/04_headless_tests_procedural_combat_enemies.md",
  "closure_state": "COMPLETE",
  "evidence_status": "validated"
}
```

## Status
Proceed

## Reason
All acceptance criteria are explicitly evidenced by documented headless test coverage, passing full-suite commands, and static QA; ticket lifecycle state and location are now consistent for terminal closure.
