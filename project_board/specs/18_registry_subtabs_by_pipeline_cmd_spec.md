# Spec: Registry sub-tabs by pipeline `RunCmd` (REGSUB)

**Ticket:** `project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/18_registry_subtabs_by_pipeline_cmd.md`  
**Spec ID prefix:** REGSUB  
**Stage:** SPECIFICATION → TEST_DESIGN  
**Last Updated By:** Spec Agent  
**Date:** 2026-04-11  

**Traceability (ticket acceptance criteria):**

| Ticket AC | Spec coverage |
|-----------|----------------|
| Sub-tab per `RunCmd` in `ALL_CMDS`, labels aligned with command UX | REGSUB-1 |
| Animated tab = enemy registry only; no player block | REGSUB-2 |
| Player tab = player registry only; no enemy tables | REGSUB-3 |
| Level tab = real data or documented empty state | REGSUB-4 |
| Smart / Stats / Test = minimal empty state, no broken API calls | REGSUB-5 |
| Frontend tests: tab switch, mount/unmount | REGSUB-6 |
| `npm test` passes | REGSUB-6, REGSUB-7 |

---

## Background and Context

- **Center panel:** `ThreePanelLayout` exposes **Code / Build / … / Registry** using inline `tabBtn(active)` styles from `asset_generation/web/frontend/src/components/layout/ThreePanelLayout.tsx`.
- **Registry body:** `ModelRegistryPane` (`asset_generation/web/frontend/src/components/Editor/ModelRegistryPane.tsx`) currently renders `RegistryPlayerSection` then `RegistryEnemyFamiliesSection` (plus modals) in one scroll.
- **Command alignment:** `RunCmd` is defined in `asset_generation/web/frontend/src/types/index.ts`. Canonical ordering is `ALL_CMDS` in `asset_generation/web/frontend/src/components/CommandPanel/commandLogic.ts`: `["animated", "player", "level", "smart", "stats", "test"]`.
- **Manifest today:** `ModelRegistryPayload` (`types/index.ts`) has `enemies` and `player_active_visual` only — no level subtree yet; Level tab is empty-state until backend/types extend.

---

## Requirement REGSUB-1: Sub-tab strip source, order, and labels

### 1. Spec Summary

- **Description:** Inside the Registry pane content (below any existing pane chrome, above the main scroll body), render exactly **six** sub-tabs, one per entry in `ALL_CMDS`, in **the same order** as `ALL_CMDS`. Each tab is selectable; exactly one tab is **active** at a time. Default active tab on first visit: **`animated`** (matches typical enemy workflow).
- **Labels:** Visible label text uses **title case** derived from the `RunCmd` token: `animated` → `Animated`, `player` → `Player`, `level` → `Level`, `smart` → `Smart`, `stats` → `Stats`, `test` → `Test`. This matches the ticket’s examples; the command `<select>` may still show lowercase tokens — sub-tabs use the mapping above for readability.
- **Styling:** Sub-tab buttons reuse the same visual recipe as center-panel tabs: the `tabBtn(active: boolean)` object from `ThreePanelLayout.tsx` (import shared style helper or duplicate the same literal style object in one place — no new visual language).
- **Constraints:** Do not add a seventh “All” tab unless a future ticket explicitly requires it; default remains **no** combined view.
- **Assumptions:** `ALL_CMDS` remains the single source of tab count and order; if a cmd is added/removed in TypeScript, tabs follow automatically.
- **Scope:** `ModelRegistryPane` and minimal shared style import; not `CommandPanel` behavior unless needed for label reuse.

### 2. Acceptance Criteria

- **REGSUB-1.1:** Six sub-tabs appear when registry data is loaded and the main registry UI is visible.
- **REGSUB-1.2:** Tab order is `Animated`, `Player`, `Level`, `Smart`, `Stats`, `Test`.
- **REGSUB-1.3:** Clicking a tab updates the active visual state (same affordance as Code/Build/Registry tabs).
- **REGSUB-1.4:** Initial active tab when opening Registry with a fresh session is `Animated`.

### 3. Risk & Ambiguity Analysis

- **Risk:** Duplicating `tabBtn` in two files may drift — prefer a tiny exported helper from `ThreePanelLayout` or a shared `layout/tabStyles.ts` in a follow-up; spec allows either if pixels match.
- **Edge case:** Registry loading/error-only UI — sub-tabs may be hidden until `data` is available, or shown disabled; implementation must not flash wrong content. Prefer: show tabs only when the same conditions today show the full pane (after successful load).

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-2: Animated tab content (enemy registry only)

### 1. Spec Summary

- **Description:** When the **Animated** sub-tab is active, the pane shows the **enemy** registry experience: `RegistryEnemyFamiliesSection` and all flows it already supports (versions, draft/in pool, slots, delete/preview/promote, add-slot modal, etc.). **`RegistryPlayerSection` must not be rendered** in the DOM for this tab (or must be fully unmounted — tests should use query absence, not `display:none` alone unless documented).
- **Load existing (animated):** The ticket calls for load-existing UX scoped to **enemy / animated** allowlist patterns. Today `RegistryPlayerSection` owns the shared `fetchLoadExistingCandidates` wiring and `filterLoadExistingCandidates` / `LoadExistingTypeFilter`. For the Animated tab, surface load-existing **for animated/enemy assets** by reusing those utilities (e.g. filter/type = enemy-only or equivalent) **either** inside `RegistryEnemyFamiliesSection` **or** as a sibling block only on the Animated tab — without duplicating conflicting API calls. At most one `openExistingRegistryModel` flow should be user-visible per tab.
- **Constraints:** No player active visual picker block on this tab.
- **Assumptions:** Existing API contracts (`fetchModelRegistry`, slot endpoints, delete/patch, etc.) unchanged.
- **Scope:** Animated tab subtree only.

### 2. Acceptance Criteria

- **REGSUB-2.1:** With Animated active, `RegistryEnemyFamiliesSection` (or its test id / heading contract used in tests) is present.
- **REGSUB-2.2:** With Animated active, player-only headings/controls from `RegistryPlayerSection` are absent (unless extracted shared subcomponents are purely neutral — default: whole `RegistryPlayerSection` absent).
- **REGSUB-2.3:** Add-slot / delete / slot-save behaviors remain reachable from Animated tab as today.

### 3. Risk & Ambiguity Analysis

- **Risk:** Splitting load-existing may require new UI block on Animated tab — Spec requires reusing `filterLoadExistingCandidates` patterns, not inventing a second backend.
- **Edge case:** `PlayerActiveModelModal` opened from elsewhere — still owned by pane; closing tab while modal open should leave modal behavior defined (prefer: modal remains until closed; no crash).

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-3: Player tab content (player registry only)

### 1. Spec Summary

- **Description:** When the **Player** sub-tab is active, render **`RegistryPlayerSection`** with the same props/wiring as today for player active visual, load-existing, and preview actions. **`RegistryEnemyFamiliesSection` must not be rendered**. Modals that only make sense for player (`PlayerActiveModelModal`) remain functional when invoked from this tab.
- **Constraints:** Enemy family tables and per-family slot tables must not appear above or below the player section.
- **Assumptions:** `AddEnemySlotModal` is not triggered from Player tab UI.
- **Scope:** Player tab subtree.

### 2. Acceptance Criteria

- **REGSUB-3.1:** With Player active, `RegistryPlayerSection` is present.
- **REGSUB-3.2:** With Player active, enemy family table content is absent.
- **REGSUB-3.3:** Player active modal and load-existing actions remain test-covered at least at smoke level (existing tests may be updated for tab prerequisite).

### 3. Risk & Ambiguity Analysis

- **Edge case:** Shared footer note (“Persisted to model_registry.json…”) may appear once per pane or per tab — either is acceptable if not duplicated confusingly twice on screen.

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-4: Level tab (data or empty state)

### 1. Spec Summary

- **Description:** When **Level** is active: if `ModelRegistryPayload` (or a documented extension) exposes level registry rows with a stable TypeScript type and API, render those rows in a table/list consistent with enemy/player density. **As of this spec date, the payload has no `levels` field** — therefore the compliant implementation shows a **non-error empty state**: short copy (1–3 lines) that level registry is not available yet, optional hint to use level pipeline commands, **no fabricated rows**, **no failing fetch** introduced solely for this tab.
- **Constraints:** Empty state must not call undefined endpoints or throw.
- **Assumptions:** If level registry lands mid-implementation, this tab becomes the home for that UI without changing tab count.
- **Scope:** Level tab only.

### 2. Acceptance Criteria

- **REGSUB-4.1:** Level tab renders without runtime errors when selected.
- **REGSUB-4.2:** With current API, user sees only empty-state copy (no mock level entries).
- **REGSUB-4.3:** If level data is later added to the manifest/API, tests must be extended to assert real rows (out of scope until types exist).

### 3. Risk & Ambiguity Analysis

- **Risk:** Parallel backend work — merge coordination per ticket Dependencies.

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-5: Smart, Stats, Test tabs (not applicable)

### 1. Spec Summary

- **Description:** For **Smart**, **Stats**, and **Test** tabs, show a minimal **static** empty state: one or two lines explaining that registry management for that command is not applicable here. **No new registry API calls** when switching to these tabs (no `fetchModelRegistry` duplication beyond the pane’s initial load).
- **Constraints:** No uncaught promise rejections; no red error banners solely because the tab was selected.
- **Assumptions:** Global registry fetch on pane mount may still run once — that is not “per tab.”
- **Scope:** These three tabs.

### 2. Acceptance Criteria

- **REGSUB-5.1:** Selecting Smart, Stats, or Test shows non-empty explanatory text and no enemy/player tables.
- **REGSUB-5.2:** Browser console has no new errors attributable to selecting these tabs in Vitest/jsdom (allow existing app warnings if any).

### 3. Risk & Ambiguity Analysis

- **Edge case:** Strict mode double-mount — empty state must remain idempotent.

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-6: Automated tests (Vitest + RTL)

### 1. Spec Summary

- **Description:** Extend tests under `asset_generation/web/frontend/src/components/Editor/` (alongside existing `ModelRegistryPane*.test.*`) to cover: (a) rendering sub-tabs; (b) switching from **Animated** to **Player** and asserting enemy-specific vs player-specific markers mount/unmount; (c) switching to **Level** / **Smart** (or **Test**) and asserting absence of enemy+player main sections and presence of empty copy.
- **Constraints:** Mock `fetchModelRegistry`, `fetchLoadExistingCandidates`, slot APIs as existing tests do; do not require real backend.
- **Assumptions:** Tests use stable queries (`getByRole`, `data-testid` added sparingly if needed).
- **Scope:** Frontend unit tests only.

### 2. Acceptance Criteria

- **REGSUB-6.1:** At least one test asserts Animated shows enemy section and hides player section.
- **REGSUB-6.2:** At least one test asserts Player shows player section and hides enemy section.
- **REGSUB-6.3:** At least one test asserts a non-applicable tab shows neither main section.
- **REGSUB-6.4:** `cd asset_generation/web/frontend && npm test` exits 0.

### 3. Risk & Ambiguity Analysis

- **Risk:** Flaky timing — use `waitFor` / `findBy*` patterns consistent with existing pane tests.

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-7: Optional `localStorage` persistence (non-blocking)

### 1. Spec Summary

- **Description:** **Optional.** If implemented, persist the selected `RunCmd` sub-tab key under a namespaced key (e.g. `blobert.registry.subtab`) and restore on mount when valid; invalid stored values fall back to default **`animated`**.
- **Constraints:** Must not break SSR/tests (guard `typeof localStorage !== "undefined"`).
- **Assumptions:** Feature is nice-to-have; absence does not block AC closure for ticket 18.
- **Scope:** `ModelRegistryPane` only.

### 2. Acceptance Criteria

- **REGSUB-7.1:** If persistence is shipped, a unit test verifies restore + invalid key fallback **or** manual QA steps documented in PR — otherwise N/A.

### 3. Risk & Ambiguity Analysis

- **Risk:** Cross-tab stale state — acceptable for editor local tool.

### 4. Clarifying Questions

- None.

---

## Requirement REGSUB-8: Shared pane infrastructure

### 1. Spec Summary

- **Description:** Initial registry load, `registryReloadSeq` refresh, error/retry UI, and bottom persistence note remain available regardless of tab **or** are clearly scoped (e.g. error banner above tabs). Prefer: **load once**, show tabs+content after `data` present, same retry as today.
- **Modals:** `AddEnemySlotModal` and `PlayerActiveModelModal` stay children of `ModelRegistryPane` so they can open from Animated/Player tabs respectively.
- **Scope:** Whole pane.

### 2. Acceptance Criteria

- **REGSUB-8.1:** After successful reload, active tab content matches selected tab.
- **REGSUB-8.2:** Retry path after fetch failure still works (existing behavior preserved).

### 3. Risk & Ambiguity Analysis

- None material.

### 4. Clarifying Questions

- None.
