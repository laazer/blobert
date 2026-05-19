# M902-19: Forgiving Tool Parsing Middleware

**Status:** PENDING  
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

See: `project_board/specs/902_19_tool_parsing_middleware_spec.md`

## Dependencies & Integration Notes

### M902-18-T5 Framework Integration Requirement ⚠️
**M902-18 Task 5 (Agent Framework Integration) MUST be completed before M902-19 implementation begins.**

M902-18 backend is complete (`get_tools_for_category()`, `measure_tool_schema_reduction()` ready in `ci/scripts/tool_category_manager.py`). However, **framework integration (Task 5)** is a prerequisite: agents must be able to declare and use tool categories.

**Dedicated Task 5 Ticket:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/18a_tool_categorization_framework_integration.md` (M902-18-T5)

**Before starting M902-19:**
1. Verify M902-18-T5 is COMPLETE (framework wiring done)
2. Confirm agents can declare categories: "I declare tool category: parse"
3. Verify `get_tools_for_category()` is callable from agent invocation context

**Why:** M902-19's tool parsing middleware will operate on agent inputs whose tools are already filtered by category (per M902-18). The repair logic must understand category-filtered tool schemas.

**Status:** M902-18 backend complete (180 tests passing). **BLOCKED:** Framework integration (Task 5) is in separate ticket M902-18-T5; awaiting agent framework discovery. See checkpoint at `project_board/checkpoints/M902-18/` and task at M902-18-T5.

### Other Dependencies

- M902-01 (Validation Gate Framework)
- Agent SDK tool execution layer (may require access to internal APIs)
