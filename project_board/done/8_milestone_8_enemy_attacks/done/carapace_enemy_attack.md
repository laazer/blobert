# TICKET: carapace_enemy_attack

Title: Carapace enemy attack — slow charge with knockback

## Description

The carapace family enemy attacks by winding up a heavy charge, then launching itself along the X axis. On hit the player is knocked back significantly. High damage, long telegraph, high knockback — readable and avoidable but dangerous if caught.

## Acceptance Criteria

- Carapace enemy enters charge wind-up when player is within range (configurable, default 6 units)
- Wind-up lasts at least 0.6 seconds (longer than other families)
- Charge travels along the X axis until it hits the player, a wall, or exceeds max range
- On hit, player takes heavy damage and a large knockback force
- Enemy decelerates after charge completes (no infinite sliding)
- Attack cooldown is long (configurable, default 4.0s)
- `run_tests.sh` exits 0

## Dependencies

- `hitbox_and_damage_system`
- `attack_telegraph_system`

---

## Execution Plan

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author formal spec (states, timing, exports, integration contracts) | Spec Agent | This ticket; `scripts/enemy/carapace_husk_attack.gd` stub; `scripts/enemy/adhesion_bug_lunge_attack.gd` (lunge + `enemy_writes_velocity_x_this_frame`); `scripts/enemies/enemy_animation_controller.gd` (`ATS2_MIN_TELEGRAPH`, `begin_ranged_attack_telegraph`); `project_board/specs/hitbox_and_damage_system_spec.md` or `EnemyAttackHitbox` API | `project_board/specs/carapace_enemy_attack_spec.md` (or agreed path); ticket Stage → TEST_DESIGN after review | None | Spec defines: wind-up ≥0.6s wall-clock before active charge; `attack_range` default 6; `cooldown_seconds` default 4; max charge distance default 6 (or explicit separate export); charge velocity, deceleration curve, hitbox activation window, damage/knockback vs HADS; how telegraph meets 0.6s given controller’s 0.3s floor; `enemy_writes_velocity_x` ownership during charge/decel; termination on player hit / wall / max range | **Assumption:** Spec resolves 0.6s vs `ATS2_MIN_TELEGRAPH` (0.3s) without breaking other families; numeric defaults for “heavy” / “large” stated explicitly |
| 2 | Primary behavioral tests (deterministic, headless) | Test Designer Agent | Spec from task 1 | `tests/scripts/combat/test_carapace_enemy_attack.gd` (or agreed path); named cases (T-CEA-*) | Task 1 | Tests fail until implementation matches spec; cover range gate, telegraph min duration, charge axis, stop conditions, cooldown, deceleration | SceneTree limits documented per `test_attack_telegraph_system` patterns if needed |
| 3 | Adversarial tests | Test Breaker Agent | Spec + primary tests | `tests/scripts/combat/test_carapace_enemy_attack_adversarial.gd` | Tasks 1–2 | Edge cases (re-entry, zero dir, concurrent states, knockback/damage bounds) | Conservative defaults per checkpoint protocol |
| 4 | Implement charge + telegraph + HADS integration | Implementation Agent (Gameplay Systems or Generalist) | Spec + failing tests | `carapace_husk_attack.gd` full behavior; optional `EnemyAnimationController` or attack-only timer changes per spec; scene wiring only if spec requires | Tasks 1–3 | All new tests pass; `enemy_writes_velocity_x_this_frame` consistent with `EnemyInfection3D` order; `cooldown_seconds` default 4, `attack_range` default 6 | Controller change could affect ATS tests — run full suite |
| 5 | Static QA and full gate | Implementation Agent or CI | Green unit tests | `timeout 300 ci/scripts/run_tests.sh` exit 0 | Task 4 | `=== ALL TESTS PASSED ===` (or project equivalent); ticket Validation Status updated | None |

---

## Specification

Normative contract: `project_board/specs/carapace_enemy_attack_spec.md` (CEA-1 … CEA-10).

- **0.6 s wind-up:** `EnemyAnimationController.begin_ranged_attack_telegraph(min_hold_seconds)` with `min_hold_seconds >= 0` enforces `max(ATS2_MIN_TELEGRAPH, min_hold_seconds)`; carapace passes `0.6`. Fallback timer uses `maxf(telegraph_fallback_seconds, 0.6)`.
- **Charge / stop:** X-axis charge at `charge_speed`; stop on HADS hit, wall slide normal `|n.x| > 0.4`, or horizontal travel ≥ `max_charge_range` from charge start.
- **Damage / knockback:** Child `EnemyAttackHitbox` with defaults `damage_amount` 35, `knockback_strength` 22 (exports on `CarapaceHuskAttack` applied to hitbox).
- **Decel:** Multiplicative `decel_factor` until `|velocity.x| < decel_velocity_epsilon`, then cooldown.
- **Velocity gate:** `EnemyInfection3D` skips zeroing `velocity.x` when `CarapaceHuskAttack.enemy_writes_velocity_x_this_frame()` returns true (same pattern as adhesion lunge).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `tests/scripts/combat/test_carapace_enemy_attack.gd` (CEA-01..03); `tests/scripts/combat/test_carapace_enemy_attack_adversarial.gd` (ADV-CEA); full Godot suite + `ci/scripts/run_tests.sh` exit 0 (`=== ALL TESTS PASSED ===`)
- Static QA: Passing — no linter errors on touched attack scripts after `Area3D`/`set()` for hitbox fields
- Integration: Partial — charge/wall/hitbox behavior covered by unit tests + existing telegraph/HADS suites; in-editor feel tuning optional

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
All acceptance criteria evidenced in Validation Status; ticket in `done/`.
