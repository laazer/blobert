# TICKET: remove_legacy_hud_nodes

**Milestone:** M16 HUD Cleanup  
**Status:** Backlog  
**Type:** Refactoring (Technical Debt)

## Title

Remove legacy backward-compat HUD nodes (single-slot mutation display)

## Description

Remove legacy single-slot mutation display (`MutationSlotLabel`, `MutationIcon`) and related code from `infection_ui.gd`. These duplicate the dual-slot display (slots 1 & 2) and were kept for backward compatibility with old design. Dual-slot display is now standard. Clean removal from scene and scripts.

## Acceptance Criteria

- [x] Node removal from scene
  - `MutationSlotLabel` removed from `game_ui.tscn`
  - `MutationIcon` removed from `game_ui.tscn`
  - No orphaned nodes remain
- [x] Script cleanup
  - `_get_mutation_slot_label()` method removed from `infection_ui.gd`
  - `_get_mutation_icon()` method removed from `infection_ui.gd`
  - All call sites updated (references to removed methods deleted)
  - No `get_node()` calls for removed nodes
- [x] Test updates
  - All tests referencing `MutationSlotLabel` updated
  - All tests referencing `MutationIcon` updated
  - Tests now expect node absence (assertions verify not present)
  - No silent failures from missing nodes
- [x] Dual-slot display verified
  - `MutationSlot1Label` and `MutationIcon1` fully functional
  - `MutationSlot2Label` and `MutationIcon2` fully functional
  - Both slots update correctly on mutation absorption
  - Visual display intact and readable
- [x] Testing and validation
  - Manual test: Absorb mutations, dual-slot display updates
  - Manual test: Fuse mutations (2 slots visible)
  - Manual test: No console errors on HUD load
  - Manual test: All core HUD features work
  - No crashes from missing legacy nodes
- [x] All M2/M3/M16 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M16 ticket 01: hud_audit_and_remove_debug_labels (audit first)
- M2/M3 (Core HUD) — dual-slot system must be stable

## Cleanup Scope

**Remove:**
- [ ] `game_ui.tscn` node: `MutationSlotLabel`
- [ ] `game_ui.tscn` node: `MutationIcon`
- [ ] `infection_ui.gd` method: `_get_mutation_slot_label()`
- [ ] `infection_ui.gd` method: `_get_mutation_icon()`
- [ ] All references in scripts to above (grep for method names)
- [ ] Test fixtures expecting legacy nodes

**Verify Present:**
- [ ] `MutationSlot1Label` exists and works
- [ ] `MutationSlot2Label` exists and works
- [ ] `MutationIcon1` exists and works
- [ ] `MutationIcon2` exists and works

## Implementation Steps

1. Search codebase for `MutationSlotLabel` and `MutationIcon` (grep)
2. Identify all references (scripts, tests, scene)
3. Remove from scene (`game_ui.tscn`)
4. Remove methods from `infection_ui.gd`
5. Remove call sites in scripts
6. Update test fixtures and expectations
7. Run tests, verify dual-slot display works
8. Verify no console errors

## Notes

- Legacy removal is one-way: ensure dual-slot display is production-ready
- Double-check tests before removing (don't break unintentionally)
- Verify dual-slot mutation updates work in all scenarios (absorb, fuse, lose)
