# TICKET: 02_physics_frame_order

**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Status:** Ready  
**Type:** Refactor (M1 code)

## Title

Document and validate physics frame execution order in PlayerController3D

## Description

Implicit frame order in `_physics_process` must be explicit and validated. Attacks need to know:
- When jump buffer/coyote time checks happen
- When collision masks update (one-way platforms)
- When renderer syncs (must be AFTER all game state updates)

Add explicit frame-order documentation and ensure execution follows:
1. State machine update (advance state_timer)
2. Timer updates (coyote, jump buffer, iframes)
3. State handler (input checks, physics apply)
4. Collision mask update (one-way platforms)
5. Renderer sync (read-only from controller)
6. move_and_slide()

Also implement and document:
- **Jump Buffer (0.1s):** Player can queue jump up to 0.1s before landing
- **Coyote Time (0.1s):** Player can jump up to 0.1s after walking off platform

## Acceptance Criteria

- [x] Frame-order execution documented (in-code comments + explicit sequence)
- [x] Jump buffer timer implemented and tested: jump queued before landing is executable
- [x] Coyote time timer implemented and tested: jump executable 0.1s after leaving ground
- [x] One-way platform collision mask updates correctly (up = exclude one-way, down = include)
- [x] Renderer sync happens after ALL game state updates (not mid-frame)
- [x] All M1 tests still pass
- [x] `run_tests.sh` exits 0

## Dependencies

- M11_prereq_1_player_state_machine (must add state timer first)

## Test Examples

```
Jump buffer: Player is on ground, hits jump button, lands before 0.1s expires → jump executes on landing
Coyote time: Player walks off platform, has 0.1s to press jump and still jump successfully
One-way platforms: From below, player passes through. From above, player lands on it.
```

## Notes

- Coyote time and jump buffer are optional polish, but recommended for responsive feel
- If M1 already has these, just document them; if not, add them
- Frame order changes must not break existing M1 behavior
