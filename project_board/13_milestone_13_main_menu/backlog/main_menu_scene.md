# TICKET: main_menu_scene

Title: Main menu scene — Start Run and Quit

## Description

Create a main menu scene that serves as the game's entry point. Set it as the Godot project's `run/main_scene` (currently `test_movement_3d.tscn`). The menu must transition cleanly into the roguelike run via `RunStateManager` / `RunSceneAssembler`.

## Acceptance Criteria

- `scenes/ui/main_menu.tscn` exists
- Scene is set as `run/main_scene` in `project.godot`
- "Start Run" button transitions to the roguelike run (RunSceneAssembler begins room sequence)
- "Quit" button exits the game cleanly (`get_tree().quit()`)
- Menu is readable with a legible font and layout at 1080p
- No orphaned state from a previous run bleeds into a new run started from the menu
- `run_tests.sh` exits 0

## Dependencies

- M6 (Roguelike Run Structure) — RunStateManager and RunSceneAssembler must be in place
