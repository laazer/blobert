# TICKET: 14_enemy_health_and_damage_reception

**Milestone:** M11 Base Mutation Attacks  
**Status:** Backlog  
**Type:** Feature

## Title

Enemy health system and damage/modifier reception

## Description

`EnemyBase` currently has a state enum (`NORMAL`, `WEAKENED`, `INFECTED`) and identity exports, but no health tracking and no methods to receive damage or modifiers. The attack pipeline (`AttackExecutor`, `PlayerProjectile3D`) calls `take_damage()`, `apply_poison()`, `apply_acid()`, and `apply_slowness()` via duck typing — these methods don't exist on actual enemies. Until they do, the entire attack system has no runtime effect.

This ticket adds the missing enemy-side contract so that the existing attack pipeline connects end-to-end.

## Acceptance Criteria

- [ ] `EnemyBase` has a configurable `max_hp` export (default 10.0) and a `current_hp` var
- [ ] `take_damage(damage: float, knockback: Vector3)` reduces `current_hp`, applies knockback impulse, and emits a `damaged` signal
- [ ] When `current_hp` <= 0, enemy transitions to a death state (disable AI, play death, emit `died` signal)
- [ ] `apply_poison(duration: float, dps: float)` applies a ticking DoT effect (damage every 0.5s for `duration` seconds)
- [ ] `apply_acid(duration: float, dps: float)` applies a ticking DoT effect (same tick rate, visually distinct from poison)
- [ ] DoT effects do not stack from the same source — re-application refreshes duration
- [ ] `apply_slowness(multiplier: float, duration: float)` reduces enemy movement speed by `multiplier` for `duration` seconds
- [ ] Knockback impulse moves the enemy in the given direction and decays over time (does not permanently alter velocity)
- [ ] WEAKENED state is entered when `current_hp` drops below a threshold (e.g. 50%) or via existing `set_base_state()` — whichever comes first
- [ ] All existing attack pipeline tests still pass (duck-typed mock tests remain valid)
- [ ] New integration tests verify `EnemyBase` receives damage from `AttackExecutor` and `PlayerProjectile3D`
- [ ] `run_tests.sh` exits 0

## Dependencies

- M11-04 (AttackResource) — defines damage values
- M11-05 (AttackExecutor) — calls take_damage/apply_* methods
- M11-13 (Verify Damage Knockback) — existing tests use mock enemies; real enemies must satisfy the same contract

## Notes

- This is the prerequisite for tickets 08 (Claw), 09 (Acid), 10 (Carapace), and 11 (Adhesion)
- Keep `EnemyBase` under 200 lines — extract DoT/modifier tracking to a helper if needed
- The knockback impulse system should work with `CharacterBody3D.velocity` in `_physics_process`
- Existing `enemy_ai_controller.gd` already handles NORMAL→WEAKENED→INFECTED transitions; this ticket adds the HP-based trigger for WEAKENED

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
6

## Last Updated By
Gameplay Systems Agent

## Validation Status
- Tests: PASS (190 tests across 3 files: 58 primary, 50 effect tracker, 82 adversarial)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
None

## Escalation Notes
None

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
None

## Status
Proceed

## Reason
Implementation complete. EnemyBase (138 lines) gains HP system, take_damage(), knockback impulse, WEAKENED threshold, death state, and DoT/slowness delegation. EnemyEffectTracker (85 lines) extracted as child Node for DoT tick timing and slowness tracking. EnemyAIController updated to remove duplicate move_and_slide() calls and consume get_speed_multiplier(). Backward compat test updated for _physics_process addition. All 190 new tests pass. Full suite (run_tests.sh) exits 0. Lint clean.
