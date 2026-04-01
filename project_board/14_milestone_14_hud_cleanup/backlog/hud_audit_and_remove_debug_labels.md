# TICKET: hud_audit_and_remove_debug_labels

Title: Audit HUD — remove or replace debug-quality text labels

## Description

Several HUD labels are debug-quality text that should not appear in a shipped game: `ChunkStatusLabel` ("Chunk: Attached"), `ClingStatusLabel` ("Wall Cling: ON"), and the raw mutation ID string in slot labels. This ticket audits every node in `game_ui.tscn` and removes or replaces debug labels with appropriate visual alternatives or nothing if the information is redundant.

## Acceptance Criteria

- `ChunkStatusLabel` removed from `game_ui.tscn` and `infection_ui.gd` (chunk state communicated via player visual instead, or removed entirely for prototype)
- `ClingStatusLabel` removed (wall cling state communicated via player visual / M14 or removed for prototype)
- Mutation slot labels display family name cleanly (e.g. "Adhesion" not "adhesion_mutation_01")
- No `get_node_or_null` calls remain for removed nodes
- All tests that reference removed node names are updated or retired
- `run_tests.sh` exits 0

## Dependencies

- M2, M3 — existing HUD functionality must survive (HP bar, mutation slots, fusion label, absorb/fuse prompts all preserved)
