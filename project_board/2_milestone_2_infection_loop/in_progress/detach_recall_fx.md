# Detach & recall visual feedback

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Add lightweight visual feedback for the detach and recall actions so they are clearly readable without relying on HP/chunk HUD alone. This includes distinct cues for detach, recall start, and chunk reabsorption, using placeholder-friendly shapes, color, and simple effects.

## Acceptance criteria

- [ ] On detach, the player receives a brief, readable feedback cue (e.g. flash/pulse on the slime body, small burst at the chunk spawn position, or short screen shake)
- [ ] On recall start, there is a distinct cue indicating recall (e.g. Line2D “tendril” between chunk and player, or a clear color/outline change on the chunk for the travel window)
- [ ] On reabsorption, there is a clear confirmation cue (e.g. brief flash on player and/or chunk disappearance effect) that is visually distinct from detach
- [ ] Visuals do not block control; movement and input responsiveness remain unchanged during detach and recall
- [ ] Implementation is limited to scenes and presentation scripts; HP math and `simulate()` in `movement_simulation.gd` are unchanged

---

## Execution Plan

**Overview:** Detach/recall visual feedback is presentation-only. The controller will expose three events (via signals) so presentation can react without touching simulation or HP logic. Spec defines the contract; tests verify signals and presentation response; Engine Integration adds signals; Presentation implements VFX.

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Produce authoritative spec for detach/recall visual feedback: three events (detach, recall_start, reabsorb), signal contract, non-blocking and placeholder-friendly constraints. | Spec Agent | Ticket, workflow_enforcement_v1.md | Spec document (e.g. `agent_context/projects/blobert/specs/detach_recall_fx_spec.md`) covering event definitions, signal names/signatures, AC mapping, and NFR (no blocking, movement_simulation.gd unchanged). | None | Spec exists; all acceptance criteria mapped to spec items; contract for signals and presentation scope explicit. | Spec numbering continues from existing project SPEC convention if applicable; otherwise standalone. |
| 2 | Design primary tests: verify controller emits signals at detach, recall start, and reabsorb; verify presentation layer responds (e.g. testable state or node property) so feedback is not a no-op. | Test Designer | Spec from Task 1 | Primary test file(s) in `tests/`; tests run headlessly; registered in `run_tests.gd`. | Task 1 | Tests fail until Tasks 4–5 implement behavior; tests pass when signals and VFX contract are implemented. | Tests may use direct signal emission or minimal scene load; no pixel/visual assertions required. |
| 3 | Add adversarial tests: edge cases (rapid detach/recall, recall cancel, no chunk), signal ordering, and non-blocking (input/movement not stalled). | Test Breaker | Spec, primary tests from Task 2 | Adversarial test file(s); all tests registered. | Task 2 | Adversarial suite passes when implementation satisfies edge cases and NFRs. | Cancel-recall and “no chunk” cases per existing controller behavior. |
| 4 | Add three signals to PlayerController and emit at detach, recall start, and reabsorb. No change to movement_simulation.gd or HP/timer logic. | Engine Integration | Spec, current player_controller.gd | player_controller.gd updated: signal declarations and emit at existing detach (has_chunk true→false), recall start (_recall_in_progress = true), reabsorb (before queue_free and has_chunk = true). | Task 1 | Signals fire at correct frames; all existing tests still pass; no change to simulate() or MovementState. | Signal names/signatures per spec; chunk position/player position may be passed as args if spec requires. |
| 5 | Implement VFX for detach, recall start, and reabsorb per spec: placeholder-friendly cues (e.g. flash/pulse, tendril or outline, reabsorb confirmation). Scenes using PlayerController show feedback. | Presentation | Spec, Task 4 signals | Scenes/scripts that connect to controller signals and play distinct cues for each event; visuals do not block control. | Task 4 | All acceptance criteria met; primary and adversarial tests pass; manual check: cues readable, movement responsive. | VFX implemented in presentation scripts and/or scene nodes; no gameplay logic in presentation. |

**Notes:** (1) movement_simulation.gd is unchanged. (2) Clarifications and assumptions logged in `agent_context/projects/blobert/CHECKPOINTS.md` under `[detach_recall_fx] Planner`. (3) Execution order: 1 → 2 → 3 → 4 → 5; 4 and 5 may be sequenced so signals exist before presentation subscribes.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

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
Test Breaker Agent

## Required Input Schema
```json
{
  "ticket_path": "/Users/jacobbrandt/workspace/blobert/project_board/2_milestone_2_infection_loop/in_progress/detach_recall_fx.md",
  "workflow_module": "/Users/jacobbrandt/workspace/blobert/agent_context/agents/common_assets/workflow_enforcement_v1.md",
  "spec_path": "agent_context/projects/blobert/specs/detach_recall_fx_spec.md"
}
```

## Status
Proceed

## Reason
Test Designer added primary behavioral tests in tests/test_detach_recall_fx.gd (DRF-4 signal contract, DRF-1/2/3 presentation test hook, DRF-NF1 non-blocking). Tests registered in run_tests.gd. Checkpoints logged for presentation API and recall verification strategy. Stage advanced to TEST_BREAK; Test Breaker adds adversarial tests per execution plan Task 3.

