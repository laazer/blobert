Title:
Procedural Texture Presets (Gradient, Spots, Stripes)

Description:
Add a texture mode panel that lets users apply a procedurally generated surface texture to the enemy body. Support three initial patterns — gradient, spots, and stripes — generated at the shader/material level with no image files required. Currently enemies are flat-shaded primitives; this adds critical visual richness with zero asset authoring cost.

Acceptance Criteria:
- A "Texture" panel exists in the editor with a mode selector: None / Gradient / Spots / Stripes
- Gradient exposes: primary color, secondary color, direction (horizontal/vertical/radial)
- Spots exposes: spot color, background color, density (scale)
- Stripes exposes: stripe color, background color, stripe width
- Texture is applied uniformly to all body parts
- Texture changes update the 3D preview in real time (no save/reload required)
- Selected mode and all exposed parameters serialize to enemy config JSON
- Switching back to "None" restores flat shading

Scope Notes:
- Per-part texture assignment is out of scope; texture applies to the whole body
- No uploaded textures in this ticket (see ticket 03)
- Shader/procedural only — no UV-mapped image textures
- No tiling offset controls

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add `texture_mode` as a `select_str` control (options: `none`, `gradient`, `spots`, `stripes`; default: `none`) to all animated slugs via a shared `_texture_control_defs()` helper, following the `_eye_shape_pupil_control_defs()` pattern
- Add per-mode parameter controls (all added to all slugs alongside `texture_mode`):
  - Gradient: `texture_grad_color_a` (str/hex), `texture_grad_color_b` (str/hex), `texture_grad_direction` (select_str: `horizontal`, `vertical`, `radial`)
  - Spots: `texture_spot_color` (str/hex), `texture_spot_bg_color` (str/hex), `texture_spot_density` (float, min 0.1, max 5.0)
  - Stripes: `texture_stripe_color` (str/hex), `texture_stripe_bg_color` (str/hex), `texture_stripe_width` (float, min 0.05, max 1.0)
- `options_for_enemy()` must validate and coerce all new keys; unknown `texture_mode` values fall back to `none`

**Frontend (`asset_generation/web/frontend/src/`)**
- `BuildControls.tsx` → `buildControlDisabled()`: disable all `texture_grad_*`, `texture_spot_*`, and `texture_stripe_*` controls when `texture_mode` is `none`; disable gradient params when mode is not `gradient`; spots params when mode is not `spots`; stripes params when mode is not `stripes`
- `components/Preview/GlbViewer.tsx` (or a new `TextureOverlay.tsx`): read `texture_mode` and corresponding params from the active build option values; apply a Three.js `ShaderMaterial` or material color map override on all mesh children of the loaded GLB when mode is non-none; revert to original materials when mode is `none`
- The texture override must react to `animatedBuildOptionValues` store changes without requiring GLB regeneration

**Tests**
- Python: `asset_generation/python/tests/utils/test_texture_controls.py` — all slugs expose `texture_mode`; coercion falls back to `none` for invalid values; per-mode param defaults round-trip JSON
- Frontend (Vitest): `BuildControls.texture.test.tsx` — `texture_grad_color_a` row is disabled when `texture_mode` is `none`; enabled when `texture_mode` is `gradient`; stripes row disabled when mode is `spots`

## Execution Plan

### Task 1 — Python: `_texture_control_defs()` helper and constants
**Agent:** Spec Agent (authored in spec); Generalist Implementation Agent (implements)
**Input:** `asset_generation/python/src/utils/animated_build_options_appendage_defs.py` — follow `_mouth_control_defs()` / `_tail_control_defs()` pattern
**Output:** New `_texture_control_defs()` function added to `animated_build_options_appendage_defs.py` returning 10 control def dicts:
  - `texture_mode` (select_str, options: none/gradient/spots/stripes, default: none)
  - `texture_grad_color_a` (str, default: "")
  - `texture_grad_color_b` (str, default: "")
  - `texture_grad_direction` (select_str, options: horizontal/vertical/radial, default: horizontal)
  - `texture_spot_color` (str, default: "")
  - `texture_spot_bg_color` (str, default: "")
  - `texture_spot_density` (float, min 0.1, max 5.0, step 0.05, default: 1.0)
  - `texture_stripe_color` (str, default: "")
  - `texture_stripe_bg_color` (str, default: "")
  - `texture_stripe_width` (float, min 0.05, max 1.0, step 0.01, default: 0.2)
  Constants declared at module level (e.g. `_TEXTURE_MODE_OPTIONS`, `_GRAD_DIRECTION_OPTIONS`, bounds).
**Dependencies:** None
**Success Criteria:** `_texture_control_defs()` importable; returns exactly 10 defs; all type/options/default values match spec; no enemy-class imports in the helper

### Task 2 — Python: wire `_texture_control_defs()` into `animated_build_controls_for_api()` and `_defaults_for_slug()`
**Agent:** Generalist Implementation Agent
**Input:** `asset_generation/python/src/utils/animated_build_options.py`; Task 1 completed
**Output:**
  - `_texture_control_defs` imported from `animated_build_options_appendage_defs`
  - `animated_build_controls_for_api()`: `_texture_control_defs()` defs appended after `_zone_extra_control_defs()` and before `[_placement_seed_def()]` in the `merged` list (or at end of non-float block — see spec for exact ordering)
  - `_defaults_for_slug()`: loop over `_texture_control_defs()` to populate default values in `out`
**Dependencies:** Task 1
**Success Criteria:** `animated_build_controls_for_api()["slug"]` contains all 10 texture control keys for every slug (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime); `_defaults_for_slug("slug")` includes all 10 keys at correct defaults

### Task 3 — Python: validation wiring in `options_for_enemy()` and `coerce_validate_enemy_build_options()`
**Agent:** Generalist Implementation Agent
**Input:** `asset_generation/python/src/utils/animated_build_options.py` and `animated_build_options_validate.py`; Task 1 completed
**Output:**
  - `options_for_enemy()`: all 10 texture control keys added to `allowed_non_mesh` set (same pattern as mouth/tail keys)
  - `coerce_validate_enemy_build_options()` in `animated_build_options_validate.py`: `static_defs.extend(m._texture_control_defs())` added alongside existing `_mouth_control_defs()` and `_tail_control_defs()` extensions
  - Invalid `texture_mode` string (e.g. `"invalid"`) coerces to `"none"`; out-of-range float values (`texture_spot_density`, `texture_stripe_width`) are clamped; empty string colors pass through unchanged
**Dependencies:** Task 1
**Success Criteria:** `options_for_enemy("slug", {"texture_mode": "invalid"})["texture_mode"] == "none"`; `options_for_enemy("slug", {"texture_spot_density": 99.9})["texture_spot_density"] == 5.0`; `options_for_enemy("slug", {})` includes all 10 texture keys at defaults

### Task 4 — Frontend: extend `buildControlDisabled()` in `BuildControls.tsx`
**Agent:** Generalist Implementation Agent
**Input:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx` — existing `buildControlDisabled()` function; Task 1 spec output
**Output:** `buildControlDisabled()` extended with texture mode conditional logic:
  - All `texture_grad_*` keys disabled when `texture_mode !== "gradient"` (including when `texture_mode` is `"none"` or absent)
  - All `texture_spot_*` keys disabled when `texture_mode !== "spots"`
  - All `texture_stripe_*` keys disabled when `texture_mode !== "stripes"`
  - `texture_mode` itself is never disabled
  - No existing disabling rules modified
**Dependencies:** None (can run in parallel with Task 1)
**Success Criteria:** `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: "none" })` returns `true`; `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: "gradient" })` returns `false`; `buildControlDisabled("slug", "texture_stripe_color", { texture_mode: "spots" })` returns `true`; existing pupil/mouth/tail rules unchanged

### Task 5 — Frontend: Three.js texture overlay in `GlbViewer.tsx`
**Agent:** Generalist Implementation Agent
**Input:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` — `Model` component owning `scene`; `useAppStore` for `animatedBuildOptionValues` and `commandContext`
**Output:** Inside the `Model` component (or a helper called from within it), add a `useEffect` that:
  - Reads `texture_mode` from `animatedBuildOptionValues[slug]` (where `slug` is derived from `commandContext` the same way `BuildControls` derives it)
  - Stores original materials of all mesh children in a `useRef` on first load (keyed by mesh UUID so restore is exact)
  - When `texture_mode` is `"gradient"`: constructs a Three.js `ShaderMaterial` using the `texture_grad_color_a`, `texture_grad_color_b`, and `texture_grad_direction` values; applies to all `THREE.Mesh` children of `scene`
  - When `texture_mode` is `"spots"`: applies a spots `ShaderMaterial` using `texture_spot_color`, `texture_spot_bg_color`, `texture_spot_density`
  - When `texture_mode` is `"stripes"`: applies a stripes `ShaderMaterial` using `texture_stripe_color`, `texture_stripe_bg_color`, `texture_stripe_width`
  - When `texture_mode` is `"none"` (or absent): restores stored original materials
  - Effect re-runs whenever the relevant store values change (reactive, no GLB reload)
  - On URL change (new model load), stored original materials are cleared and re-captured
**Dependencies:** None (can run parallel with Tasks 1–4)
**Success Criteria:** Changing `texture_mode` in the store updates all visible mesh materials without reloading the GLB; switching back to `"none"` restores original materials; no React errors in the browser console; gradient/spots/stripes are visually distinct in the viewport

### Task 6 — Python tests: `test_texture_controls.py`
**Agent:** Test Designer Agent
**Input:** Spec (authored in next stage); Task 1, 2, 3 output (implementation must exist for tests to pass)
**Output:** `asset_generation/python/tests/utils/test_texture_controls.py` with tests covering:
  - All 7 animated slugs (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime) expose `texture_mode` in `animated_build_controls_for_api()`
  - All 10 texture control keys present for each slug
  - `_texture_control_defs()` returns a fresh list each call (mutation guard)
  - `options_for_enemy("slug", {"texture_mode": "invalid"})["texture_mode"] == "none"`
  - `options_for_enemy("slug", {"texture_mode": "gradient"})["texture_mode"] == "gradient"`
  - Float clamp: `texture_spot_density` at 0.0 → 0.1, at 99.0 → 5.0
  - Float clamp: `texture_stripe_width` at 0.0 → 0.05, at 99.0 → 1.0
  - Empty hex string color fields round-trip as `""` through `options_for_enemy()`
  - All 10 texture keys present in `_defaults_for_slug()` output at correct defaults
  - Idempotency: `options_for_enemy` called twice on same input returns equal output
**Dependencies:** Tasks 1, 2, 3 (tests are RED until implementation completes)
**Success Criteria:** All tests pass after implementation; `bash .lefthook/scripts/py-tests.sh` exits 0

### Task 7 — Frontend tests: `BuildControls.texture.test.tsx`
**Agent:** Test Designer Agent
**Input:** Spec; Task 4 output (implementation must exist for tests to pass); `BuildControls.mouthTail.test.tsx` as structural pattern
**Output:** `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx` with tests covering:
  - `texture_grad_color_a` row is disabled (opacity 0.42, pointerEvents none) when `texture_mode` is `"none"`
  - `texture_grad_color_a` row is enabled when `texture_mode` is `"gradient"`
  - `texture_grad_color_a` row is disabled when `texture_mode` is `"spots"` (non-gradient non-none)
  - `texture_stripe_color` row is disabled when `texture_mode` is `"spots"`
  - `texture_spot_color` row is disabled when `texture_mode` is `"stripes"`
  - `texture_mode` control row itself is never disabled regardless of mode value
  - No bleed-over: changing `texture_mode` does not affect pupil/mouth/tail disabling rules
  - `texture_mode` select renders all four options: none, gradient, spots, stripes
**Dependencies:** Task 4 (tests are RED until implementation completes)
**Success Criteria:** All tests pass (`cd asset_generation/web/frontend && npm test` exits 0); no snapshot failures

### Task 8 — Spec completeness check and stage advance
**Agent:** Orchestrator (automated gate)
**Input:** Spec file authored by Spec Agent at `project_board/specs/procedural_texture_presets_spec.md`
**Output:** `python ci/scripts/spec_completeness_check.py project_board/specs/procedural_texture_presets_spec.md --type generic` exits 0; stage advanced to TEST_DESIGN
**Dependencies:** Spec Agent completes spec authoring
**Success Criteria:** Spec completeness check exits 0 (generic type, no required sections missing for this ticket type)

## Risks and Assumptions

| Risk / Assumption | Impact | Mitigation |
|---|---|---|
| Three.js `ShaderMaterial` uniform hex parsing: color params are raw hex strings (e.g. `"ff0000"`); the shader must parse them or caller must convert to `THREE.Color` | High | Spec must prescribe `new THREE.Color("#" + hex)` conversion with fallback to white for empty string |
| `texture_mode` and all 10 param keys added to `allowed_non_mesh` — if missed, keys silently drop in serialization round-trips | High | Task 3 explicitly gates this; tests in Task 6 cover the round-trip |
| `Model` component in `GlbViewer.tsx` is inside a `Suspense`; material override must not run before `scene` is populated | Medium | Store original materials in a `useRef` initialized after `useGLTF` resolves, not on mount |
| Color fields use `type: "str"` (not a new `"hex"` type), consistent with existing `feat_*_hex` fields | Low (confirmed) | Documented in checkpoint log; no new ControlRow rendering branch needed |
| `texture_spot_density` step size not specified in ticket; assumed 0.05 | Low | Spec Agent must nail this down; implementation uses 0.05 as default |
| `texture_stripe_width` step size not specified in ticket; assumed 0.01 | Low | Spec Agent must nail this down |
| No Blender-side geometry effect — this ticket is preview-only (Three.js shader overlay) | Confirmed in scope notes | No Python mesh builder required; `_texture_control_defs()` is controls-only declaration |

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | STATIC_QA |
| Revision | 6 |
| Last Updated By | Generalist Implementation Agent |
| Next Responsible Agent | Acceptance Criteria Gatekeeper Agent |
| Status | Proceed |
| Validation Status | Implemented `_texture_control_defs()` + wiring into controls/defaults/coercion; frontend texture-mode disabling; GLB viewer shader overlay with material restore. Tests: `timeout 300 bash .lefthook/scripts/py-tests.sh` PASS (1939 passed; diff-cover 91%); `npm test` PASS (50 files, 450 tests). |
| Blocking Issues | — |

## NEXT ACTION

Acceptance Criteria Gatekeeper Agent: verify each Acceptance Criterion is fully evidenced by implementation + tests (Python controls/coercion/serialization; frontend disabling; GLB viewer material override/restore and real-time updates), then route to fix-up if any AC lacks evidence.
