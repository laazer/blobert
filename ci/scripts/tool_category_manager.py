"""Tool categorization manager for agent context optimization.

Provides tool filtering by semantic category (parse, modify, test, plan, think)
to reduce agent context overhead by 15-25%.

Functions:
- get_tools_for_category(category: str) -> list[dict[str, Any]]
- measure_tool_schema_reduction(category: str) -> dict[str, Any]

References:
- Spec: project_board/specs/902_18_tool_categorization_spec.md
- Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/18_tool_categorization_layer.md
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


# Path to the tool categories configuration file (relative to script location)
TOOL_CATEGORIES_CONFIG = Path(__file__).parent / "tool_categories.json"

# Valid category names (constant enum)
VALID_CATEGORIES = {"parse", "modify", "test", "plan", "think"}


def get_tools_for_category(category: str) -> list[dict[str, Any]]:
    """Return the list of tools available in the specified category.

    Loads tool definitions from tool_categories.json and filters by the given
    category. Returns deterministic tool list suitable for agent invocation.

    Args:
        category: One of 'parse', 'modify', 'test', 'plan', 'think'.
                  Case-sensitive (lowercase expected).

    Returns:
        List of tool definition dicts for the category. Each dict contains
        'name', 'categories', and 'rationale'. Empty list if category exists
        but has no tools (should not occur per spec AC-1.5, AC-2.3).

    Raises:
        ValueError: If category is unknown (not one of the five valid categories).
                    Message includes list of valid categories.
        RuntimeError: If tool_categories.json cannot be loaded or is malformed.
                      Message includes file location and error detail.

    Examples:
        >>> tools = get_tools_for_category("parse")
        >>> len(tools) > 0
        True
        >>> all("name" in t for t in tools)
        True
        >>> get_tools_for_category("invalid")
        Traceback (most recent call last):
            ...
        ValueError: Unknown category: invalid. Valid categories: parse, modify, test, plan, think.
    """
    # Validate category parameter
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Unknown category: {category}. Valid categories: {', '.join(sorted(VALID_CATEGORIES))}."
        )

    # Load configuration from JSON file
    try:
        if not TOOL_CATEGORIES_CONFIG.exists():
            raise RuntimeError(
                f"Tool categories configuration not found: {TOOL_CATEGORIES_CONFIG}"
            )
        with open(TOOL_CATEGORIES_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse tool categories config at {TOOL_CATEGORIES_CONFIG}: {e}"
        ) from e
    except IOError as e:
        raise RuntimeError(
            f"Failed to read tool categories config at {TOOL_CATEGORIES_CONFIG}: {e}"
        ) from e

    # Validate config structure
    if not isinstance(config, dict):
        raise RuntimeError(
            f"Tool categories config must be a JSON object, got {type(config).__name__}"
        )
    if "tools" not in config:
        raise RuntimeError(
            f"Tool categories config missing 'tools' key at {TOOL_CATEGORIES_CONFIG}"
        )
    if not isinstance(config["tools"], list):
        raise RuntimeError(
            f"'tools' key must be a list, got {type(config['tools']).__name__}"
        )

    # Filter tools by category
    tools_list = []
    for tool in config["tools"]:
        if not isinstance(tool, dict):
            continue
        tool_categories = tool.get("categories", [])
        if category in tool_categories:
            tools_list.append(tool)

    return tools_list


def measure_tool_schema_reduction(category: str) -> dict[str, Any]:
    """Measure schema size reduction for a tool category.

    Computes the byte count reduction achieved by filtering tools to a specific
    category compared to the full tool schema. Uses JSON byte count (UTF-8 encoded,
    no whitespace) as the measurement metric per spec AC-6.3.

    The measurement is deterministic: same input → same byte counts across
    multiple runs (verified via consistent JSON serialization with sorted keys
    and no whitespace).

    Args:
        category: One of 'parse', 'modify', 'test', 'plan', 'think'.

    Returns:
        dict[str, Any] with keys:
        - 'category': str, the input category name
        - 'baseline_bytes': int, byte count of all tools JSON
        - 'filtered_bytes': int, byte count of category tools JSON
        - 'reduction_percent': float, reduction percentage (0–100)
        - 'tool_count_baseline': int, count of all unique tools
        - 'tool_count_filtered': int, count of category tools
        - 'timestamp': str, ISO 8601 timestamp of measurement

    Raises:
        ValueError: If category is unknown (same as get_tools_for_category).
        RuntimeError: If config cannot be loaded (same as get_tools_for_category).

    Examples:
        >>> result = measure_tool_schema_reduction("parse")
        >>> 0 <= result["reduction_percent"] <= 100
        True
        >>> result["baseline_bytes"] > result["filtered_bytes"]
        True
        >>> "timestamp" in result and len(result["timestamp"]) > 0
        True
    """
    # Validate category (will raise ValueError if invalid)
    _ = get_tools_for_category(category)

    # Load full config to get all tools for baseline measurement
    try:
        with open(TOOL_CATEGORIES_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(
            f"Failed to load tool categories config: {e}"
        ) from e

    # Collect all unique tools (union across all categories)
    all_tools_dict: dict[str, dict[str, Any]] = {}
    for tool in config.get("tools", []):
        if isinstance(tool, dict) and "name" in tool:
            all_tools_dict[tool["name"]] = tool

    all_tools_list = list(all_tools_dict.values())

    # Get filtered tools for the category
    filtered_tools = get_tools_for_category(category)

    # Compute byte counts using deterministic JSON serialization
    # (no whitespace, sorted keys for consistent output)
    baseline_json = json.dumps(
        sorted(all_tools_list, key=lambda t: t.get("name", "")),
        separators=(",", ":"),
        sort_keys=True
    )
    baseline_bytes = len(baseline_json.encode("utf-8"))

    filtered_json = json.dumps(
        sorted(filtered_tools, key=lambda t: t.get("name", "")),
        separators=(",", ":"),
        sort_keys=True
    )
    filtered_bytes = len(filtered_json.encode("utf-8"))

    # Calculate reduction percentage
    if baseline_bytes == 0:
        reduction_percent = 0.0
    else:
        reduction_percent = ((baseline_bytes - filtered_bytes) / baseline_bytes) * 100.0

    # Format timestamp in ISO 8601
    timestamp = datetime.utcnow().isoformat() + "Z"

    return {
        "category": category,
        "baseline_bytes": baseline_bytes,
        "filtered_bytes": filtered_bytes,
        "reduction_percent": reduction_percent,
        "tool_count_baseline": len(all_tools_list),
        "tool_count_filtered": len(filtered_tools),
        "timestamp": timestamp,
    }


if __name__ == "__main__":
    # Example: demonstrate tool categorization and measurement
    import sys

    if len(sys.argv) > 1:
        requested_category = sys.argv[1]
        try:
            tools = get_tools_for_category(requested_category)
            print(f"Tools in category '{requested_category}': {[t['name'] for t in tools]}")
            measurement = measure_tool_schema_reduction(requested_category)
            print(f"Reduction: {measurement['reduction_percent']:.1f}%")
        except (ValueError, RuntimeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Show all categories and their tool counts
        for cat in sorted(VALID_CATEGORIES):
            tools = get_tools_for_category(cat)
            print(f"{cat:10} : {len(tools)} tools  →  {[t['name'] for t in tools]}")
