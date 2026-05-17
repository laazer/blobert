# TICKET: enemy_idle_patrol

**Milestone:** M18 Enemy Navigation  
**Status:** Backlog  
**Type:** Implementation (Enemy AI)

## Title

Enemy idle and patrol — behavior when player is out of detection range

## Description

Implement idle/patrol AI for enemies outside detection range. Enemies pace back and forth along X-axis between configurable bounds instead of standing frozen. Makes the world feel alive. Transition to pursuit on player detection, return to patrol after losing player (2.0s timeout).

## Acceptance Criteria

- [x] Patrol behavior implemented
  - Enemies walk back and forth between patrol bounds
  - Bounds configurable per-instance (export vars: `patrol_min_x`, `patrol_max_x`)
  - Movement speed: 60-70% of pursuit speed (leisurely pace)
  - Smooth animation transition between idle and patrol
- [x] Boundary and collision handling
  - Patrol reverses direction at bounds (does not overshoot)
  - Patrol reverses on wall collision (respects level geometry)
  - Detection range not exceeded during patrol
  - No enemies leaving intended patrol zone
- [x] State transitions
  - **IDLE**: patrol mode when player out of range
  - **PURSUING**: transition when player enters detection range (<10 units)
  - **RETURNING**: transition back to patrol after player lost >2.0s
  - All transitions smooth (no jarring changes)
- [x] Animation support
  - Patrol animation: Walk clip at slow speed OR idle with slight movement
  - Idle animation: looping idle pose (optional pacing in place)
  - Animation plays correctly throughout patrol cycle
- [x] Detection range integration
  - Patrol stays within room bounds (does not stray far from spawn)
  - Detection distance: ~10 units (configurable)
  - Pursuit triggers immediately on player entry
  - Return to patrol on player loss (2.0s+ out of range)
- [x] Testing and validation
  - Manual test: Approach enemy slowly, patrol continues until detection
  - Manual test: Trigger detection, enemy pursues
  - Manual test: Move away, lose detection, enemy patrols after 2s
  - Manual test: Multiple enemies patrol independently
- [x] All M8 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M8 (Enemy Attacks) — Enemy base class
- M18 ticket 02: enemy_seek_and_pursue (pursuit behavior)

## Implementation Notes

- Patrol: use Tween or lerp to smoothly move between bounds
- Reverse direction: flip velocity sign on bound reach
- 2.0s timeout: use timer on player loss, cancel on re-detection
- Animation: transition between idle and walk smoothly

## Example Configuration

```gdscript
@export var patrol_min_x: float = -5.0
@export var patrol_max_x: float = 5.0
@export var patrol_speed_mult: float = 0.65  # % of pursuit speed
@export var detection_range: float = 10.0
@export var return_to_patrol_timeout: float = 2.0
```

## Notes

- Patrol is foundation for living world (makes levels feel inhabited)
- Smooth transitions prevent AI feeling janky
- Configurable per-enemy allows variety (fast vs. slow patrol)
