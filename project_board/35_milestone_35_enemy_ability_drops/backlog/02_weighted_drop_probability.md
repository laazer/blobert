# TICKET: 02_weighted_drop_probability

**Milestone:** M35 Enemy Ability Drop System  
**Status:** Backlog  
**Type:** Implementation

## Title

Weighted Drop Probability — selection algorithm with rarity distribution

## Description

Implement weighted random selection algorithm that respects rarity weights. Verify distribution matches intended probabilities (e.g., common 60%, uncommon 25%, rare 12%, epic 3%).

## Acceptance Criteria

- [x] Weighted selection uses cumulative probability bins
- [x] Each call to select_drop() returns mutation respecting weights
- [x] Distribution test verifies weights (1000+ samples, chi-squared acceptable)
- [x] Rarity values customizable per drop table
- [x] Seeding for reproducible drops (for testing)
- [x] Tests verify selection with mock tables
- [x] `run_tests.sh` exits 0

## Dependencies

- M35:01 (drop table structure)

## Implementation Notes

**Weighted selection (Godot):**
```gdscript
func select_from_table(table: DropTable) -> String:
    var total_weight = 0.0
    for entry in table.drops:
        total_weight += entry.weight
    
    var rand_val = randf() * total_weight
    var cumulative = 0.0
    for entry in table.drops:
        cumulative += entry.weight
        if rand_val <= cumulative:
            return entry.mutation_id
    
    return table.drops[-1].mutation_id  # fallback
```

## Scope Notes

- No pseudorandom seed sequence (simple randf() OK)
- Distribution testing optional for code review (chi-squared test acceptable)

