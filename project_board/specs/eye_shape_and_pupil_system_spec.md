# Eye Shape & Pupil System Spec

**Ticket:** `project_board/25_milestone_25_enemy_editor_visual_expression/backlog/01_eye_shape_and_pupil_system.md`
**Spec version:** 1
**Author:** Spec Agent
**Date:** 2026-04-14

---

## Scope & Boundaries

This spec covers:
- Three new Python build controls: `eye_shape`, `pupil_enabled`, `pupil_shape`
- Per-slug default values
- Serialization contract and coercion rules
- Geometry implementation strategy for each eye shape variant
- Pupil mesh placement strategy
- Which enemy slugs receive geometry effects vs. controls-only declarations
- Frontend conditional disabling logic

Out of scope (per ticket):
- Eye color (owned by existing color system; no new controls added here)
- Blinking, tracking, or any eye animation (deferred to M26)
- Per-eye asymmetry; both eyes on a given enemy share the same `eye_shape` / `pupil_*` settings
- Enemys that have no explicit eye sub-mesh (imp, spitter, carapace_husk): controls are declared but geometry effects are not wired in this ticket

---

## Requirement ESPS-1: Python Build Control Declarations

### 1. Spec Summary

- **Description:** Three new `AnimatedBuildControlDef`-compatible control entries are declared for every animated enemy slug: `eye_shape`, `pupil_enabled`, and `pupil_shape`. They are emitted from `animated_build_controls_for_api()` and their defaults are emitted from `_defaults_for_slug()`.
- **Constraints:**
  - The controls follow the exact `dict[str, Any]` shape that existing entries in `_ANIMATED_BUILD_CONTROLS` and `_spider_eye_control_defs()` use.
  - A new private helper function `_eye_shape_pupil_control_defs()` returns a `list[dict[str, Any]]` containing all three entries. It is called from `animated_build_controls_for_api()` for every slug.
  - The helper must not import any enemy class (no lazy import). All values are module-level constants.
  - `eye_shape` uses type `"select_str"`.
  - `pupil_enabled` uses type `"bool"`.
  - `pupil_shape` uses type `"select_str"`.
- **Assumptions:**
  - The `bool` type is already handled by `_coerce_and_validate` (confirmed: the `bool` branch exists in `BuildControlRow.tsx`; the Python-side coercion gap is addressed in ESPS-2).
  - `player_slime` is included in the slug set returned by `animated_build_controls_for_api()` and must also receive the three controls.
- **Scope:** `asset_generation/python/src/utils/animated_build_options.py`

### 2. Acceptance Criteria

**ESPS-1-AC-1:** `animated_build_controls_for_api()[slug]` for every slug in the system (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime) contains exactly one entry with `key == "eye_shape"`, one with `key == "pupil_enabled"`, and one with `key == "pupil_shape"`.

**ESPS-1-AC-2:** The `eye_shape` control entry has the following exact shape:
```
{
    "key": "eye_shape",
    "label": "Eye shape",
    "type": "select_str",
    "options": ["circle", "oval", "slit", "square"],
    "default": "circle",
}
```

**ESPS-1-AC-3:** The `pupil_enabled` control entry has the following exact shape:
```
{
    "key": "pupil_enabled",
    "label": "Pupil",
    "type": "bool",
    "default": False,
}
```

**ESPS-1-AC-4:** The `pupil_shape` control entry has the following exact shape:
```
{
    "key": "pupil_shape",
    "label": "Pupil shape",
    "type": "select_str",
    "options": ["dot", "slit", "diamond"],
    "default": "dot",
}
```

**ESPS-1-AC-5:** `_defaults_for_slug(slug)` for every slug returns a dict that includes `"eye_shape": "circle"`, `"pupil_enabled": False`, and `"pupil_shape": "dot"`.

**ESPS-1-AC-6:** The three controls appear together, in the order `eye_shape` → `pupil_enabled` → `pupil_shape`, within the control list returned per slug. They must appear before the mesh float controls (i.e., before entries from `_mesh_float_control_defs`).

**ESPS-1-AC-7:** The helper function is named `_eye_shape_pupil_control_defs` and returns `list[dict[str, Any]]`. It takes no arguments.

### 3. Risk & Ambiguity Analysis

- **Position in control list:** The three new controls are appended after slug-specific static controls (e.g., after `_spider_eye_control_defs()` for spider, after `_ANIMATED_BUILD_CONTROLS.get(slug, [])` for others). See ESPS-1-AC-6 for ordering requirement.
- **`player_slime`:** This slug has limited zones and no explicit eye mesh; the controls are declared for completeness (consistent with declaration-first, geometry-second pattern already used for zone extras). Geometry effects are not wired for `player_slime`.
- **Existing `spider` branch in `animated_build_controls_for_api`:** The spider branch currently sets `static = _spider_eye_control_defs()`. The three new controls are appended after this existing set, not inside `_spider_eye_control_defs()`.

### 4. Clarifying Questions

None. Resolved by checkpoint log `M25-ESPS/run-2026-04-14T18-00-00Z-planning.md` (assumption: universal declaration, geometry effects gated per slug in builder).

---

## Requirement ESPS-2: Python Coercion and Validation

### 1. Spec Summary

- **Description:** `_coerce_and_validate` and `options_for_enemy` correctly handle the three new keys. `eye_shape` and `pupil_shape` are coerced as `select_str`. `pupil_enabled` is coerced as `bool` using the existing `_coerce_boolish` helper.
- **Constraints:**
  - `_coerce_and_validate` currently does not have a `bool` branch. One must be added.
  - The `bool` branch must call `_coerce_boolish(out[key], default=c.get("default", False))`.
  - `options_for_enemy` must add `"eye_shape"`, `"pupil_enabled"`, and `"pupil_shape"` to `allowed_non_mesh` for every slug (not just spider). This requires that the new controls appear in the control list iterated to build `allowed_non_mesh`.
  - Invalid `eye_shape` string (e.g., `"triangle"`) falls back to `"circle"` (the declared default).
  - Invalid `pupil_shape` string falls back to `"dot"` (the declared default).
  - Any truthy value for `pupil_enabled` coerces to `True`; falsy coerces to `False`.
- **Assumptions:** `_coerce_boolish` already handles `bool`, `int`, `float`, and `str` input types (confirmed by reading the implementation).
- **Scope:** `asset_generation/python/src/utils/animated_build_options.py` (`_coerce_and_validate`, `options_for_enemy`, `_defaults_for_slug`)

### 2. Acceptance Criteria

**ESPS-2-AC-1:** `options_for_enemy("spider", {"eye_shape": "INVALID"})["eye_shape"]` returns `"circle"`.

**ESPS-2-AC-2:** `options_for_enemy("slug", {"eye_shape": "square"})["eye_shape"]` returns `"square"`.

**ESPS-2-AC-3:** `options_for_enemy("spider", {"pupil_enabled": True})["pupil_enabled"]` returns `True` (Python bool, not int).

**ESPS-2-AC-4:** `options_for_enemy("spider", {"pupil_enabled": "yes"})["pupil_enabled"]` returns `True`.

**ESPS-2-AC-5:** `options_for_enemy("spider", {"pupil_enabled": 0})["pupil_enabled"]` returns `False`.

**ESPS-2-AC-6:** `options_for_enemy("claw_crawler", {})["pupil_enabled"]` returns `False`.

**ESPS-2-AC-7:** `options_for_enemy("claw_crawler", {"pupil_shape": "NOTREAL"})["pupil_shape"]` returns `"dot"`.

**ESPS-2-AC-8:** Round-trip: `json.dumps(options_for_enemy("spider", {}))` does not raise and the serialized output contains `"eye_shape": "circle"`, `"pupil_enabled": false`, `"pupil_shape": "dot"`. Note: Python `False` must serialize as JSON `false`. `bool` must not be stored as an integer in the output dict.

**ESPS-2-AC-9:** All existing tests in `asset_generation/python/tests/` continue to pass after the change.

### 3. Risk & Ambiguity Analysis

- **`bool` type in `_coerce_and_validate`:** The function iterates `static_defs` and currently handles `int`, `float`, `select`, `select_str` types. Adding `bool` requires a new branch. The coercion must produce a Python `bool` (not `int`) so JSON serialization emits `false`/`true`.
- **`allowed_non_mesh` construction in `options_for_enemy`:** Currently, the spider branch reads `_spider_eye_control_defs()` and all other slugs read `_ANIMATED_BUILD_CONTROLS.get(enemy_type, [])`. For the three new keys to be recognized in non-mesh routing, the loop that builds `allowed_non_mesh` must iterate over the merged control list that includes `_eye_shape_pupil_control_defs()`. Implementation must ensure this does not break existing key routing.

### 4. Clarifying Questions

None.

---

## Requirement ESPS-3: Geometry Strategy — Eye Shape Variants

### 1. Spec Summary

- **Description:** The Python enemy builders for spider, slug, and claw_crawler read the `eye_shape` build option and vary the mesh primitive used (or the scale arguments) for each eye mesh object they create.
- **Constraints:**
  - The geometry effect is applied only in builders that have explicit eye sub-mesh creation loops: `AnimatedSpider.build_mesh_parts` (eye loop), `AnimatedSlug.build_mesh_parts` (stalk+eye pair loop), `AnimatedClawCrawler.build_mesh_parts` (peripheral_eyes loop).
  - imp, spitter, carapace_husk: controls are declared but **no geometry changes** are made to these builders in this ticket. They are controls-only slugs.
  - The shared eye shape logic is extracted into a module-level helper (not a method) to avoid code duplication across the three builders. Recommended location: a new module `asset_generation/python/src/enemies/eye_geometry.py` or a new function `create_eye_mesh` added directly to `asset_generation/python/src/core/blender_utils.py`. The choice is resolved in ESPS-3-AC-1.
  - The helper takes `shape: str`, `eye_scale: float`, `location: tuple[float, float, float]` and returns a Blender object.
  - Each shape must use available primitives from `blender_utils.py` (`create_sphere`, `create_box`, `create_cylinder`).
- **Assumptions:**
  - `eye_scale` is a scalar representing the radius/half-extent of the eye. Scale values passed to each primitive are derived from this scalar.
  - The default (`circle`) must produce identical output to the existing `create_sphere` calls so that no regression occurs in the default state.
- **Scope:** `animated_spider.py`, `animated_slug.py`, `animated_claw_crawler.py`, plus the new helper location.

### 2. Acceptance Criteria

**ESPS-3-AC-1:** A new function `create_eye_mesh(shape: str, location: tuple, eye_scale: float)` is added to `asset_generation/python/src/core/blender_utils.py`. It takes three positional arguments and returns the Blender object created.

**ESPS-3-AC-2:** `create_eye_mesh` dispatches to Blender primitives as follows:

| `shape` value | Primitive | Scale arguments |
|---|---|---|
| `"circle"` | `create_sphere` | `(eye_scale, eye_scale, eye_scale)` — uniform sphere, identical to current behavior |
| `"oval"` | `create_sphere` | `(eye_scale * 1.4, eye_scale, eye_scale * 0.85)` — elongated along X (forward-facing axis) |
| `"slit"` | `create_sphere` | `(eye_scale, eye_scale * 0.35, eye_scale)` — narrow along Y (side axis), giving a vertical slit silhouette |
| `"square"` | `create_box` | `(eye_scale, eye_scale, eye_scale)` — cubic box |

If `shape` is not one of the four values, `create_eye_mesh` falls back to `"circle"` behavior.

**ESPS-3-AC-3:** `AnimatedSpider.build_mesh_parts` replaces `create_sphere(location=..., scale=(eye_scale, eye_scale, eye_scale))` per-eye with `create_eye_mesh(shape, tuple(eye_center), eye_scale)` where `shape = self.build_options.get("eye_shape", "circle")`.

**ESPS-3-AC-4:** `AnimatedSlug.build_mesh_parts` replaces the `eye = create_sphere(...)` call inside the `for side in [-1, 1]` loop with `create_eye_mesh(shape, eye_location, eye_scale)`. The stalk cylinder is not affected.

**ESPS-3-AC-5:** `AnimatedClawCrawler.build_mesh_parts` replaces `eye = create_sphere(...)` inside the `for i in range(self._peripheral_eyes)` loop with `create_eye_mesh(shape, eye_location, eye_scale)`.

**ESPS-3-AC-6:** When `eye_shape` is `"circle"` (default), the part count and positions produced by each builder are identical to the pre-change output. No regression in default behavior.

**ESPS-3-AC-7:** `AnimatedSpider`, `AnimatedSlug`, and `AnimatedClawCrawler` import `create_eye_mesh` from `..core.blender_utils` alongside the existing `create_sphere` import.

### 3. Risk & Ambiguity Analysis

- **`oval` scale ratios:** The values `(1.4, 1.0, 0.85)` are design choices. They must be module-level named constants in `blender_utils.py` (e.g., `_EYE_OVAL_SCALE_X = 1.4`, `_EYE_OVAL_SCALE_Y = 1.0`, `_EYE_OVAL_SCALE_Z = 0.85`) so they are not bare tuning literals. Same applies to slit and any other non-trivial ratios.
- **`slit` axis orientation:** The Y-narrow choice (squish along Y) means the eye is a thin vertical disc from the front-facing (+X) view. If the design intent was a horizontal slit, the Z axis should be narrowed instead. This spec assumes vertical-slit (narrow Y) because enemy eyes are viewed front-on from +X and a vertical slit resembles a cat/reptile eye. If the implementer has a different interpretation, they must flag it before implementing.
- **`square` via `create_box`:** `create_box` already exists in `blender_utils.py`. The eye size is passed as the cube edge length. No new primitive is required.
- **Location tuple:** `create_sphere` and `create_box` both accept `location=(x, y, z)`. The caller (builder) computes `eye_location` the same way it currently computes the location for `create_sphere`. This is a direct substitution.

### 4. Clarifying Questions

None. Resolved by checkpoint assumption (geometry-via-scale for sphere shapes, `create_box` for square).

---

## Requirement ESPS-4: Geometry Strategy — Pupil Mesh

### 1. Spec Summary

- **Description:** When `pupil_enabled` is `True`, each eye mesh object in the three geometry-wired builders is followed by a pupil mesh object appended to `self.parts`. The pupil mesh is a small, flat shape placed on the front-facing surface of the eye.
- **Constraints:**
  - Pupil meshes are only created when `pupil_enabled` is `True`. No pupil is created when `pupil_enabled` is `False` (default). This must produce zero change to existing part counts when `pupil_enabled` is `False`.
  - A pupil mesh is added for every eye mesh created. If a spider has 4 eyes, 4 pupil meshes are appended (one after each eye in the parts list).
  - Pupil mesh placement: the pupil center is located at the point on the front-facing surface of the eye ellipsoid in the direction of `+X` (the forward axis in the Blender scene coordinate system), offset by a small epsilon to sit just above the eye surface. The exact offset is `pupil_z_offset = eye_scale * 0.05` added along the approach direction to prevent Z-fighting.
  - For slug eyes specifically: the pupil faces in the `+Z` direction (upward) since the stalk eye is at the top. The pupil center is offset `eye_scale * 0.05` along `+Z` from the stalk eye center.
  - Pupil mesh placement reuses the `_point_on_ellipsoid_surface` method from `AnimatedSpider` for the spider builder. For the slug and claw_crawler builders, the placement uses a direct vector computation (not `_point_on_ellipsoid_surface`) since they are in separate classes.
  - A new module-level helper `create_pupil_mesh(shape: str, location: tuple, pupil_scale: float)` is added to `blender_utils.py` alongside `create_eye_mesh`.
  - Pupil scale is `eye_scale * _PUPIL_EYE_SCALE_RATIO` where `_PUPIL_EYE_SCALE_RATIO = 0.35` is a module-level constant.
  - Material for pupil parts: pupil meshes receive the `"head"` zone material (same as the head sphere). No new material zone is created in this ticket.
- **Assumptions:**
  - No pupil geometry is added for imp, spitter, or carapace_husk in this ticket.
  - The pupil mesh is always a separate Blender object (not a boolean modifier or material effect). This is consistent with how all other sub-meshes are handled in this codebase.
- **Scope:** `blender_utils.py` (new `create_pupil_mesh` function), `animated_spider.py`, `animated_slug.py`, `animated_claw_crawler.py`.

### 2. Acceptance Criteria

**ESPS-4-AC-1:** A new function `create_pupil_mesh(shape: str, location: tuple, pupil_scale: float)` is added to `asset_generation/python/src/core/blender_utils.py`. It returns the Blender object created.

**ESPS-4-AC-2:** `create_pupil_mesh` dispatches as follows:

| `pupil_shape` value | Primitive | Scale arguments |
|---|---|---|
| `"dot"` | `create_sphere` | `(pupil_scale, pupil_scale, pupil_scale * 0.3)` — flat disc sphere |
| `"slit"` | `create_cylinder` | `scale=(pupil_scale * 0.25, pupil_scale, pupil_scale * 0.05)`, `vertices=8`, `depth=2.0` — thin vertical slit cylinder |
| `"diamond"` | `create_box` | `(pupil_scale * 0.6, pupil_scale * 0.25, pupil_scale * 0.9)` — tall narrow box approximating diamond |

If `shape` is not one of the three values, fall back to `"dot"` behavior. The scale ratio constants for each shape variant must be module-level named constants (e.g., `_PUPIL_DOT_Z_RATIO = 0.3`).

**ESPS-4-AC-3:** In `AnimatedSpider.build_mesh_parts`, after appending each eye part, if `pupil_enabled` is `True`: compute `pupil_center` as `eye_center + eye_dir * (eye_scale + eye_scale * 0.05)` (moving along the approach direction by the eye radius plus epsilon). Append `create_pupil_mesh(pupil_shape, tuple(pupil_center), pupil_scale)` to `self.parts`.

**ESPS-4-AC-4:** In `AnimatedSlug.build_mesh_parts`, after appending each eye sphere, if `pupil_enabled` is `True`: `pupil_center = (stalk_x, stalk_y, eye_z + eye_scale + eye_scale * 0.05)`. Append `create_pupil_mesh(pupil_shape, pupil_center, pupil_scale)` to `self.parts`.

**ESPS-4-AC-5:** In `AnimatedClawCrawler.build_mesh_parts`, after appending each peripheral eye, if `pupil_enabled` is `True`: `pupil_center = (eye_loc_x + eye_scale + eye_scale * 0.05, eye_loc_y, eye_loc_z)`. Append `create_pupil_mesh(pupil_shape, pupil_center, pupil_scale)` to `self.parts`.

**ESPS-4-AC-6:** When `pupil_enabled` is `False` (default): zero pupil parts are created. The total part count for each builder is identical to the pre-change output.

**ESPS-4-AC-7:** When `pupil_enabled` is `True`: the total part count increases by exactly N, where N is the number of eye meshes created for that enemy instance (e.g., spider with `eye_count=2` gains 2 pupil parts; slug always gains 2; claw_crawler with `peripheral_eyes=1` gains 1).

**ESPS-4-AC-8:** `apply_themed_materials` in each builder correctly accounts for pupil parts. In spider: pupil parts follow each eye part in the `parts` list; `apply_themed_materials` assigns the `head` material to each pupil part. The material application loop must be updated to iterate the correct indices. In slug: the `enumerate(self.parts[2:])` pattern in `apply_themed_materials` must treat pupil parts (after each eye) as receiving the `head` material. In claw_crawler: pupil parts are interleaved with peripheral eye parts; the `_peripheral_eyes` loop in `apply_themed_materials` must apply eye material to eye parts and `head` material to pupil parts.

**ESPS-4-AC-9:** Pupil part count per eye is always exactly 1 (one pupil mesh per eye, regardless of `pupil_shape`).

### 3. Risk & Ambiguity Analysis

- **Part list ordering in spider:** The spider `apply_themed_materials` currently uses fixed offsets (`parts[0]` = body, `parts[1]` = head, `parts[2..2+ec-1]` = eyes, then legs). If pupil parts are inserted immediately after each eye in the build loop, the material application loop must be updated accordingly. The safest approach: insert all `eye_count` eyes first, then all `eye_count` pupils. This keeps the existing eye index range contiguous and adds a new pupil range immediately after. The spec mandates this ordering: all eyes first, all pupils second, then legs. This is a deviation from a per-eye/per-pupil interleaving approach, chosen to minimize disruption to the material index arithmetic.
- **Slug part ordering:** Currently `self.parts[2:]` alternates stalk (even), eye (odd). With pupils, the order becomes stalk, eye, pupil (repeating). `apply_themed_materials` uses `i % 2` to distinguish stalks from eyes; this will break if pupils are inserted. The spec mandates: slug part layout becomes stalk, eye, pupil for each side. The `apply_themed_materials` modulo pattern must change from `% 2` to `% 3` (0=stalk, 1=eye, 2=pupil), or switch to explicit counting. Implementation must choose one approach and be consistent with test expectations.
- **Claw_crawler part ordering:** Peripheral eyes are in a contiguous range. With pupils, each eye is immediately followed by its pupil in the range. The material loop must iterate pairs.
- **`_PUPIL_EYE_SCALE_RATIO` tuning:** `0.35` is a design choice that must be declared as a module-level constant to satisfy the reviewer policy on unexplained tuning literals.
- **`slit` pupil cylinder orientation:** `create_cylinder` in Blender creates a cylinder along the Z axis by default. A "slit" pupil should appear as a tall thin vertical mark on the eye surface. Scale `(width=0.25, depth=0.25, height=1.0) * pupil_scale` with a thin Z scale achieves a disc; the values in ESPS-4-AC-2 produce a coin-shaped slit. Implementation may adjust these ratios but must document any deviation as a checkpoint.

### 4. Clarifying Questions

None beyond the risks documented above.

---

## Requirement ESPS-5: Serialization Contract

### 1. Spec Summary

- **Description:** The three new keys are serialized to and from enemy config JSON in the same way as all other build options. No new JSON structure is introduced.
- **Constraints:**
  - `eye_shape`, `pupil_enabled`, `pupil_shape` are top-level keys in the enemy options dict (not nested under `mesh`, `features`, or `zone_geometry_extras`).
  - `pupil_enabled` serializes as a JSON boolean (`true`/`false`), not as a number.
  - `eye_shape` and `pupil_shape` serialize as JSON strings.
  - Round-trip: `options_for_enemy(slug, json.loads(json.dumps(options_for_enemy(slug, {}))))` returns the same dict as `options_for_enemy(slug, {})`.
- **Assumptions:** No assumptions. Behavior is consistent with the existing `select_str` and `bool` patterns already in the codebase.
- **Scope:** `options_for_enemy`, `_coerce_and_validate`, `_defaults_for_slug` in `animated_build_options.py`.

### 2. Acceptance Criteria

**ESPS-5-AC-1:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"eye_shape": "circle"`.

**ESPS-5-AC-2:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"pupil_enabled": false` (JSON boolean, not integer 0).

**ESPS-5-AC-3:** `json.dumps(options_for_enemy("spider", {}))` produces a JSON string containing `"pupil_shape": "dot"`.

**ESPS-5-AC-4:** For every animated enemy slug, `options_for_enemy(slug, {})` returns a dict where `type(d["pupil_enabled"]) is bool` is `True`.

**ESPS-5-AC-5:** Round-trip invariant: for every animated enemy slug `s` and any valid options dict `o` where `eye_shape`, `pupil_enabled`, `pupil_shape` are set to valid values, `options_for_enemy(s, json.loads(json.dumps(options_for_enemy(s, o)))) == options_for_enemy(s, o)`.

**ESPS-5-AC-6:** Nested input format: `options_for_enemy("spider", {"spider": {"eye_shape": "oval", "pupil_enabled": True, "pupil_shape": "slit"}})` returns a dict where `eye_shape == "oval"`, `pupil_enabled == True`, `pupil_shape == "slit"`.

### 3. Risk & Ambiguity Analysis

- **`bool` vs `int` JSON serialization:** Python `json.dumps` serializes `True` as `true` and `False` as `false`. If `pupil_enabled` is stored as `int` (1 or 0), it serializes as `1`/`0`. The coercion in `_coerce_and_validate` must produce a Python `bool`, not an `int`.

### 4. Clarifying Questions

None.

---

## Requirement ESPS-6: Per-Slug Defaults

### 1. Spec Summary

- **Description:** Defaults for the three new controls are uniform across all slugs. There are no per-slug overrides.
- **Constraints:**
  - `eye_shape` default: `"circle"` for all slugs.
  - `pupil_enabled` default: `False` for all slugs.
  - `pupil_shape` default: `"dot"` for all slugs.
  - These are the values returned by `_defaults_for_slug(slug)` and also by `options_for_enemy(slug, {})`.
- **Assumptions:** No per-slug default variation is needed for this ticket. If a future ticket wants different defaults per slug, the `_defaults_for_slug` function can be extended.
- **Scope:** `_defaults_for_slug` in `animated_build_options.py`.

### 2. Acceptance Criteria

**ESPS-6-AC-1:** For every animated enemy slug (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime): `_defaults_for_slug(slug)["eye_shape"] == "circle"`.

**ESPS-6-AC-2:** For every animated enemy slug: `_defaults_for_slug(slug)["pupil_enabled"] is False` (Python `False`).

**ESPS-6-AC-3:** For every animated enemy slug: `_defaults_for_slug(slug)["pupil_shape"] == "dot"`.

### 3. Risk & Ambiguity Analysis

None.

### 4. Clarifying Questions

None.

---

## Requirement ESPS-7: Controls-Only Slugs (imp, spitter, carapace_husk, player_slime)

### 1. Spec Summary

- **Description:** The slugs imp, spitter, carapace_husk, and player_slime receive the three control declarations and correct defaults, but their Python geometry builders are NOT modified in this ticket. Eye shape and pupil options have no visual effect on these enemies until a future ticket wires the geometry.
- **Constraints:**
  - No changes to `animated_imp.py`, `animated_spitter.py`, `animated_carapace_husk.py`, or any player slime builder files in this ticket.
  - Controls are declared so the frontend renders the controls for these slugs; the controls simply have no effect on the rendered geometry.
- **Assumptions:** This is consistent with the ticket scope as stated: "Scope Notes — No per-eye asymmetry controls." The controls-only declaration pattern is already used for zone extras where `kind = "none"` has no effect.
- **Scope:** Declaration only. No builder changes for these slugs.

### 2. Acceptance Criteria

**ESPS-7-AC-1:** `animated_imp.py`, `animated_spitter.py`, `animated_carapace_husk.py` are not modified.

**ESPS-7-AC-2:** `animated_build_controls_for_api()["imp"]` contains `eye_shape`, `pupil_enabled`, `pupil_shape` entries.

**ESPS-7-AC-3:** `options_for_enemy("imp", {"eye_shape": "square", "pupil_enabled": True})` returns a dict with `eye_shape == "square"` and `pupil_enabled is True` (i.e., the values are stored and returned correctly, even though the builder does not use them).

### 3. Risk & Ambiguity Analysis

- **UX implication:** The frontend will render the controls for imp/spitter/carapace_husk, but changing them will produce no visible change in the 3D preview. This may confuse users. A future ticket may add a visual indicator or disable the controls for these slugs. This ticket does not address this gap.

### 4. Clarifying Questions

None.

---

## Requirement ESPS-8: Frontend — Conditional Disabling Logic

### 1. Spec Summary

- **Description:** The `buildControlDisabled` function in `BuildControls.tsx` is extended so that `pupil_shape` is disabled when `pupil_enabled` is `false` or absent.
- **Constraints:**
  - `pupil_shape` must be visually disabled (opacity + pointer-events: none, same pattern used for spider multi-eye controls) when the current value of `pupil_enabled` for the active slug is falsy.
  - This conditional applies to all slugs, not just spider.
  - No new tab is introduced. The three controls appear in the existing "Build" control panel (`BuildControls.tsx`), under the `nonFloat` block (all three are non-float types).
  - `eye_shape` is always enabled regardless of other control values.
  - `pupil_enabled` is always enabled (it is the toggle that controls disabling).
  - `ControlRow` in `BuildControlRow.tsx` already has a `bool` branch that renders a checkbox. No changes to `BuildControlRow.tsx` are required unless a regression is found during implementation.
- **Assumptions:**
  - `AnimatedBuildControlDef` type in `types/index.ts` already declares the `bool` variant (confirmed by reading the file).
  - The existing `nonFloat` rendering loop in `BuildControls.tsx` already calls `buildControlDisabled` and applies opacity/pointer-events. The new `pupil_shape` disabling integrates into this existing mechanism.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx`

### 2. Acceptance Criteria

**ESPS-8-AC-1:** `buildControlDisabled(slug, "pupil_shape", { pupil_enabled: false })` returns `true` for any slug value.

**ESPS-8-AC-2:** `buildControlDisabled(slug, "pupil_shape", { pupil_enabled: true })` returns `false` for any slug value.

**ESPS-8-AC-3:** `buildControlDisabled(slug, "pupil_shape", {})` (absent key) returns `true` for any slug value (absent `pupil_enabled` is treated as `false`).

**ESPS-8-AC-4:** `buildControlDisabled(slug, "eye_shape", { pupil_enabled: false })` returns `false` — `eye_shape` is never disabled by this rule.

**ESPS-8-AC-5:** `buildControlDisabled(slug, "pupil_enabled", { pupil_enabled: false })` returns `false` — the toggle itself is never disabled.

**ESPS-8-AC-6:** The existing spider placement row disabling logic (`spiderPlacementRowDisabled`) is not modified by this change.

**ESPS-8-AC-7:** `buildControlDisabled("spider", "eye_distribution", { eye_count: 1 })` continues to return `true` (regression check on existing logic).

### 3. Risk & Ambiguity Analysis

- **`pupil_enabled` value type from store:** The Zustand store stores `animatedBuildOptionValues[slug]` as `Record<string, unknown>`. The value for `pupil_enabled` may be `boolean`, `undefined`, or could be `0`/`1` from an older serialized state. The `buildControlDisabled` check must treat any falsy value (including `undefined`, `false`, `0`, empty string) as "disabled".

### 4. Clarifying Questions

None.

---

## Requirement ESPS-9: No Changes to `types/index.ts`

### 1. Spec Summary

- **Description:** The `AnimatedBuildControlDef` type in `types/index.ts` already declares all required variants including `bool` and `select_str`. No changes to this file are required.
- **Constraints:** Do not modify `types/index.ts`.
- **Assumptions:** Confirmed by reading the file.
- **Scope:** N/A.

### 2. Acceptance Criteria

**ESPS-9-AC-1:** `types/index.ts` is not modified.

### 3. Risk & Ambiguity Analysis

None.

### 4. Clarifying Questions

None.

---

## Constant Inventory

The following module-level constants must be introduced. All are in `asset_generation/python/src/core/blender_utils.py` unless noted otherwise.

| Constant name | Value | Location | Purpose |
|---|---|---|---|
| `_EYE_OVAL_SCALE_X` | `1.4` | `blender_utils.py` | X-scale ratio for oval eye |
| `_EYE_OVAL_SCALE_Z` | `0.85` | `blender_utils.py` | Z-scale ratio for oval eye |
| `_EYE_SLIT_SCALE_Y` | `0.35` | `blender_utils.py` | Y-scale ratio for slit eye (narrows side axis) |
| `_PUPIL_EYE_SCALE_RATIO` | `0.35` | `blender_utils.py` | Pupil size as fraction of eye_scale |
| `_PUPIL_SURFACE_EPSILON` | `0.05` | `blender_utils.py` | Fractional overshoot to place pupil above eye surface |
| `_PUPIL_DOT_Z_RATIO` | `0.3` | `blender_utils.py` | Z-scale ratio for dot pupil (flat disc) |
| `_PUPIL_SLIT_X_RATIO` | `0.25` | `blender_utils.py` | X-scale ratio for slit pupil cylinder |
| `_PUPIL_SLIT_Z_RATIO` | `0.05` | `blender_utils.py` | Z-scale ratio (depth) for slit pupil cylinder |
| `_PUPIL_DIAMOND_X_RATIO` | `0.6` | `blender_utils.py` | X-scale ratio for diamond pupil box |
| `_PUPIL_DIAMOND_Y_RATIO` | `0.25` | `blender_utils.py` | Y-scale ratio for diamond pupil box |
| `_PUPIL_DIAMOND_Z_RATIO` | `0.9` | `blender_utils.py` | Z-scale ratio for diamond pupil box |
| `_EYE_SHAPE_OPTIONS` | `("circle", "oval", "slit", "square")` | `animated_build_options.py` | Valid eye shape option set |
| `_PUPIL_SHAPE_OPTIONS` | `("dot", "slit", "diamond")` | `animated_build_options.py` | Valid pupil shape option set |
| `_DEFAULT_EYE_SHAPE` | `"circle"` | `animated_build_options.py` | Default eye shape |
| `_DEFAULT_PUPIL_SHAPE` | `"dot"` | `animated_build_options.py` | Default pupil shape |

---

## Slug Coverage Matrix

| Slug | Controls declared | Geometry wired (eye_shape) | Geometry wired (pupil) |
|---|---|---|---|
| `spider` | Yes | Yes | Yes |
| `slug` | Yes | Yes | Yes |
| `claw_crawler` | Yes | Yes (peripheral_eyes only; 0 eyes = no effect) | Yes (peripheral_eyes only) |
| `imp` | Yes | No (this ticket) | No (this ticket) |
| `carapace_husk` | Yes | No (this ticket) | No (this ticket) |
| `spitter` | Yes | No (this ticket) | No (this ticket) |
| `player_slime` | Yes | No (this ticket) | No (this ticket) |

---

## API Response Shape

The GET `/api/meta/enemies` response shape does not change. The three new controls are serialized as `AnimatedBuildControlDef[]` entries within the existing `animatedBuildControls[slug]` array. No new top-level keys are added to the `EnemyPreviewMeta` type.

Example output for slug `spider` (excerpt, showing only new entries):
```json
[
  { "key": "eye_shape", "label": "Eye shape", "type": "select_str", "options": ["circle", "oval", "slit", "square"], "default": "circle" },
  { "key": "pupil_enabled", "label": "Pupil", "type": "bool", "default": false },
  { "key": "pupil_shape", "label": "Pupil shape", "type": "select_str", "options": ["dot", "slit", "diamond"], "default": "dot" }
]
```

---

## Material Zone Assignment for Pupil Parts

Pupil meshes are assigned the `head` zone material. This is the same material slot as the head sphere. Rationale: pupils are part of the facial/eye feature and using the `head` slot avoids introducing a new material zone. The `extra` slot is already used for eye spheres (confirmed: `enemy_mats["extra"]` is the eye material in spider). Using `head` for pupils creates a deliberate contrast between eye iris color (`extra`) and pupil color (`head`). If the final visual result is undesirable, the assignor can switch to `extra` in a future ticket without spec changes.

**Exception for slug:** In `AnimatedSlug.apply_themed_materials`, the current `enumerate` loop assigns even indices (stalks) to `stalk_material` and odd indices (eyes) to `eye_material`. With pupils inserted, the loop logic must be rewritten to count parts explicitly and assign pupil parts to `head` material.

---

## Deferred Boundary Statement

The following items are explicitly out of scope for this ticket and deferred to future milestones:

1. Eye shape / pupil geometry for imp, spitter, carapace_husk, and player_slime builders. Controls are declared; geometry effects require a follow-on ticket.
2. Blinking and tracking animations (deferred to M26).
3. Per-eye asymmetry controls (both eyes always share settings in this ticket).
4. Eye color controls (owned by the existing color system; no new color controls in this ticket).
5. UI indicator to inform users that eye shape/pupil controls have no effect for controls-only slugs.
