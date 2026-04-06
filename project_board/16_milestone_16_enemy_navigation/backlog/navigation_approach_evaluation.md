# TICKET: navigation_approach_evaluation

Title: Evaluate NavigationAgent3D vs. direct X-axis pursuit for 2.5D

## Description

Before implementing enemy movement, decide whether Godot's `NavigationAgent3D` (with a baked NavigationMesh) or a simpler direct X-axis pursuit model is the right approach for this 2.5D game. Document the decision as an ADR in the ticket or spec.

Key considerations:
- All characters are at Z=0; the game is effectively 1D (X axis movement)
- NavigationAgent3D provides obstacle avoidance but requires NavigationMesh baking per room
- Direct pursuit (move toward player.position.x) is simpler and sufficient if obstacles are just walls
- Rooms are generated procedurally — NavigationMesh must rebake or be pre-baked per template

## Acceptance Criteria

- A decision is documented (ADR format) in the scoped run log or ticket
- If direct pursuit: reasoning for why NavigationAgent3D is not needed is stated
- If NavigationAgent3D: a proof-of-concept enemy moves to the player in `test_movement_3d.tscn`
- Decision is made before `enemy_seek_and_pursue` ticket begins implementation

## Dependencies

- M5 (generated enemy scenes must be in place)
