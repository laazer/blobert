# Checkpoint Log: extras-shell-visible-spikes-on-top
Run: run-2026-04-11-autopilot

## Stage History

- PLANNING: Started 2026-04-11T19:59Z — Autopilot Orchestrator (description mode)
- PLANNING (decomposition): 2026-04-11 — Planner Agent
- SPECIFICATION: 2026-04-11 — Spec Agent

## Ticket Creation

- Description: "fix the extras so that the shell is actually visible and spikes properly appear on top too"
- Slug: extras-shell-visible-spikes-on-top
- Ticket: project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md
- Context research findings:
  - Shell is a documented v1 stub (enemy_body_part_extras_spec.md line 27)
  - No shell geometry in zone_geometry_extras_attach.py (no handler for kind=shell in _append_body_ellipsoid_extras or _append_head_ellipsoid_extras)
  - Spikes use tip offset: Vector(p) + nrm * depth * 0.55 (hardcoded factor)
  - "On top" interpreted as: spikes should protrude visibly proud of the surface

## Resume: 2026-04-11T21-00-00Z-ap-continue
- **Trigger:** User `/ap-continue` with spec path `project_board/specs/enemy_body_part_extras_spec.md` → resolved to ticket `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md`.
- **Resuming at Stage:** `TEST_BREAK`
- **Next Agent:** Test Breaker Agent

## Checkpoint Entries

### [extras-shell-visible-spikes-on-top] PLANNING — Shell geometry approach
**Would have asked:** Should the shell be a single uniformly scaled ellipsoid primitive (create_sphere with non-uniform scale derived from zone semi-axes), or a distinct mesh type? Should it use an existing primitive (sphere/create_sphere) or require a new one?
**Assumption made:** Shell uses create_sphere with scale=(a*shell_scale, b*shell_scale, h*shell_scale) where shell_scale is a tunable float (default ~1.08) — this produces a thin offset layer over the zone ellipsoid using only the existing sphere primitive. No new primitive needed.
**Confidence:** Medium

### [extras-shell-visible-spikes-on-top] PLANNING — Shell spec field (shell_scale)
**Would have asked:** Should the shell thickness be user-configurable via a new field (e.g. shell_scale), or hardcoded?
**Assumption made:** Introduce a `shell_scale` field with a sensible default (1.08) and min/max (1.01–1.5), mirroring how spike_size and bulb_size work. This keeps the editor composable. The spec must document this field.
**Confidence:** Medium

### [extras-shell-visible-spikes-on-top] PLANNING — Spike tip offset factor
**Would have asked:** What is the correct outward factor to make spikes visibly protrude? The current value is 0.55 (tip center placed at surface + 55% of depth outward). For a cone of depth D with radius1=0.4, base starts at tip-D and the widest circle is at tip. To make the spike base flush with the surface, tip must be at surface + depth*1.0. Current 0.55 embeds the base inside the mesh.
**Assumption made:** Increase the tip offset factor from 0.55 to 1.0 across all four call sites (body spikes, body horns stub, head horns, head spikes). This places the spike tip (apex) one full depth-length above the surface point — the base circle will sit on the surface. This is a minimal, targeted fix.
**Confidence:** High

### [extras-shell-visible-spikes-on-top] PLANNING — Spec update scope
**Would have asked:** Does the existing spec at enemy_body_part_extras_spec.md need updating for shell geometry?
**Assumption made:** The spec update is scoped to the Spec Agent stage: update shell semantics from "v1 stub: no geometry" to specify the shell_scale field and ellipsoid overlay geometry. Capability matrix row for slug shell changes from "no-op" to "ellipsoid overlay." Other slugs stay no-op until wired.
**Confidence:** High

### [extras-shell-visible-spikes-on-top] PLANNING — Affected slugs for shell geometry
**Would have asked:** Should shell geometry work for all zone-capable enemies or only slug initially?
**Assumption made:** Shell geometry works wherever the zone center+radii are populated (body and head zones for slug; same code path in _append_body_ellipsoid_extras and _append_head_ellipsoid_extras handles all enemies). The generic attach function handles all enemies, so shell will work for any enemy with _zone_geom_body_center/_zone_geom_body_radii set. Capability matrix note: other enemies that expose body/head zone geometry will also get shell — document this in spec.
**Confidence:** Medium

### [extras-shell-visible-spikes-on-top] PLANNING — No new sanitize/flat-key changes
**Would have asked:** Does shell_scale need a new flat API key (extra_zone_body_shell_scale)?
**Assumption made:** Yes — add shell_scale to the flat API key regex and to _ZONE_GEOM_EXTRA_FIELDS and _default_zone_geometry_extras_payload so it round-trips through the API. This matches the pattern for spike_size and bulb_size.
**Confidence:** High

### [extras-shell-visible-spikes-on-top] TEST_BREAK — Test Breaker Agent (adversarial extension)
**Date:** 2026-04-11
**Scope:** `asset_generation/python/tests/enemies/test_shell_and_spike_protrusion.py`, `asset_generation/python/tests/enemies/test_shell_and_spike_protrusion_adversarial.py`, `asset_generation/python/tests/utils/test_animated_build_options_shell_scale.py`
**Added coverage (matrix):**
- **Attach / shell:** raw-spec clamp min/max at `_append_*` (defense in depth); missing `shell_scale` key → default 1.08; invalid string → default; combinatorial negative offset + max shell_scale on head.
- **Attach / spikes:** pyramid `vertices=4` path; body+head `distribution=random` (deterministic `MagicMock` RNG); head `uniform_shape=ring`; head horns — analytical expected tips at factor 1.0 vs captured `create_cone` locations (catches horn call site left at 0.55).
- **Options / sanitize:** `NaN` → default 1.08; `-inf` → clamp min; merge flat string `"1.22"` through `_merge_zone_geometry_extras` + sanitize; root flat `extra_zone_body_shell_scale` wins over nested `slug.zone_geometry_extras`; body/head independence; epsilon just below min / just above max.
**Evidence:** `uv run pytest tests/enemies/test_shell_and_spike_protrusion.py tests/enemies/test_shell_and_spike_protrusion_adversarial.py tests/utils/test_animated_build_options_shell_scale.py` — 55 tests: 51 failed, 4 passed pre-implementation (expected red until `zone_geometry_extras_attach` shell branch + spike `0.55→1.0` + `animated_build_options` `shell_scale` plumbing); `task hooks:py-review` + py-organization clean (adversarial tests split to satisfy 900-line module cap).
**Handoff:** Stage → `IMPLEMENTATION_GENERALIST`; Next agent → Engine Integration Agent (owns `asset_generation/python` per ticket execution plan).
**Would have asked:** None — ticket explicitly routed Test Breaker after test design.
**Assumption made:** Workflow stage `IMPLEMENTATION_GENERALIST` is the correct enum for Python-only pipeline work (no `IMPLEMENTATION_ENGINE` in `workflow_enforcement_v1.md`).
**Confidence:** High

### [extras-shell-visible-spikes-on-top] IMPLEMENTATION — Engine Integration Agent (shell_scale + shell geometry + spike factor 1.0)
**Date:** 2026-04-11
**Scope:** `asset_generation/python/src/utils/animated_build_options.py`, `asset_generation/python/src/enemies/zone_geometry_extras_attach.py`; docstring fix in `tests/enemies/test_zone_extras_offset_attach.py` (tip factor 1.0).
**Assumption made:** `_zone_extra_scale` treats `NaN` as default and signed infinity as clamp-to-bounds for all keys (spike_size, bulb_size, shell_scale, etc.) so attach-layer defense matches sanitize behavior for shell_scale without a separate helper.
**Evidence:** `uv run pytest` on `test_shell_and_spike_protrusion.py`, `test_shell_and_spike_protrusion_adversarial.py`, `test_animated_build_options_shell_scale.py` — 55 passed, exit 0; `test_slug_zone_extras_attach.py` + `test_zone_extras_offset_attach.py` — 28 passed; `bash .lefthook/scripts/py-tests.sh` — exit 0. Full `ci/scripts/run_tests.sh` not run in this handoff.
**Handoff:** Stage → `STATIC_QA`; Next → Acceptance Criteria Gatekeeper Agent.

### [extras-shell-visible-spikes-on-top] SPECIFICATION — Call site count correction
**Would have asked:** The ticket execution plan says "four call sites" for the 0.55 factor. Actual grep of zone_geometry_extras_attach.py finds 5 occurrences. How should the spec handle this?
**Assumption made:** All 5 confirmed call sites (lines 291, 322, 444, 506, 536) must be updated to factor 1.0. The breakdown is: body spikes uniform (line 291), body spikes random (line 322), head horns (line 444), head spikes uniform (line 506), head spikes random (line 536). The ticket's "four" was a miscounting omission of the fifth (head spikes random). Spec documents 5 sites.
**Confidence:** High
