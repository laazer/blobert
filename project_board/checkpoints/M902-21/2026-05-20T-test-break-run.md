# M902-21 Test Break Run

**Run id:** `2026-05-20T-test-break-run`  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md`  
**Stage:** TEST_BREAK → IMPLEMENTATION_GENERALIST  
**Agent:** Test Breaker Agent

---

## Outcome

Added `tests/ci/test_context_budget_tracking_adversarial.py` (26 tests) covering merge races, malformed JSON, reporter edge cases, middleware bypass, path traversal, and outlier math boundaries beyond the 22-method behavioral module.

---

## Adversarial matrix

| Dimension | Tests |
|-----------|-------|
| Concurrency | `TestMergeRaceConditions` (2) |
| Invalid/Corrupt | `TestMalformedTokenUsageJson` (3) |
| Reporter edge | `TestReporterEdgeCases` (5) |
| Middleware bypass | `TestMiddlewareTrackingBypass` (3) |
| Path traversal | `TestPathTraversalAdversarial` (6) |
| Outlier math | `TestOutlierMathEdgeCases` (4) |

---

## Pytest (adversarial module only)

```text
$ uv run --project asset_generation/python pytest tests/ci/test_context_budget_tracking_adversarial.py -v --tb=short

======================== 2 passed, 21 skipped in 0.07s =========================
```

- **Passed (vacuous today):** middleware missing-context skips (2) — no tracking hook in `agent_invocation_middleware.py` yet.
- **Skipped:** 21 tests pending `context_budget_tracker.py` / `context_budget_report.py`.
- **Will fail red when tracker lands unless:** only `CONTEXT_BUDGET_TRACKING=0` disables writes (`test_only_exact_zero_env_disables_tracking`).

Behavioral module still errors at collection until implementation exists (unchanged).

---

## Gaps flagged for implementation

1. Concurrent same-`stage_key` writes must leave valid JSON (last `agent_run_id` wins).
2. Corrupt on-disk JSON must raise `JSONDecodeError` without partial overwrite.
3. Reporter must skip corrupt `token_usage.json` without traceback; handle missing `rollup.total_tokens`.
4. Outlier rule: strictly `> 2 × median`; exactly `2×` is not an outlier; single-ticket types excluded.
5. Path rejection for `..`, `/`, NUL in `ticket_id`; reporter rejects checkpoints root outside repo.

---

## Handoff

Stage → `IMPLEMENTATION_GENERALIST`; implement `ci/scripts/context_budget_tracker.py`, `context_budget_report.py`, middleware hook per spec.
