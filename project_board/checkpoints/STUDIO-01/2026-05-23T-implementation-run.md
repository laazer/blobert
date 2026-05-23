# STUDIO-01 Implementation Run — 2026-05-23

**Run id:** `2026-05-23T-implementation-run`  
**Ticket:** `project_board/43_milestone_43_studio_editor_redesign/in_progress/STUDIO-01_studio_shell_tokens.md`  
**Stage:** IMPLEMENTATION_FRONTEND → STATIC_QA (ticket not COMPLETE)

---

## Outcome

- Phase 1 Studio shell: `elements.ts`, `studioTokens.ts`, `StudioLayout` + `studio/*` components, `App.tsx` flag branch (`VITE_STUDIO_LAYOUT === "1"` only).
- Legacy `ThreePanelLayout` retains `data-testid="legacy-layout"`; studio grid `256px 1fr 360px`, preview column reuses `PreviewSourceBar` / `GlbViewer` / `AnimationControls` with `blobert.editor.preview.animationExpanded` key.
- Documented flag in `asset_generation/web/frontend/README.md`; added `src/vite-env.d.ts` for `ImportMeta.env`.

---

## Test Evidence

```bash
cd asset_generation/web/frontend && npm test -- --run src/components/layout/StudioLayout.test.tsx
# Test Files  1 passed (1)
# Tests  34 passed (34)

npm test -- --run src/components/layout/ThreePanelLayout.preview_collapse.test.tsx
# Tests  3 passed (3)

npx tsc --noEmit
# exit 0
```

---

## Implementation Notes

| Topic | Decision |
|-------|----------|
| Flag parsing | `isStudioLayoutEnabled()` — strict `=== "1"` (§11) |
| Element `soft` | `#RRGGBB` blends on `#0c0c10` (test CHECKPOINT; not rgba in production) |
| Phase 1 center | No `CommandPanel` / `Terminal` in studio subtree |
| Hydration | No `selectAssetByPath({ importBuildOptions: true })` in new layout code |

---

## Workflow Transition Gates

```bash
python ci/scripts/run_workflow_transition_gates.py \
  --ticket-id STUDIO-01 \
  --transition implementation_to_static_qa
```
