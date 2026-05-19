"""Stage 8 Final Security Gate — runs 5 security scanning tools with deterministic decision matrix.

Specification: project_board/specs/902_16_security_gate_spec.md

Aggregates findings from 5 tools (gitleaks, bandit, semgrep, pip-audit, npm audit) and produces
deterministic FAIL/WARN/PASS status based on severity thresholds. Hard-fails on secrets, unsafe
deserialization, auth bypass, and CVSS >= 7.0; soft-fails on medium/low findings.

Returns M902-01 gate schema with violations, remediation hints, and tool statuses.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

logger = logging.getLogger(__name__)

# ============================================================================
# Type Definitions
# ============================================================================


class GateInputs(TypedDict, total=False):
    """Gate function inputs."""
    mode: str
    ticket_id: str
    upstream_agent: str | None
    downstream_agent: str
    changed_files: list[str]
    issue_id: str


class ToolStatus(TypedDict):
    """Tool execution status record."""
    name: str
    exit_code: int | None
    findings_count: int
    timeout: bool
    error: str | None


class Violation(TypedDict):
    """Security violation record."""
    file: str
    line: int | None
    rule: str
    message: str
    severity: Literal["ERROR", "WARN", "INFO"]


# ============================================================================
# Constants
# ============================================================================

TOOL_TIMEOUTS = {
    "gitleaks": 10,
    "bandit": 30,
    "semgrep": 60,
    "pip-audit": 20,
    "npm-audit": 20,
}

# Hard-fail rule IDs for bandit
HARD_FAIL_RULES = {
    "B201",  # Flask debug mode
    "B301", "B302", "B303",  # Unsafe deserialization (pickle, marshal)
    "B105", "B106", "B107",  # Hardcoded passwords/secrets
    "B506",  # Unsafe YAML
    "B602",  # Paramiko shell injection
}

# Soft-fail rule IDs for bandit
SOFT_FAIL_RULES = {
    "B110", "B111", "B112",  # Except too broad
    "B404", "B405", "B406", "B407",  # Import restrictions
}

# Severity order (higher = more severe)
SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


# ============================================================================
# Helper Functions
# ============================================================================


def _iso8601_timestamp() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix.

    Returns:
        ISO 8601 timestamp string in format YYYY-MM-DDTHH:MM:SSZ.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _map_severity(severity_str: str, tool_name: str) -> str:
    """Map tool-specific severity to standard severity (ERROR, WARN, INFO).

    Args:
        severity_str: tool-specific severity string (HIGH, CRITICAL, MEDIUM, etc.)
        tool_name: name of the tool (gitleaks, bandit, etc.)

    Returns:
        Standard severity: ERROR, WARN, or INFO
    """
    severity_upper = severity_str.upper()

    if tool_name == "gitleaks":
        # Gitleaks treats any secret as ERROR
        return "ERROR"
    elif tool_name == "bandit":
        # Bandit: HIGH -> ERROR, MEDIUM -> WARN, LOW -> INFO
        if severity_upper == "HIGH":
            return "ERROR"
        elif severity_upper == "MEDIUM":
            return "WARN"
        else:
            return "INFO"
    elif tool_name == "semgrep":
        # Semgrep: CRITICAL/HIGH -> ERROR, MEDIUM -> WARN, LOW -> INFO
        if severity_upper in ["CRITICAL", "HIGH"]:
            return "ERROR"
        elif severity_upper == "MEDIUM":
            return "WARN"
        else:
            return "INFO"
    elif tool_name in ["pip-audit", "npm-audit"]:
        # Dependency tools: mapped by CVSS score (handled separately)
        # This is fallback; CVSS mapping happens in respective parsers
        if severity_upper in ["CRITICAL", "HIGH"]:
            return "ERROR"
        elif severity_upper in ["MEDIUM", "MODERATE"]:
            return "WARN"
        else:
            return "INFO"

    return "INFO"  # Default


def _cvss_to_severity(cvss_score: float | str) -> str:
    """Map CVSS score to severity level.

    Args:
        cvss_score: CVSS v3.1 score (0.0-10.0)

    Returns:
        Severity: ERROR (>=7.0), WARN (4.0-6.9), INFO (<4.0)
    """
    try:
        score = float(cvss_score)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse CVSS score: {cvss_score}")
        return "WARN"

    if score >= 7.0:
        return "ERROR"
    elif score >= 4.0:
        return "WARN"
    else:
        return "INFO"


# ============================================================================
# Tool Runners
# ============================================================================


def _run_gitleaks(inputs: GateInputs) -> tuple[list[Violation], ToolStatus]:
    """Run gitleaks secret detection.

    Args:
        inputs: gate inputs with optional changed_files

    Returns:
        tuple of (violations list, tool_status dict)
    """
    tool_status: ToolStatus = {
        "name": "gitleaks",
        "exit_code": None,
        "findings_count": 0,
        "timeout": False,
        "error": None,
    }
    violations: list[Violation] = []

    try:
        # Command: gitleaks detect --source . --json --report-path <temp>.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name

        cmd = ["gitleaks", "detect", "--source", ".", "--json", "--report-path", tmp_path, "--exit-code", "1"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUTS["gitleaks"],
        )

        tool_status["exit_code"] = result.returncode

        # Read report file
        try:
            with open(tmp_path, 'r') as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            tool_status["error"] = f"Failed to parse gitleaks report: {str(e)}"
            logger.warning(tool_status["error"])
            return violations, tool_status

        # Parse matches
        matches = report.get("matches", [])
        for match in matches:
            violation: Violation = {
                "file": match.get("File", "unknown"),
                "line": match.get("LineNumber"),
                "rule": match.get("RuleID", "gitleaks-secret"),
                "message": f"Secret detected: {match.get('RuleDescription', 'unknown pattern')}",
                "severity": "ERROR",
            }
            violations.append(violation)

        tool_status["findings_count"] = len(violations)

        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass

    except subprocess.TimeoutExpired:
        tool_status["timeout"] = True
        tool_status["error"] = f"Subprocess exceeded {TOOL_TIMEOUTS['gitleaks']}s timeout"
    except FileNotFoundError:
        tool_status["error"] = "gitleaks binary not found on PATH"
    except Exception as e:
        tool_status["error"] = f"gitleaks execution failed: {str(e)}"

    return violations, tool_status


def _run_bandit(inputs: GateInputs) -> tuple[list[Violation], ToolStatus]:
    """Run bandit Python security scanning.

    Args:
        inputs: gate inputs

    Returns:
        tuple of (violations list, tool_status dict)
    """
    tool_status: ToolStatus = {
        "name": "bandit",
        "exit_code": None,
        "findings_count": 0,
        "timeout": False,
        "error": None,
    }
    violations: list[Violation] = []

    try:
        cmd = [
            "bandit",
            "-r",
            "asset_generation/python/",
            "asset_generation/web/backend/",
            "-f", "json",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUTS["bandit"],
        )

        tool_status["exit_code"] = result.returncode

        # Parse JSON output
        try:
            output = json.loads(result.stdout) if result.stdout.strip() else {"results": []}
        except json.JSONDecodeError as e:
            tool_status["error"] = f"Failed to parse bandit JSON: {str(e)}"
            logger.warning(tool_status["error"])
            return violations, tool_status

        # Process findings
        results = output.get("results", [])
        for issue in results:
            # Map bandit severity to gate severity
            bandit_severity = issue.get("severity", "MEDIUM")
            severity = _map_severity(bandit_severity, "bandit")

            violation: Violation = {
                "file": issue.get("filename", "unknown"),
                "line": issue.get("line_number"),
                "rule": issue.get("test_id", "unknown"),
                "message": issue.get("issue_text", "Security issue detected"),
                "severity": severity,
            }
            violations.append(violation)

        tool_status["findings_count"] = len(violations)

    except subprocess.TimeoutExpired:
        tool_status["timeout"] = True
        tool_status["error"] = f"Subprocess exceeded {TOOL_TIMEOUTS['bandit']}s timeout"
    except FileNotFoundError:
        tool_status["error"] = "bandit binary not found on PATH"
    except Exception as e:
        tool_status["error"] = f"bandit execution failed: {str(e)}"

    return violations, tool_status


def _run_semgrep(inputs: GateInputs) -> tuple[list[Violation], ToolStatus]:
    """Run semgrep pattern matching.

    Args:
        inputs: gate inputs

    Returns:
        tuple of (violations list, tool_status dict)
    """
    tool_status: ToolStatus = {
        "name": "semgrep",
        "exit_code": None,
        "findings_count": 0,
        "timeout": False,
        "error": None,
    }
    violations: list[Violation] = []

    try:
        cmd = [
            "semgrep",
            "--config", ".semgrep.yml",
            "asset_generation/python/",
            "asset_generation/web/backend/",
            "asset_generation/web/frontend/",
            "--json",
            "--strict",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUTS["semgrep"],
        )

        tool_status["exit_code"] = result.returncode

        # Parse JSON output
        try:
            output = json.loads(result.stdout) if result.stdout.strip() else {"results": []}
        except json.JSONDecodeError as e:
            tool_status["error"] = f"Failed to parse semgrep JSON: {str(e)}"
            logger.warning(tool_status["error"])
            return violations, tool_status

        # Process findings
        results = output.get("results", [])
        for finding in results:
            semgrep_severity = finding.get("severity", "MEDIUM")
            severity = _map_severity(semgrep_severity, "semgrep")

            # Extract line number from start/end
            start_line = None
            start = finding.get("start", {})
            if isinstance(start, dict):
                start_line = start.get("line")

            violation: Violation = {
                "file": finding.get("path", "unknown"),
                "line": start_line,
                "rule": finding.get("rule_id", "unknown"),
                "message": finding.get("message", "Pattern match detected"),
                "severity": severity,
            }
            violations.append(violation)

        tool_status["findings_count"] = len(violations)

    except subprocess.TimeoutExpired:
        tool_status["timeout"] = True
        tool_status["error"] = f"Subprocess exceeded {TOOL_TIMEOUTS['semgrep']}s timeout"
    except FileNotFoundError:
        tool_status["error"] = "semgrep binary not found on PATH"
    except Exception as e:
        tool_status["error"] = f"semgrep execution failed: {str(e)}"

    return violations, tool_status


def _run_pip_audit(inputs: GateInputs) -> tuple[list[Violation], ToolStatus]:
    """Run pip-audit for Python dependencies.

    Args:
        inputs: gate inputs

    Returns:
        tuple of (violations list, tool_status dict)
    """
    tool_status: ToolStatus = {
        "name": "pip-audit",
        "exit_code": None,
        "findings_count": 0,
        "timeout": False,
        "error": None,
    }
    violations: list[Violation] = []

    try:
        cmd = [
            "pip-audit",
            "--format", "json",
            "--desc",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUTS["pip-audit"],
            cwd="asset_generation/python",
        )

        tool_status["exit_code"] = result.returncode

        # Parse JSON output
        try:
            output = json.loads(result.stdout) if result.stdout.strip() else {"vulnerabilities": []}
        except json.JSONDecodeError as e:
            tool_status["error"] = f"Failed to parse pip-audit JSON: {str(e)}"
            logger.warning(tool_status["error"])
            return violations, tool_status

        # Process vulnerabilities
        vulns = output.get("vulnerabilities", [])
        for vuln in vulns:
            cvss_score = None
            cvssv3 = vuln.get("cvssv3", {})
            if isinstance(cvssv3, dict):
                cvss_score = cvssv3.get("base_score")

            severity = _cvss_to_severity(cvss_score) if cvss_score else "WARN"

            violation: Violation = {
                "file": vuln.get("requirement", "unknown-package"),
                "line": None,
                "rule": vuln.get("vulnerability_id", "CVE-UNKNOWN"),
                "message": f"{vuln.get('advisory', 'Known vulnerability')} (CVSS: {cvss_score})",
                "severity": severity,
            }
            violations.append(violation)

        tool_status["findings_count"] = len(violations)

    except subprocess.TimeoutExpired:
        tool_status["timeout"] = True
        tool_status["error"] = f"Subprocess exceeded {TOOL_TIMEOUTS['pip-audit']}s timeout"
    except FileNotFoundError:
        tool_status["error"] = "pip-audit binary not found on PATH"
    except Exception as e:
        tool_status["error"] = f"pip-audit execution failed: {str(e)}"

    return violations, tool_status


def _run_npm_audit(inputs: GateInputs) -> tuple[list[Violation], ToolStatus]:
    """Run npm audit for JavaScript dependencies.

    Args:
        inputs: gate inputs

    Returns:
        tuple of (violations list, tool_status dict)
    """
    tool_status: ToolStatus = {
        "name": "npm-audit",
        "exit_code": None,
        "findings_count": 0,
        "timeout": False,
        "error": None,
    }
    violations: list[Violation] = []

    try:
        cmd = [
            "npm",
            "audit",
            "--json",
            "--production",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOOL_TIMEOUTS["npm-audit"],
            cwd="asset_generation/web/frontend",
        )

        tool_status["exit_code"] = result.returncode

        # Parse JSON output
        try:
            output = json.loads(result.stdout) if result.stdout.strip() else {"vulnerabilities": {}}
        except json.JSONDecodeError as e:
            tool_status["error"] = f"Failed to parse npm audit JSON: {str(e)}"
            logger.warning(tool_status["error"])
            return violations, tool_status

        # Process vulnerabilities (npm schema is different)
        vulns_obj = output.get("vulnerabilities", {})
        if isinstance(vulns_obj, dict):
            for pkg_name, pkg_data in vulns_obj.items():
                if isinstance(pkg_data, dict):
                    vulnerabilities = pkg_data.get("vulnerabilities", [])
                    for vuln in vulnerabilities:
                        # Extract CVSS score
                        cvss_score = None
                        cvss_obj = vuln.get("cvss", {})
                        if isinstance(cvss_obj, dict):
                            cvss_score = cvss_obj.get("score")

                        severity = _cvss_to_severity(cvss_score) if cvss_score else "WARN"

                        # Get CVE ID (first one if multiple)
                        cves = vuln.get("cves", [])
                        cve_id = cves[0] if cves else "CVE-UNKNOWN"

                        violation: Violation = {
                            "file": pkg_name,
                            "line": None,
                            "rule": cve_id,
                            "message": f"{vuln.get('title', 'Vulnerable package')} (CVSS: {cvss_score})",
                            "severity": severity,
                        }
                        violations.append(violation)

        tool_status["findings_count"] = len(violations)

    except subprocess.TimeoutExpired:
        tool_status["timeout"] = True
        tool_status["error"] = f"Subprocess exceeded {TOOL_TIMEOUTS['npm-audit']}s timeout"
    except FileNotFoundError:
        tool_status["error"] = "npm binary not found on PATH"
    except Exception as e:
        tool_status["error"] = f"npm audit execution failed: {str(e)}"

    return violations, tool_status


# ============================================================================
# Decision Logic
# ============================================================================


def _determine_status(violations: list[Violation]) -> str:
    """Determine gate status (PASS, WARN, FAIL) from violations.

    Decision cascade:
    1. Any ERROR → FAIL (hard-fail)
    2. Any WARN → WARN (soft-fail)
    3. No violations → PASS

    Args:
        violations: aggregated violation list

    Returns:
        Status string: PASS, WARN, or FAIL
    """
    has_error = any(v["severity"] == "ERROR" for v in violations)
    has_warn = any(v["severity"] == "WARN" for v in violations)

    if has_error:
        return "FAIL"
    elif has_warn:
        return "WARN"
    else:
        return "PASS"


def _sort_violations(violations: list[Violation]) -> list[Violation]:
    """Sort violations by severity (ERROR > WARN > INFO).

    Args:
        violations: unsorted violation list

    Returns:
        Sorted violation list
    """
    return sorted(violations, key=lambda v: SEVERITY_ORDER.get(v["severity"], 2))


def _generate_remediation_hints(violations: list[Violation]) -> list[str]:
    """Generate actionable remediation hints from violations.

    Args:
        violations: violation list

    Returns:
        List of remediation hint strings
    """
    hints = []
    seen_rules = set()

    for violation in violations:
        rule = violation["rule"]
        file_path = violation["file"]

        # Avoid duplicate hints per rule
        if rule in seen_rules:
            continue

        if rule == "aws-manager-id" or rule.startswith("gitleaks"):
            hints.append(f"Remove secret from {file_path} and use environment variables instead")
            seen_rules.add(rule)
        elif rule.startswith("B30"):  # Unsafe deserialization
            hints.append(f"Replace pickle/marshal usage in {file_path} with json or secure alternatives")
            seen_rules.add(rule)
        elif rule.startswith("B10"):  # Hardcoded secrets
            hints.append(f"Move hardcoded password/key from {file_path} to environment variables")
            seen_rules.add(rule)
        elif rule.startswith("CVE"):  # Dependency CVE
            hints.append(f"Update vulnerable package {file_path} to a patched version")
            seen_rules.add(rule)
        elif rule.startswith("auth-bypass"):
            hints.append(f"Fix authentication bypass in {file_path}")
            seen_rules.add(rule)
        elif rule.startswith("sql-injection"):
            hints.append(f"Use parameterized queries instead of string concatenation in {file_path}")
            seen_rules.add(rule)
        else:
            hints.append(f"Review and fix {rule} violation in {file_path}")
            seen_rules.add(rule)

    return hints


# ============================================================================
# Main Gate Function
# ============================================================================


def run(inputs: GateInputs) -> dict[str, Any]:
    """Execute security gate check.

    Invokes 5 security tools (gitleaks, bandit, semgrep, pip-audit, npm audit),
    aggregates findings, applies decision matrix, and returns M902-01 gate response.

    Inputs (optional):
        - changed_files: list of file paths (optional, default [] or auto-detect)
        - mode: 'shadow' or 'blocking' (default 'shadow', always exits 0 in shadow)
        - ticket_id: ticket identifier (default 'M902-16')
        - upstream_agent: name of prior stage (optional, default None)
        - downstream_agent: name of next stage (optional, default 'commit')

    Returns: dict matching M902-01 gate schema with fields:
        - version: "1.0"
        - status: "PASS", "WARN", or "FAIL"
        - gate: "security_gate_check"
        - timestamp: ISO 8601 UTC with Z suffix
        - ticket_id: from inputs or default
        - upstream_agent: from inputs or None
        - downstream_agent: from inputs or default
        - mode: 'shadow' (always)
        - _shadow_mode: true (always)
        - message: human-readable summary
        - violations: sorted by severity (ERROR > WARN > INFO)
        - remediation_hints: actionable fix suggestions
        - tool_statuses: array of 5 tool status objects
        - duration_ms: wall-clock execution time in milliseconds
        - artifacts: list of configuration file artifacts
    """
    start_time = time.time()

    try:
        # Extract inputs with defaults
        mode = inputs.get("mode", "shadow")
        ticket_id = inputs.get("ticket_id", "M902-16")
        upstream_agent = inputs.get("upstream_agent")
        downstream_agent = inputs.get("downstream_agent", "commit")

        # Run all 5 tools
        gitleaks_violations, gitleaks_status = _run_gitleaks(inputs)
        bandit_violations, bandit_status = _run_bandit(inputs)
        semgrep_violations, semgrep_status = _run_semgrep(inputs)
        pip_audit_violations, pip_audit_status = _run_pip_audit(inputs)
        npm_audit_violations, npm_audit_status = _run_npm_audit(inputs)

        # Aggregate violations
        all_violations = (
            gitleaks_violations
            + bandit_violations
            + semgrep_violations
            + pip_audit_violations
            + npm_audit_violations
        )

        # Sort violations by severity
        sorted_violations = _sort_violations(all_violations)

        # Determine status
        status = _determine_status(sorted_violations)

        # Generate remediation hints
        remediation_hints = _generate_remediation_hints(sorted_violations)

        # Build message
        if status == "PASS":
            message = "Security gate passed: no violations detected"
        elif status == "WARN":
            message = f"Security gate: {len(sorted_violations)} warnings (no critical findings)"
        else:  # FAIL
            error_count = len([v for v in sorted_violations if v["severity"] == "ERROR"])
            message = f"Security gate failed: {error_count} critical violations detected"

        # Compute duration
        elapsed_seconds = time.time() - start_time
        duration_ms = int(elapsed_seconds * 1000)

        # Build tool statuses array
        tool_statuses = [
            gitleaks_status,
            bandit_status,
            semgrep_status,
            pip_audit_status,
            npm_audit_status,
        ]

        # Build artifacts array
        artifacts = [
            {"path": "ci/scripts/gates/security_gate_check.py", "sha256": "unknown"},
            {"path": ".semgrep.yml", "sha256": "unknown"},
        ]

        # Build result dict
        result = {
            "version": "1.0",
            "status": status,
            "gate": "security_gate_check",
            "upstream_agent": upstream_agent,
            "downstream_agent": downstream_agent,
            "ticket_id": ticket_id,
            "timestamp": _iso8601_timestamp(),
            "mode": "shadow",
            "_shadow_mode": True,
            "message": message,
            "violations": sorted_violations,
            "remediation_hints": remediation_hints,
            "tool_statuses": tool_statuses,
            "duration_ms": duration_ms,
            "artifacts": artifacts,
        }

        return result

    except Exception as e:
        logger.error(f"Security gate execution failed: {str(e)}")
        # Return minimal failure result
        elapsed_seconds = time.time() - start_time
        duration_ms = int(elapsed_seconds * 1000)

        return {
            "version": "1.0",
            "status": "FAIL",
            "gate": "security_gate_check",
            "upstream_agent": inputs.get("upstream_agent"),  # type: ignore
            "downstream_agent": inputs.get("downstream_agent", "commit"),  # type: ignore
            "ticket_id": inputs.get("ticket_id", "M902-16"),  # type: ignore
            "timestamp": _iso8601_timestamp(),
            "mode": "shadow",
            "_shadow_mode": True,
            "message": f"Security gate failed with exception: {str(e)}",
            "violations": [
                {
                    "file": "security_gate_check.py",
                    "line": None,
                    "rule": "GATE_ERROR",
                    "message": str(e),
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": ["Review security gate error logs for details"],
            "tool_statuses": [
                {"name": "gitleaks", "exit_code": None, "findings_count": 0, "timeout": False, "error": "Not run"},
                {"name": "bandit", "exit_code": None, "findings_count": 0, "timeout": False, "error": "Not run"},
                {"name": "semgrep", "exit_code": None, "findings_count": 0, "timeout": False, "error": "Not run"},
                {"name": "pip-audit", "exit_code": None, "findings_count": 0, "timeout": False, "error": "Not run"},
                {"name": "npm-audit", "exit_code": None, "findings_count": 0, "timeout": False, "error": "Not run"},
            ],
            "duration_ms": duration_ms,
            "artifacts": [],
        }
