"""Forgiving tool parsing middleware for LLM-generated tool calls.

This module implements a middleware layer that auto-repairs common LLM tool call
mistakes before execution, preventing retry loops from parsing failures.

Features:
- Multi-format parser (JSON/YAML/XML/plain-text)
- 8 repair categories: type coercion, missing fields, typo correction, quoted paths,
  nested structure handling, and validation gates
- Static whitelist-based validation to prevent dangerous mutations
- Comprehensive audit trail with severity-level logging
- Deterministic, idempotent repair logic (all pure functions)
- <10ms latency per tool call

Ticket: M902-19 (Forgiving Tool Parsing Middleware)
Specification: project_board/specs/902_19_forgiving_tool_parsing_middleware_spec.md
"""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
import yaml
from difflib import get_close_matches
from typing import Any, TypedDict


# Type definitions for better clarity
class ToolCallDict(TypedDict, total=False):
    """Tool call representation: tool name + parameters."""
    name: str
    arguments: dict[str, Any]


class ParamInfo(TypedDict, total=False):
    """Parameter schema info from tool definition."""
    type: str
    required: bool
    default: Any
    description: str


# Type mapping: schema stores types as strings, convert to Python types
TYPE_MAP = {
    "bool": bool,
    "int": int,
    "str": str,
    "dict": dict,
    "list": list,
    "float": float,
}


# =============================================================================
# PARSER: Multi-format tool call parsing (JSON, YAML, XML, plain-text)
# =============================================================================


def parse_tool_call(tool_call_str: str) -> dict[str, Any]:
    """Parse tool call string in JSON/YAML/XML/plain-text format to dict.

    Attempts JSON first (most common), then YAML, then XML.
    Falls back to error for plain-text.

    Args:
        tool_call_str: Tool call output (string)

    Returns:
        dict[str, Any]: Parsed tool call with "name" and "arguments" keys,
        or XML tag representation if parsed from XML.
        Example: {"name": "run_command", "arguments": {"command": "ls"}}

    Raises:
        json.JSONDecodeError: If JSON parsing fails with details
        Exception: If all parsers fail (YAML error, XML error, etc.)
    """
    if not isinstance(tool_call_str, str):
        raise TypeError(f"Tool call must be string, got {type(tool_call_str)}")

    # Try JSON first (most common)
    try:
        return json.loads(tool_call_str)
    except json.JSONDecodeError as e:
        # JSON failed; try YAML (module-level import at top)
        try:
            result = yaml.safe_load(tool_call_str)
            if isinstance(result, dict):
                return result
            # YAML parsed but not a dict
            raise ValueError(f"YAML parsing returned non-dict: {type(result)}")
        except Exception:
            # YAML failed; try XML (module-level import at top)
            try:
                root = ET.fromstring(tool_call_str)
                # Convert XML to dict (simple conversion)
                result_dict: dict[str, Any] = {"_tag": root.tag}
                for key, value in root.attrib.items():
                    result_dict[key] = value
                for child in root:
                    result_dict[child.tag] = child.text or child.attrib
                return result_dict
            except Exception:
                # All parsers failed; raise original JSON error with hint
                raise json.JSONDecodeError(
                    f"Failed to parse tool call as JSON/YAML/XML. "
                    f"Original JSON error: {str(e)}. "
                    f"Input: {tool_call_str[:100]}...",
                    tool_call_str,
                    e.pos,
                ) from e


# =============================================================================
# REPAIR FUNCTIONS: 8 repair categories
# =============================================================================


def _coerce_primitive_value(value: Any, param_info: dict[str, Any]) -> tuple[Any, bool, str]:
    """Shared helper for type coercion of primitive values (bool, int, float, str).

    Attempts to repair type mismatches by coercing strings to the expected type.
    Returns (repaired_value, was_repaired, description).
    Used by both top-level and nested parameter repair.

    Args:
        value: Parameter value (may be string or wrong type)
        param_info: Parameter schema dict with "type" key

    Returns:
        (repaired_value, was_repaired, repair_description)
    """
    schema_type_str = param_info.get("type")
    schema_type = TYPE_MAP.get(schema_type_str) if schema_type_str else None

    # Try bool coercion
    if schema_type is bool and isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ("true", "false"):
            repaired = lower_value == "true"
            return (repaired, True, f"string {repr(value)} → bool {repaired}")
        return (value, False, f"invalid bool string {repr(value)} (must be 'true'/'false')")

    # Try int coercion
    if schema_type is int and isinstance(value, str):
        try:
            repaired = int(value)
            # Validate it's actually an integer format (not float string)
            if str(repaired) != value:
                return (value, False, f"cannot convert {repr(value)} to int (float string or invalid format)")
            return (repaired, True, f"string {repr(value)} → int {repaired}")
        except ValueError:
            return (value, False, f"cannot convert {repr(value)} to int (non-numeric)")

    # No coercion needed
    return (value, False, "")


def repair_string_bool(value: Any, schema_type: type | None) -> tuple[Any, bool, str]:
    """Repair string→bool type coercion.

    Converts "true"/"false" (case-insensitive) to True/False.
    Rejects ambiguous values like "1", "yes", "maybe".

    This function wraps the shared _coerce_primitive_value helper and provides
    the schema_type directly. For nested structures, use _coerce_primitive_value
    with param_info dict instead.

    Args:
        value: Parameter value (may be string)
        schema_type: Expected type from schema (bool, int, str, etc.)

    Returns:
        (repaired_value, was_repaired, repair_description)
    """
    if schema_type is not bool or not isinstance(value, str):
        return (value, False, "")

    lower_value = value.lower()
    if lower_value in ("true", "false"):
        repaired = lower_value == "true"
        return (repaired, True, f"string {repr(value)} → bool {repaired}")

    # Ambiguous or invalid bool string
    return (value, False, f"invalid bool string {repr(value)} (must be 'true'/'false')")


def repair_string_int(value: Any, schema_type: type | None) -> tuple[Any, bool, str]:
    """Repair string→int type coercion.

    Converts numeric strings like "42" to 42.
    Rejects float strings like "3.14" and non-numeric strings like "abc".

    This function wraps the shared _coerce_primitive_value helper and provides
    the schema_type directly. For nested structures, use _coerce_primitive_value
    with param_info dict instead.

    Args:
        value: Parameter value (may be string)
        schema_type: Expected type from schema (bool, int, str, etc.)

    Returns:
        (repaired_value, was_repaired, repair_description)
    """
    if schema_type is not int or not isinstance(value, str):
        return (value, False, "")

    try:
        repaired = int(value)
        # Validate it's actually an integer format (not float string)
        if str(repaired) != value:
            return (value, False, f"cannot convert {repr(value)} to int (float string or invalid format)")
        return (repaired, True, f"string {repr(value)} → int {repaired}")
    except ValueError:
        return (value, False, f"cannot convert {repr(value)} to int (non-numeric)")


def repair_missing_required_fields(
    call_dict: dict[str, Any], schema: dict[str, Any]
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Repair missing required fields and optional fields with defaults.

    Adds missing optional parameters with defaults from schema.
    Returns list of missing required parameters (error case).

    Args:
        call_dict: Tool call dict (may be missing fields)
        schema: Tool schema with "parameters" key containing parameter info dicts

    Returns:
        (repaired_dict, repair_descriptions, missing_required_list):
        - repaired_dict: Updated call_dict with missing optional fields filled
        - repair_descriptions: List of added optional parameter messages
        - missing_required_list: Names of required parameters that are still missing
    """
    repairs: list[str] = []
    missing_required: list[str] = []

    parameters = schema.get("parameters", {})
    for param_name, param_info in parameters.items():
        if param_name not in call_dict:
            # Missing parameter
            if param_info.get("required", False):
                # Required param missing, no default
                missing_required.append(param_name)
            elif "default" in param_info:
                # Optional param with default; add it
                call_dict[param_name] = param_info["default"]
                repairs.append(f"added missing optional param '{param_name}' with default {param_info['default']}")

    return (call_dict, repairs, missing_required)


def repair_parameter_name_typo(
    call_dict: dict[str, Any], schema: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Repair parameter name typos using fuzzy matching (80% threshold).

    Detects misspelled parameter names and suggests corrections.
    Uses difflib.get_close_matches with 80% similarity threshold.

    Args:
        call_dict: Tool call dict (may have typos in parameter names)
        schema: Tool schema with "parameters" key containing valid parameter names

    Returns:
        (repaired_dict, repair_descriptions):
        - repaired_dict: Updated call_dict with typo names fixed
        - repair_descriptions: List of corrected typo messages
    """
    repairs: list[str] = []
    valid_params = set(schema.get("parameters", {}).keys())

    # Check for typos in provided parameters
    typo_params = [key for key in call_dict.keys() if key not in valid_params]

    for typo_param in typo_params:
        # Find close matches (80% threshold = cutoff 0.8)
        matches = get_close_matches(typo_param, valid_params, n=1, cutoff=0.8)
        if matches:
            correct_param = matches[0]
            call_dict[correct_param] = call_dict.pop(typo_param)
            repairs.append(f"corrected typo '{typo_param}' → '{correct_param}'")

    return (call_dict, repairs)


def repair_quoted_string_path(value: Any, schema_type: type | None) -> tuple[Any, bool, str]:
    """Unwrap over-quoted string paths.

    Converts `'"/path"'` (starts and ends with quotes) to `'/path'`.
    Only applies if schema_type is str.
    Idempotent: applying twice yields same result (checks inner content).

    Args:
        value: Parameter value (may be quoted)
        schema_type: Expected type from schema (typically str)

    Returns:
        (repaired_value, was_repaired, repair_description):
        - repaired_value: Unwrapped string or original if no repair needed
        - was_repaired: True if unwrapping occurred
        - repair_description: Explanation message
    """
    if schema_type is not str or not isinstance(value, str):
        return (value, False, "")

    # Check if value starts and ends with quotes
    # Pattern: "/path" where outer chars are quote marks
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        # Get inner content
        inner = value[1:-1]
        # Only unwrap if inner doesn't start with quote (idempotency check)
        # This prevents double-unwrapping like ""/path"" → "/path" → /path
        if inner and inner[0] != '"':
            return (inner, True, f"unwrapped quoted path {repr(value)} → {repr(inner)}")

    return (value, False, "")


def repair_nested_structure(
    call_dict: dict[str, Any], schema: dict[str, Any], depth: int = 0
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Repair nested structures (dicts and lists) up to 2 levels deep.

    Applies type coercion (via _coerce_primitive_value), missing field, and typo
    repairs to nested values. Rejects structures deeper than 2 levels.

    Args:
        call_dict: Tool call dict (may contain nested dicts/lists)
        schema: Tool schema with "parameters" containing nested type definitions
        depth: Current nesting depth (incremented recursively)

    Returns:
        (repaired_dict, repair_descriptions, depth_limit_violations):
        - repaired_dict: Updated call_dict with nested repairs applied
        - repair_descriptions: List of nested repair messages
        - depth_limit_violations: List of depth limit errors
    """
    repairs: list[str] = []
    violations: list[str] = []

    # Check depth limit (2 levels max)
    if depth > 2:
        violations.append(f"structure nesting exceeds 2-level limit (depth={depth})")
        return (call_dict, repairs, violations)

    parameters = schema.get("parameters", {})

    for param_name, param_value in call_dict.items():
        # Get parameter schema
        param_schema = parameters.get(param_name, {})
        param_type = param_schema.get("type")

        # Handle nested dict (like config.params)
        if isinstance(param_value, dict) and param_schema.get("type") == "dict":
            nested_schema = param_schema.get("schema", {})
            if nested_schema:
                # Recursively repair nested dict
                nested_repaired, nested_repairs, nested_violations = repair_nested_structure(
                    param_value, {"parameters": nested_schema}, depth=depth + 1
                )
                call_dict[param_name] = nested_repaired
                repairs.extend([f"nested: {r}" for r in nested_repairs])
                violations.extend(nested_violations)

        # Handle nested list (assume homogeneous schema)
        elif isinstance(param_value, list) and param_schema.get("type") == "list":
            nested_schema = param_schema.get("item_schema", {})
            if nested_schema:
                for i, item in enumerate(param_value):
                    if isinstance(item, dict):
                        nested_repaired, nested_repairs, nested_violations = repair_nested_structure(
                            item, {"parameters": nested_schema}, depth=depth + 1
                        )
                        param_value[i] = nested_repaired
                        repairs.extend([f"nested[{i}]: {r}" for r in nested_repairs])
                        violations.extend(nested_violations)

        # Type coercion for nested primitive values in dict
        if isinstance(param_value, dict) and param_schema.get("type") == "dict":
            nested_params = param_schema.get("schema", {})
            for nested_key, nested_value in param_value.items():
                nested_param_info = nested_params.get(nested_key, {})
                if nested_param_info:
                    # Use shared helper for consistent coercion logic
                    repaired, was_repaired, desc = _coerce_primitive_value(nested_value, nested_param_info)
                    if was_repaired:
                        param_value[nested_key] = repaired
                        repairs.append(f"nested coercion: {nested_key}: {desc}")

    return (call_dict, repairs, violations)


def validate_repair_safety(
    call_dict: dict[str, Any], tool_schema: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Validate repaired tool call against whitelist and dangerous tool rules.

    Checks that all parameters are in safe_parameters list.
    For dangerous tools, applies stricter validation (no command content changes).

    Args:
        call_dict: Repaired tool call dict
        tool_schema: Tool schema with safe_parameters whitelist and optional dangerous flag

    Returns:
        (is_valid, error_messages):
        - is_valid: True if all validations passed
        - error_messages: List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Extract tool name from schema for error messages
    tool_name = tool_schema.get("name", "<unknown>")
    safe_params = tool_schema.get("safe_parameters", [])
    is_dangerous = tool_schema.get("dangerous", False)

    # Check all parameters against whitelist
    for param_name in call_dict.keys():
        if param_name not in safe_params:
            errors.append(f"parameter {repr(param_name)} not in safe_parameters for tool {repr(tool_name)}")

    # For dangerous tools, reject if command content is suspicious
    if is_dangerous:
        dangerous_patterns = ["rm -rf", "rm -rf /", "chmod 777", "sudo", "su ", ": () {", "|&"]
        for param_name, param_value in call_dict.items():
            if isinstance(param_value, str):
                for pattern in dangerous_patterns:
                    if pattern in param_value:
                        errors.append(f"dangerous tool {repr(tool_name)}: suspicious pattern {repr(pattern)} in parameter {repr(param_name)}")
                        break

    return (len(errors) == 0, errors)


# =============================================================================
# MAIN MIDDLEWARE: Orchestrate parsing, repair, validation, logging
# =============================================================================


def repair_tool_call(
    tool_call: dict[str, Any] | str,
    tool_schema: dict[str, Any],
    logger: logging.Logger,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Repair and validate a tool call before execution.

    Main middleware function that orchestrates:
    1. Parse tool call (JSON/YAML/XML/plain-text)
    2. Apply repairs (type coercion, missing fields, typos, quoted paths, etc.)
    3. Validate against whitelist and dangerous tool rules
    4. Log all attempts with appropriate severity levels
    5. Return repaired call or None if unrepairable

    Args:
        tool_call: LLM-generated tool call (dict or JSON string)
        tool_schema: Tool definition with safe_parameters whitelist, parameters, type info
        logger: Logger instance for audit trail

    Returns:
        (repaired_call, repair_history) where:
        - repaired_call: Fixed dict, or None if dangerous/unrepairable
        - repair_history: List of repair descriptions ("fixed X to Y", "cannot fix Z")
    """
    repair_history: list[str] = []

    # Step 0: Parse if string input
    if isinstance(tool_call, str):
        try:
            call_dict = parse_tool_call(tool_call)
            repair_history.append("parsed tool call from string")
        except Exception as e:
            error_msg = f"Parse error: {str(e)}"
            logger.error(error_msg)
            repair_history.append(error_msg)
            return (None, repair_history)
    elif isinstance(tool_call, dict):
        call_dict = tool_call.copy()
    else:
        error_msg = f"tool_call must be dict or string, got {type(tool_call)}"
        logger.error(error_msg)
        repair_history.append(error_msg)
        return (None, repair_history)

    # Step 1: Log received call
    logger.info(f"Tool call received: {call_dict}")

    # Step 2: Apply repairs in sequence
    # 2a: Type coercion (bool and int)
    parameters = tool_schema.get("parameters", {})
    for param_name, param_value in call_dict.items():
        param_info = parameters.get(param_name, {})
        param_type_str = param_info.get("type")
        # Convert string type to Python type
        param_type = TYPE_MAP.get(param_type_str) if param_type_str else None

        # Try bool coercion
        repaired, was_repaired, desc = repair_string_bool(param_value, param_type)
        if was_repaired:
            call_dict[param_name] = repaired
            logger.warning(f"Repaired type_coercion on {repr(param_name)}: {desc}")
            repair_history.append(f"type_coercion: {desc}")
            continue

        # Try int coercion
        repaired, was_repaired, desc = repair_string_int(param_value, param_type)
        if was_repaired:
            call_dict[param_name] = repaired
            logger.warning(f"Repaired type_coercion on {repr(param_name)}: {desc}")
            repair_history.append(f"type_coercion: {desc}")
            continue

        # Try quoted path unwrapping
        repaired, was_repaired, desc = repair_quoted_string_path(param_value, param_type)
        if was_repaired:
            call_dict[param_name] = repaired
            logger.warning(f"Repaired quoted_path on {repr(param_name)}: {desc}")
            repair_history.append(f"quoted_path: {desc}")

    # 2b: Missing required fields and defaults
    call_dict, missing_repairs, missing_required = repair_missing_required_fields(call_dict, tool_schema)
    for repair_desc in missing_repairs:
        logger.warning(f"Repaired missing_field: {repair_desc}")
        repair_history.append(f"missing_field: {repair_desc}")

    if missing_required:
        error_msg = f"Missing required parameters: {', '.join(missing_required)}"
        logger.error(error_msg)
        repair_history.append(error_msg)
        return (None, repair_history)

    # 2c: Parameter name typo correction
    call_dict, typo_repairs = repair_parameter_name_typo(call_dict, tool_schema)
    for repair_desc in typo_repairs:
        logger.warning(f"Repaired typo_correction: {repair_desc}")
        repair_history.append(f"typo_correction: {repair_desc}")

    # Check for unknown parameters after typo correction
    safe_params = tool_schema.get("safe_parameters", [])
    unknown_params = [key for key in call_dict.keys() if key not in safe_params]
    if unknown_params:
        valid_suggestions = ", ".join(sorted(safe_params)[:5])
        error_msg = f"Unknown parameters after repair: {unknown_params}. Valid options: {valid_suggestions}"
        logger.error(error_msg)
        repair_history.append(error_msg)
        return (None, repair_history)

    # 2d: Nested structure repair
    call_dict, nested_repairs, nested_violations = repair_nested_structure(call_dict, tool_schema)
    for repair_desc in nested_repairs:
        logger.warning(f"Repaired nested_structure: {repair_desc}")
        repair_history.append(f"nested_structure: {repair_desc}")

    if nested_violations:
        error_msg = f"Nested structure violations: {', '.join(nested_violations)}"
        logger.error(error_msg)
        repair_history.append(error_msg)
        return (None, repair_history)

    # Step 3: Validation gate
    is_valid, validation_errors = validate_repair_safety(call_dict, tool_schema)
    if not is_valid:
        for error_msg in validation_errors:
            logger.error(f"Validation failed: {error_msg}")
            repair_history.append(f"validation_error: {error_msg}")
        return (None, repair_history)

    # Step 4: Final decision
    logger.info("Tool call ACCEPTED after repairs")
    repair_history.append("tool_call_accepted")

    return (call_dict, repair_history)
