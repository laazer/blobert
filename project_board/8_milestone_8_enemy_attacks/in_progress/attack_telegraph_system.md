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
STATIC_QA

## Revision
6

## Last Updated By
Gameplay Systems Agent

## Validation Status

- Pending — `tests/scripts/enemy/test_attack_telegraph_system.gd` + adversarial: passing (`timeout 300 godot -s tests/run_tests.gd` exit 0); GDScript review pending (STATIC_QA / AC Gatekeeper)

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
  "spec_ref": "project_board/specs/attack_telegraph_system_spec.md",
  "ticket_path": "project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md",
  "implementation_log": "project_board/checkpoints/attack_telegraph_system/run-2026-04-06-gameplay-systems.md"
}
```

## Status
Proceed

## Reason
Telegraph implementation complete: controller ATS-2 wall hold, acid/adhesion `maxf` fallback + cycle guards, carapace/claw minimal attack scripts and `EnemyInfection3D` wiring; primary + adversarial telegraph tests pass; full headless suite exit 0. Hand off for AC verification and STATIC_QA sign-off.
