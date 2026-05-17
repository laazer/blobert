# TICKET: input_hint_auto_hide

**Milestone:** M16 HUD Cleanup  
**Status:** Backlog  
**Type:** Implementation (HUD Feature)

## Title

Input hints auto-hide after first action performance (per-action hint dismissal)

## Description

Update input hints system to auto-hide hints after player first performs the corresponding action. Each hint (Move, Jump, Detach, Absorb, Fuse) tracks whether its action has been performed this run and hides independently. Hints reset on run restart. Existing `InputHintsConfig` override still works.

## Acceptance Criteria

- [x] Input hint state tracking
  - Each hint has internal flag: `_action_performed_this_run`
  - Flag persists for run duration (survives rooms)
  - Flag resets on new run start
- [x] Auto-hide on action performance
  - Move hint hides when player first moves (detects velocity change)
  - Jump hint hides when player first jumps (detects jump input)
  - Detach hint hides when player first detaches from wall
  - Absorb hint hides when player first absorbs mutation
  - Fuse hint hides when player first activates fusion
  - Each hint independent (Move can be hidden while Jump visible)
- [x] Hint behavior logic
  - Hint visible at run start (default)
  - On action detect: set `_action_performed_this_run = true`
  - On next frame: hide hint (Tween fade-out optional)
  - Once hidden, remains hidden until run restart
- [x] Config compatibility
  - `InputHintsConfig.input_hints_enabled = false` still hides ALL hints
  - Setting preserved (overrides auto-hide behavior)
  - Toggle works correctly during run
- [x] Run restart behavior
  - On run restart (game over → restart), all hints reset to visible
  - All `_action_performed` flags reset to false
  - First performance of each action triggers hide again
- [x] Visual feedback
  - Hint hide: optional fade-out (0.3s Tween for polish)
  - No jarring pops (smooth disappearance)
  - Hint reappears smoothly on new run
- [x] Testing and validation
  - Manual test: Perform move, move hint hides
  - Manual test: Perform jump, jump hint hides (while move hidden)
  - Manual test: Absorb mutation, absorb hint hides
  - Manual test: Restart run, all hints reappear
  - Manual test: Toggle InputHintsConfig, all hints disappear immediately
  - Manual test: Hints don't interfere with actual actions
- [x] All M2/M3 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M2/M3 (HUD System) — input hints already exist
- M15 (Main Menu) — run restart signal
- M16 ticket 01: hud_audit_and_remove_debug_labels

## Implementation Notes

- Use signals from PlayerController3D (jump, move, absorb, fuse) to detect actions
- Track hints in dictionary: `{ "move": performed, "jump": performed, ... }`
- Reset flags on RunStateManager.run_started signal
- Use Tween for fade-out (optional Polish enhancement)

## Example Implementation

```gdscript
# InputHintManager.gd (hypothetical)

class_name InputHintManager
extends CanvasLayer

var hints_performed = {
    "move": false,
    "jump": false,
    "detach": false,
    "absorb": false,
    "fuse": false
}

@onready var move_hint = $MoveHint
@onready var jump_hint = $JumpHint
@onready var absorb_hint = $AbsorbHint
# ... etc

func _ready():
    var player = get_tree().get_first_child_in_group("player")
    if player:
        player.moved.connect(_on_player_moved)
        player.jumped.connect(_on_player_jumped)
        player.absorbed.connect(_on_player_absorbed)
    
    RunStateManager.run_started.connect(reset_hints)

func _on_player_moved():
    if not hints_performed["move"]:
        hints_performed["move"] = true
        _hide_hint(move_hint)

func _on_player_jumped():
    if not hints_performed["jump"]:
        hints_performed["jump"] = true
        _hide_hint(jump_hint)

func _on_player_absorbed():
    if not hints_performed["absorb"]:
        hints_performed["absorb"] = true
        _hide_hint(absorb_hint)

func _hide_hint(hint: Control):
    var tween = create_tween()
    tween.tween_property(hint, "modulate:a", 0.0, 0.3)
    tween.tween_callback(hint.hide)

func reset_hints():
    hints_performed = {
        "move": false,
        "jump": false,
        "detach": false,
        "absorb": false,
        "fuse": false
    }
    move_hint.show()
    jump_hint.show()
    absorb_hint.show()
    # ... reset visibility for all hints
```

## Notes

- Signal detection reliable: watch for input processing, not frame-based polling
- Fade-out timing: 0.3s is reasonable (noticeable but not slow)
- Config toggle: should immediately hide all hints when disabled
