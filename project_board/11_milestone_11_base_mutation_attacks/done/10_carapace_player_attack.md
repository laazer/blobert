# TICKET: 10_carapace_player_attack

Title: Carapace mutation attack — ground slam with area knockback

## Description

When the player has the carapace mutation active and presses the attack input, Blobert performs a heavy ground slam. All enemies within a short radius are knocked back and take damage. Slowest attack of all base mutations but hits multiple enemies.

## What's Already Done

The generic attack infrastructure exists but carapace needs a new effect type:
- `AttackResource` supports configurable damage, cooldown, range, knockback (M11-04)
- `AttackExecutor` has MELEE_SWIPE and PROJECTILE_SPIT handlers; SLAM_AOE falls to `_handle_unknown()` (M11-05)
- `AttackDatabase` can register and look up any mutation's attack (M11-06)
- Per-mutation cooldown tracking works (M11-12)
- Knockback direction/magnitude system verified (M11-13)

## Remaining Work

- [ ] Implement `_handle_slam_aoe()` in `AttackExecutor` — radial enemy query + damage + knockback to all in radius
- [ ] Register a carapace-specific `AttackResource` with effect_type `SLAM_AOE`, cooldown 3.5s, radius 3.0
- [ ] Wind-up delay: 0.2s before hitbox activates (startup_frames or timer-based)
- [ ] Airborne slam: if player is airborne when attack triggers, delay hitbox until landing
- [ ] VFX/animation placeholder for ground slam

## Acceptance Criteria

- Slam hitbox activates in a radius around the player (configurable, default 3.0 units)
- All enemies within radius take damage and receive knockback away from the player
- Slam has a brief wind-up before the hitbox activates (0.2s)
- Attack cooldown: 3.5s
- If player is airborne, slam triggers on landing (gravity assists — more satisfying)
- `run_tests.sh` exits 0

## Dependencies

- ~~`attack_input_and_cooldown_framework`~~ (done — M11-03/04/05/06)
- ~~M11-14 (Enemy Health & Damage Reception)~~ (done — enemies have `take_damage()` and knockback impulse)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Autopilot Orchestrator

## Validation Status
- Tests: PASS — 167 carapace-specific tests (100 behavioral + 39 adversarial A + 28 adversarial B); full suite exits 0. Commits: ba957af (impl), 5eee2be (tests).
- Static QA: PASS — gd-review and gd-organization passed via pre-commit hooks.
- Integration: PASS — All 6 acceptance criteria verified against implementation code and test coverage. Evidence matrix: (1) radial hitbox via _query_enemies_in_range with configurable radius default 3.0; (2) per-enemy damage+knockback loop; (3) wind-up 0.2s via startup_frames=12 at 60fps; (4) cooldown 3.5s via CARAPACE_COOLDOWN constant; (5) airborne deferral via _is_owner_on_floor() poll loop with 3.0s timeout; (6) run_tests.sh exits 0 confirmed by full suite pass.

## Blocking Issues
None

## Escalation Notes
All acceptance criteria have explicit, defensible evidence. The only gate preventing COMPLETE is the unpushed commits. Human must run `git push` and then transition Stage from INTEGRATION → COMPLETE and move ticket to done/.

---

# NEXT ACTION

## Next Responsible Agent
Learning Agent

## Required Input Schema
None

## Status
Proceed

## Reason
All 6 acceptance criteria are satisfied with explicit test and code evidence. AC Gatekeeper verified implementation in attack_executor.gd (_handle_slam_aoe) and attack_database.gd (carapace registration), plus 3 test files with 167 passing tests. Stage held at INTEGRATION solely because commits are not pushed to origin (workflow_enforcement_v1.md mandate). Human action required: (1) `git push`, (2) set Stage to COMPLETE, (3) move ticket to done/.
