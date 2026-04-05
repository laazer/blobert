# TICKET: hud_components_scale_input

Title: Add a unified scale input for HUD components (`GameUI` / `infection_ui`)

## Description

`scenes/ui/game_ui.tscn` is a `CanvasLayer` whose children use hand-tuned `offset_*` rectangles and per-control `theme_override_font_sizes`. There is no single control for “make the whole HUD larger or smaller” (accessibility, different resolutions, or playtesting). Introduce an explicit **HUD scale** (uniform float, default `1.0`) that applies consistently to the packaged HUD so one knob rescues layout and typography together.

Implementation is flexible: e.g. a full-screen `Control` root under the layer with `scale` driven by the factor; `Window.content_scale_factor` / theme scaling if that matches project conventions; or a small script on `InfectionUI` that sets scale on a designated container and/or applies theme font scale. Pick the approach that keeps hit-testing and anchors sane and avoids blurring if that matters for the art direction. Document in code where designers or scenes set the value (exported property, autoload, or scene override).

## Acceptance Criteria

- A single documented scale parameter exists (default preserves current visual layout at `1.0`).
- All interactive/readout HUD elements shipped in `game_ui.tscn` scale together with that parameter (input hint labels included if they live under the same tree).
- `run_tests.sh` exits 0; update or extend `tests/ui/` HUD tests if they assert hard-coded pixel sizes so they remain meaningful under the default scale.

## Dependencies

- None required

## Specification

- **Formal spec:** `project_board/specs/hud_components_scale_input_spec.md`
- **Requirement IDs:** `HCSI-1` (single HUD scale parameter + documentation), `HCSI-2` (default `1.0` preserves legacy layout numbers and on-screen parity), `HCSI-3` (all shipped `Control` nodes in `game_ui.tscn` including `Hints` subtree scale together), `HCSI-4` (`GameUI` `CanvasLayer` root + `get_node` path contract for `infection_ui.gd`, layout tests, fusion T-41/T-42), `HCSI-5` (uniform scale mechanism, pivot/anchors, hit-testing), `HCSI-6` (`run_tests.sh` green; update layout tests for design vs transformed space), `HCSI-7` (out-of-scope: non–`game_ui.tscn` HUD instances)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
STATIC_QA

## Revision
6

## Last Updated By
Engine Integration Agent

## Validation Status
- `timeout 300 ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`, 2026-04-05) after `hud_scale` + HUD scaling in `infection_ui.gd` / `game_ui.tscn`.
- Checkpoint: `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-implementation.md`

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{
  "action": "verify_ac",
  "ticket_path": "project_board/maintenance/in_progress/hud_components_scale_input.md",
  "spec_path": "project_board/specs/hud_components_scale_input_spec.md"
}
```

## Status
Proceed

## Reason
Implementation complete per HCSI (exported `hud_scale`, uniform scaling, path contract preserved). Awaiting AC Gatekeeper verification before COMPLETE / folder move.
