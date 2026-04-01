# TICKET: blender_animation_export

Title: Update Blender pipeline to export named animation clips per family

## Description

The existing Blender Python pipeline (`asset_generation/python/`) exports static GLBs. Update it to bake and export named NLA animation clips — Idle, Walk, Hit, Death — for each enemy family. Each clip must be named consistently so Godot's AnimationPlayer can reference them by name without per-file configuration.

## Acceptance Criteria

- Blender script exports at minimum 4 named clips per GLB: `Idle`, `Walk`, `Hit`, `Death`
- Clip names are consistent across all 4 families (same string names)
- GLBs load in Godot without import errors
- AnimationPlayer node is present on the imported scene root and contains all 4 clips
- Existing GLBs in `assets/enemies/generated_glb/` are regenerated with animation data
- `run_tests.sh` exits 0 (no regressions from reimport)

## Dependencies

- M5 (Blender pipeline and parts library) must be complete — it is
