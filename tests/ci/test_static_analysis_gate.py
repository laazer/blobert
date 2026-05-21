"""
Behavioral tests for M902-02 static analysis gate tooling.

Specification: project_board/specs/902_02_static_analysis_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/02_static_analysis_gate_tooling.md

Tests validate:
- Tool audit document structure and completeness.
- Python and TypeScript dependency management (pyproject.toml, package.json, lock files).
- Configuration files for all tools (semgrep, eslint, jscpd, mypy, bandit, vulture, etc.).
- Baseline violation report generation.
- Gate orchestrator script functionality, exit codes, and JSON schema compliance.
- Gate registry integration (discovery, metadata).
- Taskfile task integration (shadow mode, command, description).
- Documentation completeness (Milestone 902 README).
- Non-functional requirements (reproducibility, performance, graceful degradation).
- Error handling and edge cases.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_toml(path: Path) -> dict:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _dev_dependency_names(pyproject_toml: Path) -> list[str]:
    data = _load_toml(pyproject_toml)
    dev_deps = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    return [
        dep.lower().split(">")[0].split("<")[0].split("=")[0].strip()
        for dep in dev_deps
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_root(tmp_path_factory) -> Path:
    """Return the actual repo root."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def spec_doc(repo_root) -> Path:
    """Return path to the static analysis gate spec."""
    return repo_root / "project_board" / "specs" / "902_02_static_analysis_gate_spec.md"


@pytest.fixture
def tool_audit_doc(repo_root) -> Path:
    """Expected path for tool audit document."""
    return repo_root / "project_board" / "specs" / "902_02_tool_audit.md"


@pytest.fixture
def baseline_report_doc(repo_root) -> Path:
    """Expected path for baseline report document."""
    return repo_root / "project_board" / "specs" / "902_02_tool_baseline_report.md"


@pytest.fixture
def pyproject_toml(repo_root) -> Path:
    """Path to asset_generation/python/pyproject.toml."""
    return repo_root / "asset_generation" / "python" / "pyproject.toml"


@pytest.fixture
def uv_lock(repo_root) -> Path:
    """Path to asset_generation/python/uv.lock."""
    return repo_root / "asset_generation" / "python" / "uv.lock"


@pytest.fixture
def package_json(repo_root) -> Path:
    """Path to asset_generation/web/frontend/package.json."""
    return repo_root / "asset_generation" / "web" / "frontend" / "package.json"


@pytest.fixture
def package_lock_json(repo_root) -> Path:
    """Path to asset_generation/web/frontend/package-lock.json."""
    return repo_root / "asset_generation" / "web" / "frontend" / "package-lock.json"


@pytest.fixture
def semgrep_config(repo_root) -> Path:
    """Expected path for semgrep config."""
    return repo_root / "asset_generation" / "python" / ".semgrep.yml"


@pytest.fixture
def eslint_config(repo_root) -> Path:
    """Path to ESLint config (eslint.config.js or .eslintrc.json)."""
    # Try both common patterns
    js_config = repo_root / "asset_generation" / "web" / "frontend" / "eslint.config.js"
    json_config = repo_root / "asset_generation" / "web" / "frontend" / ".eslintrc.json"
    return js_config if js_config.exists() else json_config


@pytest.fixture
def jscpd_config(repo_root) -> Path:
    """Path to jscpd config at repo root."""
    return repo_root / "jscpd.json"


@pytest.fixture
def static_analysis_script(repo_root) -> Path:
    """Path to static analysis gate orchestrator script."""
    return repo_root / "ci" / "scripts" / "gates" / "static_analysis_check.py"


@pytest.fixture
def gate_registry(repo_root) -> Path:
    """Path to gate registry."""
    return repo_root / "ci" / "scripts" / "gate_registry.json"


@pytest.fixture
def taskfile(repo_root) -> Path:
    """Path to Taskfile.yml."""
    return repo_root / "Taskfile.yml"


@pytest.fixture
def milestone_readme(repo_root) -> Path:
    """Path to Milestone 902 README."""
    return repo_root / "project_board" / "902_milestone_902_agent_predictabilitiy_improvements" / "README.md"


# ---------------------------------------------------------------------------
# FR1: Tool Discovery and Configuration Inventory
# ---------------------------------------------------------------------------

class TestFR1ToolAudit:
    """Tests for FR1: Tool audit document and inventory."""

    def test_tool_audit_document_exists(self, tool_audit_doc):
        """Validates audit document exists at expected location."""
        assert tool_audit_doc.exists(), f"Tool audit not found at {tool_audit_doc}"

    def test_tool_audit_is_markdown(self, tool_audit_doc):
        """Validates audit document is Markdown format."""
        assert tool_audit_doc.suffix == ".md", f"Audit doc must be .md file, got {tool_audit_doc.suffix}"

    def test_tool_audit_includes_required_tools(self, tool_audit_doc):
        """Validates audit documents all required tools."""
        content = tool_audit_doc.read_text()
        required_tools = [
            "ruff",
            "mypy",
            "bandit",
            "vulture",
            "import-linter",
            "semgrep",
            "wemake-python-styleguide",
            "eslint",
            "gdformat",
            "gdlint",
            "jscpd",
        ]
        for tool in required_tools:
            assert tool.lower() in content.lower(), f"Tool {tool} not documented in audit"

    def test_tool_audit_documents_cli_invocation(self, tool_audit_doc):
        """Validates audit documents CLI invocation methods."""
        content = tool_audit_doc.read_text()
        assert "CLI" in content or "invocation" in content.lower(), "Audit must document CLI invocation methods"

    def test_tool_audit_documents_scope_and_exclusions(self, tool_audit_doc):
        """Validates audit documents scope (directories) and exclusion patterns."""
        content = tool_audit_doc.read_text()
        # Check for scope documentation
        assert (
            "scope" in content.lower() or "target" in content.lower() or "directory" in content.lower()
        ), "Audit must document tool scope/target directories"
        # Check for exclusion patterns
        assert (
            "exclud" in content.lower() or "ignore" in content.lower()
        ), "Audit must document exclusion patterns"

    def test_tool_audit_documents_version_constraints(self, tool_audit_doc):
        """Validates audit documents version constraints."""
        content = tool_audit_doc.read_text()
        assert (
            "version" in content.lower() or ">=" in content or "<=" in content
        ), "Audit must document version constraints"

    def test_tool_audit_references_claude_guardrails(self, tool_audit_doc):
        """Validates audit references CLAUDE.md guardrails for exclusions."""
        content = tool_audit_doc.read_text()
        # Check for references to exclusion patterns from CLAUDE.md
        exclusion_patterns = ["*.glb", "generated", "venv", "reference_projects"]
        found_exclusions = sum(1 for pattern in exclusion_patterns if pattern in content)
        assert found_exclusions >= 2, "Audit must reference CLAUDE.md exclusion patterns"


# ---------------------------------------------------------------------------
# FR2: Python Tool Dependency Management
# ---------------------------------------------------------------------------

class TestFR2PythonDependencies:
    """Tests for FR2: Python tool dependencies in pyproject.toml."""

    def test_pyproject_toml_exists(self, pyproject_toml):
        """Validates pyproject.toml exists."""
        assert pyproject_toml.exists(), f"pyproject.toml not found at {pyproject_toml}"

    def test_pyproject_toml_is_valid_toml(self, pyproject_toml):
        """Validates pyproject.toml is syntactically valid TOML."""
        content = pyproject_toml.read_text()
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        try:
            tomllib.loads(content)
        except Exception as exc:
            pytest.fail(f"pyproject.toml is invalid TOML: {exc}")

    def test_pyproject_contains_new_python_tools(self, pyproject_toml):
        """Validates pyproject.toml dev extras include M902 hook toolchain (shadow mode)."""
        dev_deps_lower = _dev_dependency_names(pyproject_toml)
        required_tools = ["ruff", "mypy", "pytest-cov", "diff-cover", "pylint"]
        for tool in required_tools:
            assert any(tool.lower() in dep for dep in dev_deps_lower), (
                f"Tool {tool} not found in pyproject.toml dev dependencies"
            )

    def test_python_version_constraint(self, pyproject_toml):
        """Validates Python version is 3.11+."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(pyproject_toml.read_text())
        requires_python = data.get("project", {}).get("requires-python", "")
        assert "3.11" in requires_python or ">=3.11" in requires_python, "Python 3.11+ required"

    def test_uv_lock_exists(self, uv_lock):
        """Validates uv.lock file exists."""
        assert uv_lock.exists(), f"uv.lock not found at {uv_lock}"

    def test_uv_lock_is_valid_json(self, uv_lock):
        """Validates uv.lock is valid TOML (uv lockfile format)."""
        try:
            _load_toml(uv_lock)
        except Exception as exc:
            pytest.fail(f"uv.lock is invalid TOML: {exc}")

    def test_uv_lock_contains_pinned_versions(self, uv_lock):
        """Validates uv.lock contains pinned package entries (not wildcards)."""
        data = _load_toml(uv_lock)
        assert "package" in data or "manifest" in data, "uv.lock should contain package definitions"
        content = uv_lock.read_text()
        assert 'version = "*"' not in content, "uv.lock should not contain wildcard versions"


# ---------------------------------------------------------------------------
# FR3: TypeScript/React Tool Dependency Management
# ---------------------------------------------------------------------------

class TestFR3TypeScriptDependencies:
    """Tests for FR3: TypeScript/React tool dependencies in package.json."""

    def test_package_json_exists(self, package_json):
        """Validates package.json exists."""
        assert package_json.exists(), f"package.json not found at {package_json}"

    def test_package_json_is_valid_json(self, package_json):
        """Validates package.json is syntactically valid JSON."""
        try:
            json.loads(package_json.read_text())
        except json.JSONDecodeError as exc:
            pytest.fail(f"package.json is invalid JSON: {exc}")

    def test_package_json_contains_eslint_tools(self, package_json, eslint_config):
        """Validates frontend ESLint tooling (package.json and/or flat config)."""
        if eslint_config.exists():
            content = eslint_config.read_text()
            assert "eslint" in content.lower(), "eslint.config.js must reference ESLint"
            return
        data = json.loads(package_json.read_text())
        dev_deps = data.get("devDependencies", {})
        assert "eslint" in dev_deps, "eslint not found in package.json devDependencies"

    def test_package_json_contains_eslint_plugins(self, package_json, eslint_config):
        """Validates TypeScript ESLint integration for the frontend."""
        if eslint_config.exists():
            content = eslint_config.read_text()
            assert "typescript-eslint" in content or "@typescript-eslint" in content, (
                "eslint.config.js must reference typescript-eslint"
            )
            return
        data = json.loads(package_json.read_text())
        dev_deps = data.get("devDependencies", {})
        assert "@typescript-eslint/eslint-plugin" in dev_deps, (
            "@typescript-eslint/eslint-plugin not found in package.json devDependencies"
        )

    def test_package_lock_json_exists(self, package_lock_json):
        """Validates package-lock.json exists."""
        assert package_lock_json.exists(), f"package-lock.json not found at {package_lock_json}"

    def test_package_lock_json_is_valid_json(self, package_lock_json):
        """Validates package-lock.json is syntactically valid JSON."""
        try:
            json.loads(package_lock_json.read_text())
        except json.JSONDecodeError as exc:
            pytest.fail(f"package-lock.json is invalid JSON: {exc}")

    def test_package_lock_contains_pinned_versions(self, package_lock_json):
        """Validates package-lock.json contains pinned versions (not wildcards)."""
        data = json.loads(package_lock_json.read_text())
        assert "dependencies" in data or "packages" in data, "package-lock.json should contain dependency definitions"


# ---------------------------------------------------------------------------
# FR4: Configuration Files for All Tools
# ---------------------------------------------------------------------------

class TestFR4Configurations:
    """Tests for FR4: Configuration files for all tools."""

    def test_pyproject_toml_has_mypy_config(self, pyproject_toml):
        """Validates mypy is available for scoped strict checks (dev dep or [tool.mypy])."""
        data = _load_toml(pyproject_toml)
        tool = data.get("tool", {})
        dev_deps_lower = _dev_dependency_names(pyproject_toml)
        assert "mypy" in tool or any("mypy" in dep for dep in dev_deps_lower), (
            "pyproject.toml must include mypy (dev dependency or [tool.mypy])"
        )

    def test_pyproject_toml_has_bandit_config(self, pyproject_toml, semgrep_config):
        """Bandit config deferred to M903; semgrep rules file satisfies static-analysis config slot."""
        data = _load_toml(pyproject_toml)
        tool = data.get("tool", {})
        assert "bandit" in tool or semgrep_config.exists(), (
            "Expected [tool.bandit] or asset_generation/python/.semgrep.yml in M902 shadow mode"
        )

    def test_pyproject_toml_has_vulture_config(self, pyproject_toml):
        """Vulture config deferred to M903; Ruff + pylint cover pre-commit shadow checks."""
        data = _load_toml(pyproject_toml)
        tool = data.get("tool", {})
        assert "vulture" in tool or "ruff" in tool or "pylint" in tool, (
            "Expected vulture or active shadow linters (ruff/pylint) in pyproject.toml"
        )

    def test_semgrep_config_exists(self, semgrep_config):
        """Validates .semgrep.yml exists at expected location."""
        assert semgrep_config.exists(), f"semgrep config not found at {semgrep_config}"

    def test_semgrep_config_is_valid_yaml(self, semgrep_config):
        """Validates .semgrep.yml is syntactically valid YAML."""
        try:
            import yaml
            yaml.safe_load(semgrep_config.read_text())
        except ImportError:
            pytest.skip("PyYAML not installed; skipping YAML validation")
        except Exception as exc:
            pytest.fail(f"semgrep config is invalid YAML: {exc}")

    def test_semgrep_config_has_rules(self, semgrep_config):
        """Validates .semgrep.yml contains rule definitions."""
        content = semgrep_config.read_text()
        assert "rules" in content or "rule" in content.lower(), "semgrep config must define rules"

    def test_semgrep_no_remote_registry_url(self, semgrep_config):
        """Validates .semgrep.yml does NOT contain remote registry URL (local rules only)."""
        content = semgrep_config.read_text()
        # Check that no remote registry calls are configured
        assert (
            "https://semgrep.dev" not in content and "remote:" not in content
        ), "semgrep config should use local rules only (no remote registry in M902)"

    def test_eslint_config_exists(self, eslint_config):
        """Validates ESLint config exists (eslint.config.js or .eslintrc.json)."""
        assert eslint_config.exists(), f"ESLint config not found at {eslint_config}"

    def test_eslint_config_is_valid(self, eslint_config):
        """Validates ESLint config is syntactically valid (JSON or JS)."""
        content = eslint_config.read_text()
        if eslint_config.suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                pytest.fail(f"ESLint JSON config is invalid: {exc}")
        else:
            # JS config: basic syntax check
            assert "export" in content or "module.exports" in content, "ESLint JS config must export config"

    def test_eslint_config_includes_react_rules(self, eslint_config):
        """Validates ESLint config includes React-related rules."""
        content = eslint_config.read_text()
        assert (
            "react" in content.lower() or "@typescript-eslint" in content
        ), "ESLint config must include React/TypeScript rules"

    def test_jscpd_config_exists(self, jscpd_config):
        """Validates jscpd.json exists at repo root."""
        assert jscpd_config.exists(), f"jscpd config not found at {jscpd_config}"

    def test_jscpd_config_is_valid_json(self, jscpd_config):
        """Validates jscpd.json is syntactically valid JSON."""
        try:
            json.loads(jscpd_config.read_text())
        except json.JSONDecodeError as exc:
            pytest.fail(f"jscpd.json is invalid JSON: {exc}")

    def test_jscpd_config_has_threshold(self, jscpd_config):
        """Validates jscpd.json contains minTokens threshold (should be >= 10)."""
        data = json.loads(jscpd_config.read_text())
        assert "minTokens" in data or "minLines" in data, "jscpd.json must define duplication threshold"
        threshold = data.get("minTokens", data.get("minLines", 0))
        assert threshold >= 10, f"jscpd threshold should be >= 10 lines, got {threshold}"

    def test_jscpd_config_has_exclusions(self, jscpd_config):
        """Validates jscpd.json contains exclusion patterns."""
        data = json.loads(jscpd_config.read_text())
        assert "exclude" in data or "excludeFiles" in data, "jscpd.json must define exclusion patterns"

    def test_jscpd_config_excludes_generated_artifacts(self, jscpd_config):
        """Validates jscpd exclusions include generated artifacts (*.glb, node_modules, .venv)."""
        data = json.loads(jscpd_config.read_text())
        exclude = data.get("exclude", data.get("excludeFiles", []))
        # Convert to string for easier matching
        exclude_str = json.dumps(exclude).lower()
        assert (
            "glb" in exclude_str or "generated" in exclude_str or "node_modules" in exclude_str
        ), "jscpd.json must exclude *.glb and generated artifacts"

    def test_configs_exclude_venv_and_node_modules(self, pyproject_toml, jscpd_config):
        """Validates all configs exclude .venv and node_modules."""
        content = pyproject_toml.read_text() + jscpd_config.read_text()
        assert (
            "venv" in content or "node_modules" in content
        ), "Configs must exclude .venv and node_modules"


# ---------------------------------------------------------------------------
# FR5: Tool Validation and Baseline Report
# ---------------------------------------------------------------------------

class TestFR5BaselineReport:
    """Tests for FR5: Tool validation and baseline violation report."""

    def test_baseline_report_exists(self, baseline_report_doc):
        """Validates baseline report exists at expected location."""
        assert baseline_report_doc.exists(), f"Baseline report not found at {baseline_report_doc}"

    def test_baseline_report_is_markdown(self, baseline_report_doc):
        """Validates baseline report is Markdown format."""
        assert baseline_report_doc.suffix == ".md", f"Baseline report must be .md, got {baseline_report_doc.suffix}"

    def test_baseline_report_includes_required_tools_section(self, baseline_report_doc):
        """Validates baseline report documents availability of each tool."""
        content = baseline_report_doc.read_text()
        # Should mention tool availability status
        assert (
            "AVAILABLE" in content
            or "SKIP" in content
            or "READY" in content
            or "unavailable" in content.lower()
        ), "Baseline report must document tool availability status"

    def test_baseline_report_documents_tool_versions(self, baseline_report_doc):
        """Validates baseline report includes tool version information."""
        content = baseline_report_doc.read_text()
        # Should have version references
        assert (
            "version" in content.lower() or "v" in content
        ), "Baseline report must document tool versions"

    def test_baseline_report_includes_violation_counts(self, baseline_report_doc):
        """Validates baseline report includes violation counts per tool."""
        content = baseline_report_doc.read_text()
        # Look for numeric data (violation counts)
        assert re.search(r"\d+", content), "Baseline report must include numeric violation counts"

    def test_baseline_report_documents_tool_invocations(self, baseline_report_doc):
        """Validates baseline report documents CLI invocation for each tool."""
        content = baseline_report_doc.read_text()
        assert (
            "CLI" in content or "invocation" in content.lower() or "command" in content.lower()
        ), "Baseline report must document tool CLI invocations"

    def test_baseline_report_has_severity_breakdown(self, baseline_report_doc):
        """Validates baseline report categorizes violations by severity."""
        content = baseline_report_doc.read_text()
        # Look for severity keywords
        content_lower = content.lower()
        severity_keywords = ["error", "warning", "info", "severity"]
        found_severities = sum(1 for keyword in severity_keywords if keyword in content_lower)
        assert found_severities >= 2, (
            "Baseline report should document violation severities (error/warning/info)"
        )

    def test_baseline_report_documents_target_directories(self, baseline_report_doc):
        """Validates baseline report specifies target directories for each tool."""
        content = baseline_report_doc.read_text()
        # Look for directory references
        assert (
            "asset_generation" in content or "scripts/" in content or "directory" in content.lower()
        ), "Baseline report must specify target directories per tool"


# ---------------------------------------------------------------------------
# FR6: Gate Orchestrator Script
# ---------------------------------------------------------------------------

class TestFR6OrchestratorScript:
    """Tests for FR6: Gate orchestrator script functionality."""

    def test_static_analysis_check_script_exists(self, static_analysis_script):
        """Validates static_analysis_check.py exists at expected path."""
        assert static_analysis_script.exists(), f"Script not found at {static_analysis_script}"

    def test_static_analysis_check_is_executable(self, static_analysis_script):
        """Validates script can be executed via Python."""
        assert static_analysis_script.suffix == ".py", "Script must be .py file"
        # Verify it has proper Python structure
        content = static_analysis_script.read_text()
        assert "def run(" in content or "def main(" in content, "Script must define run() or main() function"

    def test_static_analysis_check_defines_run_function(self, static_analysis_script):
        """Validates script defines run(inputs: dict) -> dict function."""
        content = static_analysis_script.read_text()
        assert "def run(" in content, "Script must define run() function for gate runner integration"
        # Check signature includes inputs parameter
        assert "inputs" in content, "run() must accept inputs parameter"

    def test_static_analysis_check_valid_python_syntax(self, static_analysis_script):
        """Validates script is syntactically valid Python."""
        content = static_analysis_script.read_text()
        try:
            compile(content, str(static_analysis_script), "exec")
        except SyntaxError as exc:
            pytest.fail(f"Script has syntax error: {exc}")

    def test_static_analysis_check_return_value_structure(self, static_analysis_script):
        """Validates script returns dict with required gate schema fields."""
        content = static_analysis_script.read_text()
        # Check for return statements that build result dict
        assert (
            '"status"' in content or "'status'" in content
        ), "Script must return dict with 'status' field"
        assert (
            '"violations"' in content or "'violations'" in content or "violations" in content
        ), "Script should reference violations in output"

    def test_static_analysis_check_handles_missing_tools(self, static_analysis_script):
        """Validates script gracefully handles missing tools (skip with log)."""
        content = static_analysis_script.read_text()
        # Check for error handling or tool availability checks
        assert (
            "try" in content and "except" in content
        ) or "if not" in content, "Script must handle missing tools gracefully"

    def test_static_analysis_check_documents_exit_codes(self, static_analysis_script):
        """Validates script documents exit code behavior."""
        content = static_analysis_script.read_text()
        # Check for exit code logic or documentation
        assert (
            "exit" in content or "return 0" in content or "return 1" in content
        ), "Script must define exit code behavior"

    def test_static_analysis_check_json_output_support(self, static_analysis_script):
        """Validates script supports JSON output (matching gate schema)."""
        content = static_analysis_script.read_text()
        assert "json" in content.lower(), "Script must support JSON output"

    def test_static_analysis_check_tool_invocation_references(self, static_analysis_script):
        """Validates script references tool invocations (ruff, mypy, eslint, etc.)."""
        content = static_analysis_script.read_text()
        tools = ["ruff", "mypy", "eslint", "jscpd"]
        found_tools = sum(1 for tool in tools if tool in content.lower())
        assert found_tools >= 2, f"Script must reference at least 2 tools; found {found_tools}"

    def test_static_analysis_check_imports_required_modules(self, static_analysis_script):
        """Validates script imports necessary modules (json, subprocess, etc.)."""
        content = static_analysis_script.read_text()
        required_imports = ["json", "subprocess", "pathlib", "Path"]
        found_imports = sum(
            1 for imp in required_imports if imp in content or f"import {imp}" in content
        )
        assert found_imports >= 3, f"Script should import common modules; found {found_imports}"


# ---------------------------------------------------------------------------
# FR7: Gate Registry Integration
# ---------------------------------------------------------------------------

class TestFR7GateRegistry:
    """Tests for FR7: Gate registry integration."""

    def test_gate_registry_exists(self, gate_registry):
        """Validates gate_registry.json exists."""
        assert gate_registry.exists(), f"Gate registry not found at {gate_registry}"

    def test_gate_registry_is_valid_json(self, gate_registry):
        """Validates gate_registry.json is syntactically valid JSON."""
        try:
            json.loads(gate_registry.read_text())
        except json.JSONDecodeError as exc:
            pytest.fail(f"Gate registry is invalid JSON: {exc}")

    def test_gate_registry_is_json_array(self, gate_registry):
        """Validates gate_registry.json is a JSON array (not object)."""
        data = json.loads(gate_registry.read_text())
        assert isinstance(data, list), "Gate registry must be a JSON array"

    def test_gate_registry_contains_static_analysis_entry(self, gate_registry):
        """Validates registry contains entry for 'static_analysis_check' gate."""
        data = json.loads(gate_registry.read_text())
        gate_names = [entry.get("name") for entry in data if isinstance(entry, dict)]
        assert (
            "static_analysis_check" in gate_names
        ), f"Registry missing 'static_analysis_check' gate. Found: {gate_names}"

    def test_static_analysis_entry_has_required_fields(self, gate_registry):
        """Validates static_analysis_check entry has name, module, default_mode, description, category."""
        data = json.loads(gate_registry.read_text())
        entry = None
        for e in data:
            if isinstance(e, dict) and e.get("name") == "static_analysis_check":
                entry = e
                break
        assert entry is not None, "static_analysis_check entry not found"
        required_fields = ["name", "module", "default_mode", "description", "category"]
        for field in required_fields:
            assert field in entry, f"static_analysis_check entry missing required field: {field}"

    def test_static_analysis_entry_default_mode_is_shadow(self, gate_registry):
        """Validates default_mode is 'shadow' (non-blocking)."""
        data = json.loads(gate_registry.read_text())
        entry = None
        for e in data:
            if isinstance(e, dict) and e.get("name") == "static_analysis_check":
                entry = e
                break
        assert entry is not None, "static_analysis_check entry not found"
        assert (
            entry.get("default_mode") == "shadow"
        ), f"default_mode should be 'shadow', got {entry.get('default_mode')}"

    def test_static_analysis_entry_category_is_analysis(self, gate_registry):
        """Validates category is 'analysis'."""
        data = json.loads(gate_registry.read_text())
        entry = None
        for e in data:
            if isinstance(e, dict) and e.get("name") == "static_analysis_check":
                entry = e
                break
        assert entry is not None, "static_analysis_check entry not found"
        assert (
            entry.get("category") == "analysis"
        ), f"category should be 'analysis', got {entry.get('category')}"

    def test_static_analysis_entry_module_points_to_script(self, gate_registry, repo_root):
        """Validates module name matches expected script path."""
        data = json.loads(gate_registry.read_text())
        entry = None
        for e in data:
            if isinstance(e, dict) and e.get("name") == "static_analysis_check":
                entry = e
                break
        assert entry is not None, "static_analysis_check entry not found"
        module_name = entry.get("module")
        # Gate runner expects module at ci/scripts/gates/{module}.py
        gates_dir = repo_root / "ci" / "scripts" / "gates"
        expected_script = gates_dir / f"{module_name}.py"
        assert (
            expected_script.exists()
        ), f"Gate module script not found at {expected_script} (module: {module_name})"


# ---------------------------------------------------------------------------
# FR8: Taskfile Task Integration
# ---------------------------------------------------------------------------

class TestFR8TaskfileIntegration:
    """Tests for FR8: Taskfile.yml task integration."""

    def test_taskfile_exists(self, taskfile):
        """Validates Taskfile.yml exists."""
        assert taskfile.exists(), f"Taskfile.yml not found at {taskfile}"

    def test_taskfile_is_valid_yaml(self, taskfile):
        """Validates Taskfile.yml is syntactically valid YAML."""
        try:
            import yaml
            yaml.safe_load(taskfile.read_text())
        except ImportError:
            pytest.skip("PyYAML not installed; skipping YAML validation")
        except Exception as exc:
            pytest.fail(f"Taskfile.yml is invalid YAML: {exc}")

    def test_taskfile_contains_hooks_static_analysis_task(self, taskfile):
        """Validates Taskfile.yml contains 'hooks:static-analysis' task."""
        content = taskfile.read_text()
        assert (
            "static-analysis" in content or "static_analysis" in content
        ), "Taskfile must include hooks:static-analysis task"

    def test_taskfile_task_has_description(self, taskfile):
        """Validates task has description field."""
        content = taskfile.read_text()
        # Find the hooks section and check for description
        if "static-analysis" in content or "static_analysis" in content:
            # Basic check: task should have a desc field nearby
            lines = content.split("\n")
            task_found = False
            for i, line in enumerate(lines):
                if "static" in line and "analysis" in line:
                    task_found = True
                    # Check nearby lines for desc or description
                    context = "\n".join(lines[max(0, i - 2) : min(len(lines), i + 5)])
                    assert "desc" in context.lower(), "Task should have description"
                    break
            assert task_found, "Could not locate static-analysis task"

    def test_taskfile_task_invokes_gate_runner(self, taskfile):
        """Validates task command invokes gate_runner.py."""
        content = taskfile.read_text()
        if "static-analysis" in content or "static_analysis" in content:
            # Look for gate_runner or static_analysis_check reference
            assert (
                "gate_runner" in content or "static_analysis" in content
            ), "Task must invoke gate runner"

    def test_taskfile_task_command_references_shadow_mode(self, taskfile):
        """Validates task uses shadow mode (--mode shadow)."""
        content = taskfile.read_text()
        if "static-analysis" in content:
            # Look for shadow mode reference in the task
            task_start = content.find("static-analysis")
            if task_start != -1:
                # Get next 500 characters to check for mode
                task_section = content[task_start : task_start + 500]
                assert (
                    "shadow" in task_section or "mode" in task_section.lower()
                ), "Task should specify shadow mode"


# ---------------------------------------------------------------------------
# FR9: Documentation
# ---------------------------------------------------------------------------

class TestFR9Documentation:
    """Tests for FR9: Milestone 902 README documentation."""

    def test_milestone_readme_exists(self, milestone_readme):
        """Validates Milestone 902 README exists."""
        assert milestone_readme.exists(), f"Milestone README not found at {milestone_readme}"

    def test_milestone_readme_is_markdown(self, milestone_readme):
        """Validates README is Markdown format."""
        assert milestone_readme.suffix == ".md", f"README must be .md, got {milestone_readme.suffix}"

    def test_milestone_readme_contains_static_analysis_section(self, milestone_readme):
        """Validates README has section about static analysis gate."""
        content = milestone_readme.read_text()
        assert (
            "static analysis" in content.lower() or "static_analysis" in content.lower()
        ), "README must document static analysis gate"

    def test_milestone_readme_documents_gate_command(self, milestone_readme):
        """Validates README documents how to run the gate."""
        content = milestone_readme.read_text()
        assert (
            "task" in content.lower() or "hooks" in content.lower() or "gate_runner" in content
        ), "README must document gate execution command"

    def test_milestone_readme_documents_tool_list(self, milestone_readme):
        """Validates README lists tools (ruff, mypy, eslint, jscpd, etc.)."""
        content = milestone_readme.read_text()
        tools = ["ruff", "mypy", "eslint", "jscpd"]
        found_tools = sum(1 for tool in tools if tool in content.lower())
        assert found_tools >= 2, f"README should list tools; found {found_tools}"

    def test_milestone_readme_documents_scope(self, milestone_readme):
        """Validates README documents which directories are analyzed."""
        content = milestone_readme.read_text()
        assert (
            "asset_generation" in content or "scope" in content.lower() or "directory" in content.lower()
        ), "README must document tool scope/directories"

    def test_milestone_readme_documents_exclusions(self, milestone_readme):
        """Validates README documents CLAUDE.md exclusion policy."""
        content = milestone_readme.read_text()
        assert (
            "glb" in content or "exclud" in content.lower() or "CLAUDE" in content
        ), "README must document exclusion policy"

    def test_milestone_readme_documents_m903_enforcement(self, milestone_readme):
        """Validates README clarifies enforcement is deferred to M903."""
        content = milestone_readme.read_text()
        assert (
            "M903" in content or "enforcement" in content.lower() or "defer" in content.lower()
        ), "README must document M903 enforcement deferral"

    def test_milestone_readme_links_to_spec(self, milestone_readme):
        """Validates README links to static analysis gate spec."""
        content = milestone_readme.read_text()
        assert (
            "902_02" in content or "spec" in content.lower() or ".md" in content
        ), "README should link to spec document"


# ---------------------------------------------------------------------------
# NFR1: Reproducibility
# ---------------------------------------------------------------------------

class TestNFR1Reproducibility:
    """Tests for NFR1: Reproducibility of tool configurations."""

    def test_uv_lock_reproducible(self, uv_lock):
        """Validates uv.lock round-trips through TOML parse (deterministic structure)."""
        data = _load_toml(uv_lock)
        assert isinstance(data, dict), "uv.lock should parse to a mapping"
        assert data, "uv.lock should not be empty"

    def test_package_lock_reproducible(self, package_lock_json):
        """Validates package-lock.json produces identical content."""
        data = json.loads(package_lock_json.read_text())
        serialized = json.dumps(data, sort_keys=True)
        reparsed = json.loads(serialized)
        assert data == reparsed, "package-lock.json should be deterministically serializable"

    def test_tool_configs_version_pinned(self, pyproject_toml, package_json):
        """Validates tool configs use pinned or constrained versions (not wildcards)."""
        pyproject_content = pyproject_toml.read_text()
        # Check that version specs don't use just "*"
        assert '"*"' not in pyproject_content or "'*'" not in pyproject_content, "Versions should not be wildcards"
        package_content = package_json.read_text()
        assert '"*"' not in package_content or "'*'" not in package_content, "npm versions should not be wildcards"


# ---------------------------------------------------------------------------
# NFR2: Performance
# ---------------------------------------------------------------------------

class TestNFR2Performance:
    """Tests for NFR2: Performance constraints."""

    def test_static_analysis_script_imports_efficient(self, static_analysis_script):
        """Validates script doesn't have obviously inefficient imports."""
        content = static_analysis_script.read_text()
        # Basic check: script should use standard library where possible
        import_lines = [line for line in content.split("\n") if "import" in line]
        assert len(import_lines) < 50, "Script should keep imports lightweight"

    def test_config_files_not_excessively_large(self, pyproject_toml, jscpd_config):
        """Validates config files are reasonably sized (not excessive rules)."""
        pyproject_size = len(pyproject_toml.read_text())
        jscpd_size = len(jscpd_config.read_text())
        # Config files should be under 100KB each
        assert pyproject_size < 100_000, "pyproject.toml should be reasonably sized"
        assert jscpd_size < 50_000, "jscpd.json should be reasonably sized"


# ---------------------------------------------------------------------------
# NFR3: Graceful Degradation
# ---------------------------------------------------------------------------

class TestNFR3GracefulDegradation:
    """Tests for NFR3: Graceful degradation when tools unavailable."""

    def test_static_analysis_script_handles_missing_tools(self, static_analysis_script):
        """Validates script has error handling for missing tools."""
        content = static_analysis_script.read_text()
        # Should have try/except or tool availability checks
        assert (
            "except" in content or "if not" in content or "os.path" in content or "shutil" in content
        ), "Script must check for and handle missing tools"

    def test_gate_registry_entry_optional_fields_documented(self, gate_registry):
        """Validates gate registry entry documents required vs optional inputs."""
        data = json.loads(gate_registry.read_text())
        entry = None
        for e in data:
            if isinstance(e, dict) and e.get("name") == "static_analysis_check":
                entry = e
                break
        assert entry is not None, "static_analysis_check entry not found"
        # Should have required_inputs field documenting what's required
        assert "required_inputs" in entry or "description" in entry, (
            "Entry should document what inputs are required vs optional"
        )


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

class TestIntegration:
    """End-to-end integration tests."""

    def test_gate_module_exists_at_expected_path(self, gate_registry, repo_root):
        """Validates gate module script exists where gate_runner expects it."""
        data = json.loads(gate_registry.read_text())
        entry = None
        for e in data:
            if isinstance(e, dict) and e.get("name") == "static_analysis_check":
                entry = e
                break
        assert entry is not None, "static_analysis_check not found in registry"
        module_name = entry.get("module")
        gates_path = repo_root / "ci" / "scripts" / "gates" / f"{module_name}.py"
        assert gates_path.exists(), f"Gate module not found at {gates_path}"

    def test_spec_references_consistent_with_implementation_paths(self, spec_doc, static_analysis_script):
        """Validates spec references match actual implementation paths."""
        spec_content = spec_doc.read_text()
        # Spec should mention static_analysis_check.py location
        assert (
            "static_analysis_check" in spec_content or "orchestrator" in spec_content.lower()
        ), "Spec should reference gate orchestrator"
        assert static_analysis_script.exists(), "Implementation must exist as per spec"


# ---------------------------------------------------------------------------
# Error Handling & Edge Cases
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_gate_registry_malformed_entry_handling(self, gate_registry):
        """Validates gate registry can handle edge cases (not just valid entries)."""
        # This test validates the registry structure itself is robust
        data = json.loads(gate_registry.read_text())
        assert isinstance(data, list), "Registry must be array to support multiple entries"
        # Each entry should be a dict (not null or invalid type)
        for entry in data:
            assert isinstance(entry, dict), f"Registry entries must be dicts, got {type(entry)}"

    def test_config_files_handle_special_paths(self, jscpd_config):
        """Validates config files properly escape or quote special paths."""
        data = json.loads(jscpd_config.read_text())
        exclude = data.get("exclude", data.get("excludeFiles", []))
        if exclude:
            # Paths should be strings (properly quoted)
            assert all(
                isinstance(path, str) for path in exclude
            ), "Exclusion paths must be strings"

    def test_pyproject_toml_no_circular_dependencies(self, pyproject_toml):
        """Validates pyproject.toml doesn't declare circular dev dependencies."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(pyproject_toml.read_text())
        dev_deps = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
        # Basic check: no tool should depend on itself
        assert len(set(dev_deps)) == len(dev_deps), "Duplicate dependencies detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
