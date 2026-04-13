# TICKET: 05_backlog_optional_glb_validation_or_preview_hooks

Title: (Stretch) GLB validation or preview hooks for agent visual iteration

## Description

Optional follow-up after the core MCP milestone: add tools or endpoints that improve **visual/technical feedback** without replacing Blender authoring, for example:

- Invoke a **glTF validator** on a produced path under allowlist and return structured issues.
- Optional **single-frame render** or screenshot URL (Blender batch or headless Godot) — only if cost/complexity is acceptable.

**Disposition:** Stretch scope is **deferred** (no code in M23 for this ticket). Operator-facing pointer: `asset_generation/mcp/README.md` § **Future work — GLB validation / preview (optional, M23-05)**.

## Acceptance Criteria

- None required for M23 closure; ticket exists to capture the idea and dependencies (Blender automation, disk paths, timeouts).

## Dependencies

- M23 tickets `01`–`04` and `06` complete (core iteration); ticket `05` is optional stretch
- Art/tech direction on whether pixels-in-the-loop are desired

## Execution Plan

1. Record stretch ideas in operator docs and milestone index (no new MCP tools until dependencies + direction).
2. Re-open for implementation only after `01`–`04` and `06` are complete and product wants pixels-in-the-loop.

## Specification

- **APMCP (core):** `project_board/specs/asset_pipeline_mcp_spec.md` — no optional validator/preview tools added in this disposition pass.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage

COMPLETE

## Revision

2

## Last Updated By

Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: N/A — acceptance criteria state none required for M23 closure; no behavioral change.
- Static QA: `asset_generation/mcp/README.md` §Future work links this ticket; milestone `README.md` table updated for ticket 5.
- Integration: N/A

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent

Human

## Required Input Schema

```json
{}
```

## Notes

- Implementation deferred until dependencies (**`01`–`04`, `06`**) and art/tech direction on preview pixels.
