#!/usr/bin/env python3
"""
Baseline management module for M902-07 governance audit pipeline.

Provides functions to:
- Load and validate baseline files against schema
- Check baseline entry expiration
- Match violations against baseline entries
- Handle baseline path normalization
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def load_baseline(baseline_path: Path) -> dict[str, Any]:
    """Load baseline from file.

    If file does not exist, returns empty baseline template.

    Args:
        baseline_path: Path to .governance-baseline.json file

    Returns:
        Parsed baseline dict or empty baseline if file missing

    Raises:
        json.JSONDecodeError: If file exists but is invalid JSON
        IOError: If file cannot be read
    """
    if not baseline_path.exists():
        logger.warning(f"Baseline file not found: {baseline_path}, using empty baseline")
        return {
            "_meta": {
                "version": "1.0",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "tool": "governance-audit-pipeline",
                "description": "Empty baseline (no entries)",
            },
            "baseline_entries": [],
        }

    try:
        content = baseline_path.read_text()
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in baseline file {baseline_path}: {e}")
        raise
    except IOError as e:
        logger.error(f"Cannot read baseline file {baseline_path}: {e}")
        raise


def validate_baseline(baseline: dict[str, Any]) -> bool:
    """Validate baseline structure.

    Checks:
    - _meta is present and has required fields
    - baseline_entries is array
    - Each entry has required fields (rule_id, file, line, expires_at, owner, rationale)
    - Type correctness (rule_id is string or null, line is int or null, etc.)
    - rule_id is not null (required per spec)
    - Path normalization (forward slashes)

    Args:
        baseline: Baseline dict to validate

    Returns:
        True if valid, False otherwise

    Logs:
        Warning/error messages for validation failures
    """
    # Check _meta
    if "_meta" not in baseline:
        logger.error("Baseline missing '_meta' field")
        return False

    meta = baseline.get("_meta")
    if not isinstance(meta, dict):
        logger.error("Baseline '_meta' is not a dict")
        return False

    required_meta_fields = ["version", "generated_at", "tool", "description"]
    for field in required_meta_fields:
        if field not in meta:
            logger.warning(f"Baseline '_meta' missing field: {field}")

    # Check baseline_entries
    if "baseline_entries" not in baseline:
        logger.error("Baseline missing 'baseline_entries' field")
        return False

    entries = baseline.get("baseline_entries")
    if not isinstance(entries, list):
        logger.error("Baseline 'baseline_entries' is not an array")
        return False

    # Validate each entry
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            logger.error(f"Baseline entry {idx} is not a dict")
            return False

        # Check required fields
        required_fields = ["rule_id", "file", "line", "expires_at", "owner", "rationale"]
        for field in required_fields:
            if field not in entry:
                logger.error(f"Baseline entry {idx} missing required field: {field}")
                return False

        # Validate rule_id is not null (must be string)
        rule_id = entry.get("rule_id")
        if rule_id is None:
            logger.error(f"Baseline entry {idx} has null rule_id (required)")
            return False
        if not isinstance(rule_id, str):
            logger.error(
                f"Baseline entry {idx} rule_id is {type(rule_id).__name__}, expected string"
            )
            return False

        # Validate line is int or null
        line = entry.get("line")
        if line is not None and not isinstance(line, int):
            logger.warning(
                f"Baseline entry {idx} line is {type(line).__name__}, expected int or null"
            )

        # Validate expires_at is string or null (ISO 8601 if string)
        expires_at = entry.get("expires_at")
        if expires_at is not None and not isinstance(expires_at, str):
            logger.error(
                f"Baseline entry {idx} expires_at is {type(expires_at).__name__}, expected string or null"
            )
            return False

        # Validate owner and rationale are strings
        owner = entry.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            logger.error(f"Baseline entry {idx} owner must be non-empty string")
            return False

        rationale = entry.get("rationale")
        if not isinstance(rationale, str):
            logger.error(f"Baseline entry {idx} rationale is not a string")
            return False

        # Normalize path (backslash to forward slash)
        file_path = entry.get("file", "")
        normalized_path = file_path.replace("\\", "/")
        if normalized_path != file_path:
            logger.warning(
                f"Baseline entry {idx} file path uses backslashes, normalizing to forward slashes"
            )
            entry["file"] = normalized_path

    return True


def is_entry_expired(entry: dict[str, Any], now: Optional[datetime] = None) -> bool:
    """Check if baseline entry is expired.

    Args:
        entry: Baseline entry dict
        now: Current datetime (UTC, or None to use now)

    Returns:
        True if expires_at < now, False otherwise
    """
    if now is None:
        now = datetime.now(timezone.utc)

    expires_at_str = entry.get("expires_at")
    if expires_at_str is None:
        return False  # No expiration

    try:
        # Parse ISO 8601 date/datetime
        # Support both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SSZ formats
        if "T" in expires_at_str:
            # Full datetime
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        else:
            # Date only, treat as midnight UTC
            expires_at = datetime.fromisoformat(expires_at_str).replace(tzinfo=timezone.utc)

        # Strict inequality: expires_at < now means expired
        return expires_at < now
    except (ValueError, TypeError) as e:
        logger.error(f"Cannot parse expires_at '{expires_at_str}': {e}")
        return False


def match_violation(violation: dict[str, Any], entry: dict[str, Any]) -> bool:
    """Check if violation matches baseline entry.

    Matching criteria:
    - rule_id must match exactly
    - file must match (exact path match for now, can extend to regex in M903)
    - line must match (exact int match)

    Args:
        violation: Violation dict from audit
        entry: Baseline entry dict

    Returns:
        True if violation matches entry, False otherwise
    """
    # Rule ID must match exactly
    violation_rule = violation.get("rule")
    entry_rule = entry.get("rule_id")
    if violation_rule != entry_rule:
        return False

    # File must match (normalize paths)
    violation_file = normalize_path(violation.get("file", ""))
    entry_file = normalize_path(entry.get("file", ""))
    if violation_file != entry_file:
        return False

    # Line must match exactly (handle null/None)
    violation_line = violation.get("line")
    entry_line = entry.get("line")

    # Normalize types: if both present, must be same int
    if violation_line is not None and entry_line is not None:
        try:
            if int(violation_line) != int(entry_line):
                return False
        except (ValueError, TypeError):
            return False
    elif (violation_line is None) != (entry_line is None):
        # One is null and one is not
        return False

    return True


def normalize_path(path: str) -> str:
    """Normalize file path for matching.

    - Convert backslashes to forward slashes
    - Remove leading/trailing whitespace
    - Handle relative vs absolute paths

    Args:
        path: File path to normalize

    Returns:
        Normalized path (forward slashes, no leading/trailing whitespace)
    """
    path = path.strip()
    path = path.replace("\\", "/")
    # Remove leading slashes (make relative)
    while path.startswith("/"):
        path = path[1:]
    return path


def get_baseline_entries(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    """Get all baseline entries.

    Args:
        baseline: Baseline dict

    Returns:
        List of baseline entry dicts
    """
    return baseline.get("baseline_entries", [])
