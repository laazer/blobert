# Mouth Extra & Tail Extra Spec

**Ticket:** `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/06_mouth_and_tail_extras.md`
**Spec version:** 1
**Author:** Spec Agent
**Date:** 2026-04-15

---

## Scope & Boundaries

This spec covers:
- Six new Python build controls: `mouth_enabled`, `mouth_shape`, `tail_enabled`, `tail_shape`, `tail_length`, and the helpers that declare them
- Per-slug geometry wiring scope (which slugs receive geometry effects vs. controls-only declaration)
- Geometry placement formulas for mouth and tail mesh objects
- `create_mouth_mesh` and `create_tail_mesh` function signatures and dispatch rules
- Control ordering in `animated_build_controls_for_api()`
- Coercion and validation rules for all six keys
- `options_for_enemy()` `allowed_non_mesh` extension
- `animated_build_options_validate.py` `static_defs.extend()` additions
- Serialization contract (JSON type correctness)
- Frontend `buildControlDisabled` rules for the three dependent controls
- Non-breaking guarantee when extras are disabled

Out of scope (per ticket):
- Mouth animation (chewing, open/close) — deferred
- Tail physics or runtime motion — geometry only
- Per-enemy asymmetric tail placement
- New color controls for mouth or tail (mouth inherits head zone finish/hex; tail inherits body zone finish/hex)
- `types/index.ts` changes (all required TypeScript types already exist)

---

## Requirement MTE-1: Python Build Control Declarations

### 1. Spec Summary

- **Description:** Six new `AnimatedBuildControlDef`-compatible control entries are declared for every animated enemy slug: `mouth_enabled`, `mouth_shape`, `tail_enabled`, `tail_shape`, `tail_length`. They are emitted by `animated_build_controls_for_api()` and their defaults are emitted by `_defaults_for_slug()`.
- **Constraints:**
  - Two new private helper functions are added to `animated_build_options.py`:
    - `_mouth_control_defs()` returns a `list[dict[str, Any]]` with two entries: `mouth_enabled` (`bool`) and `mouth_shape` (`select_str`).
    - `_tail_control_defs()` returns a `list[dict[str, Any]]` with three entries: `tail_enabled` (`bool`), `tail_shape` (`select_str`), `tail_length` (`float`).
  - Neither helper imports enemy classes. All values are module-level constants or literals.
  - `mouth_enabled` uses type `"bool"`, default `False`.
  - `mouth_shape` uses type `"select_str"`, options `["smile", "grimace", "flat", "fang", "beak"]`, default `"smile"`.
  - `tail_enabled` uses type `"bool"`, default `False`.
  - `tail_shape` uses type `"select_str"`, options `["spike", "whip", "club", "segmented", "curled"]`, default `"spike"`.
  - `tail_length` uses type `"float"`, min `0.5`, max `3.0`, step `0.05`, default `1.0`.
  - `player_slime` is included in the slug set and must receive all six controls (controls-only; no geometry wired).
- **Assumptions:** `bool` type coercion path already exists in `_coerce_and_validate` (confirmed by reading `animated_build_options_validate.py`). `float` coercion path is already in `_coerce_and_validate`. No new branches are required in the coercion function beyond adding these helpers to `static_defs`.
- **Scope:** `asset_generation/python/src/utils/animated_build_options.py`

### 2. Acceptance Criteria

**MTE-1-AC-1:** `animated_build_controls_for_api()[slug]` for every slug in the system (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime) contains exactly one entry with `key == "mouth_enabled"`, one with `key == "mouth_shape"`, one with `key == "tail_enabled"`, one with `key == "tail_shape"`, and one with `key == "tail_length"`.

**MTE-1-AC-2:** The `mouth_enabled` control entry has exactly this shape:
```
{
    "key": "mouth_enabled",
    "label": "Mouth",
    "type": "bool",
    "default": False,
}
```

**MTE-1-AC-3:** The `mouth_shape` control entry has exactly this shape:
```
{
    "key": "mouth_shape",
    "label": "Mouth shape",
    "type": "select_str",
    "options": ["smile", "grimace", "flat", "fang", "beak"],
    "default": "smile",
}
```

**MTE-1-AC-4:** The `tail_enabled` control entry has exactly this shape:
```
{
    "key": "tail_enabled",
    "label": "Tail",
    "type": "bool",
    "default": False,
}
```

**MTE-1-AC-5:** The `tail_shape` control entry has exactly this shape:
```
{
    "key": "tail_shape",
    "label": "Tail shape",
    "type": "select_str",
    "options": ["spike", "whip", "club", "segmented", "curled"],
    "default": "spike",
}
```

**MTE-1-AC-6:** The `tail_length` control entry has exactly this shape:
```
{
    "key": "tail_length",
    "label": "Tail length",
    "type": "float",
    "min": 0.5,
    "max": 3.0,
    "step": 0.05,
    "default": 1.0,
}
```

**MTE-1-AC-7:** `_defaults_for_slug(slug)` for every slug returns a dict that includes `"mouth_enabled": False`, `"mouth_shape": "smile"`, `"tail_enabled": False`, `"tail_shape": "spike"`, `"tail_length": 1.0`.

**MTE-1-AC-8:** The four non-float controls (`mouth_enabled`, `mouth_shape`, `tail_enabled`, `tail_shape`) appear before any float-type control in the per-slug control list. They appear after the eye/pupil controls (`eye_shape`, `pupil_enabled`, `pupil_shape`). `tail_length` appears in the float section, before mesh float controls (i.e., before entries from `_mesh_float_control_defs(slug)`).

**MTE-1-AC-9:** `_mouth_control_defs()` takes no arguments and returns `list[dict[str, Any]]`. `_tail_control_defs()` takes no arguments and returns `list[dict[str, Any]]`.

**MTE-1-AC-10:** The helper `_tail_control_defs()` returns controls in the order: `tail_enabled`, `tail_shape`, `tail_length`.

### 3. Risk & Ambiguity Analysis

- **Control ordering mechanics:** `animated_build_controls_for_api()` already splits controls into `static_non_float` and `static_float`. `_mouth_control_defs()` returns only non-float entries; `_tail_control_defs()` returns a mix. The implementation must filter `_tail_control_defs()` through the same non-float/float split. The spec mandates the final ordering in MTE-1-AC-8.
- **`tail_length` step value:** `0.05` is a design choice (same as other slider steps in the system). It must be declared as a module-level constant `_TAIL_LENGTH_STEP = 0.05` or reuse an existing step constant. It must not be an unexplained inline literal.
- **`player_slime` in `animated_build_controls_for_api()`:** The spider branch (`if slug == "spider": static = _spider_eye_control_defs()`) handles the spider uniquely. `player_slime` falls through to the default `static = list(_ANIMATED_BUILD_CONTROLS.get(slug, []))` path, which returns an empty list. The new helpers are appended after. This is correct and requires no special casing.

### 4. Clarifying Questions

None. Resolved by the Planner's codebase findings and checkpoint log at `project_board/checkpoints/M25-MTE/run-2026-04-15T00-00-00Z-planning.md`.

---

## Requirement MTE-2: Python Coercion and Validation

### 1. Spec Summary

- **Description:** `coerce_validate_enemy_build_options` in `animated_build_options_validate.py` correctly coerces and validates all six new keys. `options_for_enemy` in `animated_build_options.py` includes all six keys in `allowed_non_mesh` so they survive the merge step.
- **Constraints:**
  - `animated_build_options_validate.py`: after the existing `static_defs.extend(m._eye_shape_pupil_control_defs())` call, add `static_defs.extend(m._mouth_control_defs())` and `static_defs.extend(m._tail_control_defs())`. No other changes to the validate module are required.
  - `options_for_enemy` in `animated_build_options.py`: after the existing `allowed_non_mesh |= {c["key"] for c in _eye_shape_pupil_control_defs()}` line, add `allowed_non_mesh |= {c["key"] for c in _mouth_control_defs()}` and `allowed_non_mesh |= {c["key"] for c in _tail_control_defs()}`.
  - Invalid `mouth_shape` (value not in option set) falls back to `"smile"` (the declared default).
  - Invalid `tail_shape` (value not in option set) falls back to `"spike"` (the declared default).
  - `tail_length` is clamped to `[0.5, 3.0]`. Values below `0.5` become `0.5`; values above `3.0` become `3.0`.
  - `mouth_enabled` and `tail_enabled` are coerced through `_coerce_boolish(v, default=False)`, producing Python `bool` (not `int`).
  - `coerce_validate_enemy_build_options` already has a `"bool"` branch; no new branch is required.
  - `coerce_validate_enemy_build_options` already has a `"float"` branch; no new branch is required.
- **Assumptions:** `_coerce_boolish` handles `bool`, `int`, `float`, and `str` inputs (confirmed by reading the implementation).
- **Scope:** `asset_generation/python/src/utils/animated_build_options_validate.py` (extend `static_defs`); `asset_generation/python/src/utils/animated_build_options.py` (extend `allowed_non_mesh`).

### 2. Acceptance Criteria

**MTE-2-AC-1:** `options_for_enemy("slug", {"mouth_shape": "INVALID"})["mouth_shape"]` returns `"smile"`.

**MTE-2-AC-2:** `options_for_enemy("slug", {"mouth_shape": "fang"})["mouth_shape"]` returns `"fang"`.

**MTE-2-AC-3:** `options_for_enemy("spider", {"tail_shape": "NOTREAL"})["tail_shape"]` returns `"spike"`.

**MTE-2-AC-4:** `options_for_enemy("spider", {"tail_shape": "curled"})["tail_shape"]` returns `"curled"`.

**MTE-2-AC-5:** `options_for_enemy("spider", {"mouth_enabled": True})["mouth_enabled"]` returns `True` (Python `bool`, not `int`).

**MTE-2-AC-6:** `options_for_enemy("spider", {"mouth_enabled": "yes"})["mouth_enabled"]` returns `True`.

**MTE-2-AC-7:** `options_for_enemy("spider", {"mouth_enabled": 0})["mouth_enabled"]` returns `False`.

**MTE-2-AC-8:** `options_for_enemy("claw_crawler", {})["mouth_enabled"]` returns `False`.

**MTE-2-AC-9:** `options_for_enemy("claw_crawler", {})["tail_enabled"]` returns `False`.

**MTE-2-AC-10:** `options_for_enemy("slug", {"tail_length": 0.0})["tail_length"]` returns `0.5` (clamped to min).

**MTE-2-AC-11:** `options_for_enemy("slug", {"tail_length": 5.0})["tail_length"]` returns `3.0` (clamped to max).

**MTE-2-AC-12:** `options_for_enemy("slug", {"tail_length": 1.5})["tail_length"]` returns `1.5` (valid, unchanged).

**MTE-2-AC-13:** `options_for_enemy("slug", {"tail_length": 0.5})["tail_length"]` returns `0.5` (boundary min, valid).

**MTE-2-AC-14:** `options_for_enemy("slug", {"tail_length": 3.0})["tail_length"]` returns `3.0` (boundary max, valid).

**MTE-2-AC-15:** All existing tests in `asset_generation/python/tests/` continue to pass after the change.

### 3. Risk & Ambiguity Analysis

- **`static_defs.extend()` ordering:** The order in which helpers are extended onto `static_defs` does not affect coercion correctness (each entry is keyed by `"key"`). The order should match the control list assembly order for readability: `_mouth_control_defs()` before `_tail_control_defs()`.
- **`tail_length` clamping of non-numeric input:** If `tail_length` is an invalid non-numeric string, the existing `float` branch in `coerce_validate_enemy_build_options` falls back to the declared `default` (`1.0`), then clamps. No special handling required.

### 4. Clarifying Questions

None.

---

## Requirement MTE-3: Per-Slug Defaults

### 1. Spec Summary

- **Description:** Defaults for all six new controls are uniform across all slugs. There are no per-slug overrides.
- **Constraints:**
  - `mouth_enabled` default: `False` for all slugs.
  - `mouth_shape` default: `"smile"` for all slugs.
  - `tail_enabled` default: `False` for all slugs.
  - `tail_shape` default: `"spike"` for all slugs.
  - `tail_length` default: `1.0` for all slugs.
  - These values are returned by both `_defaults_for_slug(slug)` and `options_for_enemy(slug, {})`.
- **Assumptions:** No per-slug default variation is needed for this ticket. If a future ticket wants different defaults per slug, `_defaults_for_slug` can be extended.
- **Scope:** `_defaults_for_slug` in `animated_build_options.py`.

### 2. Acceptance Criteria

**MTE-3-AC-1:** For every animated enemy slug (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime): `_defaults_for_slug(slug)["mouth_enabled"] is False` (Python `False`, not `0`).

**MTE-3-AC-2:** For every animated enemy slug: `_defaults_for_slug(slug)["mouth_shape"] == "smile"`.

**MTE-3-AC-3:** For every animated enemy slug: `_defaults_for_slug(slug)["tail_enabled"] is False` (Python `False`, not `0`).

**MTE-3-AC-4:** For every animated enemy slug: `_defaults_for_slug(slug)["tail_shape"] == "spike"`.

**MTE-3-AC-5:** For every animated enemy slug: `_defaults_for_slug(slug)["tail_length"] == 1.0`.

### 3. Risk & Ambiguity Analysis

None.

### 4. Clarifying Questions

None.

---

## Requirement MTE-4: Geometry Placement Formulas

### 1. Spec Summary

- **Description:** When `mouth_enabled` or `tail_enabled` is `True`, the respective mesh is created at a deterministic location derived from zone geometry instance variables already set by `build_mesh_parts`.
- **Constraints:**
  - **Mouth location formula:** `mouth_location = head_center + Vector((head_radii.x, 0, 0))`
    - `head_center` is the `_zone_geom_head_center` attribute set during the head sphere construction in each slug's `build_mesh_parts`.
    - `head_radii` is the `_zone_geom_head_radii` attribute set during the head sphere construction.
    - `head_radii.x` is the forward (+X) half-extent of the head ellipsoid.
    - The `+X` direction corresponds to the front-facing surface of the enemy in Blender world space, consistent with the zone extras `place_front=True` convention.
  - **Tail location formula:** `tail_location = body_center + Vector((-body_radii.x, 0, 0))`
    - `body_center` is the `_zone_geom_body_center` attribute set during the body sphere/cylinder construction.
    - `body_radii` is the `_zone_geom_body_radii` attribute set during the body sphere/cylinder construction.
    - `-body_radii.x` gives the rear (-X) surface point of the body ellipsoid, consistent with `place_back=True` in `zone_geometry_extras_attach.py`.
  - Both formulas use `mathutils.Vector` (already imported in all enemy builders).
  - The formula must be computed after `_zone_geom_head_center`/`_zone_geom_head_radii` and `_zone_geom_body_center`/`_zone_geom_body_radii` have been set (i.e., after the head/body sphere creation block, not before).
- **Assumptions:** All six animated enemy builders set `_zone_geom_head_center`, `_zone_geom_head_radii`, `_zone_geom_body_center`, and `_zone_geom_body_radii` as instance attributes during `build_mesh_parts()` before any extra geometry is appended (confirmed by Planner codebase finding).
- **Scope:** All six animated enemy `build_mesh_parts` implementations.

### 2. Acceptance Criteria

**MTE-4-AC-1:** For each of the six geometry-wired animated slugs, when `mouth_enabled=True`, the location passed to `create_mouth_mesh` equals `(head_center.x + head_radii.x, head_center.y, head_center.z)` (i.e., `head_center + Vector((head_radii.x, 0, 0))`).

**MTE-4-AC-2:** For each of the six geometry-wired animated slugs, when `tail_enabled=True`, the location passed to `create_tail_mesh` equals `(body_center.x - body_radii.x, body_center.y, body_center.z)` (i.e., `body_center + Vector((-body_radii.x, 0, 0))`).

**MTE-4-AC-3:** The mouth and tail geometry is appended to `self.parts` after all pre-existing parts have been added. Neither creation call occurs before the body, head, limb, or existing eye parts are created.

**MTE-4-AC-4:** `player_slime` does not call `create_mouth_mesh` or `create_tail_mesh` regardless of option values.

### 3. Risk & Ambiguity Analysis

- **Mouth faces the +X surface:** The head sphere's front-facing surface is at `head_center.x + head_radii.x` (not `head_center.x - head_radii.x`). Implementation must not accidentally negate the head offset. The tail uses the negated body radius (`-body_radii.x`) to reach the rear surface.
- **Radii attribute presence:** If `_zone_geom_head_radii` is a `Vector`, `.x` gives the X half-extent directly. Implementations must confirm the attribute is a `Vector` (or tuple with index `[0]`) in all six builders before reading `.x`.
- **`head_scale` argument for `create_mouth_mesh`:** The `head_scale` float passed to `create_mouth_mesh` should be `head_radii.x` (the X half-extent of the head ellipsoid), providing a consistent scale reference for the mouth primitive relative to the head size.

### 4. Clarifying Questions

None.

---

## Requirement MTE-5: `create_mouth_mesh` Geometry Helper

### 1. Spec Summary

- **Description:** A new standalone function `create_mouth_mesh(shape, location, head_scale)` is added to `blender_utils.py` following the identical pattern of `create_eye_mesh` and `create_pupil_mesh`.
- **Constraints:**
  - Function signature: `create_mouth_mesh(shape: str, location: tuple, head_scale: float) -> bpy.types.Object`
  - Shape dispatch via `if/elif` chain. Unknown shapes fall back to `"smile"` behavior.
  - Each non-trivial scale ratio must be a named module-level constant (not an inline literal).
  - All five shapes must be implemented:

| `shape` value | Primitive | Rationale |
|---|---|---|
| `"smile"` | `create_cylinder` | Thin curved arc; wide flat cylinder approximating an arc |
| `"grimace"` | `create_cylinder` | Thin flat cylinder, wider than smile — compressed lips |
| `"flat"` | `create_box` | Featureless flat slit |
| `"fang"` | `create_cone` | Single downward-pointing cone (fang shape) |
| `"beak"` | `create_cone` | Wider cone with a greater radius1 — beak/bill variant |

- **Assumptions:** `create_cone` already exists in `blender_utils.py` (confirmed by reading the file).
- **Scope:** `asset_generation/python/src/core/blender_utils.py`

### 2. Acceptance Criteria

**MTE-5-AC-1:** A function `create_mouth_mesh(shape: str, location: tuple, head_scale: float)` exists in `blender_utils.py` and returns the Blender object created.

**MTE-5-AC-2:** `create_mouth_mesh` dispatches to Blender primitives as follows:

| `shape` value | Primitive call | Scale |
|---|---|---|
| `"smile"` | `create_cylinder` | `(head_scale * _MOUTH_SMILE_X_RATIO, head_scale * _MOUTH_SMILE_Y_RATIO, head_scale * _MOUTH_SMILE_Z_RATIO)` |
| `"grimace"` | `create_cylinder` | `(head_scale * _MOUTH_GRIMACE_X_RATIO, head_scale * _MOUTH_GRIMACE_Y_RATIO, head_scale * _MOUTH_GRIMACE_Z_RATIO)` |
| `"flat"` | `create_box` | `(head_scale * _MOUTH_FLAT_X_RATIO, head_scale * _MOUTH_FLAT_Y_RATIO, head_scale * _MOUTH_FLAT_Z_RATIO)` |
| `"fang"` | `create_cone` | scale `(head_scale * _MOUTH_FANG_X_RATIO, head_scale * _MOUTH_FANG_X_RATIO, head_scale * _MOUTH_FANG_Z_RATIO)` |
| `"beak"` | `create_cone` | scale `(head_scale * _MOUTH_BEAK_X_RATIO, head_scale * _MOUTH_BEAK_X_RATIO, head_scale * _MOUTH_BEAK_Z_RATIO)` |

If `shape` is not one of the five values, fall back to `"smile"` behavior.

**MTE-5-AC-3:** All scale ratio constants used in `create_mouth_mesh` are declared as module-level named constants in `blender_utils.py`. No bare numeric scale ratios appear inline inside the function body (trivial identity values `1.0` are exempt from this rule).

**MTE-5-AC-4:** `create_mouth_mesh` is exported from `blender_utils.py` at module level (i.e., defined as a top-level function, importable via `from src.core.blender_utils import create_mouth_mesh`).

**MTE-5-AC-5:** The `"fang"` shape produces a narrower cone (smaller radius) than the `"beak"` shape (larger radius). Concretely: `_MOUTH_FANG_X_RATIO < _MOUTH_BEAK_X_RATIO`.

**MTE-5-AC-6:** For an unknown `shape` value (e.g., `"triangle"`), `create_mouth_mesh` returns the same object type and approximate size as `create_mouth_mesh("smile", location, head_scale)` — it does not raise an exception.

### 3. Risk & Ambiguity Analysis

- **Cylinder orientation for smile/grimace:** `create_cylinder` in Blender creates a cylinder along the Z axis by default. A smile/grimace shape should appear as a thin horizontal disc when viewed from the front (+X). Setting a large X and Y scale with a small Z scale achieves this. The implementation must orient the disc to face the viewer (thin along Z = depth into head). If the orientation is wrong (cylinder axis facing the wrong direction), the implementer must flag it and choose a corrected approach.
- **Fang vs. beak distinction:** `create_cone` with `radius1 > 0, radius2 = 0` is a cone. A beak (wider base) uses a larger `radius1`. The `radius1`/`radius2` arguments to `create_cone` may be scaled separately from the XY scale, or the XY scale can substitute. The implementer must document which approach is used. Both are acceptable; the key constraint is that fang is narrower than beak (MTE-5-AC-5).
- **Scale ratio values are implementation choices:** The exact numeric values of the scale ratio constants are not mandated by this spec (they are design/aesthetic choices). The constraint is that they must be named constants (not inline literals) and that `_MOUTH_FANG_X_RATIO < _MOUTH_BEAK_X_RATIO`. Implementation may adjust ratios aesthetically without spec change.

### 4. Clarifying Questions

None.

---

## Requirement MTE-6: `create_tail_mesh` Geometry Helper

### 1. Spec Summary

- **Description:** A new standalone function `create_tail_mesh(shape, length, location)` is added to `blender_utils.py` following the identical pattern of `create_eye_mesh`, `create_pupil_mesh`, and `create_mouth_mesh`.
- **Constraints:**
  - Function signature: `create_tail_mesh(shape: str, length: float, location: tuple) -> bpy.types.Object`
  - Note: parameter order is `(shape, length, location)` — `length` comes before `location`.
  - Shape dispatch via `if/elif` chain. Unknown shapes fall back to `"spike"` behavior.
  - The `length` parameter scales the overall tail geometry extent. A `length` of `1.0` produces a "normal" size tail; `length` of `0.5` is shorter; `3.0` is longer.
  - Each non-trivial scale ratio must be a named module-level constant.
  - All five shapes must be implemented:

| `shape` value | Primitive | Rationale |
|---|---|---|
| `"spike"` | `create_cone` | Sharp tapered cone, the narrowest rear appendage |
| `"whip"` | `create_cylinder` | Long thin cylinder — flexible whip shape |
| `"club"` | `create_sphere` | Enlarged sphere at the rear — blunt club shape |
| `"segmented"` | `create_cylinder` | Wider segmented-looking cylinder (shorter, wider than whip) |
| `"curled"` | `create_sphere` | Slightly flattened sphere approximating a coiled tail |

- **Assumptions:** Tail geometry primitives do not require any new primitive types not already in `blender_utils.py`.
- **Scope:** `asset_generation/python/src/core/blender_utils.py`

### 2. Acceptance Criteria

**MTE-6-AC-1:** A function `create_tail_mesh(shape: str, length: float, location: tuple)` exists in `blender_utils.py` and returns the Blender object created.

**MTE-6-AC-2:** `create_tail_mesh` dispatches to Blender primitives as follows:

| `shape` value | Primitive call | Primary scale principle |
|---|---|---|
| `"spike"` | `create_cone` | Narrow XY, long Z proportional to `length`; `radius2=0.0` |
| `"whip"` | `create_cylinder` | Very narrow XY (`_TAIL_WHIP_XY_RATIO`), long Z proportional to `length` |
| `"club"` | `create_sphere` | Near-uniform XY scale; Z proportional to `length * _TAIL_CLUB_Z_RATIO` |
| `"segmented"` | `create_cylinder` | Wider XY than whip (`_TAIL_SEG_XY_RATIO`), moderate Z proportional to `length` |
| `"curled"` | `create_sphere` | Slightly flattened: `(length * _TAIL_CURLED_X_RATIO, length * _TAIL_CURLED_X_RATIO, length * _TAIL_CURLED_Z_RATIO)` |

If `shape` is not one of the five values, fall back to `"spike"` behavior.

**MTE-6-AC-3:** All scale ratio constants used in `create_tail_mesh` are declared as module-level named constants in `blender_utils.py`.

**MTE-6-AC-4:** `create_tail_mesh` is importable via `from src.core.blender_utils import create_tail_mesh`.

**MTE-6-AC-5:** `create_tail_mesh("spike", 1.0, (0, 0, 0))` returns a non-None Blender object (does not raise).

**MTE-6-AC-6:** For an unknown `shape` value (e.g., `"fin"`), `create_tail_mesh` returns the same primitive type as `create_tail_mesh("spike", length, location)` — it does not raise an exception.

**MTE-6-AC-7:** `create_tail_mesh("whip", 2.0, (0, 0, 0))` produces a longer/taller geometry than `create_tail_mesh("whip", 1.0, (0, 0, 0))` (i.e., `length` parameter meaningfully scales the output).

### 3. Risk & Ambiguity Analysis

- **`length` vs. uniform scale:** The tail shapes differ in which axis `length` primarily elongates. For cone/cylinder shapes, `length` scales the Z axis (depth/height). For sphere shapes, `length` scales all axes or a dominant subset. The exact ratio constants are implementation choices; the constraint is only that unknown shapes fall back to spike, all constants are named, and `length` has a measurable effect.
- **Segmented vs. whip distinction:** Both are cylinders. The difference is XY scale (segmented is wider). The implementation must ensure `_TAIL_SEG_XY_RATIO > _TAIL_WHIP_XY_RATIO`.
- **Tail location is the root attachment point:** The `location` tuple is the tail attachment point on the body surface (the -X surface of the body). The mesh will extend further in the -X direction from that point. This means the mesh center at `location` may be partially inside the body sphere. This is acceptable — the geometry will protrude outward visually. No collision or physics are considered.

### 4. Clarifying Questions

None.

---

## Requirement MTE-7: Per-Slug Geometry Wiring

### 1. Spec Summary

- **Description:** ALL six animated enemy slugs (spider, slug, imp, spitter, claw_crawler, carapace_husk) are geometry-wired for BOTH mouth and tail. `player_slime` is controls-only for both. Each enemy builder's `build_mesh_parts` reads `mouth_enabled`, `mouth_shape`, `tail_enabled`, `tail_shape`, `tail_length` from `build_options` and conditionally creates the respective mesh.
- **Constraints:**
  - For mouth: read `mouth_enabled = self.build_options.get("mouth_enabled", False)`. If truthy, read `mouth_shape = str(self.build_options.get("mouth_shape", "smile"))`. Compute `mouth_location` using the formula from MTE-4. Call `create_mouth_mesh(mouth_shape, tuple(mouth_location), head_radii.x)`. Append the returned object to `self.parts`.
  - For tail: read `tail_enabled = self.build_options.get("tail_enabled", False)`. If truthy, read `tail_shape = str(self.build_options.get("tail_shape", "spike"))` and `tail_length = float(self.build_options.get("tail_length", 1.0))`. Compute `tail_location` using the formula from MTE-4. Call `create_tail_mesh(tail_shape, tail_length, tuple(tail_location))`. Append the returned object to `self.parts`.
  - Both `create_mouth_mesh` and `create_tail_mesh` are imported from `..core.blender_utils` in each enemy builder file.
  - Mouth and tail parts are always appended LAST (after all pre-existing parts including eyes, stalks, limbs, shells, zone extras). This preserves the indexed material assignment in `apply_themed_materials` for all existing parts.
  - Neither `animated_imp.py` nor `animated_carapace_husk.py` are controls-only for this ticket — both have confirmed explicit head spheres and body meshes. They are geometry-wired.
  - `player_slime` is not in `AnimatedEnemyBuilder.ENEMY_CLASSES`, so its builder is not modified.
- **Assumptions:** Implementation agent must verify for each of the six builders that `apply_themed_materials` does not use `self.parts[-1]` or a fixed final index that would break if new parts are appended at the end. This verification is an implementation task, not a spec gap. Conservative rule: appending at end is safe if `apply_themed_materials` uses slices or explicit index ranges bounded by known part counts.
- **Scope:** `animated_spider.py`, `animated_slug.py`, `animated_imp.py`, `animated_spitter.py`, `animated_claw_crawler.py`, `animated_carapace_husk.py`

### 2. Acceptance Criteria

**MTE-7-AC-1:** For each of the six geometry-wired animated slugs, building with `mouth_enabled=True, mouth_shape="fang"` appends exactly 1 additional part to `self.parts` vs. the default baseline build.

**MTE-7-AC-2:** For each of the six geometry-wired animated slugs, building with `tail_enabled=True, tail_shape="spike", tail_length=1.0` appends exactly 1 additional part to `self.parts` vs. the default baseline build.

**MTE-7-AC-3:** Building with both `mouth_enabled=True` and `tail_enabled=True` appends exactly 2 additional parts (1 mouth + 1 tail) to `self.parts` vs. the default baseline build.

**MTE-7-AC-4:** Building with default options (`mouth_enabled=False, tail_enabled=False`) produces an identical `len(self.parts)` as the pre-ticket baseline for every slug.

**MTE-7-AC-5:** `create_mouth_mesh` is NOT called when `mouth_enabled` is `False` (default).

**MTE-7-AC-6:** `create_tail_mesh` is NOT called when `tail_enabled` is `False` (default).

**MTE-7-AC-7:** `create_mouth_mesh` and `create_tail_mesh` are imported from `..core.blender_utils` (or `src.core.blender_utils` in fallback path) in all six builder files.

**MTE-7-AC-8:** `player_slime` builder (if it exists separately) is not modified; no `create_mouth_mesh` or `create_tail_mesh` calls are added to it.

### 3. Risk & Ambiguity Analysis

- **`apply_themed_materials` part index assumptions:** This is the highest-risk area. Some builders use `self.parts[0]`, `self.parts[1]`, `self.parts[2:]` indexing. Appending mouth and tail parts at the very end (after zone extras) is the safest strategy. If any builder uses `self.parts[-1]` or assumes the last part is a specific mesh type, appending will break material assignment. The implementation agent must audit each of the six builders' `apply_themed_materials` before writing the wiring code.
- **Mouth/tail material zone:** Mouth parts inherit the head zone material. Tail parts inherit the body zone material. No new material zone is introduced. Material assignment in `apply_themed_materials` must explicitly assign mouth parts to the `head` material slot and tail parts to the `body` material slot after appending. This spec requires the assignment; the exact index arithmetic is an implementation concern.

### 4. Clarifying Questions

None. Imp and carapace_husk are geometry-wired (not controls-only) per the Planner's verified codebase findings.

---

## Requirement MTE-8: Non-Breaking Default Guarantee

### 1. Spec Summary

- **Description:** When both `mouth_enabled` and `tail_enabled` are `False` (the default state for all slugs), the build output must be identical to the pre-ticket baseline: same number of mesh parts, same mesh types, same material assignments.
- **Constraints:**
  - No extra objects are created, appended, or mutated when the extras are disabled.
  - Disabling checks must be the first conditional in the mouth/tail block (i.e., no intermediate operations before the `if mouth_enabled` gate).
  - `_defaults_for_slug` emits `False` for both toggles, guaranteeing this condition holds for any build that does not explicitly override the defaults.
- **Assumptions:** Zone extras already follow this pattern (`kind == "none"` skips all extra geometry). The mouth/tail extras follow the same "disabled by default, explicitly enabled" pattern.
- **Scope:** All six animated enemy builder `build_mesh_parts` implementations.

### 2. Acceptance Criteria

**MTE-8-AC-1:** For every animated enemy slug, `len(build_mesh_parts())` with default options equals `len(build_mesh_parts())` with pre-ticket code (no new parts).

**MTE-8-AC-2:** For every animated enemy slug, no call to `create_mouth_mesh` or `create_tail_mesh` is made during a default build.

**MTE-8-AC-3:** All existing Python tests that assert on part counts, mesh types, or material slot assignments continue to pass without modification after this ticket's changes.

### 3. Risk & Ambiguity Analysis

- **Default value source:** The default comes from `options_for_enemy(slug, {})`, not from the builder's own fallback. As long as `_defaults_for_slug` emits `mouth_enabled=False` and `tail_enabled=False` (MTE-3-AC-1, MTE-3-AC-3), and coercion via `_coerce_boolish` produces Python `False`, the non-breaking guarantee holds.

### 4. Clarifying Questions

None.

---

## Requirement MTE-9: Serialization Contract

### 1. Spec Summary

- **Description:** All six new keys are serialized to and from enemy config JSON in the same way as existing build options. No new JSON structure is introduced.
- **Constraints:**
  - `mouth_enabled` and `tail_enabled` serialize as JSON booleans (`true`/`false`), not integers.
  - `mouth_shape` and `tail_shape` serialize as JSON strings.
  - `tail_length` serializes as a JSON float (e.g., `1.0`, `2.5`).
  - All six keys are top-level keys in the enemy options dict (not nested under `mesh`, `features`, or `zone_geometry_extras`).
  - Round-trip: `options_for_enemy(slug, json.loads(json.dumps(options_for_enemy(slug, {}))))` returns the same dict as `options_for_enemy(slug, {})` for all six new keys.
- **Assumptions:** Python `json.dumps` serializes `True`/`False` as `true`/`false` natively. The coercion in `_coerce_boolish` produces Python `bool`, ensuring this holds.
- **Scope:** `options_for_enemy`, `_coerce_and_validate`, `_defaults_for_slug` in `animated_build_options.py`.

### 2. Acceptance Criteria

**MTE-9-AC-1:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"mouth_enabled": false` (JSON boolean, not integer 0).

**MTE-9-AC-2:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"tail_enabled": false` (JSON boolean, not integer 0).

**MTE-9-AC-3:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"mouth_shape": "smile"`.

**MTE-9-AC-4:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"tail_shape": "spike"`.

**MTE-9-AC-5:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"tail_length": 1.0`.

**MTE-9-AC-6:** For every animated enemy slug, `type(options_for_enemy(slug, {})["mouth_enabled"]) is bool` is `True`.

**MTE-9-AC-7:** For every animated enemy slug, `type(options_for_enemy(slug, {})["tail_enabled"]) is bool` is `True`.

**MTE-9-AC-8:** For every animated enemy slug, `type(options_for_enemy(slug, {})["tail_length"]) is float` is `True`.

**MTE-9-AC-9:** Nested input format accepted: `options_for_enemy("spider", {"spider": {"mouth_enabled": True, "mouth_shape": "grimace", "tail_enabled": True, "tail_shape": "curled", "tail_length": 2.0}})` returns a dict where `mouth_enabled is True`, `mouth_shape == "grimace"`, `tail_enabled is True`, `tail_shape == "curled"`, `tail_length == 2.0`.

**MTE-9-AC-10:** Round-trip invariant: for every animated enemy slug `s` and any dict of valid values `o`, `options_for_enemy(s, json.loads(json.dumps(options_for_enemy(s, o)))) == options_for_enemy(s, o)`.

### 3. Risk & Ambiguity Analysis

- **`bool` vs. `int` in JSON:** Python's `json.dumps` serializes `True` as `true`. If `mouth_enabled` or `tail_enabled` is stored as `int` (1/0), it serializes as `1`/`0`. The `_coerce_boolish` function must produce a Python `bool`, not an `int`. This is guaranteed by the existing implementation but must be preserved in the new code path.
- **`tail_length` as `float` in JSON:** `json.dumps` serializes Python `float` as a JSON number. If `tail_length` is `1.0` and stored as `int` after coercion, `json.dumps` would emit `1` (integer). The `float` branch in `_coerce_and_validate` calls `max(lo, min(hi, v))` where `lo` and `hi` are `float`, so the result is always a `float`. This is correct behavior; no special handling needed.

### 4. Clarifying Questions

None.

---

## Requirement MTE-10: Frontend Conditional Disabling Logic

### 1. Spec Summary

- **Description:** The `buildControlDisabled` function in `BuildControls.tsx` is extended so that `mouth_shape` is disabled when `mouth_enabled` is falsy, and `tail_shape` and `tail_length` are disabled when `tail_enabled` is falsy.
- **Constraints:**
  - `mouth_shape` is disabled when `!values["mouth_enabled"]` (any falsy value including `undefined`, `false`, `0`, empty string).
  - `tail_shape` is disabled when `!values["tail_enabled"]`.
  - `tail_length` is disabled when `!values["tail_enabled"]`.
  - `mouth_enabled` itself is never disabled (it is the toggle).
  - `tail_enabled` itself is never disabled (it is the toggle).
  - The visual effect of "disabled" is the existing pattern: `opacity: 0.42` and `pointerEvents: "none"` applied to the control row. No CSS changes are required — the existing `buildControlDisabled` mechanism already produces this effect.
  - No new TypeScript types are required (`bool`, `select_str`, `float` control types already declared).
  - The three new rules are additions only; no existing disabling rules are removed or modified.
  - The change is exactly three guard conditions added to `buildControlDisabled`, following the existing `pupil_shape` pattern.
- **Assumptions:**
  - `AnimatedBuildControlDef` type in `types/index.ts` already declares the `bool` variant (confirmed).
  - The `nonFloat` rendering loop in `BuildControls.tsx` already calls `buildControlDisabled` and applies opacity/pointer-events.
  - `tail_length` is a float-type control. The `float` block rendering loop must also call `buildControlDisabled` and apply the disabled style for `tail_length`. If the float block does not currently call `buildControlDisabled`, it must be updated.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx`

### 2. Acceptance Criteria

**MTE-10-AC-1:** `buildControlDisabled(slug, "mouth_shape", { mouth_enabled: false })` returns `true` for any slug value.

**MTE-10-AC-2:** `buildControlDisabled(slug, "mouth_shape", { mouth_enabled: true })` returns `false` for any slug value.

**MTE-10-AC-3:** `buildControlDisabled(slug, "mouth_shape", {})` (absent key) returns `true` for any slug value (absent `mouth_enabled` is treated as falsy).

**MTE-10-AC-4:** `buildControlDisabled(slug, "mouth_enabled", { mouth_enabled: false })` returns `false` — the toggle itself is never disabled by this rule.

**MTE-10-AC-5:** `buildControlDisabled(slug, "tail_shape", { tail_enabled: false })` returns `true` for any slug value.

**MTE-10-AC-6:** `buildControlDisabled(slug, "tail_shape", { tail_enabled: true })` returns `false` for any slug value.

**MTE-10-AC-7:** `buildControlDisabled(slug, "tail_length", { tail_enabled: false })` returns `true` for any slug value.

**MTE-10-AC-8:** `buildControlDisabled(slug, "tail_length", { tail_enabled: true })` returns `false` for any slug value.

**MTE-10-AC-9:** `buildControlDisabled(slug, "tail_shape", {})` (absent key) returns `true` for any slug value.

**MTE-10-AC-10:** `buildControlDisabled(slug, "tail_length", {})` (absent key) returns `true` for any slug value.

**MTE-10-AC-11:** `buildControlDisabled(slug, "mouth_shape", { tail_enabled: false })` returns `false` — `tail_enabled` does NOT disable `mouth_shape` (no bleed-over).

**MTE-10-AC-12:** `buildControlDisabled(slug, "tail_shape", { mouth_enabled: false })` returns `false` — `mouth_enabled` does NOT disable `tail_shape` (no bleed-over).

**MTE-10-AC-13:** The existing `pupil_shape` disabling rule (`!values["pupil_enabled"]`) is not modified.

**MTE-10-AC-14:** The existing spider placement row disabling logic (`spiderPlacementRowDisabled`) is not modified.

**MTE-10-AC-15:** `buildControlDisabled("spider", "eye_distribution", { eye_count: 1 })` continues to return `true` (regression check on existing logic).

**MTE-10-AC-16:** When `tail_length` control row is rendered with `tail_enabled=false`, it has `opacity: 0.42` and `pointerEvents: "none"` in the DOM (visual disabled state).

### 3. Risk & Ambiguity Analysis

- **`tail_length` is a float-type control:** Float controls are rendered in the "float" block of `BuildControls.tsx`. If the float block rendering loop does not currently call `buildControlDisabled`, it must be updated to do so for `tail_length` to have a visual disabled state. This is an implementation concern; the spec requires the visual disabled state (MTE-10-AC-16).
- **Value type from store:** `values["tail_enabled"]` may be `boolean`, `undefined`, or (from old serialized state) `0`/`1`. The guard `!values["tail_enabled"]` treats all falsy values as disabled, which is the correct behavior.

### 4. Clarifying Questions

None.

---

## Requirement MTE-11: No Changes to `types/index.ts`

### 1. Spec Summary

- **Description:** `AnimatedBuildControlDef` in `types/index.ts` already declares all required variants including `bool`, `select_str`, and `float`. No changes to this file are required.
- **Constraints:** Do not modify `types/index.ts`.
- **Assumptions:** Confirmed by reading the existing ESPS spec (ESPS-9-AC-1) which froze this file.
- **Scope:** N/A.

### 2. Acceptance Criteria

**MTE-11-AC-1:** `types/index.ts` is not modified.

### 3. Risk & Ambiguity Analysis

None.

### 4. Clarifying Questions

None.

---

## Constant Inventory

The following module-level constants must be introduced. All are in `asset_generation/python/src/core/blender_utils.py` unless noted otherwise.

| Constant name | Required constraint | Location | Purpose |
|---|---|---|---|
| `_MOUTH_SMILE_X_RATIO` | Must be > `_MOUTH_SMILE_Z_RATIO` (wide, thin) | `blender_utils.py` | X-scale for smile cylinder |
| `_MOUTH_SMILE_Y_RATIO` | Must be > `_MOUTH_SMILE_Z_RATIO` | `blender_utils.py` | Y-scale for smile cylinder |
| `_MOUTH_SMILE_Z_RATIO` | Must be < both X and Y ratios | `blender_utils.py` | Z-scale (thin depth) for smile |
| `_MOUTH_GRIMACE_X_RATIO` | Implementation choice | `blender_utils.py` | X-scale for grimace cylinder |
| `_MOUTH_GRIMACE_Y_RATIO` | Implementation choice | `blender_utils.py` | Y-scale for grimace cylinder |
| `_MOUTH_GRIMACE_Z_RATIO` | Must be small (flat) | `blender_utils.py` | Z-scale (thin depth) for grimace |
| `_MOUTH_FLAT_X_RATIO` | Implementation choice | `blender_utils.py` | X-scale for flat box |
| `_MOUTH_FLAT_Y_RATIO` | Implementation choice | `blender_utils.py` | Y-scale for flat box |
| `_MOUTH_FLAT_Z_RATIO` | Must be small | `blender_utils.py` | Z-scale (thin slit) for flat |
| `_MOUTH_FANG_X_RATIO` | Must be < `_MOUTH_BEAK_X_RATIO` | `blender_utils.py` | XY-scale for fang cone |
| `_MOUTH_FANG_Z_RATIO` | Implementation choice | `blender_utils.py` | Z-scale (height) for fang cone |
| `_MOUTH_BEAK_X_RATIO` | Must be > `_MOUTH_FANG_X_RATIO` | `blender_utils.py` | XY-scale for beak cone |
| `_MOUTH_BEAK_Z_RATIO` | Implementation choice | `blender_utils.py` | Z-scale (height) for beak cone |
| `_TAIL_WHIP_XY_RATIO` | Must be < `_TAIL_SEG_XY_RATIO` (thinner) | `blender_utils.py` | XY-scale for whip cylinder |
| `_TAIL_SEG_XY_RATIO` | Must be > `_TAIL_WHIP_XY_RATIO` (wider) | `blender_utils.py` | XY-scale for segmented cylinder |
| `_TAIL_CLUB_Z_RATIO` | Implementation choice | `blender_utils.py` | Z-scale ratio for club sphere |
| `_TAIL_CURLED_X_RATIO` | Implementation choice | `blender_utils.py` | XY-scale for curled sphere |
| `_TAIL_CURLED_Z_RATIO` | Must be < `_TAIL_CURLED_X_RATIO` (flattened) | `blender_utils.py` | Z-scale for curled sphere (flattened) |
| `_MOUTH_SHAPE_OPTIONS` | `("smile", "grimace", "flat", "fang", "beak")` | `animated_build_options.py` | Valid mouth shape option set |
| `_TAIL_SHAPE_OPTIONS` | `("spike", "whip", "club", "segmented", "curled")` | `animated_build_options.py` | Valid tail shape option set |
| `_DEFAULT_MOUTH_SHAPE` | `"smile"` | `animated_build_options.py` | Default mouth shape |
| `_DEFAULT_TAIL_SHAPE` | `"spike"` | `animated_build_options.py` | Default tail shape |
| `_TAIL_LENGTH_MIN` | `0.5` | `animated_build_options.py` | Tail length minimum |
| `_TAIL_LENGTH_MAX` | `3.0` | `animated_build_options.py` | Tail length maximum |
| `_TAIL_LENGTH_DEFAULT` | `1.0` | `animated_build_options.py` | Tail length default |
| `_TAIL_LENGTH_STEP` | `0.05` | `animated_build_options.py` | Tail length slider step |

---

## Slug Coverage Matrix

| Slug | Controls declared | Geometry wired (mouth) | Geometry wired (tail) |
|---|---|---|---|
| `spider` | Yes | Yes | Yes |
| `slug` | Yes | Yes | Yes |
| `claw_crawler` | Yes | Yes | Yes |
| `imp` | Yes | Yes | Yes |
| `carapace_husk` | Yes | Yes | Yes |
| `spitter` | Yes | Yes | Yes |
| `player_slime` | Yes | No | No |

All six animated enemy slugs in `AnimatedEnemyBuilder.ENEMY_CLASSES` receive geometry wiring for both mouth and tail. `player_slime` appears in the controls API but not in `ENEMY_CLASSES`; its builder is not modified.

---

## Control Assembly Ordering

The final per-slug control list produced by `animated_build_controls_for_api()[slug]` must follow this ordering:

1. Non-float static controls (slug-specific, e.g., `eye_count`/`eye_distribution` for spider, `peripheral_eyes` for claw_crawler)
2. `eye_shape` (from `_eye_shape_pupil_control_defs()`)
3. `pupil_enabled` (from `_eye_shape_pupil_control_defs()`)
4. `pupil_shape` (from `_eye_shape_pupil_control_defs()`)
5. `mouth_enabled` (from `_mouth_control_defs()`)
6. `mouth_shape` (from `_mouth_control_defs()`)
7. `tail_enabled` (from `_tail_control_defs()`)
8. `tail_shape` (from `_tail_control_defs()`)
9. Float static controls (slug-specific, e.g., `eye_clustering` for spider)
10. `tail_length` (from `_tail_control_defs()`, float type — lands here)
11. Mesh float controls (from `_mesh_float_control_defs(slug)`)
12. Feature controls (from `_feature_control_defs(slug)`)
13. Part feature controls (from `_part_feature_control_defs(slug)`)
14. Zone extra controls (from `_zone_extra_control_defs(slug)`)
15. Placement seed (from `_placement_seed_def()`)

This ordering follows the existing non-float-before-float split in `animated_build_controls_for_api()`.

---

## API Response Shape

The GET `/api/meta/enemies` response shape does not change. The six new controls are serialized as `AnimatedBuildControlDef[]` entries within the existing `animatedBuildControls[slug]` array. No new top-level keys are added to the `EnemyPreviewMeta` type.

Example output for slug `slug` (excerpt, showing only new entries in order):
```json
[
  { "key": "mouth_enabled", "label": "Mouth", "type": "bool", "default": false },
  { "key": "mouth_shape", "label": "Mouth shape", "type": "select_str", "options": ["smile", "grimace", "flat", "fang", "beak"], "default": "smile" },
  { "key": "tail_enabled", "label": "Tail", "type": "bool", "default": false },
  { "key": "tail_shape", "label": "Tail shape", "type": "select_str", "options": ["spike", "whip", "club", "segmented", "curled"], "default": "spike" },
  { "key": "tail_length", "label": "Tail length", "type": "float", "min": 0.5, "max": 3.0, "step": 0.05, "default": 1.0 }
]
```

---

## Material Zone Assignment

- **Mouth parts:** Assigned the `head` zone material in `apply_themed_materials`. Rationale: mouth is a head-zone feature. No new material zone is introduced.
- **Tail parts:** Assigned the `body` zone material in `apply_themed_materials`. Rationale: tail is a body-zone feature. No new material zone is introduced.
- Mouth and tail parts are appended AFTER all existing parts (body, head, limbs, joints, stalks, eyes, pupils, zone extras). This preserves all existing index-based material assignments.

---

## Deferred Boundary Statement

The following items are explicitly out of scope for this ticket:

1. Mouth animation (chewing, open/close) — deferred to a future milestone.
2. Tail physics or runtime motion — geometry placement only.
3. Per-enemy asymmetric tail placement — all tails exit from -X axis.
4. New color controls for mouth or tail — both inherit existing zone colors.
5. UI indicator to inform users that `player_slime` controls have no geometry effect.
6. `types/index.ts` modifications — all required TypeScript control types already exist.
