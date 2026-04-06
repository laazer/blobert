# TICKET: attack_telegraph_system

Title: Enemy attack telegraphing — wind-up indicator before hitbox activates

## Description

Each enemy attack must be readable before it deals damage. Implement a telegraphing phase: a brief wind-up animation or visual indicator plays before the hitbox activates, giving the player time to react. The telegraph duration is configurable per family.

## Acceptance Criteria

- Wind-up phase lasts at minimum 0.3 seconds before hitbox activates
- A visual change occurs during wind-up (animation state change, color flash, or indicator node)
- Hitbox does NOT activate during wind-up — only after wind-up completes
- Telegraph duration is an exported variable, not hardcoded
- Works for all 4 enemy families
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `animation_controller_script` (M7)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
SPECIFICATION

## Revision
2

## Last Updated By
Planner Agent

## Validation Status

- Pending

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
  "execution_plan_ref": "project_board/checkpoints/attack_telegraph_system/run-2026-04-06-planning.md",
  "ticket_path": "project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md"
}
```

## Status
Proceed

## Reason
Planning complete; structured task table and checkpoint assumptions logged. Produce formal spec (ATS-*), hitbox boundary, and per-family targets.
