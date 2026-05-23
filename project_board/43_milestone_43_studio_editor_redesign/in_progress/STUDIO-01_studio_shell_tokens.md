# TICKET: STUDIO-01
Title: Studio shell, design tokens, and feature-flagged layout (Phase 1)
Project: blobert
Created By: Human
Created On: 2026-05-23

---

## Description

Implement **Phase 1** of the Asset Editor Studio redesign in `asset_generation/web/frontend`: a feature-flagged `StudioLayout` (256px | fluid | 360px grid, top bar, left library placeholder, central GLB preview + animation rail, right inspector tab shell) using production TypeScript/React conventions — **not** a 1:1 port of `bot_vault/asset_generation/redesign_v1/studio.jsx`.

**Authoritative spec:** `project_board/specs/studio_editor_redesign_spec.md` (§6–§9, §12 deferred boundaries).

**Reference (design-time only):** `bot_vault/asset_generation/redesign_v1/studio.jsx`, `shared.jsx`. Do **not** ship `design-canvas.jsx`.

**Conversion contract:** Match existing frontend patterns (`RegistryTagChips.tsx`, `ThreePanelLayout.tsx`): module-level `CSSProperties`, Zustand, Vitest, reuse `GlbViewer` / `PreviewSourceBar` / `AnimationControls`. No `window` globals. No `importBuildOptions` from new layout code.

---

## Acceptance Criteria

- AC-1: With `VITE_STUDIO_LAYOUT` unset or not `"1"`, `App` renders legacy `ThreePanelLayout` with no behavior regression (existing layout tests still pass).
- AC-2: With `VITE_STUDIO_LAYOUT=1`, `StudioLayout` renders with grid columns 256px / 1fr / 360px and `data-testid="studio-layout"`.
- AC-3: `src/constants/elements.ts` defines all nine element ids from the spec with `hue`, `soft`, and `ink` strings.
- AC-4: Studio center column mounts `PreviewSourceBar`, `GlbViewer`, and `AnimationControls` with the same store integration as the legacy preview stack.
- AC-5: `StudioInspector` exposes five tabs (Look, Build, Animate, Code, Versions) with switchable placeholders and `data-testid` hooks; no requirement to mount full `ColorsPane` / registry in this ticket.
- AC-6: New Vitest tests in `StudioLayout.test.tsx` cover flag off/on, inspector tab switch, and no preview hydration with `importBuildOptions: true` from Studio mount.
- AC-7: `npx tsc --noEmit` and `npm test -- --run` pass in `asset_generation/web/frontend`.

---

## Dependencies

- None (hydration bugfix `model-load-ui-settings` should remain respected; do not regress preview-only selection).

---

## Specification

- `project_board/specs/studio_editor_redesign_spec.md`

---

## Execution Plan

**Ticket ID:** STUDIO-01  
**Planning revision:** 1  
**Date:** 2026-05-23  
**Execution plan file:** `project_board/execution_plans/STUDIO-01_studio_shell_tokens.md`  
**Next agent:** Spec Agent (Task 1)

### Executive Summary

Phase 1 Studio shell in `asset_generation/web/frontend`: feature-flagged `StudioLayout` (256px | 1fr | 360px, 52px top bar), design tokens, central preview parity with legacy stack, inspector tab placeholders. Legacy `ThreePanelLayout` default. Pre-authored spec — Spec Agent validates §6–§9 only.

### Dependency Matrix

| Dependency | Folder / State | Blocks STUDIO-01? | Notes |
|------------|----------------|-------------------|-------|
| STUDIO-02+ | Deferred | **No** | §12 explicit deferral |
| Preview-only hydration (REQ-1) | Invariant | **No** | Must not regress |
| Redesign spec | `project_board/specs/` | **No** (satisfied) | Validate, don't rewrite |
| Studio components | Absent | N/A | Greenfield |

**Umbrella ticket:** No. **Cycles:** None.

### Estimated Effort (Agent Runs)

| Phase | Agent | Runs |
|-------|-------|------|
| Specification | Spec Agent | 1 |
| Test design | Test Designer Agent | 1 |
| Test break | Test Breaker Agent | 1 |
| Implementation | Implementation Frontend Agent | 1–2 |
| Static QA | Static QA | 1 |
| Learning | Learning Agent | 1 |
| AC gatekeeper | AC Gatekeeper | 1 |

**Total:** 7–8 agent runs

### Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Validate/finalize STUDIO-01 scope in existing spec: FR-* ↔ AC-* ↔ T-* traceability; §12 deferred; §10 hydration invariants | Spec Agent | Ticket; `studio_editor_redesign_spec.md`; REQ-1 | Spec freeze or gap-fill edits | — | `spec_completeness_check --type generic` PASS | Validation-first; CommandPanel/Terminal omitted from Studio center in Phase 1 |
| 2 | Vitest suite §8 T-1..T-5: flag off/on, inspector tabs, elements shape, no `importBuildOptions` on Studio mount | Test Designer Agent | Approved spec | `StudioLayout.test.tsx` (red) | 1 | Runtime assertions; jsdom + store mocks | Add `legacy-layout` testid expectation |
| 3 | Adversarial: invalid flag values, hydration spy, legacy regression | Test Breaker Agent | Spec + Task 2 | Extended failing tests | 2 | `# CHECKPOINT` where spec silent | Strictest hydration guard |
| 4 | `elements.ts` + `studioTokens.ts` (nine elements, layout tokens, tab style helper) | Implementation Frontend Agent | Spec FR-2 | Token modules | 3 | T-4 pass; tsc clean | Colors from `shared.jsx` |
| 5 | `App.tsx` flag; `StudioLayout` grid + `StudioTopBar`, `EnemyLibraryPlaceholder`, `StudioPreviewColumn`, `StudioInspector` placeholders | Implementation Frontend Agent | Spec FR-1, FR-3, FR-5 | `layout/` + `studio/` components | 4 | T-1..T-3 pass; AC-2 | CSSProperties pattern; no window globals |
| 6 | Preview parity: `PreviewSourceBar` + `GlbViewer` + `AnimationControls`; `legacy-layout` testid; env doc | Implementation Frontend Agent | Spec FR-4, FR-6 | Wiring + docs | 5 | Legacy tests pass; T-5 pass | No `importBuildOptions: true` in new code |
| 7 | Static QA: `tsc --noEmit`, `npm test -- --run` | Static QA | Tasks 4–6 | PASS evidence | 6 | AC-7 | No `as any` |
| 8 | LEARNINGS.md entry | Learning Agent | Implementation | STUDIO-01 section | 7 | Documented | — |
| 9 | AC gatekeeper: AC-1..AC-7; commit/push; move to `done/` | AC Gatekeeper | Evidence | COMPLETE | 8 | All AC met | Push mandatory |
| 10 | Orchestrator transition gates at each handoff | Autopilot Orchestrator | Artifacts | Gate PASS logs | Per stage | No skip | `mandatory_workflow_gates_v1.md` |

### Notes

- Reference `studio.jsx` for IA only; never ship `design-canvas.jsx`.
- Do not remove `centerPanel` / `setCenterPanel` in STUDIO-01.
- Full plan detail: `project_board/execution_plans/STUDIO-01_studio_shell_tokens.md`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_DESIGN

## Revision
3

## Last Updated By
Spec Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Designer Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/43_milestone_43_studio_editor_redesign/in_progress/STUDIO-01_studio_shell_tokens.md",
  "spec_path": "project_board/specs/studio_editor_redesign_spec.md",
  "execution_plan_path": "project_board/execution_plans/STUDIO-01_studio_shell_tokens.md",
  "scope": "STUDIO-01 Phase 1 only (spec §6–§9, §10, §12, §15–§16); tests §8 T-1..T-6"
}
```

## Status
Proceed

## Reason
Spec frozen for Phase 1: Studio center = preview + animation rail only (CommandPanel/Terminal deferred). Handoff to Test Designer for red Vitest suite per §8.
