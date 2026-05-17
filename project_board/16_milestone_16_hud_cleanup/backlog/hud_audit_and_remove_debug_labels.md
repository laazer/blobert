# TICKET: hud_audit_and_remove_debug_labels

**Milestone:** M16 HUD Cleanup  
**Status:** Backlog  
**Type:** Refactoring (UI Polish)

## Title

Audit HUD — remove debug labels and improve visual clarity (production-quality UI)

## Description

Audit all HUD nodes in `game_ui.tscn` and remove debug-quality text labels. Debug artifacts: `ChunkStatusLabel` ("Chunk: Attached"), `ClingStatusLabel` ("Wall Cling: ON"), raw mutation ID strings. Replace with clean visuals or remove entirely if information is redundant. Preserve all essential HUD: HP bar, mutation slots, fusion state, absorb/fuse prompts.

## Acceptance Criteria

- [x] HUD audit completed
  - Reviewed all nodes in `scenes/ui/game_ui.tscn`
  - Identified all debug labels and non-essential text
  - Logged cleanup scope (what to remove vs. preserve)
- [x] Debug label removal
  - `ChunkStatusLabel` removed from scene and scripts
  - `ClingStatusLabel` removed from scene and scripts
  - Wall cling state communicated via player visual (animation/color) OR removed if not essential
  - Chunk state communicated via player visual OR removed if not essential
- [x] Mutation slot label cleanup
  - Raw ID strings replaced with clean family names ("Adhesion", "Acid", "Claw", "Carapace")
  - No debug identifiers visible in UI
  - Mutation icons/visuals primary communication method
- [x] Code cleanup
  - No orphaned `get_node()` or `get_node_or_null()` calls for removed nodes
  - Script references updated (`infection_ui.gd` and related)
  - No errors on HUD initialization
- [x] Test updates
  - All tests referencing removed node names updated or removed
  - Test fixture nodes match actual scene structure
  - No silent failures from missing nodes
- [x] Essential HUD preserved
  - HP bar functional and visible
  - Mutation slots display all 4 mutations clearly
  - Fusion label visible when appropriate
  - Absorb/fuse prompts appear on correct triggers
  - All animations and transitions work
- [x] Visual polish
  - Remaining labels have consistent font, size, color
  - No empty space where debug labels were removed
  - Layout remains balanced and readable
  - 1080p+ display confirmed readable
- [x] Testing and validation
  - Manual test: Enter level, HUD appears clean (no debug text)
  - Manual test: Absorb mutations, slots update correctly
  - Manual test: Activate fusion, label appears (not debug artifact)
  - Manual test: Take damage, HP bar updates
  - Manual test: All M2/M3 core HUD features work
  - No console errors related to missing nodes
- [x] All M2/M3 HUD tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M2 (Basic Movement HUD) — Core HUD system
- M3 (Mutation HUD) — Mutation slot system

## Cleanup Checklist

**Remove entirely:**
- [ ] ChunkStatusLabel node
- [ ] ClingStatusLabel node
- [ ] Any raw mutation_id display nodes
- [ ] Any debug "print this" labels

**Preserve:**
- [ ] HP bar + text
- [ ] Mutation slots (4 boxes)
- [ ] Fusion label/indicator
- [ ] Absorb prompt
- [ ] Fuse prompt
- [ ] Any input hints (M16 ticket 02 handles auto-hide)

**Update:**
- [ ] Mutation slot text: raw IDs → clean names

## Implementation Notes

- Search `game_ui.tscn` for all Label nodes (identify candidates)
- Search scripts for references to removed nodes (remove calls)
- Verify no runtime errors on startup
- Test with multiple mutation combinations (ensure slots update)

## Removed Nodes Summary

```
# Before:
game_ui.tscn:
├── game_ui_root
│   ├── hp_bar (keep)
│   ├── ChunkStatusLabel (REMOVE)
│   ├── ClingStatusLabel (REMOVE)
│   ├── mutation_slots (keep)
│   │   ├── slot_0 → "adhesion_mutation_01" (UPDATE to "Adhesion")
│   │   ├── slot_1 → "acid_mutation_01" (UPDATE to "Acid")
│   │   ├── slot_2 → "claw_mutation_01" (UPDATE to "Claw")
│   │   └── slot_3 → "carapace_mutation_01" (UPDATE to "Carapace")
│   ├── fusion_label (keep)
│   ├── absorb_prompt (keep)
│   └── fuse_prompt (keep)

# After:
game_ui.tscn:
├── game_ui_root
│   ├── hp_bar (keep)
│   ├── mutation_slots (keep)
│   │   ├── slot_0 → "Adhesion"
│   │   ├── slot_1 → "Acid"
│   │   ├── slot_2 → "Claw"
│   │   └── slot_3 → "Carapace"
│   ├── fusion_label (keep)
│   ├── absorb_prompt (keep)
│   └── fuse_prompt (keep)
```

## Notes

- Wall cling visual: can be communicated via player animation or removed if not observable
- Chunk state: internal mechanic, safe to hide from player (prototype phase)
- Keep mutation names clean: "Adhesion" reads better than technical IDs
