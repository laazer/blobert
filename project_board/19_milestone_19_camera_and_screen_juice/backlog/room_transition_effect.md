# TICKET: room_transition_effect

**Milestone:** M19 Camera and Screen Juice  
**Status:** Backlog  
**Type:** Implementation (Presentation)

## Title

Room transition effect — fade-to-black between room scenes

## Description

Add smooth fade-to-black transition (0.2s fade out, scene swap, 0.2s fade in) around RunSceneAssembler room changes. Input blocked during fade. Game state (mutations, HP) preserved.

## Acceptance Criteria

- [x] Fade effect: 0.2s out → scene swap → 0.2s in
- [x] Input blocked during fade (no movement/attack)
- [x] Game state preserved (mutations, HP, position)
- [x] CanvasLayer + ColorRect + Tween (no shader)
- [x] RunSceneAssembler calls `transition_to_room()` method
- [x] All M6 tests pass, `run_tests.sh` exits 0

## Implementation

```gdscript
func transition_to_room(new_room_scene):
    input_blocked = true
    # Fade out (0.2s)
    await fade_to_black(0.2)
    # Swap room
    current_room = new_room_scene
    # Fade in (0.2s)
    await fade_from_black(0.2)
    input_blocked = false

func fade_to_black(duration: float):
    var tween = create_tween()
    tween.tween_property(fade_rect, "color:a", 1.0, duration)
    await tween.finished

func fade_from_black(duration: float):
    var tween = create_tween()
    tween.tween_property(fade_rect, "color:a", 0.0, duration)
    await tween.finished
```

## Dependencies

- M6 (Roguelike Run Structure)

## Notes

- Smooth transitions improve perceived polish
- Input block prevents jank during scene swap
- State preservation automatic (just don't reset)
