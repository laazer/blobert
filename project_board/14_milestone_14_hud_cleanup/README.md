# Epic: Milestone 14 – HUD Cleanup

**Goal:** The HUD communicates only what the player needs, when they need it — no debug labels, no legacy artifacts, no visual clutter.

## Current State

The existing HUD (`InfectionUI` / `game_ui.tscn`) accumulated nodes across multiple milestones:
- `HPLabel` + `HPBar` — health display (functional, keep)
- `MutationSlot1Label`, `MutationIcon1`, `MutationSlot2Label`, `MutationIcon2` — dual-slot display (functional, keep)
- `FusionActiveLabel` — fusion state indicator (functional, keep)
- `AbsorbPromptLabel`, `FusePromptLabel` — contextual prompts (functional, keep)
- `ChunkStatusLabel` — debug-quality label ("Chunk: Attached"), candidate for removal or icon replacement
- `ClingStatusLabel` — debug-quality label ("Wall Cling: ON"), candidate for removal or icon replacement
- `MutationSlotLabel`, `MutationIcon` — legacy single-slot nodes kept for backward compat (DSM-4-AC-8), candidates for removal
- `AbsorbFeedbackLabel` — absorb confirmation feedback (review for necessity)
- Input hint labels (`MoveHint`, `JumpHint`, etc.) — togglable but visible by default; candidates for auto-hide after first use

## Scope

- Audit every HUD node: keep, replace with icon, or remove
- Remove or replace debug-quality text labels with visual indicators where appropriate
- Remove legacy backward-compat nodes (`MutationSlotLabel`, `MutationIcon`) once no tests reference them
- Ensure mutation slots display mutation family name or icon clearly (not raw ID string)
- Input hints auto-hide after first relevant action is performed (or after N seconds)
- HUD layout does not overlap key gameplay areas (player model, chunk, enemies)
- HUD remains fully functional after cleanup — no regressions to existing mechanics

## Design Notes

- Chunk and cling status may be better communicated through player visual state (M11) than HUD text — coordinate with M11 scope
- Mutation slot display should eventually show family-specific icon or color (M11 dependency), but text label is acceptable until then
- Do not remove nodes that are referenced by tests without first updating or retiring those tests

## Dependencies

- M2 (Infection Loop) — HUD originated here; all current functionality must survive cleanup
- M3 (Dual Mutation + Fusion) — dual-slot and fusion label nodes are M3 deliverables
- M11 (Blobert Visual Identity) — some HUD elements may become redundant once Blobert's model reflects mutation state

## Exit Criteria

A non-developer watching gameplay can understand Blobert's HP, active mutations, and available actions without reading any debug-style text. No placeholder or legacy nodes remain in the HUD scene. All existing HUD-related tests pass.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
