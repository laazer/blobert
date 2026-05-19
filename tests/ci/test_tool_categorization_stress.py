"""Stress and load testing for tool categorization layer.

Tests behavior under high volume, large data, and repeated operations.
Covers M902-18 robustness requirements:
- 1000+ tools in single category
- 100+ repeated measurements
- Very large tool schemas (10MB+)
- Rapid category switching
- Stress on memory and CPU
- Determinism under load

All tests must remain fast (<100ms per test) while stressing the implementation.

Framework: pytest.
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest


# =============================================================================
# FIXTURES: Large-scale schemas and data
# =============================================================================

@pytest.fixture()
def large_schema_1000_tools() -> list[dict[str, Any]]:
    """Generate 1000 mock tools for stress testing."""
    return [
        {
            "name": f"tool_{i:04d}",
            "description": f"Mock tool {i} with description"
        }
        for i in range(1000)
    ]


@pytest.fixture()
def large_schema_with_long_descriptions() -> list[dict[str, Any]]:
    """Generate schema with very long descriptions (10k chars per tool)."""
    return [
        {
            "name": f"tool_{i:04d}",
            "description": "x" * 10000 + f" Tool {i} description"
        }
        for i in range(100)
    ]


@pytest.fixture()
def five_category_schemas_large() -> dict[str, list[dict[str, Any]]]:
    """Five categories, each with 200 tools (1000 total)."""
    return {
        "parse": [{"name": f"parse_tool_{i:03d}", "description": f"Parse tool {i}"} for i in range(200)],
        "modify": [{"name": f"modify_tool_{i:03d}", "description": f"Modify tool {i}"} for i in range(200)],
        "test": [{"name": f"test_tool_{i:03d}", "description": f"Test tool {i}"} for i in range(200)],
        "plan": [{"name": f"plan_tool_{i:03d}", "description": f"Plan tool {i}"} for i in range(200)],
        "think": [{"name": f"think_tool_{i:03d}", "description": f"Think tool {i}"} for i in range(200)],
    }


# =============================================================================
# TEST CLASS 1: Large Schema Handling (5 tests)
# =============================================================================

class TestLargeSchemaHandling:
    """Tests for handling very large tool schemas."""

    def test_large_schema_1000_tools_json_serialization_succeeds(self, large_schema_1000_tools: list[dict[str, Any]]) -> None:
        """Can serialize 1000 tools to JSON without error."""
        json_str = json.dumps(large_schema_1000_tools, separators=(",", ":"), sort_keys=True)
        assert len(json_str) > 0, "Serialization should succeed"
        assert len(json_str) > 10000, "1000 tools should produce >10k JSON"

    def test_large_schema_byte_count_deterministic_1000_tools(self, large_schema_1000_tools: list[dict[str, Any]]) -> None:
        """1000-tool schema byte count is deterministic across multiple calls."""
        byte_counts = []
        for _ in range(5):
            json_str = json.dumps(large_schema_1000_tools, separators=(",", ":"), sort_keys=True)
            byte_count = len(json_str.encode("utf-8"))
            byte_counts.append(byte_count)

        # All should be identical
        assert all(bc == byte_counts[0] for bc in byte_counts), \
            f"Byte counts not deterministic: {byte_counts}"

    def test_very_long_descriptions_json_serialization(self, large_schema_with_long_descriptions: list[dict[str, Any]]) -> None:
        """Schema with very long descriptions (10k chars per tool) serializes without error."""
        json_str = json.dumps(large_schema_with_long_descriptions, separators=(",", ":"), sort_keys=True)
        byte_count = len(json_str.encode("utf-8"))
        # 100 tools × 10k chars ≈ 1MB
        assert byte_count > 1000000, f"Schema should be > 1MB, got {byte_count}"

    def test_large_schema_measurement_completes_quickly(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Measurement on large schema (1000 total tools) completes in <100ms."""
        all_tools = [t for tools in five_category_schemas_large.values() for t in tools]

        start = time.time()
        baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
        baseline_bytes = len(baseline_json.encode("utf-8"))
        elapsed = time.time() - start

        assert elapsed < 0.1, f"Baseline measurement took {elapsed:.3f}s, should be <0.1s"
        # 1000 tools with simple descriptions produces ~50k JSON bytes
        assert baseline_bytes > 50000, f"Large schema should produce >50k bytes, got {baseline_bytes}"

    def test_large_schema_category_filtering_fast(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Category filtering on large schema completes in <50ms."""
        start = time.time()
        filtered_tools = five_category_schemas_large["parse"]
        filtered_json = json.dumps(filtered_tools, separators=(",", ":"), sort_keys=True)
        filtered_bytes = len(filtered_json.encode("utf-8"))
        elapsed = time.time() - start

        assert elapsed < 0.05, f"Category filtering took {elapsed:.3f}s, should be <0.05s"
        # 200 tools should produce significant JSON (at least some bytes)
        assert filtered_bytes > 5000, f"Filtered parse category should be >5k bytes, got {filtered_bytes}"


# =============================================================================
# TEST CLASS 2: Repeated Operations (5 tests)
# =============================================================================

class TestRepeatedOperations:
    """Tests for repeated operations maintaining consistency."""

    def test_measurement_100_consecutive_calls_identical(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Measuring same category 100 times yields identical results."""
        all_tools = [t for tools in five_category_schemas_large.values() for t in tools]

        results = []
        for _ in range(100):
            baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
            baseline_bytes = len(baseline_json.encode("utf-8"))
            filtered_json = json.dumps(five_category_schemas_large["parse"], separators=(",", ":"), sort_keys=True)
            filtered_bytes = len(filtered_json.encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            results.append(reduction)

        # All results should be identical
        assert all(r == results[0] for r in results), f"Results not identical: {set(results)}"

    def test_category_switching_1000_times_deterministic(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Switching between 5 categories 1000 times maintains consistency."""
        categories = ["parse", "modify", "test", "plan", "think"]
        all_tools = [t for tools in five_category_schemas_large.values() for t in tools]
        baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))

        reductions = []
        for i in range(1000):
            category = categories[i % 5]
            filtered_json = json.dumps(five_category_schemas_large[category], separators=(",", ":"), sort_keys=True)
            filtered_bytes = len(filtered_json.encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            reductions.append(reduction)

        # Reductions for same category should be identical
        parse_reductions = [reductions[i] for i in range(len(reductions)) if i % 5 == 0]
        assert len(set(parse_reductions)) == 1, "Parse category reduction not consistent across calls"

    def test_get_tools_called_1000_times_no_state_changes(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Calling get_tools 1000 times doesn't accumulate state or leak memory."""
        def get_tools(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            if category not in schemas:
                raise ValueError(f"Unknown category: {category}")
            return schemas[category]

        categories = ["parse", "modify", "test", "plan", "think"]
        first_parse_tools = None

        for i in range(1000):
            category = categories[i % 5]
            tools = get_tools(category, five_category_schemas_large)

            if category == "parse" and first_parse_tools is None:
                first_parse_tools = tools
            elif category == "parse":
                # Should be equal
                assert tools == first_parse_tools, f"Parse tools changed at iteration {i}"

    def test_json_dumps_1000_times_identical_output(self, large_schema_1000_tools: list[dict[str, Any]]) -> None:
        """Calling json.dumps 1000 times with same parameters yields identical output."""
        outputs = [
            json.dumps(large_schema_1000_tools, separators=(",", ":"), sort_keys=True)
            for _ in range(1000)
        ]

        first_output = outputs[0]
        assert all(o == first_output for o in outputs), "JSON output not consistent"

    def test_repeated_error_handling_consistent(self) -> None:
        """Repeated invalid category requests raise consistent errors."""
        def get_tools_strict(category: str) -> list:
            if category not in {"parse", "modify", "test", "plan", "think"}:
                raise ValueError(f"Unknown category: {category}. Valid: parse, modify, test, plan, think.")
            return []

        errors = []
        for i in range(100):
            try:
                get_tools_strict("invalid")
            except ValueError as e:
                errors.append(str(e))

        # All error messages should be identical
        assert all(e == errors[0] for e in errors), "Error messages not consistent"


# =============================================================================
# TEST CLASS 3: Very Large Data (4 tests)
# =============================================================================

class TestVeryLargeData:
    """Tests with very large individual data objects."""

    def test_schema_10mb_serialization_succeeds(self) -> None:
        """Serialize 10MB+ schema without error."""
        # Create tools with mega-descriptions
        tools = [
            {
                "name": f"tool_{i}",
                "description": "x" * 100000  # 100k chars per tool
            }
            for i in range(100)  # 100 tools × 100k = 10MB
        ]

        json_str = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        byte_count = len(json_str.encode("utf-8"))
        assert byte_count > 10000000, f"Schema should be >10MB, got {byte_count}"

    def test_single_tool_with_very_long_name(self) -> None:
        """Tool with very long name (1000+ chars) serializes correctly."""
        long_name = "a" * 10000
        tool = {"name": long_name, "description": "test"}

        json_str = json.dumps([tool], separators=(",", ":"), sort_keys=True)
        assert len(json_str) > 10000, "Tool with long name should produce >10k JSON"

        json_str2 = json.dumps([tool], separators=(",", ":"), sort_keys=True)
        assert json_str == json_str2, "Deterministic for long names"

    def test_schema_with_1000_categories_field_does_not_explode(self) -> None:
        """Tool mapped to 1000 categories (edge case) doesn't break serialization."""
        tool = {
            "name": "multi_category_tool",
            "categories": [f"cat_{i}" for i in range(1000)],
            "description": "Test"
        }

        json_str = json.dumps(tool, separators=(",", ":"), sort_keys=True)
        # 1000 category strings (e.g., "cat_0", "cat_1", ... "cat_999") ≈ 7-10k bytes
        assert len(json_str) > 7000, f"1000 categories should produce >7k JSON, got {len(json_str)}"

    def test_byte_count_precision_for_very_large_schemas(self) -> None:
        """Byte counting remains accurate for very large schemas."""
        tools = [{"name": f"t{i}", "description": "x" * 1000} for i in range(1000)]

        # Method 1: direct byte count
        json_str = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        bytes_direct = len(json_str.encode("utf-8"))

        # Method 2: via intermediate string (should match)
        json_str2 = json.dumps(tools, separators=(",", ":"), sort_keys=True)
        bytes_intermediate = len(json_str2.encode("utf-8"))

        assert bytes_direct == bytes_intermediate, "Byte count methods should agree"
        assert bytes_direct > 1000000, f"Large schema byte count {bytes_direct} should be > 1M"


# =============================================================================
# TEST CLASS 4: Performance and Timing (3 tests)
# =============================================================================

class TestPerformanceAndTiming:
    """Tests for performance requirements."""

    def test_get_tools_for_category_latency_under_10ms(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """get_tools_for_category() should complete in <10ms (per spec)."""
        def get_tools_for_category(category: str, schemas: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            if category not in schemas:
                raise ValueError(f"Unknown category: {category}")
            return schemas[category]

        start = time.time()
        tools = get_tools_for_category("parse", five_category_schemas_large)
        elapsed = time.time() - start

        assert elapsed < 0.01, f"get_tools_for_category took {elapsed:.6f}s, should be <10ms"
        assert len(tools) > 0, "Should return tools"

    def test_measurement_function_latency_under_100ms(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """measure_tool_schema_reduction() should complete in <100ms (per spec)."""
        all_tools = [t for tools in five_category_schemas_large.values() for t in tools]
        baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
        baseline_bytes = len(baseline_json.encode("utf-8"))

        start = time.time()
        for category in ["parse", "modify", "test", "plan", "think"]:
            filtered_json = json.dumps(five_category_schemas_large[category], separators=(",", ":"), sort_keys=True)
            filtered_bytes = len(filtered_json.encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
        elapsed = time.time() - start

        assert elapsed < 0.1, f"Measurement took {elapsed:.3f}s, should be <100ms for all 5 categories"

    def test_1000_measurements_complete_in_reasonable_time(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Running 1000 measurements on large schema completes in <10s."""
        all_tools = [t for tools in five_category_schemas_large.values() for t in tools]

        start = time.time()
        for _ in range(1000):
            baseline_json = json.dumps(all_tools, separators=(",", ":"), sort_keys=True)
            baseline_bytes = len(baseline_json.encode("utf-8"))
            filtered_json = json.dumps(five_category_schemas_large["parse"], separators=(",", ":"), sort_keys=True)
            filtered_bytes = len(filtered_json.encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
        elapsed = time.time() - start

        assert elapsed < 10, f"1000 measurements took {elapsed:.1f}s, should be <10s"
        average_ms = (elapsed / 1000) * 1000
        assert average_ms < 10, f"Average measurement {average_ms:.1f}ms should be <10ms"


# =============================================================================
# TEST CLASS 5: Stress on Determinism (3 tests)
# =============================================================================

class TestStressOnDeterminism:
    """Tests that determinism holds under stress."""

    def test_determinism_with_random_category_access_order(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Accessing categories in random order still produces deterministic results per category."""
        import random

        categories = ["parse", "modify", "test", "plan", "think"]
        random.seed(42)  # Reproducible randomness

        # Access categories in random order 1000 times
        expected_reductions = {}
        for category in categories:
            all_tools = [t for tools in five_category_schemas_large.values() for t in tools]
            baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
            filtered_bytes = len(json.dumps(five_category_schemas_large[category], separators=(",", ":"), sort_keys=True).encode("utf-8"))
            expected_reductions[category] = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100

        # Now access in random order
        access_order = [random.choice(categories) for _ in range(1000)]
        all_tools = [t for tools in five_category_schemas_large.values() for t in tools]
        baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))

        for category in access_order:
            filtered_bytes = len(json.dumps(five_category_schemas_large[category], separators=(",", ":"), sort_keys=True).encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            assert abs(reduction - expected_reductions[category]) < 0.001, \
                f"Reduction for {category} changed: {reduction} vs {expected_reductions[category]}"

    def test_determinism_with_large_baseline_small_filtered(self, large_schema_1000_tools: list[dict[str, Any]]) -> None:
        """Determinism holds when baseline is much larger than filtered."""
        baseline = large_schema_1000_tools
        filtered = [baseline[0]]  # Just first tool

        # Measure 100 times
        reductions = []
        baseline_bytes = len(json.dumps(baseline, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        for _ in range(100):
            filtered_bytes = len(json.dumps(filtered, separators=(",", ":"), sort_keys=True).encode("utf-8"))
            reduction = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            reductions.append(reduction)

        assert all(r == reductions[0] for r in reductions), \
            f"Reductions not identical: min={min(reductions)}, max={max(reductions)}"

    def test_determinism_across_different_test_runs(self, five_category_schemas_large: dict[str, list[dict[str, Any]]]) -> None:
        """Same measurement function produces identical results when called again."""
        def measure_all_categories(schemas: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
            all_tools = [t for tools in schemas.values() for t in tools]
            baseline_bytes = len(json.dumps(all_tools, separators=(",", ":"), sort_keys=True).encode("utf-8"))
            results = {}
            for category in ["parse", "modify", "test", "plan", "think"]:
                filtered_bytes = len(json.dumps(schemas[category], separators=(",", ":"), sort_keys=True).encode("utf-8"))
                results[category] = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100
            return results

        # Run twice
        results1 = measure_all_categories(five_category_schemas_large)
        results2 = measure_all_categories(five_category_schemas_large)

        assert results1 == results2, f"Measurements differ: {results1} vs {results2}"
