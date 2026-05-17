# TICKET: 01_frame_timeline_overlay

**Milestone:** M34 Hitbox & Frame Visualization  
**Status:** Backlog  
**Type:** Implementation

## Title

Frame Timeline Overlay — attack duration and frame counter visualization

## Description

Add debug overlay showing current frame count and frame ranges (startup/active/endlag) as attack executes. Visual timeline helps developers match animations to frame data. Overlay toggleable via debug flag.

## Acceptance Criteria

- [x] Debug overlay renders frame counter (current frame / total frames)
- [x] Startup, active, endlag windows color-coded on timeline
- [x] Overlay updates per-frame during attack execution
- [x] Overlay hides when attack completes
- [x] Toggle via exported `debug_frame_overlay` bool or InputMap action
- [x] On-screen text is legible (contrast, font size)
- [x] No performance regression when overlay off
- [x] `run_tests.sh` exits 0

## Dependencies

- M30:01 (frame data)
- M30:02 (frame event emission)

## Implementation Notes

**Overlay rendering (2D CanvasLayer):**
```gdscript
if debug_frame_overlay and active_attack:
    var elapsed = frame_counter
    var total = (active_attack.startup_frames + active_attack.active_frames + 
                 active_attack.endlag_frames)
    draw_string(font, pos, "Frame: %d/%d" % [elapsed, total])
    # Draw color bar: startup (green), active (red), endlag (blue)
    draw_rect(Rect2(0, y, elapsed * bar_width, 10), 
              get_window_color(frame_counter, active_attack))
```

## Scope Notes

- Debug feature only (not shipped in release)
- No animation preview in this ticket (visual feedback only)

