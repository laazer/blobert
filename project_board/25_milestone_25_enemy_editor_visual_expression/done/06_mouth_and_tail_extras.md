Title:
Mouth Extra & Tail Extra Configuration

Description:
Add two new optional anatomical extras to the enemy editor: a configurable mouth/faceplate geometry on the head zone and a tail appendage on the body zone. Like the eye/pupil system (M25-01), each extra is declared as build controls for all animated slugs but geometry effects are wired only to the enemy classes that have explicit head/body mesh objects.

Currently all enemies share a featureless blob head and no rear appendage, making body silhouettes indistinct. A toggled mouth (smile, grimace, flat, fang, beak) and a toggled tail (spike, whip, club, segmented, curled) let designers quickly differentiate visual archetypes without touching textures.

Acceptance Criteria:
- `mouth_enabled` toggle (bool, default off) and `mouth_shape` selector (at least 5 shapes: smile, grimace, flat, fang, beak) are available as build controls for all animated slugs
- `tail_enabled` toggle (bool, default off) and `tail_shape` selector (at least 5 shapes: spike, whip, club, segmented, curled) with a `tail_length` float (0.5–3.0, default 1.0) are available for all animated slugs
- Geometry is applied on slugs where a head or body mesh exists; controls are declared but silently skipped on slugs without the relevant mesh object
- `mouth_shape` control is disabled in the UI when `mouth_enabled` is false; `tail_shape` and `tail_length` are disabled when `tail_enabled` is false
- All new controls serialize correctly through `options_for_enemy()` JSON round-trip
- Enabling either extra does not alter any existing mesh part counts or bone layout (non-breaking addition)

Scope Notes:
- No mouth animation (chewing, open/close) — deferred
- No tail physics or runtime motion — geometry only
- No per-enemy asymmetric tail placement; tail exits from the rear (-X axis in Blender world space)
- Mouth color follows the existing head zone finish/hex system (no new color control)
- Tail color follows the existing body zone finish/hex system (no new color control)

---

## Execution Plan

### Codebase Findings (Planner Verified)

**Slug head mesh status (confirmed by reading all `build_mesh_parts` implementations):**
- `slug`: explicit `head` sphere at `(hx, 0, hz)`, sets `_zone_geom_head_center`/`_zone_geom_head_radii`. MOUTH-WIRED.
- `spider`: explicit `head` sphere, sets `_zone_geom_head_center`/`_zone_geom_head_radii`. MOUTH-WIRED.
- `claw_crawler`: explicit `head` sphere at `(hx, 0, hz)`, sets `_zone_geom_head_center`/`_zone_geom_head_radii`. MOUTH-WIRED.
- `imp`: explicit `head` sphere at `(0, 0, hz)`, sets `_zone_geom_head_center`/`_zone_geom_head_radii`. MOUTH-WIRED (not controls-only — imp has a real head object unlike eye stalks).
- `carapace_husk`: explicit `head` sphere at `(0, 0, hz_pos)`, sets `_zone_geom_head_center`/`_zone_geom_head_radii`. MOUTH-WIRED.
- `spitter`: explicit `head` sphere at `(hx, 0, hz)`, sets `_zone_geom_head_center`/`_zone_geom_head_radii`. MOUTH-WIRED (front-facing sphere, structurally identical to claw_crawler/slug head placement).
- `player_slime`: absent from `AnimatedEnemyBuilder.ENEMY_CLASSES` — appears only in controls API. CONTROLS-ONLY.

**Slug body mesh status (all animated enemies create a body object):**
- All six animated slugs (slug, spider, imp, spitter, claw_crawler, carapace_husk) create a body sphere/cylinder and set `_zone_geom_body_center`/`_zone_geom_body_radii`. ALL TAIL-WIRED.
- `player_slime`: CONTROLS-ONLY for tail.

**Tail surface point formula:** `body_center + Vector((-body_radii.x, 0.0, 0.0))` — the -X surface of the body ellipsoid. This is consistent with `place_back=True` direction in `zone_geometry_extras_attach.py`. Spec agent must document this.

**`blender_utils.py` geometry helper pattern (confirmed):**
`create_eye_mesh(shape, location, eye_scale)` and `create_pupil_mesh(shape, location, pupil_scale)` are standalone functions with named shape constants at module level (e.g. `_EYE_OVAL_SCALE_X`). `create_mouth_mesh(shape, location, head_scale)` and `create_tail_mesh(shape, length, location)` must follow the identical pattern: shape-dispatch via `if/elif` chain with named module-level scale constants, fallback to a default shape.

**`animated_build_controls_for_api()` assembly (confirmed):**
Controls are assembled as: `static_non_float + _eye_shape_pupil_control_defs() + static_float + _mesh_float_control_defs(slug) + _feature_control_defs(slug) + _part_feature_control_defs(slug) + _zone_extra_control_defs(slug) + [_placement_seed_def()]`. New helpers `_mouth_control_defs()` and `_tail_control_defs()` must follow the same split-by-type pattern: their bool/select_str controls go in the non-float block alongside eye/pupil; `tail_length` (float) goes into the float block.

**`animated_build_options_validate.py` coerce path (confirmed):**
`static_defs.extend(m._eye_shape_pupil_control_defs())` is the pattern. Adding `static_defs.extend(m._mouth_control_defs())` and `static_defs.extend(m._tail_control_defs())` propagates coercion automatically for all 6 new keys.

**`options_for_enemy()` `allowed_non_mesh` set (confirmed):**
`allowed_non_mesh |= {c["key"] for c in _eye_shape_pupil_control_defs()}` is the pattern. The same line must be added for `_mouth_control_defs()` and `_tail_control_defs()` so the 6 new keys are not silently dropped during merging.

**`buildControlDisabled` in `BuildControls.tsx` (confirmed):**
Current implementation: `if (defKey === "pupil_shape" && !values["pupil_enabled"]) return true;`. New rules: `mouth_shape` disabled when `!values["mouth_enabled"]`; `tail_shape` and `tail_length` disabled when `!values["tail_enabled"]`. No new TypeScript types needed.

### Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write spec for mouth extra + tail extra | Spec Agent | This ticket (including Codebase Findings above); `/Users/jacobbrandt/workspace/blobert/project_board/specs/eye_shape_and_pupil_system_spec.md` as structural reference; `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/utils/animated_build_options.py` control patterns | `project_board/specs/mouth_and_tail_extras_spec.md` covering: (a) all 6 control key names, option sets, defaults, coercion rules; (b) geometry-wired slug list for mouth (all 6 animated slugs) and tail (all 6 animated slugs), with `player_slime` as controls-only; (c) geometry placement formulas for mouth (head surface, +X front-facing, using `_zone_geom_head_center` + `_zone_geom_head_radii`) and tail (`body_center + Vector((-body_radii.x, 0, 0))`); (d) `create_mouth_mesh(shape, location, head_scale)` and `create_tail_mesh(shape, length, location)` function signatures; (e) control ordering rule (`mouth_enabled/mouth_shape/tail_enabled/tail_shape` in non-float block after eye/pupil; `tail_length` in float block before mesh floats); (f) serialization contract; (g) `allowed_non_mesh` set extension pattern in `options_for_enemy()`; (h) `buildControlDisabled` rules for frontend | None | Spec covers all 6 AC; `python ci/scripts/spec_completeness_check.py <spec_path> --type generic` passes; all key names, valid option sets, and defaults are enumerated; geometry placement formulas are explicit; per-slug wiring table is complete | Checkpoint logged at `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M25-MTE/run-2026-04-15T00-00-00Z-planning.md` — spitter is now included in mouth-wired slugs (all 6 animated enemies have explicit head spheres); imp and carapace_husk are geometry-wired for mouth (not controls-only). Spec agent must confirm this scope or escalate. |
| 2 | Python build controls — declare 6 new keys in `animated_build_options.py` and `animated_build_options_validate.py` | Implementation Agent | Spec (Task 1); `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/utils/animated_build_options.py` `_eye_shape_pupil_control_defs()` pattern; `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/utils/animated_build_options_validate.py` `static_defs.extend()` pattern | (a) New `_mouth_control_defs()` helper returning `[mouth_enabled (bool), mouth_shape (select_str)]`; (b) new `_tail_control_defs()` helper returning `[tail_enabled (bool), tail_shape (select_str), tail_length (float, min=0.5, max=3.0, default=1.0)]`; (c) both helpers merged into `animated_build_controls_for_api()` for ALL slugs including `player_slime`, preserving non-float-before-float ordering; (d) `options_for_enemy()` `allowed_non_mesh` set extended with both helpers' keys; (e) `_defaults_for_slug()` emits correct defaults; (f) `animated_build_options_validate.py` `static_defs.extend()` calls added for both helpers | Task 1 | `animated_build_controls_for_api()["slug"]` contains all 6 new keys; `options_for_enemy("slug", {})` returns `mouth_enabled=False, mouth_shape="smile", tail_enabled=False, tail_shape="spike", tail_length=1.0`; invalid `mouth_shape` falls back to `"smile"`; invalid `tail_shape` falls back to `"spike"`; `tail_length` is clamped to [0.5, 3.0]; `tail_length` coercion goes through the `float` branch in `coerce_validate_enemy_build_options`; all existing Python tests still pass | `tail_length` float control uses same coerce-and-validate path as existing float controls in `static_defs` (confirmed by reading `animated_build_options_validate.py`). Non-float ordering: `mouth_enabled, mouth_shape, tail_enabled, tail_shape` must appear before any float control for every slug. |
| 3 | Python geometry builders — `create_mouth_mesh` and `create_tail_mesh` in `blender_utils.py`; wire into all 6 animated enemy `build_mesh_parts` | Implementation Agent | Spec (Task 1); Task 2 controls; `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/core/blender_utils.py` (`create_eye_mesh`, `create_pupil_mesh` as geometry helper pattern with named module-level scale constants); all 6 animated enemy files | (a) `create_mouth_mesh(shape: str, location: tuple, head_scale: float) -> bpy.types.Object` in `blender_utils.py` with 5 shape dispatches (smile→arc/torus-like, grimace, flat, fang→cone, beak→cone variant), named scale constants, unknown-shape fallback; (b) `create_tail_mesh(shape: str, length: float, location: tuple) -> bpy.types.Object` in `blender_utils.py` with 5 shape dispatches (spike, whip, club, segmented, curled), named scale constants, unknown-shape fallback; (c) each of the 6 animated enemy `build_mesh_parts` updated to: read `mouth_enabled`/`mouth_shape` from `build_options`, compute mouth location from `_zone_geom_head_center`+`_zone_geom_head_radii`, call `create_mouth_mesh` when enabled; read `tail_enabled`/`tail_shape`/`tail_length` from `build_options`, compute tail location as `body_center + Vector((-body_radii.x, 0, 0))`, call `create_tail_mesh` when enabled; (d) `player_slime` skipped (not in `AnimatedEnemyBuilder.ENEMY_CLASSES`) | Task 2 | Any animated slug with `mouth_enabled=True` and `mouth_shape="fang"` appends 1 extra part to `self.parts`; default build (`mouth_enabled=False, tail_enabled=False`) produces IDENTICAL `len(self.parts)` as pre-ticket baseline for every slug; `tail_enabled=True` adds 1 extra part at computed rear point; existing `apply_themed_materials` part-count assumptions are not broken (mouth/tail parts appended after all existing parts) | Risk: `apply_themed_materials` uses indexed or enumerated `self.parts` patterns (e.g. slug uses `self.parts[0]` for body, `self.parts[1]` for head, `self.parts[2:]` for stalks/eyes). Adding mouth/tail parts at the END of `self.parts` is safe only if `apply_themed_materials` does not use `self.parts[-1]` or assume a fixed final index. Implementation agent must verify for each of the 6 enemy files. Risk: blender stubs may need extension for any new primitives used by mouth/tail shapes. |
| 4 | Python tests — control declarations, coercion, and serialization | Test Designer Agent | Spec (Task 1); Task 2 implementation; `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/utils/test_eye_shape_pupil_controls.py` as structural reference | `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/utils/test_mouth_tail_controls.py`; covers: (a) all slugs (including player_slime) declare all 6 keys in `animated_build_controls_for_api()`; (b) defaults match spec for every slug; (c) `mouth_shape` invalid string falls back to `"smile"`; (d) `tail_shape` invalid string falls back to `"spike"`; (e) `mouth_enabled`/`tail_enabled` bool coercion (truthy strings, int 0/1); (f) `tail_length` clamped to [0.5, 3.0] (test values 0.0, 0.5, 1.0, 3.0, 5.0); (g) JSON round-trip for all 6 keys preserves types; (h) nested slug envelope input format accepted; (i) `mouth_enabled`/`tail_enabled` serialize as JSON `false` not `0`; (j) `_mouth_control_defs()` and `_tail_control_defs()` helpers exist and return correct key lists | Tasks 2–3 | `bash .lefthook/scripts/py-tests.sh` passes; diff-cover preflight passes; test file follows import pattern of `test_eye_shape_pupil_controls.py` | Assumption: import pattern matches `test_eye_shape_pupil_controls.py` (`from src.utils.animated_build_options import ...`). |
| 5 | Python tests — geometry builder dispatch (with blender stubs) | Test Designer Agent | Spec (Task 1); Task 3 implementation; `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/enemies/test_eye_shape_pupil_geometry.py` as reference | `/Users/jacobbrandt/workspace/blobert/asset_generation/python/tests/enemies/test_mouth_tail_geometry.py`; covers: (a) `create_mouth_mesh` called when `mouth_enabled=True` for each geometry-wired slug; (b) `create_mouth_mesh` NOT called when `mouth_enabled=False` (default); (c) part count unchanged vs. baseline when both extras disabled; (d) `create_tail_mesh` called when `tail_enabled=True`; (e) `tail_length` passed through correctly to `create_tail_mesh`; (f) unknown `mouth_shape` produces sphere-fallback geometry (not error); (g) `player_slime` control declaration present but no geometry call | Task 3 | `bash .lefthook/scripts/py-tests.sh` passes; diff-cover passes; blender stubs are extended if new primitive shapes require it | Risk: stubs may need extension; test file should patch `blender_utils.create_mouth_mesh` and `blender_utils.create_tail_mesh` at the correct import path for each enemy module. |
| 6 | Frontend — add disabled rules for mouth/tail controls in `BuildControls.tsx` | Implementation Agent | Spec (Task 1); Task 2 API shape (controls flow through `/api/meta/enemies` automatically); `/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src/components/Preview/BuildControls.tsx` `buildControlDisabled` function; `pupil_shape` disable rule `if (defKey === "pupil_shape" && !values["pupil_enabled"]) return true;` as reference | Updated `buildControlDisabled`: add `if (defKey === "mouth_shape" && !values["mouth_enabled"]) return true;`; add `if ((defKey === "tail_shape" || defKey === "tail_length") && !values["tail_enabled"]) return true;`; no other changes | Task 2 | `mouth_shape` control row rendered with `opacity: 0.42` and `pointerEvents: "none"` when `mouth_enabled` is absent or falsy; `tail_shape` and `tail_length` similarly disabled when `tail_enabled` is absent or falsy; all three enabled when respective toggle is truthy; all existing frontend tests still pass | No new TypeScript types needed — `bool`, `select_str`, and `float` control types already declared. Change is 3 lines total. |
| 7 | Frontend tests — disabled-state logic for mouth/tail controls | Test Designer Agent | Task 6 implementation; `/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src/components/Preview/BuildControls.eyeShape.test.tsx` as reference | `/Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src/components/Preview/BuildControls.mouthTail.test.tsx`; tests: (a) `mouth_shape` disabled (opacity 0.42, pointerEvents none) when `mouth_enabled` absent; (b) `mouth_shape` disabled when `mouth_enabled=false`; (c) `mouth_shape` enabled when `mouth_enabled=true`; (d) `tail_shape` disabled when `tail_enabled` absent; (e) `tail_shape` disabled when `tail_enabled=false`; (f) `tail_length` disabled when `tail_enabled=false`; (g) `tail_shape` and `tail_length` both enabled when `tail_enabled=true`; (h) `mouth_enabled` toggle does NOT disable `tail_shape` (no bleed-over) | Task 6 | `cd asset_generation/web/frontend && npm test` passes; test file follows `@vitest-environment jsdom` pattern of `BuildControls.eyeShape.test.tsx` | — |

### Notes
- Tasks 2 and 3 are both Python-backend and can be sequenced in one agent run.
- Tasks 4 and 5 can be sequenced in one agent run after Tasks 2–3.
- Task 6 can begin once Task 2 is complete (API shape is the only frontend compile dependency).
- Task 7 is immediately sequenced after Task 6.
- Spec exit gate: `python ci/scripts/spec_completeness_check.py <spec_path> --type generic` must pass after Task 1.
- Diff-cover preflight: `bash ci/scripts/diff_cover_preflight.sh` must pass after Tasks 2–3.
- Geometry helpers `create_mouth_mesh` and `create_tail_mesh` follow the same pattern as `create_eye_mesh` / `create_pupil_mesh` in `/Users/jacobbrandt/workspace/blobert/asset_generation/python/src/core/blender_utils.py`.
- ALL 6 animated enemy slugs (spider, slug, imp, spitter, claw_crawler, carapace_husk) are geometry-wired for BOTH mouth and tail — each has an explicit head sphere and a body mesh object confirmed in code. `player_slime` is controls-only only.
- Mouth/tail mesh parts must be appended at the END of `self.parts` in each enemy's `build_mesh_parts()` to avoid breaking indexed `apply_themed_materials` assumptions.
- Checkpoint log: `/Users/jacobbrandt/workspace/blobert/project_board/checkpoints/M25-MTE/run-2026-04-15T00-00-00Z-planning.md`

---

## WORKFLOW STATE

- **Stage:** COMPLETE
- **Revision:** 7
- **Last Updated By:** Acceptance Criteria Gatekeeper Agent
- **Next Responsible Agent:** Human
- **Status:** Proceed
- **Validation Status:** All AC validated. (1) mouth_enabled/mouth_shape declared for all slugs ✓; (2) tail_enabled/tail_shape/tail_length declared ✓; (3) geometry applied on 6 wired slugs, player_slime controls-only ✓; (4) disabled rules in frontend ✓; (5) JSON serialization round-trip verified ✓; (6) non-breaking: default part counts unchanged ✓. Tests: Python 1692 passed, Frontend 410 passed, Diff-cover 87% ≥ 85%.
- **Blocking Issues:** None.
- **Escalation Notes:** None.

## NEXT ACTION

- **Next Responsible Agent:** Human
- **Required Input Schema:** Milestone review or proceed to next ticket.
- **Status:** Complete
- **Reason:** All acceptance criteria met. Implementation: Task 2 (Python controls), Task 3 (geometry builders), Task 6 (frontend disabled rules) complete. Tests pass, diff-cover passes. Ready for milestone closure.
