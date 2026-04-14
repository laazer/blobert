# Epic: Milestone 25 – Enemy Editor Visual Expression

**Goal:** Give users meaningful control over how enemies look — eye styles, surface textures, body orientation, and silhouette variation — so that every generated enemy feels visually distinct without touching animation.

## Scope

- **Eye system**: configurable eye shapes and optional pupil shape variations
- **Procedural textures**: gradient, spots, and stripes generated at the shader/material level
- **Texture upload**: PNG/JPG image applied as a custom surface texture (client-side only)
- **Part rotation**: per-part X/Y/Z rotation via numeric inputs in the properties panel
- **Bipedal presets**: standard biped and no-leg biped (penguin/toad-style) body archetypes

## Out of Scope

- Eye animation (blinking, tracking) — deferred to M26
- Per-part texture assignment — uniform body application only
- Server-side texture storage
- 3D viewport gizmos for rotation
- Custom mesh import

## Dependencies

- M21 (3D Model Quick Editor) — editor shell, 3D preview canvas, and config serialization must be functional

## Exit Criteria

- A user can open the editor, select a body preset, configure eyes with a custom pupil, apply a procedural texture, rotate the head, and see all changes reflected live in the 3D preview
- All settings round-trip through the enemy config JSON

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Verified, merged
