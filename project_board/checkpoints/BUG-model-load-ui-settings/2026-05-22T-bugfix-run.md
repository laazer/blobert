# BUG-model-load-ui-settings — bugfix run

Started: 2026-05-22

Ticket: `project_board/bugfix/in_progress/model-load-ui-settings.md`

---

## Checkpoint — Spec Agent (2026-05-22)

**Would have asked:** Does the reporter want (A) no UI mutation on preview load, or (B) full sidecar sync with CommandPanel/Colors merely broken? The one-line bug report is ambiguous (“current” may mean in-session settings vs loaded model settings; “being set” may be unwanted or a failed expectation).

**Assumption made:** Interpret as **(A) preview load must not overwrite in-session build/color/command settings**; explicit import remains for post-generation auto-select and load-existing open. Registry version preview is preview-only.

**Confidence:** Medium — codebase comment on `hydrateBuildOptionsFromPreviewGlbPath` suggests intentional merge, but call-site spread (registry preview + BuildControls sync) matches user-visible “everything changes when I load a model” bug; CommandPanel one-way sync is a confirmed secondary defect if import stays enabled anywhere.

---

## Checkpoint — Spec Agent (2026-05-22) REQ-2 scope

**Would have asked:** Should clicking a registry version’s preview control import that version’s `*.build_options.json` into the editor?

**Assumption made:** **No** for preview click; **yes** for load-existing open and `refreshAssetsAndAutoSelect` after pipeline output.

**Confidence:** Medium — aligns with preserving edits while browsing versions; can add explicit “Import settings” control in a follow-up ticket.

---

## Checkpoint — Test Designer Agent (2026-05-22)

**Deliverable:** `asset_generation/web/frontend/src/store/useAppStore.selectAssetByPath.previewOnly.test.ts`

**Test IDs:**
- `BUG-model-load-ui-settings-preview-select-does-not-import-sidecar`

**Spec traceability:** REQ-1 AC-1.1, AC-1.2, AC-1.3; REQ-5 AC-5.1 (fails pre-fix), AC-5.3 (named suites green).

**Targeted run (new file only) — expected FAIL:**

```
 FAIL  src/store/useAppStore.selectAssetByPath.previewOnly.test.ts > selectAssetByPath preview-only (REQ-1) > BUG-model-load-ui-settings-preview-select-does-not-import-sidecar
AssertionError: expected 2 to be 7 // Object.is equality

- Expected
+ Received

- 7
+ 2

 ❯ src/store/useAppStore.selectAssetByPath.previewOnly.test.ts:51:63
```

**Failing assertion summary:** After registry-style `selectAssetByPath("animated_exports/spider_animated_05.glb")` with mocked sidecar `{ eye_count: 2, ... }`, store still has `eye_count: 2` (imported) instead of preserved in-session `7`. `activeGlbUrl` updates correctly (passes).

**Non-regression (AC-5.3):**

```
npm test -- --run src/components/Preview/BuildControls.previewSync.test.tsx src/components/Preview/ColorsPane.test.tsx
# 9 passed
```

**Full suite note:** `npm test -- --run` exit 1 with 16 failures across 5 files (includes this regression test + unrelated `ImageMode`, `BuildControlRow.concurrency`, `ModelRegistryPane.family_tabs`, `BuildControls.texture`). Not introduced by test file alone; implementation handoff should not treat those as REQ-5 blockers unless reproducing on clean branch.

**Deferred:** REQ-2 import-path test, REQ-3 CommandPanel sync, REQ-4 ColorsPane preview-only — minimum scope per ticket handoff; implementation may extend.
