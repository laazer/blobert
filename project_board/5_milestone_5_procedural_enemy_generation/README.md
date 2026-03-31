# Epic: Milestone 5 – Procedural Enemy Generation

**Goal:** Blender → Godot enemy pipeline fully operational for first 4 families.
Status: Done

## Scope

- Blender Python script for kitbash enemy assembly
- Parts library (blob, sphere, capsule, spike, claw, eye, shell)
- GLB export pipeline and naming convention
- Godot scene auto-generator producing game-ready .tscn files
- Enemy base script with family, mutation drop, and state hooks
- First 4 families playable: adhesion, acid, claw, carapace (3 variants each = 12 enemies)

## Exit criteria

All 4 first-pass families can be generated in Blender, exported, auto-wrapped in Godot,
and placed in a level with correct mutation drops and functional collision.

## References

- `docs/generative_worflow_v1.md` — Blender kitbash workflow
- `docs/enemy_asset_pipeline_diagram.md` — full pipeline diagram
- `docs/godot_enemy_scene_generator_instructions.md` — Godot tool usage
- `scripts/asset_generation/load_assets.gd` — existing scene generator (in progress)

## Status folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
