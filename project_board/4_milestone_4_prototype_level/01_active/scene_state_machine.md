# TICKET: scene_state_machine
Title: Scene state machine
Project: blobert
Created By: Human
Created On: 2026-03-06T00:00:00Z

---

## Description

Epic: Milestone 4 – Prototype Level  
Status: Backlog

Introduce a reusable, pure-logic scene state machine that represents different feature configurations of the 3D main scene (e.g. baseline, infection loop demo, enemy playtest) so we can toggle features via state instead of creating new scenes for each variant.

---

## Acceptance Criteria

- [ ] A `SceneStateMachine` pure logic module exists under `scripts/` (no Node or scene dependencies) with a small, well-defined set of canonical scene states and deterministic, event-driven transitions.
- [ ] Primary and adversarial test suites under `tests/` cover allowed transitions, no-op combinations, determinism, and per-instance isolation for the scene state machine, and are wired into `tests/run_tests.gd`.
- [ ] The main 3D playable scene uses the scene state machine via a controller or manager script to switch between at least two concrete configurations (e.g. baseline movement vs. infection-loop-enabled variant) without duplicating the scene.
- [ ] Key feature systems in the 3D scene (e.g. infection loop, enemies, or HUD slices) are gated on scene state in a way that is headless-testable where reasonable and preserves existing passing tests.
- [ ] No new top-level `.tscn` scenes are introduced solely to represent feature variants that can be expressed via scene state; the state machine + configuration is the primary mechanism for toggling between these variants.

---

## Dependencies

- None

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
BLOCKED

## Revision
5

## Last Updated By
Core Simulation Agent

## Validation Status
- Tests: Failed
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- Adversarial test `test_unknown_events_do_not_change_trace_compared_to_filtered_sequence` in `tests/test_scene_state_machine_adversarial.gd` requires the trace for a sequence with interleaved unknown events to be identical (including length) to the trace for the same sequence with unknown events removed, but the scene state machine is also required to treat unknown events as strict no-ops and the test harness unconditionally records one trace entry per input event. This creates an unresolvable conflict between the specified semantics and the test harness without modifying the tests themselves.

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Orchestrator Agent

## Required Input Schema
```json
{
  "ticket_id": "string",
  "description": "string",
  "acceptance_criteria": "string[]"
}
```

## Status
Blocked

## Reason
Core Simulation Agent implemented `SceneStateMachine` as a pure-logic module that satisfies all documented contracts and passes all primary and adversarial tests except for the unknown-event trace equivalence case, which appears to be a spec/test inconsistency that cannot be resolved without changing the tests; ticket is handed back to the orchestrator for guidance or test adjustment.
