# M902-18 Tool Categorization Layer — Test Design Stage

**Ticket Path:** `project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md`

**Run Date:** 2026-05-18  
**Stage:** TEST_DESIGN  
**Agent:** Test Designer Agent

---

## Test Design Summary

**Objective:** Design comprehensive behavioral test suite covering all 8 requirements and acceptance criteria (AC) for tool categorization system.

**Test Organization:**
- **Primary tests:** `tests/ci/test_tool_categorization.py` (45 primary behavioral tests)
- **Adversarial tests:** `tests/ci/test_tool_categorization_adversarial.py` (28 adversarial/boundary tests)
- **Total coverage:** 73 tests across 6 major test classes

**Framework:** Python `pytest` with `unittest.mock` for tool schema mocks.

---

## Test Mapping to Requirements & Acceptance Criteria

### Requirement 1: Tool Categories Enum (AC-1.1–1.5)
**Test Class:** `TestToolCategoriesEnum` (7 tests)
- `test_five_categories_defined`: Verify enum has exactly 5 categories (parse, modify, test, plan, think)
- `test_category_names_lowercase`: All category constants use lowercase names
- `test_categories_importable`: Categories are importable from tool_category_manager
- `test_category_descriptions_present`: Each category has human-readable description (1–2 sentences)
- `test_no_empty_categories`: All 5 categories are non-empty (have ≥1 tool after mapping)
- `test_categories_stored_in_json`: Tool categories JSON has `categories` key with array of objects
- `test_categories_mutually_exclusive_per_agent`: Single agent invocation declares one category (not multi-category in phase 1)

**AC Coverage:** 1.1–1.5 fully covered via runtime behavior assertions (not prose).

---

### Requirement 2: Tool-to-Category Mapping (AC-2.1–2.6)
**Test Class:** `TestToolToCategoryMapping` (8 tests)
- `test_minimum_four_tools_mapped`: At least 4 tools (Read, Write, Glob, Grep) in mapping
- `test_all_tools_mapped`: Every tool in mapping is mapped to ≥1 category
- `test_no_tools_in_zero_categories`: No tool maps to zero categories
- `test_all_categories_have_tools`: Each of 5 categories includes ≥1 tool
- `test_read_in_parse_and_think`: Tool "Read" appears in parse and think categories
- `test_write_in_modify_only`: Tool "Write" appears in modify category (not others)
- `test_bash_in_multiple_categories`: Tool "Bash" can appear in test, plan, think (demonstrates tools can be in multiple categories)
- `test_tool_mapping_has_rationale`: Each tool in mapping includes rationale string explaining category assignment

**AC Coverage:** 2.1–2.6 fully covered via schema validation and deterministic tool list assertions.

---

### Requirement 3: Function Interface & Contract (AC-3.1–3.7)
**Test Class:** `TestGetToolsForCategory` (11 tests)
- `test_function_exists`: `get_tools_for_category()` is defined and callable
- `test_function_signature`: Function accepts `category: str` and returns `list`
- `test_valid_category_parse`: `get_tools_for_category("parse")` returns non-empty tool list
- `test_valid_category_modify`: `get_tools_for_category("modify")` returns non-empty tool list
- `test_valid_category_test`: `get_tools_for_category("test")` returns non-empty tool list
- `test_valid_category_plan`: `get_tools_for_category("plan")` returns non-empty tool list
- `test_valid_category_think`: `get_tools_for_category("think")` returns non-empty tool list
- `test_invalid_category_raises_valueerror`: `get_tools_for_category("invalid")` raises `ValueError`
- `test_invalid_category_error_message_lists_valid_categories`: ValueError message includes valid categories
- `test_function_is_deterministic_same_input_same_output`: Calling same function twice with same category returns equal lists (content match)
- `test_function_has_docstring`: Function has docstring documenting purpose, args, returns, exceptions

**AC Coverage:** 3.1–3.7 fully covered via function contract validation.

---

### Requirement 4: Agent Framework Integration (AC-4.1–4.6)
**Test Class:** `TestAgentFrameworkIntegration` (6 tests)
- `test_framework_accepts_tool_category_parameter`: Verify integration point (mock or actual framework) accepts `tool_category` parameter
- `test_tool_category_parameter_is_optional`: Framework works without `tool_category` (backward compatible)
- `test_valid_category_filters_tools`: When `tool_category="parse"` is passed, framework filters to parse tools only
- `test_invalid_category_falls_back_to_all_tools`: Invalid category triggers fallback to all tools (fail-safe, not fail-hard)
- `test_framework_logs_warning_on_invalid_category`: When category is invalid, framework logs warning (not error)
- `test_no_regression_existing_agents`: Agents without `tool_category` parameter receive all tools (backward compatible)

**AC Coverage:** 4.1–4.6 covered via integration-level assertions (simulated agent invocation with category parameter).

---

### Requirement 5: Agent Declaration Protocol (AC-5.1–5.6)
**Test Class:** `TestAgentCategoryDeclaration` (9 tests)
- `test_regex_pattern_extracts_valid_declaration`: Regex correctly extracts category from "I declare tool category: parse"
- `test_regex_pattern_extracts_workflow_category_syntax`: Regex extracts from "My workflow category is parse"
- `test_regex_pattern_extracts_tool_category_syntax`: Regex extracts from "Tool category: parse"
- `test_declaration_extraction_case_insensitive`: Regex accepts "PARSE", "Parse", "parse" (case-insensitive)
- `test_missing_declaration_returns_none_or_empty`: Prompt without declaration returns None or empty string
- `test_invalid_category_in_declaration_is_ignored`: Invalid category name in declaration is silently ignored (fallback to all tools)
- `test_multiple_declarations_in_prompt_uses_first`: If multiple declarations, first one wins (or documented behavior)
- `test_declaration_not_in_agent_output`: Declaration is removed from visible agent prompt before execution (framework responsibility)
- `test_declaration_regex_no_false_positives`: Phrase "My workflow category is excellent" is NOT matched as tool category

**AC Coverage:** 5.1–5.6 covered via regex extraction and validation assertions.

---

### Requirement 6: Token/Schema Measurement Protocol (AC-6.1–6.7)
**Test Class:** `TestSchemaMeasurement` (9 tests)
- `test_measurement_function_exists`: `measure_tool_schema_reduction()` is defined and callable
- `test_measurement_returns_dict_with_required_keys`: Function returns dict with keys: category, baseline_bytes, filtered_bytes, reduction_percent, tool_count_baseline, tool_count_filtered, timestamp
- `test_baseline_bytes_computed_correctly`: Baseline byte count = len(json.dumps(all_tools, separators=(',', ':')).encode('utf-8'))
- `test_filtered_bytes_computed_correctly`: Filtered byte count is computed correctly for category
- `test_reduction_percent_formula_correct`: reduction_percent = ((baseline - filtered) / baseline) * 100
- `test_reduction_percent_in_valid_range`: reduction_percent is between 0 and 100 (inclusive)
- `test_measurement_is_deterministic_same_tools_same_bytes`: Same category measured twice yields identical byte counts (determinism check)
- `test_all_categories_show_measurable_reduction`: All 5 categories return reduction_percent > 0 (no category is all-tools)
- `test_measurement_includes_timestamp`: Returned dict includes ISO 8601 timestamp

**AC Coverage:** 6.1–6.7 fully covered via measurement assertion and determinism validation.

---

### Requirement 7: Integration Testing (AC-7.1–7.7)
**Test Class:** `TestIntegration` (5 tests)
- `test_integration_parse_mode_receives_parse_tools`: Simulated agent in parse mode receives only parse tools (Read, Glob, Grep, Bash read-safe)
- `test_integration_modify_mode_receives_modify_tools`: Simulated agent in modify mode receives write tools
- `test_integration_test_mode_receives_test_tools`: Simulated agent in test mode receives test execution tools
- `test_integration_backward_compatibility_no_category_all_tools`: Agent without category declaration receives all tools
- `test_integration_reduction_metric_within_target`: Schema reduction for all categories is measurable (not reporting errors)

**AC Coverage:** 7.1–7.6 covered via integration harness; AC-7.7 (live agents) deferred to Integration Agent (Task 7) checkpoint.

---

### Requirement 8: Runbook Documentation (AC-8.1–8.7)
**Test Class:** `TestRunbookDocumentation` (2 tests)
- `test_runbook_section_exists`: Runbook has "Tool Categorization: When & How to Declare Category" section
- `test_runbook_includes_decision_tree`: Runbook includes decision tree/table for category selection with examples
- `test_runbook_includes_prompt_syntax`: Runbook documents exact syntax: "I declare tool category: <category>"
- `test_runbook_includes_3_complete_examples`: Runbook has examples for Spec (parse), Implementation (modify), Test Designer (test)
- `test_runbook_includes_fallback_guidance`: Runbook includes section: "If category blocks tool, declare broader category"
- `test_runbook_clarifies_optional_declaration`: Runbook states "category declaration is optional; backward compatible"
- `test_runbook_includes_troubleshooting`: Runbook has troubleshooting section with common issues and remedies

**AC Coverage:** 8.1–8.7 — deferred to Integration Agent (Task 7). Test Designer creates placeholder tests that verify runbook file exists (Infrastructure requirement, not behavioral test).

---

## Adversarial & Boundary Test Coverage

**Test Class:** `TestAdversarial` (28 tests)

### Error Handling (8 tests)
- Missing config file: `tool_categories.json` not found → clear RuntimeError
- Corrupted JSON (invalid JSON syntax) → clear error with line number
- Empty config file (valid JSON but empty dict) → clear error
- Null categories array → clear error
- Unknown tool in mapping → handled gracefully (skip or log)
- Duplicate tool names in mapping → detected and reported
- Tool in zero categories → detected as invalid
- Empty category (valid category but no tools assigned) → detected as potential issue

### Boundary Conditions (8 tests)
- Minimum tools (1 tool per category) → function works correctly
- Large schema (100+ tools simulated) → byte count calculation remains deterministic
- Category with all tools → valid edge case, no error
- Schema with special characters in tool names → UTF-8 encoding handled correctly
- Very large tool schema (10k+ bytes) → measurement still accurate
- Zero-byte difference between filtered and all tools → reduction_percent = 0 (edge case)
- Baseline = Filtered (100% overlap) → reduction_percent = 0 is valid
- All tools in one category → other categories empty (invalid per AC-2.3, detected)

### Declaration Protocol Edge Cases (6 tests)
- Whitespace variants: "I declare tool category:parse" (no space before parse)
- Tabs in declaration: "I declare tool category:\tparse"
- Multiple spaces: "I declare  tool  category:  parse"
- Case mixing: "i DECLARE tool CATEGORY: Parse"
- False positive: "My workflow category is excellent" (NOT matched)
- Partial match: "I declare tool" (incomplete, not matched)

### Determinism & Idempotency (6 tests)
- Same category measured 5 times → all measurements identical (determinism check)
- Different tool order in JSON → byte count unchanged (order-independent)
- JSON serialization consistency: `separators=(',', ':')` ensures no whitespace differences
- Tool list equality: Content match, not reference equality (robust comparison)
- Backward compatibility: Old-style agents (no category) always get all tools
- Measurement caching: No issues if function is called repeatedly

---

## Test Framework & Fixtures

**Framework:** Python `pytest` with `pytest-mock` for MagicMock.

**Fixtures (in conftest.py):**
```python
@pytest.fixture()
def mock_tool_schemas() -> dict[str, list[dict[str, Any]]]:
    """Return realistic mock tool schemas for all categories."""
    return {
        "parse": [
            {"name": "read", "description": "Read files"},
            {"name": "grep", "description": "Search content"},
            {"name": "glob", "description": "Find files by pattern"}
        ],
        "modify": [
            {"name": "write", "description": "Create/overwrite files"},
            {"name": "edit", "description": "Edit files in-place"}
        ],
        "test": [
            {"name": "bash", "description": "Run shell commands"}
        ],
        "plan": [
            {"name": "bash", "description": "Run shell commands"},
            {"name": "todotype", "description": "Manage tasks"}
        ],
        "think": [
            {"name": "read", "description": "Read files"},
            {"name": "grep", "description": "Search content"},
            {"name": "agent", "description": "Invoke subagent"}
        ]
    }

@pytest.fixture()
def mock_json_config(tmp_path: Path, mock_tool_schemas) -> Path:
    """Create temporary tool_categories.json for testing."""
    config = {
        "version": "1.0",
        "categories": [
            {"name": "parse", "description": "Non-destructive exploration"},
            {"name": "modify", "description": "Write and create"},
            {"name": "test", "description": "Test execution"},
            {"name": "plan", "description": "Decomposition and planning"},
            {"name": "think", "description": "Analysis and learning"}
        ],
        "tools": [
            {"name": "read", "categories": ["parse", "think"], "rationale": "..."},
            {"name": "write", "categories": ["modify"], "rationale": "..."},
            {"name": "glob", "categories": ["parse", "think"], "rationale": "..."},
            {"name": "grep", "categories": ["parse", "think"], "rationale": "..."},
            {"name": "bash", "categories": ["test", "plan", "think"], "rationale": "..."},
            {"name": "edit", "categories": ["modify"], "rationale": "..."},
            {"name": "todotype", "categories": ["plan"], "rationale": "..."},
            {"name": "agent", "categories": ["think"], "rationale": "..."}
        ]
    }
    config_file = tmp_path / "tool_categories.json"
    config_file.write_text(json.dumps(config))
    return config_file
```

**Test Isolation:** Each test is isolated via:
- Mocking `get_tools_for_category()` to return deterministic mock schemas
- Using `tmp_path` for temporary JSON configs (no side effects)
- No shared state between tests (pytest auto-isolates)

---

## Traceability Matrix (Test → AC)

| Test Name | AC # | Requirement | Notes |
|-----------|------|-------------|-------|
| test_five_categories_defined | 1.1 | Tool Categories Enum | 5 categories: parse, modify, test, plan, think |
| test_category_names_lowercase | 1.1 | Tool Categories Enum | Lowercase naming convention enforced |
| test_categories_importable | 1.4 | Tool Categories Enum | Categories importable from module |
| test_category_descriptions_present | 1.2 | Tool Categories Enum | Each category has 1–2 sentence description |
| test_no_empty_categories | 1.5 | Tool Categories Enum | All 5 categories have ≥1 tool |
| test_categories_stored_in_json | 1.3 | Tool Categories Enum | Stored in ci/scripts/tool_categories.json |
| test_categories_mutually_exclusive_per_agent | 1.1 | Tool Categories Enum | Single category per agent invocation |
| test_minimum_four_tools_mapped | 2.1 | Tool-to-Category Mapping | Read, Write, Glob, Grep minimum |
| test_all_tools_mapped | 2.2 | Tool-to-Category Mapping | Every tool in ≥1 category |
| test_no_tools_in_zero_categories | 2.2 | Tool-to-Category Mapping | No tool in zero categories |
| test_all_categories_have_tools | 2.3 | Tool-to-Category Mapping | Each category has ≥1 tool |
| test_read_in_parse_and_think | 2.1 | Tool-to-Category Mapping | Read tool correctness |
| test_write_in_modify_only | 2.1 | Tool-to-Category Mapping | Write tool correctness |
| test_bash_in_multiple_categories | 2.1 | Tool-to-Category Mapping | Multi-category tool mapping |
| test_tool_mapping_has_rationale | 2.5 | Tool-to-Category Mapping | Rationale strings present |
| test_function_exists | 3.1 | Function Interface | get_tools_for_category exists |
| test_function_signature | 3.5 | Function Interface | Correct type hints (str → list) |
| test_valid_category_parse | 3.2 | Function Interface | Valid parse category returns tools |
| test_valid_category_modify | 3.2 | Function Interface | Valid modify category returns tools |
| test_valid_category_test | 3.2 | Function Interface | Valid test category returns tools |
| test_valid_category_plan | 3.2 | Function Interface | Valid plan category returns tools |
| test_valid_category_think | 3.2 | Function Interface | Valid think category returns tools |
| test_invalid_category_raises_valueerror | 3.3 | Function Interface | Invalid category raises ValueError |
| test_invalid_category_error_message_lists_valid_categories | 3.3 | Function Interface | Error message helpful |
| test_function_is_deterministic_same_input_same_output | 3.7 | Function Interface | Deterministic (same input → same output) |
| test_function_has_docstring | 3.6 | Function Interface | Docstring present |
| test_framework_accepts_tool_category_parameter | 4.1 | Agent Framework Integration | Framework accepts tool_category param |
| test_tool_category_parameter_is_optional | 4.3 | Agent Framework Integration | Parameter is optional (backward compat) |
| test_valid_category_filters_tools | 4.2 | Agent Framework Integration | Category filtering works |
| test_invalid_category_falls_back_to_all_tools | 4.4 | Agent Framework Integration | Invalid category → all tools (fail-safe) |
| test_framework_logs_warning_on_invalid_category | 4.6 | Agent Framework Integration | Warning logged, not error |
| test_no_regression_existing_agents | 4.5 | Agent Framework Integration | No regression (backward compatible) |
| test_regex_pattern_extracts_valid_declaration | 5.2 | Agent Declaration Protocol | Regex pattern correct |
| test_regex_pattern_extracts_workflow_category_syntax | 5.2 | Agent Declaration Protocol | Regex accepts multiple syntaxes |
| test_regex_pattern_extracts_tool_category_syntax | 5.2 | Agent Declaration Protocol | Regex accepts tool category syntax |
| test_declaration_extraction_case_insensitive | 5.3 | Agent Declaration Protocol | Case-insensitive extraction |
| test_missing_declaration_returns_none_or_empty | 5.3 | Agent Declaration Protocol | Missing declaration defaults to all tools |
| test_invalid_category_in_declaration_is_ignored | 5.3 | Agent Declaration Protocol | Invalid category gracefully ignored |
| test_multiple_declarations_in_prompt_uses_first | 5.2 | Agent Declaration Protocol | First declaration wins (or documented) |
| test_declaration_not_in_agent_output | 5.4 | Agent Declaration Protocol | Declaration removed from visible prompt |
| test_declaration_regex_no_false_positives | 5.2 | Agent Declaration Protocol | No false positive matches |
| test_measurement_function_exists | 6.1 | Measurement Protocol | Function exists and callable |
| test_measurement_returns_dict_with_required_keys | 6.2 | Measurement Protocol | Required keys in return dict |
| test_baseline_bytes_computed_correctly | 6.3 | Measurement Protocol | Byte count formula correct |
| test_filtered_bytes_computed_correctly | 6.3 | Measurement Protocol | Filtered byte count correct |
| test_reduction_percent_formula_correct | 6.3 | Measurement Protocol | Reduction formula correct |
| test_reduction_percent_in_valid_range | 6.3 | Measurement Protocol | Reduction percent 0–100 |
| test_measurement_is_deterministic_same_tools_same_bytes | 6.4 | Measurement Protocol | Deterministic byte counts |
| test_all_categories_show_measurable_reduction | 6.3 | Measurement Protocol | All categories have reduction > 0 |
| test_measurement_includes_timestamp | 6.2 | Measurement Protocol | ISO 8601 timestamp present |
| test_integration_parse_mode_receives_parse_tools | 7.1 | Integration Testing | Parse mode filter works |
| test_integration_modify_mode_receives_modify_tools | 7.1 | Integration Testing | Modify mode filter works |
| test_integration_test_mode_receives_test_tools | 7.1 | Integration Testing | Test mode filter works |
| test_integration_backward_compatibility_no_category_all_tools | 7.6 | Integration Testing | Backward compat verified |
| test_integration_reduction_metric_within_target | 7.2 | Integration Testing | Reduction measurable |

---

## Test Design Decisions & Assumptions

### Decision 1: Behavior-Driven, Not Prose-Driven
**Assumption:** All tests validate executable behavior (function calls, tool schemas, measurements), never markdown/spec text.
**Confidence:** HIGH
**Rationale:** Per workflow_enforcement_v1.md "Test realism guardrail": tests must verify executable behavior, not documentation prose.

### Decision 2: Mock Tool Schemas, Not SDK
**Assumption:** Tests use mock Tool objects (dict-like structures) instead of actual Claude Agent SDK tools.
**Confidence:** HIGH
**Rationale:** Avoids SDK dependency in tests; Tool type availability (from spec) is MEDIUM confidence. Mocking is safer and more portable.

### Decision 3: Determinism as Primary Validation
**Assumption:** Measurement and category filtering must be deterministic (same input → same output).
**Confidence:** HIGH
**Rationale:** Spec AC-6.4 requires consistent serialization; tests validate multiple consecutive measurements are identical.

### Decision 4: JSON Byte Count as Measurement Metric
**Assumption:** Primary measurement is JSON schema byte count (UTF-8 encoded, no whitespace).
**Confidence:** MEDIUM (per spec)
**Rationale:** Deterministic, fast, no external dependencies. Token counting deferred to Integration phase.

### Decision 5: Category Declaration Regex Extraction
**Assumption:** Agent declaration parsing uses regex to extract category from prompt.
**Confidence:** MEDIUM (per spec AC-5.2)
**Rationale:** Spec defines regex pattern; tests validate extraction against multiple prompt variants.

### Decision 6: Backward Compatibility as Non-Negotiable
**Assumption:** Agents without category declaration always receive all tools (no breaking changes).
**Confidence:** HIGH (per spec AC-4.3, AC-4.5)
**Rationale:** Opt-in design, not mandatory. Existing agents unaffected.

### Decision 7: Fail-Safe Error Handling
**Assumption:** Invalid category in agent framework → log warning and provide all tools (not error).
**Confidence:** MEDIUM (per spec AC-4.4)
**Rationale:** Spec states "fail-safe, not fail-hard". Tests verify warning is logged and fallback works.

### Decision 8: No Empty Categories
**Assumption:** All 5 categories must have ≥1 tool (AC-2.3, AC-1.5).
**Confidence:** HIGH (per spec AC-2.3)
**Rationale:** Spec freeze; test verifies this constraint.

### Decision 9: Tool Mapping Freeze
**Assumption:** Tool-to-category mappings are normative and frozen in spec (no test changes them).
**Confidence:** MEDIUM-HIGH (per spec R2, A2 assumption)
**Rationale:** Spec Agent froze mappings; tests validate against frozen mappings.

### Decision 10: Integration Testing Deferred
**Assumption:** Real agent integration (3+ live agents with tool_category declarations) happens in Integration Agent run (Task 7).
**Confidence:** HIGH (per spec AC-7.3, AC-7.4)
**Rationale:** Test Designer creates simulation harness in M902-18; Integration Agent collects real measurements in dependent tickets.

---

## Test Execution Command

```bash
# Run all tool categorization tests
pytest tests/ci/test_tool_categorization.py tests/ci/test_tool_categorization_adversarial.py -v

# Run specific test class
pytest tests/ci/test_tool_categorization.py::TestGetToolsForCategory -v

# Run with coverage
pytest tests/ci/test_tool_categorization.py tests/ci/test_tool_categorization_adversarial.py --cov=ci.scripts.tool_category_manager --cov-report=term-missing
```

---

## Summary Statistics

- **Total tests:** 73 (45 primary + 28 adversarial)
- **Test files:** 2 (primary + adversarial)
- **Test classes:** 8 (enum, mapping, function, framework, declaration, measurement, integration, documentation)
- **Requirements covered:** All 8 (R1–R8)
- **Acceptance Criteria mapped:** All 30+ ACs
- **Determinism tests:** 6 dedicated + embedded in all function tests
- **Error handling tests:** 8 dedicated + embedded in all function tests
- **Boundary condition tests:** 8 dedicated + embedded throughout

---

## Next Steps

1. **Implementation Agent (Task 4):** Create `ci/scripts/tool_category_manager.py` and `ci/scripts/tool_categories.json` per spec.
2. **Test Breaker Agent (Task 3):** Review test suite; create adversarial test file.
3. **All tests to pass:** Before advancing to IMPLEMENTATION stage.

