# TICKET: 03_inventory_integration_and_feedback

**Milestone:** M35 Enemy Ability Drop System  
**Status:** Backlog  
**Type:** Implementation

## Title

Inventory Integration & Feedback — grant mutation and visual notification

## Description

When mutation is selected from drop table, add to player inventory. Emit signal for UI to show notification (unlock animation, sound effect). Handle inventory slot management (M3).

## Acceptance Criteria

- [x] Infection loop calls drop selection on enemy absorption
- [x] Selected mutation added to player inventory via InfectionLoop interface
- [x] Signal emitted: `on_mutation_dropped(mutation_id, rarity)`
- [x] UI listens and shows notification (visual + audio)
- [x] If inventory full, queuing behavior matches M3 design (don't override the design)
- [x] No regression to infection loop timing
- [x] Tests verify mutation grant and signal emission
- [x] `run_tests.sh` exits 0

## Dependencies

- M35:01–02 (drop selection)
- M2 (infection loop)
- M3 (inventory / mutation slots)

## Implementation Notes

**Signal/callback in InfectionLoop:**
```gdscript
func on_enemy_absorbed(enemy: Enemy):
    var table = drop_table_manager.get_table(enemy.family)
    var mutation_id = drop_probability.select_from_table(table)
    player_inventory.grant_mutation(mutation_id)
    on_mutation_dropped.emit(mutation_id, get_rarity(mutation_id))
```

## Scope Notes

- No XP/progression in this ticket (M36 handles leveling)
- Notification UI owned by M37 (HUD system)

