# M11-01 Static QA (GDScript)

**Ticket:** M11-01 Player State Machine  
**Reviewer:** gdscript-reviewer (static_qa)  
**Date:** 2026-05-23

## Scope

- `scripts/player/player_state_machine.gd`
- `scripts/player/player_state_derivation_context.gd`
- `scripts/player/player_controller_3d.gd` (FSM wiring: `_ready`, `_physics_process`, `_sync_player_state_machine`, damage/reset accessors)

## Tooling

- `task hooks:gd-review` on the three files → passed (trailing whitespace/EOF auto-fixed only)

## Organization

- **Layering:** RefCounted FSM + derivation snapshot DTO; no `Node`/`Input` in machine module. Clear separation from `MovementSimulation.MovementState` (documented in file headers and spec).
- **Controller wiring:** Single `update(delta)` per `_physics_process`; `sync_from_context` after `move_and_slide` and kinematic copy-back — matches PSM-10. Damage paths call `notify_damage_taken()` before end-of-frame sync.
- **Public API:** `get_player_state()`, `get_player_state_machine()`, `is_wall_clinging_state()` delegate to FSM as specified.

## Correctness (spec / edge cases)

| Area | Verdict |
|------|---------|
| PSM-2 ten-state enum + IDLE default | OK |
| PSM-3 timer (`update`, same-state no-op) | OK |
| PSM-4 guards (DEAD, HURT, FLOAT sources) | OK |
| PSM-5 `transition` + EC-2 `_hurt_reentry_blocked` | OK |
| PSM-6 `MIN_FLOAT_FROM_JUMP_SEC` gate; `MIN_HURT_SEC == 0` | OK (constant exposed; timer unused at 0.0 by design) |
| PSM-7 derivation priority + no FLOAT derive | OK |
| PSM-8 damage latch / sync consume | OK |
| PSM-9 `reset()` | OK |
| PSM-10 controller integration | OK |

## Findings

**Critical:** none.

**Warning:** none.

**Suggestion (non-blocking):**

1. `MIN_HURT_SEC` is not referenced in `transition`/`sync_from_context` yet — acceptable for M11-01 (`0.0`); reserve for when downstream raises duration.
2. Move-speed threshold duplicated (`_MOVE_SPEED_THRESHOLD` vs `PlayerStateDerivationContext.DEFAULT_MOVE_SPEED_THRESHOLD`) — both `0.12`; could share one constant later.
3. `can_transition_to` ends with redundant `return true` after same-state branch — cosmetic.

## Verdict

**PASS** — merge-ready for static_qa → learning. No required fixes.

## Test evidence

Regression attested in `project_board/checkpoints/M11-01/2026-05-23T-implementation-run.md` (primary + adversarial FSM suites; full suite). Static QA did not re-run full `run_tests.sh` in this pass.
