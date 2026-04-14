Title:
Movement Direction & Speed Controls

Description:
When Move mode is active, expose a direction selector and a speed/intensity slider so users can control the primary axis and magnitude of the body's locomotion loop. This lets users distinguish a vertically bobbing enemy from one that sways side-to-side, without requiring per-part overrides.

Acceptance Criteria:
- Direction selector is visible only when animation mode is "Move"
- At least 3 direction options are available: Vertical (up/down), Lateral (left/right), Forward (z-axis)
- A speed/intensity slider is present (normalized 0–1 range; both extremes must produce visible, non-degenerate motion)
- Changes to direction or intensity update the preview animation in real time with no page reload
- Both direction and intensity serialize to enemy config JSON
- Switching to a different direction does not reset speed or other animation settings

Scope Notes:
- Direction applies to the whole body, not individual parts (per-part overrides are in ticket 03)
- No diagonal or compound direction inputs in this ticket
- No physics-based movement — purely additive procedural oscillation
- Stretch mode does not use this direction selector (Stretch has no directional axis)

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add `anim_direction` as a `select_str` control (options: `vertical`, `lateral`, `forward`; default: `vertical`; `segmented: True`) to all animated slugs
- Add `anim_speed` as a `float` control (min 0.0, max 1.0, default 0.5, step 0.05, unit: `""`, hint: `"Move mode speed/intensity"`) to all animated slugs
- Both controls are preview-only parameters in this ticket; document in their `hint` fields
- `options_for_enemy()` must coerce both keys; unknown `anim_direction` values fall back to `vertical`; `anim_speed` is clamped to [0.0, 1.0]

**Frontend (`asset_generation/web/frontend/src/`)**
- `BuildControls.tsx` → `buildControlDisabled()`: disable `anim_direction` and `anim_speed` when `anim_mode` is not `move` (Stretch has no direction; Static has no motion)
- `GlbViewer.tsx` (or `AnimationOverlay.tsx`): update the procedural `move` animation clip to use `anim_direction` for axis selection and `anim_speed` for amplitude/frequency; the Three.js procedural clip should update in real time when these store values change without recreating the entire mixer

**Tests**
- Python: extend `test_anim_mode_control.py` — all slugs expose `anim_direction` and `anim_speed`; `anim_speed` 1.5 clamps to 1.0; `anim_direction` unknown coerces to `vertical`
- Frontend (Vitest): `BuildControls.animDirection.test.tsx` — `anim_direction` row disabled when `anim_mode` is `static`; disabled when `anim_mode` is `stretch`; enabled when `anim_mode` is `move`; `anim_speed` float row follows same gate

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
