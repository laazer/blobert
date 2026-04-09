# TICKET: 11_enemy_body_part_extras_spec_and_pipeline

Title: Enemy body-part “extras” — spec, build options, and procedural mesh pipeline

## Description

Add **standard visual extras** that can be attached to **enemy** procedural builds (asset pipeline + preview), analogous to how **Colors** drives per-zone materials but for **geometry overlays**.

**Extra kinds (v1 scope):**

- **Shell** — turtle-like carapace where the underlying body topology supports it; document which slugs/body shapes get a meaningful shell vs “unsupported / no-op” (do not fail the build).
- **Spikes** — user-selectable primitive style (**cone** or **pyramid**) and **spike count** (sane min/max and defaults per spec).
- **Horns** — either a dedicated preset or, if redundant, **spikes constrained to head placement**; the written spec must pick one approach and name the API fields accordingly.
- **Bulbs** — protrusions/lumps with **bulb count** (and default size/placement rules in spec).

**Per-body-part rule (v1):** Each logical body part / material zone may have **at most one** extra type active (e.g. not shell + spikes on the same part). Validation rejects or last-writer-wins must be specified; prefer explicit validation + clear editor error.

**Materials:** Each applied extra must accept the same class of controls as body materials where applicable: **finish** (when the material system supports it for these meshes) and **hex color**, keyed per part so extras can differ from the base part color.

## Acceptance Criteria

- Written spec under `project_board/specs/` defines: JSON shape (nested + flat keys), merge/sanitize behavior with existing `animated_build_options`, which enemies/slugs support which extras, and unsupported combinations (explicitly including shell-on-unsupported-mesh).
- `asset_generation/python` exposes build-control definitions for the editor API (same pathway as existing animated build controls / feature rows) so the UI can render per-part extra type + material + color without ad-hoc string parsing.
- Procedural build attaches extra geometry in Blender (or agreed generator step) for **spikes** (cone + pyramid) and **bulbs** at minimum; **shell** and **horns** implemented per spec or documented as phased with stub no-op that still round-trips options.
- `pytest` covers merge, validation (one extra per part), and at least one golden-path build option parse for a reference slug.
- `timeout 300 ci/scripts/run_tests.sh` exits 0 (or ticket documents Godot-only gaps with owner waiver — default is full green).

## Dependencies

- Soft: `done/10_body_part_color_picker_limb_joint_hierarchy.md` — align per-part keying and material finish/hex patterns with existing `feat_*` / zone contracts.

## Execution plan

1. Spec: extras schema, per-part exclusivity, material keys, slug capability matrix (`project_board/specs/enemy_body_part_extras_spec.md`).
2. Python: `animated_build_options` (and related) — defaults, nesting, sanitization; API metadata for controls.
3. Blender / generator: mesh attachment for each extra kind per spec; materials wired through `material_system` (or parallel slot) for extra sub-meshes.
4. Tests: extend `asset_generation/python/tests/utils/test_animated_build_options.py` (and new modules as needed); full CI as above.

## Specification (summary)

Authoritative contract: `project_board/specs/enemy_body_part_extras_spec.md`.

- **Key:** `zone_geometry_extras` (per-zone object with `kind`, `spike_shape`, `spike_count`, `bulb_count`, `finish`, `hex`).
- **Flat API:** `extra_zone_<zone>_*` keys; root-level flat keys merge after nested slug envelope.
- **Horns:** `kind: horns` only on **`head`**; other zones coerce to `none`.
- **Shell:** round-trip / no-op geometry in v1.
- **Geometry:** `slug` attaches spikes/bulbs/horns via `zone_geometry_extras_attach.append_slug_zone_extras` after base materials; other slugs API-only in v1.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `uv run pytest tests/` (692 passed, 149 subtests); targeted `test_animated_build_options.py`, `test_slug_zone_extras_attach.py`, `test_feature_zone_materials.py`, `test_blender_utils_cone.py`.
- Static QA: Passing — `task hooks:py-review` on touched Python modules.
- Integration: Passing — `timeout 300 ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`); diff-cover ≥ 85%; `npm test` frontend 154 passed.

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason

All acceptance criteria are evidenced: formal spec, Python merge/API controls, slug procedural attachment + `material_for_zone_geometry_extra`, pytest + full CI green.
