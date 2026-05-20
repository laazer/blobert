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
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Validation Status
- Execution Plan: COMPLETE
- Specification: COMPLETE (824 lines, 8 Requirements, 28+ test vectors)
- Checkpoint: `/project_board/checkpoints/M902-19/2026-05-20T-specification-run.md`
- Prerequisite Check: ✅ M902-18-T5 COMPLETE (all 8 ACs satisfied, middleware production-ready)
- Spec Completeness Check: PASS (type: generic; no required sections)
- Blockers: None
- Ambiguities: All 5 (A1–A5) resolved with HIGH confidence

## Blocking Issues
None. All ambiguities resolved. M902-19 ready for Test Design phase.

## Escalation Notes
- **A1 (Tool Execution Integration Point):** Resolved. Middleware sits at post-invocation, pre-execution boundary using wrapper pattern (M902-18-T5 architectural reference). No external SDK modification needed.
- **A2 (Repair Safety Boundaries):** Resolved. 8 repair categories formalized with concrete examples. Dangerous actions list defined.
- **A3 (Tool Call Schema):** Resolved. JSON dict format confirmed; parser handles JSON/YAML/XML/plain-text.
- **A4 (Validation Mechanism):** Resolved. Static parameter whitelists from M902-18 tool schema; no semantic inspection.
- **A5 (Logging Semantics):** Resolved. WARNING = repair succeeded; ERROR = repair failed; INFO = audit trail.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input
- Specification: `project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md` (COMPLETE, 824 lines)
- Execution Plan: `project_board/execution_plans/M902-19_forgiving_tool_parsing_middleware.md`
- Spec Checkpoint: `/project_board/checkpoints/M902-19/2026-05-20T-specification-run.md`
- Test Strategy: Spec Requirement 8 (28+ test vectors, 8 test classes)

## Test Design Task Details

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
Proceed

## Reason
Test Design phase complete. 51 comprehensive behavioral test cases written and all passing (exceeds 28+ spec requirement). All 8 test classes defined mapping to 8 spec requirements. All repair categories covered. Determinism verified (5+ runs identical). All 8 ticket ACs represented in test vectors with explicit evidence. No spec gaps identified. Ready for Test Breaker to expand coverage and detect flakes.

## Success Criteria for Test Design Phase
- 28+ test cases written (4–5 per repair category)
- All test cases deterministic (no flakes, 5+ identical runs)
- All repair categories and error paths covered
- All 8 ACs represented in test cases
- No spec gaps identified by Test Designer
- Test execution passes 100% with 0.1–0.5s latency
