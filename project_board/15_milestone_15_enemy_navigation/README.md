# Epic: Milestone 15 – Enemy Navigation & AI

**Goal:** Enemies actively pursue and respond to the player — a non-mutated player is in genuine danger from an approaching enemy.

## Scope

- Basic seek/pursue behavior: enemies move toward the player when in detection range
- Idle/patrol state when player is out of range
- Path following on the 2.5D constrained plane (X axis movement; Z locked)
- Separation behavior: enemies don't stack on top of each other
- Detection range and aggro radius configurable per enemy family
- Enemy AI does not break physics (CharacterBody3D movement still code-driven)
- Navigation integrates with EnemyStateMachine (NORMAL, WEAKENED, INFECTED states each have appropriate movement behavior — INFECTED stops pursuing)

## Design Notes

- Because the game is 2.5D (all characters at Z=0), full 3D NavigationAgent3D may be overkill — a simpler left/right pursuit on the X axis may be sufficient for the prototype
- Evaluate `NavigationAgent3D` vs. direct X-axis pursuit before committing to either — checkpoint the decision
- WEAKENED enemies should move slower, not stop entirely
- INFECTED enemies are absorbed by the player and should not continue chasing

## Dependencies

- M5 (Procedural Enemy Generation) — enemy scenes and EnemyStateMachine must exist
- M7 (Enemy Animation Wiring) — movement should drive Walk animation; dependency is soft (navigation can be implemented without animation, wired together in M7)

## Ordering Note

This milestone should be completed before M8 (Enemy Attacks). Enemy attacks are only threatening if enemies can close distance. Implementing attacks on stationary enemies produces a gameplay experience that will need to be re-evaluated once navigation lands.

## Exit Criteria

Enemies detect the player when within range, move toward them, and stop or slow when in WEAKENED/INFECTED state. At least one enemy family can reliably back a player into a corner with no mutations active.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
