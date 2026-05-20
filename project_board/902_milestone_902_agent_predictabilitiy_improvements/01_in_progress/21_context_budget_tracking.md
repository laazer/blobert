# M902-21: Context Budget Tracking

**Status:** PENDING  
**Target:** 2026-07-22

## Overview

Implement instrumentation that tracks token usage and effective context per agent stage. Provides visibility into which agents/stages consume tokens most heavily. Enables data-driven optimization decisions (e.g., whether tool categorization actually saves tokens).

## Acceptance Criteria

- [ ] Instrument all agent calls: capture input tokens, output tokens, total tokens
- [ ] Track per-agent metrics: spec, test-designer, implementation, review, etc.
- [ ] Per-stage metrics: tokens used, effective context (input tokens / schema size), token efficiency ratio
- [ ] Log to structured checkpoint files: `project_board/checkpoints/<ticket_id>/token_usage.json`
- [ ] Report format includes:
  - [ ] Total tokens per agent
  - [ ] Avg tokens per ticket type (feature, bugfix, refactor, etc.)
  - [ ] Top 10 token consumers (which agents, which tickets)
  - [ ] Context efficiency: tokens/schema-size ratio
  - [ ] Outliers: tickets > 2× median token usage for their type
- [ ] Integration with autopilot: summary printed at end of run
- [ ] Tested with 3+ autopilot runs; data collected for analysis
- [ ] Documentation: How to interpret metrics, what to optimize for

## Implementation Notes

- Hook into Agent SDK's token counting (if available) or estimate from LLM response metadata
- Store per-checkpoint to avoid re-logging
- Timestamp each measurement for trend analysis
- Include tool categorization state (if M902-18 active) to measure effectiveness

## Example Output

```json
{
  "ticket_id": "M902-09",
  "stages": {
    "spec": {
      "input_tokens": 4250,
      "output_tokens": 1840,
      "total_tokens": 6090,
      "schema_size_tokens": 2100,
      "context_efficiency": 0.29
    },
    "implementation": {
      "input_tokens": 8900,
      "output_tokens": 3220,
      "total_tokens": 12120,
      "schema_size_tokens": 3500,
      "context_efficiency": 0.35
    }
  },
  "total_tokens": 18210,
  "avg_tokens_per_stage": 6070,
  "outliers": []
}
```

## Metrics to Report

| Metric | Definition | Target |
|--------|-----------|--------|
| **Input Efficiency** | (Input tokens / schema size) | < 2.0 |
| **Stage Efficiency** | (Total tokens / stage complexity) | Establish baseline, then optimize |
| **Per-ticket variance** | (Max tokens - Min tokens) / Median | < 50% |
| **Tool category impact** | Tokens with vs. without categorization | 15–25% reduction |

## Spec Reference

See: `project_board/specs/902_21_context_budget_tracking_spec.md`

## Dependencies

- M902-01 (Validation Gate Framework)
- Agent SDK token counting hooks
- M902-18 (Tool Categorization, for effectiveness measurement)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
TEST_DESIGN

## Revision
3

## Last Updated By
Spec Agent

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
Test Designer Agent

## Required Input Schema
```json
{
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md",
  "spec_path": "project_board/specs/902_21_context_budget_tracking_spec.md",
  "execution_plan": "project_board/execution_plans/M902-21_context_budget_tracking.md",
  "spec_checkpoint": "project_board/checkpoints/M902-21/2026-05-20T-spec-run.md"
}
```

## Status
Proceed

## Reason
Specification complete (Revision 3). Spec at `project_board/specs/902_21_context_budget_tracking_spec.md`; `spec_completeness_check.py --type generic` PASS. Author behavioral tests per spec Test Contract (`tests/ci/test_context_budget_tracking.py`).
