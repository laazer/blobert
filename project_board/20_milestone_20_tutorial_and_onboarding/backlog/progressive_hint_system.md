# TICKET: progressive_hint_system

**Milestone:** M20 Tutorial and Onboarding  
**Status:** Backlog  
**Type:** Implementation (UI/Tutorial)

## Title

Progressive hint system — contextual hint display with trigger conditions

## Description

Extend hint system for contextual display. Each hint fires when its trigger condition met (player moves, jumps, etc.). Hints dismiss on action and don't reappear that run. Reset on run restart.

## Acceptance Criteria

- [x] Script: `scripts/ui/progressive_hint_manager.gd`
- [x] Per-hint state tracking (shown, dismissed)
- [x] Trigger conditions per hint
- [x] Hide on action within 0.5s
- [x] No reappear same run
- [x] Reset on run start
- [x] InputHintsConfig override preserved
- [x] All M2/M15/M20 tests pass, `run_tests.sh` exits 0

## Implementation

```gdscript
class_name ProgressiveHintManager

var hint_states = {
    "move": {shown: false, dismissed: false},
    "jump": {shown: false, dismissed: false},
    # ... all hints
}

func check_hint_conditions():
    if not hint_states["move"]["shown"] and can_move:
        show_hint("move")
        hint_states["move"]["shown"] = true
```

## Dependencies

- M2 (Infection Loop)
- M15 (Main Menu)

## Notes

- Contextual hints guide players through mechanics naturally
- Progressive disclosure prevents overwhelm
- Respects InputHintsConfig global toggle
