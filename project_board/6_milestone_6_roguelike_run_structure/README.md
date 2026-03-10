# Epic: Milestone 6 – Roguelike Run Structure

**Goal:** Complete run loop with procedurally assembled levels.

## Scope

- Run state manager (start, active, death, win)
- Room template system (intro, combat, mutation tease, fusion, cooldown, boss)
- Procedural room chaining per run
- Mutation reset on death
- Soft death state and run restart
- At least 2 combat rooms, 1 mutation tease, 1 boss room wired up

## Exit criteria

A full run can be started, played through procedurally arranged rooms, and ended
(win or death) with clean state reset and restart. No mutations carry over between runs.

## Status folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
