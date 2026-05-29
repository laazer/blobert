# TICKET: M12-04

**Milestone:** M12 Fused Mutation Attacks  
**Type:** Implementation

## Title

Acid + Claw fusion attack — venomous shred (3-hit combo with stacking poison)

## Description

Fusing acid and claw mutations creates a rapid melee attack that applies acid DoT on every hit. Unlike the base acid attack (which has a single DoT instance with refresh), each claw swipe in the combo poisons the enemy with a *separate* stacking acid instance. This rewards staying in melee range for sustained damage — three successful hits at close range create three independent DoT stacks that tick simultaneously.

Implementation builds on the `fusion_attack_framework` (M12 ticket 03) to combine Claw's hitbox/knockback mechanics with Acid's DoT application system.

## Acceptance Criteria

- Fusion attack resource created: `attacks/resources/acid_claw_fusion.tres`
  - Effect type: `MELEE_SWIPE_COMBO`
  - Damage per hit: 1.8
  - Combo hits: 3
  - Attack cooldown: 2.0s
  - Range: 1.2
  - Knockback per hit: 80.0 (direction: away)
- Attack executor integrates with FusionAttackFramework
  - Claw hitbox spawns at frame 6, 12, 18 (startup)
  - Each hit applies unique acid DoT via `AcidVFXSystem`
  - Acid modifier: `{ "acid_duration": 2.5, "acid_dps": 0.4 }`
- DoT stacking verified: 3 simultaneous stacks visible in enemy debug display
  - Stacks do NOT refresh each other; each decays independently
  - Damage tick rate matches base acid (10Hz)
- Attack feedback implemented:
  - Melee swipe sound triggers per hit
  - Poison VFX color overlay on enemy per applied stack
  - Knockback applies per hit
- Attack balanced in test encounters
  - DPS: ~1.2 per combo at full 3 stacks (3 hits × 1.8 damage + 3 stacks × 0.4 acid DPS for 2.5s)
  - Cooldown enforces 2.0s between combos (prevents spam)
- Attacks database entry created (`attacks.json`)
- All M11 prerequisite tests still pass
- `run_tests.sh` exits 0

## Dependencies

- M12 ticket 01: fused_attack_database_integration (done)
- M12 ticket 03: fusion_attack_framework (done)
- M11 ticket 04: attack_resource (base attack class)
- M11 ticket 05: attack_executor_handlers

## Implementation Notes

- Hitbox timing critical: each swipe must trigger collision detection separately
- Acid stacking: use `AcidVFXSystem.apply_acid()` three times (once per hit) to ensure separate instances
- Cannot refresh existing poison stacks (unlike base acid attack which refreshes)
- Test framework: verify 3 poison stacks with `enemy.acid_stacks.size() == 3` after successful combo

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
5

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Written (RED — implementation not yet present)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason
Test Designer Agent wrote 73 test functions across 3 files: tests/scripts/attacks/test_acid_claw_combo_attack.gd (41 tests, AC-1 through AC-6), tests/scripts/attacks/test_acid_claw_combo_adversarial.gd (14 tests, AC-EC-1 through AC-EC-10 + failure modes), tests/scripts/enemies/test_enemy_acid_stacking.gd (18 tests, AC-3 isolated). All tests target executable runtime behavior. Tests are RED as expected: combo_hits field, MELEE_SWIPE_COMBO handler, _apply_combo_modifiers, add_acid_stack/get_acid_stack_count, and acid_claw registration updates not yet implemented. Test Breaker Agent must attempt to make tests pass minimally and report which break.
