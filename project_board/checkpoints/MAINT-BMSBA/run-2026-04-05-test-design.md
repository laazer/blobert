# MAINT-BMSBA checkpoint — Test Designer (2026-04-05)

**Run:** test-design  
**Ticket:** `project_board/maintenance/in_progress/base_models_split_by_archetype.md`

## Outcome

- Added `asset_generation/python/tests/enemies/test_base_models_factory.py` covering BMSBA-2 / BMSBA-3 / public exports (BMSBA-1.1).
- Geometry/material paths patched on `src.enemies.base_models`; relies on `tests/enemies/conftest.py` bpy stubs for import.
- `uv run pytest tests/ -q`: **335 passed** (includes new cases + subtests).

## Would have asked

- None; spec is sufficient for factory contracts and part-count snapshots.

## Assumption made

- Part counts and `apply_material_to_object` call counts for `random.Random(42)` are treated as regression anchors (BMSBA-3.2); implementation must preserve procedural structure or update tests with justification.

## Confidence

High for factory/registry behavior; medium dependency on unchanged geometry ordering within each archetype class.
