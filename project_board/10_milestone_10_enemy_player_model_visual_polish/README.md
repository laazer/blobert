# Epic: Milestone 10 – Enemy & Player Model Review / Materials

**Goal:** Every shipped enemy and the player model are reviewed for mesh quality, proportions, and material/color generation so they read clearly in-game and match the asset pipeline’s intended palette.

## Scope

- Audit each enemy family’s GLB (and player/Blobert variants where applicable): silhouette, clipping, obvious mesh defects, and animation export issues.
- Fix or regenerate materials so base colors, infection/mutation accents, and family identity are consistent — including procedural/color-generation paths in Blender/Python (`asset_generation`) where colors are wrong or washed out.
- Align with M13 (Blobert Visual Identity) for player-side readability; avoid one-off shaders unless shared.
- Document any families deferred to a follow-up ticket with a clear reason (blocked only when scoped).

## Dependencies

- M5 / M7 — models and clips in the pipeline
- M9 — confirms which enemies appear in procedural levels (scope priority)
- M21 (3D Model Quick Editor) — optional tooling for iteration; not a blocker for manual fixes

## Exit Criteria

Each active enemy family and the player model have been reviewed; material/color issues found in review are fixed or tracked with acceptance-owned follow-ups. Visual spot-check in Godot and in the asset editor (if used) passes agreed criteria.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
