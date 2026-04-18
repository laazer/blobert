# Spec: Per-Part Rotation Controls (M25-04)

**Ticket:** `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/04_part_rotation_controls.md`
**Spec file:** `project_board/specs/part_rotation_controls_spec.md`
**Authored by:** Spec Agent
**Date:** 2026-04-19
**Checkpoint log:** `project_board/checkpoints/M25-04/run-2026-04-19T00-00-00Z-spec.md`

---

## Scope

This feature adds cosmetic orientation controls for the head and body mesh primitives of animated enemies. Rotation is expressed in degrees, stored as float build options, validated/clamped at the pipeline layer, and applied to Blender mesh objects via `Euler` rotation. It is not skeletal posing, joint rotation, or hitbox geometry modification. It does not affect gameplay or collision.

The six animated enemy slugs in scope are: `spider`, `slug`, `imp`, `spitter`, `claw_crawler`, `carapace_husk`. `player_slime` is explicitly excluded.

---

## Requirement PRC-1: Module-Level Constants and `_rig_rotation_control_defs()`

### 1. Spec Summary

**Description:** A new function `_rig_rotation_control_defs()` is added to `asset_generation/python/src/utils/animated_build_options.py`. It returns exactly 6 control definition dicts — one per axis per part (head X/Y/Z, body X/Y/Z). Three module-level float constants define the shared bounds and step for all rotation controls.

**Constraints:**
- Function must not import from Blender (`bpy`, `mathutils`). It must be callable without a Blender stub active.
- All 6 dicts must use `type="float"` exactly (not `"int"`, not `"select"`).
- Key naming must use the exact strings listed in AC-1.1. Any deviation breaks the frontend `RIG_` prefix filter.
- Constants must be module-level (not inside the function), typed as `float`, and named exactly as listed.

**Assumptions:**
- The function is defined in `animated_build_options.py` (main module), not in `animated_build_options_appendage_defs.py`.
- No `unit` or `hint` field is required by the ticket, but either may be added by the implementer without invalidating this spec. Tests must not assert on their absence.

**Scope:** `asset_generation/python/src/utils/animated_build_options.py`

### 2. Acceptance Criteria

**AC-1.1 — Exact constant values and types:**
- `_RIG_ROT_MIN: float = -180.0` exists at module level.
- `_RIG_ROT_MAX: float = 180.0` exists at module level.
- `_RIG_ROT_STEP: float = 1.0` exists at module level.
- `isinstance(_RIG_ROT_MIN, float)` is True.
- `isinstance(_RIG_ROT_MAX, float)` is True.
- `isinstance(_RIG_ROT_STEP, float)` is True.

**AC-1.2 — Return length:**
`_rig_rotation_control_defs()` returns a list of exactly 6 dicts.

**AC-1.3 — Exact key strings:**
The 6 keys, in order, are:
1. `"RIG_HEAD_ROT_X"`
2. `"RIG_HEAD_ROT_Y"`
3. `"RIG_HEAD_ROT_Z"`
4. `"RIG_BODY_ROT_X"`
5. `"RIG_BODY_ROT_Y"`
6. `"RIG_BODY_ROT_Z"`

The keys set equals `{"RIG_HEAD_ROT_X", "RIG_HEAD_ROT_Y", "RIG_HEAD_ROT_Z", "RIG_BODY_ROT_X", "RIG_BODY_ROT_Y", "RIG_BODY_ROT_Z"}`.

**AC-1.4 — Per-def field contract:**
For every dict `d` returned by `_rig_rotation_control_defs()`:
- `d["type"] == "float"`
- `d["min"] == -180.0`
- `d["max"] == 180.0`
- `d["step"] == 1.0`
- `d["default"] == 0.0`
- `"key"` and `"label"` are present and non-empty strings.
- `d["min"]` is `_RIG_ROT_MIN` (value equality).
- `d["max"]` is `_RIG_ROT_MAX` (value equality).
- `d["step"]` is `_RIG_ROT_STEP` (value equality).

**AC-1.5 — Callable without Blender:**
`_rig_rotation_control_defs()` can be imported and called without `ensure_blender_stubs()` being called first, and without any Blender module available. It must not import `bpy`, `mathutils`, or any module that transitively does so.

**AC-1.6 — Label content:**
Each label string must be human-readable and must contain the axis letter (X, Y, or Z) and indicate whether it applies to head or body. Example conforming labels: `"Head rotation X"`, `"Body rotation Z (deg)"`. Tests must not assert on exact label wording beyond containing the axis and part name.

### 3. Risk & Ambiguity Analysis

- The `_tail_control_defs()` structural template places its function in `animated_build_options_appendage_defs.py`. The ticket explicitly specifies `animated_build_options.py` for `_rig_rotation_control_defs()`. Implementer must not place it in the appendage defs file; doing so would break the `static_defs.extend(m._rig_rotation_control_defs())` call in the validate module.
- The label content requirement is intentionally loose to avoid coupling tests to UX copy. Risk: a label of `"X"` alone would pass the axis check but would be insufficient for user comprehension. Implementers should include the part name.

### 4. Clarifying Questions

No blocking questions. Checkpoint log records one assumption about module placement (High confidence, resolved).

---

## Requirement PRC-2: Insertion into `animated_build_controls_for_api()`

### 1. Spec Summary

**Description:** `_rig_rotation_control_defs()` is inserted into the `merged` list in `animated_build_controls_for_api()` at a specific position: after `static_float` and before `_mesh_float_control_defs(slug)`. The insertion applies only to slugs that are members of `AnimatedEnemyBuilder.ENEMY_CLASSES` (the 6 animated enemy slugs). It does not apply to `player_slime`.

**Constraints:**
- The existing ordering of non-float statics, eye/pupil, mouth, tail, and mesh float controls must not change.
- The rotation defs appear in the Rig float section of the web editor by virtue of the `RIG_` prefix convention. No `BuildControls.tsx` change is required.
- The insertion must be conditional: only for `slug in AnimatedEnemyBuilder.ENEMY_CLASSES`.

**Assumptions:**
- `player_slime` does not receive rotation defs because it has no discrete head/body mesh objects in Blender (it is a player model, not an animated enemy built by `AnimatedEnemyBuilder`).
- The conditional guard is `if slug in AnimatedEnemyBuilder.ENEMY_CLASSES` wrapping the rotation defs inclusion.

**Scope:** `animated_build_controls_for_api()` in `asset_generation/python/src/utils/animated_build_options.py`

### 2. Acceptance Criteria

**AC-2.1 — Rotation keys present for all 6 animated enemies:**
For each slug in `{"spider", "slug", "imp", "spitter", "claw_crawler", "carapace_husk"}`:
`{c["key"] for c in animated_build_controls_for_api()[slug]}` contains all 6 rotation keys: `RIG_HEAD_ROT_X`, `RIG_HEAD_ROT_Y`, `RIG_HEAD_ROT_Z`, `RIG_BODY_ROT_X`, `RIG_BODY_ROT_Y`, `RIG_BODY_ROT_Z`.

**AC-2.2 — Rotation keys absent for `player_slime`:**
`{c["key"] for c in animated_build_controls_for_api()["player_slime"]}` does not contain `"RIG_HEAD_ROT_X"`.

**AC-2.3 — Insertion position relative to `static_float`:**
For any animated enemy slug (e.g. `"imp"`), in the merged list:
- The first rotation def (`RIG_HEAD_ROT_X`) appears after the last entry in `static_float`.
- Equivalently: `index("RIG_HEAD_ROT_X") > index of last static_float key`. (For slugs with no `static_float` entries, the constraint is that rotation defs appear before mesh float keys.)

**AC-2.4 — Insertion position relative to `_mesh_float_control_defs`:**
For any animated enemy slug, the 6 rotation defs appear before the first mesh float control (i.e., before any key that matches `BODY_*` or `RIG_*` mesh tuning keys that come from `_mesh_float_control_defs(slug)`).

**AC-2.5 — Existing control ordering preserved:**
The relative order of: `static_non_float`, `_eye_shape_pupil_control_defs()`, `_mouth_control_defs()`, `tail_defs[:2]`, `[tail_defs[2]]`, `static_float`, `[rotation_defs]`, `_mesh_float_control_defs(slug)` is maintained exactly. No existing control moves.

**AC-2.6 — Count correctness:**
`animated_build_controls_for_api()["imp"]` contains exactly 6 more entries than it did before this change is implemented (verified by counting keys in the pre- and post-implementation states, or by asserting the count of rotation-key-containing defs equals 6).

### 3. Risk & Ambiguity Analysis

- The `claw_crawler` slug has `peripheral_eyes` in `_ANIMATED_BUILD_CONTROLS` as a non-float. This becomes part of `static_non_float` and precedes all float sections. The rotation defs insertion logic must not disrupt this.
- The `spider` slug uses `_spider_eye_control_defs()` instead of `_ANIMATED_BUILD_CONTROLS`. It includes float defs (e.g. `eye_clustering`). These become `static_float`. Rotation defs appear after `eye_clustering` for spider.

### 4. Clarifying Questions

None. The conditional guard assumption (player_slime excluded) is logged in the checkpoint file as Medium confidence. If the human intended unconditional insertion, a separate corrective run is needed.

---

## Requirement PRC-3: Wiring into `_defaults_for_slug()`

### 1. Spec Summary

**Description:** `_defaults_for_slug()` in `animated_build_options.py` must initialize all 6 rotation keys to `0.0` in its return dict. The mechanism is looping over `_rig_rotation_control_defs()` and setting each key's default value, identically to how `_tail_control_defs()` keys are initialized. This applies to all slugs passed to `_defaults_for_slug()`, but in practice only the 6 animated enemy slugs reach Blender rotation application.

**Constraints:**
- Keys must be top-level in the returned dict (not nested under `"mesh"` or any sub-object).
- Default value is `0.0` (float). Not `0` (int).

**Assumptions:** No assumptions. The pattern is unambiguous from `_tail_control_defs()` precedent.

**Scope:** `_defaults_for_slug()` in `asset_generation/python/src/utils/animated_build_options.py`

### 2. Acceptance Criteria

**AC-3.1 — Keys present at top level:**
`_defaults_for_slug("imp")` returns a dict containing `"RIG_HEAD_ROT_X"` as a top-level key.

**AC-3.2 — Default value is 0.0 for all 6 keys:**
For all slugs in `{"spider", "slug", "imp", "spitter", "claw_crawler", "carapace_husk"}` and all 6 rotation keys:
`_defaults_for_slug(slug)[key] == 0.0` and `isinstance(_defaults_for_slug(slug)[key], float)` is True.

**AC-3.3 — No effect on existing keys:**
`_defaults_for_slug("imp")["tail_enabled"]` remains `False`. `_defaults_for_slug("imp")["eye_shape"]` remains `"circle"`. Spot-check at least 3 pre-existing keys.

### 3. Risk & Ambiguity Analysis

- `_defaults_for_slug` is called for all slugs including `player_slime`. If `_rig_rotation_control_defs()` is looped unconditionally, `player_slime` would also receive default rotation keys. This is harmless for the defaults function (it just adds keys to the dict), but it would cause `player_slime` to appear with rotation defs in `animated_build_controls_for_api()` unless the API function guards the insertion. The spec requires these to remain separate concerns: defaults function can be unconditional; the API function insertion is conditional.

### 4. Clarifying Questions

None.

---

## Requirement PRC-4: Wiring into `options_for_enemy()` (`allowed_non_mesh`)

### 1. Spec Summary

**Description:** `options_for_enemy()` maintains an `allowed_non_mesh` set to decide which keys from user-supplied JSON are admitted to the merged build options. All 6 rotation keys must be added to `allowed_non_mesh` so that user-supplied values like `{"RIG_HEAD_ROT_X": 45.0}` survive into the merged dict and reach `_coerce_and_validate()`. The mechanism is `allowed_non_mesh |= {c["key"] for c in _rig_rotation_control_defs()}`.

**Constraints:**
- If rotation keys are not in `allowed_non_mesh`, user-supplied values are silently discarded (the existing `elif k in allowed_non_mesh: merged[k] = v` branch never fires). This would be a silent data loss bug.
- The update must happen before the `for k, v in src.items()` loop.

**Assumptions:** No assumptions. The pattern is unambiguous from `_tail_control_defs()` precedent in `options_for_enemy()`.

**Scope:** `options_for_enemy()` in `asset_generation/python/src/utils/animated_build_options.py`

### 2. Acceptance Criteria

**AC-4.1 — Supplied value passes through:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})` returns a dict where `result["RIG_HEAD_ROT_X"] == 45.0`.

**AC-4.2 — Default applied when key absent:**
`options_for_enemy("imp", {})` returns a dict where `result["RIG_HEAD_ROT_X"] == 0.0`.

**AC-4.3 — All 6 keys present in output:**
`options_for_enemy("slug", {})` contains all 6 rotation keys at the top level with value `0.0`.

**AC-4.4 — Non-rotation keys unaffected:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})["tail_enabled"]` remains `False`.

**AC-4.5 — Nested input ignored (rotation keys are flat only):**
Rotation controls are flat top-level keys. `options_for_enemy("imp", {"mesh": {"RIG_HEAD_ROT_X": 45.0}})` does NOT set `result["RIG_HEAD_ROT_X"]` to 45.0 (it is not a mesh key; the value in `mesh` is irrelevant). Result is `result["RIG_HEAD_ROT_X"] == 0.0` (the default).

### 3. Risk & Ambiguity Analysis

- The `allowed_non_mesh |= ...` line must appear before the `for k, v in src.items()` loop. If placed after, all user values are discarded. Implementer must follow the existing pattern exactly.

### 4. Clarifying Questions

None.

---

## Requirement PRC-5: Validation and Coercion in `coerce_validate_enemy_build_options()`

### 1. Spec Summary

**Description:** `coerce_validate_enemy_build_options()` in `animated_build_options_validate.py` must process all 6 rotation keys via the existing `static_defs` extend pattern. The mechanism is `static_defs.extend(m._rig_rotation_control_defs())` added alongside the existing `static_defs.extend(m._tail_control_defs())` call. The existing float-type branch in the `for c in static_defs` loop then handles clamping to `[-180.0, 180.0]` and NaN coercion to default `0.0` automatically.

**Constraints:**
- The extend call must be placed such that `_rig_rotation_control_defs()` items are processed in the `for c in static_defs` loop (i.e., before the loop iterates).
- NaN inputs for any rotation key must be coerced to `0.0` (the control default). This behavior comes from the existing `if math.isnan(v): dv = c.get("default", lo)` branch — no new code is needed if `static_defs.extend` is done correctly.
- `float("inf")` and `float("-inf")` inputs: these are not NaN, so they proceed to `max(lo, min(hi, v))`. `max(-180.0, min(180.0, inf)) == 180.0` and `max(-180.0, min(180.0, -inf)) == -180.0`. No special inf guard is required.

**Assumptions:**
- Inf is handled implicitly by the clamp. This is consistent with existing behavior for all other float controls in the validate loop.
- The `static_defs.extend` is unconditional (applies to all enemy types including `player_slime`). This is harmless: if rotation keys are not present in `merged`, the `if key not in out: continue` guard in the loop skips them.

**Scope:** `coerce_validate_enemy_build_options()` in `asset_generation/python/src/utils/animated_build_options_validate.py`

### 2. Acceptance Criteria

**AC-5.1 — Upper clamp:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_X": 200.0})` returns `result["RIG_HEAD_ROT_X"] == 180.0`.

**AC-5.2 — Lower clamp:**
`options_for_enemy("imp", {"RIG_BODY_ROT_Z": -200.0})` returns `result["RIG_BODY_ROT_Z"] == -180.0`.

**AC-5.3 — Boundary: exact max passes through:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_Y": 180.0})` returns `result["RIG_HEAD_ROT_Y"] == 180.0`.

**AC-5.4 — Boundary: exact min passes through:**
`options_for_enemy("imp", {"RIG_BODY_ROT_X": -180.0})` returns `result["RIG_BODY_ROT_X"] == -180.0`.

**AC-5.5 — NaN coerced to 0.0:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_Z": float("nan")})` returns `result["RIG_HEAD_ROT_Z"] == 0.0`.

**AC-5.6 — Positive inf clamped to 180.0:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_X": float("inf")})` returns `result["RIG_HEAD_ROT_X"] == 180.0`.

**AC-5.7 — Negative inf clamped to -180.0:**
`options_for_enemy("imp", {"RIG_BODY_ROT_Y": float("-inf")})` returns `result["RIG_BODY_ROT_Y"] == -180.0`.

**AC-5.8 — String input coerced to float before clamp:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_X": "45.0"})` returns `result["RIG_HEAD_ROT_X"] == 45.0`.

**AC-5.9 — Non-parseable string reverts to default:**
`options_for_enemy("imp", {"RIG_HEAD_ROT_X": "not_a_number"})` returns `result["RIG_HEAD_ROT_X"] == 0.0`.

**AC-5.10 — All 6 keys validated for all 6 animated slugs:**
For every slug in `{"spider", "slug", "imp", "spitter", "claw_crawler", "carapace_husk"}`, supplying a value of `200.0` for any rotation key results in that key clamped to `180.0`.

### 3. Risk & Ambiguity Analysis

- `float("nan") > 180.0` is `False` and `float("nan") < -180.0` is also `False`, so `max(-180.0, min(180.0, nan))` returns `nan` in Python (it passes through). The existing explicit `math.isnan(v)` guard is therefore necessary and correct; the clamp alone does not handle NaN.
- String inputs like `"45.0"` must succeed because the existing branch uses `float(out[key])` which coerces strings. This is existing behavior; the spec confirms it applies to rotation keys too.

### 4. Clarifying Questions

None.

---

## Requirement PRC-6: Blender Rotation Application in Each Enemy's `build_mesh_parts()`

### 1. Spec Summary

**Description:** In each of the 6 animated enemy classes, after the head mesh object and body mesh object are created (via `create_sphere()`, `create_cylinder()`, or equivalent) and before or immediately after being appended to `self.parts`, the implementation reads the corresponding rotation build options, converts from degrees to radians using `math.radians()`, and assigns `obj.rotation_euler = mathutils.Euler((rx, ry, rz), 'XYZ')`. This is the only output-side effect; it does not change location, scale, or any other property.

**Constraints:**
- Euler order is exactly `'XYZ'` (uppercase string).
- Conversion is `math.radians(float(self.build_options.get("RIG_BODY_ROT_X", 0.0)))` — the `or 0.0` guard is equivalent to `.get(..., 0.0)` for falsy zero but the `.get(..., 0.0)` default is cleaner; either form is acceptable as long as the default is `0.0`.
- `math` must be imported at the top of each enemy file (standard library; likely already present or added).
- `mathutils.Euler` (or `from mathutils import Euler`) must be imported. Blender provides `mathutils`; tests will mock it via Blender stubs.
- The rotation assignment is applied to the object returned by the mesh-creation helper (e.g. `body = create_sphere(...)`), not to `self.parts[-1]` after the fact (though both refer to the same object — either form is acceptable).
- Default rotation of `0.0, 0.0, 0.0` must be a no-op (i.e., assigning `Euler((0,0,0), 'XYZ')` must not change the object's visual result from the pre-change behavior).

**Assumptions:**
- All 6 slugs have a distinct "head" mesh object and a distinct "body" mesh object. See PRC-7 for the per-slug coverage matrix.
- The Blender stub system (via `ensure_blender_stubs()`) provides a `mathutils.Euler` that accepts these arguments.

**Scope:** `build_mesh_parts()` in each of:
- `asset_generation/python/src/enemies/animated_slug.py`
- `asset_generation/python/src/enemies/animated_imp.py`
- `asset_generation/python/src/enemies/animated_spider.py`
- `asset_generation/python/src/enemies/animated_claw_crawler.py`
- `asset_generation/python/src/enemies/animated_spitter.py`
- `asset_generation/python/src/enemies/animated_carapace_husk.py`

### 2. Acceptance Criteria

**AC-6.1 — Body rotation assignment:**
For each slug, after `build_mesh_parts()` executes with `build_options={"RIG_BODY_ROT_Z": 90.0}`, the body mesh object's `rotation_euler[2]` equals `math.pi / 2` (within floating-point tolerance: `abs(obj.rotation_euler[2] - math.pi/2) < 1e-9`).

**AC-6.2 — Head rotation assignment:**
For each slug, after `build_mesh_parts()` executes with `build_options={"RIG_HEAD_ROT_X": 45.0}`, the head mesh object's `rotation_euler[0]` equals `math.radians(45.0)` (within floating-point tolerance).

**AC-6.3 — Zero rotation is a no-op:**
With `build_options={}` (all defaults), `rotation_euler` for body and head equals `Euler((0.0, 0.0, 0.0), 'XYZ')`. No crash occurs.

**AC-6.4 — Euler order string:**
The `Euler(...)` call uses the second argument `'XYZ'`. This is verifiable via inspection of the code; tests relying on stub behavior must confirm the Euler is constructed with this order.

**AC-6.5 — Independent X/Y/Z assignment:**
Setting only `RIG_BODY_ROT_X=30.0` with `RIG_BODY_ROT_Y` and `RIG_BODY_ROT_Z` absent (or 0.0) produces `body.rotation_euler[0] == math.radians(30.0)`, `body.rotation_euler[1] == 0.0`, `body.rotation_euler[2] == 0.0`.

**AC-6.6 — Head and body rotations are independent:**
Setting `RIG_HEAD_ROT_X=10.0` does not affect body's `rotation_euler`, and setting `RIG_BODY_ROT_X=20.0` does not affect head's `rotation_euler`.

**AC-6.7 — Negative degrees applied correctly:**
`build_options={"RIG_BODY_ROT_Y": -90.0}` → `body.rotation_euler[1] == math.radians(-90.0)` (a negative radian value).

### 3. Risk & Ambiguity Analysis

- The `AnimatedSlug.build_mesh_parts()` creates the body sphere first (index 0), then the head sphere (index 1). The rotation assignment must target these specific objects. If a slug creates a different part first (e.g. a cylinder for the body), the implementer must identify which part is "body" and "head" per each slug's existing logic.
- Tests for Blender rotation application require a Blender stub or mock for `mathutils.Euler`. The test suite for this feature covers the Python-only aspects (control defs, validation, defaults) without running Blender. Blender rotation application is verified by code review and visual inspection (out of band for the automated test suite).
- The slug (`AnimatedSlug`) creates body at `self.parts[0]`, head at `self.parts[1]`. For other slugs, implementer must read each slug's `build_mesh_parts()` to identify the head and body object variables.

### 4. Clarifying Questions

None blocking. The per-slug coverage matrix is in PRC-7.

---

## Requirement PRC-7: Slug Coverage Matrix

### 1. Spec Summary

**Description:** Defines which slugs receive head rotation, body rotation, and which are excluded. All 6 animated enemy slugs receive both head and body rotation controls. `player_slime` is excluded from both.

**Constraints:**
- The matrix is definitive. A slug marked with both head and body rotation must have both applied in `build_mesh_parts()` and both sets of keys present in the API controls and defaults.
- A slug marked excluded must NOT have rotation keys in `animated_build_controls_for_api()` output.

**Assumptions:** No assumptions. The ticket is unambiguous on the 6-slug/player_slime boundary.

**Scope:** All files listed in PRC-6 scope, plus `animated_build_options.py`.

### 2. Acceptance Criteria

**AC-7.1 — Coverage matrix:**

| Slug | Head rotation (RIG_HEAD_ROT_X/Y/Z) | Body rotation (RIG_BODY_ROT_X/Y/Z) | Blender application |
|---|---|---|---|
| `spider` | Yes | Yes | `build_mesh_parts()` in `animated_spider.py` |
| `slug` | Yes | Yes | `build_mesh_parts()` in `animated_slug.py` |
| `imp` | Yes | Yes | `build_mesh_parts()` in `animated_imp.py` |
| `spitter` | Yes | Yes | `build_mesh_parts()` in `animated_spitter.py` |
| `claw_crawler` | Yes | Yes | `build_mesh_parts()` in `animated_claw_crawler.py` |
| `carapace_husk` | Yes | Yes | `build_mesh_parts()` in `animated_carapace_husk.py` |
| `player_slime` | No | No | Not applicable |

**AC-7.2 — `player_slime` exclusion verification:**
`animated_build_controls_for_api()["player_slime"]` does not contain any key matching the pattern `RIG_HEAD_ROT_*` or `RIG_BODY_ROT_*`.

**AC-7.3 — All 6 animated slugs covered in API output:**
`animated_build_controls_for_api()` contains keys for `"spider"`, `"slug"`, `"imp"`, `"spitter"`, `"claw_crawler"`, `"carapace_husk"`, each with all 6 rotation defs.

### 3. Risk & Ambiguity Analysis

- The ticket states "Add to all animated slugs that expose explicit head/body parts". All 6 animated enemy slugs have distinct head and body meshes in their `build_mesh_parts()` implementations. No slug is excluded from either rotation axis.
- `player_slime` appears in `animated_build_controls_for_api()` via the `| {"spider", "player_slime"}` union but has no `AnimatedEnemyBuilder.ENEMY_CLASSES` entry. The conditional insertion guard in PRC-2 ensures it is excluded.

### 4. Clarifying Questions

None.

---

## Requirement PRC-8: Python Test File

### 1. Spec Summary

**Description:** A new Python test file at `asset_generation/python/tests/utils/test_part_rotation_controls.py` provides the automated test suite for PRC-1 through PRC-5 and PRC-7. The file follows the structural pattern of `test_animated_build_options_offset_xyz.py`: section comments per requirement, one test function per AC, test names that describe the AC, no mocking of module internals beyond what the existing test infrastructure provides.

**Constraints:**
- File path is exactly `asset_generation/python/tests/utils/test_part_rotation_controls.py`.
- Tests import from `src.utils.animated_build_options` (as `abo`) and use `animated_build_controls_for_api`, `options_for_enemy` directly.
- Tests for constants use `hasattr(abo, ...)` and `isinstance(...)`.
- Tests must be independent: no shared state, no module-level setup that mutates globals.
- Tests must not require a live Blender process. Blender rotation application (PRC-6) is out of scope for this test file; it is verified by code inspection and manual smoke test.

**Assumptions:** The test file is RED (failing) until PRC-1 through PRC-5 are implemented. The Test Designer Agent writes the test file before implementation.

**Scope:** `asset_generation/python/tests/utils/test_part_rotation_controls.py`

### 2. Acceptance Criteria

**AC-8.1 — Constants section (maps to PRC-1 AC-1.1):**
`test_rig_rot_constants_exist_and_typed()`: asserts `_RIG_ROT_MIN`, `_RIG_ROT_MAX`, `_RIG_ROT_STEP` exist on the `abo` module, are `float`, and have values `-180.0`, `180.0`, `1.0` respectively.

**AC-8.2 — Control def structure section (maps to PRC-1 AC-1.2 through AC-1.5):**
- `test_rig_rotation_control_defs_returns_six_dicts()`: asserts length == 6.
- `test_rig_rotation_control_defs_exact_keys()`: asserts the key set is exactly the 6 specified strings.
- `test_rig_rotation_control_defs_type_and_bounds()`: for every dict, asserts `type="float"`, `min=-180.0`, `max=180.0`, `step=1.0`, `default=0.0`.
- `test_rig_rotation_control_defs_callable_without_blender()`: imports and calls the function; asserts no exception. (The test environment already runs without Blender, so this is implicitly verified by any test that calls the function.)

**AC-8.3 — API output section (maps to PRC-2):**
- `test_animated_build_controls_for_api_includes_rotation_keys_for_all_slugs()`: parameterized or repeated for all 6 animated enemy slugs; asserts all 6 rotation keys are present.
- `test_animated_build_controls_for_api_excludes_rotation_keys_for_player_slime()`: asserts `RIG_HEAD_ROT_X` not in player_slime controls.

**AC-8.4 — Defaults section (maps to PRC-3):**
- `test_defaults_for_slug_has_rotation_keys_at_zero()`: for each of the 6 animated slugs, asserts all 6 rotation keys equal `0.0` in `_defaults_for_slug(slug)`.

**AC-8.5 — options_for_enemy pass-through section (maps to PRC-4):**
- `test_options_for_enemy_rotation_key_passes_through()`: `options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})["RIG_HEAD_ROT_X"] == 45.0`.
- `test_options_for_enemy_rotation_default_when_absent()`: `options_for_enemy("imp", {})["RIG_HEAD_ROT_X"] == 0.0`.
- `test_options_for_enemy_all_six_rotation_keys_present()`: `options_for_enemy("slug", {})` contains all 6 keys.

**AC-8.6 — Clamp section (maps to PRC-5):**
- `test_options_for_enemy_rotation_upper_clamp()`: `options_for_enemy("imp", {"RIG_HEAD_ROT_X": 200})["RIG_HEAD_ROT_X"] == 180.0`.
- `test_options_for_enemy_rotation_lower_clamp()`: `options_for_enemy("slug", {"RIG_BODY_ROT_Z": -200})["RIG_BODY_ROT_Z"] == -180.0`.
- `test_options_for_enemy_rotation_boundary_max()`: `options_for_enemy("imp", {"RIG_HEAD_ROT_Y": 180.0})["RIG_HEAD_ROT_Y"] == 180.0`.
- `test_options_for_enemy_rotation_boundary_min()`: `options_for_enemy("imp", {"RIG_BODY_ROT_X": -180.0})["RIG_BODY_ROT_X"] == -180.0`.
- `test_options_for_enemy_rotation_nan_reverts_to_default()`: `options_for_enemy("imp", {"RIG_HEAD_ROT_Z": float("nan")})["RIG_HEAD_ROT_Z"] == 0.0`.
- `test_options_for_enemy_rotation_inf_clamped_to_max()`: `options_for_enemy("imp", {"RIG_HEAD_ROT_X": float("inf")})["RIG_HEAD_ROT_X"] == 180.0`.
- `test_options_for_enemy_rotation_neg_inf_clamped_to_min()`: `options_for_enemy("imp", {"RIG_BODY_ROT_Y": float("-inf")})["RIG_BODY_ROT_Y"] == -180.0`.

**AC-8.7 — Cross-slug coverage for clamp:**
For at least 3 distinct slugs (e.g. `"spider"`, `"slug"`, `"carapace_husk"`), assert `options_for_enemy(slug, {"RIG_BODY_ROT_Z": 200.0})["RIG_BODY_ROT_Z"] == 180.0`.

**AC-8.8 — Non-breaking (backward compat):**
`test_options_for_enemy_rotation_does_not_break_existing_keys()`: `options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})["tail_enabled"] == False` and `options_for_enemy("imp", {"RIG_HEAD_ROT_X": 45.0})["eye_shape"] == "circle"`.

**AC-8.9 — Test file runs clean:**
`bash .lefthook/scripts/py-tests.sh` exits 0 after Tasks 1–4 are implemented.

### 3. Risk & Ambiguity Analysis

- Float equality comparisons: use `==` for exact decimal values (0.0, 180.0, -180.0). For radians-converted values in PRC-6 (out of scope for this file), use `math.isclose`.
- Parameterization: the Test Designer may choose to write explicit loops over slug names or use `pytest.mark.parametrize`. Either is acceptable.

### 4. Clarifying Questions

None.

---

## Requirement PRC-9: Frontend Rig Section Verification

### 1. Spec Summary

**Description:** The web editor's `BuildControls.tsx` already renders float controls whose keys start with `"RIG_"` under a "Rig" section header (via a `d.key.startsWith("RIG_")` filter at line 353 of `BuildControls.tsx`). Because `RIG_HEAD_ROT_X` matches this filter, no `BuildControls.tsx` code change is needed. Verification is documented via a comment or assertion in the existing test file `BuildControls.meta_load.test.tsx`.

**Constraints:**
- No new test file is created for the frontend. The existing `BuildControls.meta_load.test.tsx` is extended.
- The extension is a comment block or a targeted `describe` block within the existing file.
- `npm test` must continue to pass.

**Assumptions:**
- The `d.key.startsWith("RIG_")` filter at line 353 of `BuildControls.tsx` is confirmed by code inspection; no test infrastructure is needed to verify the filter logic itself because it is already covered by existing tests.
- A code comment citing this ticket (M25-04) in `BuildControls.meta_load.test.tsx` is sufficient if the existing test coverage demonstrates that any `RIG_`-prefixed float control appears under the Rig section.

**Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.meta_load.test.tsx`

### 2. Acceptance Criteria

**AC-9.1 — No `BuildControls.tsx` change:**
The git diff for this ticket contains no modifications to `BuildControls.tsx`.

**AC-9.2 — Comment or assertion in `BuildControls.meta_load.test.tsx`:**
The file contains a reference to `RIG_HEAD_ROT_X` and ticket `M25-04` in a comment or test description, documenting that no code change is needed because the `RIG_` prefix filter covers these keys automatically.

**AC-9.3 — `npm test` passes:**
`cd asset_generation/web/frontend && npm test` exits 0 after any extension to `BuildControls.meta_load.test.tsx`.

### 3. Risk & Ambiguity Analysis

- If the Vitest test file introduces a new test assertion (not just a comment), the assertion must use a mock API response shape consistent with the store's `animatedBuildControls` type. Incorrect mock shapes can cause TypeScript errors.
- If the file receives only a comment (no assertion), AC-9.3 is trivially satisfied.

### 4. Clarifying Questions

None.

---

## Requirement PRC-10: Non-Breaking Guarantee

### 1. Spec Summary

**Description:** All existing Python and frontend tests must continue to pass after this feature is implemented. The feature is additive: new keys in defaults and validated output do not invalidate existing key expectations. Default rotation values of `0.0` produce the same Blender output as before (no rotation applied was the prior state; `Euler((0,0,0), 'XYZ')` is the identity rotation).

**Constraints:**
- No existing Python test that asserts a specific count of items in `_defaults_for_slug()`, `options_for_enemy()`, or `animated_build_controls_for_api()` output may break. If such tests exist, they must be updated to account for the 6 new keys — this is a permitted, expected change, not a regression.
- The Blender rotation assignment (default 0.0 → identity rotation) must not visually change any existing exported GLB.

**Assumptions:** No existing test counts exact items in the above functions. This assumption is logged in the checkpoint file.

**Scope:** All existing test files under `asset_generation/python/tests/` and `asset_generation/web/frontend/src/`.

### 2. Acceptance Criteria

**AC-10.1 — Python test suite passes:**
`bash .lefthook/scripts/py-tests.sh` exits 0 with no regressions after all implementation tasks.

**AC-10.2 — Diff-cover preflight passes:**
`bash ci/scripts/diff_cover_preflight.sh` exits 0.

**AC-10.3 — Frontend tests pass:**
`cd asset_generation/web/frontend && npm test` exits 0.

**AC-10.4 — Default zero rotation is identity:**
When all rotation keys are `0.0` (default), `mathutils.Euler((0.0, 0.0, 0.0), 'XYZ')` equals the default object rotation in Blender. The exported GLB for any slug with default options is visually identical to the pre-change export.

### 3. Risk & Ambiguity Analysis

- AC-10.4 is not automatically verifiable; it is a non-functional regression guarantee enforced by visual smoke test at the AC gate step. The automated gate (diff-cover) covers code coverage, not visual output.
- If any existing test counts keys in `options_for_enemy()` output, the implementer must update that test to add 6 to the expected count. This is not a new test file; it is an existing file modification.

### 4. Clarifying Questions

None.

---

## Serialization Contract

The 6 rotation keys are top-level scalar floats in the enemy build options JSON payload. They serialize and deserialize identically to other scalar float build options (e.g. `tail_length`).

**Serialization shape (example for `imp`):**
```json
{
  "RIG_HEAD_ROT_X": 0.0,
  "RIG_HEAD_ROT_Y": 0.0,
  "RIG_HEAD_ROT_Z": 45.0,
  "RIG_BODY_ROT_X": 0.0,
  "RIG_BODY_ROT_Y": 0.0,
  "RIG_BODY_ROT_Z": 0.0,
  "eye_shape": "circle",
  "mesh": { ... }
}
```

These keys are not nested under `"mesh"`, `"features"`, or `"zone_geometry_extras"`. `options_for_enemy()` validates them at the top level. They round-trip through `parse_build_options_json()` → `options_for_enemy()` without loss.

---

## Summary of Requirements

| ID | Title | Primary File(s) | Stage |
|---|---|---|---|
| PRC-1 | Module-level constants and `_rig_rotation_control_defs()` | `animated_build_options.py` | Implementation |
| PRC-2 | Insertion into `animated_build_controls_for_api()` | `animated_build_options.py` | Implementation |
| PRC-3 | Wiring into `_defaults_for_slug()` | `animated_build_options.py` | Implementation |
| PRC-4 | Wiring into `options_for_enemy()` allowed_non_mesh | `animated_build_options.py` | Implementation |
| PRC-5 | Validation and coercion in `coerce_validate_enemy_build_options()` | `animated_build_options_validate.py` | Implementation |
| PRC-6 | Blender rotation application in each enemy's `build_mesh_parts()` | 6 animated enemy files | Implementation |
| PRC-7 | Slug coverage matrix | All above | Reference |
| PRC-8 | Python test file | `test_part_rotation_controls.py` | Test Design |
| PRC-9 | Frontend Rig section verification | `BuildControls.meta_load.test.tsx` | Implementation (verification only) |
| PRC-10 | Non-breaking guarantee | All test files | AC Gate |
