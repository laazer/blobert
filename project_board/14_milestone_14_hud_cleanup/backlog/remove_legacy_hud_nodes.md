# TICKET: remove_legacy_hud_nodes

Title: Remove legacy backward-compat HUD nodes (MutationSlotLabel, MutationIcon)

## Description

`infection_ui.gd` retains a legacy single-slot label (`MutationSlotLabel`) and icon (`MutationIcon`) for backward compatibility with DSM-4-AC-8. These nodes duplicate the dual-slot display and confuse the HUD layout. This ticket removes them once no tests reference them.

## Acceptance Criteria

- `MutationSlotLabel` removed from `game_ui.tscn`
- `MutationIcon` removed from `game_ui.tscn`
- `_get_mutation_slot_label()` and `_get_mutation_icon()` and their call sites removed from `infection_ui.gd`
- All tests that reference these node names updated (expect absence rather than presence)
- Dual-slot labels (`MutationSlot1Label`, `MutationIcon1`, `MutationSlot2Label`, `MutationIcon2`) continue to function correctly
- `run_tests.sh` exits 0

## Dependencies

- `hud_audit_and_remove_debug_labels` (audit first to understand all references)
