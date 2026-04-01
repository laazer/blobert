# TICKET: enemy_separation_behavior

Title: Enemy separation — enemies don't stack on top of each other

## Description

When multiple enemies pursue the player simultaneously, they must not overlap. Implement a simple separation force: enemies push each other apart when too close. This prevents the "mob blob" where all enemies occupy the same space.

## Acceptance Criteria

- Two enemies moving toward the same target do not fully overlap
- Separation force is applied along the X axis only (consistent with 2.5D constraint)
- Separation does not prevent enemies from eventually reaching the player (soft push, not hard block)
- Separation works for up to 4 simultaneous enemies (the 4 placed in test_movement_3d.tscn)
- `run_tests.sh` exits 0

## Dependencies

- `enemy_seek_and_pursue`
