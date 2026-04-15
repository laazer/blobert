# Epic: Milestone 28 – Enemy Editor Attacks & Abilities Tab

**Goal:** Add a dedicated Attacks/Abilities workflow to the asset editor so users can define reusable ability models, compose attacks from those abilities, and assign finalized attacks to either enemy or player configurations without leaving the editor.

## Scope

- **Attacks/Abilities tab shell**: new top-level editor tab with split views for abilities and attacks
- **Ability model authoring**: create/edit/delete/version ability models with typed parameters
- **Attack authoring & ability assignment**: compose an attack type by assigning one or more ability models plus timing/cooldown metadata
- **Validation and export integration**: ensure attack payloads are schema-valid and round-trip through registry JSON consumed by the pipeline
- **Entity assignment**: assign attack types to both enemy and player configs

## Out of Scope

- Runtime combat balancing and gameplay tuning in Godot
- Full combat simulation preview in the web editor
- Networked collaborative editing
- Per-frame animation timeline tools for attack choreography
- Auto-migration of legacy attack payloads from historical formats

## Dependencies

- M23 (Asset Editor Pipeline MCP) — API and registry plumbing patterns reused for model operations
- M25 (Visual Expression) — established editor panel/navigation patterns reused for the new tab
- M26 (Animation System) — attack timing fields should align with existing animation metadata conventions
- M27 (Raw Builder Mode) — mode/state handling approach informs tab-level store separation

## Exit Criteria

- A user can create a new ability model, edit its typed parameters, save it, and reuse it across multiple attacks
- A user can create an attack type, assign one or more ability models to it, validate it, and persist it to the model registry payload used by the pipeline
- A user can assign saved attack types to enemy and player configurations
- Attack and ability definitions round-trip through backend APIs and are reloaded accurately in the editor

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Verified, merged
