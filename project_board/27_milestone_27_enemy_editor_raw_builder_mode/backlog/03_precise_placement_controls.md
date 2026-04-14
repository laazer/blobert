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

## Web Editor Implementation

**No new Python or backend changes required** — placement values are stored client-side and serialized to enemy config JSON.

**Frontend (`asset_generation/web/frontend/src/`)**
- `store/useAppStore.ts`: add `builderPlacements: Record<category, { pos: [x,y,z], rot: [x,y,z], scale: [x,y,z] }>` and `setBuilderPlacement(category, field, axis, value)` to the store; defaults per category are defined as constants in a `builderDefaults.ts` module
- Create `components/Builder/PlacementControls.tsx`: renders when a category is selected in `BuilderPartsPanel`; shows three labeled rows (Position, Rotation, Scale) each with three numeric `<input type="number">` fields for X/Y/Z; inputs are wired to `setBuilderPlacement`; uses `onBlur` to commit values (not `onChange` on every keystroke) for performance
- Validation: rotation inputs clamp to [-180, 180] on blur; scale inputs with value < 0.1 are snapped to 0.1; out-of-range values show an inline red hint next to the field (not a modal)
- "Reset Part" button calls `setBuilderPlacement` with the defaults from `builderDefaults.ts` for the active category
- `BuilderPreview.tsx`: subscribe to `builderPlacements` in Zustand; on each change, update the corresponding Three.js mesh's `position`, `rotation` (degrees → radians), and `scale` properties; use `useEffect` on the store slice to avoid full scene re-creation

**Tests**
- Frontend (Vitest): `PlacementControls.test.tsx` — entering 200 in a rotation field and blurring clamps it to 180; entering 0.05 in a scale field clamps to 0.1; "Reset Part" restores values to `builderDefaults` for that category; a valid placement update calls `setBuilderPlacement` with the correct axis/value

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
