# TICKET: progressive_hint_system

Title: Progressive hint system — show each control prompt at the moment it's needed

## Description

Extend `InputHintsConfig` and `InfectionUI` so that individual hints fire contextually rather than all-at-once on scene load. Each hint has a trigger condition; once the player performs the action, the hint dismisses and does not return for the rest of the run. Hints reset on run restart.

## Acceptance Criteria

- `scripts/ui/progressive_hint_manager.gd` exists and tracks per-hint state (shown, dismissed)
- Each hint has a trigger condition (e.g. MoveHint shows on first frame player can move, JumpHint shows after player first moves)
- Once the player performs the hinted action, the hint hides within 0.5s
- Dismissed hints do not reappear during the same run
- All hint states reset when a new run begins
- `InputHintsConfig.input_hints_enabled = false` still suppresses all hints (existing override preserved)
- `run_tests.sh` exits 0

## Dependencies

- M2 (Infection Loop) — absorb/infect hints need infection system to be stable
- M13 (Main Menu) — run restart must trigger hint reset
