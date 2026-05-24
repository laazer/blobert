# TICKET: 03_input_action_mapping

**Milestone:** M11 Base Mutation Attacks (Prerequisite)  
**Status:** Ready  
**Type:** Spec

## Title

Define input action mapping for M11+ attack system

## Description

Centralize and document all input actions used by M11+ (base attacks, fused attacks, future features). Create a spec that lists:
- All action names (move_left, move_right, jump, attack, absorb, mutate, swap_mutation, menu)
- Which input states permit which actions
- Default key bindings (configurable, but with defaults)
- Input consumption semantics (e.g., "attack" input doesn't also trigger "absorb")

This spec is the source of truth for input handling across M11 and M12.

## Acceptance Criteria

- [ ] Input action mapping spec written (`project_board/specs/input_action_mapping_spec.md` or embedded in this ticket)
- [ ] All input actions enumerated with descriptions
- [ ] State-action matrix: which states permit which inputs
  - Example: IDLE/WALK/JUMP/FALL permit "attack", but HURT/DEAD do not
- [ ] Default key bindings defined (can be overridden in settings)
- [ ] Input consumption rules documented (no input can trigger multiple conflicting actions)
- [ ] Spec references player state machine (from prereq 1)

## Dependencies

- M11_prereq_1_player_state_machine (spec must reference states)

## Example: State-Action Matrix

| State | move_left | move_right | jump | attack | absorb | menu |
|-------|-----------|------------|------|--------|--------|------|
| IDLE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WALK | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| JUMP | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ |
| FALL | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| WALL_CLING | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| ABSORB | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| HURT | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| DEAD | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

## Notes

- This is a spec-only ticket; no code changes in PlayerController yet
- Default bindings should match current M1 (check existing input map)
- M11 core tickets will implement the state-action gating logic

---

## Execution Plan

**Ticket ID:** M11-03  
**Planning revision:** 2  
**Date:** 2026-05-24  
**Next agent:** Spec Agent (Task 1)

### Executive Summary

Produce `project_board/specs/input_action_mapping_spec.md` as the normative contract for Godot InputMap action names, default bindings, per-`PlayerStateMachine.PlayerState` permit matrix, and single-winner input consumption rules. **No `PlayerController3D` changes in this ticket.** After spec approval, Test Designer authors **runtime** headless tests for a pure `PlayerInputActionPolicy` RefCounted module (specified in IAM spec); implementation of that module and InputMap registration are deferred to downstream M11 tickets (e.g. attack input framework). Spec exit type: `generic`.

### Dependency Matrix

| Dependency | Folder / State | Blocks M11-03? | Notes |
|------------|----------------|----------------|-------|
| M11-01 player state machine | `done/01_player_state_machine.md` | **No** (satisfied) | States + `player_state_machine_spec.md` are normative references |
| M11-02 physics frame order | `done/02_physics_frame_order.md` (COMPLETE) | **No** | Spec must name input-read phase in frozen `_physics_process` contract |
| `input_action_mapping_spec.md` | **Absent** | N/A | Greenfield at `project_board/specs/input_action_mapping_spec.md` |
| Input policy tests | **Absent** | N/A | Greenfield under `tests/scripts/player/` |
| M11-07 attack input framework | `to_update/07_*.md` | **No** (downstream consumer) | Must not block spec; spec freezes `attack` defaults for M11-07 |

**Umbrella ticket:** No. **Cycles:** None.

### Spec Exit Gate

```bash
python ci/scripts/spec_completeness_check.py \
  project_board/specs/input_action_mapping_spec.md \
  --type generic
```

### Test Strategy (Spec Contract vs Runtime)

| Tier | When | Location | What it proves | Invalid |
|------|------|----------|----------------|---------|
| **Spec completeness** | After Spec Agent | `spec_completeness_check.py --type generic` | Required IAM sections present | — |
| **Runtime unit (primary)** | TEST_DESIGN+ | `tests/scripts/player/test_player_input_action_policy.gd` | `PlayerInputActionPolicy` (RefCounted): `is_action_permitted(state, action)`, `resolve_consumed_actions(frame_edges)` per IAM tables | Asserting markdown/spec prose |
| **Runtime adversarial** | TEST_BREAK | `tests/scripts/player/test_player_input_action_policy_adversarial.gd` | Tie-break order, simultaneous edges, DEAD/HURT deny-all, unknown action fail-closed | Call-order logging unless IAM defines observable |
| **InputMap integration (optional)** | Deferred impl ticket | e.g. `test_project_input_map_actions.gd` | `InputMap.has_action()` for catalogued actions after `project.godot` updated | Parsing `.md` tickets |
| **Controller integration** | **Out of scope M11-03** | — | `_read_player_input` + FSM gating wired later | — |
| **Regression** | Downstream COMPLETE | `timeout 300 ci/scripts/run_tests.sh` | Full suite green when policy + map land | — |

**M11-03 completion boundary:** Spec AC satisfied; spec gate PASS; policy unit tests authored (RED acceptable without policy `.gd`). **Not required:** PlayerController edits or green policy tests.

### Estimated Effort (Agent Runs)

| Phase | Agent | Runs | Notes |
|-------|-------|------|-------|
| Specification | Spec Agent | 1 | IAM spec + `generic` gate |
| Test design | Test Designer Agent | 1 | Policy unit tests (RED) |
| Test break | Test Breaker Agent | 1 | Adversarial policy tests |
| Implementation | **Deferred** | 0 in M11-03 | Policy module + InputMap → M11-07+ |
| AC gatekeeper | AC Gatekeeper | 1 | Spec + test artifacts only |

**Total (M11-03):** 4–5 agent runs (no implementation stage unless scope expanded)

### Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Author IAM spec: action catalog (current `project.godot` + planned `attack`, `mutate`, `swap_mutation`, `menu` + M1 `detach`/`detach_2`/`infect`/`fuse`/`debug_kill`); default bindings table; full state×action matrix for all ten `PlayerState` values; consumption priority / mutual exclusion; input phase in PFO frame contract; `PlayerInputActionPolicy` API sketch; deferred boundary (no controller/InputMap edits in M11-03); cross-ref `player_state_machine_spec.md` | Spec Agent | Ticket AC; `project.godot` `[input]`; `player_controller_3d.gd` input usage; PSM spec; M11-07 ticket for `attack` default | `project_board/specs/input_action_mapping_spec.md` | — | `spec_completeness_check.py` PASS; every AC maps to IAM section | **Risk:** FLOAT/MUTATE target gating ambiguous — document current vs target. **Assume:** new keys proposed in spec, not committed in M11-03 |
| 2 | Spec exit gate + checkpoint | Spec Agent | Task 1 spec path | Gate PASS log in `project_board/checkpoints/M11-03/` | 1 | Exit code 0 | — |
| 3 | Design runtime unit tests for `PlayerInputActionPolicy` per IAM test strategy (matrix spot-checks, consumption winner, fail-closed unknown action) | Test Designer Agent | Approved spec | `tests/scripts/player/test_player_input_action_policy.gd`; register in `tests/run_tests.gd` | 2 | Tests fail RED before policy `.gd` exists; no prose asserts | **Risk:** Policy class name must match spec freeze |
| 4 | Adversarial tests: simultaneous `attack`+`absorb` edges, HURT/DEAD deny-all, FLOAT row, buffer/frame edge if IAM defines | Test Breaker Agent | Spec + Task 3 | `test_player_input_action_policy_adversarial.gd` | 3 | New RED cases; `# CHECKPOINT` where IAM ambiguous | Conservative tie-break per IAM |
| 5 | AC gatekeeper: verify spec AC, test files present, no controller diff | AC Gatekeeper | Ticket AC; artifacts | Stage COMPLETE; ticket → `done/` | 4 | All spec AC met; spec gate evidence; commit/push | Implementation intentionally deferred |
| 6 | Orchestrator: run `planner_to_spec` … gates per stage | Autopilot Orchestrator | Checkpoint artifacts | Gate PASS in `project_board/checkpoints/M11-03/` | Per stage | Exit 1 → BLOCKED | `mandatory_workflow_gates_v1.md` |

### Notes

- **Normative ID prefix:** `IAM-*` (mirror `PSM-*` style in player state machine spec).
- **Current vs planned:** Spec must document nine existing InputMap actions and four planned M11 actions; `debug_kill` flagged debug-only.
- **Downstream:** M11-07 consumes `attack` binding; mutation tickets consume `mutate` / `swap_mutation`.
- **Reference read-only:** `reference_projects/`, `3D-Platformer-Kit/`.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GAMEPLAY

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: adversarial 21 methods (37/38 PASS); primary 28/29 PASS; RED `debug_kill` permit (IAM-9.2, EC-IAM-12)
- Static QA: N/A
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
  "ticket_path": "project_board/11_milestone_11_base_mutation_attacks/in_progress/03_input_action_mapping.md",
  "spec_path": "project_board/specs/input_action_mapping_spec.md",
  "primary_tests": "tests/scripts/player/test_player_input_action_policy.gd",
  "adversarial_tests": "tests/scripts/player/test_player_input_action_policy_adversarial.gd",
  "checkpoint_log": "project_board/checkpoints/M11-03/2026-05-23T-test-break-run.md",
  "policy_script": "scripts/player/player_input_action_policy.gd",
  "red_tests": ["iam9_debug_kill_permitted_idle_when_enabled", "ec_iam12_debug_after_combat_winner"]
}
```

## Status
Proceed

## Reason
Adversarial IAM suite authored (21 methods, EC-IAM-1..16 coverage). Policy module exists; fix `debug_kill` matrix/permit so IAM-9.2 and EC-IAM-12 pass, then AC gatekeeper.
