# TICKET: main_menu_scene

**Milestone:** M15 Main Menu  
**Status:** Backlog  
**Type:** Implementation (UI Scene)

## Title

Main menu scene — Start Run and Quit (game entry point)

## Description

Create the game's main menu scene as the official entry point (`run/main_scene`). The menu provides two options: start a new roguelike run or quit. Clean transition to RunSceneAssembler without orphaned state. Update `project.godot` to use main_menu.tscn as the startup scene.

## Acceptance Criteria

- [x] Scene created: `scenes/ui/main_menu.tscn`
  - Loads as first scene when game starts
  - CanvasLayer for UI rendering (above game world)
  - Uses Godot's standard UI nodes (Panel, Button, Label)
- [x] Project configuration
  - Update `run/main_scene` in `project.godot` to point to main_menu.tscn
  - Transition from previous default (test_movement_3d.tscn)
  - Scene loads correctly at startup
- [x] UI layout and readability
  - Menu title/heading: "BLOBERT" or game name (large, readable)
  - Two buttons: "Start Run" and "Quit" (clear labels, appropriate size)
  - Button size: ~200x60px minimum (easy to click)
  - Layout: centered on screen (works at 1080p and higher)
  - Font: sans-serif, 24pt+ for buttons, 48pt+ for title
  - Contrast: readable on solid background
- [x] Start Run functionality
  - "Start Run" button triggers RunSceneAssembler or equivalent
  - Transition: fade out menu, fade in first room
  - No data corruption or state leakage
  - Run begins fresh (no carryover from previous run)
- [x] Quit functionality
  - "Quit" button calls `get_tree().quit()`
  - Exit is clean and immediate
  - No unsaved state loss (no save system yet)
- [x] State cleanup
  - No orphaned nodes in scene tree from previous runs
  - No cached music/audio from previous playthrough
  - Fresh runtime state on each new run
  - Memory cleanup on exit
- [x] Scene transition
  - Smooth fade or transition effect (optional polish)
  - No frame drops or stutter during transition
  - Audio transitions cleanly (fade out menu music if present)
- [x] Testing and validation
  - Manual test: Start game, see menu
  - Manual test: Click "Start Run", run begins
  - Manual test: Exit run, return to menu (if pause system in place)
  - Manual test: Click "Quit", game closes
  - Manual test: No visible errors in output
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M6 (Roguelike Run Structure) — RunStateManager and RunSceneAssembler

## Scene Structure

```
main_menu (CanvasLayer)
├── Panel (background, optional)
├── VBoxContainer (vertical layout)
│   ├── Title (Label) "BLOBERT"
│   ├── Spacer (Control)
│   ├── StartButton (Button) "Start Run"
│   ├── Spacer (Control)
│   └── QuitButton (Button) "Quit"
└── [Optional] Music (AudioStreamPlayer)
```

## Implementation Notes

- Use Control nodes for layout (VBoxContainer for vertical alignment)
- Button signals: `pressed()` to trigger actions
- Transition: Use `get_tree().change_scene_to_file()` or `get_tree().root.add_child(run_scene)`
- Audio: Optional background music (nice-to-have, not required)
- Save menu position/theme in memory (no persistence yet)

## Example Scene Script

```gdscript
extends CanvasLayer

@onready var start_button = $VBoxContainer/StartButton
@onready var quit_button = $VBoxContainer/QuitButton

func _ready():
    start_button.pressed.connect(_on_start_run)
    quit_button.pressed.connect(_on_quit)

func _on_start_run():
    # Call RunSceneAssembler or RunStateManager
    # Transition to roguelike run
    var run_scene = RunSceneAssembler.assemble_run()
    get_tree().root.add_child(run_scene)
    queue_free()

func _on_quit():
    get_tree().quit()
```

## Notes

- Keep menu simple: two buttons, no complexity (expansion: settings, difficulty, etc.)
- Background can be static image or simple animation (nice-to-have)
- Consider theme/branding for main menu (colors, font, visuals)
