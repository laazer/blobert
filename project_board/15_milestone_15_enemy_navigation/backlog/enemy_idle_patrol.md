# TICKET: enemy_idle_patrol

Title: Enemy idle and patrol — behavior when player is out of detection range

## Description

When the player is outside detection range, enemies should not just stand frozen. Implement idle/patrol behavior: enemies pace back and forth along the X axis between two bounds, or stand idle with occasional movement. This makes the world feel alive before the player engages.

## Acceptance Criteria

- Enemy patrols between two patrol bounds (configurable via exported Vector3 or float offset)
- Patrol reverses direction when reaching a bound or a wall
- Enemy transitions from patrol to pursuit when player enters detection range
- Enemy returns to patrol after losing the player (player exits range for >2.0s)
- Idle/patrol animation plays during this state (Walk clip at low speed, or Idle clip)
- `run_tests.sh` exits 0

## Dependencies

- `enemy_seek_and_pursue`
