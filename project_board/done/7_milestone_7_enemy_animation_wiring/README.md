# Epic: Milestone 7 – Enemy Animation Wiring

**Goal:** Generated enemies look alive — state-appropriate animations play in Godot driven by EnemyStateMachine.

## Scope

- Blender asset generation update: ensure each enemy family exports named animation clips (Idle, Walk, Hit, Death) in the GLB
- AnimationPlayer wiring per generated enemy scene: map EnemyStateMachine states to animation clips
- Shared animation controller script (or per-family override) that responds to state transitions
- Hit reaction and death animation play-through before despawn
- Animations do not interfere with physics (CharacterBody3D movement still driven by code)

## Asset Generation Dependency

The existing Blender Python pipeline (`asset_generation/python/`) will likely need updates to bake named animation clips into exported GLBs. Tickets in this milestone should include a Blender-side task before the Godot wiring tasks.

## Exit Criteria

Enemies idle, react to being hit, and play a death animation when killed. You can tell at a glance whether an enemy is alive or dead.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
