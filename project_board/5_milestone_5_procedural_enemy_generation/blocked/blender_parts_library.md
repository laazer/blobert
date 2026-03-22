Title:
Build Blender primitive parts library
---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | BLOCKED |
| Revision | 1 |
| Last Updated By | Autopilot Orchestrator |
| Next Responsible Agent | Human |
| Validation Status | Not started |
| Blocking Issues | Requires Blender installation / generated GLB assets. Cannot proceed without external tool. |

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
