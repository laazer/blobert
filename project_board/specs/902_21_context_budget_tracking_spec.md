# Spec: Context Budget Tracking — LLM Token Usage Instrumentation & Reporting

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md`

**Milestone:** 902 — Agent Predictability Improvements

**Execution plan:** `project_board/execution_plans/M902-21_context_budget_tracking.md`

**Agent:** Spec Agent

**Date:** 2026-05-20

**Status:** SPECIFICATION

**Revision:** 1

---

## Executive Summary

This specification defines **post-invocation** instrumentation that records actual (or best-effort estimated) LLM token usage per agent/stage, persists per-ticket artifacts at `project_board/checkpoints/<ticket_id>/token_usage.json`, aggregates cross-ticket metrics via a reporter CLI, and prints an autopilot end-of-run summary.

**In scope:**

1. Recorder module `ci/scripts/context_budget_tracker.py` with merge/idempotency semantics
2. Middleware hook in `ci/scripts/agent_invocation_middleware.py` (`invoke_agent_with_category_filtering`, post-`framework_invocation_fn`)
3. Reporter module `ci/scripts/context_budget_report.py` (or equivalent CLI entry)
4. `UsageMetadata` adapter contract for `framework_invocation_fn` return values + estimation fallback
5. Autopilot skill appendix for end-of-run summary invocation
6. Metrics interpretation appendix (linked from ticket)

**Out of scope:**

- Changing `ci/scripts/token_budget_analyzer.py` (pre-flight **forecast** only; remains separate command)
- Vendoring the external Claude Agent SDK
- Blocking M902-21 on M902-18 tool categorization layer (`03_blocked/`) — optional A/B fields only
- Gate-runner integration (orthogonal to `ci/scripts/audit_log.py`)

**Prerequisites (satisfied):** M902-01 Validation Gate Framework; M902-18a Framework Integration (`agent_invocation_middleware.py`).

---

## Assumptions and Checkpoint Resolutions

| # | Ambiguity | Resolution (normative) | Confidence |
|---|-----------|------------------------|------------|
| A1 | Agent SDK usage field names | Adapter reads multiple shapes (Requirement 03); missing → estimation with `confidence: "estimated"`. | Medium |
| A2 | M902-18 blocked | `tool_category_state` optional; `categorization_active: false` when unavailable. Tool-category impact report slice is **best-effort** (Requirement 09). | High |
| A3 | `schema_size_tokens` measurement | UTF-8 byte length of compact JSON serialization of tools passed to framework, integer-divided by 4 (`chars_per_token = 4`). Documented ±25% vs true tokenizer. | High |
| A4 | `context_efficiency` formula | `output_tokens / total_tokens` (2 decimal places), `total_tokens == 0` → `0.0`. Matches ticket example for `spec` stage (1840/6090 ≈ 0.29). Distinct from **input efficiency** (`input_tokens / schema_size_tokens`). | High |
| A5 | `ticket_type` for averages | Inference rules in Requirement 08; default `generic`. | Medium |
| A6 | Stage vs agent_type | `workflow_stage` from orchestrator kwargs when provided; else normalized `agent_type` (Requirement 07). | High |
| A7 | Opt-out | `CONTEXT_BUDGET_TRACKING=0` disables hook writes; middleware behavior unchanged otherwise. | High |

---

## Deferred Boundary Statement

- **Forecast vs actuals:** `token_budget_analyzer.py` is not modified and must not write `token_usage.json`.
- **Audit logs:** `audit_log.py` gate lifecycle events remain separate; no LLM token fields added there in M902-21.
- **M902-18 layer:** Full categorization A/B comparison ships only when M902-18 unblocks; until then reporter emits `tool_category_impact: null` with reason `categorization_unavailable`.
- **Automatic orchestrator wiring:** Autopilot skill documents the contract; shell wrapper under `ci/scripts/` may be added in implementation if skill-only invocation is insufficient.

---

## Requirement 01: Artifact Path & File Lifecycle

### 1. Spec Summary

- **Description:** Each ticket accumulates usage in a single JSON file under its checkpoint directory. Reporter scans all such files under a configurable checkpoints root.

- **Path:** `project_board/checkpoints/<ticket_id>/token_usage.json`

- **ticket_id normalization:** Uppercase short tag with hyphen (e.g. `M902-21`). Input `M902_21` → `M902-21`. Reject path segments containing `/`, `..`, or NUL.

- **Constraints:**
  - Repo-relative paths only; implementation must resolve under repo root and reject traversal.
  - Auto-create parent directory on first write (`mkdir -p` equivalent).
  - UTF-8 JSON, `indent=2`, `ensure_ascii=False`.
  - File is **merged** across stages within a ticket run; never full-file replace except initial create.

- **Assumptions:** Current working directory is repository root when invoked from middleware, CLI, or tests.

- **Scope:** All agent invocations routed through `invoke_agent_with_category_filtering` when tracking enabled.

### 2. Acceptance Criteria

- **AC-01.1:** First `record_stage_usage` for `M902-21` creates `project_board/checkpoints/M902-21/token_usage.json` with top-level `ticket_id: "M902-21"`.
- **AC-01.2:** Second stage for same ticket **appends/merges** into `stages` without removing prior stage entries.
- **AC-01.3:** Path `../../etc/passwd` or `ticket_id` containing `..` raises `ValueError` (or project-standard path error); no file written outside `project_board/checkpoints/`.
- **AC-01.4:** Corrupt existing JSON on merge attempt → fail-closed: raise parse error; do not overwrite with partial data (caller may catch and log).

### 3. Risk & Ambiguity Analysis

- **R1:** Concurrent writes from parallel agents — spec mandates last-write-wins **per stage key** only (Requirement 05); full-file concurrent writes are undefined; orchestrator should serialize per ticket.
- **R2:** Disk full — propagate `OSError`; autopilot logs verbatim per workflow.

### 4. Clarifying Questions

- None (resolved in Assumptions table).

---

## Requirement 02: `token_usage.json` Schema

### 1. Spec Summary

- **Description:** Normative JSON structure for per-ticket usage. All numeric token fields are non-negative integers.

#### Top-level object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Always `"1.0.0"` for M902-21 |
| `ticket_id` | string | yes | Normalized ticket id |
| `ticket_type` | string | yes | One of `feature`, `bugfix`, `refactor`, `generic` (Requirement 08) |
| `ticket_path` | string | null | Repo-relative path to ticket `.md` if known |
| `created_at` | string | yes | ISO 8601 UTC set on first write; unchanged on merge |
| `updated_at` | string | yes | ISO 8601 UTC; refreshed on every successful merge |
| `stages` | object | yes | Map **stage_key** → stage record (below) |
| `rollup` | object | yes | Recomputed on every merge (below) |
| `outliers` | array | yes | Per-ticket outlier flags (may be empty); see Requirement 09 |
| `tool_category_state` | object | null | Optional run-level summary when any stage had categorization; else `null` |

#### Stage record (`stages[<stage_key>]`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_stage` | string | yes | Normalized stage (Requirement 07) |
| `agent_type` | string | yes | Raw `agent_type` argument to middleware |
| `agent_run_id` | string | yes | Unique id for this invocation (Requirement 05) |
| `recorded_at` | string | yes | ISO 8601 UTC |
| `input_tokens` | int | yes | Prompt/input tokens (exact or estimated) |
| `output_tokens` | int | yes | Completion/output tokens |
| `total_tokens` | int | yes | Must equal `input_tokens + output_tokens` |
| `schema_size_tokens` | int | yes | Tool schema size (Requirement 04) |
| `context_efficiency` | float | yes | Requirement 04 formula |
| `input_efficiency_ratio` | float | yes | `input_tokens / max(schema_size_tokens, 1)`, 2 decimals |
| `confidence` | string | yes | `"exact"` or `"estimated"` |
| `estimation_method` | string | null | Required when `confidence` is `"estimated"`; e.g. `"char_div4"` |
| `tool_category_state` | object | null | Per-stage optional (Requirement 09) |

#### Rollup object (`rollup`)

| Field | Type | Description |
|-------|------|-------------|
| `total_tokens` | int | Sum of stage `total_tokens` |
| `total_input_tokens` | int | Sum of stage `input_tokens` |
| `total_output_tokens` | int | Sum of stage `output_tokens` |
| `avg_tokens_per_stage` | float | `total_tokens / max(stage_count, 1)`, 2 decimals |
| `stage_count` | int | `len(stages)` |
| `max_stage_tokens` | int | Max stage `total_tokens` |
| `max_stage_key` | string | Stage key with max tokens |

#### Example (normative shape; values illustrative)

```json
{
  "schema_version": "1.0.0",
  "ticket_id": "M902-09",
  "ticket_type": "feature",
  "ticket_path": "project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/09_example.md",
  "created_at": "2026-05-20T14:00:00Z",
  "updated_at": "2026-05-20T16:30:00Z",
  "stages": {
    "spec": {
      "workflow_stage": "spec",
      "agent_type": "spec",
      "agent_run_id": "550e8400-e29b-41d4-a716-446655440000",
      "recorded_at": "2026-05-20T14:05:00Z",
      "input_tokens": 4250,
      "output_tokens": 1840,
      "total_tokens": 6090,
      "schema_size_tokens": 2100,
      "context_efficiency": 0.3,
      "input_efficiency_ratio": 2.02,
      "confidence": "exact",
      "estimation_method": null,
      "tool_category_state": {
        "categorization_active": true,
        "category": "parse",
        "tools_before": 42,
        "tools_after": 12
      }
    },
    "implementation": {
      "workflow_stage": "implementation",
      "agent_type": "implementation",
      "agent_run_id": "660e8400-e29b-41d4-a716-446655440001",
      "recorded_at": "2026-05-20T16:30:00Z",
      "input_tokens": 8900,
      "output_tokens": 3220,
      "total_tokens": 12120,
      "schema_size_tokens": 3500,
      "context_efficiency": 0.27,
      "input_efficiency_ratio": 2.54,
      "confidence": "estimated",
      "estimation_method": "char_div4",
      "tool_category_state": null
    }
  },
  "rollup": {
    "total_tokens": 18210,
    "total_input_tokens": 13150,
    "total_output_tokens": 5060,
    "avg_tokens_per_stage": 9105.0,
    "stage_count": 2,
    "max_stage_tokens": 12120,
    "max_stage_key": "implementation"
  },
  "outliers": [],
  "tool_category_state": null
}
```

- **Constraints:** Unknown fields in incoming merge payloads are stripped before persist (forward-compatible writers may add fields in future schema versions only via version bump).

- **Assumptions:** `stage_key` defaults to normalized `workflow_stage` unless orchestrator passes explicit `stage_key` in context.

- **Scope:** All recorded invocations for a ticket.

### 2. Acceptance Criteria

- **AC-02.1:** Serialized file validates against field types above; negative `input_tokens` rejected at record time.
- **AC-02.2:** `total_tokens` always equals `input_tokens + output_tokens` on write.
- **AC-02.3:** `rollup` recomputed from `stages` after every merge (deterministic).
- **AC-02.4:** `schema_version` mismatch on read → `ValueError` with message containing `unsupported schema_version`.

### 3. Risk & Ambiguity Analysis

- Ticket example rounded `context_efficiency` to `0.29`; spec uses 2-decimal rounding (0.30 for 1840/6090). Tests must use spec formula, not informal example rounding.

### 4. Clarifying Questions

- None.

---

## Requirement 03: `UsageMetadata` Adapter & Estimation Fallback

### 1. Spec Summary

- **Description:** Extract token counts from `framework_invocation_fn` return value when possible; otherwise estimate from prompt and serialized response.

#### Extraction order (first match wins)

1. Return value is `dict` with nested `usage` dict containing `input_tokens` and `output_tokens` (int ≥ 0).
2. Return value is `dict` with top-level `input_tokens` and `output_tokens`.
3. Return value is `dict` with `usage_metadata` dict (same keys as 1).
4. Return value object with attributes `.usage.input_tokens` / `.output_tokens` (int-like).

If all fail → **estimation path**.

#### Estimation path (`confidence: "estimated"`)

- `input_tokens` = `len(prompt.encode("utf-8")) // 4`
- `output_tokens` = `len(response_text.encode("utf-8")) // 4` where `response_text` is:
  - `json.dumps(result)` if result is dict/list
  - `str(result)` otherwise
- `estimation_method`: `"char_div4"`
- Documented bounds: ±25% vs model tokenizer at 95% confidence for English-heavy text.

#### `record_stage_usage` signature (implementation contract)

```python
def record_stage_usage(
    ticket_id: str,
    *,
    agent_type: str,
    prompt: str,
    tools: list[dict[str, Any]],
    framework_result: Any,
    agent_run_id: str,
    workflow_stage: str | None = None,
    stage_key: str | None = None,
    ticket_path: str | None = None,
    ticket_type: str | None = None,
    checkpoints_root: Path | None = None,
) -> None:
    ...
```

- **Constraints:**
  - Never raises on estimation success path except path/validation errors.
  - Framework exceptions propagate **before** record call (middleware records only after successful `framework_invocation_fn` return).
  - Failed invocations are not recorded unless a future ticket adds explicit failure records (out of scope).

- **Assumptions:** Orchestrator supplies stable `agent_run_id` (UUID string recommended).

- **Scope:** `context_budget_tracker.py` and middleware post-call hook.

### 2. Acceptance Criteria

- **AC-03.1:** Dict `{"usage": {"input_tokens": 100, "output_tokens": 50}, "content": "..."}` → `confidence: "exact"`, totals 150.
- **AC-03.2:** Opaque string result with no usage keys → `confidence: "estimated"`, `estimation_method: "char_div4"`.
- **AC-03.3:** Negative usage values → `ValueError`, no file write.
- **AC-03.4:** `total_tokens` derived as sum, not taken from provider if provider also sends `total_tokens` that disagrees — **recompute** from input+output.

### 3. Risk & Ambiguity Analysis

- Provider-specific field names (`prompt_tokens`, `completion_tokens`) — adapter MAY map aliases in implementation if documented in module docstring; tests cover at least Anthropic-style `input_tokens`/`output_tokens`.

### 4. Clarifying Questions

- None.

---

## Requirement 04: Metric Formulas

### 1. Spec Summary

- **Description:** Frozen formulas for derived metrics.

| Metric | Formula | Notes |
|--------|---------|-------|
| `schema_size_tokens` | `len(json.dumps(tools, separators=(",", ":"), sort_keys=True).encode("utf-8")) // 4` | `tools` = list passed to framework (filtered or all) |
| `context_efficiency` | `round(output_tokens / total_tokens, 2)` if `total_tokens > 0` else `0.0` | Fraction of total tokens that are output |
| `input_efficiency_ratio` | `round(input_tokens / max(schema_size_tokens, 1), 2)` | Target **< 2.0** per ticket optimization table |
| `effective_context_ratio` | Same as `input_efficiency_ratio` | Synonym for reporting docs |

**Optimization targets (informational, not gate failures in M902-21):**

| Metric | Target |
|--------|--------|
| Input efficiency (`input_efficiency_ratio`) | < 2.0 |
| Per-ticket variance (reporter) | < 50% of median for type |
| Tool category impact | 15–25% reduction when M902-18 active |

- **Assumptions:** `chars_per_token = 4` matches estimation path for consistency.

- **Scope:** Recorder and reporter aggregations.

### 2. Acceptance Criteria

- **AC-04.1:** `input_tokens=4250`, `output_tokens=1840`, `schema_size_tokens=2100` → `context_efficiency=0.3`, `input_efficiency_ratio=2.02`.
- **AC-04.2:** `schema_size_tokens=0` with positive input → `input_efficiency_ratio` equals `input_tokens` (divide by 1).
- **AC-04.3:** Empty tools list → `schema_size_tokens=0` (serialized `[]` is 2 bytes → 0 tokens).

### 3. Risk & Ambiguity Analysis

- True tokenizer would differ; cross-run comparisons remain valid if method is stable.

### 4. Clarifying Questions

- None.

---

## Requirement 05: Idempotency & Merge Semantics

### 1. Spec Summary

- **Description:** At most one measurement per logical invocation; retries replace rather than duplicate.

- **Idempotency key:** `(ticket_id, stage_key, agent_run_id)` where `stage_key` = explicit `stage_key` or normalized `workflow_stage`.

- **Merge rules:**
  1. Load existing file if present; else initialize empty document per Requirement 02.
  2. If `stages[stage_key].agent_run_id` equals incoming `agent_run_id` → **replace** that stage entry entirely.
  3. If `stage_key` exists with **different** `agent_run_id` → **replace** stage entry (last invocation wins for that stage slot).
  4. Recompute `rollup`, `updated_at`, and per-ticket `outliers` (may be empty until reporter cross-ticket pass — store `outliers: []` at ticket level; cross-ticket outlier detection is reporter-owned per Requirement 09).

- **Assumptions:** Same stage re-run with new `agent_run_id` overwrites previous measurement for that `stage_key`.

- **Scope:** `record_stage_usage` only.

### 2. Acceptance Criteria

- **AC-05.1:** Two records same `(ticket_id, stage_key, agent_run_id)` → one stage entry, second values win.
- **AC-05.2:** Two records same `stage_key`, different `agent_run_id` → one stage entry (latest write).
- **AC-05.3:** `spec` then `test-designer` stages → two keys in `stages`, `rollup.stage_count == 2`.

### 3. Risk & Ambiguity Analysis

- Duplicate stage keys from orchestrator misconfiguration — last write wins; reporter still aggregates by `workflow_stage` field inside record.

### 4. Clarifying Questions

- None.

---

## Requirement 06: Middleware Integration & Opt-Out

### 1. Spec Summary

- **Description:** After successful `framework_invocation_fn` in `invoke_agent_with_category_filtering`, optionally call `record_stage_usage`.

- **Hook placement:** Lines after framework call (~205–210 in current middleware); use `tools_to_use` for schema size.

- **Context kwargs (from `framework_kwargs` or explicit middleware kwargs in implementation):**
  - `ticket_id` (required for recording)
  - `agent_run_id` (required)
  - `workflow_stage` (optional)
  - `stage_key` (optional)
  - `ticket_path`, `ticket_type` (optional)

- **Opt-out:** If environment variable `CONTEXT_BUDGET_TRACKING` is exactly `"0"`, skip `record_stage_usage` entirely (no file write, no logging error).

- **Missing context:** If `ticket_id` or `agent_run_id` absent → skip recording, log **one** DEBUG line per process: `"context budget tracking skipped: missing ticket_id or agent_run_id"`.

- **Backward compatibility:** Return value from middleware unchanged; tracking must not alter framework result.

- **Assumptions:** Production orchestrator passes `ticket_id` and `agent_run_id` on every tracked invocation.

- **Scope:** `agent_invocation_middleware.py` + `context_budget_tracker.py`.

### 2. Acceptance Criteria

- **AC-06.1:** With tracking enabled and context present, one middleware invocation creates/updates `token_usage.json`.
- **AC-06.2:** `CONTEXT_BUDGET_TRACKING=0` → no file created when otherwise would record.
- **AC-06.3:** Framework raises → no `token_usage.json` update for that call.
- **AC-06.4:** Middleware return value bit-identical to framework return (dict equality for dict results).

### 3. Risk & Ambiguity Analysis

- Orchestrator forgets kwargs → silent skip; integration task 8 must verify real autopilot passes kwargs.

### 4. Clarifying Questions

- None.

---

## Requirement 07: Stage & Agent Normalization

### 1. Spec Summary

- **Description:** Normalize `agent_type` and `workflow_stage` strings to stable snake_case keys.

| Raw input (case-insensitive) | Normalized `workflow_stage` |
|------------------------------|----------------------------|
| `planner`, `planning` | `planning` |
| `spec`, `specification`, `spec agent` | `spec` |
| `test-designer`, `test_designer`, `test design` | `test-designer` |
| `test-breaker`, `test_breaker`, `test break` | `test-breaker` |
| `implementation`, `implementation-generalist`, `implementation agent` | `implementation` |
| `implementation-backend`, `backend` | `implementation-backend` |
| `implementation-frontend`, `frontend` | `implementation-frontend` |
| `static-qa`, `static_qa`, `reviewer`, `python-reviewer`, `code-reviewer` | `review` |
| `integration` | `integration` |
| `ac-gatekeeper`, `acceptance`, `gatekeeper` | `acceptance` |
| `learning` | `learning` |
| `deployment` | `deployment` |
| anything else | `unknown` |

- **stage_key default:** normalized `workflow_stage` unless orchestrator overrides.

- **Per-agent metrics:** Reporter groups by `agent_type` field preserved from invocation (original string), **and** by normalized `workflow_stage` for stage tables.

- **Assumptions:** Autopilot stage enum maps 1:1 to rows above where applicable.

- **Scope:** Recorder normalization function `normalize_workflow_stage(agent_type: str, workflow_stage: str | None) -> str`.

### 2. Acceptance Criteria

- **AC-07.1:** `agent_type="Spec Agent"` + no workflow_stage → `workflow_stage="spec"`.
- **AC-07.2:** `workflow_stage="TEST_DESIGN"` → `test-designer`.
- **AC-07.3:** `agent_type="custom-bot"` → `unknown`.

### 3. Risk & Ambiguity Analysis

- New agent aliases require table updates; unknown bucket prevents crash.

### 4. Clarifying Questions

- None.

---

## Requirement 08: Ticket Type Inference

### 1. Spec Summary

- **Description:** Classify tickets for reporter averages.

| `ticket_type` | Inference rule (first match wins) |
|---------------|-----------------------------------|
| `bugfix` | Ticket path contains `bugfix` (case-insensitive) OR title/heading contains `bugfix` or `fix:` |
| `refactor` | Path or title contains `refactor` |
| `feature` | Autopilot description mode (orchestrator sets explicitly), OR path contains `/feature/`, OR title starts with `feat:` or contains `feature` in first heading |
| `generic` | Default when no rule matches |

- **Override:** If `record_stage_usage(..., ticket_type="bugfix")` provided, use as-is after validating membership in allowed set.

- **Assumptions:** `ticket_path` read from disk when recording if not passed.

- **Scope:** First write sets `ticket_type` on file; later merges must not change `ticket_type` if already set (immutable after create).

### 2. Acceptance Criteria

- **AC-08.1:** Path `.../bugfix/foo.md` → `ticket_type: "bugfix"`.
- **AC-08.2:** Unclassified ticket → `generic`.
- **AC-08.3:** File already has `ticket_type: "feature"` → merge does not overwrite with `generic`.

### 3. Risk & Ambiguity Analysis

- Mis-inferred type affects outlier baselines; orchestrator may pass explicit type for accuracy.

### 4. Clarifying Questions

- None.

---

## Requirement 09: Aggregate Reporter CLI

### 1. Spec Summary

- **Description:** `ci/scripts/context_budget_report.py` scans `**/token_usage.json` under checkpoints root and emits structured aggregate report.

#### CLI

```
python ci/scripts/context_budget_report.py [--checkpoints-root PATH] [--milestone PREFIX] [--json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--checkpoints-root` | `project_board/checkpoints` | Root directory to scan |
| `--milestone` | none | If set, only tickets under subdirs matching `*<PREFIX>*` (case-insensitive substring) |
| `--json` | off | Emit machine-readable JSON to stdout |

Exit codes: `0` success, `1` invalid args/path, `2` usage error.

#### Report JSON (`--json`)

| Section | Content |
|---------|---------|
| `generated_at` | ISO 8601 UTC |
| `tickets_scanned` | int |
| `totals_by_agent_type` | map agent_type → sum `total_tokens` across all stages |
| `totals_by_workflow_stage` | map normalized stage → sum tokens |
| `averages_by_ticket_type` | map ticket_type → `{median_total_tokens, mean_total_tokens, ticket_count}` |
| `top_10_consumers` | list of `{ticket_id, total_tokens, max_stage_key, ticket_type}` sorted by `total_tokens` desc, tie-break `ticket_id` asc |
| `efficiency_summary` | `{mean_context_efficiency, mean_input_efficiency_ratio}` across all stages |
| `outliers` | tickets where `rollup.total_tokens > 2 * median_total_tokens` for that ticket's `ticket_type` (requires ≥2 tickets of same type for median; else excluded from outlier list) |
| `tool_category_impact` | `null` or `{with_categorization_avg, without_categorization_avg, reduction_percent}` when ≥1 stage has `categorization_active: true` |

**Vacuous input:** Zero files → exit `0`, JSON with empty arrays/zero counts, human stdout message `"No token usage data found."`

- **Path safety:** Reject `--checkpoints-root` resolving outside repo root.

- **Assumptions:** Each file `rollup.total_tokens` is authoritative per ticket.

- **Scope:** Reporter only; does not mutate checkpoint files.

### 2. Acceptance Criteria

- **AC-09.1:** Two fixture tickets in tmp checkpoints → `totals_by_agent_type` sums match manual sum.
- **AC-09.2:** Eleven tickets → `top_10_consumers` length 10, deterministic ordering.
- **AC-09.3:** Type `feature` median 1000; ticket with 2500 tokens → listed in `outliers`.
- **AC-09.4:** Empty root → exit 0, no stderr traceback.
- **AC-09.5:** `../outside` checkpoints-root → exit 1.

### 3. Risk & Ambiguity Analysis

- Single-ticket type median undefined → no outlier for that type (documented).

### 4. Clarifying Questions

- None.

---

## Requirement 10: Autopilot End-of-Run Summary

### 1. Spec Summary

- **Description:** After each ticket reaches terminal stage (`COMPLETE` or `BLOCKED`) during an autopilot run, orchestrator invokes reporter scoped to tickets touched in that run, then prints human-readable summary to stdout and references paths in scoped checkpoint log.

#### Human-readable sections (stdout)

1. **Header:** `Context Budget Summary — <run_id>`
2. **Totals:** aggregate tokens across scanned tickets
3. **Top stages:** top 3 `workflow_stage` by token sum
4. **Top tickets:** top 5 from `top_10_consumers`
5. **Outliers:** list ticket ids or `None`
6. **Tool categorization:** `N/A (M902-18 inactive)` or reduction percent when data present

#### Optional artifact

- `project_board/checkpoints/<run_scope_id>/token_summary.json` — copy of reporter JSON for run; `<run_scope_id>` = autopilot run folder if created, else ticket id for single-ticket runs.

#### Skill contract (`.claude/skills/autopilot/SKILL.md` appendix)

- Add subsection **Context budget tracking (M902-21)** stating:
  - Pass `ticket_id`, `agent_run_id`, `workflow_stage` into middleware invocations.
  - After terminal ticket state, run `context_budget_report.py` with checkpoints root.
  - Paste summary section into scoped checkpoint log (not `CHECKPOINTS.md` body).

- **Assumptions:** Run processes tickets sequentially (existing autopilot hard rule).

- **Scope:** Documentation + orchestrator behavior; implementation in Task 6.

### 2. Acceptance Criteria

- **AC-10.1:** Single-ticket autopilot dry-run leaves `token_usage.json` and stdout contains `Context Budget Summary`.
- **AC-10.2:** Skill appendix exists with three bullets above (verified by file read test or integration script in Task 6).
- **AC-10.3:** `CHECKPOINTS.md` index entry may point to `token_summary.json` path; no full JSON body in index.

### 3. Risk & Ambiguity Analysis

- Forgetting reporter invocation → AC-10 unsatisfied; AC gatekeeper checks integration log (Task 8).

### 4. Clarifying Questions

- None.

---

## Requirement 11: Documentation — Metrics Interpretation

### 1. Spec Summary

- **Description:** Human-facing guide at `project_board/checkpoints/M902-21/CONTEXT_BUDGET_METRICS.md` (created in implementation Task 7; content defined here).

**Required sections:**

1. **What is measured** — actuals vs `token_budget_analyzer.py` forecast
2. **Reading `token_usage.json`** — stage keys, confidence field
3. **Input efficiency** — target < 2.0; high ratio → bloated prompts vs tool schema
4. **Context efficiency** — output/total; low → heavy input relative to output
5. **Outliers** — 2× median rule; action: split ticket or reduce scope
6. **Tool categorization impact** — how to read `tool_category_impact` when M902-18 active
7. **Baseline workflow** — collect 3+ runs, export reporter JSON, compare before/after optimizations

- **Assumptions:** Audience is agent operators and humans reviewing milestone retrospectives.

- **Scope:** Documentation only in Task 7; spec defines required headings.

### 2. Acceptance Criteria

- **AC-11.1:** Doc contains all seven section headings listed above.
- **AC-11.2:** Doc links to this spec path and `ci/scripts/token_budget_analyzer.py` as forecast counterpart.

### 3. Risk & Ambiguity Analysis

- None.

### 4. Clarifying Questions

- None.

---

## Requirement 12: Integration Evidence (3+ Autopilot Runs)

### 1. Spec Summary

- **Description:** Validation task (post-implementation) produces log `project_board/checkpoints/M902-21/<date>T-integration-validation.md` with:

- ≥3 distinct autopilot run ids
- Per run: path to `token_usage.json`, excerpt of reporter stdout (summary headers only)
- Confirmation `Context Budget Summary` printed

- **Assumptions:** Runs may be `lean` on small tickets.

- **Scope:** Integration stage; not implemented by spec author.

### 2. Acceptance Criteria

- **AC-12.1:** Integration log lists ≥3 runs with artifact paths.
- **AC-12.2:** Ticket Validation Status updated to Integration: Passing with log pointer.

### 3. Risk & Ambiguity Analysis

- Long-running; failures logged verbatim.

### 4. Clarifying Questions

- None.

---

## Failure Taxonomy

| Condition | Behavior | Observable |
|-----------|----------|------------|
| Invalid `ticket_id` / path traversal | `ValueError`, no write | Exception message contains `invalid ticket_id` or `path` |
| Negative token fields | `ValueError`, no write | `negative token count` |
| Unsupported `schema_version` on read | `ValueError` | `unsupported schema_version` |
| Corrupt JSON existing file | `json.JSONDecodeError` propagates | Caller logs stderr |
| Missing tracking context in middleware | Skip record | DEBUG log once |
| `CONTEXT_BUDGET_TRACKING=0` | Skip record | No new/updated file |
| Reporter empty scan | Exit 0 | `No token usage data found.` |
| Reporter path escape | Exit 1 | stderr explains rejection |

---

## Test Contract (for Test Designer)

**Module:** `tests/ci/test_context_budget_tracking.py` (traceability: M902-21, this spec).

| # | Scenario | Requirement |
|---|----------|-------------|
| T1 | Merge two stages without clobber | 01, 05 |
| T2 | Idempotent same `agent_run_id` | 05 |
| T3 | `context_efficiency` formula | 04 |
| T4 | Missing usage → estimated | 03 |
| T5 | Reporter totals by agent | 09 |
| T6 | Avg by ticket type | 08, 09 |
| T7 | Top 10 ordering | 09 |
| T8 | Outlier >2× median | 09 |
| T9 | Empty reporter root | 09 |
| T10 | Middleware opt-out env | 06 |
| T11 | Path traversal rejected | 01, 09 |

**Test realism:** Assert on JSON files, exit codes, and computed numeric fields — not markdown ticket prose.

**Isolation:** `tmp_path` checkpoints root; `unittest.mock` for framework returns.

---

## Acceptance Criteria Traceability (Ticket → Spec)

| Ticket AC | Spec requirements |
|-----------|-------------------|
| Instrument all agent calls (in/out/total) | 03, 06 |
| Per-agent metrics | 07, 09 |
| Per-stage metrics + context efficiency | 04, 07 |
| Log `token_usage.json` | 01, 02 |
| Report totals, avg by type, top 10, efficiency, outliers | 09 |
| Autopilot end-of-run summary | 10 |
| 3+ autopilot runs | 12 |
| Documentation interpret metrics | 11 |
| Tool categorization effectiveness | 02, 09 (optional/nullable) |

---

## Implementation File Map (informative)

| File | Role |
|------|------|
| `ci/scripts/context_budget_tracker.py` | `record_stage_usage`, merge, formulas |
| `ci/scripts/context_budget_report.py` | Aggregate reporter CLI |
| `ci/scripts/agent_invocation_middleware.py` | Post-call hook |
| `tests/ci/test_context_budget_tracking.py` | Behavioral tests |
| `project_board/checkpoints/M902-21/CONTEXT_BUDGET_METRICS.md` | Interpretation guide |
| `.claude/skills/autopilot/SKILL.md` | Appendix subsection |

**Unchanged:** `ci/scripts/token_budget_analyzer.py`, `ci/scripts/audit_log.py`.

---

## Spec Exit Gate

Before TEST_DESIGN:

```bash
python ci/scripts/spec_completeness_check.py project_board/specs/902_21_context_budget_tracking_spec.md --type generic
```

Expected: exit `0` (generic type has no extra required sections).

---

*End of specification.*
