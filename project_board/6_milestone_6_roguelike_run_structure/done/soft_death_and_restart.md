# TICKET: soft_death_and_restart
Title: Implement soft death state and run restart
Project: blobert
Created By: Human
Created On: 2026-03-21

---

## Description

When the player reaches 0 HP, trigger a soft death: brief pause, slime dissolves animation,
then seamless reset back to the entry room with a fresh run layout. No harsh game over screen.
Tone should feel like "the lab resets the experiment."

---

## Acceptance Criteria

- Death does not hard-crash or hang
- Brief visual feedback on death (dissolve or fade) — requires human visual verification
- Run resets within 2 seconds of death trigger — testable via timer assertion
- Mutation slots are empty on restart — testable headlessly
- Player position and HP are fully reset — testable headlessly (position, HP value)
- New room layout is generated on each restart — deferred to procedural_room_chaining ticket; for now containment_hall_01 is the fixed entry room

---

## Dependencies

- `project_board/6_milestone_6_roguelike_run_structure/done/run_state_manager.md` — COMPLETE; RunStateManager owns DEAD state, player_died signal, and mutation slot clear
- `scripts/system/run_state_manager.gd` — pure logic, already implemented
- `scripts/player/player_controller_3d.gd` — HP tracked in `_current_state.current_hp`; public read via `get_current_hp()`; `min_hp = 0.0` is the HP floor in MovementSimulation
- `scripts/mutation/mutation_slot_manager.gd` — `clear_all()` already called by RunStateManager on DEAD transition
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` — the entry room; SpawnPosition is at (-25, 1, 0)

---

## Architecture Decisions (Planner)

### Part 1 — Core Logic (Gameplay Systems Agent)

A new coordinator node script `scripts/system/death_restart_coordinator.gd` (extends Node) is added to the containment_hall_01 scene (or its scene root). This node:

1. Holds a `RunStateManager` instance.
2. Calls `run_state_manager.apply_event("start_run")` on `_ready()` to move to ACTIVE.
3. Polls `player.get_current_hp() <= 0.0` each `_process` frame. When true, and RSM is in ACTIVE state, calls `run_state_manager.apply_event("player_died")`.
4. Connects to `run_state_manager.player_died` signal. On signal receipt:
   a. Disables player input (freeze player velocity, set a `_dead` flag checked in `_process`).
   b. Starts a `SceneTreeTimer` of ≤ 1.5 seconds (leaving headroom for the 2-second AC).
   c. On timer timeout: calls `run_state_manager.apply_event("restart")`, then calls `_reset_run()`.
5. `_reset_run()`:
   a. Resets player position to SpawnPosition (already at -25, 1, 0 in scene).
   b. Resets player HP: sets `_current_state.current_hp` back to `_simulation.max_hp` (100.0). This requires a new public method `reset_hp()` on `PlayerController3D`.
   c. Restores both chunk slots to filled: sets `_current_state.has_chunks[0] = true` and `_current_state.has_chunks[1] = true`. Requires a new public method `reset_chunks()` on `PlayerController3D`.
   d. Clears any live detached chunks in the scene (queue_free any _chunks[i] references). Covered by `reset_chunks()`.
   e. Re-enables player input (clears `_dead` flag).
   f. Calls `run_state_manager.apply_event("start_run")` to return RSM to ACTIVE.
6. Mutation slot clearing is already handled by RSM's `apply_event("player_died")` via `_slot_manager.clear_all()`. However, the scene's `InfectionInteractionHandler` and `PlayerController3D._mutation_slot` reference the same slot manager; the coordinator must notify the UI/handler to refresh after reset. This is done by emitting a signal or calling a refresh method on the infection handler — TBD by Spec Agent.

**Key constraint:** `DeathRestartCoordinator` must not call `get_tree().reload_current_scene()`. Reset is in-place.

**Key constraint:** Death detection polling must be guarded by `_dead` flag to prevent double-firing.

**Key constraint:** The "within 2 seconds" window is the total time from `get_current_hp() <= 0` detection to run being in ACTIVE state again. Timer budget: ≤ 1.5 seconds (leaves 0.5 s margin for frame latency).

### Part 2 — Presentation (INTEGRATION — human visual check required)

A tween-based dissolve/fade on the player's `SlimeVisual` node, driven by the `player_died` signal. This is added in a separate step after core logic is verified headlessly. The visual node is at `PlayerController3D/SlimeVisual`. The fade must complete before the reset fires (within the 1.5 s timer window).

---

## New Files

| File | Type | Purpose |
|------|------|---------|
| `scripts/system/death_restart_coordinator.gd` | Node script | Core death→restart wiring; Part 1 |
| `tests/system/test_death_restart_coordinator.gd` | GDScript test | Headless tests for core logic |

## Modified Files

| File | Change |
|------|--------|
| `scripts/player/player_controller_3d.gd` | Add `reset_hp()` and `reset_chunks()` public methods |
| `scenes/levels/containment_hall_01/containment_hall_01.tscn` | Add DeathRestartCoordinator node (Part 1); add fade tween node (Part 2, INTEGRATION) |

---

## Test Plan

### Primary Suite — Core Logic (headless)

| ID | Description | Testable? |
|----|-------------|-----------|
| SDR-STRUCT-1 | Script loads headlessly | Yes |
| SDR-STRUCT-2 | DeathRestartCoordinator is not a RefCounted (extends Node) | Yes |
| SDR-CORE-1 | Calling `_on_player_died()` directly transitions RSM to DEAD | Yes |
| SDR-CORE-2 | After restart timer fires, RSM returns to ACTIVE | Yes |
| SDR-CORE-3 | After restart, player HP equals max_hp (100.0) | Yes |
| SDR-CORE-4 | After restart, mutation slots are both empty | Yes |
| SDR-CORE-5 | After restart, both chunk slots report has_chunk = true | Yes |
| SDR-CORE-6 | After restart, player position matches spawn position | Yes |
| SDR-CORE-7 | Total elapsed time from death signal to ACTIVE state is ≤ 2.0 seconds | Yes (await timer) |
| SDR-CORE-8 | Double-fire guard: calling `_on_player_died()` twice does not double-restart | Yes |
| SDR-NOOP-1 | HP at 0.0 but RSM not in ACTIVE state: no death triggered | Yes |
| SDR-NOOP-2 | HP above 0.0 in ACTIVE state: no death triggered | Yes |

### Presentation (Integration — human visual check)

| ID | Description | Testable? |
|----|-------------|-----------|
| SDR-VIS-1 | SlimeVisual fades out on death (dissolve/scale-to-zero tween) | Human only |
| SDR-VIS-2 | SlimeVisual restores to full scale/alpha after reset | Human only |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
9

## Last Updated By
Human

## Validation Status
- Tests: 21 SDR-* tests ALL PASS (15 primary + 6 adversarial).
- SDR-VIS-1 PASS: SlimeVisual fades/dissolves on death — confirmed by human playtest 2026-03-27 using procedural_run.tscn with debug_kill (K key).
- SDR-VIS-2 PASS: SlimeVisual restores to full scale after reset — confirmed same session.
- All other ACs evidenced headlessly (no crash, resets within 2s, mutation slots cleared, HP/position reset).
- Deferred AC: "New room layout on each restart" — explicitly deferred to procedural_room_chaining ticket; accepted by Spec Agent.

## Blocking Issues
None

## Escalation Notes
- AC "New room layout is generated on each restart" is deferred — confirmed acceptable by Spec Agent.
- InfectionInteractionHandler slot manager reference — RESOLVED.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Status
Proceed

## Reason
All acceptance criteria are met. Human playtest 2026-03-27 confirmed SDR-VIS-1 and SDR-VIS-2. Ticket is COMPLETE.
