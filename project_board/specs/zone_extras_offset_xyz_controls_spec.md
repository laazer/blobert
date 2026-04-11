# Spec: Zone Geometry Extras — Per-Zone X/Y/Z Offset Controls
## Ticket: 17_zone_extras_offset_xyz_controls

---

## Overview

Add three `float` controls per feature zone (`offset_x`, `offset_y`, `offset_z`) that translate the ellipsoid center used for zone geometry extras placement. The offset is applied in **Blender world-space** (Z-up, X=front/right, Y=depth) immediately before any geometry is placed, shifting the entire extra construct uniformly for that zone.

---

## Resolved Open Questions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Coordinate space | Blender world-space (Z-up). offset_x/y/z shift cx/cy/cz directly. | `_PLACE_WORLD` and `_ellipsoid_point_at` already operate in this space. No coordinate-system conversion needed. |
| Range / step / default | -2.0 to +2.0, step 0.05, default 0.0 | Body ref scale is ~0.5–2.0; this range allows up to two full body-radius shifts. Step 0.05 matches existing float controls (spike_size, clustering). |
| Visibility when kind=none or kind=shell | Always visible, always enabled. No-op when kind=none or kind=shell (no geometry is generated to shift). | Same as _finish and _hex: structural properties that persist regardless of kind. Consistent with how place_* flags are stored but unused for kind=none. |
| Key schema | Both flat and nested accepted. Canonical storage: nested under `zone_geometry_extras[zone]`. | Identical to spike_count, clustering, distribution, etc. |

---

## Requirement 1: Python — Constants and Key Schema

### 1. Spec Summary

**Description:** Three new module-level constants define the numeric bounds for offset controls. The fields `offset_x`, `offset_y`, `offset_z` are added to `_ZONE_GEOM_EXTRA_FIELDS`, `_EXTRA_ZONE_FLAT_KEY` regex, `_default_zone_geometry_extras_payload()`, and all downstream functions that process zone geometry extras.

**Constraints:**
- Constants must be named `_OFFSET_XYZ_MIN = -2.0`, `_OFFSET_XYZ_MAX = 2.0`, `_OFFSET_XYZ_STEP = 0.05`.
- `_EXTRA_ZONE_FLAT_KEY` regex must be extended to match `offset_x`, `offset_y`, `offset_z` as valid suffixes. The zone capture group (`body|head|limbs|joints|extra`) is unchanged.
- `_ZONE_GEOM_EXTRA_FIELDS` must include `"offset_x"`, `"offset_y"`, `"offset_z"` so the merge path copies them from base dicts.
- `_default_zone_geometry_extras_payload()` must return `"offset_x": 0.0`, `"offset_y": 0.0`, `"offset_z": 0.0`.
- All zones returned by `_feature_zones(slug)` get offset fields; no zone is excluded.

**Assumptions:** The `_EXTRA_ZONE_FLAT_KEY` regex is the gating regex for flat-key dispatch in `_merge_zone_geometry_extras` and `options_for_enemy`. Extending it is the only regex change required. The `_FEAT_ZONE_FLAT_KEY`, `_FEAT_LIMB_PART_FLAT_KEY`, and `_FEAT_JOINT_PART_FLAT_KEY` regexes are unaffected.

**Scope:** `asset_generation/python/src/utils/animated_build_options.py` only.

### 2. Acceptance Criteria

- **AC-1.1:** `_OFFSET_XYZ_MIN`, `_OFFSET_XYZ_MAX`, `_OFFSET_XYZ_STEP` are defined at module level as `-2.0`, `2.0`, `0.05` respectively (type `float`).
- **AC-1.2:** `_EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_offset_x")` is not `None`. Same for `offset_y`, `offset_z`, and all valid zone names (`head`, `limbs`, `joints`, `extra`).
- **AC-1.3:** `_EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_offset_w")` is `None` (non-existent axis rejected).
- **AC-1.4:** `_EXTRA_ZONE_FLAT_KEY.match("extra_zone_body_offset_x")` captures group 1 as `"body"` and group 2 as `"offset_x"`.
- **AC-1.5:** `"offset_x" in _ZONE_GEOM_EXTRA_FIELDS` is `True`. Same for `"offset_y"` and `"offset_z"`.
- **AC-1.6:** `_default_zone_geometry_extras_payload()` returns a dict containing `{"offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0}`.
- **AC-1.7:** All existing keys in `_default_zone_geometry_extras_payload()` before this change are still present unchanged.

---

## Requirement 2: Python — Merge Logic

### 1. Spec Summary

**Description:** `_merge_zone_geometry_extras` must handle `offset_x`, `offset_y`, `offset_z` as `float` fields. Both the nested path (`src["zone_geometry_extras"][zone]["offset_x"]`) and the flat path (`src["extra_zone_{zone}_offset_x"]`) must set the field in the output dict. Invalid (non-numeric) values are silently dropped (field stays at current value).

**Constraints:**
- Merge priority order (later wins, matching all other fields): defaults → base dict → nested source → flat source keys.
- Float coercion uses `float(v)` inside a `try/except (TypeError, ValueError)` block; on failure the field is not updated.
- No clamping occurs at merge time. Clamping is exclusively the responsibility of `_sanitize_zone_geometry_extras` (Requirement 3).
- The flat-key dispatch branch for `offset_x/y/z` must be inside the `elif` chain that handles `float`-typed fields, alongside `spike_size`, `bulb_size`, `clustering`.

**Assumptions:** The existing merge function handles `spike_size` and `bulb_size` as float with `try/except`. The new offset fields follow the exact same pattern.

**Scope:** `_merge_zone_geometry_extras` in `asset_generation/python/src/utils/animated_build_options.py`.

### 2. Acceptance Criteria

- **AC-2.1:** Given `src = {"extra_zone_body_offset_x": 1.5}`, `_merge_zone_geometry_extras("slug", src, base)` returns a dict where `result["body"]["offset_x"] == 1.5`.
- **AC-2.2:** Given `src = {"zone_geometry_extras": {"body": {"offset_y": -0.75}}}`, the result has `result["body"]["offset_y"] == -0.75`.
- **AC-2.3:** Given both flat and nested for the same field with different values, flat wins: `src = {"zone_geometry_extras": {"body": {"offset_z": 0.5}}, "extra_zone_body_offset_z": 1.0}` → `result["body"]["offset_z"] == 1.0`.
- **AC-2.4:** Given `src = {"extra_zone_body_offset_x": "not_a_number"}`, the field is not updated (stays at the base/default value, no exception raised).
- **AC-2.5:** Given no offset keys in `src`, all three offset fields in the output equal the corresponding values from the base dict (defaulting to 0.0 if base also had no offsets).
- **AC-2.6:** Offset values outside the clamping range (e.g. `5.0` or `-3.0`) are preserved without clamping through the merge step. Clamping only occurs in sanitize.
- **AC-2.7:** An offset key for a zone not in `_feature_zones(slug)` (e.g. `extra_zone_joints_offset_x` for a slug whose zones do not include `joints`) is silently ignored.

---

## Requirement 3: Python — Sanitize Logic

### 1. Spec Summary

**Description:** `_sanitize_zone_geometry_extras` must clamp `offset_x`, `offset_y`, `offset_z` to `[_OFFSET_XYZ_MIN, _OFFSET_XYZ_MAX]` for each zone. Invalid (non-numeric) values reset to `0.0`. The sanitize path is called by `_coerce_and_validate` after merging, so it is the final validation gate before values reach the attach layer.

**Constraints:**
- Clamping: `max(_OFFSET_XYZ_MIN, min(_OFFSET_XYZ_MAX, value))` applied after `float(value)`.
- On `TypeError` or `ValueError` from `float()`, the field resets to `0.0` (the default).
- Sanitize is called once per zone per field. No side effects on other fields.
- The sanitize block for offset fields is structurally identical to the spike_size sanitize block: `try: v = float(raw.get("offset_x", 0.0)) except ...: v = 0.0; entry["offset_x"] = max(MIN, min(MAX, v))`.

**Assumptions:** `_sanitize_zone_geometry_extras` iterates over all zones for the slug and rebuilds each zone's entry from scratch using `_default_zone_geometry_extras_payload()` as the base. The offset fields must be present in the default payload (Requirement 1 AC-1.6) for the pattern to be consistent.

**Scope:** `_sanitize_zone_geometry_extras` in `asset_generation/python/src/utils/animated_build_options.py`.

### 2. Acceptance Criteria

- **AC-3.1:** `_sanitize_zone_geometry_extras("slug", {"body": {"offset_x": 5.0, ...}})` returns a dict where `result["body"]["offset_x"] == 2.0` (clamped to max).
- **AC-3.2:** `_sanitize_zone_geometry_extras("slug", {"body": {"offset_y": -3.0, ...}})` → `result["body"]["offset_y"] == -2.0` (clamped to min).
- **AC-3.3:** `_sanitize_zone_geometry_extras("slug", {"body": {"offset_z": "bad", ...}})` → `result["body"]["offset_z"] == 0.0` (invalid resets to default).
- **AC-3.4:** `_sanitize_zone_geometry_extras("slug", {"body": {"offset_x": 0.0, ...}})` → `result["body"]["offset_x"] == 0.0` (identity: zero passes through unchanged).
- **AC-3.5:** `_sanitize_zone_geometry_extras("slug", {"body": {"offset_x": 2.0, ...}})` → `result["body"]["offset_x"] == 2.0` (boundary value not over-clamped).
- **AC-3.6:** `_sanitize_zone_geometry_extras("slug", {"body": {"offset_x": -2.0, ...}})` → `result["body"]["offset_x"] == -2.0` (boundary value not over-clamped).
- **AC-3.7:** Zone entries that lack offset keys in the input dict produce `offset_x == 0.0`, `offset_y == 0.0`, `offset_z == 0.0` in the output (defaults applied).
- **AC-3.8:** Offset sanitize for one zone does not affect another zone's offset fields.

---

## Requirement 4: Python — Control Definitions (API Metadata)

### 1. Spec Summary

**Description:** `_zone_extra_control_defs(slug)` must emit three `float` control defs per zone, appended after `hex` in the per-zone block. The defs follow the exact same shape as `spike_size` and `clustering` defs.

**Constraints:**
- Three defs per zone, in order: `offset_x`, `offset_y`, `offset_z`.
- Each def has: `key`, `label`, `type: "float"`, `min: _OFFSET_XYZ_MIN`, `max: _OFFSET_XYZ_MAX`, `step: _OFFSET_XYZ_STEP`, `default: 0.0`.
- Key format: `f"extra_zone_{zone}_offset_x"` (lowercase, underscore-separated).
- Labels: `f"{ZLabel} offset X (Blender world +X = front)"`, `f"{ZLabel} offset Y (Blender world +Y = right)"`, `f"{ZLabel} offset Z (Blender world +Z = up)"` where `ZLabel = zone.replace("_", " ").title()`.
- The three offset defs appear after the `hex` def within the same zone block, so they are the last three entries for each zone.
- `animated_build_controls_for_api()` picks up the new defs automatically (no change needed there).

**Assumptions:** The ordering within a zone block is: kind → spike_shape → spike_count → spike_size → bulb_count → bulb_size → clustering → distribution → uniform_shape → place_top → place_bottom → place_front → place_back → place_right → place_left → finish → hex → offset_x → offset_y → offset_z.

**Scope:** `_zone_extra_control_defs` in `asset_generation/python/src/utils/animated_build_options.py`.

### 2. Acceptance Criteria

- **AC-4.1:** For any slug, `_zone_extra_control_defs(slug)` returns defs containing `extra_zone_{zone}_offset_x`, `extra_zone_{zone}_offset_y`, `extra_zone_{zone}_offset_z` for every zone in `_feature_zones(slug)`.
- **AC-4.2:** Each offset def has `"type": "float"`, `"min": -2.0`, `"max": 2.0`, `"step": 0.05`, `"default": 0.0`.
- **AC-4.3:** The offset defs appear after the `extra_zone_{zone}_hex` def in the returned list.
- **AC-4.4:** `animated_build_controls_for_api()["imp"]` includes `"extra_zone_body_offset_x"` in the returned def list (end-to-end integration of the above).
- **AC-4.5:** No `"min"` or `"max"` field is a hardcoded literal; they reference `_OFFSET_XYZ_MIN` and `_OFFSET_XYZ_MAX` (verifiable by inspection during code review).

---

## Requirement 5: Python — Attach Math (Ellipsoid Center Offset Application)

### 1. Spec Summary

**Description:** `_append_body_ellipsoid_extras` and `_append_head_ellipsoid_extras` must read `offset_x`, `offset_y`, `offset_z` from their `spec` dict and apply them to the incoming ellipsoid center coordinates before any placement logic runs. All subsequent calls that use the center coordinates (`_ellipsoid_point_at`, `_ellipsoid_normal`, `_orient_cone_outward`, `hc` tuple, inline `hx/hy/hz` references) must use the shifted coordinates.

**Constraints:**
- A private helper `_zone_extra_offset(spec: dict[str, Any], axis: str) -> float` is defined in `zone_geometry_extras_attach.py`. It returns `float(spec.get(axis, 0.0))` with clamping to `[-2.0, 2.0]` and falls back to `0.0` on any exception. The clamp range matches `_OFFSET_XYZ_MIN`/`_OFFSET_XYZ_MAX` (the sanitize layer guarantees values are already in range, but the helper defends against direct calls with unsanitized dicts).
- In `_append_body_ellipsoid_extras`: at the top of the function body (before `kind = ...`), compute: `cx = cx + _zone_extra_offset(spec, "offset_x")`, `cy = cy + _zone_extra_offset(spec, "offset_y")`, `cz = cz + _zone_extra_offset(spec, "offset_z")`. These reassign the local parameter variables. All downstream uses of cx/cy/cz within the function automatically use the shifted values.
- In `_append_head_ellipsoid_extras`: same pattern at the top of the function. The local variables are named `hx`, `hy`, `hz` (matching the function parameter names). Apply: `hx = hx + _zone_extra_offset(spec, "offset_x")`, `hy = hy + _zone_extra_offset(spec, "offset_y")`, `hz = hz + _zone_extra_offset(spec, "offset_z")`. The `hc` tuple that follows must be recomputed from the shifted values.
- The `_ellipsoid_normal` call uses the shifted center coordinates. This ensures normals are computed relative to the shifted ellipsoid position, maintaining consistent outward-pointing normals.
- The radii (`a`, `b`, `h` for body; `ax`, `ay`, `az` for head) are never modified by the offset. Only the center is shifted.
- `append_animated_enemy_zone_extras` (the public entry point) is not modified. The `bc` and `hc` vectors read from the model are unchanged; the offset is applied only inside the private attach functions.

**Assumptions:** After sanitize, `spec["offset_x"]` is always a `float` in `[-2.0, 2.0]`. The helper's try/except and clamp are defensive-only for direct call paths (e.g., tests calling attach functions with unsanitized dicts). When `kind == "none"` or `kind == "shell"`, the offset is computed but no geometry is created; the computation is a no-op for the output.

**Scope:** `asset_generation/python/src/enemies/zone_geometry_extras_attach.py`.

### 2. Acceptance Criteria

- **AC-5.1:** `_zone_extra_offset({"offset_x": 1.0}, "offset_x")` returns `1.0`.
- **AC-5.2:** `_zone_extra_offset({}, "offset_x")` returns `0.0` (missing key → default).
- **AC-5.3:** `_zone_extra_offset({"offset_x": "bad"}, "offset_x")` returns `0.0` (invalid value → default).
- **AC-5.4:** `_zone_extra_offset({"offset_x": 5.0}, "offset_x")` returns `2.0` (clamped to max).
- **AC-5.5:** When `_append_body_ellipsoid_extras` is called with `spec = {"kind": "spikes", "spike_count": 1, "offset_x": 1.0, ...}` and `cx = 0.0`, the spike placement point has an X-component of approximately `1.0 + a * sin(phi) * cos(theta)` (center shifted by 1.0 before ellipsoid surface formula). Verifiable by stubbing `create_cone` and `create_sphere` and inspecting location arguments.
- **AC-5.6:** When `_append_body_ellipsoid_extras` is called with `spec = {"kind": "spikes", "offset_x": 0.0, "offset_y": 0.0, "offset_z": 0.0, ...}` and a given `cx/cy/cz`, the placement result is identical to calling with the same spec but no offset fields present (zero offset is identity).
- **AC-5.7:** When `_append_head_ellipsoid_extras` is called with `spec = {"kind": "spikes", "offset_z": 0.5, ...}` and `hz = 1.0`, the head-point computation uses `hz_effective = 1.5`. Verifiable by stubbing `create_cone` and inspecting the Z-component of the location argument.
- **AC-5.8:** Body zone offset does not affect the head zone's `hx/hy/hz` values (each attach function reads its own spec dict; the body spec and head spec are separate dicts from `raw.get("body")` and `raw.get("head")`).
- **AC-5.9:** When `kind == "none"`, no geometry is created, but calling `_append_body_ellipsoid_extras` or `_append_head_ellipsoid_extras` with a non-zero offset does not raise an exception.

---

## Requirement 6: Python — Round-Trip via `options_for_enemy`

### 1. Spec Summary

**Description:** The full pipeline `options_for_enemy(slug, raw) -> _coerce_and_validate -> _sanitize_zone_geometry_extras` must produce correct, clamped offset values in `result["zone_geometry_extras"][zone]` when given either flat or nested JSON input containing offset keys.

**Constraints:**
- The flat-key double-pass in `options_for_enemy` (the `root_flat` extraction at the end of the function) must also pick up `extra_zone_{zone}_offset_x/y/z` keys via the updated `_EXTRA_ZONE_FLAT_KEY` regex.
- Behavior for zones not in the slug's feature zone list: offset keys for unknown zones are silently ignored.
- The output dict `result["zone_geometry_extras"]` always contains `offset_x`, `offset_y`, `offset_z` for every zone in the slug's feature zone list, defaulting to `0.0` when not specified by the caller.

**Assumptions:** No changes are needed to `options_for_enemy` itself beyond what the regex and field set changes provide. The existing double-pass flat-key logic already covers the new suffix patterns once `_EXTRA_ZONE_FLAT_KEY` is updated.

**Scope:** `options_for_enemy` and `_coerce_and_validate` in `asset_generation/python/src/utils/animated_build_options.py` (via effects of Requirements 1–3).

### 2. Acceptance Criteria

- **AC-6.1:** `options_for_enemy("imp", {"extra_zone_body_offset_x": 1.0})["zone_geometry_extras"]["body"]["offset_x"] == 1.0`.
- **AC-6.2:** `options_for_enemy("imp", {"zone_geometry_extras": {"body": {"offset_y": -1.0}}})["zone_geometry_extras"]["body"]["offset_y"] == -1.0`.
- **AC-6.3:** `options_for_enemy("imp", {"extra_zone_body_offset_z": 5.0})["zone_geometry_extras"]["body"]["offset_z"] == 2.0` (out-of-range value clamped by sanitize).
- **AC-6.4:** `options_for_enemy("imp", {})["zone_geometry_extras"]["body"]["offset_x"] == 0.0` (default when absent).
- **AC-6.5:** `options_for_enemy("slug", {"extra_zone_body_offset_x": 0.5})["zone_geometry_extras"]["body"]["offset_x"] == 0.5` (slug enemy, confirming all slugs work).
- **AC-6.6:** For a slug-type enemy, setting `extra_zone_body_offset_x` does not affect `zone_geometry_extras["head"]["offset_x"]`, which remains `0.0`.

---

## Requirement 7: Frontend — `zoneExtrasPartition.ts` Updates

### 1. Spec Summary

**Description:** `SUFFIX_ORDER` in `zoneExtrasPartition.ts` must be extended to include `"offset_x"`, `"offset_y"`, `"offset_z"` as the final three entries, after `"hex"`. The `suffixRank` function then automatically sorts offset defs after `hex` defs. No changes to `EXTRA_ZONE_PREFIX_RE` are needed (it already matches any suffix after the zone name).

**Constraints:**
- The three entries are appended in the order `"offset_x"`, `"offset_y"`, `"offset_z"` at the end of the `SUFFIX_ORDER` tuple.
- The `SUFFIX_ORDER` type annotation (the `as const` assertion) must continue to include the new values.
- No other changes to the file are required. The `partitionZoneExtraDefs`, `extraZoneFromDefKey`, and `kindOptionsForZone` functions are unaffected.

**Assumptions:** The `suffixRank` function returns the array index of the matched suffix from `SUFFIX_ORDER`, or `99` for unrecognized suffixes. Appending `"offset_x"`, `"offset_y"`, `"offset_z"` to `SUFFIX_ORDER` means they receive ranks after `"hex"` and before any unrecognized suffix (rank 99).

**Scope:** `asset_generation/web/frontend/src/components/Preview/zoneExtrasPartition.ts`.

### 2. Acceptance Criteria

- **AC-7.1:** `SUFFIX_ORDER` contains `"offset_x"`, `"offset_y"`, `"offset_z"` as its last three entries (indices `N-2`, `N-1`, `N` where `N = SUFFIX_ORDER.length - 1`).
- **AC-7.2:** `suffixRank("extra_zone_body_offset_x")` returns a value greater than `suffixRank("extra_zone_body_hex")`.
- **AC-7.3:** `suffixRank("extra_zone_body_offset_x") < 99` (recognized suffix, not falling through to default rank).
- **AC-7.4:** `partitionZoneExtraDefs("imp", defsIncludingOffsets)` places offset defs after the `hex` def in the sorted per-zone list.
- **AC-7.5:** Existing suffix order for all pre-existing suffixes (`"kind"` through `"hex"`) is unchanged.

---

## Requirement 8: Frontend — `ZoneExtraControls.tsx` Disable Logic

### 1. Spec Summary

**Description:** The `rowDisabled` function must treat offset keys as always-enabled: it returns `false` for any `defKey` ending in `_offset_x`, `_offset_y`, or `_offset_z`. Offset controls are never grayed out regardless of the zone's current `kind` value.

**Constraints:**
- A new early-return guard is added to `rowDisabled` before the existing `kind === "none" || kind === "shell"` block: `if (defKey.endsWith("_offset_x") || defKey.endsWith("_offset_y") || defKey.endsWith("_offset_z")) return false;`
- This guard must be placed before any `kind`-dependent logic so that kind=none/shell/spikes/horns/bulbs do not accidentally disable offset rows.
- No other changes to `rowDisabled` are required.
- No changes to the JSX rendering logic are required; offset controls are `type: "float"` which `ControlRow` already handles natively.

**Assumptions:** `ControlRow` renders `type: "float"` controls as numeric sliders/inputs. This was confirmed for spike_size and clustering which share the same type and rendering path. No bespoke rendering for offset fields is needed.

**Scope:** `asset_generation/web/frontend/src/components/Preview/ZoneExtraControls.tsx`.

### 2. Acceptance Criteria

- **AC-8.1:** `rowDisabled("none", "extra_zone_body_offset_x", "uniform")` returns `false`.
- **AC-8.2:** `rowDisabled("none", "extra_zone_body_offset_y", "uniform")` returns `false`.
- **AC-8.3:** `rowDisabled("none", "extra_zone_body_offset_z", "uniform")` returns `false`.
- **AC-8.4:** `rowDisabled("shell", "extra_zone_body_offset_x", "uniform")` returns `false`.
- **AC-8.5:** `rowDisabled("spikes", "extra_zone_body_offset_x", "uniform")` returns `false`.
- **AC-8.6:** `rowDisabled("horns", "extra_zone_head_offset_z", "uniform")` returns `false`.
- **AC-8.7:** Existing disable logic for non-offset keys is unaffected. Example: `rowDisabled("none", "extra_zone_body_spike_count", "uniform")` still returns `true` (spike count disabled for kind=none).
- **AC-8.8:** In the rendered UI (integration), when a zone's `kind` selector is set to `"none"`, the three offset float controls remain at full opacity with pointer-events enabled.

---

## Requirement 9: Non-Functional — Test Coverage

### 1. Spec Summary

**Description:** Automated tests must cover the merge/sanitize/control-def paths and the attach-path vector assertion. Tests must not require a live Blender process; `bpy` must be stubbed.

**Constraints:**
- Primary tests appended to `tests/utils/test_animated_build_options.py` (existing pattern).
- Attach-path tests in a new file `tests/enemies/test_zone_extras_offset_attach.py` using stubs for `bpy`, `create_cone`, `create_sphere`, and `apply_material_to_object` (following the existing stub/mock pattern already used in the Python test suite for Blender-dependent modules).
- Frontend tests added or appended to the existing test file for `zoneExtrasPartition` (if present) covering `SUFFIX_ORDER` extension and `rowDisabled` offset behavior.
- The full CI suite (`timeout 300 ci/scripts/run_tests.sh`) must exit 0.

**Assumptions:** The Python test suite does not yet have a dedicated test file for zone extras attach paths. The Test Designer Agent must establish the bpy stub pattern for this file. The pattern for stubbing bpy already exists in at least one other test file in the Python project.

**Scope:** `tests/utils/test_animated_build_options.py`, `tests/enemies/test_zone_extras_offset_attach.py`, frontend test file for `ZoneExtraControls` or `zoneExtrasPartition`.

### 2. Acceptance Criteria

- **AC-9.1:** At least one test per AC in Requirements 1–6 is present in `tests/utils/test_animated_build_options.py` or a new adjacent file, exercisable via `uv run pytest tests/utils/`.
- **AC-9.2:** `tests/enemies/test_zone_extras_offset_attach.py` exists and contains at least one test asserting that a non-zero `offset_x` shifts the X-component of the placement location for a spike (AC-5.5).
- **AC-9.3:** `tests/enemies/test_zone_extras_offset_attach.py` contains at least one test asserting that `offset_x = 0.0` produces identical placement to calling with no offset field (AC-5.6, identity check).
- **AC-9.4:** A frontend test asserts that `SUFFIX_ORDER` includes `"offset_x"`, `"offset_y"`, `"offset_z"` after `"hex"`.
- **AC-9.5:** A frontend test asserts that `rowDisabled("none", "extra_zone_body_offset_x", "uniform")` returns `false`.
- **AC-9.6:** `timeout 300 ci/scripts/run_tests.sh` exits 0 with all new tests passing.

---

## Requirement 10: Non-Functional — Backward Compatibility

### 1. Spec Summary

**Description:** Existing stored `build_options` JSON that does not contain offset keys must continue to work without modification. The pipeline must not reject or error on older JSON lacking `offset_x/y/z`.

**Constraints:**
- Adding `offset_x/y/z` to `_default_zone_geometry_extras_payload()` guarantees defaults are applied on every merge pass. No migration of stored JSON is required.
- `_sanitize_zone_geometry_extras` must not raise an exception when the input dict for a zone is missing offset keys (handled by `raw.get("offset_x", 0.0)` with default).
- The `_EXTRA_ZONE_FLAT_KEY` regex change is purely additive; it matches new suffixes without removing any previously matched suffixes.
- All existing `pytest` tests must continue to pass without modification.

**Assumptions:** No stored registry JSON files are modified as part of this ticket. GLB exports are regenerated by artists who choose to use the new controls; existing exports remain valid.

**Scope:** All modified files. GLB and registry files are read-only for this ticket.

### 2. Acceptance Criteria

- **AC-10.1:** Running the existing test suite before implementing offset fields (baseline green) and after implementing (with new tests) produces no regressions: all pre-existing tests still pass.
- **AC-10.2:** `options_for_enemy("imp", {})` returns a dict with all expected pre-existing keys intact and `zone_geometry_extras["body"]["offset_x"] == 0.0`.
- **AC-10.3:** `options_for_enemy("imp", {"zone_geometry_extras": {"body": {"kind": "spikes", "spike_count": 8}}})` returns correct spike settings and `offset_x == 0.0`, `offset_y == 0.0`, `offset_z == 0.0` (no crash from missing offset keys).

---

## Risk and Ambiguity Analysis

| Risk | Severity | Mitigation |
|------|----------|------------|
| `_append_head_ellipsoid_extras` uses both the tuple `hc = (hx, hy, hz)` and the scalar variables `hx, hy, hz` directly in inner functions `_head_point` and `_head_bulb_point`. If only `hx/hy/hz` are reassigned but `hc` is not recomputed, `_orient_cone_outward` receives the wrong base center. | High | Spec explicitly requires `hc` to be recomputed after the offset is applied: `hc = (hx, hy, hz)` appears after the three offset lines. Implementer must verify all uses of `hc`, `hx`, `hy`, `hz` in the function body. |
| "shell" kind has no geometry code path in `zone_geometry_extras_attach.py`. Offset applied to a shell zone is computed but has no output effect. | Low | Documented as intentional no-op. When shell is implemented in a future ticket, the offset will work automatically since the center shift is applied unconditionally. |
| The `_EXTRA_ZONE_FLAT_KEY` regex change could accidentally widen to match previously-invalid keys if the alternation group is constructed incorrectly. | Medium | AC-1.3 requires that `"extra_zone_body_offset_w"` is not matched. Test Designer must include negative regex tests. |
| Tests for `zone_geometry_extras_attach.py` require stubbing `bpy`, `Vector`, `create_cone`, `create_sphere`, `apply_material_to_object`, `get_enemy_materials`, `apply_feature_slot_overrides`, `material_for_zone_geometry_extra`, and `placement_prng`. This is a non-trivial stub surface. | Medium | Test Designer Agent must establish the stub pattern carefully. Using `unittest.mock.patch` for module-level imports is the recommended approach. Existing `blender_stubs.py` in the project provides guidance. |
| Frontend: the three offset controls appear at the bottom of each zone's control list, after `hex`. Artists may miss them if the zone section is long. | Low | No UX change required by this spec. The controls appear in the existing collapsible zone `<details>` block and are accessible by scrolling. |
| `options_for_enemy` performs a double-pass flat-key merge (the `root_flat` block). If the regex match gate is not updated, root-level flat offset keys in the raw JSON will be silently dropped. | Medium | AC-6.1 and AC-6.5 catch this: they test flat keys at the root of the raw dict. If the regex is correct, both passes pick them up. |

---

## Axis Reference (for Artists and Implementers)

Blender world-space convention used throughout this codebase (see `_PLACE_WORLD` in `zone_geometry_extras_attach.py`):

| Offset Field | Blender World Axis | Direction |
|---|---|---|
| `offset_x` | +X | Forward / Front of creature |
| `offset_y` | +Y | Right side of creature |
| `offset_z` | +Z | Upward |

A positive `offset_z` on the body zone shifts the entire body extra construct upward. A negative `offset_x` shifts extras toward the back of the creature. These offsets are additive to the ellipsoid center computed during `build_mesh_parts`; they do not interact with facings/placement flags except that the shifted center is used for the normal vector calculation.

---

## Implementation Order (for Implementer)

The following order is recommended to maintain a passing test suite throughout implementation:

1. Add constants `_OFFSET_XYZ_MIN`, `_OFFSET_XYZ_MAX`, `_OFFSET_XYZ_STEP` (Req 1).
2. Add `"offset_x"`, `"offset_y"`, `"offset_z"` to `_default_zone_geometry_extras_payload()` (Req 1).
3. Add to `_ZONE_GEOM_EXTRA_FIELDS` (Req 1).
4. Extend `_EXTRA_ZONE_FLAT_KEY` regex (Req 1).
5. Add float merge branch for `offset_x/y/z` in `_merge_zone_geometry_extras` (Req 2).
6. Add sanitize block for `offset_x/y/z` in `_sanitize_zone_geometry_extras` (Req 3).
7. Add three control defs per zone in `_zone_extra_control_defs` (Req 4).
8. Add `_zone_extra_offset` helper and apply in `_append_body_ellipsoid_extras` and `_append_head_ellipsoid_extras` (Req 5).
9. Extend `SUFFIX_ORDER` in `zoneExtrasPartition.ts` (Req 7).
10. Add early-return guard in `rowDisabled` in `ZoneExtraControls.tsx` (Req 8).
