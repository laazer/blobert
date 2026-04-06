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

## Specification

- **Normative requirements:** `project_board/specs/attack_telegraph_system_spec.md` — **ATS-1** through **ATS-9**, **ATS-NF1**, **ATS-NF2**.
- **Summary:** Every covered attack splits a **telegraph** phase (wind-up: visible cue, ≥ 0.3 s wall-clock before the **active** phase) from damage-dealing behavior (projectiles, melee hit checks, player effects, or future attack `Area3D`). Durations are inspector-tunable via `@export` per family; `EnemyAnimationController` plays `"Attack"` when present with a completion signal, else a fallback timer plus alternate visual. Scope: **acid_spitter**, **adhesion_bug**, **carapace_husk**, **claw_crawler**. Ordering-only dependency on backlog `hitbox_and_damage_system` (hitboxes enable after telegraph).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status

- Pending

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "execution_plan_ref": "project_board/checkpoints/attack_telegraph_system/run-2026-04-06-planning.md",
  "spec_ref": "project_board/specs/attack_telegraph_system_spec.md",
  "ticket_path": "project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md",
  "test_design_log": "project_board/checkpoints/attack_telegraph_system/run-2026-04-06-test-design.md"
}
```

## Status
Proceed

## Reason
Primary behavioral tests landed in `tests/scripts/enemy/test_attack_telegraph_system.gd` (T-ATS-*). T-ATS-08 intentionally red until carapace/claw attack scripts exist at assumed paths. Adversarial pass next.
