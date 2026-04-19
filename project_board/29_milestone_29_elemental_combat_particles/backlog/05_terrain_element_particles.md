Title:
Terrain & Contact Element Particles

Description:
Emit element-appropriate particles when the player interacts with terrain in combat-relevant ways (e.g. landing, hard slide, wall impact) while an elemental active ability is in effect, using the registry from ticket `02`. Scope is **grounded, localized** VFX — not full-room terrain shaders.

Acceptance Criteria:
- At least three contact types are covered (e.g. land from air, slide, wall bump) with distinct or parameterized particle calls tied to the active element
- Physical / neutral uses the same fallback preset as other tickets; behavior is consistent with spec `01`
- Effects remain optional/disablable via a single exported flag or existing debug toggle pattern if one exists
- Automated tests: where full physics is unreliable headless, test the **decision function** (“given element + contact enum → preset id”) without requiring a full frame-perfect landing; document any skipped physics cases in the test file header
- Tests reference this ticket path in a header comment: `project_board/29_milestone_29_elemental_combat_particles/backlog/05_terrain_element_particles.md`
- `timeout 300 ci/scripts/run_tests.sh` exits 0

Scope Notes:
- Room tile materials and procedural mesh generation are out of scope unless a ticket explicitly adds decal hooks later
- Reuse movement/combat signals from `player_controller_3d` / movement sim where possible instead of polling every frame

## Godot Implementation (indicative)

**Scripts**
- `scripts/player/player_controller_3d.gd`, `scripts/movement/movement_simulation.gd` (read-only integration — avoid duplicating simulation rules)

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
