# STUDIO-01 Test Designer Run — 2026-05-23

**Run id:** `2026-05-23T-test-design-run`  
**Ticket:** `project_board/43_milestone_43_studio_editor_redesign/in_progress/STUDIO-01_studio_shell_tokens.md`  
**Stage:** TEST_DESIGN → TEST_BREAK

---

## Outcome

- Primary tests: `asset_generation/web/frontend/src/components/layout/StudioLayout.test.tsx` (11 cases covering spec §8 T-1..T-6)
- Legacy hook: `data-testid="legacy-layout"` on `ThreePanelLayout` root (FR-1 / T-1)
- Spec traceability: T-1..T-6 mapped in test file module docstring and `describe` blocks
- Ticket stage: `TEST_BREAK`, revision 4
- Handoff: `handoff-latest.yaml` (test_designer → test_breaker)

---

## Test Evidence (RED — expected)

Command:

```bash
cd asset_generation/web/frontend && npm test -- --run src/components/layout/StudioLayout.test.tsx
```

Verbatim failure (suite cannot collect — implementation modules absent):

```
 FAIL  src/components/layout/StudioLayout.test.tsx [ src/components/layout/StudioLayout.test.tsx ]
Error: Failed to resolve import "./StudioLayout" from "src/components/layout/StudioLayout.test.tsx". Does the file exist?
  Plugin: vite:import-analysis
  File: /Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src/components/layout/StudioLayout.test.tsx:52:38
  50 |  const __vi_import_1__ = await import('@testing-library/react')
  51 |  const __vi_import_2__ = await import('../../store/useAppStore')
  52 |  const __vi_import_3__ = await import('./StudioLayout')
     |                                       ^
  53 |  const __vi_import_4__ = await import('../studio/StudioPreviewColumn')
  54 |  const __vi_import_5__ = await import('../../constants/elements')

 Test Files  1 failed (1)
      Tests  no tests
```

Regression guard (legacy layout tests still green):

```bash
npm test -- --run src/components/layout/ThreePanelLayout.preview_collapse.test.tsx
# 3 passed
```

---

## Spec ↔ Test Map

| Spec | Tests |
|------|-------|
| T-1 | `T-1 feature flag off` — App + unset / non-`1` env → `legacy-layout` present, `studio-layout` absent |
| T-2 | `T-2 feature flag on` — App flag `1` + `StudioLayout` grid style; preview column testids + mocked stack |
| T-3 | `T-3 inspector tab switch` — `aria-selected` + `studio-inspector-panel-*` visibility |
| T-4 | `T-4 elements.ts` — nine ids with `hue` / `soft` / `ink` strings |
| T-5 | `T-5 preview hydration guard` — `selectAssetByPath` spy, no `importBuildOptions: true` on mount |
| T-6 | `T-6 Phase 1 center omission` — `command-panel`, `preview-terminal`, log region absent under studio subtree |

---

## Gaps / Test Breaker Focus

- Invalid / whitespace flag values (§11) — adversarial cases
- `vi.resetModules` + `import.meta.env` edge cases when App flag branches land
- Stricter hydration spy (mount + user interactions that might select assets)
- Confirm `studio-inspector-tab-*` slug casing matches implementation (`look` vs `Look`)
- Terminal test id contract: tests use `preview-terminal` mock id + `role="region"` name `Run output log`

---

## Workflow Transition Gates

```
transition=test_design_to_test_break ticket_id=STUDIO-01
  todo_validation_check: PASS — All todos completed for Test Designer Agent.
  handoff_validation_check: PASS — Handoff checklist valid for test_designer→test_breaker.
```
