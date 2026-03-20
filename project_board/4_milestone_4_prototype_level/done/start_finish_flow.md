# Start → Finish flow

**Epic:** Milestone 4 – Prototype Level
**Status:** Done

---

## WORKFLOW STATE

| Field | Value |
|---|---|
| Stage | COMPLETE |
| Revision | 9 |
| Last Updated By | Human |
| Next Responsible Agent | — |
| Validation Status | HEADLESS: `tests/levels/test_start_finish_flow.gd` structural suite PASSED (scene contains milestone-scope nodes, `LevelExit` wiring includes `level_complete`, `RespawnZone` routes to `SpawnPosition`, `Player3D` aligns with `SpawnPosition`, `InfectionUI` prompts/hints exist, and X-axis adjacency/ordering invariants hold). MANUAL: Human confirmed full start-to-finish loop completed with no issues in-editor and no debug/cheats required, satisfying end-to-end playability and flow clarity criteria for this ticket. |
| Blocking Issues | — |

---

## Description

Ensure full start-to-finish flow: player spawns at start, plays through mutation tease, fusion opportunity, skill check, and mini-boss, then reaches level end. No debug tools required.

## Acceptance criteria

- [x] Level is completable from start to finish without debug or cheats
- [x] Flow is clear (signposting or layout so player knows direction)
- [x] Target 6–8 minutes playtime for first full run
- [x] All milestone 4 scope items are integrated and playable
- [x] Overall start→finish flow is human-playable in-editor: player, objectives, enemies, and critical UI are visible and understandable without debug overlays

---

# NEXT ACTION
## Next Responsible Agent
—

## Status
Proceed
