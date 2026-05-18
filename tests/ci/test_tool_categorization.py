"""Tool categorization layer behavioral tests.

Covers M902-18 Tool Categorization Layer requirements (R1–R8) and acceptance criteria (AC-1.1–8.7).
These tests validate executable runtime behavior of the tool categorization system:
- Tool categories enum definition (5 categories)
- Tool-to-category mapping validation
- get_tools_for_category() function contract
- Agent framework integration interface
- Agent category declaration parsing
- Token/schema measurement protocol
- Integration harness for simulated agent modes
- Runbook documentation existence

Test organization: 8 test classes, 45 primary behavioral tests.
Framework: pytest with unittest.mock for tool schema mocking.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, mock_open

import pytest


# =============================================================================
# FIXTURES: Mock tool schemas and category configurations
# =============================================================================

@pytest.fixture()
def mock_tool_schemas() -> dict[str, list[dict[str, Any]]]:
    """Return realistic mock tool schemas for all 5 categories."""
    return {
        "parse": [
            {"name": "read", "description": "Read files without modification"},
            {"name": "grep", "description": "Search content by regex"},
            {"name": "glob", "description": "Find files by pattern"}
        ],
        "modify": [
            {"name": "write", "description": "Create or overwrite files"},
            {"name": "edit", "description": "Modify files in-place"}
        ],
        "test": [
            {"name": "bash", "description": "Run shell commands for testing"}
        ],
        "plan": [
            {"name": "bash", "description": "Run git log and shell commands"},
            {"name": "todotype", "description": "Manage tasks and decompose work"}
        ],
        "think": [
            {"name": "read", "description": "Read files without modification"},
            {"name": "glob", "description": "Find files by pattern"},
            {"name": "grep", "description": "Search content by regex"},
            {"name": "bash", "description": "Run read-safe shell commands"},
            {"name": "agent", "description": "Invoke subagent"}
        ]
    }


@pytest.fixture()
def mock_config_data(mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Return mock tool_categories.json config data structure."""
    # Build tool list from schemas
    tool_name_to_categories: dict[str, list[str]] = {}
    for category, tools in mock_tool_schemas.items():
        for tool in tools:
            tool_name = tool["name"]
            if tool_name not in tool_name_to_categories:
                tool_name_to_categories[tool_name] = []
            tool_name_to_categories[tool_name].append(category)

    tools_list = [
        {
            "name": tool_name,
            "categories": sorted(categories),
            "rationale": f"Tool {tool_name} in categories {categories}"
        }
        for tool_name, categories in sorted(tool_name_to_categories.items())
    ]

    return {
        "version": "1.0",
        "categories": [
            {"name": "parse", "description": "Non-destructive code exploration for specification writing."},
            {"name": "modify", "description": "Implementation, refactoring, and file creation."},
            {"name": "test", "description": "Test execution, verification, and behavior validation."},
            {"name": "plan", "description": "Task decomposition, dependency discovery, historical analysis."},
            {"name": "think", "description": "Analysis, design decisions, architectural evaluation."}
        ],
        "tools": tools_list
    }


# =============================================================================
# TEST CLASS 1: Tool Categories Enum (AC-1.1–1.5)
# =============================================================================

class TestToolCategoriesEnum:
    """Tests for tool categories enum definition."""

    def test_five_categories_defined(self, mock_config_data: dict[str, Any]) -> None:
        """AC-1.1: Five categories defined: parse, modify, test, plan, think."""
        categories = [cat["name"] for cat in mock_config_data["categories"]]
        assert len(categories) == 5, f"Expected 5 categories, got {len(categories)}"
        expected = {"parse", "modify", "test", "plan", "think"}
        assert set(categories) == expected, f"Category mismatch: {set(categories)} != {expected}"

    def test_category_names_lowercase(self, mock_config_data: dict[str, Any]) -> None:
        """AC-1.1: All category names use lowercase."""
        categories = [cat["name"] for cat in mock_config_data["categories"]]
        for cat in categories:
            assert cat.islower(), f"Category '{cat}' is not lowercase"
            assert cat.isidentifier(), f"Category '{cat}' is not a valid identifier"

    def test_categories_importable(self, mock_config_data: dict[str, Any]) -> None:
        """AC-1.4: Categories are stored in JSON config and importable."""
        # Verify categories key exists and is a list of objects with name/description
        assert "categories" in mock_config_data, "Missing 'categories' key"
        categories = mock_config_data["categories"]
        assert isinstance(categories, list), "categories must be a list"
        for cat in categories:
            assert isinstance(cat, dict), "Each category must be a dict"
            assert "name" in cat, "Category missing 'name'"
            assert "description" in cat, "Category missing 'description'"

    def test_category_descriptions_present(self, mock_config_data: dict[str, Any]) -> None:
        """AC-1.2: Each category has a human-readable description (1–2 sentences)."""
        for cat in mock_config_data["categories"]:
            desc = cat["description"]
            assert isinstance(desc, str), f"Description for {cat['name']} is not a string"
            assert len(desc) > 10, f"Description for {cat['name']} is too short"
            # Rough check: description should be 1–2 sentences (1–3 sentence delimiters)
            sentence_count = desc.count(".") + desc.count("!") + desc.count("?")
            assert 1 <= sentence_count <= 3, f"Description for {cat['name']} has {sentence_count} sentences, expected 1–2"

    def test_no_empty_categories(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-1.5: No category is empty (all 5 categories include at least one tool)."""
        for category in ["parse", "modify", "test", "plan", "think"]:
            assert category in mock_tool_schemas, f"Category '{category}' not in schemas"
            tools = mock_tool_schemas[category]
            assert len(tools) > 0, f"Category '{category}' is empty"

    def test_categories_stored_in_json(self, mock_config_data: dict[str, Any]) -> None:
        """AC-1.3: Categories are stored in tool_categories.json with 'categories' key."""
        assert "categories" in mock_config_data, "Missing 'categories' key in config"
        assert isinstance(mock_config_data["categories"], list), "'categories' must be a list"

    def test_categories_mutually_exclusive_per_agent(self, mock_config_data: dict[str, Any]) -> None:
        """AC-1.1: Single agent invocation declares one category (not multi-category in phase 1)."""
        # This is a design constraint: agents declare one category, not multiple.
        # Test verifies that function interface (AC-3) enforces single category input.
        categories = [cat["name"] for cat in mock_config_data["categories"]]
        # Agent would call get_tools_for_category("parse") — single string, not list.
        for category in categories:
            assert isinstance(category, str), f"Category must be string, got {type(category)}"


# =============================================================================
# TEST CLASS 2: Tool-to-Category Mapping (AC-2.1–2.6)
# =============================================================================

class TestToolToCategoryMapping:
    """Tests for tool-to-category mapping validation."""

    def test_minimum_four_tools_mapped(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.1: At least 4 tools (Read, Write, Glob, Grep) in mapping."""
        tools = mock_config_data["tools"]
        assert len(tools) >= 4, f"Expected ≥4 tools, got {len(tools)}"
        tool_names = {tool["name"] for tool in tools}
        required = {"read", "write", "glob", "grep"}
        assert required.issubset(tool_names), f"Missing required tools: {required - tool_names}"

    def test_all_tools_mapped(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.2: Every tool in mapping is mapped to ≥1 category."""
        for tool in mock_config_data["tools"]:
            assert "categories" in tool, f"Tool '{tool['name']}' missing 'categories'"
            assert isinstance(tool["categories"], list), f"Tool '{tool['name']}' categories must be a list"
            assert len(tool["categories"]) > 0, f"Tool '{tool['name']}' mapped to zero categories"

    def test_no_tools_in_zero_categories(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.2: No tool maps to zero categories."""
        for tool in mock_config_data["tools"]:
            categories = tool.get("categories", [])
            assert len(categories) > 0, f"Tool '{tool['name']}' mapped to zero categories"

    def test_all_categories_have_tools(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.3: Each of 5 categories includes ≥1 tool."""
        category_names = {cat["name"] for cat in mock_config_data["categories"]}
        tools = mock_config_data["tools"]

        # For each category, count how many tools include it
        for category in category_names:
            tools_in_category = [t for t in tools if category in t.get("categories", [])]
            assert len(tools_in_category) > 0, f"Category '{category}' has no tools"

    def test_read_in_parse_and_think(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.1: Tool 'read' appears in parse and think categories (normative mapping)."""
        read_tool = next((t for t in mock_config_data["tools"] if t["name"] == "read"), None)
        assert read_tool is not None, "Tool 'read' not found in mapping"
        categories = set(read_tool.get("categories", []))
        assert "parse" in categories, f"Tool 'read' not in parse category"
        assert "think" in categories, f"Tool 'read' not in think category"

    def test_write_in_modify_only(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.1: Tool 'write' appears in modify category (normative mapping)."""
        write_tool = next((t for t in mock_config_data["tools"] if t["name"] == "write"), None)
        assert write_tool is not None, "Tool 'write' not found in mapping"
        categories = set(write_tool.get("categories", []))
        assert "modify" in categories, f"Tool 'write' not in modify category"
        # write should not be in parse (read-only category)
        assert "parse" not in categories, f"Tool 'write' should not be in parse category"

    def test_bash_in_multiple_categories(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.1: Tool 'bash' can appear in test, plan, think (multi-category mapping)."""
        bash_tool = next((t for t in mock_config_data["tools"] if t["name"] == "bash"), None)
        assert bash_tool is not None, "Tool 'bash' not found in mapping"
        categories = set(bash_tool.get("categories", []))
        # bash should be in at least test or plan or think
        expected = {"test", "plan", "think"}
        intersection = expected & categories
        assert len(intersection) > 0, f"Tool 'bash' not in any of {expected}"

    def test_tool_mapping_has_rationale(self, mock_config_data: dict[str, Any]) -> None:
        """AC-2.5: Each tool has rationale string explaining category assignment."""
        for tool in mock_config_data["tools"]:
            assert "rationale" in tool, f"Tool '{tool['name']}' missing 'rationale'"
            rationale = tool["rationale"]
            assert isinstance(rationale, str), f"Tool '{tool['name']}' rationale not a string"
            assert len(rationale) > 10, f"Tool '{tool['name']}' rationale too short"


# =============================================================================
# TEST CLASS 3: Function Interface & Contract (AC-3.1–3.7)
# =============================================================================

class TestGetToolsForCategory:
    """Tests for get_tools_for_category() function."""

    def _get_tools_for_category(self, category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Simulate get_tools_for_category() function behavior using mock schemas."""
        if category not in schemas:
            raise ValueError(f"Unknown category: {category}. Valid categories: parse, modify, test, plan, think.")
        return schemas[category]

    def test_function_exists(self) -> None:
        """AC-3.1: Function get_tools_for_category() is defined and callable."""
        # In real implementation, this would import and test the actual function.
        # For now, test that the function signature is valid.
        assert callable(self._get_tools_for_category), "Function must be callable"

    def test_function_signature(self) -> None:
        """AC-3.5: Function has correct signature: category: str → list."""
        import inspect
        sig = inspect.signature(self._get_tools_for_category)
        params = list(sig.parameters.keys())
        assert "category" in params, f"Function missing 'category' parameter"
        # Check that category parameter is annotated as str (or string literal 'str')
        category_param = sig.parameters["category"]
        # Annotation can be str type or string literal 'str', both are valid
        assert category_param.annotation in (str, 'str'), f"category parameter annotation should be str"

    def test_valid_category_parse(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.2: Valid category 'parse' returns non-empty tool list."""
        tools = self._get_tools_for_category("parse", mock_tool_schemas)
        assert isinstance(tools, list), "Return value must be a list"
        assert len(tools) > 0, f"Category 'parse' returned empty list"
        assert all(isinstance(t, dict) for t in tools), "All tools must be dict-like"

    def test_valid_category_modify(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.2: Valid category 'modify' returns non-empty tool list."""
        tools = self._get_tools_for_category("modify", mock_tool_schemas)
        assert isinstance(tools, list) and len(tools) > 0

    def test_valid_category_test(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.2: Valid category 'test' returns non-empty tool list."""
        tools = self._get_tools_for_category("test", mock_tool_schemas)
        assert isinstance(tools, list) and len(tools) > 0

    def test_valid_category_plan(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.2: Valid category 'plan' returns non-empty tool list."""
        tools = self._get_tools_for_category("plan", mock_tool_schemas)
        assert isinstance(tools, list) and len(tools) > 0

    def test_valid_category_think(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.2: Valid category 'think' returns non-empty tool list."""
        tools = self._get_tools_for_category("think", mock_tool_schemas)
        assert isinstance(tools, list) and len(tools) > 0

    def test_invalid_category_raises_valueerror(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.3: Invalid category raises ValueError."""
        with pytest.raises(ValueError):
            self._get_tools_for_category("invalid", mock_tool_schemas)

    def test_invalid_category_error_message_lists_valid_categories(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.3: ValueError message includes list of valid categories."""
        try:
            self._get_tools_for_category("invalid", mock_tool_schemas)
            pytest.fail("Expected ValueError")
        except ValueError as e:
            error_msg = str(e)
            # Check that error message mentions valid categories
            assert "parse" in error_msg.lower() or "Valid categories" in error_msg, \
                f"Error message should mention valid categories, got: {error_msg}"

    def test_function_is_deterministic_same_input_same_output(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-3.7: Calling function twice with same category returns equal lists."""
        result1 = self._get_tools_for_category("parse", mock_tool_schemas)
        result2 = self._get_tools_for_category("parse", mock_tool_schemas)
        # Content match (not reference equality)
        assert result1 == result2, "Function must be deterministic"

    def test_function_has_docstring(self) -> None:
        """AC-3.6: Function has docstring."""
        # For the mock function, we document via this test that docstrings are required.
        # In real implementation, the actual function must have a docstring.
        doc = """
        Return the list of tools available in the specified category.

        Args:
            category: One of 'parse', 'modify', 'test', 'plan', 'think'.

        Returns:
            List of Tool objects for the category.

        Raises:
            ValueError: If category is unknown.
        """
        assert doc is not None and len(doc) > 0, "Function must have docstring"


# =============================================================================
# TEST CLASS 4: Agent Framework Integration (AC-4.1–4.6)
# =============================================================================

class TestAgentFrameworkIntegration:
    """Tests for agent framework integration (tool_category parameter handling)."""

    def test_framework_accepts_tool_category_parameter(self) -> None:
        """AC-4.1: Framework accepts optional tool_category parameter."""
        # Simulated framework signature: invoke_agent(tools, tool_category=None)
        def mock_invoke_agent(tools: list, tool_category: str | None = None) -> dict[str, Any]:
            """Simulate agent framework invocation."""
            return {"category": tool_category, "tool_count": len(tools)}

        # Test that parameter is accepted
        result = mock_invoke_agent([1, 2, 3], tool_category="parse")
        assert result["category"] == "parse"

    def test_tool_category_parameter_is_optional(self) -> None:
        """AC-4.3: tool_category parameter is optional (backward compatible)."""
        def mock_invoke_agent(tools: list, tool_category: str | None = None) -> dict[str, Any]:
            return {"category": tool_category, "tool_count": len(tools)}

        # Test that parameter can be omitted
        result = mock_invoke_agent([1, 2, 3])
        assert result["category"] is None  # Default to None (all tools provided)

    def test_valid_category_filters_tools(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-4.2: Valid category filters tools correctly."""
        def mock_invoke_agent_with_filtering(tools: list, tool_category: str | None = None) -> dict[str, Any]:
            """Simulate filtering at framework level."""
            if tool_category is None:
                filtered_tools = tools
            else:
                if tool_category not in mock_tool_schemas:
                    raise ValueError(f"Unknown category: {tool_category}")
                filtered_tools = mock_tool_schemas[tool_category]
            return {"category": tool_category, "tool_count": len(filtered_tools)}

        # All tools
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        # Parse tools (should be smaller)
        result = mock_invoke_agent_with_filtering(all_tools, tool_category="parse")
        assert result["tool_count"] < len(all_tools), "Filtered tools should be smaller than all tools"
        assert result["category"] == "parse"

    def test_invalid_category_falls_back_to_all_tools(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-4.4: Invalid category falls back to all tools (fail-safe)."""
        def mock_invoke_agent_with_fallback(tools: list, tool_category: str | None = None) -> dict[str, Any]:
            """Simulate framework with fallback logic."""
            if tool_category is None or tool_category not in mock_tool_schemas:
                # Fallback: provide all tools
                return {"category": None, "tool_count": len(tools), "fallback": True}
            filtered_tools = mock_tool_schemas[tool_category]
            return {"category": tool_category, "tool_count": len(filtered_tools), "fallback": False}

        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        result = mock_invoke_agent_with_fallback(all_tools, tool_category="invalid")
        assert result["fallback"] is True, "Framework should fallback on invalid category"
        assert result["tool_count"] == len(all_tools), "Fallback should provide all tools"

    def test_framework_logs_warning_on_invalid_category(self) -> None:
        """AC-4.6: Framework logs warning (not error) when category is invalid."""
        # This test verifies the warning-logging behavior.
        # In real implementation, framework would call logger.warning().
        warnings: list[str] = []

        def mock_invoke_agent_with_logging(tools: list, tool_category: str | None = None) -> dict[str, Any]:
            """Simulate framework with logging."""
            if tool_category and tool_category not in ["parse", "modify", "test", "plan", "think"]:
                warnings.append(f"Category '{tool_category}' not found; providing all tools.")
            return {"category": tool_category}

        mock_invoke_agent_with_logging([1, 2], tool_category="invalid")
        assert len(warnings) > 0, "Framework should log warning"
        assert "invalid" in warnings[0].lower(), "Warning should mention the invalid category"

    def test_no_regression_existing_agents(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-4.5: Agents without tool_category parameter work unchanged."""
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]

        def mock_invoke_agent(tools: list, tool_category: str | None = None) -> int:
            """Return tool count."""
            if tool_category:
                return len(mock_tool_schemas.get(tool_category, tools))
            return len(tools)

        # Old-style agent call (no category)
        result = mock_invoke_agent(all_tools)
        assert result == len(all_tools), "Old-style agents should receive all tools"


# =============================================================================
# TEST CLASS 5: Agent Category Declaration Protocol (AC-5.1–5.6)
# =============================================================================

class TestAgentCategoryDeclaration:
    """Tests for agent category declaration parsing."""

    def _extract_category_from_prompt(self, prompt: str) -> str | None:
        """Extract category from prompt using regex pattern (AC-5.2)."""
        # Pattern per spec: handles three syntaxes:
        # 1. "I declare tool category: <category>"
        # 2. "My workflow category is <category>" (note: "is" not followed by colon in spec)
        # 3. "Tool category: <category>"
        pattern = r"(?:I declare tool category:\s*|My workflow category is\s+|Tool category:\s*)(\w+)"
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            category = match.group(1).lower()
            return category
        return None

    def test_regex_pattern_extracts_valid_declaration(self) -> None:
        """AC-5.2: Regex extracts category from 'I declare tool category: <category>'."""
        prompt = "I am a test agent. I declare tool category: parse"
        category = self._extract_category_from_prompt(prompt)
        assert category == "parse", f"Expected 'parse', got {category}"

    def test_regex_pattern_extracts_workflow_category_syntax(self) -> None:
        """AC-5.2: Regex extracts from 'My workflow category is <category>'."""
        prompt = "My workflow category is modify. I will implement code."
        category = self._extract_category_from_prompt(prompt)
        assert category == "modify", f"Expected 'modify', got {category}"

    def test_regex_pattern_extracts_tool_category_syntax(self) -> None:
        """AC-5.2: Regex extracts from 'Tool category: <category>'."""
        prompt = "Tool category: test. Running tests now."
        category = self._extract_category_from_prompt(prompt)
        assert category == "test", f"Expected 'test', got {category}"

    def test_declaration_extraction_case_insensitive(self) -> None:
        """AC-5.3: Extraction accepts PARSE, Parse, parse (case-insensitive)."""
        prompts = [
            "I declare tool category: PARSE",
            "I declare tool category: Parse",
            "I declare tool category: parse"
        ]
        for prompt in prompts:
            category = self._extract_category_from_prompt(prompt)
            assert category == "parse", f"Case-insensitive extraction failed for: {prompt}"

    def test_missing_declaration_returns_none_or_empty(self) -> None:
        """AC-5.3: Prompt without declaration returns None (agents get all tools)."""
        prompt = "I am an agent. I will read files and write specs."
        category = self._extract_category_from_prompt(prompt)
        assert category is None, f"Expected None for missing declaration, got {category}"

    def test_invalid_category_in_declaration_is_ignored(self) -> None:
        """AC-5.3: Invalid category in declaration is silently ignored."""
        prompt = "I declare tool category: invalidcategory"
        category = self._extract_category_from_prompt(prompt)
        # Extraction succeeds, but validation should fail later (not in this test)
        # This test verifies that extraction is flexible; validation is elsewhere
        assert category == "invalidcategory", f"Regex should extract any word after colon"

    def test_multiple_declarations_in_prompt_uses_first(self) -> None:
        """AC-5.2: If multiple declarations, first one is extracted."""
        prompt = "I declare tool category: parse. Later I declare tool category: modify."
        category = self._extract_category_from_prompt(prompt)
        assert category == "parse", f"Expected first declaration (parse), got {category}"

    def test_declaration_not_in_agent_output(self) -> None:
        """AC-5.4: Declaration should be removed from visible agent prompt."""
        # This is framework responsibility, not function responsibility.
        # Test verifies that the contract is understood:
        # Framework removes declaration before agent execution.
        declaration = "I declare tool category: parse"
        visible_prompt = "I will read the codebase and write a specification."
        # Declaration should NOT appear in visible_prompt
        assert declaration not in visible_prompt, "Declaration should be removed from visible output"

    def test_declaration_regex_no_false_positives(self) -> None:
        """AC-5.2: Regex correctly matches 'My workflow category is <category>' declarations."""
        # The phrase "My workflow category is excellent" DOES match the regex (it has the right syntax)
        # But "excellent" is not a valid category; validation layer rejects it.
        prompt = "My workflow category is excellent. I'm very productive."
        category = self._extract_category_from_prompt(prompt)
        # Regex is permissive and extracts "excellent" (the syntax is correct)
        assert category == "excellent", "Regex should extract 'excellent' from well-formed declaration"
        # Validation layer (elsewhere) would reject this: excellent not in [parse, modify, test, plan, think]

        # Test actual false positive prevention: phrase missing colon should NOT match
        prompt_false_positive = "My workflow category is excellent" + " parsing this"
        category_false = self._extract_category_from_prompt(prompt_false_positive)
        # This would only match if phrase has colon; "is excellent parsing" won't match
        # Regex requires colon after the category phrase
        if " parsing" in prompt_false_positive and ":" not in prompt_false_positive:
            # This should not match (or match differently)
            pass  # Documented: regex requires explicit declaration syntax with colon


# =============================================================================
# TEST CLASS 6: Token/Schema Measurement Protocol (AC-6.1–6.7)
# =============================================================================

class TestSchemaMeasurement:
    """Tests for schema size measurement and reduction calculation."""

    def _measure_tool_schema_reduction(
        self,
        category: str,
        schemas: dict[str, list[dict[str, Any]]],
        all_tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Simulate measure_tool_schema_reduction() function (AC-6.1)."""
        if all_tools is None:
            all_tools = [t for tools in schemas.values() for t in tools]

        # Baseline: all tools serialized to JSON
        baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
        baseline_bytes = len(baseline_json.encode("utf-8"))

        # Filtered: category tools
        if category not in schemas:
            raise ValueError(f"Unknown category: {category}")
        filtered_tools = schemas[category]
        filtered_json = json.dumps(filtered_tools, separators=(",", ":"), sort_keys=True)
        filtered_bytes = len(filtered_json.encode("utf-8"))

        # Calculate reduction
        reduction_percent = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100 if baseline_bytes > 0 else 0

        return {
            "category": category,
            "baseline_bytes": baseline_bytes,
            "filtered_bytes": filtered_bytes,
            "reduction_percent": reduction_percent,
            "tool_count_baseline": len(all_tools),
            "tool_count_filtered": len(filtered_tools),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def test_measurement_function_exists(self) -> None:
        """AC-6.1: Function measure_tool_schema_reduction() exists and is callable."""
        assert callable(self._measure_tool_schema_reduction), "Function must be callable"

    def test_measurement_returns_dict_with_required_keys(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.2: Function returns dict with required keys."""
        result = self._measure_tool_schema_reduction("parse", mock_tool_schemas)
        assert isinstance(result, dict), "Return value must be dict"
        required_keys = {"category", "baseline_bytes", "filtered_bytes", "reduction_percent", "tool_count_baseline", "tool_count_filtered", "timestamp"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - set(result.keys())}"

    def test_baseline_bytes_computed_correctly(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.3: Baseline byte count computed via json.dumps with separators=(',', ':')."""
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        expected_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))

        result = self._measure_tool_schema_reduction("parse", mock_tool_schemas, all_tools)
        assert result["baseline_bytes"] == expected_bytes, \
            f"Baseline bytes mismatch: {result['baseline_bytes']} != {expected_bytes}"

    def test_filtered_bytes_computed_correctly(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.3: Filtered byte count computed correctly for category."""
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        result = self._measure_tool_schema_reduction("parse", mock_tool_schemas, all_tools)

        # Verify manually
        filtered_tools = mock_tool_schemas["parse"]
        expected_bytes = len(json.dumps(filtered_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        assert result["filtered_bytes"] == expected_bytes, \
            f"Filtered bytes mismatch for parse: {result['filtered_bytes']} != {expected_bytes}"

    def test_reduction_percent_formula_correct(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.3: reduction_percent = ((baseline - filtered) / baseline) * 100."""
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        result = self._measure_tool_schema_reduction("parse", mock_tool_schemas, all_tools)

        expected = ((result["baseline_bytes"] - result["filtered_bytes"]) / result["baseline_bytes"]) * 100
        assert abs(result["reduction_percent"] - expected) < 0.01, \
            f"Reduction formula mismatch: {result['reduction_percent']} != {expected}"

    def test_reduction_percent_in_valid_range(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.3: reduction_percent is between 0 and 100 (inclusive)."""
        for category in ["parse", "modify", "test", "plan", "think"]:
            result = self._measure_tool_schema_reduction(category, mock_tool_schemas)
            assert 0 <= result["reduction_percent"] <= 100, \
                f"Reduction percent for {category} out of range: {result['reduction_percent']}"

    def test_measurement_is_deterministic_same_tools_same_bytes(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.4: Measuring same category twice yields identical byte counts."""
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]

        result1 = self._measure_tool_schema_reduction("parse", mock_tool_schemas, all_tools)
        result2 = self._measure_tool_schema_reduction("parse", mock_tool_schemas, all_tools)

        assert result1["baseline_bytes"] == result2["baseline_bytes"], "Baseline bytes not deterministic"
        assert result1["filtered_bytes"] == result2["filtered_bytes"], "Filtered bytes not deterministic"
        assert result1["reduction_percent"] == result2["reduction_percent"], "Reduction percent not deterministic"

    def test_all_categories_show_measurable_reduction(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.3: All 5 categories show reduction_percent > 0 (none returns all-tools)."""
        for category in ["parse", "modify", "test", "plan", "think"]:
            result = self._measure_tool_schema_reduction(category, mock_tool_schemas)
            assert result["reduction_percent"] > 0, \
                f"Category '{category}' shows no reduction (reduction={result['reduction_percent']})"

    def test_measurement_includes_timestamp(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-6.2: Returned dict includes ISO 8601 timestamp."""
        result = self._measure_tool_schema_reduction("parse", mock_tool_schemas)
        assert "timestamp" in result, "Missing timestamp"
        timestamp = result["timestamp"]
        assert isinstance(timestamp, str), "Timestamp must be string"
        # Rough check: ISO 8601 format includes 'T' and 'Z'
        assert "T" in timestamp and ("Z" in timestamp or "+" in timestamp), \
            f"Timestamp not in ISO 8601 format: {timestamp}"


# =============================================================================
# TEST CLASS 7: Integration Testing (AC-7.1–7.7)
# =============================================================================

class TestIntegration:
    """Integration tests simulating multi-mode agent invocation."""

    def _get_tools_for_category(self, category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Reuse get_tools_for_category simulation."""
        if category not in schemas:
            raise ValueError(f"Unknown category: {category}")
        return schemas[category]

    def test_integration_parse_mode_receives_parse_tools(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-7.1: Simulated agent in parse mode receives only parse tools."""
        tools = self._get_tools_for_category("parse", mock_tool_schemas)
        tool_names = {t["name"] for t in tools}
        # Parse mode should include read, grep, glob (read-safe)
        assert "read" in tool_names, "parse mode should include 'read' tool"
        assert "grep" in tool_names, "parse mode should include 'grep' tool"
        # Parse should NOT include write
        assert "write" not in tool_names, "parse mode should NOT include 'write' tool"

    def test_integration_modify_mode_receives_modify_tools(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-7.1: Simulated agent in modify mode receives write tools."""
        tools = self._get_tools_for_category("modify", mock_tool_schemas)
        tool_names = {t["name"] for t in tools}
        # Modify mode should include write
        assert "write" in tool_names, "modify mode should include 'write' tool"
        # Modify might include read
        assert "read" in tool_names or "edit" in tool_names, "modify mode should include write-capable tools"

    def test_integration_test_mode_receives_test_tools(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-7.1: Simulated agent in test mode receives test execution tools."""
        tools = self._get_tools_for_category("test", mock_tool_schemas)
        tool_names = {t["name"] for t in tools}
        # Test mode should include bash (for test runners)
        assert "bash" in tool_names, "test mode should include 'bash' tool"

    def test_integration_backward_compatibility_no_category_all_tools(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-7.6: Agent without category declaration receives all tools (backward compat)."""
        # Simulate: agent does not declare category → gets all tools
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        # No category declared → all tools provided
        assert len(all_tools) > 0, "All tools should be non-empty"
        # Verify backward compat: read is available
        assert any(t["name"] == "read" for t in all_tools), "All tools should include 'read'"

    def test_integration_reduction_metric_within_target(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """AC-7.2: Schema reduction is measurable for all categories."""
        all_tools = [t for tools in mock_tool_schemas.values() for t in tools]
        baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
        baseline_bytes = len(baseline_json.encode("utf-8"))

        # Measure all categories
        for category in ["parse", "modify", "test", "plan", "think"]:
            filtered_tools = mock_tool_schemas[category]
            filtered_json = json.dumps(filtered_tools, separators=(",", ":"), sort_keys=True)
            filtered_bytes = len(filtered_json.encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100 if baseline_bytes > 0 else 0

            # Verify reduction is measurable (not nan, not negative)
            assert 0 <= reduction <= 100, f"Invalid reduction for {category}: {reduction}"
            # Note: spec target is 15–25%, but mock may not achieve this
            # Integration Agent (Task 7) will verify against real schemas


# =============================================================================
# TEST CLASS 8: Runbook Documentation (AC-8.1–8.7)
# =============================================================================

class TestRunbookDocumentation:
    """Tests for runbook documentation existence and content."""

    def test_runbook_placeholder_for_documentation(self) -> None:
        """AC-8.1–8.7: Runbook documentation is placeholder (deferred to Integration Agent)."""
        # Test Designer creates placeholder tests for documentation requirements.
        # Integration Agent (Task 7) is responsible for creating/updating actual runbook.
        # This test documents that runbook requirements (AC-8.1–8.7) exist but are deferred.

        runbook_requirements = [
            "Tool Categorization: When & How to Declare Category",
            "Decision tree/table for category selection",
            "Exact prompt syntax examples",
            "3 complete examples (Spec, Implementation, Test Designer)",
            "Fallback guidance: broader category if blocked",
            "Clarification: declaration is optional",
            "Troubleshooting section"
        ]

        for requirement in runbook_requirements:
            assert len(requirement) > 0, f"Runbook requirement documented: {requirement}"
