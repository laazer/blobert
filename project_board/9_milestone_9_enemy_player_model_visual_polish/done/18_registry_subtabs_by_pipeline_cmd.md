# TICKET: 18_registry_subtabs_by_pipeline_cmd

Title: Registry tab — sub-tabs per pipeline cmd type (animated / player / level / …)

Project: blobert

Created By: Human

Created On: 2026-04-11

---

## Description

The asset editor **Registry** center panel (`ModelRegistryPane`, opened from `ThreePanelLayout` → **Registry**) currently stacks **player** controls and **all enemy families** in a single long scroll. That mirrors the unified `model_registry.json` file but is hard to scan when many families and draft/slot rows are visible.

Add a **secondary tab strip inside the Registry pane** aligned with pipeline **`RunCmd`** values (same mental model as the Command Panel: `animated`, `player`, `level`, `smart`, `stats`, `test` — see `RunCmd` in `asset_generation/web/frontend/src/types/index.ts` and `ALL_CMDS` in `commandLogic.ts`).

Each cmd tab shows **only** the registry UI that belongs to that surface:

- **animated** — enemy family tables (versions, draft vs in pool, slots, delete/preview/promote flows); **Load existing** filtered or scoped to enemy/animated allowlist paths (reuse existing `LoadExistingTypeFilter` / candidate filtering patterns from `RegistryPlayerSection` where practical).
- **player** — active player visual, player pool/slots if present in manifest, and player-scoped load-existing UX (today `RegistryPlayerSection`).
- **level** — level export registry rows when the manifest and API expose them; if not yet modeled, show a clear empty state (no fake data) and keep layout ready for future rows.
- **smart**, **stats**, **test** — these cmds do not currently own distinct registry subtrees; show a short **empty / not applicable** state (one or two lines) so the tab bar stays consistent with the command dropdown and users are not surprised by missing sections.

Styling should **reuse** existing center-panel tab affordances (`tabBtn` pattern in `ThreePanelLayout.tsx`) so the sub-tabs visually match **Code / Build / Registry** without inventing a new chrome language.

Optional (nice-to-have, not blocking): persist the selected Registry sub-tab in `localStorage` so returning to the editor restores context.

---

## Acceptance Criteria

- Registry pane renders a **sub-tab** for each `RunCmd` in `ALL_CMDS`, with labels consistent with the command panel (e.g. Animated, Player, Level, Smart, Stats, Test).
- **Animated** tab contains the current enemy registry experience (`RegistryEnemyFamiliesSection` and related modals/flows); it does **not** show the player-only block unless product explicitly chooses an “All” tab (default: **no** — player lives under **Player** only).
- **Player** tab contains the current player registry experience (`RegistryPlayerSection`, player active modal, etc.) without enemy family tables above/below it.
- **Level** tab either shows level-specific registry UI wired to real manifest/API data or a documented empty state if level registry is not implemented yet.
- **Smart / Stats / Test** tabs show a minimal non-error empty state (no broken API calls).
- **Frontend tests** cover tab switching and that the correct sections mount or unmount (extend existing `ModelRegistryPane` tests under `asset_generation/web/frontend/src/components/Editor/`).
- `cd asset_generation/web/frontend && npm test` passes.

---

## Dependencies

- None required; coordinate with any in-flight **level** registry work if it lands during implementation (merge order only).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

5

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `npm test` (Vitest) under Node 20 per `asset_generation/web/frontend/.nvmrc`; 207 tests including `ModelRegistryPane.subtabs.test.tsx`, `ModelRegistryPane.subtabs.adversarial.test.tsx`, and updated `ModelRegistryPane.*.test.tsx` for Player tab.
- Static QA: Passing — `npm run build` (`tsc` + `vite build`) in `asset_generation/web/frontend`.
- Integration: N/A — editor-only UI; no new backend routes required.

## AC evidence (gatekeeper)

- **Sub-tab per `ALL_CMDS` + labels:** Implementation iterates `ALL_CMDS` with title-case labels; primary + adversarial tests assert six `role="tab"` names (Animated … Test).
- **Animated = enemy only:** Tests assert `RegistryEnemyFamiliesSection` heading present and `PLAYER_MODEL_SECTION_HEADING` absent on default tab; `RegistryEnemyLoadExistingSection` on Animated.
- **Player = player only:** Test switches to Player tab; enemy headings absent; player open control reachable.
- **Level:** Adversarial test asserts manifest empty copy; no extra `fetchModelRegistry` on tab switch.
- **Smart / Stats / Test:** Primary (Smart) + adversarial (Stats) assert N/A copy; no enemy/player headings.
- **Frontend tests + npm test:** As above; suite green.
- **Optional localStorage:** Implemented (`blobert.registry.subtab`); adversarial test invalid token → fallback Animated.

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
  "ticket_path": "project_board/9_milestone_9_enemy_player_model_visual_polish/done/18_registry_subtabs_by_pipeline_cmd.md"
}
```

## Status

Proceed

## Reason

All acceptance criteria have documented automated or N/A evidence; ticket moved under `done/` per workflow folder rule.
