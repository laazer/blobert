Title:
Eye Shape & Pupil Configuration

Description:
Add a structured eye system to the enemy editor. Users can select from a set of predefined eye shapes (circle, oval, slit, square) and optionally enable a pupil with its own shape variation. Currently the eye is a fixed sphere, making all enemies feel identical at a glance. This ticket replaces that with a configurable eye component backed by the existing properties panel.

Acceptance Criteria:
- At least 4 eye shapes are selectable from the UI: circle, oval, slit, square
- Pupil visibility is toggleable (on/off); default is off
- When pupils are enabled, at least 3 pupil shape options are available: dot, slit, diamond
- Eye shape and pupil changes are reflected immediately in the 3D preview
- Eye color continues to be driven by the existing color system (no new color controls here)
- All eye/pupil settings serialize correctly to enemy config JSON

Scope Notes:
- No eye animation (blinking, tracking) — deferred to M26
- No per-eye asymmetry controls; both eyes share the same shape/pupil settings
- Eye color is not owned by this ticket

---

## Execution Plan

### Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write spec for eye shape + pupil system | Spec Agent | This ticket; checkpoint log at `project_board/checkpoints/M25-ESPS/run-2026-04-14T18-00-00Z-planning.md`; existing `animated_build_options.py` patterns | `project_board/specs/eye_shape_and_pupil_system_spec.md` with: control key names, valid option sets, serialization contract, per-slug scope, geometry strategy for each shape variant, pupil mesh placement strategy | None | Spec covers all 6 AC; `python ci/scripts/spec_completeness_check.py <spec_path> --type generic` passes; key names, valid values, and defaults are fully enumerated | Risk: scope of which slugs get geometry effects is ambiguous (see checkpoint log). Assumption: `eye_shape` + `pupil_enabled` + `pupil_shape` are universal controls declared for all slugs, geometry effects wired only where eye mesh objects exist. |
| 2 | Define Python build controls — declare `eye_shape`, `pupil_enabled`, `pupil_shape` in `animated_build_options.py` | Implementation Backend Agent | Spec (Task 1); `asset_generation/python/src/utils/animated_build_options.py`; existing `_ANIMATED_BUILD_CONTROLS` pattern | New `_eye_shape_pupil_control_defs()` helper; controls added to all animated slugs via `animated_build_controls_for_api()`; `options_for_enemy()` validates and coerces the three new keys; `_defaults_for_slug()` emits defaults | Task 1 | `animated_build_controls_for_api()["spider"]` includes `eye_shape`, `pupil_enabled`, `pupil_shape`; `options_for_enemy("spider", {})` returns correct defaults; `options_for_enemy("spider", {"eye_shape": "INVALID"})` falls back to `"circle"`; all existing tests still pass | Assumption: pupil_enabled is `bool` type, not int. `_coerce_and_validate` must handle `bool` control type (already exists in `AnimatedBuildControlDef` but not yet in `_coerce_and_validate`). |
| 3 | Implement Python geometry builder — apply eye shape and pupil mesh to enemy eye parts | Implementation Backend Agent | Spec (Task 1); Task 2 controls; `asset_generation/python/src/enemies/animated_spider.py` (`build_mesh_parts`, eye loop); `animated_slug.py` (stalk-eye loop); `animated_claw_crawler.py` (peripheral_eyes loop); `blender_utils.py` (`create_sphere`, `create_box`, `create_cylinder`) | Updated `build_mesh_parts` methods (or shared helper) in spider, slug, claw_crawler; new `create_eye_mesh(shape, scale)` helper in `blender_utils.py` or a new `eye_geometry.py` module; optional pupil mesh creation per eye | Task 2 | Spider with `eye_shape="square"` produces `create_box` calls for each eye; `pupil_enabled=True` causes a pupil mesh placed on each eye surface; `pupil_enabled=False` (default) produces no pupil geometry; existing mesh part counts for default `eye_shape="circle"` are unchanged | Risk: pupil mesh placement requires computing the front-facing surface point of the eye sphere — must reuse `_point_on_ellipsoid_surface` pattern from spider. Risk: imp, spitter, carapace_husk have no explicit eye sub-mesh; controls are declared but geometry effects not yet wired for those slugs (acceptable per scope note). |
| 4 | Python tests — unit tests for control declarations, coercion, and options serialization | Test Designer Agent / Implementation Backend Agent | Spec (Task 1); Task 2 implementation; `asset_generation/python/tests/utils/test_animated_build_options.py` as reference | New test file `asset_generation/python/tests/utils/test_eye_shape_pupil_controls.py`; tests cover: all slugs declare the three new keys; default values match spec; invalid `eye_shape` string falls back; `pupil_enabled` bool coercion; `pupil_shape` fallback; round-trip JSON parse | Tasks 2–3 | `bash .lefthook/scripts/py-tests.sh` passes for the new test file; diff-cover preflight for modified `.py` files passes | Assumption: test file uses the `src.` prefix import pattern matching existing utils tests. |
| 5 | Python tests — geometry builder tests for eye shape and pupil mesh creation | Test Designer Agent / Implementation Backend Agent | Spec (Task 1); Task 3 implementation; `asset_generation/python/tests/enemies/test_animated_enemy_classes.py`; blender stub pattern (`conftest.py`) | New test file `asset_generation/python/tests/enemies/test_eye_shape_pupil_geometry.py`; tests verify: `build_mesh_parts` with `eye_shape="square"` calls `create_box` (via stub); `eye_shape="circle"` preserves existing sphere behavior; `pupil_enabled=True` increases part count by 1 per eye; `pupil_enabled=False` does not add pupil parts | Task 3 | `bash .lefthook/scripts/py-tests.sh` passes; diff-cover preflight passes | Risk: blender stubs may need updating to cover `create_box` being called in eye geometry path. Confirm stub already covers `create_box`. |
| 6 | Frontend — add `eye_shape`, `pupil_enabled`, `pupil_shape` to `BuildControls.tsx` with conditional disabling | Implementation Frontend Agent | Spec (Task 1); Task 2 backend output (the three new controls flow through existing `/api/meta/enemies` → `AnimatedBuildControlDef[]` path); `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx`; `asset_generation/web/frontend/src/types/index.ts` | Updated `BuildControls.tsx` `buildControlDisabled` logic: `pupil_shape` and any pupil-related controls are disabled when `pupil_enabled` is `false` or absent; `bool` type controls handled by `ControlRow` (verify or add handler); no new tab required — controls appear inline with existing non-float controls | Tasks 2, 3 | Frontend `ControlRow` renders a checkbox/toggle for `pupil_enabled`; `pupil_shape` dropdown is disabled when `pupil_enabled` is false; changing `eye_shape` in the UI calls `setAnimatedBuildOption` and triggers a preview regeneration (existing mechanism); no TypeScript compile errors | Assumption: `AnimatedBuildControlDef` `bool` variant already declared in `types/index.ts` (confirmed present). `ControlRow` in `BuildControlRow.tsx` may need a `bool` branch — check if one exists. |
| 7 | Frontend tests — Vitest unit tests for conditional disabling logic | Test Designer Agent / Implementation Frontend Agent | Task 6 implementation; `asset_generation/web/frontend/src/components/Preview/BuildControls.previewSync.test.tsx` and `BuildControlRow.test.tsx` as reference | New or extended test file `asset_generation/web/frontend/src/components/Preview/BuildControls.eyeShape.test.tsx`; tests cover: `pupil_shape` row disabled when `pupil_enabled=false`; `pupil_shape` row enabled when `pupil_enabled=true`; `eye_shape` control renders correct options list | Task 6 | `cd asset_generation/web/frontend && npm test` passes for new test file | Assumption: tests use the existing Vitest + React Testing Library pattern matching adjacent test files in the same directory. |

### Notes
- Tasks 2 and 3 are both Python-backend and can be sequenced in one agent run (backend implementation agent handles both).
- Tasks 4 and 5 can also be sequenced in one agent run after Tasks 2–3 complete.
- Task 6 (frontend) can begin once Task 2 is complete (the API response shape is the only frontend compile dependency; Task 3 geometry is not a frontend compile dependency).
- Task 7 is immediately sequenced after Task 6.
- Spec exit gate: orchestrator must run `python ci/scripts/spec_completeness_check.py <spec_path> --type generic` after Task 1 before advancing to TEST_DESIGN.
- Diff-cover preflight: orchestrator must run `bash ci/scripts/diff_cover_preflight.sh` after Tasks 2–3 implementation before advancing.
- The three new build option keys (`eye_shape`, `pupil_enabled`, `pupil_shape`) must serialize correctly to/from `options_for_enemy()` round-trip (covered by Task 4 tests).

---

## WORKFLOW STATE

- **Stage:** TEST_BREAK
- **Revision:** 4
- **Last Updated By:** Test Designer Agent
- **Next Responsible Agent:** Test Breaker Agent
- **Status:** Proceed
