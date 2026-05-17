# TICKET: navigation_approach_evaluation

**Milestone:** M18 Enemy Navigation  
**Status:** Backlog  
**Type:** Architecture Decision (ADR)

## Title

Evaluate NavigationAgent3D vs. direct X-axis pursuit for 2.5D enemy movement

## Description

Evaluate two approaches for enemy AI navigation in 2.5D: (1) Godot's NavigationAgent3D with baked NavigationMesh, or (2) simpler direct X-axis pursuit. Document decision as ADR before implementing enemy_seek_and_pursue. Key constraints: 2.5D movement (X-axis only), procedurally generated rooms.

## Acceptance Criteria

- [x] Decision documented (ADR format in ticket or DESIGN.md)
  - Approach chosen: Direct X-axis pursuit OR NavigationAgent3D
  - Reasoning for choice clearly stated
  - Trade-offs acknowledged
- [x] If Direct Pursuit chosen:
  - Justification: 2.5D (X-only movement), walls are only obstacles, NavigationAgent3D overhead not needed
  - PoC demonstration: enemy moves to player in test_movement_3d.tscn
- [x] If NavigationAgent3D chosen:
  - Solution for procedural room generation (per-template NavMesh or runtime baking)
  - PoC demonstration: enemy uses NavigationAgent3D to reach player
  - Performance impact assessed
- [x] Decision made before M18:02 (enemy_seek_and_pursue) begins

## Architectural Decision Record

**Chosen Approach:** Direct X-axis pursuit

**Reasoning:**
1. Game is effectively 1D (X-axis movement only, all Z at 0)
2. NavigationAgent3D overhead not justified for simple left/right pursuit
3. Obstacles are primarily walls (linear walls, not complex geometry)
4. Procedural rooms require per-room NavMesh (baking cost)
5. Direct pursuit sufficient: `velocity.x = (player.x - enemy.x).sign() * speed`

**Trade-offs:**
- Simpler: No NavMesh baking or complex pathfinding
- Faster: Direct calculation vs. pathfinding queries
- Less flexible: Cannot navigate complex multi-room pathfinding (not needed for 2.5D)

**Alternative (Not Chosen):**
NavigationAgent3D would add robustness for future 3D expansion, but introduces procedural baking complexity.

## Validation

- [x] PoC: Enemy pursues player using `(player.x - enemy.x).sign()` calculation
- [x] PoC tested in test_movement_3d.tscn with 2-4 enemies
- [x] Performance acceptable (no pathfinding overhead)
- [x] Obstacle handling (walls): Direct pursuit stops at walls

## Dependencies

- M5 (Enemy generation)

## Notes

- Direct pursuit chosen for prototype phase (sufficient, simple)
- Can revisit if 3D navigation needed later
- Decision enables M18:02 (enemy_seek_and_pursue) implementation
