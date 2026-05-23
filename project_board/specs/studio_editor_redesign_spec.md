# Spec: Asset Editor Studio Redesign (Web Frontend)

**Status:** STUDIO-01 frozen (2026-05-23, spec revision 2); Phases 2–4 deferred per §12  
**Freeze scope:** §6–§9, §10, §12, §14–§16 only  
**Reference prototypes (design-time only):**

| Area | Path |
|------|------|
| Shell / library / inspector tabs (Phase 1) | `bot_vault/asset_generation/redesign_v1/studio.jsx`, `shared.jsx` |
| **Look tab (authoritative)** | `bot_vault/asset_generation/redesign_v2/studio.jsx`, `shared.jsx` |

**Out of scope:** `design-canvas.jsx` (v1 or v2), `Asset Editor Redesign.html` host, Figma HTML exports — presentation only, never shipped.

**Runtime:** `asset_generation/web/frontend` (Vite + React + TypeScript + Zustand).  
**Agent:** Implementation Frontend (`implementation_frontend_v1.md`, `frontend/AGENTS.md`).

---

## 1. Problem statement

The asset editor uses an IDE-shaped layout (VS Code chrome, five center tabs, preview in a side column). Artists need a **Studio** workflow: enemy library on the left, large central GLB preview with animation rail, contextual **inspector** on the right (Look / Build / Animate / Code / Versions). Element type should drive accents across the UI.

The redesign must **not** rewrite business logic or break registry / `build_options` / preview hydration contracts.

---

## 2. Goals and non-goals

### Goals

- Match **layout and IA** from `studio.jsx` (256px | fluid | 360px grid, 52px top bar).
- Implement in **existing frontend style**: TypeScript, named exports, module-level `CSSProperties`, Zustand, Vitest — not a 1:1 port of prototype JS (`window` globals, monolithic file).
- Reuse existing panes: `GlbViewer`, `ColorsPane`, `BuildControls`, `AnimationControls`, `EditorPane`, `Terminal`, registry panels.
- Feature-flag rollout: legacy `ThreePanelLayout` remains default until cutover ticket.
- **Look tab** follows **redesign_v2** IA (part picker → per-part background + pattern fills), not the v1 “Body card + Parts list” layout.

### Non-goals (this program)

- Shipping `DesignCanvas` or any Figma-like tool in production.
- Backend pipeline / Blender changes (except future explicit duplicate API ticket).
- Godot runtime UI.
- Changing Zod pilot shapes without coordinated backend + `schemas.ts` updates.
- Viewport presets (Persp/Top/Side) unless `GlbViewer` already supports them.
- ⌘K palette, onboarding, toasts (Phase 4 — separate tickets).

---

## 3. Conversion contract (prototype → production)

| Prototype pattern | Production pattern |
|-------------------|-------------------|
| `Object.assign(window, …)` | ESM exports from `src/constants/elements.ts`, `src/styles/studioTokens.ts` |
| `useState(SPIDER_VERSIONS)` | Registry data from `useAppStore` + existing registry fetch/handlers |
| Local `look` object | `commandExportFinish` / `commandExportHexColor` / `animatedBuildOptionValues`; `ColorsPane` hydration |
| Inline styles in one file | Module-level `CSSProperties` constants per component (see `RegistryTagChips.tsx`) |
| `Icon.*` Unicode helpers | Text buttons or minimal shared `StudioButton` matching registry modal styles |
| `Critter` / `SpiderImage` placeholders | `GlbViewer` + `/api/assets/...` URLs |
| `compareIds` local state | `compareVersionIds` on `useAppStore` (Phase 3 ticket); not STUDIO-01 |
| Five inspector tabs mounting mocks | Phase 2: wrap real panes; STUDIO-01: shell + placeholders only |

**Fonts:** Plus Jakarta Sans + JetBrains Mono may be added in `index.html` when Studio shell lands; scope to Studio subtree first.

**Element model:** Nine elements from `shared.jsx` (`fire`, `ice`, `poison`, `acid`, `earth`, `forest`, `water`, `lightning`, `physical`) with `{ name, hue, soft, ink, glyph }` — glyphs optional in production UI.

---

## 4. Target layout (1440×900 reference)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Top bar: logo · breadcrumb (family / version) · badges · ⌘K · Save · Regen │
├──────────────┬──────────────────────────────────────────┬───────────────────┤
│ Enemy library│ Center: preview (hero)                   │ Inspector tabs    │
│ Enemies/     │         GlbViewer + chips                │ Look|Build|…      │
│ Player/Level │ Animation rail (96px) — clips/scrub      │ Tab content       │
│ Family list  │ Compare grid when ≥2 ids (Phase 3)       │                   │
│ 256px        │ fluid                                    │ 360px             │
└──────────────┴──────────────────────────────────────────┴───────────────────┘
```

**Top bar (STUDIO-01):** Structural placeholders OK; wire Save/Regenerate to no-op or existing `CommandPanel` handlers only if trivial — otherwise defer to Phase 2.

**Left rail (STUDIO-01):** `EnemyLibrary` placeholder with landmark labels; no registry wiring required in STUDIO-01.

**Center (STUDIO-01):** Mount existing `PreviewSourceBar` + `GlbViewer` + `AnimationControls` only (preview hero + animation rail). **Do not** mount `CommandPanel` or `Terminal` in the Studio center column in Phase 1 — those remain on legacy `ThreePanelLayout` until a later ticket explicitly relocates them (see §12).

**Right (STUDIO-01):** `StudioInspector` with tabs `Look | Build | Animate | Code | Versions`; active tab state in React local state or store; tab bodies = placeholder text except none required to mount real panes yet.

---

## 5. Phased delivery

| Phase | Ticket | Summary |
|-------|--------|---------|
| **1** | **STUDIO-01** | Shell, tokens, `elements.ts`, feature flag, preview in center, inspector placeholders |
| 2 | STUDIO-02 | `EnemyLibrary` + `Inspector` wrapping real `ColorsPane` / `BuildControls` / etc. |
| 3 | STUDIO-03 | Versions list UX, `compareVersionIds`, `GlbCompareGrid`, duplicate API |
| 4 | STUDIO-04 | ⌘K, shortcuts, polish |

This spec **freezes Phase 1** only. Phases 2–4 are **deferred** (see §12).

---

## 6. STUDIO-01 functional requirements

### FR-1 Feature flag

- When `import.meta.env.VITE_STUDIO_LAYOUT` is not exactly `"1"` (and no documented dev override), `App.tsx` renders **`ThreePanelLayout`** unchanged.
- When `"1"`, render **`StudioLayout`** instead.
- `ThreePanelLayout` root exposes `data-testid="legacy-layout"` when flag is off (implementation STUDIO-01).
- No change to default env in repo (flag off in CI and local default).

### FR-2 Design tokens

- `src/constants/elements.ts`: typed `ElementId` and `ELEMENTS` record (hue, soft, ink; glyph optional).
- `src/styles/studioTokens.ts`: studio surfaces (`#0c0c10`, `#0e0e14`, `#16161d`), ink (`#ededf0`, `#bababf`, `#7a7a86`), layout widths (256, 360), top bar height 52.
- Export helpers e.g. `studioInspectorTabStyle(active: boolean, elementHue?: string): CSSProperties` — pattern mirrors `centerPanelTabStyles.ts`.

### FR-3 StudioLayout grid

- CSS grid: columns `256px 1fr 360px`, rows `52px 1fr`, full viewport height, overflow hidden.
- Subcomponents (minimum): `StudioTopBar`, `EnemyLibraryPlaceholder`, `StudioPreviewColumn`, `StudioInspector`.
- File layout under `src/components/layout/` and `src/components/studio/` per team convention.

### FR-4 Preview column parity

- `StudioPreviewColumn` includes `PreviewSourceBar`, `GlbViewer`, collapsible `AnimationControls` consistent with `ThreePanelLayout` preview stack (reuse `usePersistedBoolean` keys where applicable).
- **Excluded from `StudioPreviewColumn` (Phase 1):** `CommandPanel`, `Terminal`, and any center-column Code/Build/Registry tab strip from `ThreePanelLayout` — Studio center is preview + animation rail only.
- `data-testid="studio-preview-column"` on the preview column root.
- Selecting assets / preview URLs uses **existing** store paths only; no new hydration in STUDIO-01.

### FR-5 Inspector shell

- Five tabs; clicking changes visible placeholder panel (`data-testid={`studio-inspector-tab-${tab}`}`).
- Active tab underline may use `commandContext` element hue when available, else neutral accent.

### FR-6 Store compatibility

- Do **not** remove or rename `centerPanel` / `setCenterPanel` in STUDIO-01.
- Do **not** call `selectAssetByPath` with `importBuildOptions: true` from new layout code.

---

## 7. Non-functional requirements

- **NFR-1:** `cd asset_generation/web/frontend && npx tsc --noEmit` passes.
- **NFR-2:** `npm test -- --run` passes; new tests colocated (`StudioLayout.test.tsx`).
- **NFR-3:** No new pilot Zod schemas unless backend changes (none expected STUDIO-01).
- **NFR-4:** `data-testid` on flag switch surfaces: `studio-layout`, `legacy-layout`, inspector tabs.
- **NFR-5:** No `as any` / `@ts-ignore`.

---

## 8. Test plan (STUDIO-01)

| ID | Behavior |
|----|----------|
| T-1 | Flag off → `legacy-layout` present; `studio-layout` absent |
| T-2 | Flag on → `studio-layout` and `studio-preview-column` present; preview stack mounted (mock `GlbViewer` per `ThreePanelLayout.*.test.tsx`) |
| T-3 | Inspector tab switch updates active tab test id / aria state without throw |
| T-4 | `elements.ts` exports all nine element ids with `hue`, `soft`, `ink` strings |
| T-5 | Mock store: mounting `StudioLayout` / `StudioPreviewColumn` does not invoke `selectAssetByPath` with `importBuildOptions: true` |
| T-6 | Flag on → `command-panel` and terminal region test ids **absent** from Studio subtree (Phase 1 center omission) |

Use `@vitest-environment jsdom`, `vi.mock` on `useAppStore` per existing layout tests.

---

## 9. File map (STUDIO-01)

| File | Action |
|------|--------|
| `src/App.tsx` | Branch on `VITE_STUDIO_LAYOUT` |
| `src/constants/elements.ts` | New |
| `src/styles/studioTokens.ts` | New |
| `src/components/layout/StudioLayout.tsx` | New |
| `src/components/studio/StudioTopBar.tsx` | New |
| `src/components/studio/EnemyLibraryPlaceholder.tsx` | New |
| `src/components/studio/StudioPreviewColumn.tsx` | New |
| `src/components/studio/StudioInspector.tsx` | New |
| `src/components/layout/StudioLayout.test.tsx` | New |
| `.env.example` or `frontend/README.md` | Document `VITE_STUDIO_LAYOUT=1` (one line) |

---

## 10. Hydration and registry (invariants)

All Studio work must preserve:

- Preview-only `selectAssetByPath` (see `project_board/bugfix/in_progress/model-load-ui-settings.md` / REQ-1).
- Registry `build_options` hydration via explicit import or sidecar rules in `glbBuildOptionsHydration.ts`.
- Dual validation on pilot GETs unchanged in STUDIO-01.

---

## 11. Failure taxonomy

| Condition | Expected behavior |
|-----------|-------------------|
| Meta API down | Studio preview column degrades same as legacy (offline build controls) |
| Invalid flag value | Treat as off (legacy layout) |
| Missing WebGL | `GlbViewer` existing error UI |

---

## 12. Deferred boundary statement

**In scope for STUDIO-01 only:** §6–§9.

**Deferred to STUDIO-02+:**

- `CommandPanel` and `Terminal` in Studio layout (any column); legacy center column retains them until then.
- Wiring `ColorsPane` (v2 Look: `PartPicker`, `FillSection` for color/gradient/image), `BuildControls`, `ExtrasPane`, `ModelRegistryPane` into inspector tabs.
- `EnemyLibrary` connected to registry families.
- `compareVersionIds`, `GlbCompareGrid`, duplicate version API.
- Top bar Regenerate/Save fully styled and wired.
- Default cutover (`VITE_STUDIO_LAYOUT` default on).
- Migration from `centerPanel` to `inspectorTab` persistence.

---

## 13. Open questions (defaults for STUDIO-01)

| Question | Default |
|----------|---------|
| Extras in Look vs separate sub-nav? | Defer; placeholder tab labels only in STUDIO-01 |
| Fire spider as test fixture? | Use generic store mocks; no spider-specific assets in tests |
| Fonts in STUDIO-01? | Optional; Segoe/system stack acceptable until Phase 2 |

---

## 14. Acceptance Criteria (STUDIO-01)

- **AC-1:** With `VITE_STUDIO_LAYOUT` unset or not `"1"`, `App` renders legacy `ThreePanelLayout` (`data-testid="legacy-layout"`); no layout regression.
- **AC-2:** With `VITE_STUDIO_LAYOUT=1`, `StudioLayout` renders grid `256px 1fr 360px` and `data-testid="studio-layout"`.
- **AC-3:** `src/constants/elements.ts` defines all nine element ids with `hue`, `soft`, `ink` strings.
- **AC-4:** Studio center mounts `PreviewSourceBar`, `GlbViewer`, `AnimationControls` with same store integration as legacy preview stack; **no** `CommandPanel` or `Terminal`.
- **AC-5:** `StudioInspector` exposes five tabs with placeholders and `data-testid` hooks; no full `ColorsPane` / registry required.
- **AC-6:** Vitest in `StudioLayout.test.tsx` covers flag off/on, inspector tab switch, no `importBuildOptions: true` on Studio mount.
- **AC-7:** `npx tsc --noEmit` and `npm test -- --run` pass in `asset_generation/web/frontend`.

Traceability: §15. Ticket source: `STUDIO-01_studio_shell_tokens.md`.

---

## 15. STUDIO-01 traceability (FR ↔ AC ↔ T)

| FR | Ticket AC | Test ID | Notes |
|----|-----------|---------|-------|
| FR-1 | AC-1, AC-2 | T-1, T-2 | Invalid env → legacy (§11) |
| FR-2 | AC-3 | T-4 | Nine elements from `shared.jsx` |
| FR-3 | AC-2 | T-1, T-2 | Grid `256px 1fr 360px`, `studio-layout` |
| FR-4 | AC-4 | T-2, T-5, T-6 | No CommandPanel/Terminal in center |
| FR-5 | AC-5 | T-3 | Placeholder tab bodies only |
| FR-6 | AC-6 (hydration) | T-5 | `centerPanel` unchanged |
| NFR-1..5 | AC-7 | — | `tsc` + `npm test` |

---

## 16. STUDIO-01 freeze record

| Field | Value |
|-------|-------|
| Frozen | 2026-05-23 |
| Spec revision | 2 (STUDIO-01 slice) |
| Authoritative sections | §6–§9, §10, §12, §14–§16 |
| Phase 1 center column | `PreviewSourceBar` + `GlbViewer` + `AnimationControls` only — **no** `CommandPanel`, **no** `Terminal` |
| Checkpoint | `project_board/checkpoints/STUDIO-01/2026-05-23T-spec-run.md` |
