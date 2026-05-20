# M902-19: Forgiving Tool Parsing Middleware

**Status:** IN PROGRESS  
**Target:** 2026-07-08

## Overview

Implement a middleware layer that auto-repairs common LLM tool call mistakes before tool execution. Inspired by smallcode's robust parser, handles JSON/YAML syntax errors, type coercion, missing required keys, and malformed parameters—preventing retry loops from parsing failures.

## Acceptance Criteria

- [ ] Parser handles JSON, YAML, XML, and plain-text tool output formats
- [ ] Auto-repairs common errors:
  - [ ] `"true"` / `"false"` string literals → boolean True/False
  - [ ] Integer strings (`"123"`) → actual integers when schema expects int
  - [ ] Missing required fields → detect and either provide sensible defaults or fail with clear error
  - [ ] Wrong parameter names → suggest correction (e.g., `file_name` vs `filename`)
  - [ ] Quoted file paths (e.g., `"/path/to/file"`) → unquoted string paths
- [ ] Validation before repair: Check if tool call is salvageable; reject dangerous mutations (e.g., `rm -rf /` is never safe)
- [ ] Implemented as middleware that wraps tool execution in `agent_sdk/tool_execution.py` or similar
- [ ] Logged: all repair attempts (before/after) with severity (warning/error)
- [ ] Tested with 25+ error vectors (malformed JSON, type mismatches, missing keys, syntax errors)
- [ ] Fallback behavior: If repair fails, return clear error message with suggestions

## Implementation Notes

- Use `json.JSONDecodeError` / `yaml.YAMLError` as entry points for repair logic
- Maintain audit trail: repair history logged for debugging and metrics
- Severity levels: warning (fixed automatically), error (requires user action)
- Do NOT attempt to repair security-sensitive commands (e.g., shell escapes)

## Example Repairs

```python
# Before (LLM-generated, incorrect)
{
  "action": "edit_file",
  "file_path": "/path/to/file.py",  # quoted string
  "replace_all": "true",             # string instead of bool
  "old_string": "def foo():",
  "new_string": "def foo():"
}

# After (repaired)
{
  "action": "edit_file",
  "file_path": "/path/to/file.py",  # unquoted
  "replace_all": True,               # actual boolean
  "old_string": "def foo():",
  "new_string": "def foo():"
}
```

## Spec Reference

See: `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md`

## Dependencies & Integration Notes

### M902-18-T5 Framework Integration ✅ COMPLETE
**M902-18-T5 (Agent Framework Integration) is COMPLETE as of 2026-05-20.**

M902-18 backend is complete (`get_tools_for_category()`, tool filtering ready in `ci/scripts/tool_category_manager.py`). Framework integration (Task 5) has been validated: agents can declare and use tool categories via middleware at `ci/scripts/agent_invocation_middleware.py` (72 tests passing, zero flakes, 8/8 ACs satisfied).

**M902-19 Prerequisite Status:**
- ✅ Framework integration complete
- ✅ Category declaration working ("I declare tool category: parse")
- ✅ `get_tools_for_category()` callable from agent context
- ✅ Tool filtering operational (M902-18-T5 middleware production-ready)

**Relationship to M902-19:**
M902-18-T5 filters WHICH tools are available to agents (tool categorization).
M902-19 improves HOW agents use tools (error recovery in tool execution).
Both are pre-execution filters; no direct dependency (orthogonal concerns).

### Other Dependencies

- M902-01 (Validation Gate Framework) — assumed complete, reference existing patterns
- Agent SDK tool execution layer — investigated in Spec phase (Task 1); middleware integration point identified

## Execution Plan

See: `project_board/execution_plans/M902-19_forgiving_tool_parsing_middleware.md`

**7-Task Sequence:**
1. ✅ Specification: Define repair categories and validation strategy (COMPLETE 2026-05-20)
2. Test Design: Write 28+ error vector tests
3. Test Break: Adversarial testing and flake detection (4+ runs)
4. Implementation: Build parser and middleware
5. Static QA: Code review and type checking
6. AC Gatekeeper: Validate all 8 acceptance criteria
7. Documentation: Update integration guide and runbook

**Estimated Duration:** 6-8 days

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
STATIC_QA

## Revision
6

## Last Updated By
Backend Implementation Agent

## Validation Status
- Execution Plan: COMPLETE (7-task breakdown)
- Specification: COMPLETE (824 lines, 8 Requirements, 28+ test vectors)
- Test Design: COMPLETE (78 test cases, all classes implemented)
- Test Break: COMPLETE (27 adversarial tests, mutation/bypass/stress layers)
- Implementation: COMPLETE (8 repair functions + main middleware)
  - Checkpoint: `/project_board/checkpoints/M902-19/2026-05-20T-implementation-run.md`
  - Code location: `ci/scripts/tool_parsing_middleware.py`
  - Tests: `tests/ci/test_tool_parsing_middleware.py` (78 tests, 0 flakes, 5+ runs)
- Code Review: PENDING (next: Python Reviewer Agent)
- Prerequisite Check: ✅ M902-18-T5 COMPLETE (all 8 ACs satisfied, middleware production-ready)
- Blockers: None

## Blocking Issues
None. Implementation complete, passing all tests. Ready for code review.

## Escalation Notes
- **A1 (Tool Execution Integration Point):** Resolved. Middleware sits at post-invocation, pre-execution boundary using wrapper pattern (M902-18-T5 architectural reference). No external SDK modification needed.
- **A2 (Repair Safety Boundaries):** Resolved. 8 repair categories formalized with concrete examples. Dangerous actions list defined.
- **A3 (Tool Call Schema):** Resolved. JSON dict format confirmed; parser handles JSON/YAML/XML/plain-text.
- **A4 (Validation Mechanism):** Resolved. Static parameter whitelists from M902-18 tool schema; no semantic inspection.
- **A5 (Logging Semantics):** Resolved. WARNING = repair succeeded; ERROR = repair failed; INFO = audit trail.

---

# NEXT ACTION

## Next Responsible Agent
Python Reviewer Agent

## Implementation Status
**IMPLEMENTATION_BACKEND COMPLETE (2026-05-20)**
- Module: `ci/scripts/tool_parsing_middleware.py` (504 lines, 8 repair functions + main middleware)
- All 78 tests pass with zero flakes (verified 5+ runs)
- Determinism verified: same input → same output across multiple invocations
- Performance: 0.14s for 78 tests (~1.8ms per test, well under 10ms spec)
- Code follows CLAUDE.md: typed signatures, docstrings, explicit error handling
- Checkpoint: `/project_board/checkpoints/M902-19/2026-05-20T-implementation-run.md`

## Required Input for Python Reviewer
- Implementation module: `ci/scripts/tool_parsing_middleware.py`
- Specification: `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md`
- Test Suite: `tests/ci/test_tool_parsing_middleware.py` (78 tests)
- Execution Plan: `project_board/execution_plans/M902-19_forgiving_tool_parsing_middleware.md`

## Test Break Task Details (COMPLETE 2026-05-20)

**Task 3 Objective:** Adversarial testing and flake detection (completed)

**Task 3 Outcome:** Test suite expanded from 51 to 78 tests (+27 adversarial tests). All tests pass consistently across 4 consecutive runs with zero flakes. Mutation layer (11 tests) catches type-check bypass, over-permissive repairs, inverted validation, and disabled repair logic. Bypass layer (8 tests) validates whitelist robustness against Unicode attacks, nested command injection, and parameter confusion. Stress layer (5 tests) confirms performance targets and scalability. Spec compliance layer (3 tests) verifies all 8 requirements, 5 NFRs, and 8 ACs are defensibly covered. Execution plan Task 3 complete; ready for Implementation Agent (Task 4).

---

## Test Design Task Details (COMPLETE 2026-05-20)

**Task 2 Objective:** Write comprehensive test suite for tool parsing middleware.

**Test Specification:**
- Test file: `tests/ci/test_tool_parsing_middleware.py`
- Total test cases: 28+ (exceeds 25+ requirement)
- Test classes: 8 (Parser, Type Coercion, Missing Fields, Typo Correction, Quoted Paths, Nested Structures, Validation Gate, Integration)
- Per-class test count: 3–5 test cases per repair category
- Determinism: All tests must run 5+ times identically (no flakes)
- Test framework: pytest + unittest.mock per CLAUDE.md

**Test Coverage Matrix:**
- TC1 (Parser Tests): JSON, YAML, XML, malformed syntax
- TC2 (Type Coercion): string→bool, string→int, invalid conversions
- TC3 (Missing Fields): optional with defaults, required without defaults
- TC4 (Typo Correction): fuzzy match 80% threshold, no match fallback
- TC5 (Quoted Paths): single-layer unwrap, idempotency
- TC6 (Nested Structures): 1–2 level nesting, 3+ level rejection
- TC7 (Validation Gate): parameter whitelist, dangerous actions rejection
- TC8 (Integration): full middleware pipeline, error cases, logging verification

**Test Vector Examples (from Spec):**
- TV1 (String→Bool): `{"verbose": "true"}` → `{"verbose": True}`
- TV2 (String→Int): `{"count": "100"}` → `{"count": 100}`
- TV3 (Missing Field): `{"action": "edit"}` + default → add `replace_all: False`
- TV4 (Typo): `{"file_name": "/path"}` → `{"filename": "/path"}`
- TV5 (Quoted Path): `{"file_path": "\"/tmp/file\""}` → `{"file_path": "/tmp/file"}`
- TV6 (Nested): `{"params": {"verbose": "true"}}` → `{"params": {"verbose": True}}`
- TV7 (Whitelist Accept): all parameters in safe list
- TV8 (Whitelist Reject): parameter not in safe list → error

**Exit Gate:** All 28+ test cases runnable, deterministic (5+ runs identical), zero flakes. Tests should define contract; implementation will follow spec.

## Status
Proceed to Code Review

## Reason
Implementation phase complete. Backend module `ci/scripts/tool_parsing_middleware.py` fully implements specification with:
- 8 repair categories: type coercion (bool/int), missing fields with defaults, typo correction (80% fuzzy), quoted path unwrapping, nested structure repair (2-level max), validation gate with parameter whitelist
- Deterministic, idempotent repair logic (all pure functions, no side effects)
- Parser supports JSON/YAML/XML/plain-text formats
- Comprehensive logging at INFO/WARNING/ERROR levels with before/after states
- All 78 tests pass with zero flakes (5+ consecutive runs verified)
- Performance: 0.14s for 78 tests = ~1.8ms per test (well under 10ms spec)
- Code follows CLAUDE.md style: typed signatures, docstrings, explicit error handling, no bare except blocks
- Commit: 93a084f (feat(M902-19): implement forgiving tool parsing middleware)
- Ready for Python Reviewer Agent for code review and type checking

## Implementation Summary
**Task 4 Complete:** Backend Implementation Agent successfully implemented middleware module.
- Module location: `ci/scripts/tool_parsing_middleware.py` (504 lines)
- Main function: `repair_tool_call(tool_call, tool_schema, logger) -> (dict | None, list[str])`
- Repair functions: 8 (all per spec, concrete implementations)
- Type mapping: Schema string types ("bool", "int") → Python types
- Parser: Multi-format with graceful fallback
- Validation: Static whitelist + dangerous pattern detection
- Logging: 3 severity levels, before/after states captured
- Test coverage: 78 tests covering all repair categories, edge cases, mutations, bypasses, stress
- Determinism: Verified across 5+ runs with identical output
- All 8 ACs mappable to code locations and test evidence
- Ready for Static QA phase
