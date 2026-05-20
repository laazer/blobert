"""Agent invocation middleware with tool category filtering.

This module provides a middleware layer that sits at the invocation boundary
between blobert and the external Claude Code / Claude Agent SDK framework.

The middleware:
1. Extracts tool category declarations from agent input prompts using regex
2. Filters tools based on the declared category via get_tools_for_category()
3. Delegates to the external framework with filtered tools
4. Handles errors gracefully (invalid categories → all tools, log warning)
5. Maintains backward compatibility (agents without category declaration receive all tools)

References:
- Spec: project_board/specs/902_18T5_tool_categorization_framework_integration_spec.md
- Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/00_backlog/18a_tool_categorization_framework_integration.md
- Tool Category Manager: ci/scripts/tool_category_manager.py
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

try:
    # Try relative import first (when imported as module)
    from .tool_category_manager import get_tools_for_category, VALID_CATEGORIES
except ImportError:
    # Fall back to direct import (when run as script or in test context)
    from tool_category_manager import get_tools_for_category, VALID_CATEGORIES


# Compile regex pattern once at module level for performance (NFR-2)
_CATEGORY_EXTRACTION_PATTERN = re.compile(
    r"(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)",
    re.IGNORECASE
)

# Configure module-level logger
_logger = logging.getLogger(__name__)


def extract_category_from_prompt(prompt: str) -> str | None:
    """Extract tool category declaration from agent prompt.

    Searches the prompt for a category declaration using the normative regex
    pattern from the specification. Returns the extracted category (lowercase) if
    valid, None otherwise.

    The extraction pattern matches three declaration formats (case-insensitive):
    1. "I declare tool category: parse"
    2. "My workflow category is: modify"
    3. "Tool category: test"

    If multiple declarations exist, the first match wins (deterministic).
    Extracted category is normalized to lowercase before validation.

    Args:
        prompt: Agent input prompt string (may contain category declaration).

    Returns:
        Extracted category name (lowercase) if valid declaration found, None otherwise.
        Returns None for:
        - Prompts with no category declaration
        - Malformed declarations (missing category name after colon)
        - Invalid category names (not in VALID_CATEGORIES)

    Examples:
        >>> extract_category_from_prompt("I declare tool category: parse\n\nRead the spec")
        'parse'
        >>> extract_category_from_prompt("My workflow category is: modify\n\nImplement feature")
        'modify'
        >>> extract_category_from_prompt("Write spec")
        None
        >>> extract_category_from_prompt("I declare tool category: invalid_cat")
        None
    """
    # Search for category declaration in prompt
    match = _CATEGORY_EXTRACTION_PATTERN.search(prompt)
    if match is None:
        # No declaration found
        return None

    # Extract and normalize category name to lowercase
    extracted_category = match.group(1).lower()

    # Validate category against VALID_CATEGORIES
    if extracted_category not in VALID_CATEGORIES:
        # Invalid category (not in valid set)
        return None

    return extracted_category


def invoke_agent_with_category_filtering(
    agent_type: str,
    prompt: str,
    all_tools: list[dict[str, Any]],
    framework_invocation_fn: Callable[..., Any],
    **framework_kwargs: Any,
) -> Any:
    """Invoke agent with tool category filtering.

    This is the primary middleware function that sits at the invocation boundary.
    It extracts tool category from the prompt, filters tools accordingly, and
    delegates to the external framework with the filtered tool set.

    The function is fail-safe: if category extraction or filtering fails, it
    falls back to all tools and logs a warning. Framework exceptions propagate
    unchanged.

    Invocation flow:
    1. Extract category from prompt using extract_category_from_prompt()
    2. Validate category and call get_tools_for_category() if valid
    3. Catch ValueError/RuntimeError from get_tools_for_category() → fallback to all tools
    4. Call framework_invocation_fn with filtered (or all) tools
    5. Return framework result unchanged

    Args:
        agent_type: Type/name of agent (e.g., "spec", "implementation", "test_designer").
                    Used for logging context.
        prompt: Agent input prompt. May contain category declaration. Passed unchanged
                to framework.
        all_tools: All available tools before filtering. Must be a list of dicts.
                   Passed unchanged to framework if no valid category is declared.
        framework_invocation_fn: Callable (function or method) that invokes the
                                 external framework. Must accept at minimum:
                                 agent_type, prompt, tools. Any exceptions raised
                                 by this function propagate to the caller.
        **framework_kwargs: Additional keyword arguments to pass to
                           framework_invocation_fn (beyond agent_type, prompt, tools).

    Returns:
        Result from framework_invocation_fn, unchanged (opaque to middleware).

    Raises:
        TypeError: If framework_invocation_fn is not callable.
        Any exception raised by framework_invocation_fn propagates unchanged.

    Examples:
        >>> mock_framework = lambda agent_type, prompt, tools, **kw: {"status": "ok"}
        >>> result = invoke_agent_with_category_filtering(
        ...     agent_type="spec",
        ...     prompt="I declare tool category: parse\n\nWrite spec...",
        ...     all_tools=[{"name": "read"}, {"name": "write"}],
        ...     framework_invocation_fn=mock_framework
        ... )
        >>> result["status"]
        'ok'
    """
    # Validate framework_invocation_fn is callable
    if not callable(framework_invocation_fn):
        raise TypeError(
            f"framework_invocation_fn must be callable, got {type(framework_invocation_fn).__name__}"
        )

    # Step 1: Extract category from prompt
    category = extract_category_from_prompt(prompt)

    # Step 2: Determine which tools to use
    tools_to_use = all_tools
    if category is not None:
        # Category was extracted and validated; try to filter
        try:
            filtered_tools = get_tools_for_category(category)
            tools_to_use = filtered_tools
            _logger.info(
                f"Agent '{agent_type}' using category '{category}' with {len(tools_to_use)} tools"
            )
        except ValueError as e:
            # Invalid category (should not happen since extract_category_from_prompt validates,
            # but catch for safety)
            _logger.warning(
                f"Agent '{agent_type}' declared invalid category '{category}'; "
                f"falling back to all {len(all_tools)} tools. Error: {e}"
            )
            tools_to_use = all_tools
        except RuntimeError as e:
            # Config error (file missing, malformed JSON, etc.)
            _logger.error(
                f"Agent '{agent_type}' category filtering failed due to config error; "
                f"falling back to all {len(all_tools)} tools. Error: {e}"
            )
            tools_to_use = all_tools
    else:
        # No category declaration or invalid category
        _logger.info(
            f"Agent '{agent_type}' using all {len(all_tools)} tools (no category declaration)"
        )

    # Step 3: Call framework with filtered (or all) tools
    result = framework_invocation_fn(
        agent_type=agent_type,
        prompt=prompt,
        tools=tools_to_use,
        **framework_kwargs,
    )

    # Step 4: Return framework result unchanged
    return result
