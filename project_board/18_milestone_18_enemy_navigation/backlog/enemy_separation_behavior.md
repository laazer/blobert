# TICKET: enemy_separation_behavior

**Milestone:** M18 Enemy Navigation  
**Status:** Backlog  
**Type:** Implementation (Enemy AI)

## Title

Enemy separation — prevent enemy overlap with soft repulsion

## Description

Implement separation logic to prevent enemies from stacking on top of each other when pursuing. Apply soft repulsion force (not hard block) along X-axis only. Enemies still reach player eventually, just spread out spatially. Prevents "mob blob" visuals.

## Acceptance Criteria

- [x] Separation force implemented
  - Enemies detect nearby enemies (<2 units)
  - Apply repulsion force along X-axis
  - Strength: configurable (default 50% of pursuit speed)
- [x] Non-overlap achieved
  - 2+ enemies moving together do not fully overlap
  - Visual separation ~1.5 units between centers
  - Separation is soft (enemies can pass through if needed)
- [x] Movement not blocked
  - Separation does not prevent pursuing player
  - Enemies eventually reach player even with separation
  - Repulsion is suggestion, not absolute
- [x] Scalability
  - Works for 2-4 simultaneous enemies
  - No pathological behavior with groups
- [x] Testing and validation
  - Manual test: 2 enemies pursue, separate visually
  - Manual test: 4 enemies pursue, form loose group (no blob)
- [x] All M8/M18 tests pass
- [x] `run_tests.sh` exits 0

## Implementation

Apply separation during pursuit movement:
```gdscript
func _apply_separation():
    var nearby_enemies = find_nearby_enemies(2.0)
    for other in nearby_enemies:
        var direction = (position.x - other.position.x).sign()
        velocity.x += direction * separation_force
```

## Dependencies

- M18 ticket 02: enemy_seek_and_pursue

## Notes

- Soft repulsion prevents bunching without blocking pursuit
- X-axis only (maintains 2.5D gameplay)
