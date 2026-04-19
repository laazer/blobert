# Epic: Milestone 29 – Elemental Combat Particles

**Goal:** Combat reads clearly in 3D: particle effects on the player, attacks, enemies, and terrain all reflect the **element of the currently active ability** (mutation attack / ability slot), so fire, ice, acid, poison, and physical reads are distinct at a glance.

## Scope

- **Authoritative element source:** runtime resolves “active ability element” from the same state that drives mutation attacks (active slot / equipped ability), aligned with existing combat type vocabulary (`physical`, `fire`, `ice`, `acid`, `poison`) where applicable
- **Shared VFX layer:** a small registry or factory maps element → particle presets (colors, meshes, emission rates, lifetimes) without duplicating logic in every caller
- **Player:** persistent or periodic particles on/near the player while the active ability implies a non-default element (and a clear neutral/minimal presentation for physical)
- **Attacks:** burst or trail particles on player attack execution and on enemy attack telegraphs / hit moments, keyed to that attack’s element
- **Enemies:** elemental read on enemies when relevant (e.g. family/attack element or active attack) using the same mapping — avoid one-off shaders per family unless specified in a ticket
- **Terrain:** contact and impact moments (landing, slides, certain collisions) emit element-appropriate particles when tied to combat context
- **Tuning:** exported variables or resource presets for designers; effects can be disabled for perf debugging

## Out of Scope

- Full screen-space post stacks, decals-only pipelines, or cinematic sequences
- New gameplay damage formulas or ability balance changes
- Asset editor UI for authoring particles (web editor); this milestone is Godot runtime + optional `.tscn` / `.tres` under `scenes/` / `resources/`
- Audio design and music

## Dependencies

- **M8** (Enemy Attacks) — attack timing, telegraphs, and enemy attack data paths
- **M11** (Base Mutation Attacks) — active mutation / attack slot semantics
- **M19** (Camera & Screen Juice) — juice hooks may trigger alongside particles; keep responsibilities separate
- **M28** (Enemy Editor Attacks & Abilities) — schema for ability/attack types may inform element fields; runtime should tolerate missing data with safe defaults until editor export is complete

## Exit Criteria

- With any supported element active, the player, concurrent attacks, visible enemies, and representative terrain interactions show **recognizably different** particle treatments in-engine
- One documented contract names the element enum/string set, where it is read at runtime, and how fallbacks work
- Automated tests cover the mapping and spawn API where headless Godot allows; remaining cases are listed for manual playtest with clear AC

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Verified, merged
