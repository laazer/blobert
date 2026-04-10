# TICKET: 15_eye_and_extras_placement_clustering_controls

Title: Procedural placement — clustering controls for eyes and zone extras

## Description

Add a **clustering** dimension to how **multiple eyes** and **multiple extras** (spikes, bulbs, horns, etc. — same surfaces as ticket **11** / `zone_geometry_extras` / `extra_zone_*` build keys) are distributed on the mesh. Controls should feel like **Build** tab tuning: numeric **increase/decrease** (slider or stepped float/int) with sane min/max and defaults per slug.

**Clustering** means adjusting how tightly grouped vs spread instances are relative to each other (e.g. pack toward a focal direction/region vs distribute across the allowed zone), without redefining which body zones are eligible — that stays in existing placement flags.

**Uniform layout shapes:** When distribution mode is **uniform** (see ticket **16**), the user (or spec) chooses among **deterministic pattern presets** (examples to finalize in spec: arc / ring segment, grid-like spacing, line, symmetric pairs — exact set per enemy family where it makes sense). This ticket owns the **clustering strength** parameter and how it modulates those patterns; ticket **16** owns the **random vs uniform** switch and which presets appear.

## Acceptance Criteria

- Written spec appendix or `project_board/specs/` doc defines: parameter name(s), JSON flat + nested merge rules in `animated_build_options`, and how clustering interacts with **uniform** presets vs **random** placement.
- **Eyes:** At least one animated enemy with variable eye count (e.g. spider `eye_count` path) respects clustering when count &gt; 1; enemies with a single eye or zero may no-op cleanly.
- **Extras:** Zones with countable extras (spikes, bulbs, …) respect clustering on the same zones already supported by the extras pipeline.
- Editor **Build** (and/or **Extras**) surfaces the control with the same metadata pattern as existing `int` / `float` build controls (`GET /api/meta` → `BuildControls`).
- **Determinism:** For a fixed build JSON (including mode + seed from **16**), output is stable across runs in the same environment.
- `pytest` + `timeout 300 ci/scripts/run_tests.sh` exit 0.

## Dependencies

- **Hard:** Extras placement pipeline usable for multi-instance zones (ticket **11** implemented or equivalent in tree).
- **Soft:** Ticket **16** — clustering semantics should be specified together so “uniform + shape” and “random + clustering” are not contradictory; either implement **15** after **16** or land both in one branch with a single spec.

## Open questions (resolved in spec)

- **Scope per control:** Separate **`eye_clustering`** (spider) and per-zone **`clustering`** in `zone_geometry_extras` / flat `extra_zone_<zone>_clustering`.
- **Mesh ClassVars:** Orthogonal; clustering modulates placement only.

## Execution plan

1. Spec: math definition of clustering, preset catalog for uniform mode, per-slug matrix (which enemies get which controls).
2. Python: placement algorithms in eye builders + zone extras attachment; `animated_build_options` defs and sanitization.
3. Frontend: render new control(s) from API defs.
4. Tests: golden vectors or snapshot-friendly assertions for a few (slug, mode, clustering) tuples.

## Specification (summary)

- **Doc:** `project_board/specs/eye_and_extras_placement_clustering_spec.md`
- **Helpers:** `src/utils/placement_clustering.py` — `clustered_ellipsoid_angles_bounded` for RNG ellipsoid sampling; default `clustering` 0.5; range [0, 1].
- **Spider:** `eye_clustering` build option; `_eye_dirs` scales lateral/arc spread when `eye_count > 1`.
- **Extras:** `zone_geometry_extras[*].clustering`; horns use lateral `horn_spread`; body/head spikes & bulbs use bounded angular clustering.
- **Frontend:** `extra_zone_*_clustering` in partition order; synthetic defs + `ZoneExtraControls` dims when `none`/`shell`.
- **Stub:** `blender_stubs._Vector` gained `dot` and `x`/`y`/`z` for test/runtime parity with facing + attach paths.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
1

## Last Updated By
Autopilot Orchestrator

## Validation Status

- Tests: `uv run pytest` (incl. `test_placement_clustering.py`, `test_spider_eye_clustering.py`, extended `test_animated_build_options.py`); `npm test` / `npm run build` (frontend); `timeout 300 ci/scripts/run_tests.sh` exit 0.
- Static QA: Ruff import order clean on touched Python.
- Integration: N/A (procedural Python + editor defs).

## Blocking Issues

- None

## Escalation Notes

- Ticket **16** still owns random vs uniform mode switch; this implementation applies clustering to the current stochastic placement path and documents forward interaction in the spec.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Instruction
Ship / merge when ready; ticket **16** can extend placement mode + uniform presets on top of these keys.
