# TICKET: run_state_manager
Title: Implement run state manager
Project: blobert
Created By: Human
Created On: 2026-03-21

---

## Description

GDScript autoload or scene-level manager that owns the lifecycle of a single run:
start, active, player_dead, run_won. Resets mutation state and level on death/win.
Drives the top-level game loop.

The manager is a pure-logic GDScript object (`extends RefCounted`) with no Node or scene tree
dependency in its base class. It emits signals for each state transition. Scene loading and
entity resets are side effects handled by the consumer (an autoload wrapper or scene-level
coordinator node that connects to the signals).

Entry room for v1: `containment_hall_01.tscn` (the current main scene).

---

## Acceptance Criteria

- States: START, ACTIVE, DEAD, WIN (enum; string accessor via `get_state_id() -> String`)
- Fresh instance starts in START state
- `apply_event("start_run")` transitions START → ACTIVE
- `apply_event("player_died")` transitions ACTIVE → DEAD
- `apply_event("run_won")` transitions ACTIVE → WIN
- `apply_event("restart")` transitions DEAD → START and WIN → START
- Each valid transition emits the corresponding signal before the state changes
- Invalid transitions (wrong event for current state) are strict no-ops (no state change, no signal)
- `MutationSlotManager.clear_all()` is called on the manager's internal slot manager on DEAD and WIN transitions
- The base class does not call `get_tree()`, `load()`, or any scene-loading API
- Headlessly testable: all state transitions and signal emissions verifiable via `load().new()` and manual signal connection

---

## Dependencies

- `scripts/mutation/mutation_slot_manager.gd` (MutationSlotManager — owns `clear_all()`)
- `scripts/infection/infection_interaction_handler.gd` (wires reset in the scene consumer; not a direct dep of the base class)

---

## What to Implement

### File 1: `scripts/system/run_state_manager.gd`
- `class_name RunStateManager extends RefCounted`
- Enum `State { START = 0, ACTIVE = 1, DEAD = 2, WIN = 3 }`
- Internal `_state: State` initialized to `State.START`
- Internal `_slot_manager: RefCounted` — a `MutationSlotManager` instance created in `_init()`
- Signals: `run_started`, `player_died`, `run_won`, `run_restarted` (all parameterless)
- Public API:
  - `get_state() -> State`
  - `get_state_id() -> String` — returns `"START"`, `"ACTIVE"`, `"DEAD"`, or `"WIN"`
  - `apply_event(event: String) -> void` — drives transitions per the table below
  - `get_slot_manager() -> RefCounted` — returns `_slot_manager` (for integration tests and consumers)

### Transition Table

| Current State | Event          | Next State | Signal Emitted  | Side Effect             |
|---------------|----------------|------------|-----------------|-------------------------|
| START         | `start_run`    | ACTIVE     | `run_started`   | none                    |
| ACTIVE        | `player_died`  | DEAD       | `player_died`   | `_slot_manager.clear_all()` |
| ACTIVE        | `run_won`      | WIN        | `run_won`       | `_slot_manager.clear_all()` |
| DEAD          | `restart`      | START      | `run_restarted` | none                    |
| WIN           | `restart`      | START      | `run_restarted` | none                    |
| any           | unknown event  | unchanged  | none            | none (strict no-op)     |
| any           | wrong event    | unchanged  | none            | none (strict no-op)     |

Signal emission happens **before** the state variable is updated.

### File 2: `tests/scripts/system/test_run_state_manager.gd`
Primary behavioral test suite covering all state transitions, signal emission, slot reset, and no-op guards.

### File 3: `tests/scripts/system/test_run_state_manager_adversarial.gd`
Adversarial suite covering: invalid state re-entry, unknown event strings, rapid transition sequences, instance isolation, slot manager independence from external mutation, and signal order guarantees.

---

## Test Plan

### Primary Suite IDs (RSM-*)

| ID         | Description |
|------------|-------------|
| RSM-STRUCT-1 | Script exists at `res://scripts/system/run_state_manager.gd` and is loadable headlessly |
| RSM-STRUCT-2 | `RunStateManager` is not a Node |
| RSM-STRUCT-3 | Fresh instance has `get_state() == State.START` |
| RSM-STRUCT-4 | Fresh instance has `get_state_id() == "START"` |
| RSM-STRUCT-5 | All four required signal names are present |
| RSM-STRUCT-6 | `get_slot_manager()` returns a non-null object |
| RSM-TRANS-1  | `start_run` from START transitions to ACTIVE |
| RSM-TRANS-2  | `player_died` from ACTIVE transitions to DEAD |
| RSM-TRANS-3  | `run_won` from ACTIVE transitions to WIN |
| RSM-TRANS-4  | `restart` from DEAD transitions to START |
| RSM-TRANS-5  | `restart` from WIN transitions to START |
| RSM-SIGNAL-1 | `run_started` emitted on START→ACTIVE |
| RSM-SIGNAL-2 | `player_died` signal emitted on ACTIVE→DEAD |
| RSM-SIGNAL-3 | `run_won` signal emitted on ACTIVE→WIN |
| RSM-SIGNAL-4 | `run_restarted` emitted on DEAD→START |
| RSM-SIGNAL-5 | `run_restarted` emitted on WIN→START |
| RSM-SIGNAL-6 | Signal emitted before state variable changes (emit-first contract) |
| RSM-RESET-1  | `_slot_manager.clear_all()` called on ACTIVE→DEAD (slots empty after transition) |
| RSM-RESET-2  | `_slot_manager.clear_all()` called on ACTIVE→WIN (slots empty after transition) |
| RSM-RESET-3  | `_slot_manager` slots not cleared on START→ACTIVE |
| RSM-RESET-4  | `_slot_manager` slots not cleared on DEAD→START |
| RSM-NOOP-1   | Unknown event in START is no-op |
| RSM-NOOP-2   | Wrong event (`player_died`) in START is no-op |
| RSM-NOOP-3   | Wrong event (`restart`) in ACTIVE is no-op |
| RSM-NOOP-4   | Empty string event is no-op |

### Adversarial Suite IDs (ADV-RSM-*)

| ID           | Description |
|--------------|-------------|
| ADV-RSM-01   | Two instances are fully isolated (state of A does not affect B) |
| ADV-RSM-02   | Calling `apply_event("start_run")` twice from START: second call is no-op (stays ACTIVE, signal fires only once) |
| ADV-RSM-03   | Full cycle START→ACTIVE→DEAD→START→ACTIVE→WIN→START executes without error |
| ADV-RSM-04   | Signal connection/disconnection does not crash on repeated calls |
| ADV-RSM-05   | `get_slot_manager()` returns the same instance on repeated calls (not re-created) |
| ADV-RSM-06   | Filling slots externally before transition, then transitioning ACTIVE→DEAD clears them |
| ADV-RSM-07   | `get_state_id()` always returns a non-empty string from any state |
| ADV-RSM-08   | No-op event leaves slot manager unmodified |
| ADV-RSM-09   | `restart` from START (invalid) is a strict no-op — state stays START, no signal |
| ADV-RSM-10   | `player_died` from DEAD (invalid) is a strict no-op — state stays DEAD, no signal |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_CORE

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Core Simulation Agent

## Required Input Schema
```json
{
  "ticket_path": "string",
  "spec_path": "string",
  "primary_test_path": "string",
  "adversarial_test_path": "string"
}
```

## Status
Proceed

## Reason
Test suite complete. Two files written:
- `tests/scripts/system/test_run_state_manager.gd` — 21 tests covering RSM-STRUCT-1–4, RSM-TRANS-1–5, RSM-SIGNAL-1–5, RSM-RESET-1–2, RSM-NOOP-1–4.
- `tests/scripts/system/test_run_state_manager_adversarial.gd` — 10 adversarial tests covering ADV-RSM-01 through ADV-RSM-10.
Core Simulation Agent must implement `scripts/system/run_state_manager.gd` per the ticket and spec. All tests are expected to fail until implementation is complete.
