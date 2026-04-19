Title:
Player Element Particles (Active Ability)

Description:
When the player’s **active mutation / ability** implies an elemental identity, show particle feedback on or around the player (ambient loop, short bursts on slot change, or enhanced trail behavior) using the shared registry from ticket `02`. Physical / neutral should remain subtle and must not obscure infection feedback from M3.

Acceptance Criteria:
- Switching the active ability to an elemental mutation updates player-side particles within a bounded time (same frame or next process frame — document which)
- Each canonical non-physical element has a visibly distinct treatment in-engine (color/emission/shape differs; no copy-paste identical systems)
- Physical or default state uses a minimal preset that stays readable alongside existing slime/infection visuals
- Exported tuning variables (rates, scale, lifetime) live on the player scene or controller for quick iteration
- At least one automated test covers **state transition**: mocked or harness-driven active-element change results in the expected registry preset selection (no screenshot tests required)
- Tests reference this ticket path in a header comment: `project_board/29_milestone_29_elemental_combat_particles/backlog/03_player_element_particles_active_ability.md`
- `timeout 300 ci/scripts/run_tests.sh` exits 0

Scope Notes:
- Does not include full-screen post-processing
- If active-ability state is not yet exposed in a test-friendly way, ticket `02`’s registry tests must still pass; this ticket may add a minimal seam (signal or getter) only as needed

## Godot Implementation (indicative)

**Scenes / scripts**
- `scripts/player/player_controller_3d.gd` and/or `scenes/player/player_3d.tscn` — attach or drive particle nodes consistent with existing `ParticleTrail` usage

## WORKFLOW STATE

- **Stage:** BACKLOG
- **Revision:** 0
