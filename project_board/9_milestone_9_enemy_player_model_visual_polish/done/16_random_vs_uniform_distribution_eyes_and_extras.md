# TICKET: 16_random_vs_uniform_distribution_eyes_and_extras

Title: Eye + extras distribution mode — random vs uniform (radio / segmented control)

## Description

Introduce a **mutually exclusive** distribution mode for **eyes** (when count &gt; 1) and for **zone extras** that spawn multiple instances (spikes, bulbs, horns clusters, etc.):

- **Uniform** — deterministic layout from a **shape/pattern** choice (see ticket **15** for clustering strength and preset catalog). Reproducible given the same build JSON.
- **Random** — stochastic placement within the same valid surface constraints, influenced by **clustering** from ticket **15** and by a **stable seed** in build options so the same settings re-export the same layout (unless seed is explicitly rotated).

**UI preference:** Use a **radio group** or **segmented control** (two options), **not** a single checkbox — “random” and “uniform” are opposites, not an on/off feature.

Editor placement: alongside related **Build** / **Extras** controls, or grouped in a small “Distribution” subsection so eyes and extras modes are discoverable.

## Acceptance Criteria

- Spec documents: JSON keys, defaults (e.g. default **uniform** for readability in previews), and behavior when count is 0 or 1 (mode no-op or hidden in UI).
- **Uniform** path exposes at least one **shape** selector (or derived automatically per slug) as agreed with ticket **15**; invalid shape + slug combinations fail validation with a clear error.
- **Random** path uses project RNG conventions (`self.rng` / seeded build options) so exports are reproducible when seed is fixed.
- Frontend renders **radio** (or segmented) control bound to build options; no ambiguous checkbox-only UX for this choice.
- Tests: option merge/sanitize in `animated_build_options`; at least one procedural test that uniform vs random yields different layouts for the same counts under a fixed divergent seed.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- **Hard:** Ticket **15** (clustering + uniform presets) — coordinate keys and spec in one pass if possible.
- Extras multi-instance zones (ticket **11** or current implementation).

## Open questions (resolve in spec)

- **One global mode** vs **separate modes** for eyes and for extras (per zone or global for all extras).
- Whether **player** or non-animated assets are in scope (default: **animated enemies only**).

## Execution plan

1. Spec: key layout, seed field name, UI copy, per-slug defaults.
2. Python: branch placement logic (uniform vs random) in eye + extras code paths; validation.
3. Frontend: radio group component reuse or minimal new control; wire to store.
4. Tests as above.

## Specification (summary)

- **Doc:** `project_board/specs/eye_and_extras_random_uniform_distribution_spec.md`
- **Python:** `animated_build_options.py` (defs, merge, sanitize); `placement_clustering.py` (`uniform_arc_angles`, `uniform_ring_angles`, `placement_prng`); `animated_spider.py` (uniform vs random eye dirs); `zone_geometry_extras_attach.py` (per-zone distribution branches).
- **Frontend:** `select_str.segmented` in types + `BuildControlRow`; synthetic `extra_zone_*_distribution` / `_uniform_shape` in `animatedZoneControlsMerge`; `ZoneExtraControls` + `BuildControls` disable rules; `zoneExtrasPartition` suffix order.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
1

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: `uv run pytest` (distribution + placement clustering + spider eye + `test_animated_build_options`); `npm test` (frontend); `timeout 300 ci/scripts/run_tests.sh` exit 0 (incl. diff-cover ≥ 85%).
- Static QA: Ruff on touched Python; TypeScript tests green.
- Spec: `project_board/specs/eye_and_extras_random_uniform_distribution_spec.md`.

## Blocking Issues

- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Instruction
Merge when ready; rotate `placement_seed` to explore random layouts without changing mesh RNG.

