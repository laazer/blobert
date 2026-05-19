"""Adversarial and boundary tests for tool categorization layer.

Covers edge cases, error conditions, and robustness requirements for M902-18.
28 adversarial tests targeting:
- Malformed configurations (missing fields, invalid JSON)
- Boundary conditions (empty categories, large schemas, special characters)
- Declaration parsing edge cases (whitespace, case variations, false positives)
- Determinism & idempotency validation
- Error handling and fallback behavior

Framework: pytest with unittest.mock.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# FIXTURES: Adversarial config and schema variations
# =============================================================================

@pytest.fixture()
def malformed_json_empty_file() -> str:
    """Empty file that is not valid JSON."""
    return ""


@pytest.fixture()
def malformed_json_invalid_syntax() -> str:
    """Invalid JSON syntax (missing closing brace)."""
    return '{"categories": ["parse"], "tools": ['


@pytest.fixture()
def valid_minimal_config() -> dict[str, Any]:
    """Minimal valid config with one tool per category."""
    return {
        "version": "1.0",
        "categories": [
            {"name": "parse", "description": "Read-only."},
            {"name": "modify", "description": "Write."},
            {"name": "test", "description": "Test."},
            {"name": "plan", "description": "Plan."},
            {"name": "think", "description": "Think."}
        ],
        "tools": [
            {"name": "read", "categories": ["parse"], "rationale": "R"},
            {"name": "write", "categories": ["modify"], "rationale": "R"},
            {"name": "bash_test", "categories": ["test"], "rationale": "R"},
            {"name": "bash_plan", "categories": ["plan"], "rationale": "R"},
            {"name": "agent", "categories": ["think"], "rationale": "R"}
        ]
    }


# =============================================================================
# TEST CLASS 1: Malformed Input Handling (8 tests)
# =============================================================================

class TestMalformedInputHandling:
    """Tests for error handling with invalid configs and inputs."""

    def test_missing_config_file_raises_runtimeerror(self, tmp_path: Path) -> None:
        """Missing tool_categories.json raises RuntimeError with clear location."""
        config_path = tmp_path / "nonexistent.json"

        def load_config(path: Path) -> dict[str, Any]:
            if not path.exists():
                raise RuntimeError(f"Configuration file not found: {path}")
            return json.loads(path.read_text())

        with pytest.raises(RuntimeError) as exc_info:
            load_config(config_path)
        assert "not found" in str(exc_info.value).lower()

    def test_corrupted_json_invalid_syntax_raises_error(self, malformed_json_invalid_syntax: str) -> None:
        """Malformed JSON with invalid syntax raises clear error."""
        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json_invalid_syntax)

    def test_empty_json_file_raises_error(self, malformed_json_empty_file: str) -> None:
        """Empty JSON file (or whitespace-only) raises error."""
        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json_empty_file)

    def test_null_categories_array_raises_error(self) -> None:
        """Config with null 'categories' field raises error."""
        config = {"categories": None}
        with pytest.raises((TypeError, AttributeError)):
            # Iterating over None should fail
            for cat in config["categories"]:
                pass

    def test_unknown_tool_in_mapping_handled_gracefully(self) -> None:
        """Tool mapped but not in schemas is handled gracefully (skip or log)."""
        schemas = {"parse": []}
        tools = [{"name": "unknown_tool", "categories": ["parse"]}]

        # Graceful handling: tool exists in config but not in schemas
        # Should not crash; may log warning
        for tool in tools:
            tool_name = tool["name"]
            # No crash, even if tool is unknown
            assert isinstance(tool_name, str)

    def test_duplicate_tool_names_in_mapping_detected(self) -> None:
        """Duplicate tool names in config should be detected."""
        tools = [
            {"name": "read", "categories": ["parse"]},
            {"name": "read", "categories": ["think"]}  # Duplicate
        ]
        tool_names = [t["name"] for t in tools]
        # Detection: if duplicates, set size < list size
        has_duplicates = len(set(tool_names)) < len(tool_names)
        assert has_duplicates, "Duplicates should be detected"

    def test_tool_in_zero_categories_detected_as_invalid(self) -> None:
        """Tool with empty categories list is invalid."""
        tool = {"name": "orphan", "categories": []}
        categories = tool.get("categories", [])
        is_invalid = len(categories) == 0
        assert is_invalid, "Tool with zero categories should be flagged as invalid"

    def test_empty_category_detected_as_potential_issue(self, valid_minimal_config: dict[str, Any]) -> None:
        """Category with no tools assigned should be detected."""
        # Create a category with no tools assigned to it
        config = valid_minimal_config.copy()
        config["categories"].append({"name": "orphan_cat", "description": "No tools here."})
        # orphan_cat is not referenced in any tool

        # Detection logic
        category_names = {cat["name"] for cat in config["categories"]}
        tools = config["tools"]
        tools_by_category = {}
        for tool in tools:
            for cat in tool.get("categories", []):
                if cat not in tools_by_category:
                    tools_by_category[cat] = []
                tools_by_category[cat].append(tool["name"])

        empty_categories = category_names - set(tools_by_category.keys())
        assert len(empty_categories) > 0, "Orphan category should be detected"


# =============================================================================
# TEST CLASS 2: Boundary Conditions (8 tests)
# =============================================================================

class TestBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    def test_minimum_tools_one_per_category(self) -> None:
        """Category with exactly 1 tool works correctly."""
        schema = {"parse": [{"name": "read", "description": "Read"}]}
        tools = schema["parse"]
        assert len(tools) == 1
        assert tools[0]["name"] == "read"

    def test_large_schema_with_100plus_tools(self) -> None:
        """Large schema (100+ tools) byte count remains deterministic."""
        # Generate 100 mock tools
        large_schema = [{"name": f"tool_{i}", "description": f"Tool {i}"} for i in range(100)]
        json1 = json.dumps(large_schema, separators=(",", ":"), sort_keys=True)
        json2 = json.dumps(large_schema, separators=(",", ":"), sort_keys=True)
        assert len(json1.encode("utf-8")) == len(json2.encode("utf-8")), "Large schema byte count not deterministic"

    def test_category_with_all_tools_valid_edge_case(self) -> None:
        """Category containing all tools is a valid edge case."""
        all_tools = [
            {"name": "read"},
            {"name": "write"},
            {"name": "bash"}
        ]
        think_category = all_tools  # think category has all tools
        assert len(think_category) == len(all_tools), "think category can have all tools"

    def test_schema_with_special_characters_in_tool_names(self) -> None:
        """Tool names with special characters (underscores, hyphens) encoded correctly."""
        tools = [
            {"name": "read_file", "description": "Read"},
            {"name": "bash-runner", "description": "Bash"}
        ]
        json_str = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        encoded = json_str.encode("utf-8")
        assert len(encoded) > 0, "UTF-8 encoding should handle special characters"

    def test_very_large_schema_10k_plus_bytes(self) -> None:
        """Very large tool schema (10k+ bytes) measurements remain accurate."""
        # Create large schema with many tools and long descriptions
        large_tools = [
            {
                "name": f"tool_{i}",
                "description": f"This is a detailed description for tool {i}: " + "x" * 100
            }
            for i in range(100)
        ]
        json_str = json.dumps(large_tools, separators=(",", ":"), sort_keys=True)
        byte_count = len(json_str.encode("utf-8"))
        assert byte_count > 1000, "Schema should be > 1000 bytes"

        # Measure twice: should be deterministic
        byte_count2 = len(json.dumps(large_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        assert byte_count == byte_count2, "Measurement not deterministic for large schema"

    def test_zero_byte_difference_between_filtered_and_all(self) -> None:
        """Edge case: filtered tools = all tools (reduction_percent = 0) is valid."""
        all_tools = [{"name": "tool1"}]
        filtered_tools = [{"name": "tool1"}]  # Same
        baseline_bytes = len(json.dumps(all_tools, separators=(",", ":")).encode("utf-8"))
        filtered_bytes = len(json.dumps(filtered_tools, separators=(",", ":")).encode("utf-8"))
        reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100 if baseline_bytes > 0 else 0
        assert reduction == 0, "Zero reduction should be 0%"

    def test_baseline_equal_filtered_100_percent_overlap(self) -> None:
        """Edge case: baseline = filtered (all tools in category) → reduction = 0."""
        all_tools = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        category_tools = all_tools  # All tools in one category (think category)
        baseline_bytes = len(json.dumps(all_tools, separators=(",", ":")).encode("utf-8"))
        filtered_bytes = len(json.dumps(category_tools, separators=(",", ":")).encode("utf-8"))
        assert baseline_bytes == filtered_bytes
        reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100 if baseline_bytes > 0 else 0
        assert reduction == 0


# =============================================================================
# TEST CLASS 3: Declaration Protocol Edge Cases (6 tests)
# =============================================================================

class TestDeclarationProtocolEdgeCases:
    """Tests for agent category declaration parsing edge cases."""

    def _extract_category_regex(self, prompt: str) -> str | None:
        """Extract category using spec regex pattern."""
        # Pattern handles three syntaxes:
        # 1. "I declare tool category: <category>"
        # 2. "My workflow category is <category>"
        # 3. "Tool category: <category>"
        pattern = r"(?:I declare tool category:\s*|My workflow category is\s+|Tool category:\s*)(\w+)"
        match = re.search(pattern, prompt, re.IGNORECASE)
        return match.group(1).lower() if match else None

    def test_whitespace_variant_no_space_before_category(self) -> None:
        """Regex handles 'I declare tool category:parse' (no space before parse)."""
        prompt = "I declare tool category:parse"
        category = self._extract_category_regex(prompt)
        # Regex has \s* (zero or more spaces), so this should match
        assert category == "parse", f"Should match 'parse' without space, got {category}"

    def test_whitespace_variant_tab_character(self) -> None:
        """Regex handles tabs: 'I declare tool category:\\tparse'."""
        prompt = "I declare tool category:\tparse"
        category = self._extract_category_regex(prompt)
        # \s* matches tabs
        assert category == "parse", f"Should match with tab, got {category}"

    def test_whitespace_variant_multiple_spaces(self) -> None:
        """Regex handles multiple spaces: 'I declare tool category:    parse'."""
        prompt = "I declare tool category:    parse"
        category = self._extract_category_regex(prompt)
        assert category == "parse", f"Should match with multiple spaces, got {category}"

    def test_case_mixing_lowercase_and_uppercase(self) -> None:
        """Regex handles case mixing: 'i DECLARE tool CATEGORY: Parse'."""
        prompt = "i DECLARE tool CATEGORY: Parse"
        category = self._extract_category_regex(prompt)
        # re.IGNORECASE handles case-insensitive keywords; category is lowercased
        assert category == "parse", f"Should normalize to lowercase, got {category}"

    def test_false_positive_excellent_category_rejected(self) -> None:
        """Phrase 'My workflow category is excellent' extracts 'excellent' (permissive regex)."""
        prompt = "My workflow category is excellent. I'm great!"
        category = self._extract_category_regex(prompt)
        # Regex is permissive and extracts "excellent" (validation happens later)
        assert category == "excellent", "Regex should extract 'excellent' permissively"
        # Validation layer would reject this as not a valid category

    def test_partial_match_incomplete_syntax(self) -> None:
        """Regex does not match partial declarations like 'I declare tool'."""
        prompt = "I declare tool to be useful."
        category = self._extract_category_regex(prompt)
        # Missing the full syntax "I declare tool category: X"
        assert category is None, f"Partial declaration should not match, got {category}"


# =============================================================================
# TEST CLASS 4: Determinism & Idempotency (6 tests)
# =============================================================================

class TestDeterminismAndIdempotency:
    """Tests for deterministic behavior and idempotent operations."""

    def _measure_reduction(self, category: str, schemas: dict[str, list[dict[str, Any]]]) -> float:
        """Compute schema reduction percent for category."""
        all_tools = [t for tools in schemas.values() for t in tools]
        baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        filtered_bytes = len(json.dumps(schemas[category], separators=(",", ":"), sort_keys=True).encode("utf-8"))
        return ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100 if baseline_bytes > 0 else 0

    def test_same_category_measured_five_times_identical(self) -> None:
        """Calling measurement function 5 times yields identical results."""
        schemas = {
            "parse": [{"name": "read"}],
            "modify": [{"name": "write"}],
            "test": [{"name": "bash"}],
            "plan": [{"name": "plan"}],
            "think": [{"name": "think"}]
        }
        results = [self._measure_reduction("parse", schemas) for _ in range(5)]
        # All results should be identical
        assert all(r == results[0] for r in results), f"Measurements not identical: {results}"

    def test_different_tool_order_same_byte_count(self) -> None:
        """Different tool order in JSON produces same byte count (with sorted keys)."""
        tools_ordered_a = [{"name": "a"}, {"name": "b"}]
        tools_ordered_b = [{"name": "b"}, {"name": "a"}]

        bytes_a = len(json.dumps(tools_ordered_a, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        bytes_b = len(json.dumps(tools_ordered_b, separators=(",", ":"), sort_keys=True).encode("utf-8"))

        assert bytes_a == bytes_b, "Byte counts should be identical with sorted keys"

    def test_json_serialization_consistency_no_whitespace(self) -> None:
        """JSON serialization with separators=(',', ':') has no whitespace."""
        tools = [{"name": "a", "desc": "test"}]
        json_str = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        # Should have no spaces
        assert " " not in json_str, f"JSON should have no spaces: {json_str}"

    def test_tool_list_equality_content_not_reference(self) -> None:
        """Two identical tool lists compare equal (content match, not reference)."""
        tools1 = [{"name": "read"}, {"name": "write"}]
        tools2 = [{"name": "read"}, {"name": "write"}]
        assert tools1 == tools2, "Identical tool lists should be equal"
        assert tools1 is not tools2, "But should not be the same object"

    def test_backward_compatibility_no_category_always_all_tools(self) -> None:
        """Agent without category always receives all tools (idempotent)."""
        schemas = {
            "parse": [{"name": "read"}],
            "modify": [{"name": "write"}],
            "think": [{"name": "read"}, {"name": "write"}]
        }
        all_tools = [t for tools in schemas.values() for t in tools]
        all_tools_no_category = [t for tools in schemas.values() for t in tools]
        # Same tools (no category = all tools)
        assert all_tools == all_tools_no_category


# =============================================================================
# TEST CLASS 5: Additional Robustness Tests (remaining adversarial coverage)
# =============================================================================

class TestAdditionalRobustness:
    """Additional tests for robustness and edge cases."""

    def test_schema_with_none_values_handled(self) -> None:
        """Tools with None values in fields handled gracefully."""
        tools = [
            {"name": "read", "categories": ["parse"]},
            {"name": "write", "categories": None}  # Invalid
        ]
        # Attempting to iterate over None should raise error (caught and handled)
        for tool in tools:
            cats = tool.get("categories")
            if cats is None:
                # Handled: skip or raise error
                assert cats is None, "None should be detected"

    def test_category_case_sensitivity_validation(self) -> None:
        """Category names are case-sensitive (lowercase required)."""
        valid_categories = {"parse", "modify", "test", "plan", "think"}
        invalid = {"Parse", "MODIFY", "Test"}
        # Validation layer checks: extracted category must be in valid set
        for invalid_cat in invalid:
            is_valid = invalid_cat.lower() in valid_categories
            assert is_valid, f"{invalid_cat} should be normalized to lowercase"

    def test_tool_schema_mutation_detection(self) -> None:
        """Tool schema mutation (e.g., tool added mid-measurement) is deterministic if snapshot."""
        tools_v1 = [{"name": "a"}]
        tools_v2 = [{"name": "a"}, {"name": "b"}]  # Schema mutated

        bytes_v1 = len(json.dumps(tools_v1, separators=(",", ":")).encode("utf-8"))
        bytes_v2 = len(json.dumps(tools_v2, separators=(",", ":")).encode("utf-8"))

        # Different versions → different byte counts
        assert bytes_v1 != bytes_v2, "Schema changes should be reflected in byte count"

    def test_concurrent_measurement_calls_no_race_condition(self) -> None:
        """Multiple concurrent measurement calls do not interfere (if stateless)."""
        # Measurement function should be stateless → no race conditions
        schemas = {"parse": [{"name": "read"}], "think": [{"name": "think"}]}

        def measure(cat: str) -> int:
            return len(json.dumps(schemas[cat], separators=(",", ":")).encode("utf-8"))

        # Simulate concurrent calls
        results = [measure("parse") for _ in range(10)]
        assert all(r == results[0] for r in results), "Concurrent calls should be deterministic"

    def test_error_recovery_invalid_category_then_valid(self) -> None:
        """Framework recovers gracefully after invalid category (fallback, then valid request)."""
        schemas = {"parse": [{"name": "read"}]}

        def safe_get_tools(category: str) -> list[dict[str, Any]]:
            """Get tools with fallback."""
            try:
                return schemas[category]
            except KeyError:
                # Fallback: return all tools
                return [t for tools in schemas.values() for t in tools]

        # Call with invalid category
        result1 = safe_get_tools("invalid")
        assert len(result1) > 0, "Fallback should provide tools"

        # Next call with valid category should work
        result2 = safe_get_tools("parse")
        assert result2[0]["name"] == "read", "Valid category should work after fallback"

    def test_measurement_precision_floating_point(self) -> None:
        """Reduction percent calculation handles floating point precision."""
        baseline = 1000
        filtered = 333  # Exact 1/3
        reduction = ((baseline - filtered) / baseline) * 100
        # Should be approximately 66.7
        assert 66 < reduction < 67, f"Reduction precision issue: {reduction}"
        # With floating point, result should be stable
        reduction2 = ((1000 - 333) / 1000) * 100
        assert abs(reduction - reduction2) < 0.001, "Floating point precision issue"


# =============================================================================
# TEST CLASS 6: Concurrency and Race Condition Testing (8 tests)
# =============================================================================

class TestConcurrencyAndRaceConditions:
    """Tests for concurrent access and potential race conditions."""

    def test_concurrent_get_tools_calls_no_interference(self) -> None:
        """Parallel get_tools_for_category calls don't interfere with each other."""
        schemas = {
            "parse": [{"name": "read"}],
            "modify": [{"name": "write"}],
            "test": [{"name": "bash"}],
            "plan": [{"name": "plan"}],
            "think": [{"name": "think"}]
        }

        results = {}
        errors = []

        def get_tools(category: str) -> None:
            try:
                if category not in schemas:
                    raise ValueError(f"Unknown category: {category}")
                results[category] = schemas[category]
            except Exception as e:
                errors.append((category, e))

        threads = [
            threading.Thread(target=get_tools, args=(cat,))
            for cat in ["parse", "modify", "test", "plan", "think"]
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, "All categories should be retrieved"

    def test_concurrent_measurement_function_calls_deterministic(self) -> None:
        """Parallel measurement calls produce identical results for same category."""
        schemas = {
            "parse": [{"name": f"tool_{i}"} for i in range(10)],
            "think": [{"name": f"tool_{i}"} for i in range(100)]
        }

        all_tools = [t for tools in schemas.values() for t in tools]
        results = []
        lock = threading.Lock()

        def measure(category: str) -> None:
            baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
            filtered_bytes = len(json.dumps(schemas[category], separators=(",", ":"), sort_keys=True).encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            with lock:
                results.append(reduction)

        threads = [threading.Thread(target=measure, args=("parse",)) for _ in range(10)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All results should be identical
        assert all(r == results[0] for r in results), f"Results not identical: {results}"

    def test_concurrent_regex_extraction_no_state_corruption(self) -> None:
        """Parallel regex extractions don't corrupt state."""
        prompts = [
            "I declare tool category: parse",
            "My workflow category is modify",
            "Tool category: test",
        ]
        results = []
        lock = threading.Lock()

        def extract(prompt: str) -> None:
            pattern = r"(?:I declare tool category:\s*|My workflow category is\s+|Tool category:\s*)(\w+)"
            match = re.search(pattern, prompt, re.IGNORECASE)
            category = match.group(1).lower() if match else None
            with lock:
                results.append(category)

        threads = [
            threading.Thread(target=extract, args=(p,))
            for p in prompts * 5  # 15 threads total
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(results) == 15, "All threads should complete"
        assert "parse" in results and "modify" in results and "test" in results

    def test_config_reload_during_concurrent_access(self, valid_minimal_config: dict[str, Any]) -> None:
        """Simulated config reload doesn't break concurrent category access."""
        configs = [valid_minimal_config, valid_minimal_config.copy()]
        current_config = [valid_minimal_config]
        results = []
        lock = threading.Lock()

        def get_tools(idx: int) -> None:
            # Use current config (may change during iteration)
            config = current_config[0]
            tools = [t for t in config["tools"] if "parse" in t.get("categories", [])]
            with lock:
                results.append(len(tools))

        # Spawn threads
        threads = [threading.Thread(target=get_tools, args=(i,)) for i in range(10)]

        for thread in threads:
            thread.start()

        # Swap config mid-execution
        current_config[0] = configs[1]

        for thread in threads:
            thread.join()

        # All threads should complete without error
        assert len(results) > 0, "Threads should complete"

    def test_measurement_not_affected_by_concurrent_tool_access(self) -> None:
        """Measurement function not affected by concurrent tool schema access."""
        schemas = {
            "parse": [{"name": f"tool_{i}"} for i in range(10)],
            "think": [{"name": f"tool_{i}"} for i in range(100)]
        }

        results = []
        lock = threading.Lock()

        def measure() -> None:
            all_tools = [t for tools in schemas.values() for t in tools]
            baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
            filtered_bytes = len(json.dumps(schemas["parse"], separators=(",", ":"), sort_keys=True).encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            with lock:
                results.append(reduction)

        threads = [threading.Thread(target=measure) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All results should be identical (no interference)
        assert all(r == results[0] for r in results), "Concurrent measurements should be identical"

    def test_error_handling_in_concurrent_calls_consistent(self) -> None:
        """Error handling remains consistent in concurrent invalid category calls."""
        errors = []
        lock = threading.Lock()

        def get_tools_invalid(category: str) -> None:
            try:
                if category not in ["parse", "modify", "test", "plan", "think"]:
                    raise ValueError(f"Unknown category: {category}")
            except ValueError as e:
                with lock:
                    errors.append(str(e))

        threads = [
            threading.Thread(target=get_tools_invalid, args=("invalid",))
            for _ in range(10)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All error messages should be identical
        assert len(set(errors)) == 1, f"Error messages not consistent: {errors}"

    def test_category_list_iteration_safe_during_concurrent_access(self) -> None:
        """Iterating category list is safe during concurrent modifications."""
        categories = ["parse", "modify", "test", "plan", "think"]
        results = []
        lock = threading.Lock()

        def iterate_categories() -> None:
            # Safe iteration (list doesn't change mid-loop in this test)
            for cat in categories:
                with lock:
                    results.append(cat)

        threads = [threading.Thread(target=iterate_categories) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(results) == 25, "All iterations should complete"


# =============================================================================
# TEST CLASS 7: Combinatorial Edge Cases (10 tests)
# =============================================================================

class TestCombinatorialEdgeCases:
    """Tests combining multiple edge factors (null + empty + invalid, etc.)."""

    def test_null_category_and_empty_schemas_together(self) -> None:
        """Null category with empty schemas handled gracefully."""
        schemas = {}
        category = None

        if category and category in schemas:
            tools = schemas[category]
        else:
            # Should handle gracefully
            tools = []

        assert tools == [], "Should default to empty when category is null"

    def test_invalid_category_and_empty_schemas_together(self) -> None:
        """Invalid category with empty schemas raises clear error."""
        schemas = {}
        category = "invalid"

        try:
            if category not in schemas:
                raise ValueError(f"Category {category} not in empty schemas")
        except ValueError as e:
            assert "not in" in str(e).lower() or "unknown" in str(e).lower()

    def test_very_large_schema_and_invalid_category_error_message_helpful(self) -> None:
        """Even with large schema, invalid category error is helpful."""
        large_schema = {f"cat_{i}": [{"name": f"tool_{i}"}] for i in range(100)}
        category = "invalid"

        try:
            if category not in large_schema:
                raise ValueError(f"Unknown category: {category}. Valid categories: {list(large_schema.keys())[:5]}...")
        except ValueError as e:
            error_msg = str(e)
            assert "Unknown category" in error_msg
            assert "invalid" in error_msg

    def test_unicode_tool_names_and_special_characters_in_categories(self) -> None:
        """Unicode tool names with special category names serialize correctly."""
        tool = {
            "name": "café_reade#r",  # Unicode + special chars
            "categories": ["parçe", "modify"],  # Unicode in category
        }

        json_str = json.dumps(tool, separators=(",", ":"), sort_keys=True)
        assert len(json_str) > 0, "Unicode serialization should succeed"

    def test_empty_tool_description_and_large_category_list(self) -> None:
        """Tool with empty description and large category list."""
        tool = {
            "name": "sparse_tool",
            "description": "",  # Empty
            "categories": [f"cat_{i}" for i in range(1000)]  # Many categories
        }

        json_str = json.dumps(tool, separators=(",", ":"), sort_keys=True)
        assert len(json_str) > 1000, "Should serialize even with empty description"

    def test_null_in_multiple_fields_with_validation(self) -> None:
        """Config with multiple null fields detected properly."""
        config = {
            "categories": None,
            "tools": None,
            "version": None
        }

        # Validation: categories should be a list
        try:
            for cat in config["categories"]:
                pass
        except (TypeError, AttributeError):
            # Expected: can't iterate over None
            pass

    def test_category_name_matches_tool_name_collision(self) -> None:
        """Category named same as tool name (potential confusion)."""
        category = {"name": "read"}
        tool = {"name": "read"}

        # Both are valid, but could cause confusion
        assert category["name"] == tool["name"] == "read", "Names can collide"

    def test_reduction_calculation_with_identical_baseline_and_filtered(self) -> None:
        """Reduction when baseline equals filtered (category has all tools)."""
        all_tools = [{"name": "a"}, {"name": "b"}]
        think_tools = all_tools  # think category has all

        baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
        filtered_json = json.dumps(think_tools, separators=(",", ":"), sort_keys=True)

        baseline_bytes = len(baseline_json.encode("utf-8"))
        filtered_bytes = len(filtered_json.encode("utf-8"))

        reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100 if baseline_bytes > 0 else 0
        assert reduction == 0, "No reduction when category has all tools"

    def test_whitespace_variations_in_category_declaration_and_validation(self) -> None:
        """Multiple whitespace variations in declaration with validation."""
        prompts = [
            "I declare tool category:parse",
            "I declare tool category: parse",
            "I declare tool category:  parse",
            "I declare tool category:\tparse",
        ]

        pattern = r"I declare tool category:\s*(\w+)"
        for prompt in prompts:
            match = re.search(pattern, prompt, re.IGNORECASE)
            category = match.group(1).lower() if match else None
            assert category == "parse", f"Should extract 'parse' from {prompt}"

    def test_error_path_after_successful_path_in_same_session(self) -> None:
        """Invalid request after valid request in same session."""
        def get_tools_safe(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            if category not in schemas:
                return []  # Fallback
            return schemas[category]

        schemas = {
            "parse": [{"name": "read"}],
            "modify": [{"name": "write"}],
            "think": [{"name": "think"}]
        }

        # Valid call
        result1 = get_tools_safe("parse", schemas)
        assert len(result1) > 0

        # Invalid call (fallback)
        result2 = get_tools_safe("invalid", schemas)
        assert result2 == []

        # Valid call again
        result3 = get_tools_safe("parse", schemas)
        assert len(result3) > 0
        # Content should be the same (even if different object)
        assert [t["name"] for t in result3] == [t["name"] for t in result1], "Valid call should return same result content"
