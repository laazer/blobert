# Epic: Milestone 16 – Camera & Screen Juice

**Goal:** Hits feel impactful, abilities feel powerful, and the camera keeps the action readable — the game feels good to play, not just functional.

## Scope

- **Screen shake:** configurable magnitude and decay; triggered on player hit, chunk impact, ability use, enemy death
- **Hit pause / hitstop:** brief freeze (1–3 frames) on heavy hit confirmation to sell impact
- **Camera lead:** camera anticipates movement direction slightly rather than hard-following player position
- **Combat zoom:** slight zoom-in during active combat, reset when no enemies in range
- **Room transition:** smooth pan or fade between rooms rather than instant cut
- **Ability visual feedback:** mutation attacks have a visible wind-up or impact frame (VFX placeholder acceptable)
- All effects are tunable via exported variables — not hardcoded

## Out of Scope

- Particle systems or full VFX passes (those belong in M11 / Blobert Visual Identity or a dedicated VFX milestone)
- Audio — handled separately
- Cutscenes or cinematic sequences

## Design Notes

- Screen shake and hit pause are the highest-value additions for perceived game feel; prioritize these
- Camera lead and combat zoom are secondary — implement only after shake and hitstop feel good
- All juice effects should be optional/disableable so they don't interfere with playtesting other mechanics
- Godot's `Camera3D` tween system is the preferred implementation path for smooth follow

## Dependencies

- M1 (Core Movement) — basic camera follow already exists; this milestone extends it
- M8 (Enemy Attacks) — hit reactions and attack impacts are the primary juice triggers
- M9 (Base Mutation Attacks) — ability feedback targets mutation attack moments

## Exit Criteria

A 30-second combat clip looks and feels noticeably more impactful than the same clip without juice. Screen shake triggers on hits. Hitstop is present on heavy hits. Camera leads movement. Room transitions are not instant cuts.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
