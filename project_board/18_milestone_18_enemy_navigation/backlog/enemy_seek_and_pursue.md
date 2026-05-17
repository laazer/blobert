# TICKET: enemy_seek_and_pursue

**Milestone:** M18 Enemy Navigation  
**Status:** Backlog  
**Type:** Implementation (Enemy AI)

## Title

Enemy seek and pursue — movement toward player with state-dependent speed

## Description

Implement pursuit movement for enemies. When player enters detection range, enemy moves toward player along X-axis. Movement respects enemy state: NORMAL=100% speed, WEAKENED=50% speed, INFECTED=no pursuit. Stop before reaching attack range to prevent walking through player.

## Acceptance Criteria

- [x] Detection system
  - Enemy detects player at configurable range (export var, default 8 units)
  - Detection updates continuously (every frame or on range change)
- [x] Pursuit movement
  - Enemy moves toward player along X-axis
  - Movement speed configurable per-family (export var)
  - Smooth movement (no jerky teleporting)
- [x] State-based speed modifiers
  - **NORMAL state**: 100% movement speed
  - **WEAKENED state**: 50% movement speed
  - **INFECTED state**: 0% (no pursuit)
  - State changes apply immediately
- [x] Attack range stopping
  - Enemy stops at configurable attack range (default 1.5 units)
  - Does not walk into/through player
  - Slight clearance for visual separation
- [x] Pursuit exit conditions
  - Exit pursuit if player leaves detection range (>8 units)
  - Exit pursuit if enemy enters INFECTED state
  - Return to patrol or idle on exit
- [x] Animation support
  - Run/pursuit animation plays during movement
  - Animation speed matches movement speed
  - Smooth transition to idle/patrol on pursuit exit
- [x] Testing and validation
  - Manual test: Trigger detection, enemy pursues
  - Manual test: Change state to WEAKENED, speed reduces
  - Manual test: Infect enemy, pursuit stops
  - Manual test: Exit range, enemy stops pursuing
- [x] All M8 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M8 (Enemy Attacks) — Enemy base class and state machine
- M18 ticket 01: enemy_idle_patrol (returns to patrol on pursuit exit)
- M18 ticket 04: navigation_approach_evaluation

## Implementation Notes

- Direction: calculate `(player.x - enemy.x).sign()` for left/right movement
- Stop distance: prevent overlap with player hitbox
- Animation: use run/pursuit clip during movement
- State check: query enemy state machine before each movement tick

## Example Movement Logic

```gdscript
func _process_pursuit():
    var direction = (player.position.x - position.x).sign()
    var current_speed = movement_speed
    
    # Apply state modifier
    if enemy_state == WEAKENED:
        current_speed *= 0.5
    elif enemy_state == INFECTED:
        current_speed = 0.0
    
    # Check attack range
    var distance_to_player = abs(player.position.x - position.x)
    if distance_to_player <= attack_range:
        current_speed = 0.0
    
    # Apply movement
    velocity.x = direction * current_speed
```

## Configuration

```gdscript
@export var detection_range: float = 8.0
@export var movement_speed: float = 3.5
@export var attack_range: float = 1.5
@export var weakened_speed_mult: float = 0.5
```

## Notes

- Pursuit is core AI: smooth implementation critical
- State modifiers make infection meaningful (temporarily stops pursuits)
- Attack range prevents visual weirdness (walking into player)
