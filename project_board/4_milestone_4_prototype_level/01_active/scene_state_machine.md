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
TEST_BREAK

## Revision
3

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
Test Breaker Agent

## Required Input Schema
```json
{
  "ticket_id": "string",
  "description": "string",
  "acceptance_criteria": "string[]"
}
```

## Status
Proceed

## Reason
Primary scene state machine behavioral tests have been authored and wired into the headless runner; Test Breaker Agent should now design adversarial suites and harden the contract before implementation proceeds.
