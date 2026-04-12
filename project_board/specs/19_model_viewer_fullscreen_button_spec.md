# Spec: GLB viewer element fullscreen (GLBFS)

**Ticket:** `project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/19_model_viewer_fullscreen_button.md`  
**Spec ID prefix:** GLBFS  
**Stage:** SPECIFICATION → TEST_DESIGN  
**Last Updated By:** Spec Agent  
**Date:** 2026-04-11  

**Traceability (ticket acceptance criteria):**

| Ticket AC | Spec coverage |
|-----------|----------------|
| Enter fullscreen control visible loaded + empty | GLBFS-1 |
| Exit via control + Escape | GLBFS-2 |
| Canvas / OrbitControls usable after enter/exit | GLBFS-3 |
| Accessibility | GLBFS-4 |
| Vitest mocks fullscreen APIs | GLBFS-5 |
| `npm test` passes | GLBFS-5 |

---

## Background and Context

- **Component:** `GlbViewer` in `asset_generation/web/frontend/src/components/Preview/GlbViewer.tsx`.
- **Layout:** Root is a `div` with `flex: 1`, `position: "relative"`, `overflow: "hidden"`. Empty state is an inner placeholder `div`; loaded state wraps `@react-three/fiber` `Canvas` with `OrbitControls`, lights, grid.
- **Parent:** `PreviewSourceBar` sits in `ThreePanelLayout` **above** `GlbViewer` in the preview column — **not** inside `GlbViewer`’s root `div`.
- **API:** Standard Fullscreen API: `Element.requestFullscreen()` / `document.exitFullscreen()`; `document.fullscreenElement`; `fullscreenchange` event on `document`.

---

## Requirement GLBFS-1: Control placement and visibility

### 1. Spec Summary

- **Description:** Add a single **primary control** (icon button or text button) on the **viewer chrome**: overlaid on the `GlbViewer` root `div` (e.g. top-right corner, `position: absolute`, high `z-index`) so it does not affect flex layout of the canvas. The control is visible when **no model** is loaded (empty placeholder) and when a **model is loaded** (Canvas visible). Clicking attempts to enter or exit fullscreen per GLBFS-2.
- **Fullscreen target:** The **element** passed to `requestFullscreen()` is the **`GlbViewer` outer wrapper** (the `position: "relative"` root `div` that contains either the empty state or the Canvas). This **excludes** `PreviewSourceBar` and the rest of the app — viewport-only fullscreen.
- **Constraints:** Do not fullscreen `document.documentElement` or `#root` by default.
- **Assumptions:** Control remains visible in fullscreen (inside the fullscreen element) so user can exit without relying only on Escape.
- **Scope:** `GlbViewer.tsx` only unless a one-line wrapper in layout is unavoidable (prefer keeping logic in `GlbViewer`).

### 2. Acceptance Criteria

- **GLBFS-1.1:** With `activeGlbUrl == null`, the fullscreen control is visible and keyboard-focusable.
- **GLBFS-1.2:** With `activeGlbUrl` set, the fullscreen control remains visible over the canvas area.
- **GLBFS-1.3:** Fullscreen element is the `GlbViewer` root wrapper, verified in tests via mock call target.

### 3. Risk & Ambiguity Analysis

- **Risk:** `z-index` below canvas — ensure button stacks above R3F canvas in the same stacking context.

### 4. Clarifying Questions

- None.

---

## Requirement GLBFS-2: Enter, exit, and Escape

### 1. Spec Summary

- **Description:** The control **toggles** fullscreen: if `document.fullscreenElement !== target`, call `target.requestFullscreen()` (optionally with `{ navigationUI: "hide" }` where supported); if already fullscreen on `target`, call `document.exitFullscreen()`. **Escape** key exits fullscreen via **browser default** — no custom key handler required for Escape; implementation must **listen** to `fullscreenchange` to sync React state (`isFullscreen`) when user presses Escape.
- **Constraints:** Handle `requestFullscreen` returning a Promise — rejections must not surface as unhandled rejections in normal unsupported case (see GLBFS-6).
- **Assumptions:** Standard desktop browsers; iOS Safari quirks handled by disable path (GLBFS-6).
- **Scope:** `GlbViewer` + document listeners.

### 2. Acceptance Criteria

- **GLBFS-2.1:** Click when not fullscreen invokes `requestFullscreen` on the viewer wrapper (mocked in test).
- **GLBFS-2.2:** Click when fullscreen invokes `exitFullscreen` (mocked).
- **GLBFS-2.3:** When tests simulate `fullscreenchange` clearing fullscreen, UI updates to “enter” state without extra click.

### 3. Risk & Ambiguity Analysis

- **Edge case:** Fullscreen another element elsewhere in app — `fullscreenchange` should only treat “our” element as active when `document.fullscreenElement === ref.current`.

### 4. Clarifying Questions

- None.

---

## Requirement GLBFS-3: Resize and OrbitControls after fullscreen

### 1. Spec Summary

- **Description:** On `fullscreenchange`, ensure the R3F canvas receives layout updates: rely on browser resize + `Canvas` resize handling **or** explicitly call `gl.setSize` / invalidate via `@react-three/fiber` patterns if needed. **Observable:** after exit, orbit drag still rotates model; after enter, model fills the fullscreen region. No stuck zero-size canvas in manual QA.
- **PreviewSourceBar:** Remains **outside** fullscreen subtree; in fullscreen it is **hidden** from view (because only `GlbViewer` is fullscreen — the bar stays on the underlying page). No requirement to duplicate the bar inside fullscreen.
- **Constraints:** Avoid forcing full page reload.
- **Assumptions:** `ResizeObserver` or default ThreeFiber resize on window `resize` is sufficient if `fullscreenchange` fires — if not, attach `fullscreenchange` listener that triggers canvas resize/invalidate.
- **Scope:** `GlbViewer` and R3F canvas subtree.

### 2. Acceptance Criteria

- **GLBFS-3.1:** Implementation registers `fullscreenchange` (on `document`) and cleans up on unmount.
- **GLBFS-3.2:** Manual QA checklist in PR or test that after toggle, canvas `width`/`height` attributes or client rects are non-zero (optional jsdom smoke).

### 3. Risk & Ambiguity Analysis

- **Risk:** WebGL DPR changes — acceptable if visual is correct in Chrome/Firefox manual pass.

### 4. Clarifying Questions

- None.

---

## Requirement GLBFS-4: Accessibility

### 1. Spec Summary

- **Description:** The control is a native `<button type="button">` (or equivalent with full keyboard support). Provide **distinct accessible names** for enter vs exit states, e.g. `aria-label="Enter fullscreen"` vs `aria-label="Exit fullscreen"`, **or** `aria-pressed={true|false}` with a single name `Fullscreen` — pick one pattern and apply consistently. Focus ring must remain visible with default or theme styles.
- **Constraints:** Must not rely on color alone for state.
- **Assumptions:** Screen reader reads updated label on toggle.
- **Scope:** Fullscreen button only.

### 2. Acceptance Criteria

- **GLBFS-4.1:** Button is focusable via Tab.
- **GLBFS-4.2:** Tests assert `aria-pressed` **or** distinct `aria-label`/`name` between states.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement GLBFS-5: Unit tests (Vitest + RTL)

### 1. Spec Summary

- **Description:** Add or extend tests colocated with `GlbViewer` (e.g. `GlbViewer.test.tsx`). Mock `HTMLElement.prototype.requestFullscreen` and `document.exitFullscreen` as `vi.fn()` resolving Promises. Mock `document.fullscreenEnabled` as `true` when testing enabled path. Assert: first click calls `requestFullscreen` with `this ===` the viewer container; simulate entering fullscreen by setting mock `document.fullscreenElement` and dispatching `fullscreenchange`; second click calls `exitFullscreen`.
- **Constraints:** Do not require real WebGL or canvas rendering for the contract test.
- **Scope:** Frontend tests only.

### 2. Acceptance Criteria

- **GLBFS-5.1:** At least one test covers toggle API calls with mocks.
- **GLBFS-5.2:** `cd asset_generation/web/frontend && npm test` exits 0.

### 3. Risk & Ambiguity Analysis

- **Risk:** jsdom lacks Fullscreen — mocks are mandatory.

### 4. Clarifying Questions

- None.

---

## Requirement GLBFS-6: Unsupported fullscreen

### 1. Spec Summary

- **Description:** When fullscreen is not available (`document.fullscreenEnabled === false` **or** `requestFullscreen` missing on the element prototype), the button is **disabled** **or** visible but no-op **without** throwing and **without** `console.error` from this feature. Provide `title` tooltip e.g. “Fullscreen not supported” when disabled/no-op.
- **Constraints:** No unhandled promise rejections on click in unsupported mode.
- **Assumptions:** Feature detection runs after mount (client-only).
- **Scope:** `GlbViewer`.

### 2. Acceptance Criteria

- **GLBFS-6.1:** Test or documented manual case: with `fullscreenEnabled: false`, click does not call `requestFullscreen` (or calls guarded path that no-ops silently).

### 3. Risk & Ambiguity Analysis

- **Edge case:** `fullscreenEnabled` true but `requestFullscreen` rejects — treat as unsupported for that session (disable or show tooltip once).

### 4. Clarifying Questions

- None.

---

## Requirement GLBFS-7: Out of scope

### 1. Spec Summary

- **Description:** Browser-chrome F11 “real” fullscreen, iOS non-standard video fullscreen, and fullscreen of the entire editor shell are **out of scope**.
- **Scope:** N/A

### 2. Acceptance Criteria

- N/A

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.
