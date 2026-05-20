# Execution Plan: M902-21 Context Budget Tracking

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/21_context_budget_tracking.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-21/2026-05-20T-planning-run.md`

---

## Executive Summary

**Objective:** Instrument every agent/stage invocation to capture actual (or best-effort estimated) LLM token usage, persist per-ticket artifacts under `project_board/checkpoints/<ticket_id>/token_usage.json`, aggregate cross-run metrics (totals, averages by ticket type, top consumers, context-efficiency ratios, outliers), and print an autopilot end-of-run summary.

**Scope:**
- New Python module(s) under `ci/scripts/` for record → merge → report (distinct from forecast-only `token_budget_analyzer.py`)
- Hook at agent invocation boundary (`ci/scripts/agent_invocation_middleware.py` and/or orchestrator wrapper around `framework_invocation_fn`)
- JSON schema for per-stage records + run-level rollup fields matching ticket example
- CLI/report subcommand for milestone-wide or run-root aggregation
- Autopilot skill appendix: when to write `token_usage.json`, when to print summary
- Agent-facing doc: how to interpret metrics and optimization targets (table in ticket)

**Prerequisites:** M902-01 COMPLETE (`02_complete/01_validation_gate_framework.md`). M902-18a COMPLETE (`agent_invocation_middleware.py`). M902-18 layer BLOCKED — tool-category A/B metrics are **optional** (nullable `tool_category_state`), not gating.

**Estimated Effort:** 6–9 agent runs (spec → tests → implementation recorder → implementation reporter → autopilot/docs → integration runs → AC gatekeeper)

---

## Repo Discovery (Planning Evidence)

| Asset | Path | Relevance |
|-------|------|-----------|
| Agent invocation middleware | `ci/scripts/agent_invocation_middleware.py` | Primary integration seam: `invoke_agent_with_category_filtering(agent_type, prompt, all_tools, framework_invocation_fn, **kwargs)` |
| Tool category manager | `ci/scripts/tool_category_manager.py` | Supplies filtered tool list → `schema_size_tokens` input |
| Token budget **forecast** (not actuals) | `ci/scripts/token_budget_analyzer.py` | Reuse ticket-type/complexity heuristics for `ticket_type` label only; do not conflate with usage recorder |
| Gate audit events | `ci/scripts/audit_log.py` | Orthogonal (gate lifecycle); no LLM usage today |
| Override audit artifact | `ci/scripts/gates/override_audit_log.json` | Pattern for JSON artifacts under `ci/`; M902-21 target dir is `project_board/checkpoints/` per AC |
| External Agent SDK | **Not vendored in repo** | Middleware delegates to `framework_invocation_fn`; spec must define `UsageMetadata` adapter contract when SDK returns usage, else estimation fallback |

**Gap:** No existing `token_usage.json` writer or post-run aggregator in codebase (grep confirms ticket example is aspirational).

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: schemas, hooks, reporting, autopilot contract** | Spec Agent | Ticket AC + example JSON; middleware source; `token_budget_analyzer.py` heuristics; checkpoint protocol paths; M902-18a middleware behavior | `project_board/specs/902_21_context_budget_tracking_spec.md` with: (a) `token_usage.json` JSON Schema (per-ticket file, per-stage objects, timestamps, idempotent merge rules), (b) required fields: `input_tokens`, `output_tokens`, `total_tokens`, `schema_size_tokens`, `context_efficiency` (= defined formula), (c) `UsageMetadata` extraction contract from `framework_invocation_fn` return value + fail-closed estimation path when missing, (d) `schema_size_tokens` measurement (serialized filtered tools JSON byte/char heuristic or tokenizer — pick one, document error bounds), (e) stage/agent normalization table (`spec`, `test-designer`, `implementation`, …), (f) ticket-type taxonomy (`feature`, `bugfix`, `refactor`, `generic`) and inference rules from ticket path/content, (g) optional `tool_category_state` (`category`, `tools_before`, `tools_after`, `categorization_active: bool`) when M902-18 layer unavailable → `categorization_active: false`, (h) reporter CLI: inputs (checkpoints root, optional milestone filter), outputs (totals per agent, avg per ticket type, top 10 consumers, efficiency stats, outliers >2× median by type), (i) autopilot end-of-run summary format (stdout sections + optional `token_summary.json` under run checkpoint dir), (j) dedup/idempotency: one measurement per `(ticket_id, stage, agent_run_id)` — no double-count on retries, (k) documentation section: metric definitions matching ticket table + optimization targets. Run `python ci/scripts/spec_completeness_check.py project_board/specs/902_21_context_budget_tracking_spec.md --type generic` before TEST_DESIGN. | None | Spec exit gate PASS; every AC bullet mapped to a spec section; formulas unambiguous. | **A1:** Agent SDK usage fields unknown — spec defines adapter + estimation with `confidence: estimated|exact`. **A2:** M902-18 blocked — A/B token comparison is best-effort optional, not blocking AC. |
| **2** | **Test design: recorder, merge, reporter (behavioral)** | Test Designer | Spec (Task 1); `tests/ci/test_agent_invocation_middleware.py` patterns | `tests/ci/test_context_budget_tracking.py` (stable name): (1) record stage appends/merges `token_usage.json` without clobbering prior stages, (2) idempotent re-record same `agent_run_id` replaces not duplicates, (3) `context_efficiency` matches spec formula, (4) missing usage metadata triggers estimation path with flagged confidence, (5) reporter totals per agent across two fixture tickets, (6) avg-by-ticket-type with mixed fixtures, (7) top-10 ordering deterministic, (8) outlier detection flags ticket >2× median for its type, (9) vacuous reporter on empty checkpoints dir → empty report not crash. Module docstring traces M902-21 / spec path. `unittest.mock` for framework return payloads. | Task 1 | Tests red before Task 4; no markdown/ticket prose assertions. | Fixture paths under `tmp_path` only. |
| **3** | **Test break: adversarial merge/report edge cases** | Test Breaker | Tests (Task 2), spec | Expanded cases: corrupt JSON partial file, negative token fields rejected, huge stage list, duplicate stage keys, clock skew timestamps, unknown agent_type bucketed to `unknown`, zero `schema_size_tokens` (efficiency divide-by-zero policy), concurrent write simulation (last-write-wins per spec), reporter with 11 tickets for top-10 tie-break. 4 consecutive pytest runs zero flakes. | Task 2 | +10 adversarial cases; determinism documented. | |
| **4** | **Implementation: usage recorder + middleware hook** | Implementation Agent (Generalist) | Spec; tests (Tasks 2–3) | `ci/scripts/context_budget_tracker.py` (name per spec): functions to `record_stage_usage(ticket_id, stage, agent_type, usage_metadata, tools, **ctx) -> None`, merge into `project_board/checkpoints/<ticket_id>/token_usage.json`; wire into `invoke_agent_with_category_filtering` post-call (capture tools passed + framework result metadata). TypedDict/Pydantic per project Python rules. All Task 3 tests for recorder PASS. | Tasks 1–3 | Single ticket file accumulates stages; timestamps ISO-8601; optional tool category fields populated when middleware filtered. | **R1:** Framework mock in tests — production orchestrator must pass real metadata when available. **R2:** Do not break middleware backward compat when tracker disabled via env flag (spec should define `CONTEXT_BUDGET_TRACKING=0` opt-out). |
| **5** | **Implementation: aggregate reporter CLI** | Implementation Agent (Generalist) | Spec; Task 4 artifacts | `ci/scripts/context_budget_report.py` (or subcommand on tracker module): scan `project_board/checkpoints/**/token_usage.json`, emit JSON report matching spec sections (totals, averages, top 10, efficiency, outliers). CLI: `--checkpoints-root`, `--json`, `--milestone`. Tests from Task 2–3 for reporter PASS. | Task 4 | Sample fixture run produces stable JSON golden or structural assertions; exit 0 on success. | Cross-ticket IO — path confinement tests required (no `..` escape). |
| **6** | **Autopilot + orchestrator integration** | Implementation Agent (Generalist) | Spec § autopilot; `.claude/skills/autopilot/SKILL.md` | (a) Autopilot skill update: after ticket COMPLETE/BLOCKED, invoke reporter for run scope + print human-readable summary (total tokens, top stages, outlier tickets if any); (b) document orchestrator call site if outside skill (e.g. shell wrapper under `ci/scripts/`). Ensure checkpoint index run header can reference `token_summary` path. | Tasks 4–5 | Manual/automated dry-run: single ticket autopilot leaves `token_usage.json` + summary lines in scoped checkpoint log. | Autopilot skill is markdown — test via doc contract test or integration script per spec. |
| **7** | **Documentation: interpretation guide** | Spec Agent or Integration | Spec metrics table; reporter output | `project_board/checkpoints/M902-21/CONTEXT_BUDGET_METRICS.md` or section in spec appendix linked from ticket: how to read efficiency ratios, when to optimize schema vs prompt, tool categorization impact readout, baseline establishment workflow. | Task 1 | Human can act on metrics without reading Python. | |
| **8** | **Integration validation: 3+ autopilot runs** | Integration / Autopilot Orchestrator | Tasks 4–6 deployed; 3 distinct tickets (mix types if possible) | Evidence in `project_board/checkpoints/M902-21/` integration log: 3 run ids, each with `token_usage.json`, aggregated report output pasted (summary only), confirmation summary printed at end of run. Update ticket Validation Status → Integration: Passing with log pointers. | Tasks 4–7 | AC "Tested with 3+ autopilot runs" satisfied with artifact paths. | **R3:** Long-running — may run lean autopilot on small backlog tickets. Failures logged verbatim per workflow. |
| **9** | **Static QA** | python-reviewer / Code Reviewer | Tasks 4–6 Python | Ruff-clean; typed public APIs; no bare `except`; path safety reviewed. | Tasks 4–6 | No blocking findings. | |
| **10** | **AC gatekeeper** | AC Gatekeeper | All outputs; ticket AC | Per-AC evidence matrix; targeted pytest; reporter smoke; git clean + push before COMPLETE; `git mv` ticket to `02_complete/`. | Tasks 1–9 | All AC checkboxes evidenced; M902-17 umbrella item for M902-21 can be checked when parent re-run. | COMPLETE blocked without push. |

---

## Dependency Matrix

| Dependency | Folder / State | Blocks M902-21 core? | Notes |
|------------|----------------|----------------------|-------|
| M902-01 Validation Gate Framework | `02_complete/` | No (satisfied) | Gate envelope patterns only |
| M902-18a Framework Integration | `02_complete/` | No (satisfied) | Middleware hook ready |
| M902-18 Tool Categorization Layer | `03_blocked/` | **No** | Optional `tool_category_state` / A/B metrics deferred |
| Agent SDK (external) | N/A in repo | Soft | Estimation fallback required in spec |
| `token_budget_analyzer.py` | `ci/scripts/` | No | Forecast-only; optional cross-link in docs |

**Umbrella:** No.

---

## Acceptance Criteria Traceability (Planning)

| AC | Task owner |
|----|------------|
| Instrument all agent calls (in/out/total tokens) | 1, 4 |
| Per-agent metrics | 1, 4, 5 |
| Per-stage metrics + context efficiency | 1, 4 |
| Log `project_board/checkpoints/<ticket_id>/token_usage.json` | 1, 4 |
| Report: totals, avg by type, top 10, efficiency, outliers | 1, 5 |
| Autopilot end-of-run summary | 1, 6 |
| 3+ autopilot runs with data | 8 |
| Documentation interpret metrics | 1, 7 |
| Tool categorization effectiveness (M902-18) | 1, 4 (optional fields) |

---

## Notes

- **Separation of concerns:** `token_budget_analyzer.py` remains pre-flight **forecast**; new modules record **actuals** post-invocation. Spec must state both commands in runbook.
- **Hook placement:** Prefer post-`framework_invocation_fn` in middleware so filtered `tools_to_use` is available for `schema_size_tokens`; pass `agent_type` as stage key unless spec defines separate `workflow_stage` from orchestrator.
- **Checkpoint protocol:** Ambiguity resolutions belong in scoped log `project_board/checkpoints/M902-21/2026-05-20T-planning-run.md`, not `CHECKPOINTS.md` bodies.
- **M902-17:** Parent validation ticket lists M902-21 as integration evidence — complete M902-21 before M902-17 re-gate.
- **Test filenames:** No ticket id in test module name (`test_context_budget_tracking.py`).

---

## Next Steps

**Immediate:** Spec Agent — author `902_21_context_budget_tracking_spec.md` and pass `spec_completeness_check.py --type generic`.

**Unblocks:** Data-driven optimization of tool categorization (M902-18 when unblocked), milestone retrospectives, M902-17 final validation evidence.
