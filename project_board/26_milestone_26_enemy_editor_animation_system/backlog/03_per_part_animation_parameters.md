Title:
Per-Part Animation Parameters

Description:
Extend the animation system to allow users to configure animation behavior at the individual part level. A head can bob independently of the body; a limb can wiggle while the torso is still. Per-part settings override the global mode for that specific part, enabling expressive character differentiation without authoring custom animations. Builds on the part properties panel established in M25.

Acceptance Criteria:
- Selecting a part in the editor reveals an "Animation" section in its properties panel
- Each part has an "Animate" toggle; when off, the part inherits global animation behavior; when on, its own parameters are active
- Animated parts expose: animation type (bob, wiggle, pulse), axis (X/Y/Z), speed (normalized 0–1), and amplitude (normalized 0–1)
- Multiple parts can have different animation types simultaneously
- The 3D preview reflects all active per-part animations composited with the global mode
- Per-part animation settings serialize to enemy config JSON per part entry
- Disabling the "Animate" toggle on a part removes per-part overrides from the config (reverts to global)

Scope Notes:
- Per-part settings override global animation for that part; there is no blending between the two
- No phase/synchronization controls between parts in this ticket
- Animation types are limited to bob, wiggle, and pulse — no custom curve authoring
- Only applies when global animation mode is non-static; per-part settings are ignored in Static mode

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add per-part animation flat controls using a `PART_ANIM_` prefix (analogous to `RIG_` for rig floats), one set per named part region: `head`, `body`, `limbs`
  - `PART_ANIM_HEAD_ENABLED` (bool, default False), `PART_ANIM_HEAD_TYPE` (select_str: `bob`, `wiggle`, `pulse`; default `bob`), `PART_ANIM_HEAD_AXIS` (select_str: `x`, `y`, `z`; default `y`), `PART_ANIM_HEAD_SPEED` (float, 0–1, default 0.5), `PART_ANIM_HEAD_AMP` (float, 0–1, default 0.3)
  - Same five controls for `body` and `limbs` (15 controls total)
- Add to all animated slugs that have those part regions; document excluded slugs
- All controls are preview-only in this ticket; `options_for_enemy()` validates and coerces all 15 keys

**Frontend (`asset_generation/web/frontend/src/`)**
- `BuildControls.tsx` → `buildControlDisabled()`: all `PART_ANIM_*` controls are disabled when `anim_mode` is `static`; `PART_ANIM_HEAD_TYPE`, `PART_ANIM_HEAD_AXIS`, `PART_ANIM_HEAD_SPEED`, `PART_ANIM_HEAD_AMP` are disabled when `PART_ANIM_HEAD_ENABLED` is false (repeat for body and limbs)
- The 15 `PART_ANIM_` controls will appear in the Rig float table for floats and in the non-float section for bool/select_str controls; no new component needed if the existing `BuildControls.tsx` layout suffices. If the panel becomes unwieldy, group them under a collapsible "Per-Part Animation" section
- `GlbViewer.tsx` (or `AnimationOverlay.tsx`): when a part's `PART_ANIM_*_ENABLED` is true and global mode is non-static, apply a Three.js procedural sub-clip to the corresponding bone group; the clip type maps to: bob=Y-axis translate oscillation, wiggle=rotation oscillation, pulse=scale oscillation; amplitude and speed drive the clip parameters

**Tests**
- Python: `test_per_part_anim_controls.py` — all target slugs expose all 15 `PART_ANIM_*` keys; `PART_ANIM_HEAD_ENABLED` defaults to false; `PART_ANIM_HEAD_SPEED` clamps to [0, 1]; unknown `PART_ANIM_HEAD_TYPE` coerces to `bob`
- Frontend (Vitest): `BuildControls.perPartAnim.test.tsx` — `PART_ANIM_HEAD_TYPE` row disabled when `PART_ANIM_HEAD_ENABLED` is false; enabled when true; all `PART_ANIM_*` rows disabled when `anim_mode` is `static`

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
