Title:
Per-Part Rotation Controls

Description:
Add X/Y/Z rotation inputs to the part properties panel so users can orient individual body parts (head, torso, limbs). Currently parts can be positioned but not rotated, which forces unnatural default poses and limits design variation. This ticket adds cosmetic rotation of the primitive shape — it is not joint rotation or skeletal posing.

Acceptance Criteria:
- Each selectable part exposes X, Y, Z rotation inputs in the properties panel
- Inputs accept numeric values in degrees; valid range is -180 to 180
- Values outside the valid range are clamped or rejected with inline feedback
- A "Reset Rotation" button restores the part to 0/0/0
- Rotation changes reflect immediately in the 3D preview
- Rotation values serialize correctly to enemy config JSON alongside position and scale

Scope Notes:
- Numeric inputs only — no 3D viewport rotation gizmo
- This is cosmetic orientation of the shape primitive, not joint/skeletal rotation
- No rotation constraints or limits tied to part type
- Does not affect collision or gameplay hitbox geometry

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
