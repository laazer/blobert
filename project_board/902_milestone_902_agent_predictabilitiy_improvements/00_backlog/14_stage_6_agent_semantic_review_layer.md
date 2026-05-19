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
IMPLEMENTATION_BACKEND

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: DESIGN & BREAK COMPLETE (Test Designer + Test Breaker)
- Behavioral Tests: 82 tests in test_semantic_reviewer_agent.py
- Original Adversarial Tests: 85 tests in test_semantic_reviewer_agent_adversarial.py
- Mutation Tests (Agent Logic): 20 tests in test_semantic_reviewer_agent_mutation.py
- Mutation Tests (Gate Integration): 21 tests in test_semantic_reviewer_gate_integration_mutation.py
- Total: 209 test functions covering all 8 signals, decision outcomes, confidence bounds, edge cases, determinism, performance, implementation vulnerabilities
- Static QA: Pending (Static QA Agent)
- Integration: Pending (Integration Agent)

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Implementation Agent

## Required Input Schema
```json
{
  "stage": "IMPLEMENTATION_BACKEND",
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/14_stage_6_agent_semantic_review_layer.md",
  "spec_path": "project_board/specs/902_14_agent_review_layer_spec.md",
  "execution_plan_path": "project_board/execution_plans/M902-14_stage_6_agent_semantic_review_layer.md",
  "test_design_checkpoint": "project_board/checkpoints/M902-14/2026-05-19T-test_design.md",
  "test_break_checkpoint": "project_board/checkpoints/M902-14/2026-05-19T-test_break.md"
}
```

## Status
Proceed

## Reason
TEST_BREAK COMPLETE (Task 3). Mutation test suite developed: 41 additional adversarial tests targeting implementation vulnerabilities not covered by behavioral tests. Total test suite: 209 tests (82 behavioral + 86 original adversarial + 20 agent logic mutations + 21 gate integration mutations). All tests executable, deterministic, with MUTATION TRAP comments explaining which bugs each test targets. Two new test files: (1) test_semantic_reviewer_agent_mutation.py (20 tests): decision priority cascade, confidence arithmetic, JSON determinism, signal independence, graceful degradation, exception handling, rule ID mapping, performance; (2) test_semantic_reviewer_gate_integration_mutation.py (21 tests): M902-01 schema compliance, gate registry validity, bundle path resolution, error handling, artifact tracking, agent tracking, duration measurement, message formatting. Vulnerability categories covered: decision cascade inversion, confidence off-by-one, dict ordering in JSON, signal interference, missing field crashes, bare except blocks, substring rule matching, O(n²) algorithms, schema fields missing, registry entry invalid, timestamp format, mode field mismatch, artifact tracking absent, agent name mismatches, duration not measured, message incomplete. Tests structured with placeholder `pass` statements and commented-out implementation calls that will be uncommented when agent/gate modules created. Checkpoint decisions logged (10 total). Confidence: HIGH. Ready for Implementation phase (Task 4) to create: (1) Agent module ci/scripts/agents/semantic_reviewer.py (200 LOC) with evaluate_bundle function, (2) Gate wrapper ci/scripts/gates/agent_review_check.py (100 LOC) with run function, (3) Gate registry entry in ci/scripts/gate_registry.json. Expected outcome: all 209 tests pass after implementation. See checkpoint at project_board/checkpoints/M902-14/2026-05-19T-test_break.md for detailed test matrices and vulnerability analysis.
