Title:
Precise Placement Controls (Position, Rotation, Scale)

Description:
For each placed part in builder mode, expose numeric position, rotation, and scale inputs so users can place parts with exact values rather than relying on drag or defaults. A reset-to-default button ensures users can recover from bad edits. This is the primary ergonomic differentiator of builder mode over preset mode.

Acceptance Criteria:
- Each placed part exposes in its properties panel: X/Y/Z position (float), X/Y/Z rotation (degrees, -180 to 180), X/Y/Z scale (float, min 0.1)
- All inputs accept keyboard entry; pressing Enter or tabbing away commits the value
- Values outside valid ranges are clamped or rejected with inline validation feedback visible next to the field
- A "Reset Part" button restores the part's position, rotation, and scale to its auto-placed defaults for that component type
- All changes reflect in the 3D preview immediately
- All placement values serialize to enemy config JSON per part

Scope Notes:
- Numeric inputs only — no 3D viewport gizmo or drag handles in this ticket
- No grid snapping or alignment aids
- Scale is per-axis (non-uniform stretch supported); no locked uniform scale mode required
- Reset restores to auto-placed defaults, not to the last saved state

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
