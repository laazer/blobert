# TICKET: sandbox_scene_legacy_external_enemy_visuals

Title: Duplicate `test_movement_3d` sandbox with legacy third-party enemy mesh for devlog capture

## Description

`scenes/levels/sandbox/test_movement_3d.tscn` wires each `EnemyInfection3D` instance with `model_scene` pointing at generated GLBs under `res://assets/enemies/generated_glb/`. The base scene `scenes/enemy/enemy_infection_3d.tscn` still ships a **default `EnemyVisual`** (`res://assets/Models/gobot/model/gobot.glb`—third-party / external-game style asset, not a bespoke blobert mesh) when `model_scene` is left unset (`enemy_infection_3d.gd` only swaps the visual when `model_scene != null`).

For devlog GIFs that should match footage from before generated enemy art landed—without reverting git history—add a **duplicate** sandbox level that is otherwise the same (floor, spawn, `InfectionInteractionHandler`, `GameUI`, player, enemy positions, `mutation_drop` values, physics flags) but **does not** assign `model_scene` on the four enemies (remove overrides so that default external mesh is used), and drop the now-unused `ext_resource` entries for the four generated GLBs from that copy only.

Keep `project.godot` `run/main_scene` on `test_movement_3d.tscn`; this duplicate is opened manually or via **Run Current Scene** when recording.

## Acceptance Criteria

- New scene file under `scenes/levels/sandbox/` (name TBD, e.g. `test_movement_3d_legacy_enemy_visual.tscn`) loads without errors and instantiates cleanly in headless/editor.
- Enemy nodes match the live sandbox’s count, names, transforms, and `mutation_drop` strings; `model_scene` is unset on each so visuals match the default `enemy_infection_3d.tscn` packaged mesh.
- No regression: existing tests and `run/main_scene` still target `test_movement_3d.tscn` unless a test explicitly needs to assert the new scene (optional one-line instantiate smoke test is fine; not required).

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce formal spec (requirement IDs, file path, edge cases) from ticket + scene contracts | Spec Agent | This ticket; `scenes/levels/sandbox/test_movement_3d.tscn`; `scenes/enemy/enemy_infection_3d.tscn`; `scripts/enemy/enemy_infection_3d.gd` | `project_board/specs/sandbox_scene_legacy_external_enemy_visuals_spec.md` | — | Spec names the new `.tscn` path; lists exact nodes/properties to match vs omit; states `project.godot` unchanged | Assumes duplicate is a verbatim structural copy minus four `model_scene` overrides and four GLB `ext_resource` lines |
| 2 | Author tests per spec (optional one-line packed-scene load smoke) | Test Designer Agent | Spec from task 1 | New/updated `tests/**/*.gd` only if spec demands | 1 | Failing tests exist before implementation if any new behavior asserted; else documented N/A | AC allows zero new tests; spec should not over-require |
| 3 | Adversarial review of spec + tests | Test Breaker Agent | Spec + test files from 1–2 | Gap list or test hardening recommendations | 2 | Blind spots documented or resolved | Low risk for scene-only change |
| 4 | Add duplicate sandbox `.tscn`: same tree as `test_movement_3d.tscn` except remove `model_scene` on four enemy instances and remove unused GLB `ext_resource` entries | Implementation Generalist Agent | Spec; source `test_movement_3d.tscn` | New scene under `scenes/levels/sandbox/` | 3 | `timeout 300 godot -s tests/run_tests.gd` exit 0; opening new scene in editor/headless shows no load errors | Duplicated `unique_id` values may need Godot re-save; root `node name` should differ from `TestMovement3D` for clarity |
| 5 | Validate AC and workflow closure prep | Static QA / Acceptance Criteria Gatekeeper Agent (or human per board) | Implemented scene + full suite | Updated ticket validation bullets; Stage toward INTEGRATION/COMPLETE per policy | 4 | `run/main_scene` still `test_movement_3d.tscn`; enemies use default gobot visual when `model_scene` unset | Gatekeeper agent availability per autopilot config |

## Dependencies

- None required

## Specification

Formal spec (requirements **SLEEV-1**–**SLEEV-5**, traceable to acceptance criteria):  
`project_board/specs/sandbox_scene_legacy_external_enemy_visuals_spec.md`

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Pass — `timeout 300 ci/scripts/run_tests.sh` exit 0 (2026-04-05); output ends with `=== ALL TESTS PASSED ===`. AC1–AC2 and the testable parts of AC3 are covered by `tests/scenes/levels/test_legacy_enemy_visual_sandbox_scene.gd` (SLEEV-1 packed load + `Node3D` root, SLEEV-2 tree/order/respawn line parity vs `test_movement_3d.tscn`, SLEEV-3 no forbidden `generated_glb/*_animated_00.glb` ext_resources + no `model_scene =` on four enemies + `mutation_drop`/transform/`physics_interpolation_mode` + runtime `model_scene == null`, ADV single legacy basename, loadable non-empty `run/main_scene`).
- Static QA: Gatekeeper cross-check — ticket AC vs `project.godot` vs spec SLEEV-4.2; no edits to Description/AC text.
- Integration: N/A — AC satisfied by automated scene load/instantiate and property assertions; no separate in-editor manual step required beyond what tests exercise.
- **`run/main_scene` vs ticket prose (SLEEV-4.2 resolution, explicit evidence):** `project.godot` has `run/main_scene="res://scenes/levels/procedural_run.tscn"` (not `res://scenes/levels/sandbox/test_movement_3d.tscn`). Ticket Description § “Keep `project.godot` `run/main_scene` on `test_movement_3d.tscn`” and AC3’s “`run/main_scene` still target `test_movement_3d.tscn`” therefore **do not match the repo baseline** as of this closure. Per spec **SLEEV-4.2** (`sandbox_scene_legacy_external_enemy_visuals_spec.md`), closure is allowed when equality to `test_movement_3d.tscn` is **not** asserted and drift is documented. **Test contract:** `test_sleev_4_main_scene_not_legacy_duplicate()` documents deferral to ADV-PRS-19 / repo entry policy and asserts **SLEEV-4.1** only (`run/main_scene` must not reference `test_movement_3d_legacy_enemy_visual.tscn`). This ticket’s change set did **not** repoint `run/main_scene` to the new legacy sandbox.

## Blocking Issues
- None (SLEEV-4.2 documented; not silently claiming `test_movement_3d.tscn` as `run/main_scene`).

## Escalation Notes
- If product intent is strictly `run/main_scene` == `test_movement_3d.tscn`, that is a separate repo-policy / Planner follow-up (out of scope for falsifying this ticket’s Validation Status).

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "action": "ticket_complete",
  "ticket_path": "project_board/maintenance/done/sandbox_scene_legacy_external_enemy_visuals.md",
  "notes": "Archive or link devlog recording workflow; optional follow-up if main_scene should match ticket prose."
}
```

## Status
Complete

## Reason
All acceptance criteria are mapped to automated tests or explicitly documented per SLEEV-4.2; `run/main_scene` evidence recorded honestly (`procedural_run.tscn`). Gatekeeper re-ran full suite (exit 0). Stage COMPLETE; ticket moved to `maintenance/done/`.
