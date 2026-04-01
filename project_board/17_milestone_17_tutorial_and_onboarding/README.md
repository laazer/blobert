# Epic: Milestone 17 – Tutorial & Onboarding

**Goal:** A first-time player understands how to move, throw a chunk, infect an enemy, and absorb a mutation without reading a manual.

## Scope

- Dedicated intro room (no enemies) that teaches movement and chunk mechanics through environment prompts
- Progressive hint system: show the relevant control prompt at the moment the player needs it, not all at once
- Infection tutorial: one pre-placed weakened enemy in a safe room with a prompt guiding the player through infect → absorb
- Hint auto-dismissal: once the player performs the action, the hint disappears and does not return
- Input hints already exist on the HUD (`InputHintsConfig`); this milestone makes them contextual and progressive rather than always-on
- Tutorial rooms are part of the roguelike run intro sequence — not a separate game mode

## Out of Scope

- Voice acting or narration
- Tooltip system for advanced mechanics (fusion, fused attacks) — those are surfaced through UI, not tutorial
- Separate tutorial level or mode — tutorial rooms must work within the existing RunSceneAssembler flow

## Design Notes

- The existing input hints (`MoveHint`, `JumpHint`, `DetachHint`, etc.) are the building block — this milestone makes them fire at the right moment
- The mutation tease room from M4 already introduces mutation; the tutorial room precedes it and covers movement + chunk
- Coordinate with M14 (HUD Cleanup) — tutorial hints must survive or be updated alongside any HUD node cleanup
- Do not over-explain: one mechanic per room, brief prompt, player executes, hint clears

## Dependencies

- M1 (Core Movement) — movement mechanics must be stable
- M2 (Infection Loop) — infection and absorb must be working
- M4 (Prototype Level) — room structure and RunSceneAssembler integration required
- M13 (Main Menu) — tutorial runs after the player hits Start; must route correctly from menu into tutorial intro room
- M14 (HUD Cleanup) — coordinate hint node ownership

## Exit Criteria

A person who has never seen the game can complete the tutorial rooms and reach the first combat room without asking for help. All core mechanics (move, jump, chunk throw, infect, absorb) are demonstrated once before the player encounters a threatening enemy.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
