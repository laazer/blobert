# TICKET: 11_adhesion_player_attack

Title: Adhesion mutation attack — sticky projectile that briefly immobilises enemies

## Description

When the player has the adhesion mutation active and presses the attack input, Blobert fires a sticky projectile that briefly immobilises the first enemy it hits (root effect, ~1.0s). The attack interacts with the infection loop: a rooted enemy is easier to infect.

## What's Already Done

The generic PROJECTILE_SPIT pipeline and slow modifier hook are implemented:
- `AttackExecutor._handle_projectile_spit()` creates `PlayerProjectile3D` with modifiers (M11-05)
- `PlayerProjectile3D._on_body_entered()` calls `apply_slowness(multiplier, duration)` when `slow` modifier is set (M11-05)
- Projectile collision, consumed flag, velocity, and despawn on lifetime verified (M11-13)

## Remaining Work

- [ ] Register an adhesion-specific `AttackResource` with tuned values (cooldown 2.5s, projectile range 10 units)
- [ ] Implement full root effect: movement set to 0 for 1.0s (current `apply_slowness` is a multiplier, not a hard root)
- [ ] Root interaction with infection loop: rooted enemy is easier to infect
- [ ] Projectile despawns on wall collision (current despawn is lifetime-only)
- [ ] Visually distinct adhesion projectile

## Acceptance Criteria

- Firing projectile is visible and travels along the X axis from the player
- Projectile hits the first enemy in its path and despawns
- On hit, enemy movement is set to 0 for 1.0 seconds
- Enemy in NORMAL state can be infected during the root window (existing infection flow applies)
- Projectile despawns on wall collision or after max range (configurable, default 10 units)
- Attack cooldown: 2.5s
- `run_tests.sh` exits 0

## Dependencies

- ~~`attack_input_and_cooldown_framework`~~ (done — M11-03/04/05/06)
- ~~M11-14 (Enemy Health & Damage Reception)~~ (done — enemies have `take_damage()` and `apply_slowness()`)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Pass — 180 adhesion tests (98 behavioral + 82 adversarial) pass; full suite run_tests.gd exits 0. Commits: 36daa53 (tests), 9680eae (impl).
- Static QA: Pass — gd-review and gd-organization pre-commit hooks passed on all modified files.
- Integration: Pass — adhesion registered in AttackDatabase with correct PROJECTILE_SPIT pipeline, root effect (slow:0.0, slow_duration:1.0), wall despawn, cooldown 2.5s, effective range 10u (8.0 speed * 1.25s lifetime). All 7 AC items have explicit automated test coverage with no manual verification gaps.

## Blocking Issues
None

## Escalation Notes
None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
None

## Status
Proceed

## Reason
All 7 acceptance criteria verified with explicit automated evidence: (1) X-axis travel + color distinction tested, (2) first-enemy-consumes semantics + despawn tested, (3) root effect (speed=0 for 1.0s) tested via EnemyEffectTracker + executor + projectile paths with adversarial boundary coverage, (4) infection-during-root tested (claw can infect rooted+weakened; adhesion alone does not infect), (5) wall collision despawn + lifetime despawn + effective range 10.0 tested, (6) cooldown 2.5s exact value tested, (7) full test suite exits 0 confirmed. No manual verification items in AC. Ticket moved to done/.
