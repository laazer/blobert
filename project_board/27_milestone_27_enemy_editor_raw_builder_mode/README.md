# Epic: Milestone 27 – Enemy Editor Raw Builder Mode

**Goal:** Unlock power-user control with a from-scratch construction workflow where users select individual components (body, head, arms, legs) and place them with precise numeric spatial control, without being constrained by preset archetypes.

## Scope

- **Builder mode entry point**: blank canvas with no default enemy loaded; independent of preset mode
- **Component type selector**: per-category selection (body base, head, leg, arm) from a fixed set of primitive options
- **Precise placement controls**: numeric position, rotation, and scale inputs per placed part with reset-to-default

## Out of Scope

- Custom mesh import
- Per-instance arm/leg variation (both arms share one type in this milestone)
- 3D viewport gizmos or drag-based placement
- Undo/redo history
- Draft persistence across page reloads
- Loading a saved config back into builder mode (forward-compat serialization only)

## Dependencies

- M25 (Visual Expression) — part properties panel pattern must be established; color, texture, rotation controls reused here
- M26 (Animation System) — animation panel should be composable with builder-mode parts

## Exit Criteria

- A user can enter builder mode, select a box body, cone head, stub legs, and sphere arms, set numeric positions for each, and produce a valid enemy config that the existing preview renders correctly
- All placements round-trip through enemy config JSON

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Verified, merged
