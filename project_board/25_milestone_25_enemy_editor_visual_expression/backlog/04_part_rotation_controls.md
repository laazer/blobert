Title:
Per-Part Rotation Controls

Description:
Add X/Y/Z rotation inputs to the part properties panel so users can orient individual body parts (head, torso, limbs). Currently parts can be positioned but not rotated, which forces unnatural default poses and limits design variation. This ticket adds cosmetic rotation of the primitive shape — it is not joint rotation or skeletal posing.

Acceptance Criteria:
- Each selectable part exposes X, Y, Z rotation inputs in the properties panel
- Inputs accept numeric values in degrees; valid range is -180 to 180
- Values outside the valid range are clamped or rejected with inline feedback
- A "Reset Rotation" button restores the part to 0/0/0
- Rotation changes reflect immediately in the 3D preview
- Rotation values serialize correctly to enemy config JSON alongside position and scale

Scope Notes:
- Numeric inputs only — no 3D viewport rotation gizmo
- This is cosmetic orientation of the shape primitive, not joint/skeletal rotation
- No rotation constraints or limits tied to part type
- Does not affect collision or gameplay hitbox geometry

## Web Editor Implementation

**Python (`asset_generation/python/src/utils/animated_build_options.py`)**
- Add per-part rotation float controls using the existing `RIG_` prefix convention so they appear in the Rig float table: `RIG_HEAD_ROT_X`, `RIG_HEAD_ROT_Y`, `RIG_HEAD_ROT_Z`, `RIG_BODY_ROT_X`, `RIG_BODY_ROT_Y`, `RIG_BODY_ROT_Z` (degrees; min -180, max 180, default 0, step 1)
- Add to all animated slugs that expose explicit head/body parts; document which slugs are excluded (e.g. slug has no distinct head part)
- `options_for_enemy()` must clamp values to [-180, 180] during coercion

**Frontend (`asset_generation/web/frontend/src/`)**
- No `BuildControls.tsx` changes required; `RIG_` float controls automatically appear in the existing "Rig" float table section with filter support
- Verify that `RIG_HEAD_ROT_X` etc. appear under the Rig section header (the `d.key.startsWith("RIG_")` filter in `BuildControls.tsx:353`) — no code change needed if the naming convention is followed
- A "Reset Rotation" button is out of scope for the Rig table (individual cell reset is not part of the existing float table pattern); the existing per-key default coercion on re-generate serves as reset

**Tests**
- Python: `test_part_rotation_controls.py` — all target slugs expose `RIG_HEAD_ROT_X/Y/Z` and `RIG_BODY_ROT_X/Y/Z`; value 200 is clamped to 180; value -200 is clamped to -180; defaults are 0
- Frontend (Vitest): confirm `RIG_HEAD_ROT_X` appears in the Rig section filter (covered by existing `BuildControls.meta_load.test.tsx` pattern — extend that test file rather than creating a new one)

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
