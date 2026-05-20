# Execution Plan: M902-19 Forgiving Tool Parsing Middleware

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/19_forgiving_tool_parsing_middleware.md`

**Status:** PLANNING COMPLETE  
**Revision:** 1  
**Date:** 2026-05-20  
**Next Agent:** Spec Agent (Task 1)  
**Checkpoint:** `project_board/checkpoints/M902-19/2026-05-20T-planning-run.md`

---

## Executive Summary

**Objective:** Implement a "forgiving" tool parsing middleware that auto-repairs common LLM tool call mistakes (type mismatches, syntax errors, missing fields, typos) before tool execution, preventing retry loops.

**Scope:**
- Build parser handling JSON/YAML/XML/plain-text tool output formats
- Implement 6-8 repair categories (string→bool, int strings, missing fields, typo correction, etc.)
- Add validation gate rejecting dangerous mutations
- Wire middleware into tool execution layer (post-invocation, pre-execution)
- Audit trail with severity-level logging
- 25+ error vector test coverage

**Prerequisites:** ✅ M902-18-T5 complete (tool categorization framework ready; M902-19 orthogonal concern)

**Estimated Effort:** 6-8 days (similar to M902-18-T5 timeline)

**Key Ambiguities:**
1. Tool execution integration point location (investigate early in Spec phase)
2. Tool call schema format (assume JSON dict per ticket AC)
3. Repair safety boundaries (spec will define concrete categories)
4. Validation mechanism (static whitelists per tool category)
5. Logging semantics (warning = fixed, error = cannot fix)

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| **1** | **Specification: Define Repair Logic & Validation Strategy** | Spec Agent | Ticket AC, example repair cases, M902-18-T5 validation patterns, agent framework docs | Specification: `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md` with: (a) 6-8 repair categories formally defined with examples, (b) Validation rules per category and safety constraints, (c) Tool execution integration point identified (where middleware sits in Agent SDK), (d) Audit trail format with logging levels (warning/error/info), (e) Fallback behavior when repair fails, (f) Test strategy with 25+ error vectors organized by repair category. Section headers must include: Requirements (R1–R8+), Acceptance Criteria mapping, Non-Functional Requirements (NFR-1: determinism, NFR-2: performance, etc.), Test Strategy. | None (start) | Spec answers all 5 critical ambiguities: (A1) Where is tool execution? (A2) Which repairs are safe? (A3) Tool schema format? (A4) Validation approach? (A5) Logging semantics? All repair categories formalized with concrete examples. **AC Exit Gate:** Run `python ci/scripts/spec_completeness_check.py <spec_path> --type api`; must PASS before advancing to TEST_DESIGN. | **A1 (Integration point unknown):** Spec Agent must investigate Agent SDK docs/code. If tool execution not accessible, escalate with "Tool Execution Layer Inaccessible" blocking issue. **A3 (Schema format):** Assume JSON dict with string/int/bool/list/dict values per ticket AC. Confirm with framework docs. Confidence after Spec: MEDIUM → MEDIUM-HIGH. |
| **2** | **Test Design: Write Parser & Repair Test Suite** | Test Designer | Specification (Task 1), ticket AC examples, test_agent_framework_integration.py (M902-18-T5 reference patterns), tool parsing examples | Test file: `tests/ci/test_tool_parsing_middleware.py` (920+ lines, 38+ test cases, 9+ test classes). Coverage: (a) Parser tests for JSON/YAML/XML/plain-text formats (4+ cases), (b) Repair category tests (25+ cases, one test class per repair category): string bool→True/False, int strings→int, missing required fields→sensible defaults or clear error, wrong parameter names→typo correction suggestion, quoted paths→unquoted, nested structure handling, (c) Validation tests ensuring dangerous mutations rejected (5+ cases), (d) Fallback tests verifying irreparable cases return clear errors (3+ cases), (e) Adversarial tests for edge cases: multiple simultaneous errors, Unicode characters, very large dicts, deeply nested structures, race conditions. All tests must be deterministic (no randomness). Use unittest.mock per CLAUDE.md. | Task 1 (Spec complete) | All 38+ test cases runnable. All code paths in future implementation covered. Zero flakes (deterministic, verified across 5+ runs). Tests validate before/after states for each repair. Test names describe behavior, not ticket IDs (per CLAUDE.md). **AC Exit:** All tests initially pass (no pre-implementation run needed; tests define contract). | **A2 (Schema format):** Test mocks must use exact tool call format from spec. If spec reveals different format than assumed, restructure tests immediately. **Determinism:** Repair output must be consistent. Tests validate idempotency (repair(repair(X)) == repair(X)). |
| **3** | **Test Break: Adversarial Testing & Flake Detection** | Test Breaker | Tests from Task 2, specification, M902-18-T5 test-break reference | Enhanced test suite with 5+ additional adversarial cases per repair category (50+ total). Coverage: (a) Mutation tests attempting to bypass validation (e.g., nested dangerous commands, Unicode obfuscation), (b) Boundary tests (empty strings, nulls, max-size dicts), (c) Race condition tests (concurrent repair invocations), (d) Spec conformance mutation tests (ensure repairs match spec exactly, not "close enough"). Run full test suite 4+ times consecutively showing zero flakes. **Test Matrix:** 6+ repair categories × 8-10 adversarial cases = 50+ new tests. | Task 2 (Tests complete) | All tests pass consistently across 4+ full runs. Test suite expanded 2-3× (38 → 100+). Validation logic tested for bypass attempts. Zero flakes. No test timeouts or hangs. **Determinism Verified:** Same seed/input → identical output across runs. | **R3 (Over-repair):** Test cases verify invalid repairs are REJECTED, not silently applied. Mutation tests attempt to bypass validation; all must fail. **R4 (Non-determinism):** All tests must be deterministic. If any flake detected, diagnose and fix before proceeding. Confidence after Test Break: HIGH. |
| **4** | **Implementation: Build Parser & Middleware** | Implementation Agent | Specification (Task 1), tests (Task 2–3), M902-18-T5 middleware as architectural reference | Middleware module at `ci/scripts/tool_parsing_middleware.py` (or location per spec) with: (a) Entrypoint function wrapping tool execution (signature per spec), (b) Parser for JSON/YAML/XML/plain-text (separate parser functions per format), (c) 6+ repair functions (one per category, pure functions: same input→same output), (d) Validation gate function (rejects dangerous mutations based on spec whitelist), (e) Audit trail logging function (logs repairs with severity level per spec), (f) Fallback error handler (returns clear error message when repair impossible), (g) Type hints and docstrings per CLAUDE.md (no bare except, explicit error handling). All 100+ tests from Task 3 PASSING. Determinism verified (5+ runs, same input→same output). **Artifact:** Implementation code + commit message ("feat(M902-19): implement forgiving tool parsing middleware"). | Tasks 1–3 complete | Code follows CLAUDE.md style: typed (dict[str, Any], TypedDict for fixed key sets), documented (docstrings with Args/Returns/Raises), explicit exception handling (no bare except blocks), correct logging levels. All 100+ tests PASS. Zero regressions in existing code. Determinism verified. Type checking clean. Diff-cover passes (Python test coverage gate if applicable). | **A2 (Repair scope):** Implementation sticks strictly to spec-defined categories and validation rules. Over-repair or under-repair rejected in Static QA. **A4 (Validation):** Whitelist-based validation per spec (parameter name allowlist + type constraints), no content inspection of commands or dangerous eval/exec. **Middleware composition:** Tool parsing (M902-19) executes AFTER tool categorization (M902-18-T5) in the invocation pipeline; verify no tool loss when both layers active. |
| **5** | **Static QA: Code Review & Type Checking** | Code Reviewer Agent | Implementation code from Task 4, specification | Code review summary addressing: (a) Python Ruff rules (E9, F, I per CLAUDE.md), (b) Type hint completeness (mypy validation if available), (c) Documentation completeness (docstrings on all public functions), (d) Security validation (no eval, exec, subprocess without bounds; no command content inspection), (e) Style consistency with M902-18-T5 middleware (precedent). **Artifact:** Code review report (inline in checkpoint or separate summary). Optional: TypedDict findings if type hints improved. | Task 4 (Implementation complete) | Ruff clean (no E9/F/I violations). Type hints on all functions (no untyped signatures). All public functions documented. No bare except blocks. No security findings blocking release. Code review approves readiness for AC Gatekeeper. Any blocking findings routed back to Implementation Agent. | Code Review is validation gate, not approval (AC Gatekeeper approves via AC mapping). If blocking findings: Implementation Agent fixes + resubmits. Target: zero blocking findings from Code Reviewer. |
| **6** | **AC Gatekeeper: Validate All Acceptance Criteria** | AC Gatekeeper Agent | All task outputs (1–5), ticket AC (8 items), specification | Validation report: 8/8 acceptance criteria marked PASS or BLOCKED with objective evidence. Each AC mapped to: (a) Code location (file, function, line), (b) Test evidence (test file name + test case name), (c) Test execution result (e.g., test name: PASSED), (d) Artifact path (checkpoint, test output, code segment). **AC checklist:** (AC-1) Parser handles JSON/YAML/XML/plain-text ✓ (AC-2) Auto-repairs implemented: string bool→True/False, int strings, missing fields, typo correction, quoted paths ✓ (AC-3) Validation rejects dangerous mutations ✓ (AC-4) Middleware wraps tool execution ✓ (AC-5) All repairs logged with severity ✓ (AC-6) 25+ error vectors tested ✓ (AC-7) Fallback behavior with clear error messages ✓ (AC-8) Audit trail functional (before/after logging) ✓ | Tasks 1–5 complete | All 8 ACs satisfied with explicit evidence. No ambiguity in AC mapping. If all ACs PASS: route ticket to COMPLETE + move file to `project_board/902_milestone_902_agent_predictabilitiy_improvements/02_complete/`. If any AC BLOCKED: set ticket Stage to BLOCKED, document blocking issue, route back to owner. | **R1 (Integration point missing):** If middleware cannot locate tool execution layer in Agent SDK (Task 1 Spec issue not caught), mark AC-4 BLOCKED. Escalate entire ticket to BLOCKED with "Tool Execution Layer Inaccessible" blocking issue. Do NOT mark COMPLETE without all 8 ACs evidenced. Confidence: HIGH (Tests define ACs; AC Gatekeeper verifies by running tests + mapping to code). |
| **7** | **Documentation: Integration Guide & Runbook** | Integration Agent (Documenter) | Implementation (Task 4), specification (Task 1), M902-18-T5 integration guide as reference | Updated guide at `project_board/checkpoints/M902-19/INTEGRATION_GUIDE.md` (500+ words) with: (a) Overview: purpose, design, how it fits in agent pipeline, (b) Repair categories summary (6-8 types), (c) Before/after examples for each repair type (concrete tool calls), (d) Audit log format and interpretation (example log output), (e) Integration with M902-18-T5: both are pre-execution filters; tool categorization → repair middleware stacking (no conflicts), (f) Runbook: how agents use parsed output, how to interpret repair logs, troubleshooting (what if repair fails anyway?), (g) API contract: function signatures, expected exceptions, retry logic. Include code snippets showing middleware invocation. | Task 6 (AC Gatekeeper complete) | Documentation is accurate (reflects actual implementation code), clear to future readers, includes working code examples, no dead links, explains interaction with M902-18-T5 (middleware composition). Runbook is actionable for M902-20+ agents implementing dependent features. No ambiguity; future readers don't need to reverse-engineer code. | Documentation is internal (not a test artifact). No AC test coverage needed. Reviewed for clarity by Documenter. If unclear sections found: route back to Implementation Agent to clarify code or back to Documentation Agent to improve prose. Target: Future agent reads guide once and understands architecture + integration points. |

---

## Notes

- **Middleware Composition:** M902-19 (tool parsing repair) and M902-18-T5 (tool categorization filtering) are orthogonal layers. Both operate pre-execution. Stacking order: agent → tool categorization filter (M902-18-T5) → tool repair middleware (M902-19) → agent execution. No tool loss; both layers preserve tool list integrity.

- **Test Naming Convention:** Per CLAUDE.md, test file and test function names must describe behavior, not ticket IDs. Use patterns like `test_string_bool_repair_true_case`, not `test_M902_19_AC2_repair`. Traceability via docstrings/comments, not filenames.

- **Determinism Requirement:** All repair functions must be pure (no side effects, same input → same output). Tests verify idempotency: `repair(repair(X)) == repair(X)`. No randomness, no state, no I/O in repair logic.

- **Security Gate:** Validation must use static whitelists (parameter name allowlists per tool category), not semantic analysis. Reject any repair that could enable dangerous commands (e.g., shell escapes, path traversal). Test Breaker must write bypass attempt tests to ensure validation is not bypassed.

- **Rollout Plan (after COMPLETE):** M902-19 unblocks M902-20+ (downstream features may depend on forgiving parsing). Update CHECKPOINTS.md with completion entry after AC Gatekeeper validates all 8 ACs.

- **No Blocking Dependencies:** M902-19 does not depend on any incomplete ticket. M902-18-T5 is complete; M902-01 (Validation Gate Framework) is assumed complete (reference existing validation patterns).

---

## Risk Mitigation Summary

| Risk | Mitigation | Owner |
|---|---|---|
| **R1:** Integration point inaccessible | Spec Agent investigates early (Task 1). Escalate if blocking. | Spec Agent |
| **R2:** Tool schema incompatible | Test Designer creates mocks matching spec schema. Implementation adapts if needed. | Spec Agent + Test Designer |
| **R3:** Over-aggressive repair creates vulnerabilities | Validation gate whitelists per spec. Test Breaker writes bypass tests. Code Reviewer validates security. | Implementation Agent + Test Breaker |
| **R4:** Non-deterministic behavior | All repair functions pure. Test Breaker verifies idempotency across 4+ runs. | Implementation Agent + Test Breaker |
| **R5:** Logging overhead impacts performance | Spec defines lazy evaluation for audit trail. Test Breaker benchmarks. | Spec Agent + Test Breaker |
| **R6:** Fallback errors unclear to users | Spec templates error messages. Test Designer validates clarity. | Spec Agent + Test Designer |
| **R7:** Conflict with M902-18-T5 categorization | Both are pre-execution filters; verify composition in tests. No tool loss. | Implementation Agent + Test Designer |

---

## Acceptance Criteria (from Ticket)

1. ✅ Parser handles JSON, YAML, XML, and plain-text tool output formats
2. ✅ Auto-repairs common errors (string bool→true/false, int strings, missing fields, typo correction, quoted paths)
3. ✅ Validation before repair: Check if salvageable; reject dangerous mutations
4. ✅ Implemented as middleware wrapping tool execution
5. ✅ Logged: all repair attempts with severity
6. ✅ Tested with 25+ error vectors
7. ✅ Fallback behavior: clear error message with suggestions
8. ✅ Audit trail functional

---

## Next Steps

**Immediate (Task 1):** Route to Spec Agent
- Investigate Agent SDK tool execution layer
- Define 6-8 repair categories with validation rules
- Complete specification by target date (2026-05-25)

**Unblock:** M902-19 execution can proceed in parallel with M902-20+ (no cross-ticket dependencies)

**Final Checkpoint:** Update CHECKPOINTS.md with completion entry after Task 6 (AC Gatekeeper)

