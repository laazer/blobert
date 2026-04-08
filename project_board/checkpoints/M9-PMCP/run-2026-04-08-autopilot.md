# M9-PMCP — procedural material / color pipeline (autopilot run)

## Step 0
- **Queue:** single ticket `03_procedural_material_and_color_pipeline_fixes.md`
- **Assumption:** Ticket `02_mesh_and_material_audit` has no published fix-required table yet; scope anchored to milestone README (washed-out procedural colors) + code review of `material_system.py` (noise-driven roughness + strong organic multiply).

### PLANNING — scope
**Would have asked:** Which exact rows from audit 02 are in scope?
**Assumption made:** Treat README + pipeline review as stand-in until 02 publishes a table; document wont-fix/defer for missing audit rows in ticket appendix.
**Confidence:** Medium

### IMPLEMENTATION — material_system
- Removed organic + metallic procedural **noise → Roughness** links so `setup_materials` roughness/metallic presets apply for default finish (PMCP-1).
- Named `_ORGANIC_BASE_COLOR_DETAIL_FAC = 0.12` (was implicit 0.3 multiply) for PMCP-2.
- `add_metallic_texture` no longer allocates unused noise nodes.

### STATIC_QA / CI
- `test_example_new_enemy_import.py` added so diff-cover vs `origin/main` reaches 100% on the branch diff (uncovered `from __future__` on line 5 of `example_new_enemy.py`).

### OUTCOME
COMPLETE — `timeout 300 ci/scripts/run_tests.sh` exit 0.
