# Checkpoint Log: 17_zone_extras_offset_xyz_controls
Run: run-2026-04-11-autopilot

## Stage History

- PLANNING: Started 2026-04-11T00:00:00Z — Autopilot Orchestrator
- SPECIFICATION: Started 2026-04-11 — Spec Agent

## Checkpoint Entries

### [17] SPECIFICATION — coordinate space confirmation

**Would have asked:** The planner assumed Blender world-space (Z-up, X=front, Y=right) for offset application. Should this be confirmed as the authoritative frame rather than a per-zone-ellipsoid local space?

**Assumption made:** Confirmed world-space. The existing `_PLACE_WORLD` dict in `zone_geometry_extras_attach.py` documents `place_top = (0,0,1)`, `place_front = (1,0,0)`, `place_right = (0,1,0)` — all in Blender world-space. The `cx`, `cy`, `cz` parameters to `_ellipsoid_point_at` are already world-space coordinates. Applying `offset_x/y/z` directly to those coordinates is world-space translation and is consistent with all existing placement logic. No alternative coordinate frame is used anywhere in the codebase.

**Confidence:** High

---

### [17] SPECIFICATION — numeric range and step final values

**Would have asked:** Should the range be the planner's suggested -2.0..+2.0 with step 0.05, or should it be scaled to the bounding ellipsoid dimensions?

**Assumption made:** Fixed symmetric range -2.0..+2.0 with step 0.05, default 0.0. Rationale: The body ref scale (geometric mean of semi-axes) is typically 0.5–2.0 for current enemies. A -2.0..+2.0 range provides up to two full body-radius shifts in any direction, which is artistically sufficient without placing extras completely detached from the body. Step 0.05 matches the existing step used by spike_size, bulb_size, and eye_clustering controls. Ellipsoid-relative scaling would require knowing radii at spec-definition time, which is not available to the API metadata layer.

**Confidence:** High

---

### [17] SPECIFICATION — visibility when kind=none or kind=shell

**Would have asked:** Should offset controls be always visible (no-op when kind=none/shell) or hidden/disabled when kind=none?

**Assumption made:** Always visible, always enabled (not grayed out), regardless of kind. Rationale: (1) Offset controls are independent of kind — they translate the ellipsoid center before any extras are placed, so they remain meaningful even for future kind implementations. (2) The existing pattern in rowDisabled already keeps _finish and _hex always enabled as structural properties; offset is in the same category. (3) Disabling offsets for kind=none would require un-disabling them on kind change, creating more UI state to manage. (4) When kind=none or kind=shell, offsets are stored but have no visual effect — this matches exactly how place_* flags behave for kind=none (they are stored but no geometry is generated to filter). The no-op nature must be documented in the spec for artists.

**Confidence:** High

---

### [17] SPECIFICATION — flat vs nested key schema confirmation

**Would have asked:** Should both flat and nested representations be accepted, or flat-only?

**Assumption made:** Confirmed: both representations accepted, canonical storage is nested. Flat keys `extra_zone_{zone}_offset_x`, `extra_zone_{zone}_offset_y`, `extra_zone_{zone}_offset_z` merge into `zone_geometry_extras[zone].offset_x/y/z`. This follows the identical pattern of spike_count, spike_size, clustering, and all other zone extra fields, including the double-pass flat-key merge in `options_for_enemy`.

**Confidence:** High

---

### [17] SPECIFICATION — apply offset before or after ellipsoid center lookup

**Would have asked:** Should the offset be applied to cx/cy/cz at the top of `_append_body_ellipsoid_extras` and `_append_head_ellipsoid_extras`, or should it be applied at the call site in `append_animated_enemy_zone_extras`?

**Assumption made:** Apply at the top of each `_append_*_ellipsoid_extras` function. This keeps the offset application colocated with the coordinate usage (cx/cy/cz are local to each function and used immediately for ellipsoid_point_at and ellipsoid_normal). It does not change the public signature of `append_animated_enemy_zone_extras` and does not affect the center coordinates stored on the model. The ellipsoid normal computation must also use the offset center so that normals are computed relative to the shifted ellipsoid, not the original.

**Confidence:** High
