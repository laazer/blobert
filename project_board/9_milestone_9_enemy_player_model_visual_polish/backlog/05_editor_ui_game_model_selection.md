# TICKET: 05_editor_ui_game_model_selection

Title: Editor UI — which models the game uses (player replacement + enemy version slots)

## Description

**Player:** UI to choose exactly **one active** player/Blobert visual (full **replacement** of current in-game mesh path). Changing selection updates registry and is picked up by game load (or documented restart requirement).

**Enemies:** UI to **add/remove version slots** per enemy **type/family** — each slot points at an in-use export; together they form the pool used for spawning (see `08_runtime_spawn_random_enemy_visual_variant`). Draft models cannot be slotted until promoted via `04_editor_ui_draft_status_for_exports`.

## Acceptance Criteria

- Player active model change reflects in-game per spec (immediate reload or restart — spec decides).
- Enemy version list edits persist; empty slot list behavior defined (fallback to default export or error — per spec).
- API + UI tests cover happy path and at least one validation error (e.g. draft not slotable).
- `timeout 300 ci/scripts/run_tests.sh` exits 0.

## Dependencies

- `01_spec_model_registry_draft_versions_and_editor_contract`
- `04_editor_ui_draft_status_for_exports` (soft — can mock registry state in tests)
- M21
