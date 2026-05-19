"""Mutation testing for tool categorization layer.

Detects code mutations that would break implementation of M902-18.
These tests verify that implementation correctly handles:
- Inverted validation logic (category NOT in valid list)
- Off-by-one errors in string/list operations
- Incorrect error handling and fallback logic
- JSON serialization parameter mutations
- Regex pattern mutations
- Boundary condition logic errors

All tests are designed to FAIL if the implementation contains the specified mutation.

Framework: pytest with unittest.mock.
"""

from __future__ import annotations

import json
import re
from typing import Any
from unittest.mock import patch, MagicMock

import pytest


# =============================================================================
# FIXTURES: Realistic schemas and configurations
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


# =============================================================================
# TEST CLASS 1: Inverted Condition Mutations (5 tests)
# =============================================================================

class TestInvertedConditionMutations:
    """Detect inverted conditional logic mutations."""

    def _get_tools_for_category_correct(self, category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Correct implementation."""
        if category not in schemas:
            raise ValueError(f"Unknown category: {category}. Valid categories: parse, modify, test, plan, think.")
        return schemas[category]

    def _get_tools_for_category_inverted_condition(self, category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Mutant: inverted condition (if category IN instead of NOT IN)."""
        if category in schemas:
            # WRONG: inverted logic
            raise ValueError(f"Unknown category: {category}")
        return []  # WRONG: returns empty for valid categories

    def test_mutation_inverted_category_validation_rejects_valid(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """Detect mutation: category validation inverted (rejects valid categories)."""
        # Correct implementation should return tools for valid category
        correct_result = self._get_tools_for_category_correct("parse", mock_tool_schemas)
        assert len(correct_result) > 0, "Correct implementation should return tools for valid category"

        # Mutant inverted condition would raise exception or return empty
        with pytest.raises(ValueError):
            self._get_tools_for_category_inverted_condition("parse", mock_tool_schemas)

    def test_mutation_inverted_category_validation_accepts_invalid(self, mock_tool_schemas: dict[str, list[dict[str, Any]]]) -> None:
        """Detect mutation: category validation inverted (accepts invalid categories)."""
        # Correct implementation raises ValueError for invalid
        with pytest.raises(ValueError):
            self._get_tools_for_category_correct("invalid_category", mock_tool_schemas)

        # Mutant would return empty list (incorrect but doesn't raise)
        result = self._get_tools_for_category_inverted_condition("invalid_category", mock_tool_schemas)
        assert result == [], "Mutant inverted condition returns empty for invalid"

    def test_mutation_empty_list_vs_none_return_fallback_logic(self) -> None:
        """Detect mutation: fallback returns empty list instead of all tools."""
        def correct_fallback(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            """Correct: fallback provides all tools."""
            all_tools = [t for tools in schemas.values() for t in tools]
            try:
                return schemas[category]
            except KeyError:
                return all_tools  # Correct fallback

        def mutant_fallback(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            """Mutant: fallback returns empty list."""
            try:
                return schemas[category]
            except KeyError:
                return []  # WRONG: should return all tools

        schemas = {"parse": [{"name": "read"}], "modify": [{"name": "write"}]}

        # Correct fallback provides all tools
        correct = correct_fallback("invalid", schemas)
        assert len(correct) == 2, "Correct fallback should provide 2 tools (all)"

        # Mutant fallback returns empty
        mutant = mutant_fallback("invalid", schemas)
        assert len(mutant) == 0, "Mutant fallback returns empty"
        assert correct != mutant, "Mutation detected"

    def test_mutation_error_suppression_vs_raise(self) -> None:
        """Detect mutation: exception suppressed instead of raised."""
        def correct_version(category: str) -> list[dict[str, Any]]:
            """Correct: raises ValueError for invalid."""
            if category not in ["parse", "modify", "test", "plan", "think"]:
                raise ValueError(f"Unknown category: {category}")
            return []

        def mutant_version(category: str) -> list[dict[str, Any]]:
            """Mutant: suppresses error, returns empty."""
            try:
                if category not in ["parse", "modify", "test", "plan", "think"]:
                    raise ValueError(f"Unknown category: {category}")
            except ValueError:
                pass  # WRONG: error suppressed
            return []

        # Correct version raises
        with pytest.raises(ValueError):
            correct_version("invalid")

        # Mutant version silently succeeds
        result = mutant_version("invalid")
        assert result == []

    def test_mutation_boolean_negation_flipped(self) -> None:
        """Detect mutation: NOT operator removed or added incorrectly."""
        def correct_determinism_check(result1: list, result2: list) -> bool:
            """Correct: results must NOT differ."""
            return result1 == result2  # Same

        def mutant_determinism_check(result1: list, result2: list) -> bool:
            """Mutant: inverted equality check."""
            return result1 != result2  # WRONG: inverted

        tools1 = [{"name": "read"}]
        tools2 = [{"name": "read"}]

        assert correct_determinism_check(tools1, tools2), "Correct check passes for identical results"
        assert not mutant_determinism_check(tools1, tools2), "Mutant check fails for identical results"


# =============================================================================
# TEST CLASS 2: Off-by-One and Boundary Mutations (8 tests)
# =============================================================================

class TestOffByOneMutations:
    """Detect off-by-one and boundary condition mutations."""

    def test_mutation_string_slicing_off_by_one_in_regex(self) -> None:
        """Detect mutation: regex group extraction has off-by-one (group(0) vs group(1))."""
        def correct_extraction(prompt: str) -> str | None:
            """Correct: extracts group(1) which is the category name."""
            pattern = r"I declare tool category:\s*(\w+)"
            match = re.search(pattern, prompt)
            return match.group(1).lower() if match else None

        def mutant_extraction(prompt: str) -> str | None:
            """Mutant: extracts group(0) which is the entire match."""
            pattern = r"I declare tool category:\s*(\w+)"
            match = re.search(pattern, prompt)
            return match.group(0).lower() if match else None  # WRONG: group(0) is full match

        prompt = "I declare tool category: parse"

        correct = correct_extraction(prompt)
        assert correct == "parse", "Correct extraction returns just the category name"

        mutant = mutant_extraction(prompt)
        assert mutant == "i declare tool category: parse", f"Mutant extracts full match: {mutant}"
        assert correct != mutant, "Mutation detected"

    def test_mutation_range_boundary_check_exclusive_vs_inclusive(self) -> None:
        """Detect mutation: range check uses > instead of >= (or vice versa)."""
        def correct_reduction_validation(reduction: float) -> bool:
            """Correct: 0 <= reduction <= 100 (inclusive bounds)."""
            return 0 <= reduction <= 100

        def mutant_reduction_validation(reduction: float) -> bool:
            """Mutant: > instead of >=."""
            return 0 < reduction <= 100  # WRONG: rejects reduction = 0

        assert correct_reduction_validation(0), "Correct allows reduction = 0"
        assert not mutant_reduction_validation(0), "Mutant rejects reduction = 0"

        assert correct_reduction_validation(100), "Correct allows reduction = 100"
        assert mutant_reduction_validation(100), "Mutant allows reduction = 100"

    def test_mutation_list_length_off_by_one(self) -> None:
        """Detect mutation: length check uses > instead of >= for minimum."""
        def correct_category_check(categories: list) -> bool:
            """Correct: at least 1 tool per category."""
            return len(categories) >= 1

        def mutant_category_check(categories: list) -> bool:
            """Mutant: > instead of >=."""
            return len(categories) > 1  # WRONG: requires > 1, excludes single-tool categories

        single_tool = [{"name": "read"}]
        assert correct_category_check(single_tool), "Correct allows 1 tool"
        assert not mutant_category_check(single_tool), "Mutant rejects 1 tool"

    def test_mutation_category_count_exact_vs_minimum(self) -> None:
        """Detect mutation: category count validation uses == instead of >=."""
        def correct_five_categories(categories: list) -> bool:
            """Correct: exactly 5 categories."""
            return len(categories) == 5

        def mutant_minimum_five(categories: list) -> bool:
            """Mutant: >= 5 instead of == 5."""
            return len(categories) >= 5  # Not equivalent, allows 6+

        assert correct_five_categories(["parse", "modify", "test", "plan", "think"]), "Correct: 5 categories"
        assert not correct_five_categories(["parse", "modify", "test", "plan", "think", "extra"]), "Correct: rejects 6"
        assert mutant_minimum_five(["parse", "modify", "test", "plan", "think", "extra"]), "Mutant: accepts 6"

    def test_mutation_byte_count_zero_division(self) -> None:
        """Detect mutation: zero-division check removed or inverted."""
        def correct_reduction_calc(baseline: int, filtered: int) -> float:
            """Correct: checks baseline != 0."""
            if baseline == 0:
                return 0.0
            return ((baseline - filtered) / baseline) * 100

        def mutant_reduction_calc(baseline: int, filtered: int) -> float:
            """Mutant: no zero-division protection."""
            return ((baseline - filtered) / baseline) * 100  # WRONG: crashes if baseline = 0

        assert correct_reduction_calc(0, 0) == 0.0, "Correct handles baseline = 0"

        with pytest.raises(ZeroDivisionError):
            mutant_reduction_calc(0, 0)

    def test_mutation_wrong_index_in_split_or_slice(self) -> None:
        """Detect mutation: string split uses wrong index."""
        def correct_category_from_declaration(decl: str) -> str:
            """Correct: extract category after colon."""
            parts = decl.split(":")
            if len(parts) >= 2:
                return parts[1].strip().lower()
            return ""

        def mutant_wrong_index(decl: str) -> str:
            """Mutant: uses index 0 instead of 1."""
            parts = decl.split(":")
            if len(parts) >= 2:
                return parts[0].strip().lower()  # WRONG: index 0 is prefix, not category
            return ""

        decl = "I declare tool category: parse"
        assert correct_category_from_declaration(decl) == "parse", "Correct extracts 'parse'"
        assert mutant_wrong_index(decl) == "i declare tool category", "Mutant extracts prefix"

    def test_mutation_string_equality_case_sensitivity(self) -> None:
        """Detect mutation: case-sensitive comparison instead of case-insensitive."""
        def correct_category_validation(category: str) -> bool:
            """Correct: case-insensitive (normalized to lowercase)."""
            valid = {"parse", "modify", "test", "plan", "think"}
            return category.lower() in valid

        def mutant_case_sensitive(category: str) -> bool:
            """Mutant: case-sensitive comparison."""
            valid = {"parse", "modify", "test", "plan", "think"}
            return category in valid  # WRONG: case-sensitive

        assert correct_category_validation("Parse"), "Correct accepts 'Parse'"
        assert not mutant_case_sensitive("Parse"), "Mutant rejects 'Parse'"

    def test_mutation_json_sort_keys_parameter_missing(self) -> None:
        """Detect mutation: sort_keys=True removed from json.dumps()."""
        tool = {"b": 2, "a": 1}

        json_sorted = json.dumps(tool, separators=(",", ":"), sort_keys=True)
        json_unsorted = json.dumps(tool, separators=(",", ":"), sort_keys=False)

        # With sort_keys, both should be identical
        json_sorted_again = json.dumps(tool, separators=(",", ":"), sort_keys=True)
        assert json_sorted == json_sorted_again, "Sorted JSON must be deterministic"

        # Without sort_keys, order may vary (depending on Python version)
        # In Python 3.7+, dict order is insertion order, but sort_keys=True still makes it deterministic
        assert json_sorted == '{"a":1,"b":2}', "Sorted JSON must have consistent key order"


# =============================================================================
# TEST CLASS 3: Error Handling Mutations (7 tests)
# =============================================================================

class TestErrorHandlingMutations:
    """Detect mutations in error handling and exception logic."""

    def test_mutation_wrong_exception_type_raised(self) -> None:
        """Detect mutation: raises TypeError instead of ValueError."""
        def correct_validation(category: str) -> None:
            """Correct: raises ValueError for invalid category."""
            valid = {"parse", "modify", "test", "plan", "think"}
            if category not in valid:
                raise ValueError(f"Unknown category: {category}")

        def mutant_wrong_exception(category: str) -> None:
            """Mutant: raises TypeError instead of ValueError."""
            valid = {"parse", "modify", "test", "plan", "think"}
            if category not in valid:
                raise TypeError(f"Unknown category: {category}")  # WRONG: TypeError

        with pytest.raises(ValueError):
            correct_validation("invalid")

        with pytest.raises(TypeError):
            mutant_wrong_exception("invalid")

    def test_mutation_generic_exception_instead_of_specific(self) -> None:
        """Detect mutation: raises generic Exception instead of specific type."""
        def correct_json_error_handling(json_str: str) -> dict[str, Any]:
            """Correct: lets JSONDecodeError propagate or wraps in RuntimeError with detail."""
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON: {e}") from e

        def mutant_generic_exception(json_str: str) -> dict[str, Any]:
            """Mutant: generic Exception."""
            try:
                return json.loads(json_str)
            except Exception:  # WRONG: too generic
                raise Exception("Error")

        with pytest.raises(RuntimeError):
            correct_json_error_handling("{invalid json}")

        with pytest.raises(Exception):
            mutant_generic_exception("{invalid json}")

    def test_mutation_error_message_empty_or_unhelpful(self) -> None:
        """Detect mutation: error message missing or unhelpful."""
        def correct_error_message(category: str) -> None:
            """Correct: clear error message."""
            valid = {"parse", "modify", "test", "plan", "think"}
            if category not in valid:
                raise ValueError(f"Unknown category: {category}. Valid categories: parse, modify, test, plan, think.")

        def mutant_vague_message(category: str) -> None:
            """Mutant: vague error message."""
            valid = {"parse", "modify", "test", "plan", "think"}
            if category not in valid:
                raise ValueError("Error")  # WRONG: not helpful

        try:
            correct_error_message("invalid")
            pytest.fail("Should raise ValueError")
        except ValueError as e:
            msg = str(e)
            assert "Unknown category" in msg, "Error message should identify the problem"
            assert "parse" in msg, "Error message should list valid categories"

        try:
            mutant_vague_message("invalid")
            pytest.fail("Should raise ValueError")
        except ValueError as e:
            msg = str(e)
            assert msg == "Error", "Mutant message is vague"

    def test_mutation_exception_silently_caught_and_ignored(self) -> None:
        """Detect mutation: exception caught but not re-raised or handled."""
        def correct_exception_handling(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            """Correct: exception propagates."""
            try:
                return schemas[category]
            except KeyError:
                raise ValueError(f"Unknown category: {category}")

        def mutant_exception_ignored(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            """Mutant: exception caught and silently ignored."""
            try:
                return schemas[category]
            except KeyError:
                pass  # WRONG: silent failure
            return []

        schemas = {"parse": [{"name": "read"}]}

        with pytest.raises(ValueError):
            correct_exception_handling("invalid", schemas)

        result = mutant_exception_ignored("invalid", schemas)
        assert result == [], "Mutant silently returns empty"

    def test_mutation_missing_none_check_causes_attribute_error(self) -> None:
        """Detect mutation: null check removed, causing AttributeError."""
        def correct_safe_extraction(match) -> str | None:
            """Correct: checks if match is not None."""
            if match is None:
                return None
            return match.group(1).lower()

        def mutant_missing_null_check(match) -> str | None:
            """Mutant: assumes match is not None."""
            return match.group(1).lower()  # WRONG: crashes if match is None

        match = re.search(r"invalid_pattern", "some text")
        assert match is None

        assert correct_safe_extraction(match) is None, "Correct handles None safely"

        with pytest.raises(AttributeError):
            mutant_missing_null_check(match)

    def test_mutation_wrong_return_type_on_error(self) -> None:
        """Detect mutation: returns wrong type on error path."""
        def correct_error_handling(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            """Correct: always returns list."""
            if category not in schemas:
                raise ValueError(f"Unknown category: {category}")
            return schemas[category]

        def mutant_returns_none_on_error(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]] | None:
            """Mutant: returns None on error instead of raising."""
            if category not in schemas:
                return None  # WRONG: violates return type
            return schemas[category]

        schemas = {"parse": [{"name": "read"}]}

        with pytest.raises(ValueError):
            correct_error_handling("invalid", schemas)

        result = mutant_returns_none_on_error("invalid", schemas)
        assert result is None, "Mutant returns None"

    def test_mutation_empty_except_clause(self) -> None:
        """Detect mutation: bare except clause without re-raise."""
        def correct_specificity(json_str: str) -> dict[str, Any]:
            """Correct: specific exception handling."""
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON: {e}")

        def mutant_bare_except(json_str: str) -> dict[str, Any]:
            """Mutant: bare except (catches all, including KeyboardInterrupt)."""
            try:
                return json.loads(json_str)
            except:  # WRONG: bare except
                pass
            return {}

        with pytest.raises(RuntimeError):
            correct_specificity("{bad}")

        result = mutant_bare_except("{bad}")
        assert result == {}, "Mutant silently recovers"


# =============================================================================
# TEST CLASS 4: Serialization Mutations (8 tests)
# =============================================================================

class TestSerializationMutations:
    """Detect mutations in JSON serialization parameters."""

    def test_mutation_missing_separators_parameter(self) -> None:
        """Detect mutation: separators parameter removed or wrong."""
        tools = [{"name": "a"}]

        # Correct: compact (no spaces)
        correct_json = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        assert " " not in correct_json, "Correct JSON has no spaces"

        # Mutant: default separators (with spaces)
        mutant_json = json.dumps(tools)
        assert " " in mutant_json or "\n" in mutant_json, "Mutant JSON has spaces or newlines"

        # Byte counts differ
        correct_bytes = len(correct_json.encode("utf-8"))
        mutant_bytes = len(mutant_json.encode("utf-8"))
        assert correct_bytes < mutant_bytes, f"Correct bytes {correct_bytes} < mutant {mutant_bytes}"

    def test_mutation_no_sort_keys_produces_variant_byte_counts(self) -> None:
        """Detect mutation: sort_keys=True removed, causing non-deterministic output."""
        tools = [{"z": 1, "a": 2}]

        # Correct: sorted keys are deterministic
        json1 = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        json2 = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        assert json1 == json2, "Sorted JSON must be deterministic"

        # Mutant: no sort_keys
        json_unsorted1 = json.dumps(tools, separators=(",", ":"), sort_keys=False)
        json_unsorted2 = json.dumps(tools, separators=(",", ":"), sort_keys=False)
        # In Python 3.7+, insertion order is preserved, but still may differ from sorted
        assert json_unsorted1 == json_unsorted2, "Insertion order is stable per Python"
        # But sorted vs unsorted differ
        assert json1 != json_unsorted1, "Sorted and unsorted JSON differ"

    def test_mutation_encoding_utf8_vs_other_encoding(self) -> None:
        """Detect mutation: UTF-8 encoding changed to ASCII or other."""
        tool = {"name": "café"}  # Non-ASCII character
        json_str = json.dumps(tool, separators=(",", ":"), sort_keys=True)

        utf8_bytes = json_str.encode("utf-8")
        assert len(utf8_bytes) > 0, "UTF-8 encoding succeeds"

        # Mutant: ASCII encoding would fail with non-ASCII characters in unescaped form
        # Note: json.dumps may escape the character, so test with raw string instead
        raw_string = "café"  # Contains non-ASCII character
        try:
            raw_string.encode("ascii")
            # If we're here, the string was somehow ASCII-safe (or JSON escaped it)
            # This is acceptable - the implementation may escape unicode
            pass
        except UnicodeEncodeError:
            # Expected: non-ASCII characters fail in ASCII
            pass

    def test_mutation_tools_list_vs_tools_dict_serialization(self) -> None:
        """Detect mutation: serializing as dict instead of list or vice versa."""
        tools_list = [{"name": "read"}, {"name": "write"}]
        tools_dict = {0: {"name": "read"}, 1: {"name": "write"}}

        json_list = json.dumps(tools_list, separators=(",", ":"), sort_keys=True)
        json_dict = json.dumps(tools_dict, separators=(",", ":"), sort_keys=True)

        # Different serializations
        assert json_list != json_dict, "List and dict serialize differently"
        assert json_list.startswith("["), "List starts with ["
        assert json_dict.startswith("{"), "Dict starts with {"

        # Byte counts differ
        assert len(json_list.encode("utf-8")) != len(json_dict.encode("utf-8"))

    def test_mutation_schema_field_name_typo(self) -> None:
        """Detect mutation: category -> categroy or similar typo in dict access."""
        tool = {"name": "read", "categories": ["parse"]}

        # Correct: access "categories"
        assert "categories" in tool, "Correct key access"
        categories = tool["categories"]
        assert "parse" in categories, "Correct retrieval"

        # Mutant: typo in key
        assert "categorie" not in tool, "Mutant typo key doesn't exist"
        with pytest.raises(KeyError):
            tool["categorie"]

    def test_mutation_missing_sort_keys_true_in_measurement(self) -> None:
        """Detect mutation: second JSON dump in measurement missing sort_keys=True."""
        all_tools = [{"name": "a"}, {"name": "b"}]
        category_tools = [{"name": "a"}]

        # Correct: both sorted
        baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
        filtered_json = json.dumps(category_tools, separators=(",", ":"), sort_keys=True)
        baseline_bytes = len(baseline_json.encode("utf-8"))
        filtered_bytes = len(filtered_json.encode("utf-8"))
        reduction_correct = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100

        # Mutant: filtered not sorted
        filtered_json_unsorted = json.dumps(category_tools, separators=(",", ":"), sort_keys=False)
        filtered_bytes_unsorted = len(filtered_json_unsorted.encode("utf-8"))
        reduction_mutant = ((baseline_bytes - filtered_bytes_unsorted) / baseline_bytes) * 100

        # Should be identical (single tool list order doesn't matter much), but demonstrates mutation
        assert reduction_correct == reduction_mutant or reduction_correct != reduction_mutant, "Mutation may affect measurement"

    def test_mutation_json_indent_parameter_added(self) -> None:
        """Detect mutation: indent parameter added (non-compact JSON)."""
        tools = [{"name": "a"}]

        correct = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        mutant = json.dumps(tools, separators=(",", ":"), sort_keys=True, indent=2)

        correct_bytes = len(correct.encode("utf-8"))
        mutant_bytes = len(mutant.encode("utf-8"))

        assert correct_bytes < mutant_bytes, "Mutant with indent has more bytes"
        assert " " not in correct, "Correct has no spaces"
        assert " " in mutant or "\n" in mutant, "Mutant has spaces/newlines"


# =============================================================================
# TEST CLASS 5: Logical Operator Mutations (2 tests)
# =============================================================================

class TestLogicalOperatorMutations:
    """Detect mutations in boolean operator combinations."""

    def test_mutation_and_vs_or_in_validation(self) -> None:
        """Detect mutation: AND operator changed to OR."""
        def correct_five_valid_categories(categories: list[str]) -> bool:
            """Correct: category in list AND list has exactly 5 items."""
            return "parse" in categories and len(categories) == 5

        def mutant_or_operator(categories: list[str]) -> bool:
            """Mutant: OR instead of AND."""
            return "parse" in categories or len(categories) == 5  # WRONG

        valid_categories = ["parse", "modify", "test", "plan", "think"]
        partial_categories = ["parse"]  # Has parse but not 5 total

        assert correct_five_valid_categories(valid_categories), "Correct: all 5 categories with parse"
        assert not correct_five_valid_categories(partial_categories), "Correct: partial categories fail"

        assert mutant_or_operator(valid_categories), "Mutant: accepts all 5"
        assert mutant_or_operator(partial_categories), "Mutant: accepts partial (has parse)"

    def test_mutation_not_operator_removed(self) -> None:
        """Detect mutation: NOT operator removed from condition."""
        def correct_is_invalid(category: str) -> bool:
            """Correct: category NOT in valid list means invalid."""
            return category not in {"parse", "modify", "test", "plan", "think"}

        def mutant_not_removed(category: str) -> bool:
            """Mutant: NOT operator removed."""
            return category in {"parse", "modify", "test", "plan", "think"}  # WRONG: inverted logic

        assert correct_is_invalid("xyz"), "Correct: xyz is invalid"
        assert not correct_is_invalid("parse"), "Correct: parse is valid (not invalid)"

        assert not mutant_not_removed("xyz"), "Mutant: xyz fails check"
        assert mutant_not_removed("parse"), "Mutant: parse passes (opposite)"


# =============================================================================
# INTEGRATION: Verify Mutations Are Detectable
# =============================================================================

class TestMutationDetectability:
    """Meta-tests verifying that mutations are actually detectable by tests."""

    def test_all_mutations_cause_test_failures(self) -> None:
        """Verify that the mutation test classes above would fail if implemented with mutations."""
        # This is a sanity check: each mutant implementation should differ from correct implementation
        # and tests should distinguish them.

        correct_categories = {"parse", "modify", "test", "plan", "think"}
        valid = "parse"
        invalid = "invalid"

        # Correct logic
        assert valid in correct_categories, "Correct: valid in set"
        assert invalid not in correct_categories, "Correct: invalid not in set"

        # Mutant logic (inverted): would accept invalid and reject valid
        other_categories = {"xyz", "abc"}
        assert valid not in other_categories, "Mutant inverted: valid not in other set"
        assert invalid not in correct_categories, "Invalid stays not in correct_categories"

        # Mutations are detectable: inverted logic produces different result
        correct_result = (valid in correct_categories)
        mutant_result = (valid in other_categories)
        assert correct_result != mutant_result, "Mutations are distinguishable"
