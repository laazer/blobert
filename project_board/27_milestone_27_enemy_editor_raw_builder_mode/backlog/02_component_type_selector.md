Title:
Component Type Selector (Body, Head, Arms, Legs)

Description:
In builder mode, let users explicitly choose the primitive type for each of the four body regions. Each category offers at least 3 distinct options. Selecting a component type auto-places it at a default position in the preview. This gives users compositional control over the enemy's silhouette before any fine-tuning.

Acceptance Criteria:
- Body Base selector offers at least 3 options (e.g., sphere, box, capsule); selecting one places it at the origin
- Head Type selector offers at least 3 options (e.g., sphere, cube, cone); selecting one places it at a sensible default above the body
- Leg Type selector offers at least 3 options (e.g., cylinders, stubs, none); "none" produces no leg geometry
- Arm Type selector offers at least 3 options (e.g., cylinders, spheres, none); "none" produces no arm geometry
- Selecting any component type updates the 3D preview immediately
- All four regions must be assigned (none as a valid choice counts) before the config is considered valid for export
- All four component selections serialize to the enemy config format shared with preset mode

Scope Notes:
- Both arms share one arm type; per-instance variation is out of scope
- No custom mesh import — primitive-based types only
- Joint positions are auto-placed at category defaults; manual joint control is in ticket 03
- Visual properties (color, texture) from M25 apply to builder-mode parts using the same panel

## Web Editor Implementation

**Python / FastAPI (`asset_generation/web/backend/`)**
- Add `GET /api/builder/component-types` endpoint that returns the valid type options per category; the response shape is `{ "body": ["sphere","box","capsule"], "head": [...], "legs": [...], "arms": [...] }`
- The type lists are static in this ticket (hardcoded in a new `routers/builder.py`); no Python asset-pipeline dependency required yet
- Register the new router in `main.py` under prefix `/api/builder`

**Frontend (`asset_generation/web/frontend/src/`)**
- `store/useAppStore.ts`: add `builderComponents: { body: string|null, head: string|null, legs: string|null, arms: string|null }` and `setBuilderComponent(category, type)` to the store
- `components/Builder/BuilderPartsPanel.tsx`: for each category row, render a `<select>` (or segmented button group) populated from the `/api/builder/component-types` response; on selection, call `setBuilderComponent(category, type)` and update the 3D preview
- `components/Builder/BuilderPreview.tsx` (or reuse `GlbViewer.tsx`): compose a Three.js scene from the four selected primitive types using `THREE.SphereGeometry`, `THREE.BoxGeometry`, `THREE.CapsuleGeometry`, `THREE.CylinderGeometry` etc.; each category maps to a named mesh placed at a default position in the scene; update the scene when `builderComponents` store values change
- Enemy config serialization: `builderComponents` must serialize to a JSON shape compatible with the existing enemy config format (`component_types` key) so the spec writer can generate from it

**Tests**
- Backend: `test_builder_component_types.py` — `GET /api/builder/component-types` returns 200 with at least 3 options per category; unknown path returns 404
- Frontend (Vitest): `BuilderPartsPanel.test.tsx` — selecting `box` from the body dropdown calls `setBuilderComponent("body","box")`; all four categories must be assigned for the config to be considered valid (a validity flag is truthy only when none are null)

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
