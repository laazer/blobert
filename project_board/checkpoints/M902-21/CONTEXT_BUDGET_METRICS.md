# Context Budget Metrics — Interpretation Guide

**Ticket:** M902-21 · **Spec:** `project_board/specs/902_21_context_budget_tracking_spec.md`

## What is measured

Post-invocation **actual** (or estimated) LLM token usage per agent stage is recorded in `project_board/checkpoints/<ticket_id>/token_usage.json`. This is distinct from **forecast** output from `ci/scripts/token_budget_analyzer.py`, which estimates budget before a run and does not write usage artifacts.

## Reading `token_usage.json`

- **`stages`:** One entry per `stage_key` (defaults to normalized `workflow_stage`). Latest invocation wins per key.
- **`confidence`:** `exact` when provider usage metadata was parsed; `estimated` when `char_div4` fallback was used (`estimation_method`).
- **`rollup`:** Recomputed sums across all stages after each merge.

## Input efficiency

**`input_efficiency_ratio`** = `input_tokens / max(schema_size_tokens, 1)` (2 decimals). Target **&lt; 2.0**. High values suggest prompts are large relative to the tool schema passed to the framework.

## Context efficiency

**`context_efficiency`** = `output_tokens / total_tokens` (2 decimals; `0.0` when total is 0). Low values mean most tokens were input/prompt rather than model output.

## Outliers

The reporter flags tickets where `rollup.total_tokens` is **strictly greater than** `2 × median_total_tokens` for the same `ticket_type`, requiring at least two tickets of that type. Action: split scope, reduce context, or investigate a single heavy stage in `stages`.

## Tool categorization impact

When M902-18 is active, stages may include `tool_category_state.categorization_active: true`. The reporter’s `tool_category_impact` compares average stage tokens with vs. without categorization. When inactive, the field is `null` and autopilot prints `N/A (M902-18 inactive)`.

## Baseline workflow

1. Run autopilot (or instrumented invocations) on **3+** tickets with `ticket_id` and `agent_run_id` passed to middleware.
2. Export aggregates: `python ci/scripts/context_budget_report.py --json > token_summary.json`
3. Compare medians and outliers before/after optimizations (tool filtering, prompt trimming, stage splits).
