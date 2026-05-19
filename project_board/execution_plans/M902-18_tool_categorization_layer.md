# M902-18: Tool Categorization Layer — Execution Plan

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md`

**Planner Agent Run:** 2026-05-18  
**Status:** READY FOR SPECIFICATION

---

## Executive Summary

Implement a tool categorization system that filters agent tool schemas by workflow stage (parse/modify/test/plan/think) to reduce context overhead by 15–25%. The feature integrates with Claude Agent SDK's tool filtering mechanism and requires configuration, function implementation, measurement instrumentation, and multi-agent integration testing.

**Key Constraints:**
- Scope: Tool schema reduction only; no agent logic changes
- Dependencies: M902-01 (Validation Gate Framework) COMPLETE ✓; SDK tool filtering API must exist
- Design decisions: 5 categories, JSON config, function interface, agent opt-in declaration
- Testing: 3+ agent integration tests across milestone; token savings measurement

---

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | **SPECIFICATION: Freeze tool-to-category mappings and SDK integration contract** | Spec Agent | Ticket M902-18; checkpoint M902-18/2026-05-18T-planner.md; gate_runner.py (reference); gate_registry.json (reference) | Spec file: `project_board/specs/902_18_tool_categorization_spec.md` with: (a) tool-to-category mapping table (parse/modify/test/plan/think) with rationale, (b) SDK API surface contract (function signature, filtering mechanism, error handling), (c) `ci/scripts/tool_categories.json` schema, (d) agent declaration interface (input prompt syntax), (e) token measurement protocol and baseline collection procedure, (f) AC coverage matrix linking all 8 acceptance criteria to spec sections | None (gate M902-01 already complete) | (1) Spec exists and is well-formed; (2) All 8 AC mapped to spec sections; (3) SDK API surface explicitly defined (native vs. custom middleware); (4) tool_categories.json schema is finalized and validated; (5) Token measurement method is testable and repeatable; (6) No ambiguities remain on tool filtering boundaries | **CRITICAL ASSUMPTION:** SDK tool filtering API exists and is invocable from agent framework. **MEDIUM confidence.** If SDK API is unavailable, escalate and propose custom middleware approach. **MEDIUM-risk:** Tool-to-category boundaries may create false negatives (parse mode blocking needed tool). **MEDIUM:** Token measurement may require custom instrumentation if SDK lacks granular reporting. Spec Agent must clarify all three in coordination with agent framework team. |
| 2 | **TEST_DESIGN: Author comprehensive test suite for tool categorization** | Test Designer Agent | Spec file (from Task 1); gate_runner.py; existing test suite patterns (tests/ci/*.py) | Test design doc: `project_board/test_designs/902_18_tool_categorization_test_design.md` with: (a) 30–40 primary behavioral tests covering: category enum definition (5 tests), tool mapping validation (8 tests), get_tools_for_category() function (7 tests), agent declaration parsing (5 tests), token measurement protocol (5 tests), edge cases (5 tests); (b) Traceability matrix linking each test to AC; (c) Test file naming (deterministic, behavior-descriptive, no ticket ID); (d) Mock/fixture strategy for agent SDK tool schema (tool definition stubs); (e) Determinism notes (no randomness, repeatable outputs); (f) Recommended test framework and command | Spec from Task 1 | (1) Test design covers all 8 ACs; (2) 30+ primary tests identified with clear names; (3) No prose assertions (behavior-only, testable); (4) Test naming follows project conventions (test_<package>_<concern>.gd/py); (5) Mock strategy documented for SDK tool objects; (6) Traceability matrix is complete | **MEDIUM:** Agent declaration parsing tests must cover edge cases (invalid category, missing declaration, conflicting declarations). Spec will define valid syntax. **MEDIUM:** Tool schema mock objects must represent actual SDK types; Test Designer may need to inspect gate_runner.py to infer types. **MEDIUM:** Token measurement protocol may require custom instrumentation hooks; test harness must inject or mock this. |
| 3 | **TEST_BREAK: Extend test suite with adversarial and boundary tests** | Test Breaker Agent | Test design (from Task 2); spec (from Task 1) | Extended test suite: `tests/ci/test_tool_categorization_adversarial.py` (25–30 adversarial tests) covering: (a) boundary conditions: empty tool lists, missing categories, duplicate tools across categories, 0–100 tools per category; (b) malformed inputs: invalid JSON in tool_categories.json, invalid category names, null/undefined tool objects; (c) interface conflicts: same tool in multiple categories (if collision detection required), tool name collisions; (d) token measurement edge cases: schema size 0 bytes, very large schema (10k+ tools), schema format mutations; (e) agent declaration mutations: whitespace variants, case sensitivity, invalid category names, multiple declarations in single prompt; (f) SDK API error paths: filtering API not available, SDK version mismatch, tool schema unavailable | Test design from Task 2 | (1) 25–30 adversarial tests added; (2) All boundary conditions covered; (3) All tests deterministic and repeatable; (4) No prose assertions; (5) Tests encode conservative assumptions (e.g., tool filtering fails closed if SDK unavailable); (6) Test file named test_tool_categorization_adversarial.py (no ticket ID); (7) Vulnerability coverage matrix provided (10+ edge cases × 2–3 test variants each) | **MEDIUM:** Malformed input handling depends on Spec definition of error semantics. Test Breaker must encode conservative assumption: invalid JSON → structured error, not silent skip. **MEDIUM:** Token measurement edge cases may be difficult to inject without custom instrumentation. Fallback: mock the measurement function. **HIGH:** Tool collision detection (if category-crossing tools exist) must be explicitly tested. Spec must define policy. |
| 4 | **IMPLEMENTATION_BACKEND: Implement tool categorization layer** | Implementation Agent (Backend) | Spec (Task 1); test suite (Tasks 2–3); gate_runner.py (reference); gate_registry.json (reference) | Deliverables: (1) `ci/scripts/tool_categories.json` — configuration file with category-to-tools mapping (per spec schema); (2) `ci/scripts/tool_category_manager.py` (or equiv) — module implementing `get_tools_for_category(category: str) -> list[Tool]` function, category validation, error handling; (3) SDK integration layer — if custom middleware required, implementation of tool filtering hook (or coordination patch to agent framework); (4) `ci/scripts/agent_tool_filter.py` (or equiv) — optional middleware for agent invocation with category parameter; (5) Token measurement instrumentation — function to measure baseline (all tools) and filtered (category) schema sizes, with logging/reporting; (6) Documentation — docstrings, usage examples, error handling guide; (7) All code follows project style (CLAUDE.md) and passes Ruff linter | Spec + test suite | (1) tool_categories.json is valid JSON and matches spec schema; (2) get_tools_for_category() function is callable and returns list[Tool]; (3) All 8 ACs have corresponding implementation; (4) Token measurement is repeatable and logged in structured format; (5) Error paths handle invalid categories, missing config, SDK unavailability gracefully; (6) Code passes Ruff checks; (7) All code is covered by tests from Tasks 2–3 (100% new code, 100% path coverage for happy path + error paths) | **CRITICAL:** SDK tool filtering API must be available and invocable. If API does not exist, implementation is blocked; escalate. **MEDIUM:** Tool collision detection logic (if required) must be fail-closed: unknown collisions → WARN, not SKIP. **MEDIUM:** Token measurement may require instrumentation of agent SDK internals; may need coordination or custom measurement proxy. Implementation Agent should verify measurability in Task 1 (Spec) output before beginning implementation. |
| 5 | **IMPLEMENTATION_BACKEND: Integrate tool categorization into agent framework** | Implementation Agent (Backend) | Spec (Task 1); implementation from Task 4; agent framework code (requires locating) | Deliverables: (1) Agent framework integration — modify agent invocation to accept optional `tool_category` parameter (per spec contract); (2) If custom middleware, wire middleware into pre-agent-call hook (or equivalent); (3) Agent input schema update — if needed, document required `tool_category` declaration format for agents; (4) Gate registration — register tool_categorization as a gate in gate_registry.json (or if not a gate, document architectural position); (5) Testing — run full test suite (Tasks 2–3) against integrated framework, verify no regressions in existing agent calls; (6) Backward compatibility — agents that do not declare category should receive all tools (default behavior, no breaking changes) | Implementation from Task 4; spec from Task 1 | (1) Agent framework accepts tool_category parameter (or equivalent per spec); (2) Backward compatibility verified: old agent code without tool_category still works; (3) All tests from Tasks 2–3 pass against integrated framework; (4) Token measurements are collected and logged in checkpoint logs; (5) Integration verified with mock or stub agent calls; (6) No regressions in existing gate infrastructure (gate_runner.py still works) | **CRITICAL:** Agent framework location/structure unknown; requires codebase exploration. Implementation Agent must first locate agent invocation code, understand current tool-passing mechanism, and determine integration point. **HIGH-risk:** Integration may require coordination outside of this ticket (agent framework team). If framework is external or versioned separately, create explicit coordination issue. **MEDIUM:** Backward compatibility testing must cover all existing agent types (Planner, Spec, Test Designer, Test Breaker, Implementation, Reviewer, Acceptance, Learning). Use existing test suite as regression baseline. |
| 6 | **STATIC_QA: Lint and code review** | Static QA Agent | Implementation from Tasks 4–5; spec from Task 1; test suite from Tasks 2–3 | Deliverables: (1) Ruff checks pass: E9, F, I rules (per CLAUDE.md); (2) Type annotations present for all functions: `get_tools_for_category(category: str) -> list[Tool]`, category validation, error returns; (3) Code review findings — if any, route back to Implementation Agent with specific recommendations; (4) Documentation review — docstrings are clear, examples are correct, usage guide is complete; (5) Test coverage validation — verify all new code is exercised by test suite (Tasks 2–3) | Implementation + tests from Tasks 4–5 | (1) Ruff clean (zero violations); (2) All functions have type hints; (3) No bare `dict` types (use dict[str, T] or TypedDict); (4) Error handling is explicit (no silent catches); (5) Documentation is present and accurate; (6) Code follows CLAUDE.md naming (snake_case for functions, UPPERCASE for constants); (7) No new TODOs without issue links (per reviewer_check gate) | **MEDIUM:** Type annotations may be complex for `list[Tool]` if Tool is a complex SDK type. Static QA must verify Tool type can be imported and used consistently. **MEDIUM:** Test coverage requirements are strict; Implementation Agent must ensure 100% coverage for happy path + all error paths. Use pytest --cov or equiv to verify. |
| 7 | **INTEGRATION: Verify 3+ agent use of tool categorization** | Integration Agent | Implementation from Tasks 4–5; checkpoint logs from Planner/Spec/Test Designer runs | Deliverables: (1) Integration test harness — script or test that simulates 3+ different agent runs (e.g., Spec Agent in parse mode, Implementation Agent in modify mode, Test Designer in test mode) and verifies each receives correct tool subset; (2) Checkpoint logs — three agent runs (or more) include tool_category declaration and token measurement in decision logs; (3) Token savings report — baseline (all tools) vs. filtered measurements for each category, 15–25% reduction verified; (4) Measurement protocol validation — verify token measurement is repeatable and matches spec protocol; (5) Documentation — update agent runbook (project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md or equiv) with "When/How to Declare Category" section | Implementation + tests + spec from prior tasks; checkpoint logs from M902 agent runs | (1) 3+ agent runs successfully use tool_category parameter; (2) Each run declares category and receives corresponding tool subset; (3) Token baseline and filtered measurements are collected and logged; (4) Token reduction 15–25% verified (or documented if baseline differs); (5) No regressions in existing agent workflow; (6) Runbook updated with clear examples; (7) All measurements are reproducible and within ±10% margin of first measurement | **HIGH-risk:** Token measurement baseline may vary by SDK version or model; cannot guarantee 15–25% reduction without controlling all variables. Spec (Task 1) must define baseline collection procedure; Integration Agent must follow strictly. **MEDIUM:** 3-agent integration may require coordinating across other ticket runs in M902 backlog; may need to defer or rely on parallel ticket execution. If parallel tickets exist, incorporate tool_category declarations in their test design (Tasks 2–3 from dependent tickets). **MEDIUM:** Runbook updates may conflict with M902-08 runbook updates (workflow visualization). Coordinate with M902-08 implementation or Planner to merge. |
| 8 | **ACCEPTANCE_CRITERIA_GATEKEEPER: Verify all 8 ACs satisfied** | Acceptance Criteria Gatekeeper Agent | Spec (Task 1); implementation + tests + integration (Tasks 4–7); checkpoint logs from all stages | Deliverables: (1) AC checklist with evidence — all 8 ACs (from ticket lines 12–19) mapped to implementation, test, or integration evidence; (2) Evidence package: code file paths, test names, checkpoint measurements, documentation links; (3) Gatekeeper report — structured validation of each AC with pass/fail/conditional status; (4) Risk review — any remaining gaps or assumptions documented; (5) Stage advancement approval — recommend Stage → COMPLETE if all ACs satisfied, or route back to agent if gaps exist | Implementation + tests + integration deliverables; spec; checkpoint logs | (1) All 8 ACs have explicit evidence (code, tests, or measurements); (2) Each AC is traceable to deliverable; (3) No prose-only assertions (all evidence is executable or measurable); (4) Token savings measurement is verified and logged; (5) 3+ agent integration verified; (6) No blocking issues remain | **MEDIUM:** AC6 (tool schema reduction 15–25%) may be difficult to verify if baseline is not precisely controlled. Gatekeeper must validate measurement protocol was followed (per Spec from Task 1). If measurement cannot be validated, escalate as conditional PASS (measurement attempted, results logged, may require follow-up in future ticket). **MEDIUM:** AC7 (3+ agent integration) may depend on other M902 tickets; if parallel tickets exist, gatekeeper must verify their checkpoint logs include tool_category declarations. |

---

## Design Decisions Frozen

| # | Decision | Rationale | Owner | Open Questions |
|---|----------|-----------|-------|-----------------|
| 1 | Five categories: `parse`, `modify`, `test`, `plan`, `think` | Align with agent workflow stages (specification notes these correspond to agent responsibilities). Simplify filtering without over-granularity. | Spec Agent | None (defined in ticket) |
| 2 | Config file: `ci/scripts/tool_categories.json` | Centralize tool-to-category mapping in single file; integrates with existing gate infrastructure; allows dynamic reloading without code changes. | Spec Agent | Schema design (Task 1) must be finalized |
| 3 | Function interface: `get_tools_for_category(category: str) -> list[Tool]` | Simple, type-safe, aligns with gate_runner.py patterns; allows SDK filtering by category. | Spec Agent | SDK Tool type must be clarified; may need to adjust signature if Tool is complex type. |
| 4 | Agent opt-in declaration in input prompt | Agents declare category (e.g., "I'm in parse mode, give me read-only tools") rather than implicit agent-type detection; allows flexibility and agent awareness. | Spec Agent | Exact syntax and validation rules to be defined in Task 1 |
| 5 | Token measurement: baseline vs. filtered schema size | Quantify context reduction by comparing all-tools schema size vs. category-filtered schema size; log results in checkpoint logs. | Spec Agent | Measurement method (byte count, token count, custom instrumentation) to be finalized in Task 1 |
| 6 | Backward compatibility: agents without category declaration receive all tools | Ensure existing agent code continues to work without modification; category filtering is opt-in, not breaking change. | Implementation Agent (Task 4) | Default behavior clear in spec; no ambiguity |
| 7 | Measurement collection during agent integration testing | Baseline + category-filtered measurements collected in live agent runs (Tasks 2–3 per M902 checkpoint protocol); ensures realistic token counts. | Integration Agent (Task 7) | Measurement instrumentation location (in get_tools_for_category or elsewhere) to be defined in Task 1 |
| 8 | Scope: tool schema reduction only; no agent logic changes | Feature is transparent to agent decision-making; agents see same API, fewer tools available. Reduces context overhead without semantic changes. | Planner (entire plan) | Confirmed in ticket overview |

---

## Clarifying Questions & Assumptions

| # | Question | Status | Assumption | Confidence | Resolution Owner |
|---|----------|--------|-----------|-----------|------------------|
| 1 | Does Claude Agent SDK expose native tool filtering API? | BLOCKING | SDK supports tool filtering (native or custom middleware); if not, custom middleware will be built. | MEDIUM | Spec Agent (Task 1) must coordinate with SDK team and confirm API surface. If unavailable, escalate and propose custom middleware approach. |
| 2 | Are example tool-to-category mappings (parse/modify/test/plan/think) normative or heuristic? | OPEN | Example table is normative; Spec Agent will freeze exact mappings with rationale. | MEDIUM-HIGH | Spec Agent (Task 1) must finalize mappings and explain tool selection per category. |
| 3 | What metric measures token savings: byte count, token count, or other? | OPEN | Token measurement via schema JSON byte count as proxy; may require custom instrumentation. | MEDIUM | Spec Agent (Task 1) must define measurement method and baseline collection procedure. |
| 4 | Does AC7 (3+ agent integration) require all three agents in single ticket or across milestone? | OPEN | Integration testing across 3+ tickets in M902 backlog, not all in M902-18. Agents in later tickets (Spec, Test, Implementation) declare categories during their runs. | MEDIUM-HIGH | Test Designer (Task 2) will clarify scope; Integration Agent (Task 7) will verify coverage across milestone runs. |
| 5 | Where is agent framework code that invokes tools? | BLOCKING | Agent framework is internal to Claude Agent SDK or agent orchestrator; location TBD. | MEDIUM | Implementation Agent (Task 5) must locate framework code, understand current tool-passing mechanism, and determine integration point. May require coordination outside this ticket. |
| 6 | How should tool collisions (same tool in multiple categories) be handled? | OPEN | Spec will define policy: error, warning, or allowed (with priority). Assume fail-closed: collision → WARN, not silent skip. | MEDIUM | Spec Agent (Task 1) must define semantics; Test Breaker (Task 3) will test boundary case. |
| 7 | Is tool categorization a gate (registered in gate_registry.json) or infrastructure? | OPEN | Feature is infrastructure (not a gate); provides tool filtering for agents. May be invoked by agent framework before agent execution, not as a discrete gate step. | MEDIUM-HIGH | Implementation Agent (Task 5) will clarify architectural position after SDK integration. |
| 8 | What is the target baseline for token reduction: all existing agents or subset? | OPEN | Baseline = current all-tools schema size for representative agent SDK version; measured against each category's filtered schema size. Spec will define baseline collection method. | MEDIUM | Spec Agent (Task 1) must define baseline procedure; Integration Agent (Task 7) will execute and log measurements. |

---

## Gating & Dependencies

### Hard Blockers
None. M902-01 (Validation Gate Framework) is COMPLETE.

### Soft Dependencies
- **M902-17 (Final Validation & Stage Integration):** AC requires "15–25% context reduction verified" (M902-18 is this feature). M902-18 completion unblocks M902-17 AC6 validation.
- **M902-19 through M902-23 (later context optimization tickets):** May benefit from or depend on tool categorization foundation. Not explicitly listed in dependencies.

### Gating from M902-18
- **Spec completeness gate (before Task 3):** Spec file from Task 1 must pass `python ci/scripts/gate_runner.py spec_completeness_check --spec_file <spec> --ticket_type generic` before TEST_DESIGN begins (per workflow_enforcement_v1.md).
- **No other gates block Tasks 1–2.**

---

## Risk Matrix & Mitigation

| Risk | Likelihood | Severity | Impact | Mitigation | Owner |
|------|-----------|----------|--------|-----------|-------|
| SDK tool filtering API unavailable or incompatible | Medium | High | Feature cannot be implemented; requires redesign or external coordination | Spec Agent (Task 1) confirms API surface in coordination with SDK team; if unavailable, escalate and propose custom middleware. Propose alternate architecture in spec if needed. | Spec Agent |
| Tool-to-category mappings create false negatives (parse mode blocks needed Bash tool) | Medium | Medium | Agents cannot complete tasks; workaround is declaring different category (reduces context benefit) | Test Breaker (Task 3) creates adversarial tests for boundary cases. Spec (Task 1) defines fallback policy: if category too restrictive, agent declares broader category. | Test Breaker Agent |
| Token measurement baseline not reproducible or differs across SDK versions | Low | Medium | Cannot verify 15–25% reduction target; may affect AC6 acceptance | Spec (Task 1) defines baseline collection procedure and documents SDK version dependency. Gatekeeper (Task 8) validates measurements follow procedure. Accept conditional PASS if measurement attempted but baseline varies. | Spec Agent + Gatekeeper |
| Integration testing deferred too late; insufficient time to collect 3-agent measurements | Medium | Medium | AC7 (3+ agent integration) may be incomplete; possibly deferred to M903 | Assign Spec/Test Designer agents (early in milestone) to declare tool_category in their runs; collect measurements early. Integration Agent (Task 7) verifies coverage. If incomplete, document in checkpoint and escalate to Planner for M903 follow-up. | Integration Agent |
| Agent framework changes required outside this ticket scope | Medium | High | Integration (Task 5) may require external coordination or blocking other work | Implementation Agent (Task 5) explores agent framework code early. If custom middleware needed, prototype in Task 4 before integration. Document external dependencies in checkpoint. Escalate to Planner if blocked. | Implementation Agent |
| Tool collision detection logic adds complexity; behavior undefined | Low | Low | Edge case; may not affect most use cases | Spec (Task 1) defines policy upfront: error, warn, or allow. Test Breaker (Task 3) tests chosen policy. | Spec Agent + Test Breaker |
| Runbook updates (AC8) conflict with M902-08 documentation work | Low | Low | Documentation inconsistency; requires coordination | Integration Agent (Task 7) checks M902-08 status before updating runbook. If M902-08 is in progress, merge updates or defer to M902-08 completion. Coordinate via Planner. | Integration Agent |

---

## Success Metrics

| Criterion | Definition | Evidence |
|-----------|-----------|----------|
| **Design frozen (Tasks 1–2)** | Spec complete; 8 ACs mapped to implementation; tool-to-category mappings finalized; SDK API confirmed | Spec file exists; checkpoint decision log (Task 1) documents all clarifications |
| **Code complete (Tasks 4–5)** | tool_categories.json, get_tools_for_category(), SDK integration, token measurement all implemented and tested | Implementation files committed; 100% test coverage; Ruff clean |
| **Tests comprehensive (Tasks 2–3)** | 30+ primary + 25+ adversarial tests; all ACs covered; no prose assertions; all tests pass | Test suite runs; test design and test breaker checkpoint logs document coverage matrix |
| **Integration verified (Task 7)** | 3+ agent runs declare tool_category; token measurements collected; 15–25% reduction verified; runbook updated | Integration test harness runs; checkpoint logs from 3+ agent runs include measurements; runbook section added |
| **ACs satisfied (Task 8)** | All 8 ACs from ticket have explicit evidence (code, test, or measurement) | Gatekeeper report with AC checklist; no gaps |
| **Quality gates passed** | Ruff clean; no unaddressed TODOs; code review findings resolved | Static QA report (Task 6) clear; no blocking findings |

---

## Sequencing & Handoff

```
Task 1 (Spec Agent) — SPECIFICATION stage
   ↓ (advances when: spec complete, ACs mapped, no ambiguities)
Task 2 (Test Designer) — TEST_DESIGN stage
   ↓ (advances when: test design complete, traceability matrix done)
Task 3 (Test Breaker) — TEST_BREAK stage
   ↓ (advances when: adversarial suite added, all tests documented)
Tasks 4–5 (Implementation) — IMPLEMENTATION_BACKEND stage
   ↓ (advances when: code complete, all tests pass, no TODOs)
Task 6 (Static QA) — STATIC_QA stage
   ↓ (advances when: Ruff clean, code review passed)
Task 7 (Integration) — INTEGRATION stage
   ↓ (advances when: 3+ agents verified, measurements logged, runbook updated)
Task 8 (Acceptance Gatekeeper) — AC VALIDATION
   ↓ (final checkpoint; all ACs verified or escalated)
Stage → COMPLETE
```

---

## Estimated Effort & Timeline

| Task | Stage | Estimated Effort | Duration | Owner |
|------|-------|-----------------|----------|-------|
| 1 | SPECIFICATION | 4–6 hrs (coord w/ SDK, freeze design) | 1 day | Spec Agent |
| 2 | TEST_DESIGN | 6–8 hrs (test harness, fixtures, traceability) | 1 day | Test Designer |
| 3 | TEST_BREAK | 4–6 hrs (adversarial suite, edge cases) | 1 day | Test Breaker |
| 4–5 | IMPLEMENTATION | 8–12 hrs (config, functions, SDK integration, backward compat) | 2 days | Implementation Agent |
| 6 | STATIC_QA | 2–3 hrs (lint, type checks, code review) | 0.5 day | Static QA Agent |
| 7 | INTEGRATION | 4–6 hrs (harness, 3+ agent runs, measurements, runbook) | 1 day | Integration Agent |
| 8 | AC VALIDATION | 2–3 hrs (checklist, evidence mapping, gatekeeper report) | 0.5 day | Acceptance Gatekeeper |
| **Total** | — | **30–44 hrs** | **~1 week** | — |

**Target completion:** 2026-05-25 (1 week from start of SPECIFICATION)

---

## Notes

- **Checkpoint protocol:** All ambiguities logged in `project_board/checkpoints/M902-18/2026-05-18T-planner.md` and task-specific checkpoints per agent run (Tasks 1–8).
- **Test naming:** All test files must follow behavior-descriptive naming (e.g., `test_tool_categorization.py`, `test_tool_categorization_adversarial.py`); no ticket IDs or milestone numbers in filenames (per CLAUDE.md project conventions).
- **SDK coordination:** Spec Agent (Task 1) must explicitly contact SDK team if tool filtering API is unclear; do not assume availability.
- **Token measurement:** Integration Agent (Task 7) should pilot measurement protocol on 1 agent run before collecting 3-run baseline; validate repeatable results.
- **Runbook location:** M902-08 (Workflow Visualization) may have already updated the README with runbook sections. Integration Agent should check status and merge tool_category content into existing runbook section, not duplicate.

---

## Appendix: Acceptance Criteria Mapping

| AC # | Acceptance Criterion (from ticket) | Owner (Task) | Evidence Type |
|------|-----------------------------------|-------------|---------------|
| 1 | Define tool categories enum: `parse`, `modify`, `test`, `plan`, `think` | Spec (Task 1) | Code: enum or constant in tool_categories.json / tool_category_manager.py |
| 2 | Categorize all existing agent tools into one or more categories | Spec (Task 1) + Implementation (Task 4) | Code: tool_categories.json mapping all current tools; completeness verified in test |
| 3 | Implement `get_tools_for_category(category: str) -> list[Tool]` function | Implementation (Task 4) | Code: function in tool_category_manager.py; unit tests (Task 2) verify behavior |
| 4 | Agent framework passes `tool_category` parameter to each agent | Implementation (Task 5) | Code: agent invocation modified; integration test (Task 7) verifies parameter propagation |
| 5 | Agents can declare category in input prompt (e.g., "I'm in parse mode...") | Spec (Task 1) + Implementation (Task 4) | Spec: declares syntax; Implementation: parses declaration; Tests (Task 2) verify parsing |
| 6 | Tool schema reduction measured: baseline (all tools) vs. category-filtered size | Spec (Task 1) + Implementation (Task 4) + Integration (Task 7) | Code: token measurement function; Integration: collects baseline + filtered measurements; Checkpoint logs record results |
| 7 | Integration tested with 3+ agents (spec, implementation, test-designer) | Integration (Task 7) | Integration test harness; checkpoint logs from 3+ M902 agent runs including tool_category declarations |
| 8 | Documented in agent runbook: when/how to declare category | Integration (Task 7) | Documentation: section added to project_board/902_milestone_902_agent_predictabilitiy_improvements/README.md or agent runbook |

