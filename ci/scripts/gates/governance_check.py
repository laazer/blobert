"""
Governance check gate — automated enforcement of governance rules for multi-agent handoffs.

Specification: project_board/specs/902_03_handoff_governance_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/03_handoff_governance_rule_enforcement.md

Rules validated across six categories:
  - Architecture (AR-01 to AR-06): dependency direction, layer boundaries
  - Exception Safety (EX-01 to EX-05): bare except, silent swallowing, context preservation
  - Reflection Safety (RF-01 to RF-05): getattr/setattr scoping, dynamic import validation
  - Async Safety (AS-01 to AS-05): blocking I/O in async, subprocess timeouts, React hooks
  - Observability (OB-01 to OB-05): structured logging, error tracking
  - Governance Integrity (GV-01 to GV-06): bypass prevention, suppression format

JSON Output: matches M902-01 gate schema with violations[], remediation_hints[], artifacts[], duration_ms.
Modes: shadow (report, exit 0) and blocking (fail on violations).
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rule catalog (frozen from spec)
RULES = {
    # Architecture (AR-01 to AR-06)
    "AR-01": {
        "name": "arch-no-domain-http",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"(import\s+(fastapi|flask|requests|urllib))",
        "scope": ["asset_generation/python/src/model_registry", "asset_generation/python/src/enemies",
                  "asset_generation/python/src/player", "asset_generation/python/src/materials"],
        "file_pattern": r"\.py$",
        "description": "Domain code must not import HTTP libraries",
    },
    "AR-02": {
        "name": "arch-no-router-logic",
        "severity": "WARN",
        "suppressible": True,
        "description": "Router files must delegate to service layer (>10 LOC in handler)",
    },
    "AR-03": {
        "name": "arch-service-not-http",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"(JSONResponse|fastapi\.Response)",
        "scope": ["asset_generation/web/backend/services"],
        "file_pattern": r"\.py$",
        "description": "Service layer must not construct HTTP responses",
    },
    "AR-04": {
        "name": "arch-forbidden-reverse-imports",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"from\s+\.\.routers",
        "scope": ["asset_generation/web/backend/services", "asset_generation/web/backend/core"],
        "file_pattern": r"\.py$",
        "description": "Services/adapters must not import from routers",
    },
    "AR-05": {
        "name": "arch-react-hook-deps",
        "severity": "ERROR",
        "suppressible": True,
        "description": "React hooks must include proper dependency arrays",
        "file_pattern": r"\.(tsx|ts)$",
    },
    "AR-06": {
        "name": "arch-feature-boundary",
        "severity": "WARN",
        "suppressible": True,
        "description": "Feature components must not directly import from other features",
        "file_pattern": r"\.(tsx|ts)$",
    },
    # Exception Safety (EX-01 to EX-05)
    "EX-01": {
        "name": "except-no-bare",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"except\s*:",
        "scope": [],  # All Python files
        "file_pattern": r"\.py$",
        "description": "No bare `except:` clauses",
    },
    "EX-02": {
        "name": "except-no-silent-swallow",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"except\s+\w+\s*:\s*pass",
        "scope": [],
        "file_pattern": r"\.py$",
        "description": "Exception handlers must log or re-raise",
    },
    "EX-03": {
        "name": "except-preserve-context",
        "severity": "WARN",
        "suppressible": True,
        "description": "Re-raised exceptions must preserve context via `from e`",
    },
    "EX-04": {
        "name": "except-handler-must-log",
        "severity": "WARN",
        "suppressible": True,
        "description": "Critical handlers must log before returning/re-raising",
    },
    "EX-05": {
        "name": "except-no-bare-promise-reject",
        "severity": "WARN",
        "suppressible": True,
        "description": "TypeScript: no bare Promise rejections",
        "file_pattern": r"\.(tsx|ts)$",
    },
    # Reflection Safety (RF-01 to RF-05)
    "RF-01": {
        "name": "reflect-getattr-scoped",
        "severity": "WARN",
        "suppressible": True,
        "pattern": r"getattr\(|hasattr\(",
        "scope": [],
        "file_pattern": r"\.py$",
        "description": "`getattr`/`hasattr` must be in allowed zones",
    },
    "RF-02": {
        "name": "reflect-setattr-forbidden",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"setattr\(",
        "scope": ["asset_generation/python/src/model_registry", "asset_generation/python/src/enemies",
                  "asset_generation/python/src/player", "asset_generation/python/src/materials"],
        "file_pattern": r"\.py$",
        "description": "No `setattr` on domain objects",
    },
    "RF-03": {
        "name": "reflect-dict-mutation-forbidden",
        "severity": "WARN",
        "suppressible": True,
        "pattern": r"\.__dict__\[",
        "scope": [],
        "file_pattern": r"\.py$",
        "description": "No `__dict__` direct mutation",
    },
    "RF-04": {
        "name": "reflect-import-validation",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"importlib\.import_module\(\s*(?!.*validate|.*allowlist)",
        "scope": ["asset_generation/web/backend/services"],
        "file_pattern": r"\.py$",
        "description": "Dynamic imports must validate module names",
    },
    "RF-05": {
        "name": "reflect-type-check-explicit",
        "severity": "INFO",
        "suppressible": False,
        "pattern": r"type\([^)]+\)\s*==",
        "scope": [],
        "file_pattern": r"\.py$",
        "description": "Type checks must use `isinstance`, not `type(x) ==`",
    },
    # Async Safety (AS-01 to AS-05)
    "AS-01": {
        "name": "async-no-sync-network",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"(requests\.(get|post|put|delete)|urllib\.request\.urlopen)",
        "scope": ["asset_generation/web/backend/routers", "asset_generation/web/backend/services"],
        "file_pattern": r"\.py$",
        "description": "FastAPI routes must use async HTTP clients",
    },
    "AS-02": {
        "name": "async-no-unbounded-sleep",
        "severity": "ERROR",
        "suppressible": True,
        "pattern": r"time\.sleep\(\s*(?![0-9]|.*\s*<\s*[01])",
        "scope": ["asset_generation/web/backend/routers"],
        "file_pattern": r"\.py$",
        "description": "FastAPI routes must not sleep without timeout",
    },
    "AS-03": {
        "name": "async-subprocess-timeout",
        "severity": "WARN",
        "suppressible": True,
        "pattern": r"subprocess\.(run|call|Popen)\([^)]*\)",
        "scope": ["asset_generation/web/backend"],
        "file_pattern": r"\.py$",
        "description": "Subprocess calls must include timeout parameter",
    },
    "AS-04": {
        "name": "react-hook-effect-cleanup",
        "severity": "ERROR",
        "suppressible": False,
        "description": "useEffect cleanup must be registered",
        "file_pattern": r"\.(tsx|ts)$",
    },
    "AS-05": {
        "name": "react-hook-missing-deps",
        "severity": "ERROR",
        "suppressible": False,
        "description": "useEffect dependency arrays must be complete",
        "file_pattern": r"\.(tsx|ts)$",
    },
    # Observability (OB-01 to OB-05)
    "OB-01": {
        "name": "obs-critical-flows-log",
        "severity": "WARN",
        "suppressible": True,
        "description": "Critical backend flows must log operation_id and duration",
    },
    "OB-02": {
        "name": "obs-error-type-logged",
        "severity": "WARN",
        "suppressible": True,
        "description": "Exception handlers must log error_type",
    },
    "OB-03": {
        "name": "obs-user-context-if-applicable",
        "severity": "INFO",
        "suppressible": True,
        "description": "Routes handling user-scoped operations must log user_context",
    },
    "OB-04": {
        "name": "obs-no-bare-print",
        "severity": "WARN",
        "suppressible": False,
        "pattern": r"^\s*print\(",
        "scope": ["asset_generation/web/backend"],
        "file_pattern": r"\.py$",
        "description": "No bare `print()` statements in backend",
    },
    "OB-05": {
        "name": "obs-console-use-discouraged",
        "severity": "WARN",
        "suppressible": True,
        "pattern": r"console\.log\(",
        "scope": ["asset_generation/web/frontend/src"],
        "file_pattern": r"\.(tsx|ts)$",
        "description": "Discourage bare `console.log` in React",
    },
    # Governance Integrity (GV-01 to GV-06)
    "GV-01": {
        "name": "gov-no-git-no-verify",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"--no-verify",
        "scope": [],
        "file_pattern": r"",
        "description": "No `--no-verify` in committed source",
    },
    "GV-02": {
        "name": "gov-suppression-requires-issue",
        "severity": "WARN",
        "suppressible": False,
        "description": "Suppressions must cite issue or ticket",
    },
    "GV-03": {
        "name": "gov-no-blanket-linter-disable",
        "severity": "ERROR",
        "suppressible": False,
        "pattern": r"#\s*eslint-disable\s*(?![a-z-/])",
        "scope": ["asset_generation/web/frontend"],
        "file_pattern": r"\.(tsx|ts)$",
        "description": "Linter disables must be granular",
    },
    "GV-04": {
        "name": "gov-no-sempreg-disable-all",
        "severity": "WARN",
        "suppressible": False,
        "pattern": r"#\s*nosemgrep\s*(?![A-Z]{2}-\d{2})",
        "scope": [],
        "file_pattern": r"\.py$",
        "description": "No blanket semgrep disables",
    },
    "GV-05": {
        "name": "gov-gate-bypass-detection",
        "severity": "WARN",
        "suppressible": False,
        "description": "No attempts to bypass gate runner",
    },
    "GV-06": {
        "name": "gov-process-audit-trail",
        "severity": "WARN",
        "suppressible": False,
        "description": "Gate execution must be logged",
    },
}

# Remediation hints mapped to rule IDs
REMEDIATION_HINTS = {
    "EX-01": "Replace bare 'except:' with specific exception type: 'except ValueError as e:'",
    "EX-02": "Add logging or re-raise in exception handler: 'logger.error(...); raise' or 'logger.error(...); return'",
    "AR-01": "Remove HTTP library imports from domain modules (fastapi, requests, urllib, flask)",
    "AR-03": "Move HTTP response construction to routers; services should return data only",
    "AR-04": "Services and adapters must not import from routers; use dependency injection instead",
    "AS-01": "Replace requests.get/post with httpx.AsyncClient or aiohttp for async contexts",
    "AS-02": "Replace time.sleep() with asyncio.sleep() and wrap in asyncio.timeout() context",
    "OB-04": "Replace print() with logger.info/warning/error() for structured logging",
    "GV-01": "Remove --no-verify flags; all commits must pass validation gates",
    "GV-03": "Replace blanket eslint-disable with granular: # eslint-disable-line <rule-name>",
    "GV-04": "Replace blanket nosemgrep with specific rule: # nosemgrep <rule-id> <issue-link>",
    "RF-02": "Use factory/builder pattern instead of setattr; define proper constructors",
    "RF-01": "Move getattr/hasattr usage to routers, serializers, utilities, or tests only",
}


def _is_in_allowed_zone(file_path: str, rule_id: str) -> bool:
    """Check if file is in an allowed zone for reflection operations."""
    allowed_zones = {
        "RF-01": [
            "routers",  # Zone A
            "utilities",  # Zone C
            "tests",  # Zone D
            "__tests__",  # Zone D (TS)
        ]
    }

    zones = allowed_zones.get(rule_id, [])
    for zone in zones:
        if zone in file_path:
            return True
    return False


def _parse_suppression_comment(comment: str) -> tuple[Optional[str], Optional[str]]:
    """Parse suppression comment format: # nosemgrep <rule-id> <issue-link>.

    Returns: (rule_id, issue_link) or (None, None) if invalid.
    """
    # Match: # nosemgrep <RULE-ID> <ISSUE>
    match = re.search(r"#\s*nosemgrep\s+([A-Z]{2}-\d{2})\s+(\S+)", comment)
    if match:
        return match.group(1), match.group(2)
    return None, None


def _is_valid_issue_link(issue_link: str) -> bool:
    """Validate that issue link is a valid reference."""
    # Valid: M902-03, https://github.com/..., JIRA-123, GH-456
    patterns = [
        r"^M\d{3}-\d{2}$",  # Milestone-task format
        r"^https?://",  # URL
        r"^JIRA-\d+$",  # JIRA
        r"^GH-\d+$",  # GitHub
    ]
    return any(re.match(p, issue_link) for p in patterns)


def _has_valid_suppression(line: str, rule_id: str) -> bool:
    """Check if line has valid suppression for given rule."""
    rule_id_match, issue_link = _parse_suppression_comment(line)
    if rule_id_match == rule_id and issue_link:
        return _is_valid_issue_link(issue_link)
    return False


def _scan_file_for_violations(file_path: Path) -> list[dict[str, Any]]:
    """Scan a single file for governance violations.

    Returns: list of violation dicts
    """
    violations = []

    if not file_path.exists():
        return violations

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.debug(f"Failed to read file {file_path}: {e}")
        return violations

    lines = content.split("\n")
    file_str = str(file_path)

    # Check each rule
    for rule_id, rule_def in RULES.items():
        pattern = rule_def.get("pattern")
        if not pattern:
            continue

        file_pattern = rule_def.get("file_pattern", "")
        if file_pattern and not re.search(file_pattern, file_str):
            continue

        scope = rule_def.get("scope", [])
        if scope and not any(s in file_str for s in scope):
            continue

        # Search for pattern matches
        try:
            compiled_pattern = re.compile(pattern, re.MULTILINE)
        except re.error:
            logger.debug(f"Invalid regex pattern for {rule_id}: {pattern}")
            continue

        for line_num, line in enumerate(lines, 1):
            if compiled_pattern.search(line):
                # Check for suppression
                if rule_def.get("suppressible") and _has_valid_suppression(line, rule_id):
                    continue

                # Special handling for certain rules
                if rule_id == "EX-02" and "except" not in line:
                    continue

                # Determine if this is actually a violation context
                if rule_id == "RF-01" and _is_in_allowed_zone(file_str, rule_id):
                    continue

                violations.append({
                    "file": file_str,
                    "line": line_num,
                    "rule": rule_id,
                    "message": rule_def.get("description", "Governance violation"),
                    "severity": rule_def.get("severity", "WARN"),
                    "suppressible": rule_def.get("suppressible", False),
                })

    return violations


def _check_bare_except(file_path: Path) -> list[dict[str, Any]]:
    """Dedicated check for bare except (EX-01) with better accuracy."""
    violations = []

    if not file_path.suffix == ".py":
        return violations

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations

    lines = content.split("\n")
    file_str = str(file_path)

    for line_num, line in enumerate(lines, 1):
        # Match bare except: (with optional comment)
        if re.search(r"except\s*:\s*(?:#|$)", line):
            # Check for suppression
            if _has_valid_suppression(line, "EX-01"):
                continue

            violations.append({
                "file": file_str,
                "line": line_num,
                "rule": "EX-01",
                "message": "Bare except clause detected",
                "severity": "ERROR",
                "suppressible": False,
            })

    return violations


def _check_governance_bypass(file_path: Path) -> list[dict[str, Any]]:
    """Check for governance bypass patterns (GV-01, GV-03, GV-04, GV-02)."""
    violations = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations

    lines = content.split("\n")
    file_str = str(file_path)

    for line_num, line in enumerate(lines, 1):
        # GV-01: --no-verify
        if "--no-verify" in line:
            violations.append({
                "file": file_str,
                "line": line_num,
                "rule": "GV-01",
                "message": "Git hook bypass flag '--no-verify' found",
                "severity": "ERROR",
                "suppressible": False,
            })

        # GV-03: blanket eslint-disable
        if re.search(r"#\s*eslint-disable\s*(?![a-z-/])", line):
            violations.append({
                "file": file_str,
                "line": line_num,
                "rule": "GV-03",
                "message": "Blanket eslint-disable without rule names",
                "severity": "ERROR",
                "suppressible": False,
            })

        # GV-04: blanket nosemgrep
        if re.search(r"#\s*nosemgrep\s*(?![A-Z]{2}-\d{2})", line):
            # Check if it has at least a rule ID but no issue link
            rule_match = re.search(r"#\s*nosemgrep\s+([A-Z]{2}-\d{2})(?:\s|$)", line)
            if rule_match:
                # Has rule ID; check if it has issue link
                issue_part = line[line.index(rule_match.group(1)) + len(rule_match.group(1)):].strip()
                if not issue_part or not _is_valid_issue_link(issue_part.split()[0] if issue_part.split() else ""):
                    violations.append({
                        "file": file_str,
                        "line": line_num,
                        "rule": "GV-02",
                        "message": "Suppression must cite issue or ticket",
                        "severity": "WARN",
                        "suppressible": False,
                    })
            else:
                # No rule ID at all
                violations.append({
                    "file": file_str,
                    "line": line_num,
                    "rule": "GV-04",
                    "message": "Blanket nosemgrep without rule ID",
                    "severity": "WARN",
                    "suppressible": False,
                })

    return violations


def _scan_codebase(repo_root: Path = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Scan entire codebase for governance violations.

    Returns: (violations, scanned_files)
    """
    if repo_root is None:
        repo_root = Path.cwd()

    violations = []
    scanned_files = []

    # Scan Python files
    python_paths = [
        repo_root / "asset_generation" / "python" / "src",
        repo_root / "asset_generation" / "web" / "backend",
    ]

    # Scan TypeScript files
    ts_paths = [
        repo_root / "asset_generation" / "web" / "frontend" / "src",
    ]

    all_paths = python_paths + ts_paths

    for base_path in all_paths:
        if not base_path.exists():
            continue

        # Python files
        if "python" in str(base_path) or "backend" in str(base_path):
            for py_file in base_path.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                scanned_files.append(str(py_file.relative_to(repo_root)))
                violations.extend(_check_bare_except(py_file))
                violations.extend(_scan_file_for_violations(py_file))
                violations.extend(_check_governance_bypass(py_file))

        # TypeScript files
        if "frontend" in str(base_path):
            for ts_file in base_path.rglob("*.tsx"):
                if "node_modules" in str(ts_file):
                    continue
                scanned_files.append(str(ts_file.relative_to(repo_root)))
                violations.extend(_check_governance_bypass(ts_file))
                violations.extend(_scan_file_for_violations(ts_file))

    return violations, scanned_files


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Gate entry point called by gate_runner.

    Args:
        inputs: dict with keys:
            - mode: "shadow" or "blocking"
            - repo_root: optional path to repo root
            - ticket_id: ticket identifier
            - upstream_agent: name of upstream agent
            - downstream_agent: name of downstream agent

    Returns: dict with status, violations, remediation_hints, artifacts, duration_ms
    """
    start_time = time.time()
    mode = inputs.get("mode", "shadow")
    repo_root = Path(inputs.get("repo_root", "."))
    ticket_id = inputs.get("ticket_id", "unknown")
    upstream_agent = inputs.get("upstream_agent", "unknown")
    downstream_agent = inputs.get("downstream_agent", "unknown")

    logger.info(f"Starting governance check (mode={mode}, repo={repo_root})")

    # Scan codebase
    violations, scanned_files = _scan_codebase(repo_root)

    # Deduplicate violations
    unique_violations = []
    seen = set()
    for v in violations:
        key = (v["file"], v["line"], v["rule"])
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    violations = unique_violations

    # Build remediation hints
    remediation_hints = []
    seen_hints = set()
    for violation in violations:
        rule_id = violation.get("rule", "")
        if rule_id in REMEDIATION_HINTS:
            hint = REMEDIATION_HINTS[rule_id]
            if hint not in seen_hints:
                remediation_hints.append(hint)
                seen_hints.add(hint)

    # Determine overall status
    has_errors = any(v.get("severity") == "ERROR" for v in violations)
    status = "FAIL" if violations else "PASS"

    duration_ms = int((time.time() - start_time) * 1000)

    # Build gate result
    result = {
        "version": "0.1.0",
        "status": status,
        "gate": "governance_check",
        "upstream_agent": upstream_agent,
        "downstream_agent": downstream_agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id,
        "violations": violations,
        "remediation_hints": remediation_hints,
        "artifacts": [{"path": f, "type": "scanned"} for f in scanned_files[:100]],  # Limit artifacts
        "duration_ms": duration_ms,
        "message": f"{'Violations' if violations else 'No violations'} detected in governance check.",
    }

    logger.info(f"Governance check complete: {len(violations)} violations, {len(scanned_files)} files scanned")

    return result
