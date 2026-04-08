# Epic: Milestone 10 – Procedural Enemies in Level & Attack Loop

**Goal:** New animated enemy models are wired into procedurally generated rooms, and enemies run a continuous attack loop so combat in runs is representative of shipping gameplay.

## Scope

- Integrate exported/generated enemy scenes (GLB + attack metadata where applicable) into the procedural room / run assembly path (same pipeline that builds levels for roguelike runs — not only the sandbox test level).
- Ensure spawned enemies use the correct scene variants, animation clips, and family/mutation metadata consistent with `EnemyBase` / infection hooks.
- Drive enemy attacks on a loop (idle → telegraph → strike → recovery or equivalent) aligned with existing attack systems (M8), using exported clip names / timing where present.
- Validate at least one combat-room template spawns these enemies and they attack the player without manual placement.

## Dependencies

- M5 (Procedural Enemy Generation) — game-ready enemy scenes and naming
- M6 (Roguelike Run Structure) — room templates and procedural chaining
- M7 (Enemy Animation Wiring) — clips available in Godot
- M8 (Enemy Attacks) — damage, hitboxes, telegraphs
- M9 (Enemy & Player Model Review / Materials) — mesh/material baseline for models shown in runs (coordinate timing; technical wiring may start earlier)

## Exit Criteria

Procedurally assembled runs include enemies using the new models; those enemies repeatedly execute attacks when engaging the player, with no editor-only setup required.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
