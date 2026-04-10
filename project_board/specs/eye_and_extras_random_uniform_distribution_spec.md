# Spec: Random vs uniform distribution for eyes and zone extras (M9-16)

## Goal

Add an explicit **distribution mode** (mutually exclusive **uniform** vs **random**) for:

1. **Spider** multi-eye placement when `eye_count > 1`.
2. **Zone geometry extras** (`zone_geometry_extras` / `extra_zone_*`) when `kind` is `spikes`, `bulbs`, or (head) `horns` multi-instance paths.

**Uniform** uses deterministic angular presets (`uniform_shape`: `arc` | `ring`) modulated by **`clustering`** (ticket **15**). **Random** uses `clustered_ellipsoid_angles_bounded` with a **dedicated PRNG** from **`placement_seed`** so layouts are reproducible for fixed JSON without consuming the mesh `rng` stream.

## JSON keys and defaults

| Key | Scope | Type | Values | Default |
|-----|--------|------|--------|---------|
| `eye_distribution` | Spider | string | `uniform`, `random` | `uniform` |
| `eye_uniform_shape` | Spider | string | `arc` (only option today) | `arc` |
| `placement_seed` | All animated slugs (merge) | int | any int (clamped modulo 2³¹ for `random.Random`) | `0` |
| `distribution` | Each `zone_geometry_extras` zone | string | `uniform`, `random` | `uniform` |
| `uniform_shape` | Each zone | string | `arc`, `ring` | `arc` |

### Flat API keys (extras)

- `extra_zone_<zone>_distribution`
- `extra_zone_<zone>_uniform_shape`

Merge/sanitize follows existing `zone_geometry_extras` rules in `animated_build_options.py`. Unknown distribution/shape values fall back to defaults. **Horns:** `uniform_shape` is forced to **`arc`** in sanitize (lateral pair layout).

## Semantics

- **Uniform + arc / ring:** Uses `uniform_arc_angles` / `uniform_ring_angles` with the zone’s clustering; body/head spikes and bulbs iterate with facing retries and small phase jitter per attempt.
- **Random:** Uses `placement_prng(model)` → `random.Random(placement_seed % 2**31)` for ellipsoid angle draws (body/head spikes & bulbs). Spider eye random path uses the same `placement_prng(self)`.
- **Single eye (`eye_count <= 1`):** Distribution/clustering/uniform-pattern controls are a **no-op** in placement; the asset editor **dims** spider `eye_distribution`, `eye_uniform_shape`, and `eye_clustering` when `eye_count <= 1`, and dims `eye_uniform_shape` when mode is **random**.

## Frontend

- API may set `"segmented": true` on `select_str` defs for distribution modes; the editor renders a **two-button segmented** control (not a lone checkbox).
- Extras pane: `extra_zone_*_distribution` disabled for `kind` `none` / `shell`; `extra_zone_*_uniform_shape` disabled for `none` / `shell`, for **random** distribution, and for **horns** (pattern fixed to arc server-side).

## Determinism

For fixed `build_options` (including `placement_seed`, `distribution`, `uniform_shape`, `clustering`), exports are stable. **Note:** Random placement does **not** use `model.rng` for these draws; it uses **`placement_seed`** so mesh variance from `rng` does not desync multi-instance extras/eyes.

## Related

- Ticket **15:** `eye_clustering` and per-zone `clustering`.
- Ticket **11:** zone extras pipeline and facings.
