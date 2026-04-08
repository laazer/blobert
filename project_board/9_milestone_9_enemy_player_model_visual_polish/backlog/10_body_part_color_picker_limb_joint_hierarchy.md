# TICKET: 10_body_part_color_picker_limb_joint_hierarchy

Title: Fix body-part color picker + hierarchical colors (limbs / joints + per-part overrides)

## Description

The asset editor’s **material color controls** (feature `finish` + `hex` rows from `animated_build_controls_for_api()`, rendered in `BuildControlRow.tsx` for keys ending in `_hex`) need a **reliability pass** and a **clearer hierarchy**:

1. **Fix the current picker** — address incorrect or confusing behavior today (e.g. `<input type="color">` vs RRGGBB text getting out of sync, invalid/empty hex handling, labels that don’t match what gets applied in Blender, or zones that don’t map cleanly to `material_system` / mesh assignment). Enumerate concrete bugs in the spec or ticket revision as they are found.

2. **Top-level category colors** — users must be able to set colors (and finishes where applicable) at **coarse scope** for logical groups, at minimum:
   - **All limbs** (shared default for limb segments)
   - **All joints** (shared default for joint balls / hinge visuals when `LIMB_JOINT_VISUAL` or equivalent is on)

   These sit **above** per-instance tuning.

3. **Per-limb / per-joint overrides** — where the rig exposes distinct parts (e.g. left arm vs right arm, or joint index along a chain), allow **optional** hex/finish overrides that **inherit** from the limb or joint **category default** when unset.

Implementation spans **`asset_generation/python/src/utils/animated_build_options.py`** (feature zones, flat keys, defaults, merge rules), **`asset_generation/python/src/materials/material_system.py`** (how `build_options["features"]` maps to Blender materials), **`BuildControlRow.tsx`** / **`BuildControls.tsx`** (grouped UI: category rows + expandable per-part rows), and **pytest** / frontend tests for merge + sanitization.

## Acceptance Criteria

- Documented **bug list** for the old picker is closed or explicitly waived with reason.
- **Limb** and **joint** category controls exist in the API for every slug that has segmented limbs with joint visuals (or spec lists exceptions).
- **Per-part** overrides work for at least one reference enemy (e.g. imp or spider) without breaking slugs that only use coarse zones.
- Nested + flat JSON round-trip preserved for new keys; `_sanitize_hex` / finish validation unchanged or extended consistently.
- `pytest asset_generation/python/tests/utils/test_animated_build_options.py` (and new tests) pass; frontend tests updated if command/build-option wiring changes.
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `03_procedural_material_and_color_pipeline_fixes` (soft — coordinate to avoid conflicting material contracts)
