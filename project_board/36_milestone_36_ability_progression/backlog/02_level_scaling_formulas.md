# TICKET: 02_level_scaling_formulas

**Milestone:** M36 Ability Progression & Leveling  
**Status:** Backlog  
**Type:** Implementation

## Title

Level Scaling Formulas — damage/cooldown scaling per mutation level

## Description

Define scaling curves: damage scales +15% per level, cooldown scales -10% per level (faster recharge). Executor applies formula based on active mutation level before attack execution.

## Acceptance Criteria

- [x] Damage formula: `base_damage * (1.0 + 0.15 * (level - 1))`
- [x] Cooldown formula: `base_cooldown * (1.0 - 0.10 * (level - 1))`
- [x] Scaling applied per-attack (not global)
- [x] Level 1 = base stats (no modifier)
- [x] Level 5 = 60% damage boost, 40% cooldown reduction
- [x] Formulas exported/tweakable per mutation (or global default)
- [x] Tests verify scaling math
- [x] `run_tests.sh` exits 0

## Dependencies

- M36:01 (level tracking)
- M11 (attack resource / executor)

## Implementation Notes

**Scaling in executor:**
```gdscript
func apply_level_scaling(attack: AttackResource, level: int) -> AttackResource:
    var scaled = attack.duplicate()
    scaled.damage *= (1.0 + 0.15 * (level - 1))
    scaled.cooldown *= (1.0 - 0.10 * (level - 1))
    return scaled
```

## Scope Notes

- Simple linear formulas (no exponential curves in this ticket)
- Range/knockback not scaled in base ticket (future)

