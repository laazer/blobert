# M12-02 Gameplay Systems Agent Run — 2026-05-29

## Ticket
`project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md`

## Stage
IMPLEMENTATION_GAMEPLAY

## Agent
Gameplay Systems Agent

## Summary

Implemented all 6 fused attack registration blocks in `scripts/attacks/attack_database.gd` per
spec `project_board/specs/fused_attack_resources_spec.md`.

## Implementation

Modified file: `scripts/attacks/attack_database.gd`

Added 40 named constants (6 combos x ~6-7 numeric properties each) after the existing 4 base
attack constant blocks. Added 6 `register_fused_attack()` calls in `_register_defaults()` after
the final `register_base_attack("adhesion", adhesion)` call.

Fused attacks registered:
- acid_claw (ID 101): MELEE_SWIPE, damage=4.0, cooldown=1.5, range=1.5, knockback=3.0, acid modifiers
- adhesion_claw (ID 102): MELEE_SWIPE, damage=3.5, cooldown=2.0, range=1.5, knockback=1.0, slow:0.0 modifiers
- carapace_claw (ID 103): SLAM_AOE, damage=5.0, cooldown=3.0, range=2.5, knockback=6.0, startup=8, infect_weakened
- acid_adhesion (ID 104): PROJECTILE_SPIT, damage=2.0, cooldown=3.0, speed=10.0, lifetime=1.75, combined acid+slow modifiers
- acid_carapace (ID 105): SLAM_AOE, damage=4.5, cooldown=4.0, range=3.5, knockback=4.0, startup=12, acid modifiers
- adhesion_carapace (ID 106): SLAM_AOE, damage=3.5, cooldown=3.5, range=3.0, knockback=2.0, startup=12, slow:0.0 modifiers

## Spec Discrepancies Resolved

The ticket prompt contained out-of-range stats (cooldowns/damages that differ from the spec).
The frozen spec at `project_board/specs/fused_attack_resources_spec.md` (Revision 1) is authoritative.
All values were taken from the spec Section 4 stat blocks, not the ticket example values.

Key spec-vs-ticket-prompt deltas confirmed via spec and test files:
- acid_claw cooldown: spec=1.5 (not 1.2 from ticket prompt)
- adhesion_claw: spec=cooldown 2.0, range 1.5, knockback 1.0 (ticket prompt said 1.5/1.6/2.5)
- acid_carapace: spec=damage 4.5 (ticket prompt said 5.5)

## Critical Implementation Decisions

1. **slow:0.0 falsy trap (FAR-EC-1):** adhesion_claw, acid_adhesion, adhesion_carapace all use
   `"slow": 0.0` (not `"slow": false` or absent). This is the M11-11 root-encoding pattern.
   The value is a float zero that signals full stop; tests verify `has("slow")` AND
   `typeof() == TYPE_FLOAT` AND `== 0.0`.

2. **SLAM_AOE startup_frames:** carapace_claw=8, acid_carapace=12, adhesion_carapace=12.
   All non-zero per ADV-13 test invariant.

3. **Named constants:** Every non-identity numeric literal uses a named const. Identity literals
   (0, 0.0) are used inline as per spec DR-4 exemption.

4. **attack_id for acid_carapace:** spec table header says `acid_id` (FAR-EC-7 typo). Used
   `attack_id` property (correct GDScript property name).

## Test Results

Pending: `timeout 300 godot --headless -s tests/run_tests.gd`

The test runner must be invoked by the parent orchestrator/CI before Stage advance to STATIC_QA.

## gd-review Notes

All fused registration blocks use only named constants for non-identity numeric literals.
No inline tuning literals appear in the fused sections. Identity literals (0, 0.0) are
exempt per DR-4 and spec Section 3 (FAR-1 Constraints).

## Checkpoint Assumptions

None. All values directly from frozen spec Section 4. No judgment calls required.
