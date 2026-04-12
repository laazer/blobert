# TICKET: 19_model_viewer_fullscreen_button

Title: Asset editor — fullscreen control for the 3D model viewer

Project: blobert

Created By: Human

Created On: 2026-04-11

---

## Description

The asset editor’s **GLB preview** is rendered by `GlbViewer` (`asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx`) inside the right-hand preview column of `ThreePanelLayout` (below `PreviewSourceBar`). On smaller displays or when reviewing silhouette/material detail, users need a **one-click fullscreen** path without leaving the editor.

Add a **fullscreen** affordance (icon or labeled button) on or adjacent to the viewer chrome so the **3D viewport** can occupy the entire display using the browser **Fullscreen API** (`element.requestFullscreen()` / `document.exitFullscreen()`), with **Escape** exiting fullscreen per browser default.

**Scope decisions (implementation time):**

- Target element should be the **viewer wrapper** that contains the R3F `Canvas` (the outer `position: "relative"` div in `GlbViewer`, or a thin parent if the control must sit outside the canvas). Fullscreen should **not** accidentally include the whole app unless product prefers that — default is **viewport-only** for focus on the model.
- **PreviewSourceBar** can remain above the canvas in normal layout; in fullscreen, either include it in the fullscreen subtree (if users still need path/source context) or hide it — pick the simpler behavior that keeps **orbit controls + lighting** correct after resize (listen for `fullscreenchange` and let the canvas reflow).
- Handle **unsupported** fullscreen (older browsers): disable the button or no-op with a short `title` tooltip; no console errors.

Optional: mirror **F11**-style is out of scope (browser chrome); stick to element fullscreen.

---

## Acceptance Criteria

- Visible **Enter fullscreen** control when a model is loaded and when empty (empty state may still fullscreen the dark placeholder — acceptable).
- **Exit fullscreen** via the same control (toggle) and via **Escape** (native).
- Canvas / `OrbitControls` remain usable after enter and exit (no stuck dimensions — verify resize or `fullscreenchange` handling).
- **Accessibility:** button has `aria-pressed` or distinct labels for enter vs exit; keyboard focusable.
- **Tests:** at least one frontend test (e.g. Vitest + RTL) that mocks `requestFullscreen` / `exitFullscreen` on the container and asserts the toggle calls the API; `cd asset_generation/web/frontend && npm test` passes.

---

## Dependencies

- None

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

PLANNING

## Revision

1

## Last Updated By

Human

## Validation Status

- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent

Planner

## Required Input Schema

```json
{}
```

## Status

Proceed

## Reason

Straightforward UI task in the existing React preview stack; no backend changes expected.
