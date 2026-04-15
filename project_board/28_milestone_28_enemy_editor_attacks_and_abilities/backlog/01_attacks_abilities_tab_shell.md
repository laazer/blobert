Title:
Attacks/Abilities Tab Entry & Workspace Shell

Description:
Add a new top-level "Attacks / Abilities" tab in the web editor with a two-pane workspace: reusable ability models on the left and attack definitions on the right. This tab must have independent state from existing visual/animation/builder tabs so users can author combat data without polluting other editor contexts.

Acceptance Criteria:
- A new "Attacks / Abilities" tab is visible in the primary editor navigation
- Entering the tab renders two labeled panes: "Ability Models" and "Attacks"
- Leaving and returning to the tab preserves unsaved local form state for the current session
- Existing tabs (Visual, Animation, Builder) continue to function with no regression in selected state
- If the user attempts to leave with dirty changes, a confirmation prompt appears before discarding
- Keyboard focus order across controls in the tab is logical and accessible

Scope Notes:
- No final API persistence in this ticket; this is shell/state scaffolding only
- No drag-and-drop reordering in pane lists
- No in-tab 3D runtime combat playback preview
- Dirty-state prompt can use `window.confirm` in this milestone

## Web Editor Implementation

**No Python or backend changes required for this ticket** — UI shell and store isolation only.

**Frontend (`asset_generation/web/frontend/src/`)**
- `App.tsx` and/or top-level navigation: add an "Attacks / Abilities" tab route or mode selector
- `store/useAppStore.ts`: add `attacksTabState` slice (active subpanel, selected ability ID, selected attack ID, dirty flags) isolated from builder/preset slices
- Create `components/AttacksAbilities/AttacksAbilitiesWorkspace.tsx`: parent layout containing left and right panes plus toolbar row
- Create `components/AttacksAbilities/AbilityModelsPane.tsx` and `components/AttacksAbilities/AttacksPane.tsx` placeholders with empty-state messaging and list containers
- Add leave-guard behavior when `attacksTabState.isDirty` is true and user attempts to switch tabs

**Tests**
- Frontend (Vitest): `AttacksAbilitiesTabShell.test.tsx` — tab appears, entering renders two panes, switching away with dirty state triggers confirm, confirming discard clears the local slice

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0

- **Stage:** BACKLOG
- **Revision:** 0
