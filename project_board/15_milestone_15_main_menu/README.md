# Epic: Milestone 15 – Main Menu

**Goal:** The game has a proper entry point — a main menu that lets the player start a run, quit, and understand the context before gameplay begins.

## Scope

- Main menu scene with at minimum: Start Run, Quit
- Transition from menu to the roguelike run (RunStateManager / RunSceneAssembler)
- Game Over / run-end screen with basic run stats (mutations absorbed, rooms cleared) and a Restart option that routes back through the run system
- Clean state on restart — mutations cleared, HP reset, room sequence regenerated
- Minimal visual polish: readable layout, consistent with the game's aesthetic

## Out of Scope (For Now)

- Settings menu (explicitly deferred per board Non-Goals)
- Save/load or persistent meta-progression (deferred)
- Credits, lore, or narrative screens
- Animated intro or logo sequence

## Design Notes

- The menu does not need to be visually elaborate — legible and functional first
- Game Over screen should reinforce the roguelike loop: run ends, stats shown, restart is the primary call to action
- RunStateManager already has a death/restart state; the menu and game-over screen plug into this existing machine — do not bypass or replace it

## Dependencies

- M6 (Roguelike Run Structure) — RunStateManager and RunSceneAssembler must be in place before the menu can wire into them

## Exit Criteria

A fresh game launch lands on a main menu. The player can start a run, play, die, see a game-over screen, and restart — all without touching the editor or debug tools. No orphaned scenes or state leakage between runs.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
