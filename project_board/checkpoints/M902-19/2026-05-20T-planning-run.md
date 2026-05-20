# M902-19 Forgiving Tool Parsing Middleware — PLANNING COMPLETE

**Date:** 2026-05-20  
**Stage:** PLANNING → SPECIFICATION  
**Revision:** 1 → 2  
**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/19_forgiving_tool_parsing_middleware.md`

---

## Context & Discovery

### Prerequisite Status
✅ **M902-18-T5 (Tool Categorization Framework Integration) is COMPLETE**
- Middleware deployed at `ci/scripts/agent_invocation_middleware.py`
- Framework wiring functional and tested (72 tests passing, zero flakes)
- Agents can declare tool categories via prompt declarations
- Tool filtering via `get_tools_for_category()` operational
- All 8 ACs satisfied per AC Gatekeeper validation

### M902-19 Scope Analysis

**Feature Objective:** Implement a "forgiving" tool parsing middleware that auto-repairs common LLM tool call mistakes before execution, preventing retry loops from parsing failures.

**Key Components:**
1. **Parser Layer** — handles JSON, YAML, XML, plain-text tool output formats
2. **Auto-repair Logic** — fixes type mismatches, missing fields, syntax errors, typos
3. **Validation Gate** — rejects dangerous mutations (security-sensitive commands)
4. **Middleware Integration** — wraps tool execution in Agent SDK
5. **Audit Trail** — logs all repair attempts with severity levels
6. **Test Coverage** — 25+ error vectors across all repair categories

**Relationship to M902-18-T5:**
- M902-18-T5 filters WHICH tools are available to agents (tool categorization)
- M902-19 improves HOW agents use tools (error recovery in tool execution)
- M902-19's repair middleware executes AFTER tool invocation (orthogonal concern)
- No direct dependency: M902-19 can proceed independently of M902-18-T5 completion

### Critical Ambiguities & Assumptions

**A1: Tool Execution Integration Point (MEDIUM confidence)**
- **Question:** Where does tool execution happen in the Agent SDK?
- **Assumption:** Agent SDK exposes tool execution layer (e.g., `agent_sdk/tool_execution.py` or similar)
- **Evidence needed:** Spec Agent must locate tool execution code or documentation
- **Risk:** If Agent SDK does not expose tool execution, middleware must intercept at framework boundary (wrapping approach like M902-18-T5)

**A2: Repair Strategy Scope (MEDIUM confidence)**
- **Question:** Which error types are "salvageable" vs dangerous?
- **Assumption:** Spec defines 6-8 repair categories with clear safety boundaries
- **Risk:** Over-aggressive repair could introduce security issues; under-repair wastes opportunity
- **Confidence:** Ticket AC provides 8 concrete repair examples; scope is clear enough for Spec

**A3: Tool Schema Format for Repair (MEDIUM-HIGH confidence)**
- **Question:** What format do LLM tool calls take?
- **Assumption:** Tool calls are JSON dicts with keys like `action`, `file_path`, `replace_all`, etc. (per AC example)
- **Risk:** Actual tool call format may vary by agent framework
- **Confidence:** Ticket AC example is concrete; schema likely standardized by Agent SDK

**A4: Validation Mechanism (MEDIUM confidence)**
- **Question:** How to distinguish legitimate parameter mutations from security violations?
- **Assumption:** Validation is based on parameter name whitelisting and type constraints, not command content inspection
- **Risk:** Static whitelisting may miss genuine edge cases
- **Confidence:** Spec will define allowlist per tool category (inherited from M902-18)

**A5: Logging Severity Semantics (HIGH confidence)**
- **Question:** What distinguishes "warning" (auto-fixed) vs "error" (requires user action)?
- **Assumption:** Warning = repair succeeded + tool executed safely. Error = repair failed + tool not invoked.
- **Evidence:** Ticket AC specifies logging with severity levels
- **Confidence:** Clear from AC specification

---

## Execution Plan

### Overview

**Goal:** Decompose M902-19 into 7 sequential tasks suitable for agent execution.

**Sequence:**
1. **Specification** — Define repair logic, validation strategy, middleware integration point
2. **Test Design** — Write tests for 25+ error vectors across 6 repair categories
3. **Test Break** — Ensure determinism and adversarial coverage
4. **Implementation** — Build parser, repair logic, validation gate, audit trail
5. **Static QA** — Code review, type checking, lint validation
6. **AC Gatekeeper** — Validate all 8 acceptance criteria
7. **Documentation** — Update integration guide, runbook

**Estimated Effort:** 6-8 days (based on M902-18-T5 timeline: 4 days from planning to complete)

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: Define Repair Logic & Validation Strategy** | Spec Agent | Ticket AC, example repair cases, M902-18-T5 validation patterns, agent framework docs | Specification: `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md` with: (a) 6-8 repair categories defined (type coercion, missing fields, syntax fixes, typo correction, etc.), (b) Validation rules per category with safety constraints, (c) Tool execution integration point identified (where middleware sits), (d) Audit trail format and logging levels, (e) Fallback behavior when repair impossible, (f) Test strategy (25+ error vectors organized by repair category). | None (start here) | Spec answers: Where does tool execution happen? Which repairs are safe? How to validate non-dangerous mutations? All repair categories formalized. **AC Exit Gate:** `python ci/scripts/spec_completeness_check.py <spec_path> --type api` must PASS. | **A1 (Integration point unknown):** Spec must investigate Agent SDK. If external tool execution unavailable, escalate. **A3 (Schema format):** Confirm tool call format with framework docs. Confidence: MEDIUM → MEDIUM-HIGH. |
| **2** | **Test Design: Write Parser & Repair Tests** | Test Designer | Specification (Task 1), ticket AC examples, test_agent_framework_integration.py (reference patterns) | Test file: `tests/ci/test_tool_parsing_middleware.py` with: (a) 25+ test cases covering 6+ repair categories, (b) Behavioral tests for each repair type (string bool → True, int string → 123, missing field handling, etc.), (c) Validation tests ensuring dangerous mutations rejected, (d) Fallback tests verifying clear error on irreparable cases, (e) Adversarial tests for edge cases (multiple errors in one dict, nested structures, Unicode, etc.). | Task 1 (Spec complete) | All test cases runnable. Covers all repair code paths. Zero flakes (deterministic). Validates before/after states for each repair. **Test Matrix:** 6+ categories × 4-5 test cases per = 25+ total. | **Determinism:** Parser output must be consistent across multiple runs (no random behavior). Tests validate idempotency. |
| **3** | **Test Break: Adversarial Testing & Flake Detection** | Test Breaker | Tests from Task 2, specification | Enhanced test suite: (a) 5+ additional adversarial test cases per repair category, (b) Boundary condition tests (Unicode, empty strings, very large dicts, deeply nested structures), (c) Race condition tests (concurrent repair attempts), (d) Mutation tests for validation logic (attempt to bypass safety checks), (e) 4+ consecutive full test runs showing zero flakes. | Task 2 (Tests complete) | All tests pass consistently. Test suite expanded 2-3x. Zero flakes across 4+ runs. Validation logic tested for bypass attempts. | **R3 (Over-repair):** Test cases verify that invalid repairs are rejected, not silently applied. **Determinism:** All tests must be deterministic. |
| **4** | **Implementation: Build Parser & Middleware** | Implementation Agent | Specification (Task 1), tests (Task 2, Task 3), M902-18-T5 middleware reference | Middleware module at `ci/scripts/tool_parsing_middleware.py` (or location per spec) with: (a) Parser function handling JSON/YAML/XML/plain-text formats, (b) 6+ repair functions (one per category), (c) Validation gate rejecting dangerous mutations, (d) Audit trail logging all repair attempts with severity, (e) Fallback behavior with clear error messages, (f) All tests from Task 3 passing, (g) Type hints and docstrings per CLAUDE.md. **Artifact:** Implementation code + commit message. | Tasks 1–3 complete | Code follows CLAUDE.md style (typed, documented, explicit exception handling). All 25+ tests PASS. Zero regressions. Determinism verified (5+ runs). Type checking clean. Diff-cover gates pass (if Python-only). | **A2 (Repair scope):** Implementation sticks strictly to spec-defined categories. Over-repair rejected in code review. **A4 (Validation):** Whitelist-based validation per spec, no content inspection of commands. |
| **5** | **Static QA: Code Review & Lint** | Code Reviewer Agent | Implementation code from Task 4 | Code review summary: (a) All findings from Python Ruff review (E9, F, I rules), (b) Type hints validation (mypy or similar), (c) Documentation completeness check, (d) Security validation (no dangerous eval/exec, proper input bounds), (e) Approval checklist confirming ready for acceptance. **Artifact:** Code review report (may be inline in checkpoint). | Task 4 (Implementation complete) | Ruff clean (no E9/F/I violations). Type hints complete. All functions documented. No bare except blocks. Security findings (if any) resolved. Ready for AC Gatekeeper. | Code review is validation, not approval (AC Gatekeeper approves). If blocking findings: route back to Implementation Agent. |
| **6** | **AC Gatekeeper: Validate Acceptance Criteria** | AC Gatekeeper Agent | All task outputs (1–5), ticket AC, specification | Validation report: 8/8 acceptance criteria marked PASS with evidence. Each AC mapped to: (a) Code location, (b) Test file + test name, (c) Test execution result (PASS), (d) Evidence artifact path. If all ACs pass, advance ticket to COMPLETE. | Tasks 1–5 complete | All 8 ACs satisfied: (AC-1) Parser handles JSON/YAML/XML/plain-text ✓ (AC-2) Auto-repairs implemented (string bool, int strings, missing fields, typo correction, quoted paths) ✓ (AC-3) Validation rejects dangerous mutations ✓ (AC-4) Middleware wraps tool execution ✓ (AC-5) All repairs logged with severity ✓ (AC-6) 25+ error vectors tested ✓ (AC-7) Fallback behavior with clear errors ✓ (AC-8) Audit trail functional ✓ | **R1 (Integration point missing):** If middleware cannot locate tool execution, mark AC-4 BLOCKED. Escalate to BLOCKED stage. Do not mark COMPLETE without all ACs satisfied. |
| **7** | **Documentation: Update Integration Guide & Runbook** | Integration Agent (or Documenter) | Implementation (Task 4), specification (Task 1) | Updated documentation at `project_board/checkpoints/M902-19/INTEGRATION_GUIDE.md` with: (a) Middleware purpose and design, (b) API contract (repair categories, validation rules), (c) Example tool call before/after for each repair, (d) Audit log format and interpretation, (e) Integration with M902-18-T5 tool categorization (orthogonal middleware layers), (f) Runbook for future agents using parser middleware, (g) Troubleshooting guide (what if repair fails?). | Task 6 (AC Gatekeeper complete) | Documentation is accurate (reflects implementation), clear to future readers, includes working examples, no dead links. Explains interaction with M902-18-T5 (stacking middleware layers). | Documentation is internal (not a test artifact). No ambiguity for downstream agents (M902-20+) implementing dependent features. |

---

## Risk Register

| ID | Risk | Mitigation | Owner |
|---|---|---|---|
| **R1** | Tool execution layer inaccessible in Agent SDK | Spec Agent investigates early; if external, escalate with constraints documented | Spec Agent |
| **R2** | Tool call schema incompatible with expected format | Test Designer creates adaptors in test mocks; Implementation follows spec schema | Spec Agent + Test Designer |
| **R3** | Over-aggressive repair introduces security vulnerabilities | Validation gate whitelists safe mutations; Test Breaker writes bypass attempt tests | Implementation Agent + Test Breaker |
| **R4** | Repair logic creates non-deterministic behavior | All repair functions must be pure (same input → same output); tests verify idempotency | Implementation Agent + Test Breaker |
| **R5** | Logging overhead impacts performance | Audit trail uses lazy evaluation; benchmark in Test Breaker | Test Breaker |
| **R6** | Fallback error messages unclear to agents | Spec defines error message templates; Test Designer validates clarity | Spec Agent + Test Designer |
| **R7** | Middleware conflicts with M902-18-T5 tool categorization | Both are pre-invocation filters; document composition (categorization → repair). Verify no tool loss. | Spec Agent + Implementation Agent |

---

## Assumptions & Confidence

| ID | Assumption | Evidence | Confidence |
|---|---|---|---|
| **As1** | Tool execution happens at predictable boundary (before agent sees tools) | M902-18-T5 located it; Agent SDK docs | MEDIUM-HIGH |
| **As2** | Tool calls are JSON dicts with string/int/bool/list/dict values | Ticket AC example shows this format | MEDIUM-HIGH |
| **As3** | 25+ error vectors is sufficient coverage | M902-18 set bar at 38 tests; M902-19 matching scale | MEDIUM |
| **As4** | Repair logic can use static whitelists (no ML needed) | Ticket says "inspect parameter names" not "understand semantics" | HIGH |
| **As5** | Logging semantics (warning vs error) align with repair outcome | Clear from AC spec | HIGH |

---

## Success Criteria Summary

✅ **Execution plan is actionable:** Each task self-contained, depends only on prior tasks, clearly scoped.

✅ **Ambiguities documented:** A1–A5 with evidence requirements and confidence levels.

✅ **Risk register complete:** 7 risks with mitigations and owners.

✅ **No blocking issues at PLANNING stage:** M902-18-T5 prerequisite complete; tool execution investigation deferred to Spec Agent.

✅ **Checkpoint ready for Spec Agent:** All context needed for specification phase documented.

---

## Next Steps

**Immediate:** Route to Spec Agent (Task 1)
- Read specification prompt from this checkpoint
- Investigate Agent SDK tool execution layer
- Formalize 6-8 repair categories and validation rules
- Complete specification by end of day

**Unblock downstream:** M902-19 can proceed in parallel with M902-20+ (no cross-dependencies)

