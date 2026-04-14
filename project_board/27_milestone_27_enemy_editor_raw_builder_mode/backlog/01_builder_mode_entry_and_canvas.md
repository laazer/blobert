Title:
Builder Mode Entry Point & Blank Canvas

Description:
Add a "Build from Scratch" mode toggle that gives the user an empty 3D canvas with no default enemy preloaded. This is the entry point for the raw builder workflow. Users who want full compositional control should not have to deconstruct a preset to start fresh. The mode is tracked independently from preset mode within the editor session.

Acceptance Criteria:
- A "Build from Scratch" button or mode toggle is visible on the editor home or start screen
- Activating it clears any current enemy state and presents an empty 3D viewport
- A parts panel is visible showing available component categories: Body, Head, Arms, Legs
- None of the four categories are pre-populated; the canvas starts empty
- The user can exit back to preset mode; if there are unsaved builder changes, a confirmation prompt is shown before discarding
- Builder mode state is tracked separately from preset mode (switching modes does not corrupt preset config)

Scope Notes:
- No auto-save or draft persistence across page reloads in this ticket
- Undo/redo is out of scope
- Loading a saved config back into builder mode is not required (forward-compat only)
- The confirmation prompt on exit does not need to support named saves

## Web Editor Implementation

**No Python changes required for this ticket** — builder mode state is client-side only at this stage.

**Frontend (`asset_generation/web/frontend/src/`)**
- `store/useAppStore.ts` (Zustand): add `builderModeActive: boolean` and `setBuilderModeActive(active: boolean)` to the store; builder mode state is independent of `commandContext` (preset mode)
- `App.tsx` or the top-level layout: render a "Build from Scratch" button visible on the home/start screen; clicking it sets `builderModeActive: true` and clears active enemy/GLB state
- Create `components/Builder/BuilderCanvas.tsx`: renders when `builderModeActive` is true; shows an empty `GlbViewer` (or a cleared canvas placeholder) and a `BuilderPartsPanel.tsx` sidebar listing the four categories (Body, Head, Arms, Legs) with no parts pre-populated
- `BuilderPartsPanel.tsx`: four category rows, each showing a label and a "Not selected" placeholder; clicking a category opens the type selector (ticket 02)
- An "Exit Builder" button sets `builderModeActive: false`; if any component type has been selected, show a `window.confirm` guard before clearing
- When `builderModeActive` is true, the existing `BuildControls.tsx` panel is hidden

**Tests**
- Frontend (Vitest): `BuilderCanvas.entry.test.tsx` — clicking "Build from Scratch" sets `builderModeActive` to true; `BuilderCanvas` renders with four empty category rows; "Exit Builder" with unsaved state triggers confirm guard; confirming sets `builderModeActive` to false

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
