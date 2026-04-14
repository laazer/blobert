# Epic: Milestone 26 – Enemy Editor Animation System

**Goal:** Let users define how their enemy moves — idle loops, locomotion style, and per-part animation behaviors — producing enemies that feel alive in the 3D preview and translate correctly into Godot's animation pipeline.

## Scope

- **Animation mode selector**: Static / Move / Stretch as top-level modes
- **Movement direction control**: axis and speed/intensity for Move mode
- **Per-part animation parameters**: per-part override for animation type (bob, wiggle, pulse), axis, speed, and amplitude

## Out of Scope

- Custom keyframing or timeline authoring
- Physics-based or simulation-driven animation
- Animation export or Godot AnimationPlayer wiring (that is M7 territory)
- Eye animation (blinking, tracking)

## Dependencies

- M25 (Visual Expression) — part selection and properties panel must be stable before per-part animation extends them
- M21 (3D Model Quick Editor) — 3D preview canvas must support live animation playback

## Exit Criteria

- A user can set an enemy to Move mode with lateral direction, configure the head to bob independently, and see both animations composited correctly in the live preview
- All animation settings round-trip through enemy config JSON

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Verified, merged
