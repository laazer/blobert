# TICKET: 01_player_state_machine

**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Status:** Ready  
**Type:** Refactor (M1 code)

## Title

Refactor PlayerController3D: Extract implicit state management into explicit RefCounted state machine

## Description

M1's PlayerController3D manages state implicitly (jump vs. walk vs. fall detected through velocity checks). M11 needs explicit state transitions to gate attack input correctly (can't attack while HURT, can attack while FALLING, etc.).

Extract implicit states (IDLE, WALK, JUMP, FALL, WALL_CLING, HURT, DEAD, and any others) into a RefCounted FSM with:
- Enum listing all states
- `transition(new_state)` method with guard logic
- `can_transition_to(new_state)` to enforce rules
- `state_timer` tracking time in current state (for minimum action durations)

This is a non-breaking refactor: gameplay behavior unchanged, just codified as a state machine.

## Acceptance Criteria

- [ ] RefCounted state machine class created (`scripts/player/player_state_machine.gd`)
- [ ] All player states enumerated (IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING, ABSORB, MUTATE, HURT, DEAD)
- [ ] Transition rules enforced (e.g., can't go DEAD → any state)
- [ ] PlayerController3D uses state machine for all state checks
- [ ] State timer incremented each frame and reset on transition
- [ ] All M1 tests still pass (no behavior change)
- [ ] `run_tests.sh` exits 0

## Dependencies

- M1 (completed, but code will be modified)

## Notes

- Do not add attack-specific states yet (CHARGE_UP, ABILITY_USE) — M11 core will add those
- State transitions can be logged for debugging, but not required
- Minimum action durations (e.g., 0.05s before FLOAT from JUMP) should use `state_timer` checks

---

## Execution Plan

**Ticket ID:** M11-01  
**Planning revision:** 2  
**Date:** 2026-05-23  
**Next agent:** Spec Agent (Task 1)

### Executive Summary

Introduce `PlayerStateMachine` (`scripts/player/player_state_machine.gd`) as a RefCounted gameplay FSM separate from `MovementSimulation.MovementState`. Wire `PlayerController3D` to derive/update gameplay states each physics frame without changing M1 behavior. Downstream M11 tickets (input gating, attacks, frame order) depend on explicit states and `state_timer`.

### Dependency Matrix

| Dependency | Folder / State | Blocks M11-01? | Notes |
|------------|----------------|----------------|-------|
| M1 movement + player controller | Implemented (`scripts/movement/`, `scripts/player/`) | **No** (satisfied) | Code to refactor exists |
| `player_state_machine.gd` | **Absent** | N/A | Greenfield deliverable |
| M11-02 physics frame order | `backlog/` | **No** | Depends on M11-01; not a prerequisite |
| Attack states (CHARGE_UP, ABILITY_USE) | Out of scope | **No** | Deferred per ticket Notes |

**Umbrella ticket:** No. **Cycles / WARN:** None.

### Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | `agent_context/agents/2_spec/player_state_machine_spec.md`; spec exit `--type generic` |
| Test design | Test Designer Agent | 1 | `tests/scripts/player/test_player_state_machine.gd` + adversarial |
| Test break | Test Breaker Agent | 1 | DEAD terminal, HURT re-entry, min durations, MovementState naming traps |
| Implementation | Gameplay Systems Agent | 1–2 | FSM + PlayerController3D wiring; no behavior change |
| Static QA | GDScript Reviewer | 1 | `task hooks:gd-review` on changed `.gd` |
| Learning | Learning Agent | 1 | `project_board/LEARNINGS.md` entry |
| AC gatekeeper | AC Gatekeeper | 1 | AC matrix; `run_tests.sh` exit 0; commit/push before COMPLETE |

**Total:** 7–8 agent runs

### Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author normative spec: 10 gameplay states, transition matrix, `can_transition_to` / `transition` API, `state_timer` contract, derivation rules from kinematic signals (floor, velocity, wall cling, chunk stuck, damage, HP), distinction from `MovementSimulation.MovementState`, integration points in `PlayerController3D`, future-state note (no CHARGE_UP/ABILITY_USE) | Spec Agent | Ticket AC; `player_controller_3d.gd`; `enemy_state_machine.gd`; `INTEGRATION_ROADMAP.md` state section | `agent_context/agents/2_spec/player_state_machine_spec.md` | — | Spec completeness check PASS (`--type generic`); AC traceable to spec sections | **Risk:** FLOAT/ABSORB/MUTATE/HURT not explicit in code today — spec must freeze behavior-preserving rules. **Assume:** dual-layer (kinematic vs gameplay) naming documented |
| 2 | Write headless unit tests for `PlayerStateMachine`: enum coverage, guarded transitions, DEAD terminal, `state_timer` increment/reset, minimum-duration gates | Test Designer Agent | Approved spec Task 1 | `tests/scripts/player/test_player_state_machine.gd` | 1 | Tests fail (red) before implementation; assert runtime FSM behavior not markdown | **Risk:** Prose-only tests — forbidden per workflow guardrail |
| 3 | Adversarial tests: invalid transitions, double HURT, DEAD→any, timer edge at epsilon, conflation with MovementState | Test Breaker Agent | Spec + Task 2 tests | `tests/scripts/player/test_player_state_machine_adversarial.gd` | 2 | New failures encode conservative assumptions; `# CHECKPOINT` where spec ambiguous | **Assume:** strictest defensible transition denial |
| 4 | Implement `PlayerStateMachine` RefCounted class: enum (IDLE, WALK, JUMP, FALL, FLOAT, WALL_CLING, ABSORB, MUTATE, HURT, DEAD), `get_state()`, `can_transition_to()`, `transition()`, `update(delta)`, `state_timer` | Gameplay Systems Agent | Spec; red tests | `scripts/player/player_state_machine.gd` | 3 | All Task 2–3 tests PASS | **Risk:** Over-scoping attack states — stay within apply ticket Notes |
| 5 | Integrate FSM into `PlayerController3D`: instantiate machine, derive state each `_physics_process`, replace implicit velocity/floor checks used for gameplay gating, expose accessor for downstream systems; preserve `MovementSimulation` path unchanged | Gameplay Systems Agent | Task 4; controller source | Updated `scripts/player/player_controller_3d.gd` | 4 | No M1 behavior regression; controller uses FSM for state checks per AC | **Risk:** Large controller diff — minimal wiring, no unrelated refactors |
| 6 | Add controller integration/regression tests if spec requires observable wiring beyond pure FSM | Gameplay Systems Agent | Spec integration section | Additional tests under `tests/scripts/player/` only if spec mandates | 5 | Targeted tests PASS; no duplicate FSM unit coverage | **Assume:** full suite is primary regression gate |
| 7 | Run full test suite and GDScript review | GDScript Reviewer (Static QA) | Tasks 4–6 | `run_tests.sh` exit 0 evidence; review findings resolved or waived | 6 | `timeout 300 ci/scripts/run_tests.sh` → 0; no high-priority review blockers | **Risk:** Scene/integration tests sensitive to timing |
| 8 | Extract learnings (dual FSM pattern, naming, test placement) | Learning Agent | Completed implementation | `LEARNINGS.md` append | 7 | Entry references M11-01 | — |
| 9 | AC gatekeeper: verify all AC checkboxes, git clean + pushed | AC Gatekeeper | Ticket AC; test evidence | Stage COMPLETE; ticket moved to `done/` | 8 | All AC met with evidence; commit/push verified | Per workflow enforcement |
| 10 | Orchestrator: run `planner_to_spec` … `learning_to_ac_gatekeeper` gates at each transition | Autopilot Orchestrator | Checkpoint artifacts | Gate PASS logs in scoped checkpoint | Per stage | No gate skip; BLOCKED on exit 1 | Mandatory gates per `mandatory_workflow_gates_v1.md` |

### Notes

- **Non-breaking refactor:** Gameplay feel unchanged; tests are the contract.
- **Naming:** Use `PlayerStateMachine.PlayerState` (or spec-frozen name) — never alias `MovementSimulation.MovementState`.
- **Downstream:** M11-02 (frame order) expects `state_machine.update(delta)` as step 1 — spec should note hook point without implementing frame reorder here.
- **Reference read-only:** `reference_projects/`, `3D-Platformer-Kit/` — patterns only.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: RED (primary 31 failures + adversarial 45 failures — `player_state_machine.gd` not implemented; both suites parse and run)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Gameplay Systems Agent

## Required Input Schema
```json
{
  "execution_plan_section": "string — ticket Execution Plan tasks 4-6 (FSM + controller wiring)",
  "checkpoint_log": "project_board/checkpoints/M11-01/2026-05-23T-test-break-run.md",
  "spec_path": "project_board/specs/player_state_machine_spec.md",
  "primary_test_path": "tests/scripts/player/test_player_state_machine.gd",
  "adversarial_test_path": "tests/scripts/player/test_player_state_machine_adversarial.gd",
  "implementation_target": "scripts/player/player_state_machine.gd"
}
```

## Status
Proceed

## Reason
Adversarial suite complete (EC-1..EC-10 + stress/naming probes). Primary + adversarial tests RED until `PlayerStateMachine` is implemented. Gameplay Systems Agent should implement FSM and wire `PlayerController3D` per spec without behavior change.
