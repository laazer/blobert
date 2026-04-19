Title:
Bipedal Body Presets (Standard & No-Leg)

Description:
Add two bipedal silhouette options to the body type selector: standard biped (upright, legs below center of mass) and no-leg biped (penguin/toad-style — compressed body, stubby protrusions instead of full legs). These are fixed presets that produce meaningfully different creature silhouettes quickly, without requiring the raw builder workflow.

Acceptance Criteria:
- A "Body Type" selector in the editor includes: Default, Standard Biped, No-Leg Biped
- Standard Biped produces a taller body with distinct upper/lower limb separation in the preview
- No-Leg Biped produces a low-center-of-mass body with short wide stubs instead of legs
- Switching body type updates the 3D preview immediately
- User-configured properties (color, texture, eye settings) are preserved when switching presets
- The selected body type is reflected in the serialized enemy config

Scope Notes:
- These are fixed presets, not freeform rig definitions; no custom skeleton authoring
- Arm configuration is not altered by body type selection
- No blending or interpolation between body types
- No-Leg Biped stubs are stylized primitives, not physics-simulated joints

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add `body_type` as a `select_str` control (options: `default`, `standard_biped`, `no_leg_biped`; default: `default`) to all animated slugs via a shared `_body_type_control_def()` helper
- `options_for_enemy()` must validate and coerce `body_type`; unknown values fall back to `default`
- The Blender geometry builders for each affected slug must branch on `build_options["body_type"]` to select the correct skeleton/mesh layout (standard biped = full leg geometry; no_leg_biped = stub geometry)

**Frontend (`asset_generation/web/frontend/src/`)**
- No `BuildControls.tsx` structural changes required; `body_type` is a `select_str` and renders automatically via the existing `ControlRow` path
- Because `body_type` changes the GLB geometry (requires Blender regeneration), the preview updates on the next "Run" command — not in real time; add a note in the control's `hint` field in Python: `"Preview updates after regeneration"`
- No `buildControlDisabled()` changes needed for this ticket

**Tests**
- Python: `test_body_type_control.py` — all animated slugs expose `body_type`; `options_for_enemy(slug, {"body_type": "INVALID"})` returns `default`; `standard_biped` and `no_leg_biped` are valid options for all slugs
- Frontend (Vitest): extend `BuildControls.meta_load.test.tsx` — `body_type` select_str row renders for an animated slug; selecting `no_leg_biped` calls `setAnimatedBuildOption` with the correct value

## Specification

- `project_board/specs/bipedal_body_presets_spec.md`

## WORKFLOW STATE

- **Stage:** COMPLETE
- **Revision:** 8

- **Last Updated By:** Acceptance Criteria Gatekeeper Agent

- **Validation Status:**
  - Tests: Passing — `uv run pytest tests/` (1963 passed); Vitest `BuildControls.meta_load.test.tsx` (7 tests)
  - Static QA: Ruff clean on touched Python
  - Integration: N/A (API control surface covered by Python tests)

- **Blocking Issues:** None

## NEXT ACTION

- **Next Responsible Agent:** Human

- **Status:** Proceed

- **Reason:** Implementation merged; commit recorded. Push when ready.
