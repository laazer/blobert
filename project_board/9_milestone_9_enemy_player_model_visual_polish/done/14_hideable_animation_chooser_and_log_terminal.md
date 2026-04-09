# TICKET: 14_hideable_animation_chooser_and_log_terminal

Title: Asset editor — hideable animation chooser and log / report (terminal) panes

## Description

The right column in `asset_generation/web/frontend/src/components/layout/ThreePanelLayout.tsx` stacks **preview** (`PreviewSourceBar`, `GlbViewer`), **`AnimationControls`** (animation chooser), **`CommandPanel`**, and **`Terminal`** (streaming log / run output). On smaller viewports or when focusing on the 3D viewport and commands, **AnimationControls** and **Terminal** consume vertical space with no way to collapse them.

Add **independent hide/show toggles** (or a compact collapse affordance) for:

1. **Animation chooser** — `AnimationControls` component (`asset_generation/web/frontend/src/components/Preview/AnimationControls.tsx`).
2. **Log / report pane** — `Terminal` component (`asset_generation/web/frontend/src/components/Terminal/Terminal.tsx`).

Behavior should mirror existing editor patterns where possible (e.g. center panel **Hide** / vertical tab strip): clear button or chevron, accessible name (`aria-expanded` / `aria-controls` or equivalent), and **hidden panes must not steal keyboard focus** when collapsed.

**Optional (spec in ticket revision):** persist visibility in `localStorage` under a namespaced key so reloads keep user preference.

## Acceptance Criteria

- User can **hide** and **show** the animation chooser without hiding the GLB viewer or command panel.
- User can **hide** and **show** the terminal / log pane without hiding the command panel; when hidden, streamed output behavior is unchanged (buffer or discard policy documented — default: keep buffering in store so showing again reveals recent lines, matching current mental model).
- Layout does not leave dead flex gaps when collapsed (viewport expands sensibly for `GlbViewer` / command area).
- Frontend test(s): at least one RTL test proving toggle changes visibility and labels/roles are stable (`asset_generation/web/frontend` `npm test`).
- `npm run build` passes.

## Dependencies

- None (pure frontend UX).

## Execution plan

1. Add UI chrome (e.g. per-section header row with collapse) in `ThreePanelLayout.tsx` or inside `AnimationControls` / `Terminal` — pick the approach with least duplication.
2. State: `useState` in layout or extend `useAppStore` if persistence or cross-component sync is required.
3. Tests + visual spot-check at narrow window height.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
1

## Last Updated By
Autopilot / implementation handoff

## Validation Status

- Tests: `npm test` (167 passed including `ThreePanelLayout.preview_collapse.test.tsx`, `usePersistedBoolean.test.ts`); `npm run build`; `timeout 300 ci/scripts/run_tests.sh` exit 0.
- A11y: section toggles use `aria-expanded` / `aria-controls`; collapsed panels unmounted (no focusable controls inside).
- Persistence: `blobert.editor.preview.animationExpanded` / `terminalExpanded` in localStorage (`1`/`0`).

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
{}
```

## Status
Proceed

## Reason

Collapsible Animations + Log sections in `ThreePanelLayout`, `usePersistedBoolean`, Terminal `scrollIntoView` guard for jsdom, RTL tests + build green.
