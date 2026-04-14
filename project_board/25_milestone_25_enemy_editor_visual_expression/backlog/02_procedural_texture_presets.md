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

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
