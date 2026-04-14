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

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
