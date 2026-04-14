Title:
Animation Mode Selector (Static / Move / Stretch)

Description:
Add a top-level animation panel with a mode selector offering three options: Static (no animation), Move (locomotion-style oscillation), and Stretch (elastic scale deformation loop). This is the foundational control for the entire animation system — all per-part configuration in subsequent tickets layers on top of the selected mode. Currently no animation controls exist in the editor.

Acceptance Criteria:
- An "Animation" panel is visible in the editor with a clearly labeled mode selector: Static / Move / Stretch
- Static mode disables all animation parameters; the 3D preview shows no motion
- Move mode produces a looping body oscillation animation (bounce or sway) in the 3D preview
- Stretch mode produces a looping elastic scale deformation in the 3D preview
- Preview playback starts automatically when a non-static mode is selected; stops when Static is selected
- Mode selection serializes to enemy config JSON
- Switching modes does not reset other editor settings (color, texture, eye, rotation)

Scope Notes:
- No custom keyframing or timeline; Move and Stretch are parameter-driven loops only
- Animation preview is viewport-only; no export in this ticket
- Loop speed is a fixed default in this ticket (speed control is in ticket 02)

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add `anim_mode` as a `select_str` control (options: `static`, `move`, `stretch`; default: `static`; `segmented: True`) to all animated slugs via a shared `_animation_mode_control_def()` helper
- `options_for_enemy()` must validate and coerce `anim_mode`; unknown values fall back to `static`
- `anim_mode` is a preview-only parameter in this ticket — it does not yet influence Blender GLB generation; document this in the control's `hint` field: `"Preview only — does not affect GLB generation yet"`

**Frontend (`asset_generation/web/frontend/src/`)**
- `BuildControls.tsx` → `buildControlDisabled()`: all future animation sub-controls (direction, speed, per-part) should be disabled when `anim_mode` is `static` — wire this gate now so ticket 02 and 03 only need to add their keys to the disable list
- `GlbViewer.tsx` (or a new `AnimationOverlay.tsx`): when `anim_mode` is `move`, apply a looping `THREE.AnimationMixer` procedural clip that oscillates the root bone or scene root on the Y axis using a sine curve; when `stretch`, apply a looping scale deformation via a `THREE.AnimationClip`; when `static`, clear any procedural clip and resume default idle pose
- Procedural animation clips are created in JavaScript from `anim_mode` value changes — no GLB regeneration required
- The existing `AnimationControls.tsx` (which plays named GLB clips) must not conflict with the new procedural overlay; if a named clip is active, pause it while a procedural mode is running

**Tests**
- Python: `test_anim_mode_control.py` — all animated slugs expose `anim_mode`; unknown value coerces to `static`; `static`/`move`/`stretch` are the only valid options
- Frontend (Vitest): `BuildControls.animMode.test.tsx` — segmented `anim_mode` control renders with 3 buttons; clicking `move` calls `setAnimatedBuildOption` with `"move"`; clicking `static` triggers the disable gate for animation sub-controls (direction row shows disabled)

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
