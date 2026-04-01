# TICKET: enemy_seek_and_pursue

Title: Enemy seek and pursue — enemies move toward player when in detection range

## Description

Implement movement behavior for all 4 enemy families: when the player enters detection range, the enemy moves toward the player along the X axis. When the player exits range or the enemy is INFECTED, the enemy stops pursuing. Uses the approach determined in `navigation_approach_evaluation`.

## Acceptance Criteria

- Enemy detects player when player enters detection radius (configurable per family, default 8 units)
- Enemy moves toward the player along the X axis while in NORMAL or WEAKENED state
- Enemy does not pursue when INFECTED
- WEAKENED enemies move at 50% of their normal speed
- Enemy stops at attack range (does not walk through the player)
- Detection radius and move speed are exported variables
- `run_tests.sh` exits 0

## Dependencies

- `navigation_approach_evaluation`
- EnemyStateMachine (M2/M5) — state must be readable to determine pursuit behavior
