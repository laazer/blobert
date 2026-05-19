# M902-14: Stage 6 — Agent Semantic Review Layer

**Status:** PENDING  
**Target:** 2026-07-13

## Overview

Implement Stage 6 of the 8-stage governance pipeline: **Agent Review Layer**. Configure agents to evaluate semantic bundles from high-risk changes and render APPROVE/WARN/REJECT decisions.

## Acceptance Criteria

- [ ] Agent evaluates extracted bundle on: SRP correctness, abstraction justification, hierarchy correctness, ownership clarity, observability completeness, async safety, exception handling, suppression justification
- [ ] Agent output: JSON with decision (approve/warn/reject), confidence (0.0–1.0), reasoning, violations
- [ ] Integrated into validation gate system as callable agent
- [ ] Gate reads agent output and routes: APPROVE → Stage 7, WARN → log + proceed, REJECT → FAIL back to implementation
- [ ] Implemented as agent instruction set in `agent_context/agents/` (semantic_reviewer agent)
- [ ] Tested with known architectural patterns and edge cases
- [ ] Agent receives only extracted bundle (not full repo context)

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
