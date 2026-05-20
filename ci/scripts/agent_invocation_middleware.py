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
import os
import re
from pathlib import Path
from typing import Any, Callable, TypedDict

# Relative import per module convention (collocated service modules).
# Tests and dynamic imports are mocked/patched; no fallback needed.
from .context_budget_tracker import record_stage_usage
from .tool_category_manager import get_tools_for_category, VALID_CATEGORIES


# Tool definition schema: enforces required fields for all tool dicts.
# Each tool MUST have name, categories, and rationale for filtering and logging.
class ToolDefinition(TypedDict):
    """Tool definition with semantic categorization.

    Fields:
        name: Tool identifier (e.g., 'read', 'write', 'bash').
        categories: List of semantic categories (subset of 'parse', 'modify', 'test', 'plan', 'think').
        rationale: Human-readable description of the tool's purpose.
    """
    name: str
    categories: list[str]
    rationale: str


# Compile regex pattern once at module level for performance (NFR-2)
_CATEGORY_EXTRACTION_PATTERN = re.compile(
    r"(?:I declare tool category|My workflow category is|Tool category):\s*(\w+)",
    re.IGNORECASE
)

# Configure module-level logger
_logger = logging.getLogger(__name__)
_context_budget_skip_logged = False


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
    all_tools: list[ToolDefinition],
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
        all_tools: All available tools before filtering. Each tool MUST conform to
                   ToolDefinition schema (name, categories, rationale).
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
        ...     all_tools=[{"name": "read", "categories": ["parse"], "rationale": "Read"}],
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

    _maybe_record_context_budget(
        agent_type=agent_type,
        prompt=prompt,
        tools_to_use=tools_to_use,
        all_tools_count=len(all_tools),
        category=category,
        framework_result=result,
        framework_kwargs=framework_kwargs,
    )

    # Step 4: Return framework result unchanged
    return result


def _maybe_record_context_budget(
    *,
    agent_type: str,
    prompt: str,
    tools_to_use: list[ToolDefinition],
    all_tools_count: int,
    category: str | None,
    framework_result: Any,
    framework_kwargs: dict[str, Any],
) -> None:
    """Post-invocation context budget hook (M902-21). Opt-out: CONTEXT_BUDGET_TRACKING=0."""
    global _context_budget_skip_logged  # noqa: PLW0603

    if os.environ.get("CONTEXT_BUDGET_TRACKING") == "0":
        return

    ticket_id = framework_kwargs.get("ticket_id")
    agent_run_id = framework_kwargs.get("agent_run_id")
    if not ticket_id or not agent_run_id:
        if not _context_budget_skip_logged:
            _logger.debug(
                "context budget tracking skipped: missing ticket_id or agent_run_id"
            )
            _context_budget_skip_logged = True
        return

    checkpoints_root = framework_kwargs.get("checkpoints_root")
    root_path = Path(checkpoints_root) if checkpoints_root is not None else None

    tool_category_state: dict[str, Any] | None = None
    if category is not None:
        tool_category_state = {
            "categorization_active": True,
            "category": category,
            "tools_before": all_tools_count,
            "tools_after": len(tools_to_use),
        }

    try:
        record_stage_usage(
            str(ticket_id),
            agent_type=agent_type,
            prompt=prompt,
            tools=list(tools_to_use),
            framework_result=framework_result,
            agent_run_id=str(agent_run_id),
            workflow_stage=framework_kwargs.get("workflow_stage"),
            stage_key=framework_kwargs.get("stage_key"),
            ticket_path=framework_kwargs.get("ticket_path"),
            ticket_type=framework_kwargs.get("ticket_type"),
            checkpoints_root=root_path,
            tool_category_state=tool_category_state,
        )
    except Exception:  # noqa: BLE001 — tracking must not break invocations
        _logger.exception("context budget tracking failed for ticket %s", ticket_id)
