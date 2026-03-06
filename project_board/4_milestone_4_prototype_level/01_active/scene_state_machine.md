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
6

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: Failed — primary scene state machine tests pass, but adversarial test `test_unknown_events_do_not_change_trace_compared_to_filtered_sequence` in `tests/test_scene_state_machine_adversarial.gd` still fails due to the unknown-event trace equivalence requirement.
- Static QA: Not Run — no documented review mapping `SceneStateMachine` states/transitions and unknown-event semantics back to the Acceptance Criteria.
- Integration: Not Run — no documented evidence that the main 3D playable scene is using `SceneStateMachine` to switch between concrete configurations or that feature systems are correctly gated on state.

## Blocking Issues
- AC: "Primary and adversarial test suites under `tests/` cover allowed transitions, no-op combinations, determinism, and per-instance isolation for the scene state machine" is not satisfied: adversarial test `test_unknown_events_do_not_change_trace_compared_to_filtered_sequence` in `tests/test_scene_state_machine_adversarial.gd` currently fails, and there is no documented decision reconciling the unknown-event semantics with the test harness expectation that traces with and without unknown events are identical (including length).
- AC: "The main 3D playable scene uses the scene state machine via a controller or manager script to switch between at least two concrete configurations" is not evidenced: no integration or manual test notes show the 3D scene driving at least two concrete configurations via `SceneStateMachine`.
- AC: "Key feature systems in the 3D scene are gated on scene state in a way that is headless-testable where reasonable and preserves existing passing tests" is not evidenced: there is no validation that infection loop, enemies, HUD slices, or similar systems are wired through scene state without breaking existing tests.
- AC: "No new top-level `.tscn` scenes are introduced solely to represent feature variants that can be expressed via scene state" is not evidenced: no static QA review is documented confirming that recent scene changes respect this constraint.

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_id": "string",
  "description": "string",
  "acceptance_criteria": "string[]"
}
```

## Status
Needs Attention

## Reason
Ticket remains in `BLOCKED` stage because multiple Acceptance Criteria lack concrete validation evidence: (1) an adversarial unknown-event trace test in `tests/test_scene_state_machine_adversarial.gd` still fails and there is no documented decision on whether to change the test, the semantics, or the Acceptance Criteria; (2) there is no integration or manual testing record showing the main 3D scene using `SceneStateMachine` to switch between at least two concrete configurations; (3) there is no static QA review confirming that key feature systems are correctly gated on scene state and that no new top-level variant scenes were introduced. Human owner must decide how to reconcile the unknown-event test with the intended semantics, run/record integration and static QA checks against each Acceptance Criterion, and then update this ticket’s Validation Status accordingly.
