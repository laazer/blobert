# Checkpoint Log: 17_zone_extras_offset_xyz_controls
Run: run-2026-04-11-planning
Stage: PLANNING → SPECIFICATION

## Stage History

- PLANNING: Planner Agent 2026-04-11

## Checkpoint Entries

### [17] PLANNING — offset axis space choice

**Would have asked:** Should offset X/Y/Z apply in local zone-ellipsoid center space (same axes used by `_ellipsoid_point_at` which uses Blender world space: X=front, Y=right, Z=up), or in a separate normalized or surface-normal-relative space?

**Assumption made:** Offsets are applied in Blender world space, as a simple translation of the ellipsoid center coordinates (cx, cy, cz) before extras are placed. This is the most conservative, predictable choice: it matches the existing axes documented in the place_* facing comments ("World axes (Blender Z-up)"), requires no coordinate-system conversion, and lets artists reason about X/Y/Z from the Blender world perspective. The spec agent must confirm and document this.

**Confidence:** Medium

---

### [17] PLANNING — offset range / step values

**Would have asked:** What numeric range and step should the float controls use? The ticket mentions "min, max, step" should be defined in spec. Should ranges be symmetric (e.g. -2.0..2.0) or relative to bounding ellipsoid?

**Assumption made:** Use a fixed symmetric range: -2.0 to +2.0 with step 0.05, default 0.0. This is consistent with spike_size/bulb_size scale conventions in this codebase (ref scale ~1.0) and provides practical artist-facing control. The Spec Agent must document this and may adjust.

**Confidence:** Medium

---

### [17] PLANNING — shell kind behavior for offsets

**Would have asked:** The ticket open question asks whether shell (kind="shell") should share the same offset triple. Shell extras are not yet implemented in `zone_geometry_extras_attach.py` (no code path for "shell"). Should offset keys still be present for shell zones as no-ops?

**Assumption made:** Offset keys are always present for all zones regardless of kind. When kind="none" or kind="shell" (which produces no geometry currently), the offsets exist but have no effect. This matches the ticket suggestion: "always visible but documented as no-op when kind===none". The Spec Agent must pick one behavior and document it explicitly.

**Confidence:** High

---

### [17] PLANNING — flat vs nested key schema

**Would have asked:** Should offsets be flat keys (`extra_zone_{zone}_offset_x`) or nested fields under `zone_geometry_extras[zone]`? The ticket names both options.

**Assumption made:** Both flat and nested representations should work (like all other zone extra fields). The canonical internal storage is nested (inside `build_options["zone_geometry_extras"][zone]`). Flat keys `extra_zone_{zone}_offset_x`, `extra_zone_{zone}_offset_y`, `extra_zone_{zone}_offset_z` are accepted via the merge path and stored as `offset_x`, `offset_y`, `offset_z` in the zone dict. This is the exact pattern used by spike_count, spike_size, clustering, etc.

**Confidence:** High

---

### [17] PLANNING — agent assignment for Python + frontend

**Would have asked:** Should the Python pipeline work and the TypeScript frontend work be assigned to separate agents or one generalist?

**Assumption made:** Two separate agents: (1) Python pipeline backend work goes to Implementation Backend Agent (Python), (2) Frontend TypeScript work goes to Implementation Frontend Agent. The frontend change is minimal — extend SUFFIX_ORDER and the regex in zoneExtrasPartition.ts to include offset_x/y/z suffixes, and add offset controls to rowDisabled logic in ZoneExtraControls.tsx. Python is the primary complexity. This follows the ticket's own four-step plan.

**Confidence:** High
