# TICKET: scene_state_machine
Title: Scene state machine
Project: blobert
Created By: Human
Created On: 2026-03-06T00:00:00Z

---

## Description

Epic: Milestone 4 – Prototype Level  
Status: Backlog

Introduce a reusable, pure-logic scene state machine that represents different feature configurations of the 3D main scene (e.g. baseline, infection loop demo, enemy playtest) so we can toggle features via state instead of creating new scenes for each variant.

---

## Acceptance Criteria

- [ ] A `SceneStateMachine` pure logic module exists under `scripts/` (no Node or scene dependencies) with a small, well-defined set of canonical scene states and deterministic, event-driven transitions.
- [ ] Primary and adversarial test suites under `tests/` cover allowed transitions, no-op combinations, determinism, and per-instance isolation for the scene state machine, and are wired into `tests/run_tests.gd`.
- [ ] The main 3D playable scene uses the scene state machine via a controller or manager script to switch between at least two concrete configurations (e.g. baseline movement vs. infection-loop-enabled variant) without duplicating the scene.
- [ ] Key feature systems in the 3D scene (e.g. infection loop, enemies, or HUD slices) are gated on scene state in a way that is headless-testable where reasonable and preserves existing passing tests.
- [ ] No new top-level `.tscn` scenes are introduced solely to represent feature variants that can be expressed via scene state; the state machine + configuration is the primary mechanism for toggling between these variants.

---

## Dependencies

- None

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE

## Revision
9

## Last Updated By
Engine Integration Agent

## Validation Status
- Tests: Full suite run — 253 passed, 0 failed (2026-03-27). All 7 integration tests in `test_scene_state_integration_3d.gd` pass: `scene_state_3d_has_variant_controller`, `scene_state_3d_controller_has_get_state_machine`, `scene_state_3d_controller_returns_state_machine`, `scene_state_3d_initial_state_baseline`, `scene_state_3d_switch_variants_starts_baseline`, `scene_state_3d_switch_variants_infection_demo`, `scene_state_3d_switch_variants_back_to_baseline`.
- Static QA: Not Run
- Integration: COMPLETE — `SceneVariantController` node (type: Node) wired to `scripts/system/scene_variant_controller_3d.gd` is a direct child of root in `scenes/levels/sandbox/test_movement_3d.tscn`. Controller owns a `SceneStateMachine` instance and exposes `get_state_machine()`, `select_baseline()`, and `select_infection_demo()`. Two concrete configurations (BASELINE and INFECTION_DEMO) are driveable via the API without scene duplication.
- AC Coverage:
  - AC-1 (SceneStateMachine pure logic module): COVERED — `scripts/system/scene_state_machine.gd` exists, extends RefCounted (no Node), 3 canonical states, deterministic event-driven transitions.
  - AC-2 (primary + adversarial test suites wired): COVERED — primary suite (9 tests) and adversarial suite (6 tests) pass; auto-discovered by `run_tests.gd`.
  - AC-3 (main 3D scene uses SSM for 2+ configurations without scene duplication): COVERED — `test_scene_state_integration_3d.gd` passes (7 tests). No new .tscn scenes introduced for variants.
  - AC-4 (key feature systems gated on state, headless-testable): PARTIAL — controller comment acknowledges feature system gating is not yet wired. `get_config()` returns correct flag maps per state (BASELINE/INFECTION_DEMO/ENEMY_PLAYTEST) but no runtime scene nodes are currently toggled based on state. No test asserts feature system gating. Gatekeeper Agent should evaluate whether this requires additional implementation before COMPLETE.
  - AC-5 (no new top-level .tscn scenes for variants): COVERED — no new scenes introduced.

## Blocking Issues
None

## Escalation Notes
- AC-4 gap: `scene_variant_controller_3d.gd` does not yet apply `get_config()` to runtime nodes (enemies, infection handler visibility). This is a known gap flagged in the controller's own comment. The integration test does not assert this behavior. Gatekeeper Agent to decide if this blocks COMPLETE or if a separate ticket is appropriate.

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Status
Proceed

## Reason
All tests pass (253/253 including all 7 integration tests). Engine integration wiring is structurally complete: SceneVariantController node exists in test_movement_3d.tscn, owns a SceneStateMachine, and exposes the full variant-selection API. AC-4 feature system gating is not yet exercised at runtime — Gatekeeper Agent must determine if this is a blocking gap or acceptable scope reduction given no failing tests assert it.
