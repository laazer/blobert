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
