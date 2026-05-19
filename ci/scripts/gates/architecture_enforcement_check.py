"""Stage 3 Architecture Enforcement Gate — structural rules for SRP, dependencies, duplication, complexity.

Specification: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/11_stage_3_architecture_enforcement_gate.md

Orchestrates five analysis tools (import-linter, eslint, semgrep, jscpd, radon) and aggregates violations
with proper severity classification, deduplication, and scoring.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Severity weight mapping for risk_score computation
SEVERITY_WEIGHTS = {
    "CRITICAL": 100,
    "ERROR": 80,
    "WARN": 50,
    "INFO": 10,
}

# Severity order for sorting
SEVERITY_ORDER = {
    "CRITICAL": 0,
    "ERROR": 1,
    "WARN": 2,
    "INFO": 3,
}


def _iso8601_timestamp() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix."""
    ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    # Convert +00:00 to Z
    return ts.replace("+00:00", "Z")


def _invoke_tool(
    tool_name: str,
    args: list[str],
    timeout: int,
    cwd: str,
) -> subprocess.CompletedProcess:
    """Invoke a subprocess tool with standard error handling.

    Raises subprocess.TimeoutExpired on timeout, FileNotFoundError if executable not found,
    CalledProcessError if exit code indicates failure (other than tool-specific acceptable codes).

    Args:
        tool_name: name of tool (for logging)
        args: command and arguments
        timeout: timeout in seconds
        cwd: working directory for subprocess

    Returns: CompletedProcess with captured output

    Raises:
        subprocess.TimeoutExpired: if tool exceeds timeout
        FileNotFoundError: if executable not found on PATH
        CalledProcessError: if exit code outside acceptable range (propagates to caller)
    """
    try:
        logger.debug(f"Running {tool_name}: {args}")
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        logger.error(f"{tool_name} timeout (exceeded {timeout}s)")
        raise
    except FileNotFoundError:
        logger.warning(f"{tool_name} not found on PATH")
        raise


def _run_import_linter(codebase_root: str) -> list[dict[str, Any]]:
    """Run import-linter and return violations with AR-* rules.

    Returns: list of violation dicts with tool, severity, file, line, column, rule_id, message.
    On timeout/unavailable, raises subprocess.TimeoutExpired or FileNotFoundError.
    On JSON parse error, raises ValueError.
    """
    result = _invoke_tool("import-linter", ["lint-imports", "--config", ".import-linter"], 60, codebase_root)

    violations: list[dict[str, Any]] = []

    # import-linter exit code 0 = clean, 1 = violations found
    if result.returncode not in (0, 1):
        logger.error(f"import-linter exited with code {result.returncode}: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, "lint-imports")

    if result.returncode == 1 and result.stdout:
        # Parse import-linter output (text format)
        # import-linter outputs lines like:
        # "ERROR: <file>:<line>:<column>: <message>"
        # or violation contracts
        for line in result.stdout.split("\n"):
            if not line.strip():
                continue

            # Try to parse as violation (heuristic)
            # import-linter format varies; conservative parsing
            if "forbidden import" in line.lower() or "circular" in line.lower():
                # Extract file and line if present
                parts = line.split(":")
                if len(parts) >= 2:
                    try:
                        file_path = parts[0].strip()
                        line_no = int(parts[1]) if parts[1].strip().isdigit() else 0

                        # Determine rule_id and severity based on message
                        rule_id = "AR-02"
                        severity = "ERROR"

                        if "circular" in line.lower():
                            rule_id = "AR-07"
                            severity = "CRITICAL"
                        elif "forbidden" in line.lower() and "import" in line.lower():
                            rule_id = "AR-02"
                            severity = "ERROR"

                        violations.append({
                            "tool": "import-linter",
                            "severity": severity,
                            "file": file_path,
                            "line": line_no,
                            "column": 0,
                            "rule_id": rule_id,
                            "message": line.strip(),
                        })
                    except (ValueError, IndexError):
                        # Parsing failed for this line; skip
                        pass

    logger.debug(f"import-linter found {len(violations)} violations")
    return violations


def _run_eslint(codebase_root: str) -> list[dict[str, Any]]:
    """Run eslint-plugin-boundaries and return violations with AR-* rules.

    Returns: list of violation dicts.
    On timeout/unavailable, raises subprocess.TimeoutExpired or FileNotFoundError.
    On JSON parse error, raises ValueError.
    """
    result = _invoke_tool(
        "eslint",
        ["npx", "eslint", "--format", "json", "asset_generation/web/frontend/src"],
        60,
        codebase_root,
    )

    violations: list[dict[str, Any]] = []

    # eslint returns 0 if no errors, >0 if errors/warnings found
    if result.stdout.strip():
        try:
            eslint_output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"eslint output parsing failed: {e}. Output: {result.stdout[:500]}")
            raise ValueError(f"eslint produced invalid JSON: {str(e)}") from e

        # eslint JSON format: array of {filePath, messages: [{line, column, message, ruleId}]}
        if isinstance(eslint_output, list):
            for file_entry in eslint_output:
                file_path = file_entry.get("filePath", "unknown")
                messages = file_entry.get("messages", [])
                for msg in messages:
                    line = msg.get("line", 0)
                    column = msg.get("column", 0)
                    rule_id = msg.get("ruleId", "UNKNOWN")
                    message = msg.get("message", "")
                    severity = msg.get("severity", 1)  # 1=warning, 2=error

                    # Map eslint severity and rule_id to gate severity
                    gate_severity = "WARN" if severity == 1 else "ERROR"

                    # Map eslint rule IDs to architecture rules
                    if "boundaries" in rule_id.lower():
                        gate_rule_id = "AR-03" if "import" in message.lower() else "AR-06"
                    else:
                        gate_rule_id = rule_id

                    violations.append({
                        "tool": "eslint",
                        "severity": gate_severity,
                        "file": file_path,
                        "line": line,
                        "column": column,
                        "rule_id": gate_rule_id,
                        "message": message,
                    })

    logger.debug(f"eslint found {len(violations)} violations")
    return violations


def _run_semgrep(codebase_root: str) -> list[dict[str, Any]]:
    """Run semgrep with custom rule set and return violations with AR-*, AS-*, CX-* rules.

    Returns: list of violation dicts.
    On timeout/unavailable, raises subprocess.TimeoutExpired or FileNotFoundError.
    On JSON parse error, raises ValueError.
    """
    result = _invoke_tool(
        "semgrep",
        [
            "semgrep",
            "--config",
            "asset_generation/python/.semgrep.yml",
            "--json",
            "asset_generation/python/src",
            "asset_generation/web/backend",
        ],
        120,
        codebase_root,
    )

    violations: list[dict[str, Any]] = []

    # semgrep exit code 0 = clean, nonzero = violations or error
    if result.stdout.strip():
        try:
            semgrep_output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"semgrep output parsing failed: {e}. Output: {result.stdout[:500]}")
            raise ValueError(f"semgrep produced invalid JSON: {str(e)}") from e

        # semgrep JSON format: {results: [{path, start: {line, col}, message, rule_id}]}
        results = semgrep_output.get("results", [])
        for finding in results:
            file_path = finding.get("path", "unknown")
            start = finding.get("start", {})
            line = start.get("line", 0)
            col = start.get("col", 0)
            message = finding.get("message", "")
            rule_id = finding.get("check_id", finding.get("rule_id", "UNKNOWN"))

            # Map semgrep rule IDs to gate rule IDs
            # Semgrep returns rule ids; map to AR-*, AS-*, etc based on message/rule_id
            gate_rule_id = rule_id
            gate_severity = "WARN"

            if "hardcoded" in rule_id.lower() or "secret" in message.lower():
                gate_rule_id = "AR-01"
                gate_severity = "ERROR"
            elif "circular" in message.lower():
                gate_rule_id = "AR-07"
                gate_severity = "CRITICAL"
            elif "forbidden" in message.lower() or "import" in message.lower():
                gate_rule_id = "AR-02"
                gate_severity = "ERROR"
            elif "async" in message.lower() or "blocking" in message.lower():
                gate_rule_id = "AS-01"
                gate_severity = "CRITICAL"
            elif rule_id == "sql-injection-risk":
                gate_rule_id = "AR-05"
                gate_severity = "CRITICAL"

            violations.append({
                "tool": "semgrep",
                "severity": gate_severity,
                "file": file_path,
                "line": line,
                "column": col,
                "rule_id": gate_rule_id,
                "message": message,
            })

    logger.debug(f"semgrep found {len(violations)} violations")
    return violations


def _run_jscpd(codebase_root: str) -> list[dict[str, Any]]:
    """Run jscpd (duplication checker) and return violations with DUP-* rules.

    Returns: list of violation dicts.
    On timeout/unavailable, raises subprocess.TimeoutExpired or FileNotFoundError.
    On JSON parse error, raises ValueError.
    """
    result = _invoke_tool(
        "jscpd",
        ["npx", "jscpd", "--config", "jscpd.json", "--format", "json"],
        120,
        codebase_root,
    )

    violations: list[dict[str, Any]] = []

    if result.stdout.strip():
        try:
            jscpd_output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"jscpd output parsing failed: {e}. Output: {result.stdout[:500]}")
            raise ValueError(f"jscpd produced invalid JSON: {str(e)}") from e

        # jscpd JSON format: {duplicates: [{firstFile: {name, start}, secondFile: {name, start}, lines}]}
        duplicates = jscpd_output.get("duplicates", [])
        for dup in duplicates:
            first_file = dup.get("firstFile", {})
            first_name = first_file.get("name", "unknown")
            first_line = first_file.get("start", {}).get("line", 0)

            second_file = dup.get("secondFile", {})
            second_name = second_file.get("name", "unknown")
            second_line = second_file.get("start", {}).get("line", 0)

            lines = dup.get("lines", 0)

            # Create violation for duplication
            message = f"Duplication: '{first_name}' lines {first_line}-{first_line + lines} duplicates '{second_name}' lines {second_line}-{second_line + lines} ({lines} lines)"

            violations.append({
                "tool": "jscpd",
                "severity": "WARN",
                "file": first_name,
                "line": first_line,
                "column": 0,
                "rule_id": "DUP-01",
                "message": message,
            })

    logger.debug(f"jscpd found {len(violations)} violations")
    return violations


def _run_radon(codebase_root: str) -> list[dict[str, Any]]:
    """Run radon (complexity checker) and return violations with CX-* rules.

    Returns: list of violation dicts.
    On timeout/unavailable, raises subprocess.TimeoutExpired or FileNotFoundError.
    On JSON parse error, raises ValueError.
    """
    result = _invoke_tool(
        "radon",
        ["radon", "cc", "-j", "asset_generation/python/src"],
        60,
        codebase_root,
    )

    violations: list[dict[str, Any]] = []

    if result.stdout.strip():
        try:
            radon_output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"radon output parsing failed: {e}. Output: {result.stdout[:500]}")
            raise ValueError(f"radon produced invalid JSON: {str(e)}") from e

        # radon cc JSON format: {filename: {function_name: {lineno, col_offset, classname, classmethod, complexity}}}
        for filename, items in radon_output.items():
            if isinstance(items, dict):
                for func_name, metrics in items.items():
                    if isinstance(metrics, dict):
                        complexity = metrics.get("complexity", 0)
                        lineno = metrics.get("lineno", 0)
                        col_offset = metrics.get("col_offset", 0)

                        # Threshold: complexity > 10 is WARN
                        if complexity > 10:
                            violations.append({
                                "tool": "radon",
                                "severity": "WARN",
                                "file": filename,
                                "line": lineno,
                                "column": col_offset,
                                "rule_id": "CX-03",
                                "message": f"Cognitive complexity in '{func_name}' is {complexity} (threshold: 10)",
                            })

    logger.debug(f"radon found {len(violations)} violations")
    return violations


def _collect_violations(codebase_root: str) -> list[dict[str, Any]]:
    """Call all five tools and collect violations.

    Args:
        codebase_root: path to codebase root for subprocess working directory

    Returns: aggregated list of violations from all tools.
    On tool timeout/unavailable, record as violation with TOOL_TIMEOUT or TOOL_UNAVAILABLE rule_id.
    On tool error (non-zero exit), record as TOOL_ERROR violation.
    On tool JSON parse error, record as TOOL_ERROR violation.
    """
    violations: list[dict[str, Any]] = []

    # Tool definitions: (tool_name, tool_function)
    tools = [
        ("import-linter", _run_import_linter),
        ("eslint", _run_eslint),
        ("semgrep", _run_semgrep),
        ("jscpd", _run_jscpd),
        ("radon", _run_radon),
    ]

    for tool_name, tool_func in tools:
        try:
            tool_violations = tool_func(codebase_root)
            violations.extend(tool_violations)
        except subprocess.TimeoutExpired as e:
            # Record timeout as violation
            violations.append({
                "tool": tool_name,
                "severity": "ERROR",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_TIMEOUT",
                "message": f"{tool_name} timeout (exceeded {e.timeout}s)",
            })
            logger.warning(f"Tool {tool_name} timeout")
        except FileNotFoundError:
            # Tool not installed: record as WARN
            violations.append({
                "tool": tool_name,
                "severity": "WARN",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_UNAVAILABLE",
                "message": f"{tool_name} not installed",
            })
            logger.warning(f"Tool {tool_name} not available")
        except (subprocess.CalledProcessError, ValueError) as e:
            # CalledProcessError: tool exited with non-zero code (other than normal failure codes)
            # ValueError: tool produced invalid JSON or other parsing error
            # Record as TOOL_ERROR for both cases; both indicate tool failure, not governance violation
            violations.append({
                "tool": tool_name,
                "severity": "ERROR",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_ERROR",
                "message": f"{tool_name} error: {str(e)}",
            })
            logger.error(f"Tool {tool_name} error: {e}", exc_info=True)
        except Exception as e:
            # Defensive catch for unexpected exceptions from tool function.
            # Tool functions are plugin-like and may throw domain-specific exceptions;
            # catching and recording as TOOL_ERROR prevents crashes while preserving visibility.
            # This is justified exception handling: catching to transform into structured violation,
            # not to swallow silently. See code_governance.md: explicit recovery with clear semantics.
            violations.append({
                "tool": tool_name,
                "severity": "ERROR",
                "file": tool_name,
                "line": 0,
                "column": 0,
                "rule_id": "TOOL_ERROR",
                "message": f"{tool_name} error: {str(e)}",
            })
            logger.error(f"Tool {tool_name} unexpected error: {e}", exc_info=True)

    return violations


def _deduplicate_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate violations by fingerprint (file, line, rule_id).

    If multiple violations have the same fingerprint, keep the most severe one.

    Args:
        violations: list of violation dicts

    Returns: deduplicated list of violations
    """
    fingerprint_map: dict[tuple[str, int, str], dict[str, Any]] = {}

    for v in violations:
        fingerprint = (v["file"], v["line"], v["rule_id"])

        if fingerprint not in fingerprint_map:
            fingerprint_map[fingerprint] = v
        else:
            # Keep the more severe violation
            existing = fingerprint_map[fingerprint]
            existing_weight = SEVERITY_WEIGHTS.get(existing["severity"], 0)
            new_weight = SEVERITY_WEIGHTS.get(v["severity"], 0)

            if new_weight > existing_weight:
                fingerprint_map[fingerprint] = v

    return list(fingerprint_map.values())


def _sort_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort violations by severity (descending) then by line number (ascending).

    Returns: sorted list of violations
    """
    return sorted(
        violations,
        key=lambda v: (SEVERITY_ORDER.get(v["severity"], 999), v["line"]),
    )


def _compute_risk_score(violations: list[dict[str, Any]]) -> int:
    """Compute risk_score as weighted average of violation severities.

    Formula: sum(weights) / len(violations), clamped [0, 100]
    If no violations, risk_score = 0

    Args:
        violations: list of violation dicts

    Returns: risk_score integer in [0, 100]
    """
    if not violations:
        return 0

    weights = [SEVERITY_WEIGHTS.get(v["severity"], 0) for v in violations]
    avg = sum(weights) / len(weights) if weights else 0
    # Round to nearest integer
    return max(0, min(100, int(round(avg))))


def _compute_architecture_score(violations: list[dict[str, Any]]) -> int:
    """Compute architecture_score as 100 - (AR_violations * 10), clamped [0, 100].

    Only counts AR-* prefixed rule_ids.

    Args:
        violations: list of violation dicts

    Returns: architecture_score integer in [0, 100]
    """
    ar_count = sum(1 for v in violations if v["rule_id"].startswith("AR-"))
    score = 100 - (ar_count * 10)
    return max(0, min(100, score))


def _determine_status(
    violations: list[dict[str, Any]],
    risk_score: int,
    architecture_score: int,
    mode: str,
) -> str:
    """Determine gate status based on violations and scores.

    Status logic:
    - If mode == 'shadow': always return PASS (override)
    - If any CRITICAL severity: ESCALATE
    - If architecture_score <= 30: ESCALATE
    - If any ERROR severity: FAIL
    - If architecture_score <= 50: FAIL
    - If any WARN severity: WARN
    - If architecture_score <= 80: WARN
    - Otherwise: PASS

    Args:
        violations: list of violation dicts
        risk_score: computed risk score
        architecture_score: computed architecture score
        mode: 'shadow' or 'blocking'

    Returns: status string (PASS | WARN | FAIL | ESCALATE)
    """
    # Shadow mode always returns PASS (after collecting and reporting violations)
    if mode == "shadow":
        return "PASS"

    # Check for CRITICAL violations or low architecture_score
    has_critical = any(v["severity"] == "CRITICAL" for v in violations)
    if has_critical or architecture_score <= 30:
        return "ESCALATE"

    # Check for ERROR violations or bad architecture score
    has_error = any(v["severity"] == "ERROR" for v in violations)
    if has_error or architecture_score <= 50:
        return "FAIL"

    # Check for WARN violations or moderate architecture score
    has_warn = any(v["severity"] == "WARN" for v in violations)
    if has_warn or architecture_score <= 80:
        return "WARN"

    return "PASS"


def _build_severity_counts(violations: list[dict[str, Any]]) -> dict[str, int]:
    """Count violations by severity level.

    Args:
        violations: list of violation dicts

    Returns: dict mapping severity level to count
    """
    counts = {"CRITICAL": 0, "ERROR": 0, "WARN": 0, "INFO": 0}
    for v in violations:
        severity = v["severity"]
        if severity in counts:
            counts[severity] += 1
    return counts


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute architecture enforcement gate.

    Inputs (optional):
        - mode: 'shadow' (default) or 'blocking'
        - ticket_id: ticket identifier (default 'M902-11')
        - codebase_root: path to codebase root (default current directory)

    Returns: dict matching gate result schema with fields:
        - status: PASS | WARN | FAIL | ESCALATE
        - gate: "architecture_enforcement_check"
        - ticket_id: from inputs or default
        - timestamp: ISO 8601 UTC
        - message: human-readable summary
        - violations: list of violation dicts (sorted by severity, then line)
        - risk_score: weighted average of violation severities [0, 100]
        - architecture_score: 100 - (AR_violations * 10), clamped [0, 100]
        - severity_counts: dict of counts by severity level
        - artifacts: list of artifact paths (empty for this gate)
        - duration_ms: elapsed time in milliseconds
    """
    start_time = time.time()
    mode = inputs.get("mode", "shadow")
    ticket_id = inputs.get("ticket_id", "M902-11")
    codebase_root = inputs.get("codebase_root", os.getcwd())

    try:
        # Step 1: Collect violations from all tools
        violations = _collect_violations(codebase_root)

        # Step 2: Deduplicate violations by fingerprint
        violations = _deduplicate_violations(violations)

        # Step 3: Sort violations by severity and line
        violations = _sort_violations(violations)

        # Step 4: Compute scores
        risk_score = _compute_risk_score(violations)
        architecture_score = _compute_architecture_score(violations)

        # Step 5: Determine status
        status = _determine_status(violations, risk_score, architecture_score, mode)

        # Step 6: Build severity counts
        severity_counts = _build_severity_counts(violations)

        # Step 7: Build result message
        if status == "PASS":
            if violations:
                message = f"Code passed architecture enforcement (shadow mode: {len(violations)} violations recorded for review)"
            else:
                message = "Code passed architecture enforcement"
        elif status == "WARN":
            message = f"Code has architecture warnings ({severity_counts['WARN']} WARN, {severity_counts['INFO']} INFO)"
        elif status == "FAIL":
            message = f"Code failed architecture enforcement ({severity_counts['ERROR']} ERROR, {severity_counts['WARN']} WARN)"
        else:  # ESCALATE
            message = f"Code has critical architecture violations ({severity_counts['CRITICAL']} CRITICAL, {severity_counts['ERROR']} ERROR)"

        elapsed_ms = max(1, int((time.time() - start_time) * 1000))

        return {
            "status": status,
            "gate": "architecture_enforcement_check",
            "ticket_id": ticket_id,
            "timestamp": _iso8601_timestamp(),
            "message": message,
            "violations": violations,
            "risk_score": risk_score,
            "architecture_score": architecture_score,
            "severity_counts": severity_counts,
            "artifacts": [],
            "duration_ms": elapsed_ms,
        }

    except Exception as e:
        logger.exception(f"Unexpected error in architecture_enforcement_check gate: {e}")
        elapsed_ms = max(1, int((time.time() - start_time) * 1000))
        return {
            "status": "FAIL",
            "gate": "architecture_enforcement_check",
            "ticket_id": ticket_id,
            "timestamp": _iso8601_timestamp(),
            "message": f"Unexpected error: {str(e)}",
            "violations": [
                {
                    "tool": "architecture_enforcement_check",
                    "severity": "ERROR",
                    "file": "architecture_enforcement_check",
                    "line": 0,
                    "column": 0,
                    "rule_id": "GATE_ERROR",
                    "message": str(e),
                }
            ],
            "risk_score": 100,
            "architecture_score": 0,
            "severity_counts": {"CRITICAL": 0, "ERROR": 1, "WARN": 0, "INFO": 0},
            "artifacts": [],
            "duration_ms": elapsed_ms,
        }
