# Epic: Milestone 11 – Blobert Visual Identity

**Goal:** You can tell what mutation Blobert has at a glance — the model reflects the active mutation state.

## Scope

- Blobert model or texture updates per base mutation (4 variants)
- Fused state produces a visually distinct blended or combined look
- Neutral/no-mutation state has a clear default appearance
- Transitions between states are smooth (not jarring instant swaps)
- Visual identity does not conflict with the existing infection state color feedback (M3)

## Asset Generation Dependency

New Blobert model variants or texture sets will likely require Blender work. This milestone has a significant asset production component before Godot wiring can begin.

## Dependencies

- M3 (Dual Mutation + Fusion) — mutation and fusion state system in place
- M9 (Base Mutation Attacks) — mutation identity fully established in gameplay

## Exit Criteria

A new player can identify Blobert's active mutation from across the room without looking at the UI. Fusion state is visually distinct from all base states.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
