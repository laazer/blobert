# M902-21 Implementation Checkpoint

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md`

**Run:** 2026-05-20T-implementation-run

## Delivered

| File | Role |
|------|------|
| `ci/scripts/context_budget_tracker.py` | `record_stage_usage`, merge, metrics, path safety |
| `ci/scripts/context_budget_report.py` | Aggregate reporter CLI (`--json`, `--milestone`) |
| `ci/scripts/agent_invocation_middleware.py` | Post-invocation hook; `CONTEXT_BUDGET_TRACKING=0` opt-out |
| `project_board/checkpoints/M902-21/CONTEXT_BUDGET_METRICS.md` | Metrics interpretation guide |
| `.claude/skills/autopilot/SKILL.md` | Context budget tracking subsection |

## Test evidence

```bash
cd /Users/jacobbrandt/workspace/blobert
python -m pytest tests/ci/test_context_budget_tracking.py tests/ci/test_context_budget_tracking_adversarial.py -q
```

```
45 passed in 1.33s
```

## Notes

- Reporter allows sandbox roots named `checkpoints` or `*checkpoints` outside repo; rejects `..` traversal and `outside_repo` dirs.
- Median: average for exactly two tickets of a type; lower-middle for even counts ≥4 (adversarial contract).
