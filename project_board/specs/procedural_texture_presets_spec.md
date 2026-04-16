# Procedural Texture Presets Spec

**Ticket:** `project_board/25_milestone_25_enemy_editor_visual_expression/in_progress/02_procedural_texture_presets.md`
**Spec version:** 1
**Author:** Spec Agent
**Date:** 2026-04-16

---

## Scope & Boundaries

This spec covers:
- Ten new Python build controls declared via `_texture_control_defs()` in `animated_build_options_appendage_defs.py`
- Exact insertion position of those controls in `animated_build_controls_for_api()`
- Default population in `_defaults_for_slug()`
- `allowed_non_mesh` extension in `options_for_enemy()`
- `static_defs.extend()` wiring in `coerce_validate_enemy_build_options()`
- Coercion and validation rules: unknown mode fallback, float clamping, hex string passthrough
- Per-slug coverage matrix (all 7 animated slugs)
- Serialization contract (JSON type correctness)
- Frontend `buildControlDisabled()` rules per mode group
- Three.js shader overlay behavior in `GlbViewer.tsx`: material capture, per-mode ShaderMaterial, hex-to-THREE.Color conversion, restore on mode=none, re-capture on URL change
- Non-breaking guarantee: all existing controls unaffected

Out of scope (per ticket):
- Per-part texture assignment (texture applies uniformly to all body mesh children)
- Uploaded or image-based textures (see ticket 03)
- UV-offset or tiling controls
- Blender-side mesh geometry effects; this ticket is preview-only (Three.js shader overlay)
- New `ControlRow` rendering type for hex fields; `type: "str"` reuses the existing string input branch

---

## Constant Inventory

The following module-level constants must be declared in `animated_build_options_appendage_defs.py` before the `_texture_control_defs()` function:

| Constant | Type | Value |
|---|---|---|
| `_TEXTURE_MODE_OPTIONS` | `tuple[str, ...]` | `("none", "gradient", "spots", "stripes")` |
| `_DEFAULT_TEXTURE_MODE` | `str` | `"none"` |
| `_GRAD_DIRECTION_OPTIONS` | `tuple[str, ...]` | `("horizontal", "vertical", "radial")` |
| `_DEFAULT_GRAD_DIRECTION` | `str` | `"horizontal"` |
| `_DEFAULT_TEXTURE_COLOR` | `str` | `""` |
| `_TEXTURE_SPOT_DENSITY_MIN` | `float` | `0.1` |
| `_TEXTURE_SPOT_DENSITY_MAX` | `float` | `5.0` |
| `_TEXTURE_SPOT_DENSITY_STEP` | `float` | `0.05` |
| `_TEXTURE_SPOT_DENSITY_DEFAULT` | `float` | `1.0` |
| `_TEXTURE_STRIPE_WIDTH_MIN` | `float` | `0.05` |
| `_TEXTURE_STRIPE_WIDTH_MAX` | `float` | `1.0` |
| `_TEXTURE_STRIPE_WIDTH_STEP` | `float` | `0.01` |
| `_TEXTURE_STRIPE_WIDTH_DEFAULT` | `float` | `0.2` |

No unexplained inline literals are permitted for these values in the function body.

---

## Slug Coverage Matrix

All 7 slugs receive all 10 texture control definitions. There are no per-slug exclusions.

| Slug | Receives texture controls | Geometry effect (Blender) |
|---|---|---|
| `spider` | Yes (all 10) | No (preview-only) |
| `slug` | Yes (all 10) | No (preview-only) |
| `claw_crawler` | Yes (all 10) | No (preview-only) |
| `imp` | Yes (all 10) | No (preview-only) |
| `carapace_husk` | Yes (all 10) | No (preview-only) |
| `spitter` | Yes (all 10) | No (preview-only) |
| `player_slime` | Yes (all 10) | No (preview-only) |

---

## Requirement PTP-1: Python Build Control Declarations

### 1. Spec Summary

- **Description:** Ten new `AnimatedBuildControlDef`-compatible control entries are declared for every animated enemy slug: `texture_mode`, `texture_grad_color_a`, `texture_grad_color_b`, `texture_grad_direction`, `texture_spot_color`, `texture_spot_bg_color`, `texture_spot_density`, `texture_stripe_color`, `texture_stripe_bg_color`, `texture_stripe_width`. They are emitted by `animated_build_controls_for_api()` and their defaults are emitted by `_defaults_for_slug()`.
- **Constraints:**
  - A new private helper function `_texture_control_defs()` is added to `asset_generation/python/src/utils/animated_build_options_appendage_defs.py`, following the pattern established by `_mouth_control_defs()` and `_tail_control_defs()`.
  - `_texture_control_defs()` takes no arguments and returns `list[dict[str, Any]]` with exactly 10 entries, in the order listed in the constant inventory table below.
  - The function must not import any enemy class. All values are resolved from the module-level constants declared above.
  - `_texture_control_defs()` is imported into `animated_build_options.py` from `animated_build_options_appendage_defs`.
  - `animated_build_controls_for_api()` inserts the 10 texture control defs immediately after the `_zone_extra_control_defs(slug)` block and immediately before `[_placement_seed_def()]` in the `merged` list. All 10 texture defs are non-float (`type` is either `"select_str"` or `"str"`) except `texture_spot_density` and `texture_stripe_width`, which are `"float"`. The float controls among texture defs must appear after `_mesh_float_control_defs(slug)` and the feature/part-feature/zone-extra blocks, but before `placement_seed`.
  - `_defaults_for_slug(slug)` loops over `_texture_control_defs()` and populates `out[c["key"]] = c.get("default")` for each entry, following the same pattern used for `_mouth_control_defs()` and `_tail_control_defs()`.
  - `player_slime` is included in the slug set and receives all 10 texture controls with no special casing.
- **Assumptions:** The existing `"str"` type in `coerce_validate_enemy_build_options` is not coerced (str fields are passed through as-is after existing validation); this is consistent with how `feat_*_hex` fields work. Confirmed: the validator loop only processes `int`, `float`, `select`, `select_str`, and `bool` branches; `str` fields require no additional coercion logic beyond passthrough.
- **Scope:** `asset_generation/python/src/utils/animated_build_options_appendage_defs.py` (declaration); `asset_generation/python/src/utils/animated_build_options.py` (wiring into merged list and defaults).

### 2. Acceptance Criteria

**PTP-1-AC-1:** `_texture_control_defs()` is callable with no arguments and returns a `list` of exactly 10 `dict` objects.

**PTP-1-AC-2:** The returned list contains exactly these entries in exactly this order:

Entry 1 — `texture_mode`:
```
{
    "key": "texture_mode",
    "label": "Texture mode",
    "type": "select_str",
    "options": ["none", "gradient", "spots", "stripes"],
    "default": "none",
}
```

Entry 2 — `texture_grad_color_a`:
```
{
    "key": "texture_grad_color_a",
    "label": "Gradient color A",
    "type": "str",
    "default": "",
}
```

Entry 3 — `texture_grad_color_b`:
```
{
    "key": "texture_grad_color_b",
    "label": "Gradient color B",
    "type": "str",
    "default": "",
}
```

Entry 4 — `texture_grad_direction`:
```
{
    "key": "texture_grad_direction",
    "label": "Gradient direction",
    "type": "select_str",
    "options": ["horizontal", "vertical", "radial"],
    "default": "horizontal",
}
```

Entry 5 — `texture_spot_color`:
```
{
    "key": "texture_spot_color",
    "label": "Spot color",
    "type": "str",
    "default": "",
}
```

Entry 6 — `texture_spot_bg_color`:
```
{
    "key": "texture_spot_bg_color",
    "label": "Spot background color",
    "type": "str",
    "default": "",
}
```

Entry 7 — `texture_spot_density`:
```
{
    "key": "texture_spot_density",
    "label": "Spot density",
    "type": "float",
    "min": 0.1,
    "max": 5.0,
    "step": 0.05,
    "default": 1.0,
}
```

Entry 8 — `texture_stripe_color`:
```
{
    "key": "texture_stripe_color",
    "label": "Stripe color",
    "type": "str",
    "default": "",
}
```

Entry 9 — `texture_stripe_bg_color`:
```
{
    "key": "texture_stripe_bg_color",
    "label": "Stripe background color",
    "type": "str",
    "default": "",
}
```

Entry 10 — `texture_stripe_width`:
```
{
    "key": "texture_stripe_width",
    "label": "Stripe width",
    "type": "float",
    "min": 0.05,
    "max": 1.0,
    "step": 0.01,
    "default": 0.2,
}
```

**PTP-1-AC-3:** `animated_build_controls_for_api()[slug]` for every slug in `{spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime}` contains exactly one entry for each of the 10 keys listed in PTP-1-AC-2.

**PTP-1-AC-4:** The 10 texture control entries appear immediately after all `extra_zone_*` entries and immediately before the `placement_seed` entry in the per-slug control list returned by `animated_build_controls_for_api()`.

**PTP-1-AC-5:** `_defaults_for_slug(slug)` for every slug returns a dict that includes all 10 texture keys at their declared defaults: `texture_mode="none"`, `texture_grad_color_a=""`, `texture_grad_color_b=""`, `texture_grad_direction="horizontal"`, `texture_spot_color=""`, `texture_spot_bg_color=""`, `texture_spot_density=1.0`, `texture_stripe_color=""`, `texture_stripe_bg_color=""`, `texture_stripe_width=0.2`.

**PTP-1-AC-6:** Calling `_texture_control_defs()` twice returns two separate list objects (mutation guard: modifying the returned list must not affect subsequent calls).

**PTP-1-AC-7:** `_texture_control_defs()` does not import or reference any enemy class (`AnimatedSpider`, `AnimatedSlug`, etc.).

**PTP-1-AC-8:** All 13 module-level constants listed in the Constant Inventory section are present in `animated_build_options_appendage_defs.py`.

### 3. Risk & Ambiguity Analysis

- **Insertion position mechanics:** `animated_build_controls_for_api()` currently ends its `merged` list with `+ _zone_extra_control_defs(slug) + [_placement_seed_def()]`. The new texture block inserts between these two. Because `texture_spot_density` and `texture_stripe_width` are `float` type, the float/non-float split used for slug-specific static controls does not apply here; the texture defs are appended as a flat block after the zone-extra defs.
- **`type: "str"` for hex fields:** Hex color fields (`texture_grad_color_a`, etc.) use `type: "str"` consistent with `feat_*_hex` fields. No new ControlRow rendering branch is required. The coercion loop in `coerce_validate_enemy_build_options` does not process `str` fields; they pass through as-is.
- **`options` field on `texture_mode` and `texture_grad_direction`:** These are `select_str` controls and must include the `"options"` key as a `list` (not a tuple). `list(_TEXTURE_MODE_OPTIONS)` and `list(_GRAD_DIRECTION_OPTIONS)` satisfy this.
- **Float controls in texture defs and the non-float/float split:** The existing split in `animated_build_controls_for_api()` applies to `static_non_float` and `static_float` derived from `_ANIMATED_BUILD_CONTROLS.get(slug, [])`. The texture defs are appended after all of that, so the presence of float-typed entries in `_texture_control_defs()` does not require additional splitting logic.

### 4. Clarifying Questions

None. All resolved by reading the codebase and checkpoint log at `project_board/checkpoints/M25-PTP/run-2026-04-16T12-00-00Z-spec.md`.

---

## Requirement PTP-2: Python Coercion and Validation

### 1. Spec Summary

- **Description:** `coerce_validate_enemy_build_options` in `animated_build_options_validate.py` correctly coerces and validates all 10 new keys. `options_for_enemy` in `animated_build_options.py` includes all 10 keys in `allowed_non_mesh` so they survive the flat-key merge step.
- **Constraints:**
  - `animated_build_options_validate.py`: after the existing `static_defs.extend(m._tail_control_defs())` call and before `static_defs.append(m._placement_seed_def())`, add `static_defs.extend(m._texture_control_defs())`. The `_texture_control_defs` function must be referenced via the `m` module alias (consistent with the existing pattern for `_mouth_control_defs` and `_tail_control_defs`).
  - `options_for_enemy` in `animated_build_options.py`: after the existing `allowed_non_mesh |= {c["key"] for c in _tail_control_defs()}` line, add `allowed_non_mesh |= {c["key"] for c in _texture_control_defs()}`.
  - Invalid `texture_mode` (any string not in `["none", "gradient", "spots", "stripes"]`) is coerced to `"none"` (the declared default). This is handled automatically by the existing `select_str` branch in `coerce_validate_enemy_build_options`.
  - Invalid `texture_grad_direction` (any string not in `["horizontal", "vertical", "radial"]`) is coerced to `"horizontal"` (the declared default). Same mechanism.
  - `texture_spot_density` is clamped to `[0.1, 5.0]`. Values below `0.1` become `0.1`; values above `5.0` become `5.0`. Non-numeric input falls back to default `1.0` and then clamps.
  - `texture_stripe_width` is clamped to `[0.05, 1.0]`. Values below `0.05` become `0.05`; values above `1.0` become `1.0`. Non-numeric input falls back to default `0.2` and then clamps.
  - `texture_grad_color_a`, `texture_grad_color_b`, `texture_spot_color`, `texture_spot_bg_color`, `texture_stripe_color`, `texture_stripe_bg_color` are `type: "str"` fields. The validator loop does not process `str` fields; they pass through unchanged. Empty string `""` is a valid value and must not be modified. A hex string like `"ff0000"` must also pass through unchanged.
  - `texture_mode` value comparison in `coerce_validate_enemy_build_options` uses the existing `select_str` branch which calls `.strip().lower()` before comparison. A value of `"None"` (capitalized) is coerced to `"none"`.
- **Assumptions:** `_coerce_boolish` is not needed for any texture control (no `bool` type in texture defs). The existing `int`, `float`, `select`, `select_str`, and `bool` branches in `coerce_validate_enemy_build_options` already handle all required cases; no new branch is required.
- **Scope:** `asset_generation/python/src/utils/animated_build_options_validate.py` (extend `static_defs`); `asset_generation/python/src/utils/animated_build_options.py` (extend `allowed_non_mesh`).

### 2. Acceptance Criteria

**PTP-2-AC-1:** `options_for_enemy("slug", {"texture_mode": "invalid"})["texture_mode"]` returns `"none"`.

**PTP-2-AC-2:** `options_for_enemy("slug", {"texture_mode": "gradient"})["texture_mode"]` returns `"gradient"`.

**PTP-2-AC-3:** `options_for_enemy("slug", {"texture_mode": "spots"})["texture_mode"]` returns `"spots"`.

**PTP-2-AC-4:** `options_for_enemy("slug", {"texture_mode": "stripes"})["texture_mode"]` returns `"stripes"`.

**PTP-2-AC-5:** `options_for_enemy("slug", {"texture_mode": "GRADIENT"})["texture_mode"]` returns `"gradient"` (case-insensitive coercion via `.strip().lower()`).

**PTP-2-AC-6:** `options_for_enemy("slug", {"texture_mode": "None"})["texture_mode"]` returns `"none"`.

**PTP-2-AC-7:** `options_for_enemy("slug", {})["texture_mode"]` returns `"none"` (default when key absent).

**PTP-2-AC-8:** `options_for_enemy("spider", {"texture_grad_direction": "invalid"})["texture_grad_direction"]` returns `"horizontal"`.

**PTP-2-AC-9:** `options_for_enemy("spider", {"texture_grad_direction": "radial"})["texture_grad_direction"]` returns `"radial"`.

**PTP-2-AC-10:** `options_for_enemy("slug", {"texture_spot_density": 0.0})["texture_spot_density"]` returns `0.1` (clamped to min).

**PTP-2-AC-11:** `options_for_enemy("slug", {"texture_spot_density": 99.0})["texture_spot_density"]` returns `5.0` (clamped to max).

**PTP-2-AC-12:** `options_for_enemy("slug", {"texture_spot_density": 2.5})["texture_spot_density"]` returns `2.5` (valid, unchanged).

**PTP-2-AC-13:** `options_for_enemy("slug", {"texture_spot_density": 0.1})["texture_spot_density"]` returns `0.1` (boundary min, valid).

**PTP-2-AC-14:** `options_for_enemy("slug", {"texture_spot_density": 5.0})["texture_spot_density"]` returns `5.0` (boundary max, valid).

**PTP-2-AC-15:** `options_for_enemy("slug", {"texture_stripe_width": 0.0})["texture_stripe_width"]` returns `0.05` (clamped to min).

**PTP-2-AC-16:** `options_for_enemy("slug", {"texture_stripe_width": 99.0})["texture_stripe_width"]` returns `1.0` (clamped to max).

**PTP-2-AC-17:** `options_for_enemy("slug", {"texture_stripe_width": 0.5})["texture_stripe_width"]` returns `0.5` (valid, unchanged).

**PTP-2-AC-18:** `options_for_enemy("slug", {"texture_stripe_width": 0.05})["texture_stripe_width"]` returns `0.05` (boundary min, valid).

**PTP-2-AC-19:** `options_for_enemy("slug", {"texture_stripe_width": 1.0})["texture_stripe_width"]` returns `1.0` (boundary max, valid).

**PTP-2-AC-20:** `options_for_enemy("slug", {"texture_grad_color_a": "ff0000"})["texture_grad_color_a"]` returns `"ff0000"` (hex string passes through unchanged).

**PTP-2-AC-21:** `options_for_enemy("slug", {"texture_grad_color_a": ""})["texture_grad_color_a"]` returns `""` (empty string passes through unchanged).

**PTP-2-AC-22:** `options_for_enemy("slug", {})` returns a dict that includes all 10 texture keys at their declared defaults.

**PTP-2-AC-23:** Calling `options_for_enemy("claw_crawler", {"texture_mode": "spots", "texture_spot_density": 3.0})` twice with the same input returns equal dicts (idempotency).

**PTP-2-AC-24:** All existing tests in `asset_generation/python/tests/` continue to pass after the changes (non-breaking guarantee).

### 3. Risk & Ambiguity Analysis

- **`str` fields bypass coercion:** The validator loop only coerces `int`, `float`, `select`, `select_str`, and `bool` fields. `type: "str"` fields are not processed. This means hex color values are stored verbatim as Python `str` and serialized as JSON strings. The frontend must handle any format conversion (e.g., prepending `#` before passing to `THREE.Color`).
- **`allowed_non_mesh` completeness:** If any of the 10 keys is omitted from `allowed_non_mesh`, the key will be silently dropped during the merge step in `options_for_enemy()`. The implementation must use `{c["key"] for c in _texture_control_defs()}` (set comprehension over the full list) to guarantee all 10 are included.
- **`static_defs.extend()` ordering in validate:** The order in which helpers are extended does not affect coercion correctness (each entry is keyed by `"key"`). Extending `_texture_control_defs()` after `_tail_control_defs()` and before `_placement_seed_def()` matches the `animated_build_controls_for_api()` ordering for readability.

### 4. Clarifying Questions

None.

---

## Requirement PTP-3: Per-Slug Defaults and Serialization Contract

### 1. Spec Summary

- **Description:** Defaults for all 10 new controls are uniform across all 7 slugs. The serialized JSON representation of a complete enemy build options dict includes all 10 texture keys as flat top-level keys.
- **Constraints:**
  - `texture_mode` serializes as a JSON string (e.g., `"none"`, `"gradient"`).
  - `texture_grad_color_a`, `texture_grad_color_b`, `texture_grad_direction`, `texture_spot_color`, `texture_spot_bg_color`, `texture_stripe_color`, `texture_stripe_bg_color` serialize as JSON strings.
  - `texture_spot_density` serializes as a JSON number (float).
  - `texture_stripe_width` serializes as a JSON number (float).
  - The 10 keys are flat top-level keys in the build options dict, not nested under any sub-object (unlike `features` or `zone_geometry_extras`).
  - Round-trip: `json.loads(json.dumps(options_for_enemy("slug", {})))` produces a dict with all 10 texture keys at their declared defaults.
- **Assumptions:** No assumptions. Flat key structure is confirmed by analogy with `mouth_enabled`, `tail_enabled`, etc., which are flat top-level keys.
- **Scope:** Affects `asset_generation/python/src/utils/animated_build_options.py` output and any downstream JSON serialization.

### 2. Acceptance Criteria

**PTP-3-AC-1:** `options_for_enemy("slug", {})` returns a dict where `result["texture_mode"]` is the Python string `"none"`.

**PTP-3-AC-2:** `options_for_enemy("slug", {})` returns a dict where `result["texture_spot_density"]` is the Python float `1.0`.

**PTP-3-AC-3:** `options_for_enemy("slug", {})` returns a dict where `result["texture_stripe_width"]` is the Python float `0.2`.

**PTP-3-AC-4:** `json.dumps(options_for_enemy("slug", {}))` succeeds without raising `TypeError` (all values are JSON-serializable).

**PTP-3-AC-5:** After a JSON round-trip (`json.loads(json.dumps(options_for_enemy("slug", {})))`), the resulting dict contains `"texture_mode": "none"`, `"texture_spot_density": 1.0`, `"texture_stripe_width": 0.2`, and all other texture keys at their declared defaults.

**PTP-3-AC-6:** `_defaults_for_slug("player_slime")` includes all 10 texture keys at their declared defaults.

**PTP-3-AC-7:** The 10 texture keys are present at the top level of `options_for_enemy("slug", {})`, not nested under `"features"`, `"zone_geometry_extras"`, `"mesh"`, or any other sub-object.

### 3. Risk & Ambiguity Analysis

- **`texture_spot_density` and `texture_stripe_width` as Python `float`:** After coercion, these are Python `float` objects (e.g., `1.0`, not `1`). JSON serialization via `json.dumps` will render them as `1.0`, which is valid. The frontend must treat them as numbers.
- **Hex color fields as empty string by default:** Default value `""` serializes to the JSON empty string `""`. The frontend color conversion must treat `""` as white, not as an error.

### 4. Clarifying Questions

None.

---

## Requirement PTP-4: Frontend `buildControlDisabled()` Rules

### 1. Spec Summary

- **Description:** `buildControlDisabled()` in `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx` is extended with conditional disabling logic for the three mode-specific parameter groups. The function reads `texture_mode` from the `values` argument to determine which parameter group is active.
- **Constraints:**
  - `texture_mode` itself is never disabled by `buildControlDisabled()`.
  - All `texture_grad_*` keys (`texture_grad_color_a`, `texture_grad_color_b`, `texture_grad_direction`) are disabled when `texture_mode !== "gradient"`. This includes when `texture_mode` is `"none"`, `"spots"`, `"stripes"`, `undefined`, or any other value.
  - All `texture_spot_*` keys (`texture_spot_color`, `texture_spot_bg_color`, `texture_spot_density`) are disabled when `texture_mode !== "spots"`.
  - All `texture_stripe_*` keys (`texture_stripe_color`, `texture_stripe_bg_color`, `texture_stripe_width`) are disabled when `texture_mode !== "stripes"`.
  - No existing disabling rules are modified. The function remains backward compatible.
  - The function signature `buildControlDisabled(slug: string, defKey: string, values: Readonly<Record<string, unknown>>): boolean` is unchanged.
  - Evaluation order: the new texture mode checks are placed before the existing `slug === "spider"` spider placement check (or after, order does not matter for correctness as no key overlaps exist, but must be in the same function body).
  - Reading `texture_mode` from `values`: `const mode = typeof values["texture_mode"] === "string" ? values["texture_mode"] : "none";` — if `texture_mode` is absent or non-string, it is treated as `"none"`, which disables all mode-specific parameters.
- **Assumptions:** No new imports are needed. The check is a pure string comparison. `values["texture_mode"]` is the value as stored in the `animatedBuildOptionValues` store, which is the raw value set by the user (before Python coercion). The frontend must be defensive about the value type.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.tsx` — `buildControlDisabled()` function only.

### 2. Acceptance Criteria

**PTP-4-AC-1:** `buildControlDisabled("slug", "texture_mode", { texture_mode: "none" })` returns `false` (`texture_mode` control is never disabled).

**PTP-4-AC-2:** `buildControlDisabled("slug", "texture_mode", { texture_mode: "gradient" })` returns `false`.

**PTP-4-AC-3:** `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: "none" })` returns `true`.

**PTP-4-AC-4:** `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: "gradient" })` returns `false`.

**PTP-4-AC-5:** `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: "spots" })` returns `true`.

**PTP-4-AC-6:** `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: "stripes" })` returns `true`.

**PTP-4-AC-7:** `buildControlDisabled("slug", "texture_grad_color_b", { texture_mode: "gradient" })` returns `false`.

**PTP-4-AC-8:** `buildControlDisabled("slug", "texture_grad_direction", { texture_mode: "gradient" })` returns `false`.

**PTP-4-AC-9:** `buildControlDisabled("slug", "texture_grad_direction", { texture_mode: "none" })` returns `true`.

**PTP-4-AC-10:** `buildControlDisabled("slug", "texture_spot_color", { texture_mode: "spots" })` returns `false`.

**PTP-4-AC-11:** `buildControlDisabled("slug", "texture_spot_color", { texture_mode: "none" })` returns `true`.

**PTP-4-AC-12:** `buildControlDisabled("slug", "texture_spot_color", { texture_mode: "gradient" })` returns `true`.

**PTP-4-AC-13:** `buildControlDisabled("slug", "texture_spot_bg_color", { texture_mode: "spots" })` returns `false`.

**PTP-4-AC-14:** `buildControlDisabled("slug", "texture_spot_density", { texture_mode: "spots" })` returns `false`.

**PTP-4-AC-15:** `buildControlDisabled("slug", "texture_spot_density", { texture_mode: "stripes" })` returns `true`.

**PTP-4-AC-16:** `buildControlDisabled("slug", "texture_stripe_color", { texture_mode: "stripes" })` returns `false`.

**PTP-4-AC-17:** `buildControlDisabled("slug", "texture_stripe_color", { texture_mode: "spots" })` returns `true`.

**PTP-4-AC-18:** `buildControlDisabled("slug", "texture_stripe_color", { texture_mode: "none" })` returns `true`.

**PTP-4-AC-19:** `buildControlDisabled("slug", "texture_stripe_bg_color", { texture_mode: "stripes" })` returns `false`.

**PTP-4-AC-20:** `buildControlDisabled("slug", "texture_stripe_width", { texture_mode: "stripes" })` returns `false`.

**PTP-4-AC-21:** `buildControlDisabled("slug", "texture_stripe_width", { texture_mode: "gradient" })` returns `true`.

**PTP-4-AC-22:** `buildControlDisabled("slug", "texture_grad_color_a", {})` returns `true` (missing `texture_mode` treated as `"none"`).

**PTP-4-AC-23:** `buildControlDisabled("slug", "texture_grad_color_a", { texture_mode: 42 })` returns `true` (non-string `texture_mode` treated as `"none"`).

**PTP-4-AC-24 (non-breaking):** `buildControlDisabled("slug", "pupil_shape", { pupil_enabled: false })` returns `true` (existing pupil rule unchanged).

**PTP-4-AC-25 (non-breaking):** `buildControlDisabled("slug", "mouth_shape", { mouth_enabled: false })` returns `true` (existing mouth rule unchanged).

**PTP-4-AC-26 (non-breaking):** `buildControlDisabled("slug", "tail_length", { tail_enabled: false })` returns `true` (existing tail rule unchanged).

**PTP-4-AC-27 (non-breaking):** `buildControlDisabled("spider", "eye_uniform_shape", { eye_distribution: "random" })` returns `true` (existing spider eye rule unchanged).

**PTP-4-AC-28:** `buildControlDisabled("spider", "texture_grad_color_a", { texture_mode: "none" })` returns `true` (texture rules apply to spider slug too).

### 3. Risk & Ambiguity Analysis

- **`texture_mode` absent from values:** If the user has not yet set `texture_mode`, `values["texture_mode"]` will be `undefined`. The implementation must treat this as `"none"`, disabling all mode-specific parameters.
- **Non-string `texture_mode`:** If `values["texture_mode"]` is a number or boolean (e.g., from a stale store), the `typeof` check must coerce to `"none"`.
- **Key prefix matching vs. exact key matching:** The implementation must check exact key matches for each of the 9 parameter keys, not prefix-based matching. This avoids future accidental disabling of keys with similar names.

### 4. Clarifying Questions

None.

---

## Requirement PTP-5: Three.js Shader Overlay in GlbViewer.tsx

### 1. Spec Summary

- **Description:** Inside the `Model` component in `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx`, a `useEffect` applies a Three.js `ShaderMaterial` overlay to all `THREE.Mesh` children of the loaded GLB `scene` when `texture_mode` is non-`"none"`. When `texture_mode` is `"none"`, original materials are restored. The effect reacts to store changes without requiring a GLB reload.
- **Constraints:**
  - The `Model` component already receives `url` and `animation` props and has access to `scene` from `useGLTF(url)`.
  - The overlay effect reads `texture_mode` and the 9 associated parameter values from `useAppStore`'s `animatedBuildOptionValues[slug]`, where `slug` is derived from `commandContext` (same derivation as in `BuildControls.tsx`: if `cmd === "player"` and color is valid, use `PLAYER_PROCEDURAL_BUILD_SLUG`; otherwise `normalizeAnimatedSlug(enemy)`).
  - Original materials are stored in a `useRef<Map<string, THREE.Material | THREE.Material[]>>` keyed by `mesh.uuid`. This ref is populated the first time the effect runs after `scene` is loaded (the first call after `useGLTF(url)` resolves).
  - On GLB URL change: the stored materials map must be cleared (set to an empty `Map`) and re-captured from the new scene's meshes. This prevents restored materials from one GLB being applied to a different GLB's meshes.
  - When `texture_mode` is `"gradient"`:
    - A `THREE.ShaderMaterial` is constructed using `texture_grad_color_a`, `texture_grad_color_b`, and `texture_grad_direction` uniform values.
    - The `ShaderMaterial` is applied to `mesh.material` for every `THREE.Mesh` found by traversing `scene.traverse()`.
    - Uniforms: `uColorA: { value: THREE.Color }`, `uColorB: { value: THREE.Color }`, `uDirection: { value: number }` where direction encodes horizontal=0, vertical=1, radial=2.
    - Vertex shader declares `varying vec2 vUv; varying vec3 vPosition;` and assigns `vUv = uv; vPosition = position;`.
    - Fragment shader blends between `uColorA` and `uColorB` based on direction: horizontal uses `vUv.x`; vertical uses `vUv.y`; radial uses `length(vUv - vec2(0.5))` scaled to `[0, 1]`.
  - When `texture_mode` is `"spots"`:
    - A `THREE.ShaderMaterial` is constructed using `texture_spot_color`, `texture_spot_bg_color`, and `texture_spot_density`.
    - Uniforms: `uSpotColor: { value: THREE.Color }`, `uBgColor: { value: THREE.Color }`, `uDensity: { value: number }`.
    - Fragment shader generates spot pattern using `fract(vUv * uDensity)` offset to `[-0.5, 0.5]` and emits `uSpotColor` inside a circle of radius 0.35, `uBgColor` outside.
  - When `texture_mode` is `"stripes"`:
    - A `THREE.ShaderMaterial` is constructed using `texture_stripe_color`, `texture_stripe_bg_color`, and `texture_stripe_width`.
    - Uniforms: `uStripeColor: { value: THREE.Color }`, `uBgColor: { value: THREE.Color }`, `uStripeWidth: { value: number }`.
    - Fragment shader generates stripe pattern using `fract(vUv.x)` (horizontal stripes); emits `uStripeColor` when `fract(vUv.x) < uStripeWidth`, `uBgColor` otherwise.
  - When `texture_mode` is `"none"` or absent: for every `THREE.Mesh` in the scene, restore the original material from the stored ref (by `mesh.uuid`). If no stored material is found for a mesh UUID (new mesh), leave its material unchanged.
  - Hex-to-THREE.Color conversion: for each color parameter, if the stored string is `""` (empty), use `new THREE.Color(1, 1, 1)` (white). Otherwise, attempt `new THREE.Color("#" + hexString)`. If the string is already prefixed with `#`, use it as-is. If parsing fails (invalid hex), fall back to `new THREE.Color(1, 1, 1)` (white).
  - The effect must not cause React errors (no state mutations inside render, no missing dependencies warnings in strict mode).
  - The effect dependency array must include: `scene`, `texture_mode`, and all 9 associated parameter values. On any change to these values, the effect re-runs without reloading the GLB.
  - The effect does not run before `scene` is populated. `useGLTF` is a suspending hook; `scene` is guaranteed to be non-null when the `Model` component body executes. No additional guard is required.
  - The `Model` component does not pass texture params as props. It reads them directly from the store via `useAppStore`.
- **Assumptions:** The `Model` component is currently a standalone function component inside `GlbViewer.tsx`. Adding `useAppStore` hooks to `Model` is permitted. If the implementation agent extracts the overlay to a separate component or custom hook for cleanliness, this is acceptable, provided it is called from within `Model` and the behavioral requirements are met.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx` — `Model` function and its supporting hooks.

### 2. Acceptance Criteria

**PTP-5-AC-1:** When `texture_mode` is set to `"gradient"` in the store, all `THREE.Mesh` children of the loaded GLB have their `material` replaced with a `THREE.ShaderMaterial` instance. The replacement occurs without reloading the GLB URL.

**PTP-5-AC-2:** When `texture_mode` is subsequently set to `"none"`, all `THREE.Mesh` children of the loaded GLB have their original materials restored.

**PTP-5-AC-3:** The gradient `ShaderMaterial` has exactly three uniforms: `uColorA`, `uColorB`, and `uDirection`. Changing `texture_grad_color_a` in the store causes `uColorA` to update on the next effect run.

**PTP-5-AC-4:** When `texture_grad_color_a` is `""`, the `uColorA` uniform value is `new THREE.Color(1, 1, 1)` (white).

**PTP-5-AC-5:** When `texture_grad_color_a` is `"ff0000"`, the `uColorA` uniform value is `new THREE.Color("#ff0000")` (red).

**PTP-5-AC-6:** The spots `ShaderMaterial` has exactly three uniforms: `uSpotColor`, `uBgColor`, and `uDensity`. Changing `texture_spot_density` in the store causes `uDensity` to update.

**PTP-5-AC-7:** The stripes `ShaderMaterial` has exactly three uniforms: `uStripeColor`, `uBgColor`, and `uStripeWidth`. Changing `texture_stripe_width` in the store causes `uStripeWidth` to update.

**PTP-5-AC-8:** When a new GLB URL is loaded (`url` changes), the stored original materials map is cleared and re-captured from the new scene's meshes before any texture overlay is applied.

**PTP-5-AC-9:** `texture_grad_direction: "horizontal"` passes `uDirection = 0`; `"vertical"` passes `uDirection = 1`; `"radial"` passes `uDirection = 2`.

**PTP-5-AC-10:** No React errors appear in the browser console when toggling between texture modes in the preview.

**PTP-5-AC-11:** The gradient vertex shader declares both `varying vec2 vUv;` and `varying vec3 vPosition;` varyings; the spots and stripes vertex shaders declare at minimum `varying vec2 vUv;`.

**PTP-5-AC-12:** The three `ShaderMaterial` instances used for gradient, spots, and stripes are visually distinct from each other and from flat-shaded materials when non-default colors are applied.

**PTP-5-AC-13:** `texture_mode` absent from the store (slug not yet loaded) is treated as `"none"` — no material override is applied.

### 3. Risk & Ambiguity Analysis

- **`Model` component inside `Suspense`:** `useGLTF` suspends. The `Model` function body only executes after the GLB is resolved, so `scene` is always non-null when the overlay effect runs. No additional null guard is required on `scene`, but the effect should guard against an empty `scene.children` (e.g., an empty GLB).
- **Material capture timing:** The ref must be populated from the scene meshes on first run (when the ref map is empty or after URL change). Subsequent runs must use the stored originals for restoration, not re-capture from the scene (since the scene meshes may already have shader materials applied from a previous run).
- **`scene.traverse()` vs. `scene.children`:** `scene.traverse()` visits all descendants recursively, which is necessary for deeply nested GLB hierarchies. Using only `scene.children` would miss nested mesh nodes.
- **Hex string format from store:** The store holds raw user input strings (whatever was typed into the text control). The conversion function must handle: empty string, 6-char lowercase hex (`"ff0000"`), 6-char uppercase hex (`"FF0000"`), strings prefixed with `#` (`"#ff0000"`), and invalid strings (fall back to white). The `THREE.Color` constructor accepts `"#rrggbb"` format natively.
- **`commandContext` derivation inside `Model`:** `BuildControls` and `Model` derive `slug` from `commandContext` using the same logic. The implementation must replicate this derivation exactly (including the `player` + valid color check). A shared utility function is acceptable if it already exists; otherwise the logic is duplicated.
- **ShaderMaterial and existing material types:** Some GLB meshes may use `MeshStandardMaterial` or other standard material types. Replacing with `ShaderMaterial` will drop lighting/PBR effects. This is acceptable per the ticket scope (preview-only overlay). When restored to `"none"`, the original `MeshStandardMaterial` is restored and PBR effects return.
- **`needsUpdate` flag:** After replacing `mesh.material`, `mesh.material.needsUpdate = true` must be set to ensure Three.js re-renders the mesh with the new material.

### 4. Clarifying Questions

None. All resolved by reading the codebase and the ticket's Risk and Assumptions table.

---

## Requirement PTP-6: Python Test Coverage (`test_texture_controls.py`)

### 1. Spec Summary

- **Description:** A new Python test file `asset_generation/python/tests/utils/test_texture_controls.py` covers the Python-side requirements: control declarations, per-slug coverage, defaults, coercion, validation, and idempotency.
- **Constraints:**
  - Test file path: `asset_generation/python/tests/utils/test_texture_controls.py`
  - Tests are authored by the Test Designer Agent; they are RED until the implementation (Tasks 1–3) completes.
  - All tests use `pytest` style (function-based, no class wrappers unless grouping is clearer).
  - All 7 slugs must be covered either by parametrize or by explicit iteration.
- **Assumptions:** `pytest.mark.parametrize` is available (confirmed by existing test suite).
- **Scope:** `asset_generation/python/tests/utils/test_texture_controls.py` (new file).

### 2. Acceptance Criteria

**PTP-6-AC-1:** Test: `_texture_control_defs()` returns exactly 10 entries.

**PTP-6-AC-2:** Test: all 7 slugs (spider, slug, claw_crawler, imp, carapace_husk, spitter, player_slime) expose all 10 texture control keys in `animated_build_controls_for_api()`.

**PTP-6-AC-3:** Test: `_texture_control_defs()` called twice returns two different list objects (mutation guard).

**PTP-6-AC-4:** Test: `options_for_enemy("slug", {"texture_mode": "invalid"})["texture_mode"] == "none"`.

**PTP-6-AC-5:** Test: `options_for_enemy("slug", {"texture_mode": "gradient"})["texture_mode"] == "gradient"`.

**PTP-6-AC-6:** Test: `texture_spot_density` clamped at lower bound — `options_for_enemy("slug", {"texture_spot_density": 0.0})["texture_spot_density"] == 0.1`.

**PTP-6-AC-7:** Test: `texture_spot_density` clamped at upper bound — `options_for_enemy("slug", {"texture_spot_density": 99.0})["texture_spot_density"] == 5.0`.

**PTP-6-AC-8:** Test: `texture_stripe_width` clamped at lower bound — `options_for_enemy("slug", {"texture_stripe_width": 0.0})["texture_stripe_width"] == 0.05`.

**PTP-6-AC-9:** Test: `texture_stripe_width` clamped at upper bound — `options_for_enemy("slug", {"texture_stripe_width": 99.0})["texture_stripe_width"] == 1.0`.

**PTP-6-AC-10:** Test: empty hex string color fields round-trip — `options_for_enemy("slug", {"texture_grad_color_a": ""})["texture_grad_color_a"] == ""`.

**PTP-6-AC-11:** Test: non-empty hex string color fields round-trip — `options_for_enemy("slug", {"texture_grad_color_a": "ff0000"})["texture_grad_color_a"] == "ff0000"`.

**PTP-6-AC-12:** Test: all 10 texture keys present in `_defaults_for_slug(slug)` output at correct defaults (parametrized over all 7 slugs).

**PTP-6-AC-13:** Test (idempotency): calling `options_for_enemy("claw_crawler", {"texture_mode": "spots", "texture_spot_density": 3.0})` twice returns equal dicts.

**PTP-6-AC-14:** Test: `animated_build_controls_for_api()["slug"]` has the `placement_seed` entry appearing after all 10 texture control entries (ordering check).

**PTP-6-AC-15:** Test: `options_for_enemy("slug", {"texture_mode": "SPOTS"})["texture_mode"] == "spots"` (case-insensitive coercion).

**PTP-6-AC-16:** Test: `options_for_enemy("spider", {"texture_grad_direction": "radial"})["texture_grad_direction"] == "radial"` (valid non-default direction passes through).

**PTP-6-AC-17:** Test: `options_for_enemy("spider", {"texture_grad_direction": "diagonal"})["texture_grad_direction"] == "horizontal"` (invalid direction coerces to default).

**PTP-6-AC-18:** Test: `bash .lefthook/scripts/py-tests.sh` exits 0 after implementation completes.

### 3. Risk & Ambiguity Analysis

- **Slug enumeration:** The test must not hardcode a fixed list of slugs but instead derive them from `animated_build_controls_for_api().keys()` to remain future-proof. The fixture for all 7 slugs should cross-reference the expected set.
- **`_texture_control_defs` import path:** The function is in `animated_build_options_appendage_defs`. Tests must import it from that module path (or via the public `animated_build_options` module if re-exported there).

### 4. Clarifying Questions

None.

---

## Requirement PTP-7: Frontend Test Coverage (`BuildControls.texture.test.tsx`)

### 1. Spec Summary

- **Description:** A new Vitest test file `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx` covers the frontend conditional disabling rules introduced in PTP-4.
- **Constraints:**
  - Test file path: `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx`
  - Tests are authored by the Test Designer Agent; they are RED until the Task 4 implementation completes.
  - `BuildControls.mouthTail.test.tsx` is the structural pattern to follow.
  - Tests should verify the disabling behavior by rendering the `BuildControls` component (or calling `buildControlDisabled` directly if it is exported) with specific store states.
  - Disabled rows must have `opacity: 0.42` and `pointerEvents: "none"` applied (following the existing `ControlRow` disabled rendering pattern).
- **Assumptions:** `buildControlDisabled` may not be exported; tests that render `BuildControls` and inspect the DOM are acceptable if the function is not directly callable.
- **Scope:** `asset_generation/web/frontend/src/components/Preview/BuildControls.texture.test.tsx` (new file).

### 2. Acceptance Criteria

**PTP-7-AC-1:** Test: `texture_grad_color_a` row has `opacity: 0.42` and `pointerEvents: "none"` when `texture_mode` is `"none"`.

**PTP-7-AC-2:** Test: `texture_grad_color_a` row does not have disabled styling when `texture_mode` is `"gradient"`.

**PTP-7-AC-3:** Test: `texture_grad_color_a` row has disabled styling when `texture_mode` is `"spots"` (non-gradient non-none).

**PTP-7-AC-4:** Test: `texture_stripe_color` row has disabled styling when `texture_mode` is `"spots"`.

**PTP-7-AC-5:** Test: `texture_spot_color` row has disabled styling when `texture_mode` is `"stripes"`.

**PTP-7-AC-6:** Test: `texture_mode` control row itself is not disabled regardless of mode value (for each of the 4 valid mode values).

**PTP-7-AC-7 (non-bleed):** Test: changing `texture_mode` does not affect the disabling of `pupil_shape` (pupil rule remains controlled by `pupil_enabled`).

**PTP-7-AC-8 (non-bleed):** Test: changing `texture_mode` does not affect the disabling of `mouth_shape` (mouth rule remains controlled by `mouth_enabled`).

**PTP-7-AC-9:** Test: the `texture_mode` select control renders all four options: `"none"`, `"gradient"`, `"spots"`, `"stripes"`.

**PTP-7-AC-10:** Test: `texture_spot_density` row has disabled styling when `texture_mode` is `"none"`.

**PTP-7-AC-11:** Test: `texture_stripe_width` row has disabled styling when `texture_mode` is `"gradient"`.

**PTP-7-AC-12:** Test: `cd asset_generation/web/frontend && npm test` exits 0 after implementation completes (no snapshot failures).

### 3. Risk & Ambiguity Analysis

- **Store mocking:** Tests must mock `useAppStore` to inject controlled `animatedBuildOptionValues` for the test slug. The existing `BuildControls.mouthTail.test.tsx` provides the pattern for this.
- **ControlRow rendering pattern for disabled state:** The existing `ControlRow` component applies `opacity: 0.42` and `pointerEvents: "none"` when its `isDisabled` prop is true. Tests should query by label text and inspect the parent row's style.

### 4. Clarifying Questions

None.

---

## Requirement PTP-8: Non-Breaking Guarantee

### 1. Spec Summary

- **Description:** All existing build controls, coercion rules, and frontend disabling rules remain unaffected by this change. No existing test must fail due to the new texture controls.
- **Constraints:**
  - `animated_build_controls_for_api()` for all existing slugs continues to include all previously defined controls in the same order.
  - `options_for_enemy()` for all existing slugs continues to return all previously defined keys at the same values when called with the same input.
  - `buildControlDisabled()` for all existing control keys (`pupil_shape`, `mouth_shape`, `tail_shape`, `tail_length`, `eye_uniform_shape`) continues to return the same boolean values.
  - `bash .lefthook/scripts/py-tests.sh` continues to exit 0 after all Python changes.
  - `cd asset_generation/web/frontend && npm test` continues to exit 0 after all frontend changes.
- **Assumptions:** No assumptions.
- **Scope:** Entire `asset_generation/python/` and `asset_generation/web/frontend/` test suites.

### 2. Acceptance Criteria

**PTP-8-AC-1:** All Python tests present before this ticket pass after implementation.

**PTP-8-AC-2:** All frontend tests present before this ticket pass after implementation.

**PTP-8-AC-3:** `options_for_enemy("spider", {})` continues to return `{"eye_count": ..., "eye_shape": ..., "pupil_enabled": False, ...}` at unchanged defaults.

**PTP-8-AC-4:** The `placement_seed` key continues to appear as the last entry in the per-slug control list for all slugs.

### 3. Risk & Ambiguity Analysis

- **`placement_seed` remains last:** The insertion of `_texture_control_defs()` before `[_placement_seed_def()]` in `merged` must preserve `placement_seed` as the final entry. Tests should confirm this ordering.

### 4. Clarifying Questions

None.
