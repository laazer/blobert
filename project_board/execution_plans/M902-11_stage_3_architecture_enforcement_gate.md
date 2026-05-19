# M902-11 Execution Plan: Stage 3 — Architecture Enforcement Gate

**Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/11_stage_3_architecture_enforcement_gate.md`  
**Plan Version:** 1.0  
**Created:** 2026-05-19  
**Status:** READY FOR EXECUTION

---

## Overview

This execution plan decomposes M902-11 into 7 sequential, testable tasks. The feature implements Stage 3 of the 8-stage governance pipeline: structural architecture enforcement using import-linter (Python), eslint-plugin-boundaries (TypeScript), semgrep (custom rules), jscpd (duplication), and radon/lizard (complexity).

The gate must:
1. Run multiple analysis tools with tool-specific timeout and error handling
2. Aggregate violations into a unified gate schema (from M902-01)
3. Classify severity: FAIL for SRP/dependency/circular imports; WARN for complexity; PASS for clean
4. Return structured JSON matching gate result schema
5. Register in `gate_registry.json`
6. Be tested with architecture violation vectors (SRP, circular imports, duplication, complexity)

**Dependencies:**
- M902-01 (Validation Gate Framework) — COMPLETE
- M902-02 (Static Analysis tools baseline) — COMPLETE
- `bot_vault/architecture/code_governance.md` (Stage 3 rules) — READ

**No gating blockers identified.**

---

## Task Breakdown

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Specification freeze: Architecture enforcement rules, tool contracts, output schema | Spec Agent | Ticket M902-11, `code_governance.md` Stage 3 section, M902-01 gate schema, M902-02 tool audit | Spec file `project_board/specs/902_11_architecture_enforcement_gate_spec.md` (requirements 01–08, acceptance criteria, test vectors, non-functional requirements) | M902-01, M902-02, code_governance.md | Spec completeness check passes; all 7 ticket ACs mapped to requirements; tool contracts frozen (import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard); SRP/circular/duplication/complexity rules enumerated; output schema validated against M902-01 | Q1: Should complexity warnings block or warn-only? A: WARN per code_governance.md Stage 3 "exit rules" (complexity violations → WARN or FAIL configurable). Assume WARN for Stage 3; implementation can make configurable. Q2: How should tool unavailability be handled? A: Gracefully via exit code skip or PASS with message (pattern from M902-02, M902-09). Q3: What is the duplication detection threshold (jscpd)? A: Defer tuning to M903+; spec documents baseline (8+ lines, cross-file) per code_governance. Q4: Should async safety violations block (from code_governance.md 4.4)? A: Yes, FAIL per code_governance "async safety violations → hard fail". Q5: Observability violations? A: WARN-level per code_governance Stage 3. Q6: Tool timeout values? A: Reference M902-02 TOOL_TIMEOUTS dict; apply same pattern. Confidence: HIGH. |
| 2 | Test Design: Behavioral test suite for architecture enforcement | Test Designer Agent | Spec file from Task 1 | Test file `tests/ci/test_architecture_enforcement_check.py` with 50+ behavioral tests covering: (a) module signature & output schema, (b) SRP violations (controller→repo, domain→infra, service→HTTP), (c) dependency direction violations (reverse edges, circular imports), (d) cross-layer state mutation, (e) duplication clusters, (f) complexity spikes, (g) async safety violations, (h) tool invocation & mocking, (i) registry integration, (j) error handling | Task 1 (Spec) | Tests cover all 7 ticket ACs; test vectors from spec; at least 50+ tests; deterministic (mocked subprocess, no real tools); syntax valid; all tests passing locally before handoff | Will mock subprocess to avoid requiring external tools in test environment. Will use strategy pattern for tool mocks to allow future tool swaps. Reference M902-09/M902-10 test suites for structure and patterns. Confidence: MEDIUM (new tool suite; untested patterns). |
| 3 | Test Break: Adversarial & mutation test suite for architecture enforcement | Test Breaker Agent | Behavioral test suite from Task 2 | Additional test file `tests/ci/test_architecture_enforcement_check_adversarial.py` with 40+ adversarial tests covering: (a) tool output mutation (malformed JSON, missing fields, invalid severity), (b) violation boundary conditions (line 0, huge line numbers, empty messages), (c) priority/severity edge cases, (d) tool timeout failures, (e) missing tool graceful handling, (f) concurrent tool execution, (g) determinism/flakiness, (h) registry contract violations, (i) assumption validation (tool paths, git availability), (j) performance/memory stress tests | Task 2 (Behavioral tests) | 40+ adversarial tests; all tests passing; designed to catch regressions and edge cases; deterministic; no external tool dependencies | Same mocking strategy as Task 2. Will encode conservative assumptions as checkpoint markers. Confidence: MEDIUM. |
| 4 | Implementation: Python module `architecture_enforcement_check.py` with tool orchestration & aggregation | Implementation Agent | Spec from Task 1, tests from Tasks 2–3 | Module `ci/scripts/gates/architecture_enforcement_check.py` with: (a) `run(inputs: dict) -> dict` function matching M902-01 gate schema, (b) tool invocation for import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard with timeout/error handling, (c) violation aggregation and SRP/dependency/circular-import detection, (d) severity classification (FAIL for SRP/circular, WARN for complexity), (e) output schema matching M902-01, (f) proper exception handling (no bare except, explicit propagation), (g) logging per code_governance.md observability rules | Tasks 2–3 (tests define contract) | Module created; all tests pass (100% pass rate); code review passes (no bare except, SRP intact, no logging-only handlers); diff-cover preflight passes if Python tests added | Import-linter will be invoked on Python code only (asset_generation/python, backend). eslint-plugin-boundaries on TypeScript (asset_generation/web/frontend). semgrep on all languages. jscpd on all source code. radon/lizard on Python/GDScript. Tool paths assumed available in PATH or environment; gracefully skip if missing. Confidence: MEDIUM (tool integration complexity). |
| 5 | Static QA: Code review, linting, type checking | Spec/Code Review Agent | Implementation from Task 4 | Code review report; module passes all linters (ruff, mypy, wemake rules from code_governance.md exception handling rules); no bare except clauses; proper logging; SRP maintained; gate schema compliance validated | Task 4 (Implementation) | No ruff/mypy/wemake violations; no bare except; proper exception propagation; code follows CLAUDE.md patterns from existing gates (M902-09, M902-10, M902-02); gate schema validated | Reference M902-02 static_analysis_check.py and M902-09 diff_classification.py as implementation patterns. Use same logging, timeout, error handling patterns. Confidence: HIGH (pattern well-established). |
| 6 | Integration: Register gate in `gate_registry.json`, verify orchestration path | Integration Agent | Module from Task 4 + Static QA from Task 5 | Updated `gate_registry.json` with entry for `architecture_enforcement_check` gate (stage: 3, blocking: true for SRP/circular/async violations, shadow: false for complexity warnings); gate is callable by orchestrator; integration tests pass (gate can be imported and run by gate_runner.py) | Tasks 4–5 (implementation & review) | Registry entry created with correct metadata; gate is importable; orchestrator can call `run({})` and receive valid JSON; integration tests pass (< 10s execution time per test) | Will follow gate_registry.json schema from M902-09 (stage, blocking, shadow, description fields). Registry modification may require Spec Agent validation if schema unclear. Confidence: HIGH. |
| 7 | Acceptance Gatekeeper: Verify all 7 ticket ACs met, advance to COMPLETE | Spec Agent / Planner Agent | All deliverables from Tasks 1–6 | Gatekeeper report; ticket Stage advanced to COMPLETE; Revision incremented; Last Updated By set; all 7 ACs verified: (AC1) gate runs tools, (AC2) detects SRP, (AC3) detects dependency direction, (AC4) detects cross-layer mutation, (AC5) detects duplication, (AC6) detects complexity, (AC7) detects async safety, (AC8) implemented as architecture_enforcement_check.py, (AC9) integrated into registry, (AC10) tested with violation vectors | Tasks 1–6 (all prior work) | All 7 ACs from ticket verified; implementation COMPLETE; tests passing; code review clean; registry integrated; ticket advanced to COMPLETE stage | Gatekeeper must run acceptance tests and validate each AC against implementation. Use M902-09 acceptance gatekeeper log as pattern. Confidence: HIGH (process well-established). |

---

## Notes

### Dependencies & Ordering

- **Strict sequential:** Tasks must complete in order (1 → 2 → 3 → 4 → 5 → 6 → 7)
- **Task 1 (Spec)** requires reading `code_governance.md` Stage 3 section and M902-01/M902-02 for tool context
- **Tasks 2–3 (Tests)** can be done in parallel after Task 1 completes (though sequenced 2 → 3 per standard workflow)
- **Task 4 (Implementation)** depends on Tasks 2–3 for test contracts
- **Task 5 (Static QA)** depends on Task 4; can leverage Task 3 test vectors for validation
- **Task 6 (Integration)** depends on Tasks 4–5
- **Task 7 (Acceptance)** depends on all prior tasks (final gate before COMPLETE)

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Tool integration complexity (5 tools, varying output formats) | MEDIUM | HIGH | Follow M902-02 static_analysis_check.py pattern; create tool-specific adapters; mock all tools in tests to avoid external dependencies |
| Semgrep rule design (custom SRP/circular rules undefined) | MEDIUM | HIGH | Spec Agent must enumerate exact rule definitions in Requirement 04; reference code_governance.md dynamic introspection rules; defer advanced rules to M903 if undefined |
| Duplication detection threshold ambiguity (8+ lines?) | LOW | MEDIUM | Document baseline in spec (8+ lines, cross-file per code_governance); allow configuration in M903 |
| Async safety detection (blocking I/O, unbounded spawning) | MEDIUM | MEDIUM | Use semgrep rules + radon async detection; defer full-stack async analysis to agent layer (Stage 6) if needed |
| Performance under large repos (5 tools, timeouts) | LOW | MEDIUM | Set tool timeouts (reference M902-02 TOOL_TIMEOUTS); parallelize tool execution if time permits; gate should exit <10s nominal case |
| Tool unavailability (tools not in PATH) | MEDIUM | LOW | Gracefully skip missing tools; return PASS with explanatory message (pattern from M902-02); log warnings |

### Assumptions

1. **Tool availability:** All 5 tools are installed and available in PATH (import-linter, eslint-plugin-boundaries, semgrep, jscpd, radon/lizard). If unavailable, gate gracefully skips and logs warning.
2. **Architecture patterns defined:** SRP rules, dependency direction, circular import detection are well-defined in code_governance.md Stage 3 section. Spec Agent reads and freezes rules.
3. **Complexity severity:** Complexity violations are WARN-level (not FAIL) per code_governance.md. Can be made configurable in implementation.
4. **Duplication baseline:** 8+ lines, cross-file (per code_governance.md). Spec Agent documents this threshold.
5. **Async safety as HARD FAIL:** async safety violations (blocking I/O in async, unbounded spawning) are HARD FAIL per code_governance.md Stage 2 & 3 exit rules.
6. **Gate schema from M902-01:** Output must conform to gate-result-success.json and gate-result-failure.json schemas defined in M902-01 framework.
7. **No circular imports in blobert codebase:** Current state assumed clean; tests will inject violations to verify detection.
8. **Tool output formats stable:** Tool JSON output formats stable; no breaking changes expected during this work.

### Deferred Scope (M903+)

- Orchestration and routing decisions (which pipeline stages to skip based on classification)
- Tool configuration tuning (timeouts, rules, thresholds)
- Parallel tool execution optimization
- Agent semantic review integration (Stage 6)
- Advanced async/observability rule definitions
- Dynamic SRP rule injection from agent layer

---

## File Paths (Source of Truth)

**Input files:**
- Ticket: `/Users/jacobbrandt/workspace/blobert/project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/11_stage_3_architecture_enforcement_gate.md`
- Code governance: `/Users/jacobbrandt/workspace/blobert/bot_vault/architecture/code_governance.md`
- Gate framework (M902-01): `project_board/specs/902_01_gate_runner_spec.md`
- Tool audit (M902-02): `project_board/specs/902_02_static_analysis_gate_spec.md`
- Reference implementation (M902-09): `ci/scripts/gates/diff_classification.py`, `tests/ci/test_diff_classification_gate.py`
- Reference implementation (M902-10): `ci/scripts/gates/formatting_check.py`, `tests/ci/test_formatting_check.py`

**Output files:**
- Spec: `/Users/jacobbrandt/workspace/blobert/project_board/specs/902_11_architecture_enforcement_gate_spec.md` (Task 1)
- Behavioral tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_architecture_enforcement_check.py` (Task 2)
- Adversarial tests: `/Users/jacobbrandt/workspace/blobert/tests/ci/test_architecture_enforcement_check_adversarial.py` (Task 3)
- Implementation: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/architecture_enforcement_check.py` (Task 4)
- Registry: `/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/gate_registry.json` (Task 6, update)

---

## Execution Readiness Checklist

- [x] All tasks are small, single-objective, and self-contained
- [x] Dependencies are explicit and ordered correctly
- [x] Success criteria are measurable and testable
- [x] Risks and assumptions are documented
- [x] File paths are absolute and verified
- [x] No blocking issues or ambiguities remain
- [x] Spec Agent has sufficient context to freeze requirements
- [x] Test Designers have reference implementations (M902-09, M902-10)
- [x] Implementation Agent has test contracts to implement against
- [x] Integration Agent has clear registry schema and gate contract

**Plan is ready for handoff to Spec Agent.**

