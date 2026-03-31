# Epic: Milestone 12 – Advanced Terrain

**Goal:** The environment is dangerous — terrain hazards create meaningful navigation decisions and reinforce mutation identity.

## Scope

- **Tar pits** — slow movement, adhesion-mutation immune or reduced effect; player sinks gradually
- **Lava pits** — continuous burn damage; carapace mutation reduces or negates
- **Spikes** — static instant-damage geometry; claw mutation may interact (climb?)
- **Spike traps** — triggered spikes (proximity or timed), telegraphed before activation
- **Acid traps** — area-denial acid pools; acid mutation immune or reduced effect

Each hazard must:
- Deal damage or apply a status effect on contact
- Have a clear visual read so the player can react in time
- Have at least one mutation that interacts meaningfully (immunity, reduced damage, or bonus)

## Design Notes

- Hazards reinforce the value of absorbing the right enemy — carapace keeps you alive in lava, acid lets you walk through acid traps
- Hazards should appear in the roguelike room templates (M6) as placeable elements
- Asset generation: tar, lava, spike, and acid visuals may need Blender or shader work

## Dependencies

- M4 (Prototype Level) — collision and physics baseline
- M9 (Base Mutation Attacks) — mutation identity established before immunity interactions are meaningful

## Exit Criteria

All 5 hazard types are placeable in a level, deal damage or apply effects correctly, and at least one mutation interaction works per hazard type. A skilled player can use mutations to navigate hazards a non-mutated player cannot.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
