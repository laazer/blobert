# TICKET: 17_zone_extras_offset_xyz_controls

Title: Zone geometry extras — per-zone X / Y / Z offset controls (Build-style floats)
Project: blobert
Created By: Human
Created On: 2026-04-11

---

## Description

Add **three numeric controls per feature zone** (body, head, limbs, joints, extra — whatever `_feature_zones(slug)` returns) to **translate** that zone's procedural geometry extras (shell, spikes, horns, bulbs, etc.) in **local/world space as defined in spec** after placement and facings (`place_*`) are resolved.

UX should match **Build** tuning: `type: "float"` metadata from `animated_build_options` / `GET /api/meta`, with **min**, **max**, **step**, and **default 0** (or neutral center), rendered by the same control row machinery as mesh sliders (`BuildControls.tsx` / Extras pane).

**Suggested keys** (finalize in spec / implementation):

- Flat: `extra_zone_{zone}_offset_x`, `extra_zone_{zone}_offset_y`, `extra_zone_{zone}_offset_z`
- Nested: fields on each entry under `build_options["zone_geometry_extras"][zone]` alongside existing `kind`, `spike_*`, `bulb_*`, `clustering`, `place_*`, `finish`, `hex`.

Update **`_EXTRA_ZONE_FLAT_KEY`**, **`_ZONE_GEOM_EXTRA_FIELDS`**, **`_default_zone_geometry_extras_payload()`**, **`_merge_zone_geometry_extras`**, **`_sanitize_zone_geometry_extras`**, and **`_zone_extra_control_defs()`** in `asset_generation/python/src/utils/animated_build_options.py` so merge + sanitize + API defs stay consistent.

Apply offsets in **`asset_generation/python/src/enemies/zone_geometry_extras_attach.py`** (or the single choke point that positions extra geometry for a zone) so preview and export match.

---

## Acceptance Criteria

- Every zone that supports `zone_geometry_extras` exposes **offset X/Y/Z** in the meta-driven UI when extras are enabled (or always visible but documented as no-op when `kind === "none"` — pick one behavior in spec and stick to it).
- Changing offsets visibly moves the **entire** extra construct for that zone (not individual spike instances unless spec explicitly expands scope).
- Flat and nested JSON round-trip; invalid values clamp or reset like other float extras.
- `pytest` for merge/sanitize and at least one attach-path test or vector assertion that non-zero offset shifts placement.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

---

## Dependencies

- None beyond existing zone extras pipeline (`zone_geometry_extras`, ticket **11** if still tracking umbrella work).

---

## Open questions (spec)

- **Space:** Offset in **parent/body local** vs **world** vs **along surface normal** — pick one primary model; document for artists.
- **Shell vs scattered extras:** Same offset triple for all kinds, or shell-only exceptions if topology differs.

---

## Execution plan

1. Spec: axis meaning, ranges (e.g. symmetric −1..1 or scaled to bounding ellipsoid), default.
2. Python: defaults, regex/fields, control defs, attach math.
3. Frontend: auto-render new float defs on **Extras** (no bespoke hacks unless `select_str` / grouping requires it).
4. Tests + visual spot-check in editor preview.

---

## Planning Output

### Task Decomposition

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Write formal spec: offset axis space, numeric ranges/step, JSON key schema, behavior for kind=none/shell, attach-point math contract | Spec Agent | This ticket; `animated_build_options.py` (constants pattern, `_ZONE_GEOM_EXTRA_FIELDS`, `_ZONE_GEOM_EXTRA_PLACE_KEYS`); `zone_geometry_extras_attach.py` (`_ellipsoid_point_at`, `_append_body_ellipsoid_extras`, `_append_head_ellipsoid_extras` — cx/cy/cz are Blender world-space coords, Z-up); existing `_EXTRA_ZONE_FLAT_KEY` regex pattern | Spec file at `project_board/specs/zone_extras_offset_xyz_controls_spec.md` covering: (a) Blender world-space X/Y/Z offset interpretation, (b) range −2.0..+2.0 step 0.05 default 0.0 or spec-preferred alternative, (c) key names `offset_x/y/z` nested + flat `extra_zone_{zone}_offset_x/y/z`, (d) always-visible behavior with no-op note when kind=none/shell, (e) attach-math contract: cx += offset_x before all placement calls | None | Spec file exists; all open questions in ticket resolved with rationale; attach math contract is precise enough for test-design to write vector assertions | Assumption: world-space Blender axes (X=front, Y=right, Z=up) is the correct coordinate frame. If the spec agent determines surface-normal offset is preferable, the Python implementation task will be more complex. Shell no-op is documented assumption but spec may override. |
| 2 | Design and write tests (primary): merge/sanitize unit tests for new offset fields; API-def coverage; attach-path vector assertion (offset shifts cx before placement) | Test Designer Agent | Spec from Task 1; `tests/utils/test_animated_build_options.py` (existing patterns); `zone_geometry_extras_attach.py` (attach function signatures) | New test cases appended to `tests/utils/test_animated_build_options.py`; new test file `tests/enemies/test_zone_extras_offset_attach.py` with at least one vector assertion confirming non-zero offset_x shifts placement | Task 1 | Tests cover: flat key merge, nested merge, clamp, invalid reset, API def has type=float+step, offset_x=1.0 shifts cx by 1.0 in attach | Risk: `zone_geometry_extras_attach.py` uses `bpy` — tests must stub or mock bpy to avoid Blender dependency. Existing test pattern for attach path may not exist yet; if none exists, Test Designer must establish the pattern. |
| 3 | Write adversarial/edge-case tests (test-break): zero-offset no-op, extreme clamp, invalid float ignored, no cross-contamination between zones, offset independent of kind | Test Breaker Agent | Spec from Task 1; primary tests from Task 2 | Additional adversarial test cases appended to existing test files, each marked with `# ADVERSARIAL` comment | Task 2 | Tests include: offset 0.0 produces same cx as no-offset call; offset clamped at boundary equals max/min; string "abc" as offset_x is ignored (field stays 0.0); offset_x on body zone does not affect head zone cx | Risk: If attach-path stubs are complex, adversarial tests may need to reuse fixtures from primary tests. |
| 4 | Implement Python backend: add `offset_x/y/z` to constants, regex, fields, default payload, merge, sanitize, control defs, and apply offsets in attach functions | Implementation Backend Agent (Python) | Spec from Task 1; failing tests from Tasks 2–3; `animated_build_options.py`; `zone_geometry_extras_attach.py` | Updated `animated_build_options.py` with: new constants (`_OFFSET_XYZ_MIN=-2.0`, `_OFFSET_XYZ_MAX=2.0`, `_OFFSET_XYZ_STEP=0.05`), extended `_EXTRA_ZONE_FLAT_KEY` regex, `offset_x/y/z` in `_ZONE_GEOM_EXTRA_FIELDS`, `_default_zone_geometry_extras_payload`, merge float branch, sanitize clamp, and `_zone_extra_control_defs` three new entries. Updated `zone_geometry_extras_attach.py` with: helper `_zone_extra_offset(spec, axis)` returning clamped float; cx/cy/cz offset applied at the top of `_append_body_ellipsoid_extras` and `_append_head_ellipsoid_extras` before any placement call | Task 3 | `uv run pytest tests/utils/test_animated_build_options.py tests/enemies/test_zone_extras_offset_attach.py -q` exits 0; `task hooks:py-review` clean; no bare dict typing violations | Risk: `_EXTRA_ZONE_FLAT_KEY` regex change must be backward-compatible (no existing keys broken). The attach functions receive cx/cy/cz as positional floats — must thread offset through cleanly without signature breakage of the public `append_animated_enemy_zone_extras` function. |
| 5 | Implement frontend: extend `SUFFIX_ORDER` and regex in `zoneExtrasPartition.ts` to recognize `offset_x/y/z` suffixes; add disable logic to `ZoneExtraControls.tsx` for offset rows (enabled only when kind != none); no bespoke rendering needed — `ControlRow` handles float type natively | Implementation Frontend Agent | Spec from Task 1; `zoneExtrasPartition.ts` (`SUFFIX_ORDER`, `EXTRA_ZONE_PREFIX_RE`); `ZoneExtraControls.tsx` (`rowDisabled` function) | Updated `zoneExtrasPartition.ts` with `"offset_x"`, `"offset_y"`, `"offset_z"` added to `SUFFIX_ORDER` after `hex`; updated `rowDisabled` in `ZoneExtraControls.tsx` to return `false` for `offset_x/y/z` keys (always enabled) per spec; `zoneExtrasPartition.test.ts` updated with offset suffix round-trip assertion | Task 1 | `cd asset_generation/web/frontend && npm test` exits 0; offset float controls appear in Extras pane when slug is selected; ControlRow renders float type automatically | Risk: Spec says offsets are always enabled regardless of kind (never grayed out). rowDisabled must return false for offset keys unconditionally. |
| 6 | Run full test suite, fix any integration issues, verify CI passes | Implementation Backend Agent (Python) (or Generalist if cross-domain fixes needed) | All code from Tasks 4–5; `ci/scripts/run_tests.sh` | `timeout 300 ci/scripts/run_tests.sh` exits 0; no regressions in existing zone-extras tests | Tasks 4, 5 | Exit code 0; no failing tests; `task hooks:python` clean | Risk: Frontend test runner and Python test runner are separate — both must pass. The CI script must be checked to confirm it runs both. |

### Notes on Agent Assignment

- Tasks 1 (spec), 2–3 (test design/break), 4 (Python backend implementation), 5 (frontend TypeScript), 6 (integration gate) each map to the workflow stage sequence: SPECIFICATION → TEST_DESIGN → TEST_BREAK → IMPLEMENTATION_BACKEND → IMPLEMENTATION_FRONTEND → INTEGRATION.
- No Godot runtime involvement — this is Python pipeline + web editor only.
- The checkpoint log at `project_board/checkpoints/17_zone_extras_offset_xyz_controls/run-2026-04-11-planning.md` documents four assumptions made during planning (offset space, range, shell behavior, flat/nested schema). Spec Agent confirmed all four assumptions in `run-2026-04-11-autopilot.md`.

### Spec Decisions (Resolved)

All four planning-phase open questions are now resolved in `project_board/specs/zone_extras_offset_xyz_controls_spec.md`:

1. **Coordinate space:** Blender world-space (Z-up, X=front, Y=right). Offset applied directly to cx/cy/cz.
2. **Range/step/default:** -2.0..+2.0, step 0.05, default 0.0.
3. **Visibility when kind=none:** Always visible, always enabled. No-op for kind=none/shell (no geometry generated). Same category as finish/hex.
4. **Key schema:** Both flat (`extra_zone_{zone}_offset_x/y/z`) and nested (`zone_geometry_extras[zone].offset_x/y/z`) accepted. Canonical storage is nested.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: 41 new Python tests RED (as expected, pre-implementation); 755 existing Python tests GREEN. 14 new frontend tests RED (as expected, pre-implementation); 170 existing frontend tests GREEN.
- Static QA: Ruff clean (no errors on new test files)
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason
Primary tests written. Files modified:
- `asset_generation/python/tests/utils/test_animated_build_options.py` — 41 new test cases appended covering Requirements 1–6 and 10 (constants, regex, fields, default payload, merge flat/nested/priority, sanitize clamp/reset/boundary, control defs shape, round-trip via options_for_enemy, backward compat).
- `asset_generation/python/tests/enemies/test_zone_extras_offset_attach.py` — new file with 16 tests covering Requirement 5 (_zone_extra_offset helper AC-5.1–5.4; body offset_x/y/z vector assertions AC-5.5–5.6; head offset_z vector assertion AC-5.7; isolation AC-5.8; kind=none no-exception AC-5.9).
- `asset_generation/web/frontend/src/components/Preview/zoneExtrasPartition.test.ts` — 14 new frontend tests covering Requirement 7 (SUFFIX_ORDER last-three AC-7.1, suffixRank ordering AC-7.2–7.3, partitionZoneExtraDefs placement AC-7.4, existing order unchanged AC-7.5) and Requirement 8 (rowDisabled always returns false for offset keys AC-8.1–8.7, existing disable behavior preserved).
Test Breaker Agent must add adversarial/edge-case tests (zero-offset no-op, extreme clamp, cross-zone contamination, invalid float ignored) per Task 3 in the planning table.
