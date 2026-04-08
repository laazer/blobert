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
