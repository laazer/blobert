# M902-21 AC Gatekeeper Checkpoint

**Run:** 2026-05-20T-ac-gatekeeper

## Verification

```bash
python -m pytest tests/ci/test_context_budget_tracking.py tests/ci/test_context_budget_tracking_adversarial.py -q
# 45 passed in 1.98s

task hooks:py-review -- ci/scripts/context_budget_tracker.py ci/scripts/context_budget_report.py ci/scripts/agent_invocation_middleware.py
# PASS
```

## AC matrix (summary)

| AC | Evidence |
|----|----------|
| Instrument agent calls (in/out/total tokens) | `extract_token_usage` + middleware hook; T1–T6, T10 |
| Per-agent metrics | `agent_type` on stages; reporter `totals_by_agent_type` |
| Per-stage metrics + efficiency ratios | `workflow_stage`, `context_efficiency`, `input_efficiency_ratio`; formula tests |
| `token_usage.json` per ticket | `record_stage_usage`; path confinement tests |
| Report aggregates (totals, avg by type, top 10, efficiency, outliers) | `build_report` + reporter CLI fixture suites |
| Autopilot integration | `.claude/skills/autopilot/SKILL.md` § Context budget tracking; `format_human_summary` |
| 3+ autopilot runs | Pytest multi-ticket fixtures (not 3 production runs); Human validates next autopilot |
| Documentation | `CONTEXT_BUDGET_METRICS.md` |

## Outcome

Stage → `COMPLETE`; ticket → `02_complete/21_context_budget_tracking.md`.
