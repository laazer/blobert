# Spec: Enemy body-part geometry extras (M9-EBPE)

## Goal

Standard **geometry overlays** keyed by the same **material zones** as `features` (body, head, limbs, joints, extra), with per-zone **finish** / **hex** overrides for extra sub-meshes, merged into `animated_build_options` like existing feature materials.

## JSON shape

### Top-level key: `zone_geometry_extras`

Map **zone name** → **extra payload** (one object per zone). Valid zone names are exactly those in `_FEATURE_ZONES_BY_SLUG` for the active slug (unknown zones in input are ignored).

### Payload fields (all zones)

| Field | Type | Notes |
|-------|------|--------|
| `kind` | string | `none`, `shell`, `spikes`, `horns`, `bulbs` |
| `finish` | string | Same set as feature finishes (`default`, `glossy`, `matte`, `metallic`, `gel`) |
| `hex` | string | RRGGBB after sanitize (empty = inherit zone appearance from `features[zone]` when applying materials) |
| `spike_shape` | string | `cone` or `pyramid` (used when `kind` is `spikes` or `horns`) |
| `spike_count` | int | Clamped **1–24**; used when `kind` is `spikes` |
| `bulb_count` | int | Clamped **1–16**; used when `kind` is `bulbs` |
| `shell_scale` | float | Clamped **1.01–1.5**, step 0.01, default **1.08**; used when `kind` is `shell`. Controls how much the shell overscales the zone ellipsoid semi-axes. |

### Per-kind semantics

- **`none`:** No geometry; other fields ignored for generation.
- **`shell`:** Scaled-ellipsoid overlay. A single `create_sphere` call with `location=(cx, cy, cz)` and `scale=(a * shell_scale, b * shell_scale, h * shell_scale)`, where `(cx, cy, cz)` is the zone center (after `offset_xyz` is applied), and `(a, b, h)` are the zone ellipsoid semi-axes. `shell_scale` is read from the spec via `_zone_extra_scale(spec, "shell_scale", default=1.08, lo=1.01, hi=1.5)`. Material, `finish`, and `hex` are applied identically to other extra kinds. This produces a carapace-like thin overlay wrapping the zone ellipsoid. Applies to **both body and head** zones wherever zone geometry is populated (i.e. wherever `_zone_geom_body_center`/`_zone_geom_body_radii` or `_zone_geom_head_center`/`_zone_geom_head_radii` are set on the model). For any enemy that does not populate those attributes, the `elif kind == "shell":` branch is reached but the outer guard in `append_animated_enemy_zone_extras` short-circuits before calling `_append_body_ellipsoid_extras` / `_append_head_ellipsoid_extras`.
- **`spikes`:** Cones or square pyramids (`spike_shape`) distributed on the zone mesh; `spike_count` drives count.
- **`horns`:** Dedicated kind; **placement is head zone only**. If `horns` is set on a non-head zone, validation **coerces `kind` to `none`** for that zone. Implements two horn primitives using `spike_shape` (count fixed at 2 internally).
- **`bulbs`:** Small spherical protrusions; `bulb_count` drives count.

### Spike tip offset geometry (v2 — protrusion fix)

The tip location for all spike/horn cone primitives is:

```
tip = Vector(surface_point) + nrm * depth * 1.0
```

where `depth` is the cone depth and `nrm` is the outward ellipsoid surface normal at `surface_point`. This places the cone apex at `surface_point + depth` outward, so the cone base circle (at `tip - depth * nrm` in local cone space) sits **flush on the ellipsoid surface**. No part of the spike cone is embedded in the body mesh.

**Prior behavior (v1):** The factor was `0.55`, which placed the base circle at `surface_point - 0.45 * depth` — 45% of depth below the surface. Spikes appeared partially buried.

**All five call sites must be updated:**

| Line (pre-fix) | Function | Mode |
|---|---|---|
| 291 | `_append_body_ellipsoid_extras` | body spikes, uniform |
| 322 | `_append_body_ellipsoid_extras` | body spikes, random |
| 444 | `_append_head_ellipsoid_extras` | head horns |
| 506 | `_append_head_ellipsoid_extras` | head spikes, uniform |
| 536 | `_append_head_ellipsoid_extras` | head spikes, random |

Source: `asset_generation/python/src/enemies/zone_geometry_extras_attach.py`. Lines are as of the commit at ticket creation; implementer must grep for `depth * 0.55` to confirm all occurrences.

### Exclusivity (v1)

At most **one** `kind` per zone — enforced structurally (single `kind` field). There is no separate "stack" of extras.

### Merge / sanitize order

1. Start from defaults: every allowed zone for the slug has `kind: none` and default numeric/string fields (including `shell_scale: 1.08`).
2. Merge nested `zone_geometry_extras` from the slug object (e.g. `{ "slug": { "zone_geometry_extras": { ... } } }`) or from flat root when not using nested slug envelope.
3. Merge **flat API keys** (see below); later sources overwrite earlier ones for the same field.
4. Run validation: unknown `kind` → `none`; invalid finish → `default`; clamp counts; **horns off-head → `none`**; `shell_scale` clamped to `[1.01, 1.5]`.
5. `shell` on a zone whose enemy does not populate zone center/radii is **valid in payload** (round-trips) but the geometry attachment is a no-op because the outer guard never invokes `_append_body/head_ellipsoid_extras` for that enemy.

### Flat API keys (editor / `animated_build_controls_for_api`)

Pattern:

`extra_zone_<zone>_<suffix>`

Where `<zone>` is one of `body`, `head`, `limbs`, `joints`, `extra`.

Suffixes:

- `kind` — `select_str` with options `none`, `shell`, `spikes`, `horns`, `bulbs`
- `spike_shape` — `cone`, `pyramid`
- `spike_count` — int (min/max aligned with spec)
- `bulb_count` — int
- `finish` — same as `feat_*_finish`
- `hex` — same as `feat_*_hex`
- `shell_scale` — float, min 1.01, max 1.5, step 0.01, default 1.08

Flat keys are **ignored** when the slug has no such zone (e.g. `extra_zone_joints_*` on `slug`).

## `shell_scale` field specification

| Attribute | Value |
|---|---|
| Field name | `shell_scale` |
| Type | float |
| Default | 1.08 |
| Min | 1.01 |
| Max | 1.5 |
| Step (UI) | 0.01 |
| Sanitize | Clamped to `[1.01, 1.5]` in `_sanitize_zone_geometry_extras`; non-numeric → default |
| Flat key suffix | `shell_scale` |
| Regex pattern | Must be added to `_EXTRA_ZONE_FLAT_KEY` alternation group |
| Frozenset | Must be added to `_ZONE_GEOM_EXTRA_FIELDS` |
| Default payload | Must appear in `_default_zone_geometry_extras_payload()` return dict |
| Control def | Added in `_zone_extra_control_defs(slug)` as `float` type control |

### `shell_scale` control def shape

```
{
    "key": "extra_zone_<zone>_shell_scale",
    "label": "<ZoneLabel> shell scale",
    "type": "float",
    "min": 1.01,
    "max": 1.5,
    "step": 0.01,
    "default": 1.08,
}
```

One entry per zone, following the same per-zone loop pattern as `spike_size` and `bulb_size` control defs in `_zone_extra_control_defs`.

## Capability matrix (v2)

| Slug | Zones receiving **real** spike/bulb geometry | `shell` | `horns` |
|------|-----------------------------------------------|---------|---------|
| `slug` | `body`, `head` | ellipsoid overlay (body + head) | head only |
| `imp`, `carapace_husk`, `spider`, `claw_crawler`, `spitter` | none in v1 (merge/API only) | no-op (zone center/radii not populated) | head only (validation); no horn mesh until wired |

**Note on shell for non-slug enemies:** The `shell` kind is valid in payload and round-trips for all enemies. For enemies that do not expose `_zone_geom_body_center`/`_zone_geom_body_radii`/`_zone_geom_head_center`/`_zone_geom_head_radii`, the geometry attachment is skipped by the guard in `append_animated_enemy_zone_extras`. No special per-slug guard is needed in `_append_body_ellipsoid_extras` or `_append_head_ellipsoid_extras`. If a future enemy populates those attributes, shell geometry will activate automatically.

**Reference golden path:** `slug` with `zone_geometry_extras.body` spikes and bulbs — options parse + merge tests; generator attaches geometry for slug **body** and **head** where kind is spikes/horns/bulbs/shell.

## Blender / material wiring

- Extra meshes are appended to the procedural part list **before** `finalize()` join, or created and parented consistently with existing primitives.
- Material resolution: base palette from the enemy theme for that **zone**, then apply `finish` / `hex` from the extra payload (same pipeline family as `_material_for_finish_hex` / feature overrides).
- Shell mesh uses the same material resolution as spikes and bulbs: `material_for_zone_geometry_extra("body"/"head", slot_mats, features, finish, hex)`.

## Files modified by this spec

| File | Changes |
|---|---|
| `asset_generation/python/src/utils/animated_build_options.py` | Add `_SHELL_SCALE_MIN = 1.01`, `_SHELL_SCALE_MAX = 1.5`; add `shell_scale: 1.08` to `_default_zone_geometry_extras_payload()`; add `"shell_scale"` to `_ZONE_GEOM_EXTRA_FIELDS`; add `shell_scale` to `_EXTRA_ZONE_FLAT_KEY` regex alternation; add `shell_scale` float control in `_zone_extra_control_defs`; clamp `shell_scale` in `_sanitize_zone_geometry_extras` |
| `asset_generation/python/src/enemies/zone_geometry_extras_attach.py` | Add `elif kind == "shell":` branch in `_append_body_ellipsoid_extras` and `_append_head_ellipsoid_extras`; change factor `0.55` → `1.0` at all 5 call sites |

## Tests (obligations)

- Merge nested + flat `zone_geometry_extras` with `features` unchanged.
- Validation: horns on `body` for slug → `kind` becomes `none` for that zone.
- Clamping: `spike_count`, `bulb_count` extremes.
- Golden path: `options_for_enemy("slug", {...})` includes expected `zone_geometry_extras.body.kind` and counts after merge.
- `test_shell_body_appends_sphere`: kind=shell on body zone → `create_sphere` called once, one part appended; location equals zone center (offset 0), scale equals `(a * 1.08, b * 1.08, h * 1.08)` for default shell_scale.
- `test_shell_head_appends_sphere`: kind=shell on head zone → same assertion for head semi-axes.
- `test_shell_none_is_noop`: kind=none → no sphere called for shell (existing behavior preserved).
- `test_spike_tip_protrudes_above_surface`: for a unit sphere zone (a=b=h=1), place one spike with factor=1.0; extract the `location` passed to `create_cone`; verify the location is strictly farther from zone center than the surface point along the normal direction. Concretely: `dot(tip - center, nrm) > dot(surface_point - center, nrm)`.
- `test_shell_scale_field_round_trips`: `shell_scale` default present in `_default_zone_geometry_extras_payload()` output and equals 1.08; flat key `extra_zone_body_shell_scale` is accepted and round-trips through `options_for_enemy("slug", {"extra_zone_body_shell_scale": 1.2})` with the output `zone_geometry_extras.body.shell_scale == 1.2`.
- `test_shell_scale_clamping`: values outside `[1.01, 1.5]` are clamped; non-numeric input falls back to 1.08.

## AC traceability

| AC | Evidence |
|----|----------|
| Written spec | This file |
| Python API controls | `_zone_extra_control_defs` + pytest API key tests |
| Procedural attachment | `zone_geometry_extras_attach` + slug `build_mesh_parts` hook |
| Shell geometry | `_append_body_ellipsoid_extras` / `_append_head_ellipsoid_extras` `elif kind == "shell":` branch |
| Spike protrusion fix | All 5 `depth * 0.55` → `depth * 1.0` in `zone_geometry_extras_attach.py` |
| pytest | `test_animated_build_options.py` + extras-focused cases (shell + spike protrusion) |
| Full CI | `timeout 300 ci/scripts/run_tests.sh` |
