# MAINT-HCSI — Test Designer run 2026-04-05

**Ticket:** `project_board/maintenance/in_progress/hud_components_scale_input.md`  
**Spec:** `project_board/specs/hud_components_scale_input_spec.md`  
**Stage handoff:** TEST_DESIGN → TEST_BREAK  

## Summary

- Added `tests/ui/test_hud_components_scale_input.gd`: HCSI-4 (root type/name/script + flat + nested paths), HCSI-1 (`hud_scale` float default 1.0), HCSI-5 (global rect size ratios at `hud_scale` 2.0 + cross-widget factor match + property round-trip), HCSI-6 (global rects within 3200×1880 at default scale, spot nodes).
- Updated `tests/ui/test_player_hud_layout.gd`: `_control_design_rect()` for scene-local `offset_*` (design space); T-6.7–T-6.10 and comments trace MAINT-HCSI / HCSI-2.
- Updated `tests/levels/test_fusion_opportunity_room.gd` T-42: viewport bounds use `get_global_rect()` (HCSI-6); nonzero size still from design-space offsets (AC-FUSE-HUD-1.8).

## Spec gaps / assumptions (for Spec Agent if any)

- **HCSI-1 naming:** Tests require the exported property name `hud_scale` on the GameUI instance (matches spec primary name). If implementation aliases only `scale` on a `Control` owner, tests must be updated in the same PR or export `hud_scale` as the single designer-facing knob.

## Would have asked

- None (spec names `hud_scale` explicitly).

## Assumption made

- Headless `get_global_rect()` after `add_child` is non-degenerate for HPBar and `Hints/MoveHint` at default layout (same assumption as existing HUD layout tests).

## Confidence

High for path and scale-ratio contracts; medium until implementation confirms setter runs before rect read without an extra frame.
