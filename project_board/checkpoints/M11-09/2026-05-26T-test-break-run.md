# M11-09 — Acid Player Attack (Test Break)

**Run:** 2026-05-26T-test-break-run
**Agent:** Test Breaker Agent
**Ticket:** `project_board/11_milestone_11_base_mutation_attacks/in_progress/09_acid_player_attack.md`
**Spec:** `project_board/specs/acid_player_attack_spec.md`

## Summary

40 adversarial tests written to `tests/scripts/attacks/test_acid_attack_adversarial.gd` (833 lines). Combined with 33 primary tests = 73 total behavioral tests for M11-09.

## Adversarial Dimensions Covered

| Dimension | Count | Tests |
|-----------|-------|-------|
| Null & Empty | 6 | acid_on_hit false, empty modifiers, missing duration/dps fallbacks |
| Boundary | 5 | zero damage, huge duration/dps, near-zero duration, cooldown precision |
| State Machine | 5 | state=99, state=-1, dead enemy (both paths), WEAKENED→INFECTED mid-DoT |
| Projectile Consumed | 4 | second body, pre-consumed, bare target, no apply_acid |
| Non-Stacking Refresh | 4 | DPS change, WEAKENED→NORMAL duration, independent tracking, stop_all |
| Registration Safety | 3 | double registration, cross-entry isolation, nonexistent key |
| Concurrency/Order | 3 | active flag, acid+poison coexistence (executor + projectile) |
| Mutation Testing | 2 | integer truthy, int duration/dps |
| Visual Distinction | 2 | color difference, executor sets color |
| Determinism | 2 | repeated NORMAL and WEAKENED runs |
| Stress/Load | 2 | 10x rapid refresh, 20 concurrent DoTs |
| Assumption Checks | 2 | DEFAULT_ACID_DPS constant sync, explicit vs fallback DPS |

## Gaps Discovered

1. **_apply_modifiers does NOT guard against dead targets** — Current AttackExecutor._apply_modifiers (line 109-114) does not check `target.is_dead()` before calling `apply_acid`. In production, `EnemyBase.apply_acid()` guards on `_is_dead`, but this is a defense-in-depth gap. Test `test_adv_dead_enemy_executor_path` documents this — the mock exposes that the modifier logic itself doesn't check death.

2. **Missing WEAKENED doubling logic** — Both AttackExecutor (line 109-114) and PlayerProjectile3D (line 68-73) call `apply_acid` with raw duration from modifiers. The spec (APA-3) requires checking `target.get_base_state() == 1` and doubling duration. Tests `test_adv_weakened_to_infected_mid_dot`, `test_adv_refresh_weakened_then_normal_duration`, and `test_adv_repeated_weakened_identical_output` will fail until implementation adds this logic.

3. **Missing color property on PlayerProjectile3D** — No `color` var exists. Test `test_adv_executor_projectile_color_set` will fail until added.

4. **Missing color-set in _handle_projectile_spit** — `_handle_projectile_spit()` does not set `projectile.color = resource.color` (line 73-89). Same test covers this.

## Implementation Notes for Gameplay Systems Agent

- Add WEAKENED doubling logic to `_apply_modifiers()` in **both** `scripts/attacks/attack_executor.gd` (acid_on_hit branch, line 109-114) and `scripts/attacks/player_projectile_3d.gd` (acid_on_hit branch, line 68-73). Pattern per spec APA-3: check `target.has_method("get_base_state") and target.get_base_state() == 1`, then `acid_dur *= 2.0`.
- Add `var color: Color = Color.WHITE` to `PlayerProjectile3D`.
- Add `projectile.color = resource.color` in `AttackExecutor._handle_projectile_spit()`.
- Register acid `AttackResource` in `AttackDatabaseNode._register_defaults()` following the claw pattern.
- Declare `ACID_*` constants at module level in `attack_database.gd`.

## Checkpoints

### [M11-09] TEST_BREAK — Mock death guard gap
**Would have asked:** Should _apply_modifiers in AttackExecutor check target.is_dead() before applying acid, or is the guard in EnemyBase.apply_acid() sufficient?
**Assumption made:** EnemyBase.apply_acid() guard is the intended defense (APA-3e, EC-5); documenting the mock gap in test_adv_dead_enemy_executor_path without requiring implementation change.
**Confidence:** High
