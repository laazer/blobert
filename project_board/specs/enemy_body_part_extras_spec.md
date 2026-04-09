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

### Per-kind semantics

- **`none`:** No geometry; other fields ignored for generation.
- **`shell`:** **v1 stub:** no additional geometry; options round-trip and appear in API. Supported topologies (e.g. carapace) may gain geometry in a later phase; **slug / soft bodies:** always no-op.
- **`spikes`:** Cones or square pyramids (`spike_shape`) distributed on the zone mesh; `spike_count` drives count.
- **`horns`:** Dedicated kind; **placement is head zone only**. If `horns` is set on a non-head zone, validation **coerces `kind` to `none`** for that zone. Implements two horn primitives using `spike_shape` (count fixed at 2 internally).
- **`bulbs`:** Small spherical protrusions; `bulb_count` drives count.

### Exclusivity (v1)

At most **one** `kind` per zone — enforced structurally (single `kind` field). There is no separate “stack” of extras.

### Merge / sanitize order

1. Start from defaults: every allowed zone for the slug has `kind: none` and default numeric/string fields.
2. Merge nested `zone_geometry_extras` from the slug object (e.g. `{ "slug": { "zone_geometry_extras": { ... } } }`) or from flat root when not using nested slug envelope.
3. Merge **flat API keys** (see below); later sources overwrite earlier ones for the same field.
4. Run validation: unknown `kind` → `none`; invalid finish → `default`; clamp counts; **horns off-head → `none`**.
5. `shell` on unsupported mesh remains **`kind: shell`** for round-trip but generator performs **no-op** geometry.

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

Flat keys are **ignored** when the slug has no such zone (e.g. `extra_zone_joints_*` on `slug`).

## Capability matrix (v1)

| Slug | Zones receiving **real** spike/bulb geometry | `shell` | `horns` |
|------|-----------------------------------------------|---------|---------|
| `slug` | `body`, `head` | no-op | head only |
| `imp`, `carapace_husk`, `spider`, `claw_crawler`, `spitter` | none in v1 (merge/API only) | no-op | head only (validation); no horn mesh until wired |

**Reference golden path:** `slug` with `zone_geometry_extras.body` spikes and bulbs — options parse + merge tests; generator attaches geometry for slug **body** and **head** where kind is spikes/horns/bulbs.

## Blender / material wiring

- Extra meshes are appended to the procedural part list **before** `finalize()` join, or created and parented consistently with existing primitives.
- Material resolution: base palette from the enemy theme for that **zone**, then apply `finish` / `hex` from the extra payload (same pipeline family as `_material_for_finish_hex` / feature overrides).

## Tests (obligations)

- Merge nested + flat `zone_geometry_extras` with `features` unchanged.
- Validation: horns on `body` for slug → `kind` becomes `none` for that zone.
- Clamping: `spike_count`, `bulb_count` extremes.
- Golden path: `options_for_enemy("slug", {...})` includes expected `zone_geometry_extras.body.kind` and counts after merge.

## AC traceability

| AC | Evidence |
|----|----------|
| Written spec | This file |
| Python API controls | `_zone_extra_control_defs` + pytest API key tests |
| Procedural attachment | `zone_geometry_extras_attach` + slug `build_mesh_parts` hook |
| pytest | `test_animated_build_options.py` + extras-focused cases |
| Full CI | `timeout 300 ci/scripts/run_tests.sh` |
