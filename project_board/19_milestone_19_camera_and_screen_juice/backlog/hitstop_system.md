# TICKET: hitstop_system

**Milestone:** M19 Camera and Screen Juice  
**Status:** Backlog  
**Type:** Implementation (Game Feel)

## Title

Hitstop system — brief time freeze on heavy hit for impact feedback

## Description

Implement hitstop (time freeze) on heavy impacts. Game pauses for 2 frames (Engine.time_scale = 0.05) to sell hit weight. Triggered by carapace attacks, fusion attacks, enemy deaths. Audio unaffected by timescale.

## Acceptance Criteria

- [x] Hitstop singleton: `scripts/system/hitstop.gd`
- [x] `trigger_hitstop(duration_frames: int)` method
  - Sets Engine.time_scale = 0.05
  - Restores after duration
  - Default heavy hit: 2 frames
- [x] Heavy hit only (carapace, fusion, deaths)
- [x] Audio unaffected (separate audio streams)
- [x] Stacking: extend existing hitstop, don't reset
- [x] All M11 tests pass, `run_tests.sh` exits 0

## Implementation

```gdscript
extends Node
class_name Hitstop

var hitstop_remaining: float = 0.0
var hitstop_target: float = 0.0

func trigger_hitstop(duration_frames: int):
    hitstop_remaining = duration_frames * (1.0 / 60.0)
    hitstop_target = 0.05
    Engine.time_scale = hitstop_target

func _process(delta):
    if hitstop_remaining > 0:
        hitstop_remaining -= delta
    else:
        Engine.time_scale = 1.0
```

## Dependencies

- M11 (Base Mutation Attacks) — hit events

## Notes

- Heavy hits feel weightier with hitstop
- 2-frame freeze is good balance (not too long)
- Audio separation prevents distortion
