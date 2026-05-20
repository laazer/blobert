# M902-21 Planning Run

**Run id:** `2026-05-20T-planning-run`  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md`  
**Stage:** PLANNING → SPECIFICATION  
**Planner:** Planner Agent

---

## Outcome

Planning complete. Execution plan: `project_board/execution_plans/M902-21_context_budget_tracking.md` (10 tasks). Handoff to Spec Agent.

---

### [M902-21] PLANNING — Agent SDK token source

**Would have asked:** Does the Claude Agent SDK expose `input_tokens` / `output_tokens` on every invocation return, and what are the exact field names?

**Assumption made:** Spec will define a `UsageMetadata` adapter: prefer exact fields from `framework_invocation_fn` return when present; otherwise estimate from prompt/response character counts with `confidence: "estimated"` and document ±error bounds. No hard dependency on vendored SDK in repo.

**Confidence:** Medium

---

### [M902-21] PLANNING — M902-18 blocked vs tool-category metrics

**Would have asked:** Should M902-21 block until M902-18 layer is unblocked for A/B token comparison?

**Assumption made:** Core instrumentation and reporting ship without M902-18. Optional JSON fields (`tool_category_state`, `categorization_active`) default false/null; "Tool category impact" AC satisfied as N/A until M902-18 completes, then reporter adds comparison slice without schema break.

**Confidence:** High

---

### [M902-21] PLANNING — schema_size_tokens measurement

**Would have asked:** Which tokenizer or byte heuristic should define `schema_size_tokens`?

**Assumption made:** Spec freezes one method: serialized JSON length of the tool list passed to the framework at invocation time, divided by 4 (chars-per-token heuristic), unless spec chooses tiktoken with explicit model id. `context_efficiency` = `output_tokens / max(schema_size_tokens, 1)` or ticket's ratio — spec must pick one formula and tests enforce it.

**Confidence:** Medium

---

### [M902-21] PLANNING — ticket_type for averages

**Would have asked:** How should autopilot classify tickets for "avg tokens per ticket type"?

**Assumption made:** Infer from ticket markdown sections (`## Description` keywords), milestone folder name, or autopilot input mode (description → `feature`, path containing `bugfix` → `bugfix`); default `generic`. Spec publishes normalization table.

**Confidence:** Medium

---

## Repo discovery summary

- **Hook site:** `ci/scripts/agent_invocation_middleware.py` (`invoke_agent_with_category_filtering`)
- **Forecast only:** `ci/scripts/token_budget_analyzer.py` (not usage actuals)
- **Audit:** `ci/scripts/audit_log.py` (gate events, not LLM tokens)
- **No** `token_usage.json` implementation found
- **Dependencies:** M902-01 and M902-18a in `02_complete/`; M902-18 layer in `03_blocked/` (non-gating)
