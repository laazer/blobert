# TICKET: input_hint_polish_core_mechanics
Title: Input hint polish for core mechanics
Project: blobert
Created By: Autopilot Orchestrator
Created On: 2026-03-05T12:00:00Z

---

## Description
Upgrade on-screen input hints in the core movement and infection-loop scenes so a new player immediately understands move, jump, detach/recall, and absorb actions. Align hint text with actual input actions and keep layout readable across common aspect ratios.

Source backlog card: `project_board/2_milestone_2_infection_loop/backlog/input_hint_polish_core_mechanics.md`

---

## Acceptance Criteria
- On-screen hints exist for: move (left/right), jump, detach/recall (shared input), and absorb in the infection-loop scene
- Hint text and glyphs use consistent naming with the `project.godot` input actions and key bindings
- Hints are placed at screen edges or HUD regions and do not overlap the central play area or HP/chunk UI
- Layout remains readable at common resolutions (e.g. 16:9 and 16:10) when run in-editor
- Hints can be globally toggled on/off via a single configuration point (e.g. autoload or project setting), without changing scene wiring

---

## Dependencies
- None

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Presentation Agent

## Validation Status
- Tests: Run (Passing)
- Static QA: Not Run
- Integration: Not Run

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
{
  "field_name": "type"
}
```

## Status
Proceed

## Reason
Presentation-layer input hints implemented for core movement and infection-loop scenes; all primary + adversarial InputHints tests now pass.

# TICKET: input_hint_polish_core_mechanics
Title: Input hint polish for core mechanics
Project: blobert
Created By: Autopilot Orchestrator
Created On: 2026-03-05T12:00:00Z

---

## Description
Upgrade on-screen input hints in the core movement and infection-loop scenes so a new player immediately understands move, jump, detach/recall, and absorb actions. Align hint text with actual input actions and keep layout readable across common aspect ratios.

Source backlog card: `project_board/2_milestone_2_infection_loop/backlog/input_hint_polish_core_mechanics.md`

---

## Acceptance Criteria
- On-screen hints exist for: move (left/right), jump, detach/recall (shared input), and absorb in the infection-loop scene
- Hint text and glyphs use consistent naming with the `project.godot` input actions and key bindings
- Hints are placed at screen edges or HUD regions and do not overlap the central play area or HP/chunk UI
- Layout remains readable at common resolutions (e.g. 16:9 and 16:10) when run in-editor
- Hints can be globally toggled on/off via a single configuration point (e.g. autoload or project setting), without changing scene wiring

---

## Dependencies
- None

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
PLANNING

## Revision
1

## Last Updated By
Autopilot Orchestrator

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
Planner Agent

## Required Input Schema
```json
{
  "field_name": "type"
}
```

## Status
Proceed

## Reason
New ticket seeded from project_board backlog card for autopilot processing.

