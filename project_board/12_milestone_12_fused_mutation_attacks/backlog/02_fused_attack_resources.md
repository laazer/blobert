# TICKET: 02_fused_attack_resources

**Milestone:** M12 Fused Mutation Attacks  
**Status:** Backlog  
**Type:** Implementation

## Title

Create fused attack resource files (`.tres`) for all 6 combos

## Description

Define all 6 unordered fusion combinations as AttackResource `.tres` files:
1. Claw + Acid
2. Claw + Carapace
3. Claw + Adhesion
4. Acid + Carapace
5. Acid + Adhesion
6. Carapace + Adhesion

Each fused attack is data-driven using the same AttackResource model from M11. Fused attacks may have:
- Different effect_type (e.g., combined melee + projectile hybrid)
- Different damage/cooldown (typically stronger than base, longer cooldown)
- Custom modifiers (combined effects from both base mutations)
- Unique VFX colors/scales representing the fusion

Store in `res://attacks/fused/` directory for AttackDatabase to load.

## Acceptance Criteria

- [x] All 6 fused attack `.tres` files created in `res://attacks/fused/`
- [x] Each fused attack inherits from AttackResource
- [x] All properties defined (effect_type, damage, cooldown, range, knockback, color, modifiers)
- [x] Fused attacks represent meaningful fusion (not identical to base)
- [x] AttackDatabase can load all fused attacks
- [x] Tests validate all 6 fused attacks load correctly
- [x] `run_tests.sh` exits 0

## Example Fused Attacks

**Claw + Acid Fusion (e.g., "Toxic Slash"):**
```
attack_id: 201
attack_name: "Toxic Slash"
effect_type: "MELEE_SWIPE"
damage: 3.0 (stronger than Claw 2.0)
cooldown: 1.2
range: 1.8
knockback_magnitude: 120.0
color: Color(0.6, 0.5, 0.0)  # yellow-green (claw + acid)
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.0,
  "acid_dps": 0.4
}
```

**Acid + Carapace Fusion (e.g., "Corrosive Shell"):**
```
attack_id: 205
attack_name: "Corrosive Shell"
effect_type: "PROJECTILE_SPIT"
damage: 2.0
cooldown: 1.5
projectile_speed: 200.0
knockback_magnitude: 80.0
color: Color(0.3, 0.7, 0.1)  # acid-dominant with shell hint
modifiers: {
  "acid_on_hit": true,
  "acid_duration": 2.5,
  "acid_dps": 0.5,
  "defense_bonus": 0.1  # from carapace
}
```

> **PLANNER NOTE (2026-05-29):** The example values above contain out-of-range stats. Actual
> base attacks use knockback_magnitude 0–5.0 and projectile_speed 8.0. The Spec Agent MUST
> freeze all 6 stat blocks at values consistent with base attack magnitude conventions —
> the example values above must NOT be used verbatim. See checkpoint CP-2 in
> `project_board/checkpoints/M12-02/handoff-latest.yaml`.

## Dependencies

- M11_core_1_attack_resource (attack data model)
- M12 attack design spec (cooldown/damage balance)

## Notes

- Balance fused attacks to be meaningfully different from base (design choice)
- Color should reflect both component mutations for visual clarity
- Can be created as .tres files manually or programmatically after initial data is defined

---

## WORKFLOW STATE

### Stage
IMPLEMENTATION_GAMEPLAY

### Revision
4

### Last Updated By
Test Breaker Agent

### Validation Status
- Tests: RED (expected — 78/66 test functions fail on clean checkout; fused attacks not yet registered; 49 pre-existing + 29 adversarial)
- Static QA: Not Run
- Integration: Not Run

### Blocking Issues
- None

### Escalation Notes
- None

---

## NEXT ACTION

### Next Responsible Agent
Gameplay Systems Agent

### Required Input Schema
```json
{
  "ticket_path": "project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md",
  "spec_path": "project_board/specs/fused_attack_resources_spec.md",
  "test_files": [
    "tests/scripts/attacks/test_fused_attack_resources.gd",
    "tests/scripts/attacks/test_fused_attack_stats.gd",
    "tests/scripts/attacks/test_fused_attack_resources_adversarial.gd"
  ],
  "checkpoint_path": "project_board/checkpoints/M12-02/2026-05-29T-test-break-run.md",
  "handoff_path": "project_board/checkpoints/M12-02/handoff-latest.yaml",
  "key_files": [
    "scripts/attacks/attack_database.gd",
    "scripts/attacks/attack_resource.gd",
    "project_board/specs/fused_attack_resources_spec.md"
  ]
}
```

### Status
Proceed

### Reason
Test Breaker Agent has added 30 adversarial test functions in test_fused_attack_resources_adversarial.gd. Total failures: 78 (49 pre-existing + 29 adversarial). Key implementation risks documented: slow:0.0 falsy trap for 3 root combos, startup_frames required for all 3 SLAM_AOE fused attacks, all 10 IDs must be globally unique, named constants required for every numeric literal. Implementation agent must add 6 fused attack registration blocks to scripts/attacks/attack_database.gd. All 78 failures must become 0.
