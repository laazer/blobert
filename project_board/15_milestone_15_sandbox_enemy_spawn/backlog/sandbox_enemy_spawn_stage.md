Title:
Sandbox enemy spawn stage

Description:
Add a dedicated sandbox scene and spawn controls so any generated enemy family can be instantiated at runtime for tuning and QA. Avoid reliance on procedural run assembly or manual scene edits.

Acceptance Criteria:
- One scene (or documented variant) loads player + empty arena suitable for combat
- Player can spawn at least one instance per current enemy family via UI or agreed debug input
- Spawned enemies use the same scripts/scenes as the main game (not duplicate hacks)
- Clear/reset removes or respawns enemies without leaving orphan nodes or broken state
- `CLAUDE.md` or this epic README documents how to launch the sandbox
