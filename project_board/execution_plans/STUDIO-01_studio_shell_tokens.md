# Execution Plan: STUDIO-01 — Studio shell, tokens, feature-flagged layout

**Ticket ID:** STUDIO-01  
**Planning revision:** 1  
**Date:** 2026-05-23  
**Authoritative spec:** `project_board/specs/studio_editor_redesign_spec.md` (§6–§9; §12 deferred)  
**Next agent:** Spec Agent (Task 1)

---

## Executive Summary

Deliver Phase 1 of the Asset Editor Studio redesign in `asset_generation/web/frontend`: a `VITE_STUDIO_LAYOUT`-gated `StudioLayout` (256px | 1fr | 360px grid, 52px top bar, left library placeholder, central GLB preview + animation rail, right inspector tab shell with placeholders). Legacy `ThreePanelLayout` remains default. Reuse existing preview stack (`PreviewSourceBar`, `GlbViewer`, `AnimationControls`) and store paths; do **not** call `selectAssetByPath` with `importBuildOptions: true` from new layout code. Spec is pre-authored — Spec Agent validates/finalizes STUDIO-01 scope only.

---

## Dependency Matrix

| Dependency | Folder / State | Blocks STUDIO-01? | Notes |
|------------|----------------|-------------------|-------|
| STUDIO-01 (self) | `in_progress/` | N/A | Active ticket |
| STUDIO-02+ (inspector wiring, registry library) | Not started / deferred | **No** | Explicitly out of scope §12 |
| `model-load-ui-settings` bugfix (REQ-1 preview-only) | `bugfix/in_progress/` | **No** (invariant) | Must not regress; no new hydration |
| Pre-authored redesign spec | `project_board/specs/studio_editor_redesign_spec.md` | **No** (satisfied) | Spec Agent validates §6–§9 |
| `ThreePanelLayout`, `GlbViewer`, store | Implemented | **No** (satisfied) | Reuse patterns |
| `elements.ts`, `StudioLayout` | **Absent** | N/A | Greenfield deliverables |

**Umbrella ticket:** No. **Cycles / WARN:** None.

---

## Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | Validate/freeze existing spec; `spec_completeness_check --type generic` |
| Test design | Test Designer Agent | 1 | `StudioLayout.test.tsx` + elements coverage (T-1..T-5) |
| Test break | Test Breaker Agent | 1 | Flag/hydration adversarial probes |
| Implementation | Implementation Frontend Agent | 1–2 | Tokens + shell + App flag branch |
| Static QA | Static QA / Frontend reviewer | 1 | `tsc --noEmit`, `npm test -- --run` |
| Learning | Learning Agent | 1 | `LEARNINGS.md` entry |
| AC gatekeeper | AC Gatekeeper | 1 | AC-1..AC-7; commit/push before COMPLETE |

**Total:** 7–8 agent runs

---

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Validate and finalize STUDIO-01 scope in existing spec: §6 FR-* ↔ ticket AC-1..AC-7 ↔ §8 T-* traceability; §12 deferred boundaries explicit; §10 hydration invariants preserved; open questions §13 defaults frozen | Spec Agent | Ticket; `project_board/specs/studio_editor_redesign_spec.md`; `frontend/AGENTS.md`; `model-load-ui-settings` REQ-1 | Spec updated only if gaps found; otherwise attestation of freeze | — | `python ci/scripts/spec_completeness_check.py project_board/specs/studio_editor_redesign_spec.md --type generic` PASS | **Assume:** validation-first, not rewrite. **Risk:** CommandPanel/Terminal placement — default: omit from `StudioPreviewColumn` in Phase 1 (preview hero + animation rail only per §4, §79) |
| 2 | Author Vitest suite per §8: flag off/on (T-1, T-2), inspector tab switch (T-3), elements export shape (T-4), no `importBuildOptions: true` on Studio mount (T-5); `@vitest-environment jsdom`, `vi.mock` on `useAppStore` mirroring `ThreePanelLayout.*.test.tsx` | Test Designer Agent | Approved spec Task 1 | `src/components/layout/StudioLayout.test.tsx` (+ colocated elements test if split) | 1 | Tests fail (red) before implementation; runtime assertions only | **Risk:** Prose-only tests forbidden. **Assume:** add `data-testid="legacy-layout"` expectation — Implementation adds hook on `ThreePanelLayout` |
| 3 | Adversarial tests: invalid/non-`"1"` flag values → legacy; double-mount flag toggle; spy `selectAssetByPath` for forbidden `{ importBuildOptions: true }` from Studio subtree; legacy layout regression smoke | Test Breaker Agent | Spec + Task 2 tests | Extended/adversarial cases in layout test file(s) | 2 | New failures encode conservative assumptions; `# CHECKPOINT` where spec silent | **Assume:** strictest hydration guard per BUG model-load-ui-settings |
| 4 | Implement design tokens: `src/constants/elements.ts` (`ElementId`, nine `ELEMENTS` with hue/soft/ink from `shared.jsx`); `src/styles/studioTokens.ts` (surfaces, ink, 256/360/52 layout constants, `studioInspectorTabStyle` helper mirroring `centerPanelTabStyles.ts`) | Implementation Frontend Agent | Spec FR-2; red T-4 | New token modules | 3 | T-4 passes; `npx tsc --noEmit` clean | **Risk:** Color drift from prototype — copy values from `shared.jsx` |
| 5 | Implement Studio shell: `App.tsx` branches on `import.meta.env.VITE_STUDIO_LAYOUT === "1"`; `StudioLayout` grid (256px 1fr 360px, 52px + 1fr rows); `StudioTopBar`, `EnemyLibraryPlaceholder`, `StudioPreviewColumn`, `StudioInspector` (five tabs, placeholders, testids); `data-testid="studio-layout"` | Implementation Frontend Agent | Spec FR-1, FR-3, FR-5; Tasks 3–4 | Files under `src/components/layout/` and `src/components/studio/` per §9 | 4 | T-1..T-3 pass; grid matches AC-2 | **Assume:** module-level `CSSProperties`; no `window` globals |
| 6 | Preview column parity + legacy hook: `StudioPreviewColumn` mounts `PreviewSourceBar`, `GlbViewer`, collapsible `AnimationControls` with same `usePersistedBoolean` keys as `ThreePanelLayout`; add `data-testid="legacy-layout"` on `ThreePanelLayout` root; document `VITE_STUDIO_LAYOUT=1` in `.env.example` or `frontend/README.md` | Implementation Frontend Agent | Spec FR-4, FR-6, AC-1, AC-4; `ThreePanelLayout.tsx` preview section | Updated preview wiring + minimal legacy testid + one-line env doc | 5 | Existing `ThreePanelLayout.*.test.tsx` pass; T-5 pass; no `importBuildOptions: true` in new layout code | **Risk:** Accidental hydration if copying registry handlers — placeholders only in inspector |
| 7 | Static QA: `cd asset_generation/web/frontend && npx tsc --noEmit && npm test -- --run`; review for `as any`, pilot schema drift, convention match (`RegistryTagChips.tsx` style) | Static QA | Tasks 4–6 | PASS evidence in checkpoint | 6 | AC-7 satisfied | **Risk:** GlbViewer WebGL mocks in jsdom — follow existing preview test patterns |
| 8 | Document learnings (feature-flag rollout, studio token layer, preview-only hydration guard) | Learning Agent | Completed implementation | `project_board/LEARNINGS.md` STUDIO-01 section | 7 | Entry references ticket + invariant | — |
| 9 | AC gatekeeper: verify AC-1..AC-7 with test/typecheck evidence; git clean + pushed; move ticket to `done/` | AC Gatekeeper | Ticket AC; checkpoint logs | Stage COMPLETE | 8 | All AC met; remote pushed | Per workflow enforcement — no COMPLETE without push |
| 10 | Orchestrator: run mandatory transition gates (`planner_to_spec` … `learning_to_ac_gatekeeper`) before each stage advance | Autopilot Orchestrator | Checkpoint artifacts | Gate PASS logs in scoped checkpoint | Per stage | Exit 0 on all transitions; BLOCKED on exit 1 | No skip flags per `mandatory_workflow_gates_v1.md` |

---

## Notes

- **Not a 1:1 port:** Reference `bot_vault/asset_generation/redesign_v1/studio.jsx` for IA only; do not ship `design-canvas.jsx`.
- **Store compatibility:** Do not remove/rename `centerPanel` / `setCenterPanel` in STUDIO-01.
- **Fonts:** Optional in Phase 1; system/Segoe stack acceptable until STUDIO-02 (spec §13).
- **Deferred (STUDIO-02+):** Real `ColorsPane` / `BuildControls` in inspector, registry-connected `EnemyLibrary`, compare grid, top-bar Save/Regen wiring, default flag cutover.
