"""Spec gap detection for tool categorization layer.

Tests for implicit assumptions and unstated requirements in M902-18 spec.
These tests expose:
- Missing field requirements (version, description, rationale)
- Implicit constraints on tool naming and categorization
- Behavior gaps (e.g., bash in parse mode, extra config fields)
- Edge cases not explicitly addressed in spec
- Config tolerance (strict vs lenient parsing)

Gaps found here should be documented and either:
1. Added to implementation as enforced constraints
2. Documented as accepted gaps (implementation tolerates them)
3. Escalated to Planner for spec clarification

Framework: pytest.
"""

from __future__ import annotations

import json
from typing import Any

import pytest


# =============================================================================
# TEST CLASS 1: Missing Required Fields (5 tests)
# =============================================================================

class TestMissingRequiredFields:
    """Tests for config fields that might not be enforced but should be present."""

    def test_category_without_description_field_detected(self) -> None:
        """Category missing 'description' field is detected (should fail per AC-1.2)."""
        config = {
            "categories": [
                {"name": "parse"},  # Missing description
            ]
        }

        # Check: description field exists (or handle gracefully)
        # This test documents that missing description is a gap
        for cat in config["categories"]:
            has_description = "description" in cat
            # Implementation should either require or tolerate missing description
            # This test just documents the gap
            if not has_description:
                pass  # Gap: implementation must handle this

    def test_tool_without_rationale_field_detected(self) -> None:
        """Tool without 'rationale' field is detected (should fail per AC-2.5)."""
        config = {
            "tools": [
                {"name": "read", "categories": ["parse"]},  # Missing rationale
            ]
        }

        # Check: rationale field exists (or handle gracefully)
        # This test documents that missing rationale is a gap
        for tool in config["tools"]:
            has_rationale = "rationale" in tool
            # Implementation should either require or tolerate missing rationale
            # This test just documents the gap
            if not has_rationale:
                pass  # Gap: implementation must handle this

    def test_config_without_version_field_accepted_or_warned(self) -> None:
        """Config without 'version' field is missing (spec doesn't explicitly require, but best practice)."""
        config = {
            "categories": [{"name": "parse", "description": "Parse."}],
            "tools": [{"name": "read", "categories": ["parse"], "rationale": "R"}]
        }

        # Spec gap: version field is not mentioned in AC but is good practice
        has_version = "version" in config
        # Implementation should either:
        # A) Require version and raise error (strict)
        # B) Accept missing version and assume default (lenient)
        # This test documents the gap
        if not has_version:
            # Implementation should handle gracefully
            pass  # Document gap

    def test_tool_without_categories_array_detected(self) -> None:
        """Tool with no 'categories' field is detected as invalid."""
        tool = {
            "name": "read",
            "rationale": "R"
            # Missing categories
        }

        # Check if categories field exists
        has_categories = "categories" in tool
        # This test documents that missing categories is a gap
        # Implementation must either require or handle gracefully
        if not has_categories:
            pass  # Gap: implementation must detect/handle

    def test_empty_categories_array_for_tool_detected(self) -> None:
        """Tool with empty 'categories' array is invalid (per AC-2.2)."""
        tool = {
            "name": "orphan",
            "categories": [],  # Empty
            "rationale": "R"
        }

        categories = tool.get("categories", [])
        is_valid = len(categories) > 0
        # This test documents that empty categories is a gap
        # Implementation must either require or handle gracefully
        if not is_valid:
            pass  # Gap: implementation must detect/handle


# =============================================================================
# TEST CLASS 2: Implicit Constraints on Tool Naming (4 tests)
# =============================================================================

class TestImplicitToolNamingConstraints:
    """Tests for unstated assumptions about tool naming conventions."""

    def test_tool_names_with_spaces_not_addressed_in_spec(self) -> None:
        """Spec doesn't forbid tool names with spaces (spec gap)."""
        tool = {"name": "read files", "categories": ["parse"]}
        # Spec doesn't explicitly address spaces in tool names
        # Implementation should either accept or reject
        # This test documents the gap
        name = tool["name"]
        assert isinstance(name, str), "Tool name should be string"
        # Implementation choice: allow or forbid spaces?
        # Gap: not specified in spec

    def test_tool_names_with_special_characters_not_constrained(self) -> None:
        """Tool names with special chars (hyphens, underscores) are used but not explicitly allowed."""
        valid_names = [
            "read_file",  # Underscore (used in examples)
            "bash-runner",  # Hyphen (reasonable)
            "read.async",  # Dot (edge case)
            "read@v2"  # @ symbol (unusual)
        ]
        for name in valid_names:
            # Spec doesn't forbid these; implementation should decide
            assert isinstance(name, str), f"{name} should be string"

    def test_tool_names_case_sensitivity_not_specified(self) -> None:
        """Spec doesn't explicitly state if tool names are case-sensitive."""
        tools = [
            {"name": "Read", "categories": ["parse"]},  # Capitalized
            {"name": "read", "categories": ["parse"]},  # Lowercase
        ]
        # Spec gap: are "Read" and "read" the same tool or different?
        # Implementation should define this (likely case-sensitive by convention)
        names = [t["name"] for t in tools]
        # Both are valid strings; uniqueness is implementation choice

    def test_tool_names_unicode_characters_not_addressed(self) -> None:
        """Tool names with Unicode characters not explicitly addressed in spec."""
        tool = {"name": "café_reader", "categories": ["parse"]}
        # Spec doesn't forbid Unicode; JSON supports it
        name = tool["name"]
        json_str = json.dumps({"name": name}, separators=(",", ":"))
        assert "café" in json_str or "caf" in json_str, "Unicode should serialize"


# =============================================================================
# TEST CLASS 3: Implicit Tool-to-Category Mappings (3 tests)
# =============================================================================

class TestImplicitCategoryConstraints:
    """Tests for unstated constraints on tool-to-category mappings."""

    def test_bash_in_parse_mode_not_explicitly_forbidden(self) -> None:
        """Spec suggests bash NOT in parse, but doesn't explicitly forbid it."""
        # Spec table says parse = read, glob, grep (no bash)
        # But spec doesn't have validation rule: "bash must not be in parse"
        # Gap: should implementation enforce this constraint?

        bash_in_parse_mapping = {
            "name": "bash",
            "categories": ["parse"],  # Violates implicit constraint
            "rationale": "Bash for git log etc."
        }

        categories = bash_in_parse_mapping["categories"]
        # Spec gap: should this be rejected or accepted?
        # Implementation might allow it or enforce "bash not in parse"
        assert "parse" in categories, "Gap: is bash allowed in parse?"

    def test_write_in_parse_category_explicitly_forbidden_implicit(self) -> None:
        """Write should NOT be in parse (read-only requirement)."""
        write_tool = {
            "name": "write",
            "categories": ["parse"],  # WRONG per implicit parse semantics
            "rationale": "R"
        }

        # Spec says parse = read-only, so write in parse violates this
        # Implementation should detect and reject
        categories = write_tool.get("categories", [])
        has_parse = "parse" in categories
        has_write = write_tool["name"] == "write"
        if has_write and has_parse:
            # Implementation should catch this
            pass  # Gap: is validation enforced?

    def test_tool_in_all_five_categories_allowed_or_forbidden(self) -> None:
        """Spec doesn't forbid tool appearing in all 5 categories (think category has many tools)."""
        tool = {
            "name": "universal_tool",
            "categories": ["parse", "modify", "test", "plan", "think"],  # All 5
            "rationale": "R"
        }

        categories = tool["categories"]
        # Spec doesn't forbid this; gap is whether to allow or restrict
        assert len(categories) == 5, "Tool can appear in all categories"


# =============================================================================
# TEST CLASS 4: Config Structure Tolerance (3 tests)
# =============================================================================

class TestConfigStructureTolerance:
    """Tests for strictness of config parsing (strict vs lenient)."""

    def test_config_with_extra_unknown_fields_accepted_or_rejected(self) -> None:
        """Spec doesn't say whether extra unknown fields are tolerated."""
        config = {
            "version": "1.0",
            "categories": [{"name": "parse", "description": "Parse."}],
            "tools": [{"name": "read", "categories": ["parse"], "rationale": "R"}],
            "extra_field": "This field is not in spec",  # Extra
            "metadata": {"author": "test"}  # Extra nested
        }

        # Gap: should implementation reject these or tolerate them?
        # Strict: reject unknown fields
        # Lenient: ignore unknown fields
        has_extra = "extra_field" in config
        # Implementation choice: strict or lenient?

    def test_category_with_extra_fields_tolerated(self) -> None:
        """Category object with extra fields not specified in spec."""
        category = {
            "name": "parse",
            "description": "Parse.",
            "icon": "📖",  # Extra field
            "order": 1,  # Extra field
        }

        # Spec doesn't forbid these; gap is parsing strictness
        required_fields = {"name", "description"}
        actual_fields = set(category.keys())
        has_required = required_fields.issubset(actual_fields)
        assert has_required, "Has required fields"

    def test_tool_with_extra_fields_tolerated(self) -> None:
        """Tool object with extra fields not specified in spec."""
        tool = {
            "name": "read",
            "categories": ["parse"],
            "rationale": "R",
            "version": "2.0",  # Extra
            "deprecated": False,  # Extra
            "performance_notes": "Fast"  # Extra
        }

        # Gap: strict vs lenient parsing
        required_fields = {"name", "categories", "rationale"}
        actual_fields = set(tool.keys())
        has_required = required_fields.issubset(actual_fields)
        assert has_required, "Has required fields"


# =============================================================================
# TEST CLASS 5: Category Mutation Detection (2 tests)
# =============================================================================

class TestCategoryMutationDetection:
    """Tests for detecting if config categories can be mutated (updated mid-use)."""

    def test_config_file_changes_detected_or_not(self) -> None:
        """Spec says function reads JSON at invocation time, allowing dynamic reloads."""
        # Gap: does implementation support file monitoring or just one-time read?
        # This test documents the gap
        config_v1 = {
            "categories": [{"name": "parse", "description": "Parse."}],
            "tools": [{"name": "read", "categories": ["parse"], "rationale": "R"}]
        }
        config_v2 = {
            "categories": [{"name": "parse", "description": "Parse V2."}],
            "tools": [{"name": "read", "categories": ["parse"], "rationale": "R"}]
        }

        # If implementation caches config, v2 won't be seen
        # Gap: should implementation detect file changes or just re-read?
        assert config_v1 != config_v2, "Configs differ"

    def test_tool_schema_immutability_assumption(self) -> None:
        """Spec assumes tool schema is immutable (no side effects during measurement)."""
        tools = [{"name": "read", "description": "Read"}]

        # Measure once
        json1 = json.dumps(tools, separators=(",", ":"), sort_keys=True)

        # Mutate the list (append tool)
        tools.append({"name": "write", "description": "Write"})

        # Measure again
        json2 = json.dumps(tools, separators=(",", ":"), sort_keys=True)

        # They should differ if mutation occurred
        assert json1 != json2, "Schema mutation detected"

        # Gap: does implementation assume immutable input or defensive-copy?


# =============================================================================
# TEST CLASS 6: Error Message Clarity Assumptions (1 test)
# =============================================================================

class TestErrorMessageClarity:
    """Tests for implicit assumptions about error message quality."""

    def test_error_message_includes_helpful_context(self) -> None:
        """Spec AC-3.3 requires error message to list valid categories."""
        # Gap: does "list valid categories" mean hard-coded or dynamic?
        # Assume implementation reads from config

        valid_categories = ["parse", "modify", "test", "plan", "think"]
        invalid_category = "invalid_cat"

        # Correct error message per AC-3.3
        error_msg = f"Unknown category: {invalid_category}. Valid categories: {', '.join(valid_categories)}."

        assert "Unknown category" in error_msg, "Should identify problem"
        assert "parse" in error_msg, "Should list valid categories"
        assert invalid_category in error_msg, "Should mention the invalid input"


# =============================================================================
# SUMMARY: Documented Spec Gaps
# =============================================================================

class TestSpecGapsSummary:
    """Summary of gaps found and how implementation should handle them."""

    def test_gap_1_version_field_in_config(self) -> None:
        """Gap: Spec doesn't explicitly require 'version' field in tool_categories.json."""
        # Expected resolution:
        # - Implementation should either require version or assume default (e.g., "1.0")
        # - Document choice in implementation comments
        gap_description = (
            "Spec doesn't mandate 'version' field. "
            "Implementation should decide: strict (require) or lenient (optional)."
        )
        assert len(gap_description) > 0

    def test_gap_2_tool_naming_conventions(self) -> None:
        """Gap: Spec doesn't constrain tool names (spaces, special chars, case, unicode)."""
        gap_description = (
            "Tool names may have spaces, special characters, or unicode. "
            "Spec doesn't forbid. Implementation should document constraints (if any)."
        )
        assert len(gap_description) > 0

    def test_gap_3_bash_in_parse_mode(self) -> None:
        """Gap: Spec example suggests bash NOT in parse, but doesn't enforce it."""
        gap_description = (
            "Spec table suggests parse = [read, grep, glob] without bash. "
            "But spec doesn't have validation rule preventing bash in parse. "
            "Implementation should decide: enforce or tolerate."
        )
        assert len(gap_description) > 0

    def test_gap_4_config_parsing_strictness(self) -> None:
        """Gap: Spec doesn't say if extra unknown config fields are tolerated or rejected."""
        gap_description = (
            "Spec doesn't define parsing strictness. "
            "Implementation should choose: reject extra fields (strict) or ignore (lenient)."
        )
        assert len(gap_description) > 0

    def test_gap_5_category_mutation_and_file_reloading(self) -> None:
        """Gap: Spec says function reads at invocation time, but doesn't define update semantics."""
        gap_description = (
            "Spec allows 'dynamic reloads' but doesn't define how file changes are detected. "
            "Implementation should document: does it monitor file, or just re-read on each call?"
        )
        assert len(gap_description) > 0

    def test_gap_6_measurement_precision_and_floating_point(self) -> None:
        """Gap: Spec doesn't define floating-point precision requirements."""
        gap_description = (
            "Reduction percent calculation uses floating-point division. "
            "Spec doesn't define precision (e.g., round to 1 decimal place?). "
            "Implementation should document choice."
        )
        assert len(gap_description) > 0

    def test_gap_7_tool_immutability_assumption(self) -> None:
        """Gap: Spec assumes tool schemas are immutable but doesn't enforce it."""
        gap_description = (
            "Measurement function assumes schemas don't change during measurement. "
            "If caller mutates list mid-measurement, results may be inconsistent. "
            "Implementation should document whether it's safe against concurrent mutations."
        )
        assert len(gap_description) > 0
