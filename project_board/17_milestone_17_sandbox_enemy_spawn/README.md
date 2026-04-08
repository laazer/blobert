# Epic: Milestone 17 – Sandbox Enemy Spawn Stage

**Goal:** A dedicated sandbox where designers and playtesters can spawn any supported enemy on demand — fast iteration on attacks, AI, and feel without editing levels or the procedural run.

## Scope

- Standalone scene (or isolated sub-mode) using the normal player controller and camera
- Spawn workflow: select enemy family or concrete scene, spawn at a defined origin, in front of the player, or at a raycast hit — whichever matches existing debug patterns in the repo
- Clear or reset spawned enemies so the arena does not accumulate broken state
- One documented way to enter the sandbox (project setting, `main_scene` note in `CLAUDE.md`, or menu hook) so the whole team uses the same path
- Optional: duplicate spawn, clear-all hotkey, or simple on-screen list — keep UI minimal until M16/M20 HUD work conflicts

## Out of Scope

- Procedural room chaining or run state (use M6 paths for that)
- Full “level editor” or asset browser beyond enemies
- Shipping this as the default player-facing mode

## Dependencies

- M5 (Procedural Enemy Generation) — game-ready enemy scenes and `EnemyBase` hooks must exist
- M8 (Enemy Attacks) — soft dependency for meaningful combat playtest; sandbox is still useful earlier for placement and infection

## Exit Criteria

From a single launch into the sandbox, every current enemy family can be spawned without the editor, fought or weakened/infected as in the main game, and cleared for another spawn.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
