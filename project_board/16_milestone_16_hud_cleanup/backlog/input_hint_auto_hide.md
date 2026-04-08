# TICKET: input_hint_auto_hide

Title: Input hints auto-hide after the player performs the relevant action

## Description

Currently input hints (`MoveHint`, `JumpHint`, `DetachHint`, `DetachRecallHint`, `AbsorbHint`) are visible by default and toggled only by `InputHintsConfig`. Update the system so each hint disappears permanently after the player first performs the relevant action during a run. Hints reset on run restart.

## Acceptance Criteria

- Each input hint tracks whether the player has performed its action this run
- Once performed, the hint hides and does not reappear for the rest of the run
- On run restart (new run from game over screen), all hints reset and display again
- `InputHintsConfig.input_hints_enabled = false` still overrides all hints (existing behavior preserved)
- Hints do not hide simultaneously — each hides independently
- `run_tests.sh` exits 0

## Dependencies

- `hud_audit_and_remove_debug_labels`
- M15 (Main Menu / run restart) — hints must reset on restart
