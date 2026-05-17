# TICKET: game_over_screen

**Milestone:** M15 Main Menu  
**Status:** Backlog  
**Type:** Implementation (UI Scene)

## Title

Game over / run summary screen with restart and main menu options

## Description

Create a game over screen that displays when player dies (HP reaches 0). Shows basic run statistics and provides two options: restart the run (fresh state) or return to main menu. Plugs into RunStateManager death state. Includes brief pause/animation before showing screen.

## Acceptance Criteria

- [x] Screen triggers on player death
  - Listens to PlayerController3D or RunStateManager death signal
  - Displays after 0.5s delay (allows death animation)
- [x] Run statistics display
  - Mutations absorbed count (display all 4 mutations if applicable)
  - Rooms cleared count
  - Optional: total damage dealt, enemies defeated, run duration
  - Clear formatting, readable at 1080p+
- [x] UI layout
  - Title: "GAME OVER" or "RUN ENDED" (large, prominent)
  - Statistics section (centered, easy to read)
  - Two buttons: "Restart" and "Main Menu"
  - Button size: 200x60px minimum
  - Font: 24pt+ for buttons, 16pt for stats
- [x] Restart functionality
  - "Restart" button resets all run state
  - Reset items: Player HP, mutations, room sequence, state variables
  - No carryover from previous run
  - Starts fresh roguelike run (same as "Start Run" from menu)
- [x] Main Menu functionality
  - "Main Menu" button returns to main_menu_scene
  - Clean transition (fade out, load menu)
  - Menu appears fresh (no state carryover)
- [x] State cleanup
  - No orphaned run state in memory
  - No mutation data leaks between runs
  - No cached enemies or rooms
  - Memory freed after run ends
- [x] Transition timing
  - Brief pause after death (0.5s) before screen appears
  - Optional: fade-in animation for screen
  - No instant pop-up (poor game feel)
  - Audio: optional death music or silence
- [x] Testing and validation
  - Manual test: Die in a room, game over screen appears
  - Manual test: Click "Restart", new run begins with 0 mutations
  - Manual test: Click "Main Menu", return to menu
  - Manual test: Stats match actual run (5 rooms cleared shows "5")
  - Manual test: No state bleed to new run
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M15 ticket 01: main_menu_scene (redirect target)
- M6 (Roguelike Run Structure) — RunStateManager and death signal

## Scene Structure

```
game_over_screen (CanvasLayer)
├── Panel (dark background, semi-transparent)
├── VBoxContainer (centered)
│   ├── Title (Label) "GAME OVER"
│   ├── StatsPanel (VBox)
│   │   ├── RoomsCleared (Label) "Rooms: 5"
│   │   ├── MutationsAbsorbed (Label) "Mutations: 2"
│   │   └── [Optional] OtherStats
│   ├── Spacer (Control)
│   ├── RestartButton (Button) "Restart"
│   ├── Spacer (Control)
│   └── MainMenuButton (Button) "Main Menu"
└── [Optional] DeathMusic (AudioStreamPlayer)
```

## Implementation Notes

- Connect to `RunStateManager.player_death()` signal
- Use `yield(get_tree(), "process_frame")` or Timer for 0.5s delay
- State reset: call RunStateManager.reset_run() or equivalent
- Fade transition: use Tween for opacity change

## Example Script

```gdscript
extends CanvasLayer

@onready var rooms_label = $Panel/VBox/RoomsCleared
@onready var mutations_label = $Panel/VBox/MutationsAbsorbed
@onready var restart_button = $Panel/VBox/RestartButton
@onready var menu_button = $Panel/VBox/MainMenuButton

func _ready():
    # Connect to death signal (deferred display)
    var player = get_tree().get_first_child_in_group("player")
    if player:
        player.died.connect(_on_player_died)
    
    restart_button.pressed.connect(_on_restart)
    menu_button.pressed.connect(_on_main_menu)
    hide()

func _on_player_died(run_data):
    await get_tree().create_timer(0.5).timeout
    show()
    rooms_label.text = "Rooms: %d" % run_data.rooms_cleared
    mutations_label.text = "Mutations: %d" % run_data.mutations_count

func _on_restart():
    RunStateManager.reset_run()
    get_tree().reload_current_scene()

func _on_main_menu():
    RunStateManager.reset_run()
    get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
```

## Notes

- Keep screen simple: stats + two buttons (no complexity)
- Consider visual theme: dark overlay, readable text
- Optional: confetti animation, death jingle, slow-mo replay
