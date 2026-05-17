Title:
Build Blender primitive parts library
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | Done (the Python pipeline already handled this) |
| Revision | 6 |
| Last Updated By | Autopilot Orchestrator |
| Next Responsible Agent | Human |
| Validation Status | Superseded |
| Blocking Issues | Ticket premise is incorrect. The asset_generation/python pipeline already implements a procedural Python-based parts system (create_sphere, create_cylinder, etc. in src/core/blender_utils.py). There is no separate enemy_parts.blend file needed. Spec and test artifacts generated for this ticket were incorrect and have been deleted. The actual M5 work is captured in blender_python_generator.md. |

---

Description:
Create enemy_parts.blend with the core reusable mesh components: BaseBlob, BaseSphere,
BaseCapsule, EyeNode, Spike, Claw, Shell, Tentacle, Wing, OrbCore, Blade.
Each piece should be extremely simple (under 100 triangles). Organized in a Parts collection.

Acceptance Criteria:
- All parts exist in a single enemy_parts.blend file
- Each part is under 100 triangles
- Parts are logically named and organized in a Blender collection
- File is committed to assets/enemies/parts/

---

## Notes

This ticket was written before the asset_generation/python pipeline was reviewed.
The pipeline already handles enemy part assembly procedurally via Python classes in
src/enemies/. There is no .blend parts library — parts are primitive geometry operations
composed per-enemy in Python code.

Superseded by the revised blender_python_generator.md ticket.
