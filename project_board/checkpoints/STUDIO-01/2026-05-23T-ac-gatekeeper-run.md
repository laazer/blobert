# STUDIO-01 AC Gatekeeper Run — 2026-05-23

**Run id:** `2026-05-23T-ac-gatekeeper-run`  
**Ticket:** `project_board/43_milestone_43_studio_editor_redesign/in_progress/STUDIO-01_studio_shell_tokens.md`  
**Verdict:** **NOT COMPLETE** — held at `INTEGRATION`

---

## Acceptance criteria matrix

| AC | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| AC-1 | Legacy `ThreePanelLayout` when flag off; no regression | `StudioLayout.test.tsx` T-1 + §11 invalid flags; `ThreePanelLayout.preview_collapse` 3/3; `ThreePanelLayout.extras_tab` 1/1 (gatekeeper re-run) | **Met** (scoped) |
| AC-2 | `VITE_STUDIO_LAYOUT=1` → grid `256px 1fr 360px`, `data-testid="studio-layout"` | `studioTokens.ts` (`STUDIO_LIBRARY_WIDTH_PX=256`, `STUDIO_INSPECTOR_WIDTH_PX=360`); T-2 tests | **Met** |
| AC-3 | Nine element ids with `hue`, `soft`, `ink` | `src/constants/elements.ts`; T-4 tests | **Met** |
| AC-4 | Center: `PreviewSourceBar`, `GlbViewer`, `AnimationControls`; same store keys | `StudioPreviewColumn.tsx`; T-2, T-6; no CommandPanel/Terminal in studio subtree | **Met** |
| AC-5 | `StudioInspector` five tabs + placeholders + testids | `StudioInspector.tsx`; T-3 tests | **Met** |
| AC-6 | Vitest: flag off/on, tabs, no `importBuildOptions: true` on Studio mount | `StudioLayout.test.tsx` 34/34 (T-1..T-6, adversarial) | **Met** |
| AC-7 | `tsc --noEmit` and `npm test -- --run` pass | `tsc` exit 0; **full suite FAIL** (see below) | **Not met** |

**Spec traceability:** `project_board/specs/studio_editor_redesign_spec.md` §6–§9 FR/NFR/T map to AC-1..AC-7; implementation matches §11 strict `"1"` flag (`studioLayoutFlag.ts`).

---

## Commands (gatekeeper re-run)

```bash
cd asset_generation/web/frontend && npx tsc --noEmit
# exit 0

npm test -- --run src/components/layout/StudioLayout.test.tsx
# Tests  34 passed (34)

npm test -- --run src/components/layout/ThreePanelLayout.preview_collapse.test.tsx src/components/layout/ThreePanelLayout.extras_tab.test.tsx
# Tests  4 passed (4)

npm test -- --run
# Test Files  3 failed | 82 passed (85)
# Tests  14 failed | 835 passed (849)
```

### Full-suite failures (AC-7 blocker; not STUDIO-01 files)

- `src/components/Preview/BuildControlRow.concurrency.test.tsx` (9)
- `src/components/Preview/BuildControls.texture.test.tsx` (1)
- `src/components/ColorPicker/modes/ImageMode.test.tsx` (4)

Example tail (`ImageMode.test.tsx`):

```
expect(onFileChange).toHaveBeenCalledWith(pngFile, "blob:mock-url"…
Received: Array [ File {}, "blob:mock-url", undefined, null ]
```

---

## Git / workflow enforcement

Per `workflow_enforcement_v1.md` **Commit and Push BEFORE COMPLETE**:

- STUDIO-01 implementation paths largely **uncommitted** (`StudioLayout.tsx`, `src/components/studio/`, `src/constants/`, `src/styles/`, `studioLayoutFlag.ts`, `vite-env.d.ts`, etc.).
- Branch working tree includes additional unrelated frontend modifications outside STUDIO-01 scope.
- **Cannot** set Stage `COMPLETE` or move ticket to `done/` until AC-7 green, STUDIO-01 work committed, and `git push` succeeds.

---

## Routing

- **Stage:** `INTEGRATION` (not `BLOCKED` — STUDIO-01 deliverables and scoped tests are green; gaps are full-suite + git closure).
- **Next agent:** `Human` (or Static QA to fix suite / confirm pre-existing failures on branch).
