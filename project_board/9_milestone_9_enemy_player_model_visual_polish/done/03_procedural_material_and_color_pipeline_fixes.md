# TICKET: 03_procedural_material_and_color_pipeline_fixes

Title: Fix procedural materials / colors in asset_generation for audited families

## Description

Implement fixes from `02_mesh_and_material_audit_enemy_families_and_player` (and ongoing review) in **`asset_generation`** — e.g. `material_system.py`, mesh build options, or family-specific color tables — so exported GLBs match the intended palette and read correctly in Godot (PBR roughness/metallic sanity, no washed-out defaults unless intentional).

Avoid one-off shaders per enemy unless promoted to a shared primitive; prefer extending existing material helpers.

## Acceptance Criteria

- Each **fix-required** color/material issue from the audit has a corresponding code change or a documented wont-fix with reason.
- Regenerated exports (or documented regen command) show visible improvement on at least one problem family called out in the audit.
- `pytest` for `asset_generation/python` passes; `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `02_mesh_and_material_audit_enemy_families_and_player`

## Execution Plan

| # | Stage | Deliverable |
|---|--------|-------------|
| 1 | Planner | Scope + audit stand-in assumptions (checkpoint) |
| 2 | Spec | `project_board/specs/procedural_material_color_pipeline_spec.md` (PMCP-*) |
| 3 | Test design | `tests/materials/test_material_system_principled_pipeline.py` |
| 4 | Test break | `# CHECKPOINT` adversarial cases on mocks |
| 5 | Implementation | `material_system.py` PBR + organic tuning; regen note |
| 6 | Script review + AC Gatekeeper | pytest + `run_tests.sh`; COMPLETE |

## Specification

- **Path:** `project_board/specs/procedural_material_color_pipeline_spec.md`

## Audit appendix (ticket 03)

| Source | Status | Notes |
|--------|--------|--------|
| `02_mesh_and_material_audit…` published table | **Deferred** | No fix-required rows in repo yet; this ticket uses milestone README (“washed out” procedural colors) + code review as stand-in per PMCP-5. |
| Organic noise → full roughness swing | **Fix in code** | PMCP-1 |
| Strong organic multiply on base color | **Fix in code** | PMCP-2 |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

9

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `tests/materials/test_material_system_principled_pipeline.py` (PMCP-1/2 + `# CHECKPOINT` ceiling); `tests/materials/test_feature_zone_materials.py` unchanged behavior; `tests/enemies/test_example_new_enemy_import.py` (diff-cover on `example_new_enemy.py` line 5 for branch vs `origin/main`); full `uv run pytest tests/` 575 passed; `timeout 300 ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`, diff-cover 100% on touched diff hunk set).
- Static QA: Ruff clean on touched Python (`material_system.py`, new tests).
- Integration / manual: Regen slug (organic + rocky dirt slot) for visible material pass: from `asset_generation/python`, `uv run python main.py animated slug 1` → `animated_exports/slug_animated_00.glb` (per `main.py` help). Audit ticket `02` still has no published table — AC-1 satisfied via **Audit appendix** + PMCP-5 wont-fix/defer rows.

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

- Optional: run Blender regen above and spot-check slug in Godot editor; push branch if satisfied.

## Notes

Spec: `project_board/specs/procedural_material_color_pipeline_spec.md`. Scoped log: `project_board/checkpoints/M9-PMCP/run-2026-04-08-autopilot.md`.
