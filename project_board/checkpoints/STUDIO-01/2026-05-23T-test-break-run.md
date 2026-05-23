# STUDIO-01 Test Breaker Run — 2026-05-23

**Run id:** `2026-05-23T-test-break-run`  
**Ticket:** `project_board/43_milestone_43_studio_editor_redesign/in_progress/STUDIO-01_studio_shell_tokens.md`  
**Stage:** TEST_BREAK → IMPLEMENTATION_FRONTEND

---

## Outcome

- Extended adversarial Vitest: `asset_generation/web/frontend/src/components/layout/StudioLayout.test.tsx` (35 intended cases when implementation modules exist; 24 new adversarial cases authored)
- §11 invalid-flag matrix: 14 values + `resetModules` on→off toggle
- T-5 hardened: inspector tab cycling, sidecar spy, App+flag-on integration
- T-3/T-4 edge: lowercase tab ids, single visible panel, hex color `#CHECKPOINT`, exactly nine keys
- Ticket stage: `IMPLEMENTATION_FRONTEND`, revision 5
- Handoff: `handoff-latest.yaml` (`test_break_to_implementation`)

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
  File: /Users/jacobbrandt/workspace/blobert/asset_generation/web/frontend/src/components/layout/StudioLayout.test.tsx:60:38
  58 |  const __vi_import_2__ = await import('../../api/client')
  59 |  const __vi_import_3__ = await import('../../store/useAppStore')
  60 |  const __vi_import_4__ = await import('./StudioLayout')
     |                                       ^
  61 |  const __vi_import_5__ = await import('../studio/StudioPreviewColumn')
  62 |  const __vi_import_6__ = await import('../../constants/elements')

 Test Files  1 failed (1)
      Tests  no tests
```

Legacy regression guard (still green):

```bash
npm test -- --run src/components/layout/ThreePanelLayout.preview_collapse.test.tsx
# 3 passed
```

---

## Adversarial Matrix

| Dimension | Coverage |
|-----------|----------|
| Null & Empty | `""`, whitespace-only flag |
| Boundary | `"0"`, `"01"`, `"10"`, padded `" 1"` / `"1 "` |
| Invalid/Corrupt | `"true"`, `"TRUE"`, `"yes"`, `"\n1"`, `"\t"` |
| Order dependency | `resetModules` after flag `1` then invalid |
| Combinatorial | App flag on + sidecar spy + `selectAssetByPath` spy |
| Mutation testing | Strict `=== "1"` contract (§11) |
| Assumption checks | Lowercase `studio-inspector-tab-*`; hex colors `#CHECKPOINT` |
| Determinism | `it.each` invalid flags; tab cycle asserts single panel |

---

## Gaps Documented (for implementation)

| Gap | Conservative assumption (`# CHECKPOINT` in tests) |
|-----|---------------------------------------------------|
| Flag parsing | Only exact `import.meta.env.VITE_STUDIO_LAYOUT === "1"` enables studio; trim/coerce not required unless product changes §11 |
| Element colors | `hue` / `soft` / `ink` are `#RRGGBB` hex (six digits); spec only mandates non-empty strings |
| Sidecar on studio mount | Studio mount + tab clicks must not call `fetchBuildOptionsSidecarForGlbPath` (REQ-1 parity) |
| Tab ids | `studio-inspector-tab-look` not `Look` |

---

## Workflow Transition Gates

```
transition=test_break_to_implementation ticket_id=STUDIO-01
  breaker_gaps_documented: PASS (this checkpoint)
  breaker_impl_notes: PASS (gaps table above)
```
