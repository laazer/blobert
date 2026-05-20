# M902-21 Test Design Run

**Run id:** `2026-05-20T-test-design-run`  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md`  
**Stage:** TEST_DESIGN → TEST_BREAK  
**Agent:** Test Designer Agent

---

## Outcome

Behavioral test module `tests/ci/test_context_budget_tracking.py` authored (22 test methods mapping spec Test Contract T1–T11). Handoff to Test Breaker Agent.

---

## Test contract coverage

| ID | Scenario | Test class / method |
|----|----------|---------------------|
| T1 | Merge two stages | `TestRecordStageMerge::test_merge_two_stages_preserves_both_entries` |
| T2 | Idempotent `agent_run_id` | `TestRecordStageIdempotency` (2 methods) |
| T3 | `context_efficiency` formula | `TestMetricFormulas::test_context_and_input_efficiency_ratios` |
| T4 | Missing usage → estimated | `TestUsageMetadataEstimation` (2 methods) |
| T5 | Reporter totals by agent | `TestContextBudgetReporter::test_totals_by_agent_type_sums_match_manual` |
| T6 | Avg by ticket type | `test_averages_by_ticket_type` |
| T7 | Top 10 ordering | `test_top_10_consumers_deterministic_with_eleven_tickets` |
| T8 | Outlier >2× median | `test_outlier_above_twice_median_for_ticket_type` |
| T9 | Empty reporter root | `test_empty_checkpoints_root_exit_zero` |
| T10 | Middleware opt-out env | `TestMiddlewareContextBudgetHook` (4 methods) |
| T11 | Path traversal rejected | `TestPathSafety` + `test_reporter_rejects_checkpoints_root_outside_repo` |

Additional: stage normalization, ticket_type inference/immutability, negative usage rejection, ticket_id hyphen normalization.

---

## Pytest collection (expected red — no implementation yet)

```text
$ uv run --project asset_generation/python pytest tests/ci/test_context_budget_tracking.py -v --tb=line

==================================== ERRORS ====================================
__________ ERROR collecting tests/ci/test_context_budget_tracking.py ___________
tests/ci/test_context_budget_tracking.py:64: in <module>
    _tracker = _import_ci_script("context_budget_tracker")
tests/ci/test_context_budget_tracking.py:48: in _import_ci_script
    raise ModuleNotFoundError(f"No module at {path}")
E   ModuleNotFoundError: No module at /Users/jacobbrandt/workspace/blobert/ci/scripts/context_budget_tracker.py
=========================== short test summary info ============================
ERROR tests/ci/test_context_budget_tracking.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

**Interpretation:** Collection error is intentional TDD red until Implementation Agent adds `context_budget_tracker.py` and `context_budget_report.py` and wires middleware hook.

---

## Spec gaps / questions for Spec Agent

None blocking test design. Reporter human stdout string `"No token usage data found."` and failure stderr for path escape are asserted per Requirement 09; exact wording may be adjusted in implementation if message remains semantically equivalent (Test Breaker to confirm).

---

## Handoff

- **Next:** Test Breaker Agent — adversarial/mutation pass on `tests/ci/test_context_budget_tracking.py`
- **Then:** Implementation Agent — `ci/scripts/context_budget_tracker.py`, `context_budget_report.py`, middleware hook
