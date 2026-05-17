# TICKET: 03_charge_and_combo_feedback

**Milestone:** M37 Active Ability UI System  
**Status:** Backlog  
**Type:** Implementation

## Title

Charge & Combo Feedback — meter fill and hit counter display

## Description

When charging (M31), show charge meter filling. Show combo counter during consecutive hits (increments on hit, resets on miss/timeout). Visual feedback reinforces attack success.

## Acceptance Criteria

- [x] Charge meter appears when holding attack (M31 integration)
- [x] Meter fills 0→100% as charge accumulates
- [x] Combo counter visible during combo (increments per hit)
- [x] Combo counter resets after 2.0s inactivity
- [x] Visual feedback: number or icon badge with count
- [x] Color changes on milestone hits (3-hit, 5-hit, etc.)
- [x] Charge meter hides when attack released
- [x] Combo counter hides when reset
- [x] `run_tests.sh` exits 0

## Dependencies

- M31 (charge mechanics)
- M30 (frame timing — combo timeout)
- M37:01 (HUD panel)

## Implementation Notes

**Charge meter update:**
```gdscript
func _process(delta):
    if player.is_charging:
        charge_meter.value = player.charge_level * 100
    else:
        charge_meter.visible = false

func _on_hit():
    combo_count += 1
    combo_timer.start(2.0)  # reset after 2s inactivity

func _on_combo_timer_timeout():
    combo_count = 0
    combo_label.visible = false
```

## Scope Notes

- Combo damage multiplier not in this ticket (future balancing)
- Combo visual only (no game mechanic changes)

