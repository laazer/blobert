# TICKET: 01_mutation_drop_table_system

**Milestone:** M35 Enemy Ability Drop System  
**Status:** Backlog  
**Type:** Implementation

## Title

Mutation Drop Table System — per-enemy drop probability framework

## Description

Define drop tables mapping enemy families to mutation probabilities (common/uncommon/rare/epic). When enemy is absorbed via infection loop, consult table to determine which mutation is granted. Support weighted random selection.

## Acceptance Criteria

- [x] DropTable resource format: enemy_family → [(mutation_id, rarity_weight)]
- [x] Rarity tiers: common(1.0), uncommon(0.5), rare(0.25), epic(0.1) or similar
- [x] Weighted random selection: pick mutation using cumulative probability
- [x] All enemy families have drop tables defined
- [x] Fallback behavior for missing family (physical mutation or log warning)
- [x] Tests verify weighted selection distribution (statistical test acceptable)
- [x] `run_tests.sh` exits 0

## Dependencies

- M2 (infection loop framework)
- M11-M12 (mutation system)

## Implementation Notes

**DropTable structure (Godot resource):**
```gdscript
class_name DropTable extends Resource

@export var enemy_family: String
@export var drops: Array[DropEntry] = []

class DropEntry:
    @export var mutation_id: String
    @export var rarity: String  # "common", "uncommon", "rare", "epic"
    @export var weight: float = 1.0
```

## Scope Notes

- Drop tables hardcoded/data-driven per family (not procedurally generated)
- Rarity affects visual feedback, not mechanics in this ticket

