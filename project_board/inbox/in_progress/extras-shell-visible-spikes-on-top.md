# TICKET: extras-shell-visible-spikes-on-top

Title: Fix zone geometry extras — shell visible geometry + spikes appear on top
Project: blobert
Created By: Autopilot Orchestrator (from description)
Created On: 2026-04-11

---

## Description

**User description (verbatim):** "fix the extras so that the shell is actually visible and spikes properly appear on top too"

**Context from codebase exploration:**

The `zone_geometry_extras` system in `asset_generation/python/src/enemies/zone_geometry_extras_attach.py` currently:

1. **Shell (`kind = "shell"`)** is a documented v1 stub — no geometry is created. The existing spec (`project_board/specs/enemy_body_part_extras_spec.md`) explicitly says "v1 stub: no additional geometry." The user wants shell to produce actual visible geometry.

2. **Spikes "on top"** — spikes are placed on the ellipsoid surface using surface normals + an outward offset (`tip = point + normal * depth * 0.55`). If spikes are not visually appearing on top of the mesh (i.e., tips are inside or flush with the body surface), the outward normal offset factor may be insufficient, or the geometry attach order causes them to be occluded. The user wants spikes to visibly appear proud of the surface.

**Shell geometry design (to be finalized in spec):** A shell should be a thin offset/shell layer wrapping the ellipsoid — a `create_sphere` with non-uniform scale `(a * shell_scale, b * shell_scale, h * shell_scale)` where `shell_scale` is a new user-configurable field (default ~1.08, range 1.01–1.5). This reuses the existing sphere primitive and produces a carapace-like overlay on the zone ellipsoid. The shell is applied to both body and head zones wherever zone geometry is populated, for any enemy that has those zones wired.

**Spike "on top" semantics:** The current tip offset factor of `0.55` places the spike's base inside the body mesh (the cone apex is at `surface + 0.55 * depth`, but the base circle is at `apex - depth`, which is `surface - 0.45 * depth` — embedded). Increasing the factor to `1.0` places the apex one full depth-length above the surface, making the base circle sit flush on the surface. This is the targeted fix — change the literal `0.55` → `1.0` at all five call sites (body spikes uniform, body spikes random, head horns, head spikes uniform, head spikes random).

**Fields to add:**
- `shell_scale`: float, default 1.08, min 1.01, max 1.5, step 0.01 — controls how much the shell overscales the ellipsoid. Added to `_default_zone_geometry_extras_payload`, `_ZONE_GEOM_EXTRA_FIELDS`, and the flat API key regex (suffix `shell_scale`).

---

## Acceptance Criteria

- Shell kind produces visible geometry on the body and head zones for `slug` (and any other zone-capable enemies). Geometry wraps the ellipsoid zone as a thin scaled-up overlay or carapace shell. (inferred)
- Spike tips visibly protrude proud of the base mesh surface — no spike should appear partially buried or flush when placed on a visible zone. (inferred)
- Changing `kind` from `none` → `shell` in the editor preview shows a visible shell shape on the model. (inferred)
- Changing `kind` to `spikes` shows spikes clearly rising above the surface. (inferred)
- `pytest` for shell geometry creation (non-empty parts list when kind=shell) and spike protrusion (tip position > surface position along normal direction).
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

---

## Dependencies

- Depends on: zone geometry extras system (ticket M9-EBPE, completed); offset controls (ticket 17, completed)
- Related spec: `project_board/specs/enemy_body_part_extras_spec.md` (shell is currently v1 stub — this ticket upgrades it)

---

## Execution Plan

### Task 1 — Spec update (Spec Agent)
Update `project_board/specs/enemy_body_part_extras_spec.md`:
- Change shell semantics from "v1 stub: no additional geometry" to: scaled-ellipsoid overlay using `create_sphere(scale=(a*shell_scale, b*shell_scale, h*shell_scale))`, centered on zone center (plus offset_xyz). Document `shell_scale` field.
- Add `shell_scale` to the payload fields table (float, default 1.08, min 1.01, max 1.5).
- Update capability matrix: slug shell row from "no-op" to "ellipsoid overlay (body+head)"; note that any enemy with zone geometry wired also gets shell.
- Document spike tip offset fix: factor raised from 0.55 to 1.0 across all call sites.

### Task 2 — Test Design (Test Designer Agent)
Write failing tests in `asset_generation/python/tests/enemies/test_slug_zone_extras_attach.py` (or a new focused file `test_shell_and_spike_protrusion.py`):
- `test_shell_body_appends_sphere`: kind=shell on body → `create_sphere` called once, one part appended per zone with shell.
- `test_shell_head_appends_sphere`: kind=shell on head → same assertion.
- `test_shell_none_is_noop`: kind=none → no sphere called (existing behavior preserved).
- `test_spike_tip_protrudes_above_surface`: for a unit sphere zone (a=b=h=1), place one spike, extract the `location` passed to `create_cone`, verify the location is strictly farther from zone center than the surface point (dot with normal > surface_radius).
- `test_shell_scale_field_round_trips`: shell_scale default present in `_default_zone_geometry_extras_payload()` output; flat key `extra_zone_body_shell_scale` is accepted by `sanitize_build_options` for slug.

### Task 3 — Implementation (Engine Integration Agent)
Files to modify (Python pipeline only):

**`asset_generation/python/src/utils/animated_build_options.py`**
- Add `_SHELL_SCALE_MIN = 1.01`, `_SHELL_SCALE_MAX = 1.5` constants near the existing size constants.
- Add `shell_scale: 1.08` to `_default_zone_geometry_extras_payload()`.
- Add `"shell_scale"` to `_ZONE_GEOM_EXTRA_FIELDS` frozenset.
- Add `shell_scale` to the `_EXTRA_ZONE_FLAT_KEY` regex alternation.
- Add `shell_scale` to the zone control defs returned by `_zone_extra_control_defs` (float control, min/max/step/default matching spec).
- In `_sanitize_zone_geometry_extras` (or equivalent validation), clamp `shell_scale` to `[_SHELL_SCALE_MIN, _SHELL_SCALE_MAX]`.

**`asset_generation/python/src/enemies/zone_geometry_extras_attach.py`**
- In `_append_body_ellipsoid_extras`: add `elif kind == "shell":` branch — call `create_sphere(location=(cx,cy,cz), scale=(a*shell_scale, b*shell_scale, h*shell_scale))` where `shell_scale = _zone_extra_scale(spec, "shell_scale", default=1.08, lo=1.01, hi=1.5)`. Apply material, append to parts.
- In `_append_head_ellipsoid_extras`: same branch for head zone.
- Change spike tip offset factor from `0.55` to `1.0` at all five call sites:
  - `_append_body_ellipsoid_extras` uniform mode (line 291): `nrm * (depth * 0.55)` → `nrm * depth`
  - `_append_body_ellipsoid_extras` random mode (line 322): same change
  - `_append_head_ellipsoid_extras` horns (line 444): same change
  - `_append_head_ellipsoid_extras` spikes uniform (line 506): same change
  - `_append_head_ellipsoid_extras` spikes random (line 536): same change

### Task 4 — Static QA (Static QA Agent)
Run:
- `task hooks:py-review -- asset_generation/python/src/utils/animated_build_options.py asset_generation/python/src/enemies/zone_geometry_extras_attach.py`
- `task hooks:py-organization -- asset_generation/python/src/utils/animated_build_options.py asset_generation/python/src/enemies/zone_geometry_extras_attach.py`
Fix any findings.

### Task 5 — Integration / Full CI (Engine Integration Agent)
- Run `bash .lefthook/scripts/py-tests.sh` and verify exit 0.
- Run `bash ci/scripts/diff_cover_preflight.sh` and verify coverage gate passes.
- Run `timeout 300 ci/scripts/run_tests.sh` and verify exit 0.
- Commit all changes with message: `feat(asset-pipeline): shell geometry and spike protrusion fix for zone extras`

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Extended — adversarial cases added (attach: shell raw-spec clamp/missing/string/offset×scale, spike pyramid/random/ring/horns analytical tips; options: NaN/−inf, merge string coercion, root-flat override, epsilon bounds). Split `test_shell_and_spike_protrusion_adversarial.py` for module line cap. Pre-implementation: 55 tests total (51 failing / 4 passing) across the three focused files until shell branch + spike factor fix + shell_scale API land.
- Static QA: `task hooks:py-review` clean on modified test files
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Engine Integration Agent

## Required Input Schema
```json
{
  "implementation_paths": [
    "asset_generation/python/src/enemies/zone_geometry_extras_attach.py",
    "asset_generation/python/src/utils/animated_build_options.py"
  ],
  "spec_path": "project_board/specs/enemy_body_part_extras_spec.md",
  "test_files": [
    "asset_generation/python/tests/enemies/test_shell_and_spike_protrusion.py",
    "asset_generation/python/tests/enemies/test_shell_and_spike_protrusion_adversarial.py",
    "asset_generation/python/tests/utils/test_animated_build_options_shell_scale.py"
  ]
}
```

## Status
Proceed

## Reason
Adversarial test extension complete (shell attach clamp/missing/invalid string, combinatorial offset×scale, spike pyramid/random/ring paths, horn tip vs analytical factor=1.0, options NaN/inf/merge order/string coercion/epsilon bounds). Hand off to Engine Integration Agent to implement shell geometry, spike tip factor 1.0 at all five sites, and shell_scale in animated_build_options per spec.
