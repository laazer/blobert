Ticket: M9-PMCP / 03_procedural_material_and_color_pipeline_fixes
Goal: Fix procedural PBR/material read in asset_generation (organic noise vs roughness, washed base colors) per milestone README; audit 02 has no published table yet.
Outcome: COMPLETE
Checkpoint log: project_board/checkpoints/M9-PMCP/run-2026-04-08-autopilot.md
Rework / surprises:
- diff-cover failed at 83% because `example_new_enemy.py` line 5 sat in the same branch diff uncovered; fixed with a one-line import test.
- Fake Blender node tests needed dict-based `outputs`/`inputs` because MagicMock `__getitem__` binding broke on `noise.outputs["Fac"]`.
- Single-ticket autopilot left the file in backlog until gatekeeper; then git mv to done/.

Git: commit after staging (orchestrator will record SHA in session).
