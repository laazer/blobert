# TICKET: 02_cooldown_timer_ui

**Milestone:** M37 Active Ability UI System  
**Status:** Backlog  
**Type:** Implementation

## Title

Cooldown Timer UI — circular or linear countdown display

## Description

Show cooldown timer for active mutation. Render as circular radial progress (fills from 0° to 360° as cooldown expires) or linear bar. Update smoothly each frame based on remaining cooldown.

## Acceptance Criteria

- [x] Cooldown timer renders as circular radial or linear progress
- [x] Timer fills from empty (on cooldown start) to full (on availability)
- [x] Updates smooth every frame (no stutter or step)
- [x] Color changes when attack ready (green) vs cooling (gray/red)
- [x] Shows numeric countdown (seconds remaining, 1 decimal place)
- [x] Hides when cooldown is 0
- [x] M36 integration: cooldown reflects current level scaling
- [x] `run_tests.sh` exits 0

## Dependencies

- M37:01 (mutation status panel)
- M30 (frame timing — cooldown duration)
- M36:02 (level scaling applies to cooldown)

## Implementation Notes

**Circular progress shader or material:**
```gdscript
# Radial progress (0.0 = empty, 1.0 = full)
func update_cooldown_display(remaining: float, total: float):
    var progress = 1.0 - (remaining / total)  # 0 on cooldown start, 1 when ready
    cooldown_timer_material.set_shader_parameter("progress", progress)
    time_label.text = "%.1f" % remaining
```

## Scope Notes

- Choose one style (radial or linear) — both acceptable
- No animation easing (linear fill acceptable)

