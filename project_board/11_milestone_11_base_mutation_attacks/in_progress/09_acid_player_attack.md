# TICKET: 09_acid_player_attack

Title: Acid mutation attack — ranged acid spit with damage over time

## Description

When the player has the acid mutation active and presses the attack input, Blobert spits an acid projectile. On enemy hit, the enemy takes a damage-over-time debuff for 3s. If the enemy is already WEAKENED, the DoT duration is doubled.

## What's Already Done

The generic PROJECTILE_SPIT pipeline and acid modifier hook are implemented:
- `AttackExecutor._handle_projectile_spit()` creates `PlayerProjectile3D` with damage, speed, knockback, modifiers (M11-05)
- `PlayerProjectile3D._on_body_entered()` calls `apply_acid(duration, dps)` when `acid_on_hit` modifier is set (M11-05)
- Projectile collision, consumed flag, and despawn logic verified (M11-13)

## Remaining Work

- [ ] Register an acid-specific `AttackResource` in the attack database with tuned values (cooldown 2.0s)
- [ ] Implement actual DoT tick system in `EnemyBase` — current `apply_acid()` is a duck-typed stub with no tick logic
- [ ] DoT tick interval: every 0.5s for 3.0s
- [ ] WEAKENED state doubles DoT duration to 6.0s
- [ ] DoT non-stacking: same-source acid refreshes duration instead of stacking
- [ ] Visually distinct acid projectile (differentiate from adhesion projectile)

## Acceptance Criteria

- Acid projectile is visually distinct from adhesion projectile
- Projectile travels along the X axis and hits the first enemy
- On hit, enemy takes DoT damage every 0.5s for 3.0s
- If enemy is WEAKENED, DoT duration increases to 6.0s
- DoT does not stack from the same mutation (only one acid DoT per enemy at a time; refreshes on re-hit)
- Attack cooldown: 2.0s
- `run_tests.sh` exits 0

## Dependencies

- ~~`attack_input_and_cooldown_framework`~~ (done — M11-03/04/05/06)
- ~~M11-14 (Enemy Health & Damage Reception)~~ (done — enemies have `take_damage()`, `apply_acid()`, and DoT system via EnemyEffectTracker)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PASS (187/187 — 83 behavioral + 104 adversarial, 0 failures)
- AC1 (visual distinction): EVIDENCED — acid Color.CHARTREUSE vs claw Color.ORANGE_RED; color property on PlayerProjectile3D set by executor. Tests: APA-6a/b/c/d, ADV color tests.
- AC2 (X-axis travel, first hit): EVIDENCED — PlayerProjectile3D._physics_process moves along X; _on_body_entered consumes on first hit. Tests: APA-7a/b/d, ADV second-body-after-consumed.
- AC3 (DoT 0.5s tick, 3.0s duration): EVIDENCED — EnemyEffectTracker.DOT_TICK_INTERVAL=0.5; acid_duration=3.0 in resource/database. Tests: APA-4a, APA-1g, APA-2d, APA-3a/f.
- AC4 (WEAKENED doubles to 6.0s): EVIDENCED — get_base_state()==1 check in both AttackExecutor and PlayerProjectile3D. Tests: APA-3b/g/i/j, ADV weakened tests.
- AC5 (non-stacking, refresh): EVIDENCED — EnemyEffectTracker.add_dot refreshes duration. Tests: APA-5a/b/c, ADV rapid-refresh, last-write-wins.
- AC6 (cooldown 2.0s): EVIDENCED — ACID_COOLDOWN=2.0 in attack_database.gd. Tests: APA-1c, APA-2d, APA-7c, ADV cooldown.
- AC7 (run_tests.sh exits 0): EVIDENCED (self-reported by implementation agent checkpoint).
- Static QA: Not Run
- Integration: Not Run
- Git State: FAIL — implementation files modified but uncommitted and unpushed

## Blocking Issues
- Work not committed/pushed. `git status` shows 3 modified files (scripts/attacks/attack_database.gd, attack_executor.gd, player_projectile_3d.gd) and 2 untracked test files (tests/scripts/attacks/test_acid_attack.gd, test_acid_attack_adversarial.gd). Per workflow_enforcement_v1.md "Commit and Push BEFORE COMPLETE Closure" rule, all implementation work must be committed and pushed before Stage can transition to COMPLETE. This is non-negotiable.

## Escalation Notes
All 7 acceptance criteria have explicit behavioral test evidence. The sole blocker is the uncommitted/unpushed git state — a workflow compliance gap from the implementation handoff.

---

# NEXT ACTION

## Next Responsible Agent
Gameplay Systems Agent

## Required Input Schema
None

## Status
Proceed

## Reason
All 7 acceptance criteria are behaviorally evidenced by 187 passing tests (83 behavioral + 104 adversarial). However, the implementation agent did not commit or push before handoff. The Gameplay Systems Agent must: (1) `git add` the 3 modified files and 2 new test files under scripts/attacks/ and tests/scripts/attacks/; (2) commit with a conventional commit message; (3) `git push` to origin. Once committed and pushed, re-route to Acceptance Criteria Gatekeeper Agent for final COMPLETE transition.
