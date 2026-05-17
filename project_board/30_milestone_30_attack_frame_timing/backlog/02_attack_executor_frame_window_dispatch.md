# TICKET: 02_attack_executor_frame_window_dispatch

**Milestone:** M30 Attack Frame Timing  
**Status:** Backlog  
**Type:** Implementation

## Title

Attack Executor Frame Window Dispatch — startup/active/endlag event emission

## Description

Extend the attack executor to emit timed events at frame boundaries (startup end, active start/end, endlag end) using the frame data added in ticket 01. These events are the hook for cancel windows (M30:03), visual effects (hitstop, screen shake), and audio (impact SFX). Executor must respect frame data declaratively without hardcoded delays.

## Acceptance Criteria

- [x] AttackExecutor reads startup/active/endlag from AttackResource
- [x] Events emitted at frame transitions: `on_startup_end()`, `on_active_start()`, `on_active_end()`, `on_endlag_end()`
- [x] Frame counting is deterministic (per-frame increment in `_process` or `_physics_process`, configurable)
- [x] Events fire in the correct frame and propagate to hitbox/visual systems
- [x] Attack duration matches frame data: `(startup + active + endlag) / 60 = duration_seconds`
- [x] Multiple attacks can execute in sequence without frame counter collision
- [x] Tests verify event order and timing (headless, no render)
- [x] `run_tests.sh` exits 0

## Dependencies

- M30:01 (AttackResource frame properties)
- M11 (AttackExecutor base)

## Implementation Notes

**GDScript example:**
```gdscript
var frame_counter: int = 0
var active_attack: AttackResource = null

func _process(delta):
    if active_attack:
        frame_counter += 1
        
        if frame_counter == active_attack.startup_frames:
            on_startup_end.emit()
        elif frame_counter == (active_attack.startup_frames + 1):
            on_active_start.emit()
        elif frame_counter == (active_attack.startup_frames + active_attack.active_frames):
            on_active_end.emit()
        elif frame_counter >= (active_attack.startup_frames + active_attack.active_frames + active_attack.endlag_frames):
            on_endlag_end.emit()
            frame_counter = 0
            active_attack = null
```

## Scope Notes

- Frame counter reset happens automatically after endlag
- No animation blending or frame-skipping in this ticket (deterministic frame count)
- Visual/audio hookups happen in other milestones

