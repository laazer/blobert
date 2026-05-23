# TICKET: claw_enemy_attack

Title: Claw enemy attack — fast multi-hit melee swipe

## Description

The claw family enemy attacks with a fast 2-hit swipe combo when the player is at close range. Short cooldown makes the claw enemy aggressive and punishing if the player stands still.

## Acceptance Criteria

- Claw enemy triggers attack when player is within melee range (configurable, default 2 units)
- Attack is a 2-hit combo: first swipe fires, brief pause, second swipe fires
- Each hit uses the shared hitbox system
- Per-hit damage is lower than other families (compensated by 2 hits)
- Attack cooldown is short (configurable, default 1.2s)
- Each swipe has a minimal telegraph (short wind-up animation frame)
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `attack_telegraph_system`
- M15 (Enemy Navigation) recommended — claw enemy must close distance to be threatening

---

## Execution Plan

| # | Objective | Output |
|---|-----------|--------|
| 1 | Spec | `project_board/specs/claw_enemy_attack_spec.md` (CLA-1..9) |
| 2 | Primary tests | `tests/scripts/combat/test_claw_enemy_attack.gd` |
| 3 | Adversarial tests | `tests/scripts/combat/test_claw_enemy_attack_adversarial.gd` |
| 4 | Implementation | `scripts/enemy/claw_crawler_attack.gd` — 2× telegraph + HADS hitbox re-arm |
| 5 | Gate | `timeout 300 ci/scripts/run_tests.sh` exit 0 |

---

## Specification

Normative contract: `project_board/specs/claw_enemy_attack_spec.md`.

- **Combo:** Telegraph → swipe 1 window (`EnemyAttackHitbox`) → `combo_pause_seconds` → telegraph → swipe 2 → `cooldown_seconds`.
- **Defaults:** `attack_range` 2, `cooldown_seconds` 1.2, `damage_per_hit` 7, `knockback_per_hit` 4, `telegraph_fallback_seconds` 0.35 (≥ ADV-ATS-08b floor).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
5

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `tests/scripts/combat/test_claw_enemy_attack.gd` (CLA-01..03); `tests/scripts/combat/test_claw_enemy_attack_adversarial.gd` (ADV-CLA); `test_attack_telegraph_system*.gd` (ADV-ATS-08b); `ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`)
- Static QA: Passing — no new linter errors on `claw_crawler_attack.gd`
- Integration: Partial — combo timing validated by contract tests + telegraph suite; in-editor feel optional

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

## Status
Proceed

## Reason
All acceptance criteria evidenced; ticket in `done/`.
