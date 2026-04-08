# TICKET: hitstop_system

Title: Hitstop system — brief freeze on heavy hit confirmation

## Description

Implement hitstop: when a heavy hit connects, the game pauses for 1–3 frames to sell impact. This is distinct from screen shake — it's a time freeze, not a camera effect. Triggered on heavy hits (carapace attacks, fusion attacks, enemy deaths).

## Acceptance Criteria

- `scripts/system/hitstop.gd` exists as an autoload or singleton
- `trigger_hitstop(duration_frames: int)` freezes `Engine.time_scale` to 0.05 for the specified frames then restores it
- Default heavy hit duration: 2 frames
- Hitstop does not affect audio pitch (time scale change should not distort SFX)
- Hitstop is not triggered on light hits (claw swipe, acid spit) — only heavy impacts
- Multiple hitstop calls during an active hitstop extend rather than reset the duration
- `run_tests.sh` exits 0

## Dependencies

- M8 (Enemy Attacks) or M11 (Base Mutation Attacks) — hit events must exist to trigger hitstop
