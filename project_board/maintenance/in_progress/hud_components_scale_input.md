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

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
SPECIFICATION

## Revision
2

## Last Updated By
Planner Agent

## Validation Status
- Pending pipeline

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Spec Agent

## Required Input Schema
```json
{
  "action": "spec",
  "ticket_path": "project_board/maintenance/in_progress/hud_components_scale_input.md"
}
```

## Status
Proceed

## Reason
Planning complete; execution plan and checkpoint recorded under `project_board/checkpoints/MAINT-HCSI/run-2026-04-05-planning.md`. Spec Agent shall produce the formal specification for unified HUD scale and test/layout contracts.
