# Epic: Milestone 9 – Enemy & Player Model Review / Materials

**Goal:** Every shipped enemy and the player model are reviewed for mesh quality, proportions, and material/color generation so they read clearly in-game and match the asset pipeline’s intended palette.

## Scope

- Audit each enemy family’s GLB (and player/Blobert variants where applicable): silhouette, clipping, obvious mesh defects, and animation export issues.
- Fix or regenerate materials so base colors, infection/mutation accents, and family identity are consistent — including procedural/color-generation paths in Blender/Python (`asset_generation`) where colors are wrong or washed out.
- Align with M13 (Blobert Visual Identity) for player-side readability; avoid one-off shaders unless shared.
- Document any families deferred to a follow-up ticket with a clear reason (blocked only when scoped).
- **Versions / draft / editor / spawn:** decomposed into ordered backlog tickets `01`–`09` below. **Umbrella blocked ticket** (cross-cutting acceptance + old “single card” text): `blocked/enemy_model_versions_draft_editor_and_spawn.md`.
- **Draft vs live on disk:** shipped GLBs stay under `animated_exports/`, `player_exports/`, `level_exports/` at the root; draft iterations use the `draft/` subfolder under each (see `project_board/specs/registry_draft_live_directory_layout_spec.md`). Optional: `.gitignore` `**/draft/**` under those roots if you do not want draft GLBs in commits.

## Backlog tickets (execution order)

1. `backlog/01_spec_model_registry_draft_versions_and_editor_contract.md` — spec: registry, draft, player active path, enemy version slots, allowlist roots, deletion rules.
2. `backlog/02_mesh_and_material_audit_enemy_families_and_player.md` — per-family + player mesh/material audit table.
3. `backlog/03_procedural_material_and_color_pipeline_fixes.md` — fix `asset_generation` materials/colors from audit.
4. `backlog/04_editor_ui_draft_status_for_exports.md` — UI: mark exports **draft** / promote to in-use.
5. `backlog/05_editor_ui_game_model_selection.md` — UI: **player** active model (replacement) + **enemy** version slots for the game pool.
6. `backlog/06_editor_load_existing_models_allowlist.md` — editor: load only **draft + in-use** from **canonical** asset roots (no misc GLBs).
7. `backlog/07_editor_delete_draft_and_in_use_models.md` — delete draft + delete in-use with safety rules.
8. `backlog/08_runtime_spawn_random_enemy_visual_variant.md` — random visual variant among in-use versions at spawn (coordinate M10).
9. `backlog/09_automated_tests_registry_allowlist_delete.md` — cross-cutting tests for registry, allowlist, delete invariants.
10. `done/10_body_part_color_picker_limb_joint_hierarchy.md` — fix editor color picker; **limb** + **joint** category colors + per-limb/joint overrides (`animated_build_options`, `material_system`, React preview).
11. `backlog/11_enemy_body_part_extras_spec_and_pipeline.md` — **Extras** feature: spec, per-part exclusive extra type (shell / spikes / horns / bulbs), spike shape + counts, materials; Python + Blender pipeline + tests.
12. `backlog/12_enemy_body_part_extras_editor_ui.md` — **Extras** tab in asset editor (`ThreePanelLayout`), per-part extra + material/color UI; depends on **11**.
13. `done/13_registry_paths_align_with_draft_vs_in_use_directories.md` — on-disk dirs match **draft** vs **live** / pool lifecycle; export + promote move files and registry paths; git-friendly commits for in-use assets only.
14. `done/14_hideable_animation_chooser_and_log_terminal.md` — collapsible **AnimationControls** + **Terminal** in `ThreePanelLayout`; optional persisted visibility.
15. `done/15_eye_and_extras_placement_clustering_controls.md` — **Clustering** slider/step controls (Build-style) for multi-eye and multi-extra placement; uniform **shape** presets coordinated with **16**.
16. `done/16_random_vs_uniform_distribution_eyes_and_extras.md` — **Random vs uniform** distribution (**radio** / segmented, not checkbox); seed for reproducible random; coordinated with **15**.
17. `backlog/17_zone_extras_offset_xyz_controls.md` — per-zone **offset X/Y/Z** for all geometry extras (Build-style floats in `animated_build_options` + apply in `zone_geometry_extras_attach`).
18. `backlog/18_registry_subtabs_by_pipeline_cmd.md` — Registry pane **sub-tabs** per pipeline **`RunCmd`** (animated vs player vs level vs …) so each cmd has its own registry / slots / draft view for readability.
19. `backlog/19_model_viewer_fullscreen_button.md` — **Fullscreen** control for the **3D model viewer** (`GlbViewer` / Fullscreen API; resize-safe canvas, a11y, frontend test).

## Dependencies

- M5 / M7 — models and clips in the pipeline
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
