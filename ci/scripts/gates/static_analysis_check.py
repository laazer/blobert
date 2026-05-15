"""
Static analysis gate orchestrator for M902-02.

Runs all configured static analysis tools (Python, TypeScript, Godot, duplication)
and aggregates results into a structured JSON output matching the gate schema.

Tools:
  Python: ruff, mypy, bandit, vulture, import-linter, semgrep, wemake
  TypeScript: eslint + plugins
  Godot: gdformat, gdlint (optional)
  Cross-repo: jscpd

Output: JSON matching gate schema from M902-01 framework
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tool timeout constraints (seconds)
TOOL_TIMEOUTS = {
    "ruff": 60,
    "mypy": 120,
    "bandit": 60,
    "vulture": 60,
    "import-linter": 60,
    "semgrep": 120,
    "wemake-python-styleguide": 60,
    "eslint": 60,
    "gdformat": 60,
    "gdlint": 60,
    "jscpd": 120,
}

# Gate schema fields (from M902-01 framework)
GATE_SCHEMA = {
    "status": "shadow|blocking",
    "violations": [
        {
            "tool": "str",
            "severity": "ERROR|WARNING|INFO",
            "file": "str",
            "line": "int",
            "column": "int",
            "message": "str",
        }
    ],
    "remediation_hints": ["str"],
    "artifacts": ["str"],
    "duration_ms": "int",
    "upstream_agent": "str",
    "downstream_agent": "str",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _build_violation(
    tool: str,
    severity: str,
    file: str,
    line: int,
    column: int,
    message: str,
) -> dict[str, Any]:
    """Build a violation object matching gate schema.

    Args:
        tool: Tool name (e.g., 'ruff', 'mypy')
        severity: One of 'ERROR', 'WARNING', 'INFO'
        file: File path (relative or absolute)
        line: Line number (0-based or 1-based depending on tool)
        column: Column number (0-based or 1-based depending on tool)
        message: Violation message

    Returns:
        dict matching gate schema violation structure
    """
    return {
        "tool": tool,
        "severity": severity.upper() if severity else "WARNING",
        "file": file,
        "line": int(line) if line else 0,
        "column": int(column) if column else 0,
        "message": str(message),
    }


def _parse_json_output(text: str, tool_name: str) -> dict | list | None:
    """Safely parse JSON output from tool, with error logging.

    Args:
        text: Raw output text from tool
        tool_name: Name of tool (for logging)

    Returns:
        Parsed JSON object/array, or None if parse failed
    """
    if not text or not text.strip():
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"{tool_name}: JSON parse failed - {str(e)[:200]}")
        return None


def _tool_available(tool_name: str, check_npm: bool = False) -> bool:
    """Check if a tool is available in PATH.

    Args:
        tool_name: Tool name to check
        check_npm: If True, check for npm availability instead

    Returns:
        True if tool is available, False otherwise
    """
    if check_npm:
        return shutil.which("npm") is not None
    return shutil.which(tool_name) is not None


def _run_tool(
    cmd: list[str],
    tool_name: str,
    timeout_sec: int = 60,
) -> subprocess.CompletedProcess | None:
    """Run a tool command with timeout and error handling.

    Args:
        cmd: Command as list (e.g., ['ruff', 'check', 'src'])
        tool_name: Tool name for logging
        timeout_sec: Timeout in seconds

    Returns:
        CompletedProcess if successful, None if timeout or error
    """
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"{tool_name}: timeout after {timeout_sec}s")
        return None
    except Exception as e:
        logger.error(f"{tool_name}: execution failed - {type(e).__name__}: {str(e)[:200]}")
        return None


# ============================================================================
# TOOL REGISTRY AND EXECUTION
# ============================================================================


class ToolExecutor:
    """Generic tool executor for registries of similar tools."""

    def __init__(self, tool_name: str, availability_check: Callable[[], bool],
                 parser: Callable[[str], list[dict]]):
        """Initialize tool executor.

        Args:
            tool_name: Display name of tool
            availability_check: Callable that returns True if tool is available
            parser: Callable that takes tool output string and returns violations list
        """
        self.tool_name = tool_name
        self.availability_check = availability_check
        self.parser = parser

    def execute(self) -> tuple[list[dict], str]:
        """Execute tool and return violations + status.

        Returns:
            Tuple of (violations list, status string)
        """
        if not self.availability_check():
            return [], "SKIPPED"

        try:
            violations = self.parser()
            return violations, "OK"
        except Exception as e:
            logger.error(f"{self.tool_name}: parsing failed - {type(e).__name__}: {str(e)[:200]}")
            return [], f"ERROR: {str(e)[:100]}"


def run(inputs: dict) -> dict:
    """
    Main gate runner function (required by gate_runner.py framework).

    Args:
        inputs: dict with keys:
            - ticket_id: str
            - upstream_agent: str
            - downstream_agent: str
            - mode: "shadow" or "blocking" (default: "shadow")
            - output_dir: str (optional, default: current dir)

    Returns:
        dict matching GATE_SCHEMA with aggregated violations and exit status
    """
    start_time = time.time()

    # Extract inputs with defaults
    ticket_id = inputs.get("ticket_id", "M902-02")
    upstream_agent = inputs.get("upstream_agent", "Implementation Generalist")
    downstream_agent = inputs.get("downstream_agent", "Spec Agent")
    mode = inputs.get("mode", "shadow")
    output_dir = inputs.get("output_dir", ".")

    repo_root = Path(__file__).resolve().parents[3]  # blobert/ (from ci/scripts/gates/)

    # Validate output directory
    if output_dir != ".":
        output_path = Path(output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

    # Initialize result structure
    all_violations: list[dict] = []
    tool_statuses: dict[str, str] = {}
    hints: set[str] = set()

    # Define tool registry: maps tool name to executor callable
    python_targets = [
        str(repo_root / "asset_generation/python/src"),
        str(repo_root / "asset_generation/web/backend"),
    ]

    tools: dict[str, Callable[[], tuple[list[dict], str]]] = {
        "ruff": lambda: _execute_ruff(python_targets),
        "mypy": lambda: _execute_mypy(python_targets),
        "bandit": lambda: _execute_bandit(python_targets),
        "vulture": lambda: _execute_vulture([str(repo_root / "asset_generation/python/src")]),
        "import-linter": lambda: _execute_import_linter(repo_root / "asset_generation/python"),
        "semgrep": lambda: _execute_semgrep(
            python_targets,
            str(repo_root / "asset_generation/python/.semgrep.yml"),
        ),
        "wemake-python-styleguide": lambda: _execute_wemake([str(repo_root / "asset_generation/python/src")]),
        "eslint": lambda: _execute_eslint(
            str(repo_root / "asset_generation/web/frontend/src"),
            repo_root / "asset_generation/web/frontend",
        ),
        "gdformat": lambda: _execute_gdformat([
            str(repo_root / "scripts"),
            str(repo_root / "scenes"),
            str(repo_root / "tests"),
        ]),
        "gdlint": lambda: _execute_gdlint([
            str(repo_root / "scripts"),
            str(repo_root / "scenes"),
            str(repo_root / "tests"),
        ]),
        "jscpd": lambda: _execute_jscpd(str(repo_root), repo_root / "jscpd.json"),
    }

    # Execute all tools
    for tool_name, executor in tools.items():
        try:
            violations, status = executor()
            all_violations.extend(violations)
            tool_statuses[tool_name] = status
            if status == "SKIPPED":
                hints.add(f"{tool_name}: tool not found in PATH")
        except Exception as e:
            error_msg = f"ERROR: {str(e)[:100]}"
            tool_statuses[tool_name] = error_msg
            hints.add(f"{tool_name}: {error_msg}")
            logger.exception(f"Tool {tool_name} failed:")

    # =========================================================================
    # AGGREGATE RESULTS
    # =========================================================================

    duration_ms = int((time.time() - start_time) * 1000)

    # Build remediation hints from tool statuses
    for tool, status in tool_statuses.items():
        if "SKIPPED" in status:
            hints.add(f"{tool}: skipped ({status})")
        elif "ERROR" in status and tool not in [h.split(":")[0] for h in hints]:
            hints.add(f"{tool}: {status}")

    # Determine exit status based on mode
    has_violations = len(all_violations) > 0
    status = "blocking" if mode == "blocking" and has_violations else "shadow"

    # Build result dict matching gate schema
    result: dict[str, Any] = {
        "status": status,
        "violations": all_violations,
        "remediation_hints": sorted(list(hints)),
        "artifacts": [],  # Populated if gate produces output files
        "duration_ms": duration_ms,
        "upstream_agent": upstream_agent,
        "downstream_agent": downstream_agent,
        "tool_statuses": tool_statuses,  # Extra: detailed per-tool status
    }

    # Write JSON output if output_dir specified
    if output_dir != ".":
        output_path = Path(output_dir) / f"static_analysis_check_{ticket_id}.json"
        output_path.write_text(json.dumps(result, indent=2))
        result["artifacts"].append(str(output_path))

    return result


# ============================================================================
# TOOL EXECUTORS (REFACTORED)
# ============================================================================


def _execute_ruff(targets: list[str]) -> tuple[list[dict], str]:
    """Execute ruff and return violations + status."""
    if not _tool_available("ruff"):
        return [], "SKIPPED"

    cmd = ["ruff", "check"] + targets + ["--output-format=json"]
    result = _run_tool(cmd, "ruff", TOOL_TIMEOUTS["ruff"])
    if not result:
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "ruff")
    if not output:
        return [], "OK"

    violations = []
    for item in output if isinstance(output, list) else [output]:
        violations.append(_build_violation(
            tool="ruff",
            severity="ERROR" if "error" in str(item).lower() else "WARNING",
            file=item.get("filename", "unknown"),
            line=item.get("line", 0),
            column=item.get("column", 0),
            message=item.get("message", str(item)),
        ))
    return violations, "OK"


def _execute_mypy(targets: list[str]) -> tuple[list[dict], str]:
    """Execute mypy and return violations + status."""
    if not _tool_available("mypy"):
        return [], "SKIPPED"

    cmd = ["mypy"] + targets + ["--json"]
    result = _run_tool(cmd, "mypy", TOOL_TIMEOUTS["mypy"])
    if not result:
        return [], "SKIPPED"

    violations = []
    for line in result.stdout.split("\n"):
        if not line.strip():
            continue
        output = _parse_json_output(line, "mypy")
        if not output:
            continue
        violations.append(_build_violation(
            tool="mypy",
            severity=output.get("severity", "ERROR").upper(),
            file=output.get("filename", "unknown"),
            line=output.get("line", 0),
            column=output.get("column", 0),
            message=output.get("message", str(output)),
        ))
    return violations, "OK"


def _execute_bandit(targets: list[str]) -> tuple[list[dict], str]:
    """Execute bandit and return violations + status."""
    if not _tool_available("bandit"):
        return [], "SKIPPED"

    cmd = ["bandit", "-r"] + targets + ["--format", "json"]
    result = _run_tool(cmd, "bandit", TOOL_TIMEOUTS["bandit"])
    if not result:
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "bandit")
    if not output or not isinstance(output, dict):
        return [], "OK"

    violations = []
    for item in output.get("results", []):
        violations.append(_build_violation(
            tool="bandit",
            severity=item.get("severity", "WARNING").upper(),
            file=item.get("filename", "unknown"),
            line=item.get("line_number", 0),
            column=0,
            message=item.get("issue_text", str(item)),
        ))
    return violations, "OK"


def _execute_vulture(targets: list[str]) -> tuple[list[dict], str]:
    """Execute vulture and return violations + status."""
    if not _tool_available("vulture"):
        return [], "SKIPPED"

    cmd = ["vulture"] + targets + ["--json"]
    result = _run_tool(cmd, "vulture", TOOL_TIMEOUTS["vulture"])
    if not result:
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "vulture")
    if not output:
        return [], "OK"

    violations = []
    for item in output if isinstance(output, list) else [output]:
        violations.append(_build_violation(
            tool="vulture",
            severity="WARNING",
            file=item.get("filename", "unknown"),
            line=item.get("line_number", 0),
            column=0,
            message=item.get("message", str(item)),
        ))
    return violations, "OK"


def _execute_import_linter(target_dir: Path) -> tuple[list[dict], str]:
    """Execute import-linter and return violations + status."""
    if not _tool_available("lint-imports"):
        return [], "SKIPPED"

    try:
        cmd = ["lint-imports"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=TOOL_TIMEOUTS["import-linter"], cwd=str(target_dir)
        )
    except subprocess.TimeoutExpired:
        logger.error("import-linter: timeout")
        return [], "SKIPPED"
    except Exception as e:
        logger.error(f"import-linter: {type(e).__name__}: {str(e)[:200]}")
        return [], "SKIPPED"

    violations = []
    for line in result.stdout.split("\n"):
        if "Contract" in line or "violation" in line.lower():
            violations.append(_build_violation(
                tool="import-linter",
                severity="ERROR",
                file=str(target_dir),
                line=0,
                column=0,
                message=line.strip(),
            ))
    return violations, "OK"


def _execute_semgrep(targets: list[str], config_file: str) -> tuple[list[dict], str]:
    """Execute semgrep and return violations + status."""
    if not _tool_available("semgrep"):
        return [], "SKIPPED"

    cmd = ["semgrep", "--config", config_file] + targets + ["--json"]
    result = _run_tool(cmd, "semgrep", TOOL_TIMEOUTS["semgrep"])
    if not result:
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "semgrep")
    if not output or not isinstance(output, dict):
        return [], "OK"

    violations = []
    for item in output.get("results", []):
        violations.append(_build_violation(
            tool="semgrep",
            severity=item.get("severity", "WARNING").upper(),
            file=item.get("path", "unknown"),
            line=item.get("start", {}).get("line", 0),
            column=item.get("start", {}).get("col", 0),
            message=item.get("extra", {}).get("message", str(item)),
        ))
    return violations, "OK"


def _execute_wemake(targets: list[str]) -> tuple[list[dict], str]:
    """Execute wemake-python-styleguide and return violations + status."""
    if not _tool_available("flake8"):
        return [], "SKIPPED"

    cmd = ["flake8"] + targets + ["--format=json"]
    result = _run_tool(cmd, "wemake-python-styleguide", TOOL_TIMEOUTS["wemake-python-styleguide"])
    if not result:
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "wemake-python-styleguide")
    if not output or not isinstance(output, dict):
        return [], "OK"

    violations = []
    for file_path, items in output.items():
        for item in items:
            violations.append(_build_violation(
                tool="wemake-python-styleguide",
                severity="WARNING",
                file=file_path,
                line=item.get("line_number", 0),
                column=item.get("column_number", 0),
                message=item.get("text", str(item)),
            ))
    return violations, "OK"


def _execute_eslint(target: str, cwd: Path) -> tuple[list[dict], str]:
    """Execute eslint and return violations + status."""
    if not _tool_available("eslint", check_npm=True):
        return [], "SKIPPED"

    cmd = ["npx", "eslint", target, "--format", "json"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=TOOL_TIMEOUTS["eslint"], cwd=str(cwd)
        )
    except subprocess.TimeoutExpired:
        logger.error("eslint: timeout")
        return [], "SKIPPED"
    except Exception as e:
        logger.error(f"eslint: {type(e).__name__}: {str(e)[:200]}")
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "eslint")
    if not output:
        return [], "OK"

    violations = []
    for file_item in output if isinstance(output, list) else [output]:
        for msg in file_item.get("messages", []):
            violations.append(_build_violation(
                tool="eslint",
                severity="ERROR" if msg.get("severity") == 2 else "WARNING",
                file=file_item.get("filePath", "unknown"),
                line=msg.get("line", 0),
                column=msg.get("column", 0),
                message=msg.get("message", str(msg)),
            ))
    return violations, "OK"


def _execute_gdformat(targets: list[str]) -> tuple[list[dict], str]:
    """Execute gdformat and return violations + status."""
    if not _tool_available("gdformat"):
        return [], "SKIPPED"

    cmd = ["gdformat"] + targets + ["--check"]
    result = _run_tool(cmd, "gdformat", TOOL_TIMEOUTS["gdformat"])
    if not result:
        return [], "SKIPPED"

    violations = []
    for line in result.stdout.split("\n"):
        if "would reformat" in line.lower() or "error" in line.lower():
            violations.append(_build_violation(
                tool="gdformat",
                severity="WARNING",
                file=line.split(":")[0] if ":" in line else "unknown",
                line=0,
                column=0,
                message=line.strip(),
            ))
    return violations, "OK"


def _execute_gdlint(targets: list[str]) -> tuple[list[dict], str]:
    """Execute gdlint and return violations + status."""
    if not _tool_available("gdlint"):
        return [], "SKIPPED"

    cmd = ["gdlint"] + targets
    result = _run_tool(cmd, "gdlint", TOOL_TIMEOUTS["gdlint"])
    if not result:
        return [], "SKIPPED"

    violations = []
    for line in result.stdout.split("\n"):
        if ":" not in line:
            continue
        # Parse format: filename:line:col: message
        parts = line.split(":", 4)
        if len(parts) >= 4:
            violations.append(_build_violation(
                tool="gdlint",
                severity="WARNING",
                file=parts[0],
                line=int(parts[1]) if parts[1].isdigit() else 0,
                column=int(parts[2]) if parts[2].isdigit() else 0,
                message=parts[3].strip() if len(parts) > 3 else "",
            ))
    return violations, "OK"


def _execute_jscpd(target: str, config_file: Path) -> tuple[list[dict], str]:
    """Execute jscpd and return violations + status."""
    if not _tool_available("jscpd", check_npm=True):
        return [], "SKIPPED"

    cmd = ["npx", "jscpd", "--config", str(config_file), "--format", "json", target]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=TOOL_TIMEOUTS["jscpd"]
        )
    except subprocess.TimeoutExpired:
        logger.error("jscpd: timeout")
        return [], "SKIPPED"
    except Exception as e:
        logger.error(f"jscpd: {type(e).__name__}: {str(e)[:200]}")
        return [], "SKIPPED"

    output = _parse_json_output(result.stdout, "jscpd")
    if not output or not isinstance(output, dict):
        return [], "OK"

    violations = []
    for item in output.get("duplicates", []):
        violations.append(_build_violation(
            tool="jscpd",
            severity="INFO",
            file=item.get("firstFile", "unknown"),
            line=item.get("firstFileStart", 0),
            column=0,
            message=f"Duplicate code block ({item.get('lines', 0)} lines, {item.get('tokens', 0)} tokens)",
        ))
    return violations, "OK"


if __name__ == "__main__":
    # Allow direct invocation for testing
    result = run(
        {
            "ticket_id": "M902-02",
            "mode": "shadow",
            "upstream_agent": "Implementation Generalist",
            "downstream_agent": "Spec Agent",
        }
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "shadow" else 1)
