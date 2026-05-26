# TICKET: 08_claw_player_attack

Title: Claw mutation attack — fast melee swipe with short cooldown

## Description

When the player has the claw mutation active and presses the attack input, Blobert performs a fast melee swipe in the facing direction. Short cooldown encourages aggressive play. A WEAKENED enemy hit by a claw swipe transitions directly to INFECTED (skipping the standard infect interaction window).

## What's Already Done

The generic MELEE_SWIPE pipeline is fully implemented and verified:
- `AttackResource` with configurable damage, cooldown, range, knockback (M11-04)
- `AttackExecutor._handle_melee_swipe()` queries enemies in range, applies damage + knockback + modifiers (M11-05)
- `AttackDatabase` registers and looks up attacks by mutation id (M11-06)
- Per-mutation cooldown tracking in `PlayerController3D` (M11-03, M11-12)
- Damage and knockback delivery verified with 69 automated tests (M11-13)

## Remaining Work

- [ ] Register a claw-specific `AttackResource` in the attack database with tuned values (range ~1.5, cooldown 0.8s)
- [ ] Implement WEAKENED → INFECTED state transition on claw hit (not in the generic executor — needs claw-specific post-hit logic or a modifier)
- [ ] VFX/animation placeholder for claw swipe
- [ ] Verify single-frame hitbox (hitbox active for one frame only, no multi-hit)

## Acceptance Criteria

- Swipe hitbox activates immediately in front of the player (short range, ~1.5 units)
- Swipe animation plays (or a visual indication — VFX placeholder acceptable)
- On hit, enemy takes damage
- If the enemy is WEAKENED, it transitions to INFECTED state (claw can trigger infection directly)
- Attack cooldown: 0.8s (shortest of all mutations)
- Hitbox is only active for one frame (no multi-hit from a single press)
- `run_tests.sh` exits 0

## Dependencies

- ~~`attack_input_and_cooldown_framework`~~ (done — M11-03/04/05/06)
- ~~M11-14 (Enemy Health & Damage Reception)~~ (done — enemies have `take_damage()` and HP tracking)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Pass (133/133 — ClawAttackTests 79/79, ClawAttackAdversarialTests 54/54, full suite ALL TESTS PASSED)
- Static QA: Pass (gd-review exit 0, gd-organization exit 0; numeric literals extracted to named constants)
- Integration: Pass (all implementation committed b05731b, spec+checkpoints committed b543fb3, pre-commit hooks clean)

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
Complete

## Reason
All 7 acceptance criteria verified with explicit evidence: (1) Swipe hitbox range ~1.5 units — attack_range=1.5 with HITBOX_RANGE_FACTOR=0.5 produces center at 0.75, radius 0.75, effective span 0–1.5; boundary tests confirm hit at 1.5, miss at 1.501. (2) VFX placeholder — melee_vfx_requested signal emitted with Color.ORANGE_RED and scale 1.2; tested on hit and whiff. (3) Damage delivery — take_damage(3.0, knockback) verified per-enemy. (4) WEAKENED→INFECTED — infect_weakened modifier with pre-damage state capture enforces two-hit invariant; dead guard prevents post-mortem infection; 10+ dedicated tests. (5) Cooldown 0.8s — AttackResource.cooldown asserted == 0.8 and < 1.0. (6) Single-frame hitbox — exactly 1 hit per enemy per execute_attack(), no persistent Area3D, _is_active guard. (7) run_tests.sh exits 0 — 133/133 pass. Git state clean; all artifacts committed.
