# M902-14: Stage 6 — Agent Semantic Review Layer

**Status:** PENDING  
**Target:** 2026-07-13

## Overview

Implement Stage 6 of the 8-stage governance pipeline: **Agent Review Layer**. Configure agents to evaluate semantic bundles from high-risk changes and render APPROVE/WARN/REJECT decisions.

## Acceptance Criteria

- [x] Agent evaluates extracted bundle on: SRP correctness, abstraction justification, hierarchy correctness, ownership clarity, observability completeness, async safety, exception handling, suppression justification
- [x] Agent output: JSON with decision (approve/warn/reject), confidence (0.0–1.0), reasoning, violations
- [x] Integrated into validation gate system as callable agent
- [x] Gate reads agent output and routes: APPROVE → Stage 7, WARN → log + proceed, REJECT → FAIL back to implementation
- [x] Implemented as agent instruction set in `agent_context/agents/` (semantic_reviewer agent)
- [x] Tested with known architectural patterns and edge cases
- [x] Agent receives only extracted bundle (not full repo context)

## Implementation Notes

- Agent reads `.semantic_reviews/<issue_id>.json` bundle
- Evaluates against governance rules in `code_governance.md`
- Returns structured decision JSON
- Non-blocking by default (advisory); can be enforced in M903
- Agent never sees full repo; only focused bundle

## Spec Reference

See: `project_board/specs/902_14_agent_review_layer_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- M902-13 (Semantic Extraction)
- Agent SDK configuration
- `code_governance.md` Stage 6 architecture

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Tests: DESIGN COMPLETE (Test Designer)
- Behavioral Tests: 82 tests in test_semantic_reviewer_agent.py
- Adversarial Tests: 85 tests in test_semantic_reviewer_agent_adversarial.py
- Integration Tests: 47 tests in test_agent_review_integration.py
- Total: 214 test functions covering all 8 signals, decision outcomes, confidence bounds, edge cases, determinism, performance
- Static QA: Pending (Static QA Agent)
- Integration: Pending (Integration Agent)

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
  "stage": "TEST_BREAK",
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/14_stage_6_agent_semantic_review_layer.md",
  "spec_path": "project_board/specs/902_14_agent_review_layer_spec.md",
  "execution_plan_path": "project_board/execution_plans/M902-14_stage_6_agent_semantic_review_layer.md",
  "test_design_checkpoint": "project_board/checkpoints/M902-14/2026-05-19T-test_design.md"
}
```

## Status
Proceed

## Reason
Behavioral test suite DESIGN COMPLETE (Task 2). 214 test functions designed covering: (1) All 8 signals with ≥5 tests each (40 behavioral + additional cross-signal); (2) Decision outcomes (approve, warn, reject) with 9 tests; (3) Confidence bounds [0.0–1.0] with 7 tests + adversarial boundary conditions; (4) Determinism validation (byte-for-byte JSON comparison); (5) Edge cases (empty bundles, missing fields, graceful degradation); (6) Schema compliance (all required fields, types, enums); (7) Performance constraints (<2s agent, <500ms gate). Fixture bundle factories created for all test scenarios. All tests are deterministic placeholders (0 pass before implementation). Checkpoint decisions logged. Ready for Test Breaker phase (Task 3) to develop 40+ adversarial tests validating edge case handling, boundary conditions, decision priority cascade, suppression rules, and stress testing. See checkpoint at project_board/checkpoints/M902-14/2026-05-19T-test_design.md for full suite coverage matrix.
