# Spec: Eye and extras placement clustering (M9-15)

## Goal

Add a **clustering** control (0 = spread, 1 = tight pack) for:

1. **Spider eyes** when `eye_count > 1` (single eye: clustering is a no-op in placement).
2. **Zone geometry extras** when `kind` is `spikes`, `horns`, or `bulbs` — modulates how tightly multiple instances group on the allowed surface (same facings / placement flags as ticket 11).

Ticket **16** adds explicit **random vs uniform** distribution mode; this spec defines clustering for the **current** stochastic placement path. When 16 lands, **uniform** presets will use the same `clustering` value to modulate angular spread around each preset’s focal region.

## Parameters

| Key | Scope | Type | Range | Default |
|-----|--------|------|-------|---------|
| `eye_clustering` | Spider only | float | 0.0–1.0 | 0.5 |
| `clustering` | Each `zone_geometry_extras` zone | float | 0.0–1.0 | 0.5 |

### Flat API keys (extras)

`extra_zone_<zone>_clustering` — merged into `zone_geometry_extras[zone].clustering` like other `extra_zone_*` suffixes.

### Nested JSON

Under `zone_geometry_extras.<zone>.clustering` (float).

Merge order matches existing `zone_geometry_extras` rules: defaults → nested map → flat keys (later wins).

## Semantics

- **0.0:** Legacy breadth — eyes use full lateral / arc span; extras sample uniformly over the same angular domains as pre-clustering (body: full ellipsoid bands; head spikes/bulbs: their historical phi windows).
- **1.0:** Samples concentrate near the **center** of each domain (eyes bunch toward the frontal meridian; extras sample near the domain centroid in `(theta, phi)` space).
- **Horns (count = 2):** Lateral separation scales down as clustering increases (no RNG).

## Determinism

For fixed `build_options` (including `mesh` / `features` / `zone_geometry_extras`) and fixed procedural RNG seed, output is stable. Clustering does not introduce extra RNG streams; it only reshapes how existing draws are mapped to angles.

## Editor

Controls are exposed via `animated_build_controls_for_api()` as `float` rows (`GET /api/meta`), same metadata pattern as other build floats. Frontend **Extras** tab shows per-zone clustering; spider **Build** tab shows `eye_clustering`.

## Tests (obligations)

- `placement_clustering` unit tests: spread vs tight variance; bounds.
- `options_for_enemy` merge/sanitize for `eye_clustering` and `extra_zone_*_clustering`.
- Spider `_eye_dirs` regression: high clustering reduces lateral spread for `eye_count >= 3` (and pair eyes).

## Interaction with ticket 16 (forward)

- **Random mode (16):** Clustering continues to modulate RNG-backed angular sampling as documented above.
- **Uniform mode (16):** Clustering modulates how wide each deterministic preset spreads around its focal parameterization; exact preset catalog is owned by 16.
