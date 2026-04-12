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

COMPLETE

## Revision

5

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `npm test` under Node 20; `GlbViewer.test.tsx` covers toggle on wrapper, `aria-pressed`, Escape-equivalent `fullscreenchange` when `fullscreenElement` clears, and disabled + tooltip when `fullscreenEnabled === false`.
- Static QA: Passing — `npm run build` (`tsc` + `vite build`) in `asset_generation/web/frontend`.
- Integration: N/A — browser Fullscreen API; automated suite uses jsdom mocks. **OrbitControls / canvas sizing:** implementation dispatches `resize` after `fullscreenchange` so R3F can reflow; manual orbit smoke still recommended before release if policy requires it.

## AC evidence (gatekeeper)

- **Control visible (empty + loaded):** `GlbViewer` always renders the control on the root wrapper; empty and loaded branches share the same outer `div` (verified in code review path).
- **Exit via control + Escape:** Toggle covered by tests; Escape native behavior mirrored by test that clears `fullscreenElement` and fires `fullscreenchange` → UI returns to “Enter fullscreen”.
- **OrbitControls usable:** Contract = `fullscreenchange` → `window` `resize` dispatch; no automated WebGL drag test in CI.
- **Accessibility:** Tests assert `aria-pressed` and enter/exit names; native `<button>` focusable.
- **Vitest mocks + npm test:** `GlbViewer.test.tsx` as above; full frontend suite green.

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{
  "ticket_path": "project_board/9_milestone_9_enemy_player_model_visual_polish/done/19_model_viewer_fullscreen_button.md"
}
```

## Status

Proceed

## Reason

All acceptance criteria have test-backed or documented implementation evidence; ticket moved under `done/`.
