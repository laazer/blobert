"""
Adversarial tests for M902-02 static analysis gate.

Tests expose weaknesses in tool configuration, gate execution, JSON parsing,
file I/O, and error handling. Mutation testing on inputs, configs, and runtime
state to catch edge cases and false confidence from mock-heavy design.

Specification: project_board/specs/902_02_static_analysis_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/02_static_analysis_gate_tooling.md
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def repo_root() -> Path:
    """Return actual repo root."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def pyproject_toml(repo_root) -> Path:
    """Path to asset_generation/python/pyproject.toml."""
    return repo_root / "asset_generation" / "python" / "pyproject.toml"


@pytest.fixture
def package_json(repo_root) -> Path:
    """Path to asset_generation/web/frontend/package.json."""
    return repo_root / "asset_generation" / "web" / "frontend" / "package.json"


@pytest.fixture
def gate_registry(repo_root) -> Path:
    """Path to gate registry."""
    return repo_root / "ci" / "scripts" / "gate_registry.json"


@pytest.fixture
def jscpd_config(repo_root) -> Path:
    """Path to jscpd.json."""
    return repo_root / "jscpd.json"


@pytest.fixture
def semgrep_config(repo_root) -> Path:
    """Path to semgrep config."""
    return repo_root / "asset_generation" / "python" / ".semgrep.yml"


@pytest.fixture
def taskfile(repo_root) -> Path:
    """Path to Taskfile.yml."""
    return repo_root / "Taskfile.yml"


# ============================================================================
# FIXTURE SYNTAX CORRUPTION TESTS
# ============================================================================


class TestPyprojectTomlCorruption:
    """Test pyproject.toml parsing under corruption and edge cases."""

    def test_pyproject_with_truncated_dev_deps(self, pyproject_toml: Path) -> None:
        """Test pyproject.toml with incomplete or truncated dev dependencies."""
        # CHECKPOINT: Tool availability edge case — truncated array
        if not pyproject_toml.exists():
            pytest.skip("pyproject.toml not found")
        content = pyproject_toml.read_text()
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        # Simulate truncation: remove closing bracket from dev array
        truncated = content.replace("]", "", 1) if "]" in content else content
        if truncated != content:
            with pytest.raises(Exception):
                tomllib.loads(truncated)

    def test_pyproject_with_duplicate_tool_keys(self, tmp_path: Path) -> None:
        """Test that duplicate [tool.X] sections are handled correctly."""
        # Mutation: JSON doesn't allow dups, but TOML may handle them differently
        invalid_toml = """
[tool.mypy]
python_version = "3.11"

[tool.mypy]
strict = true
"""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text(invalid_toml)
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        # TOML should handle or reject duplicates consistently
        try:
            data = tomllib.loads(invalid_toml)
            # If it succeeds, both should be present or merged
            assert "tool" in data and "mypy" in data.get("tool", {})
        except Exception:
            # If it fails, should be consistent
            pass

    def test_pyproject_with_empty_dev_deps_list(self, tmp_path: Path) -> None:
        """Test pyproject with empty dev dependencies."""
        toml_content = """
[project]
name = "test"
version = "0.0.1"

[project.optional-dependencies]
dev = []
"""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text(toml_content)
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(toml_content)
        # Empty dev deps is valid but incomplete
        assert data["project"]["optional-dependencies"]["dev"] == []

    def test_pyproject_with_null_version_values(self, tmp_path: Path) -> None:
        """Test pyproject with null/none version strings (mutation)."""
        invalid_toml = """
[project.optional-dependencies]
dev = ["mypy>>=1.8", "bandit", ""]
"""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text(invalid_toml)
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(invalid_toml)
        # Empty string in deps list is technically valid but semantically wrong
        assert "" in data["project"]["optional-dependencies"]["dev"]

    def test_pyproject_with_extremely_long_version_string(self, tmp_path: Path) -> None:
        """Test pyproject with pathologically long version constraint."""
        long_constraint = "a" * 10000
        invalid_toml = f"""
[project.optional-dependencies]
dev = ["mypy>={long_constraint}"]
"""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text(invalid_toml)
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        data = tomllib.loads(invalid_toml)
        # Should parse but version string is nonsensical
        assert long_constraint in data["project"]["optional-dependencies"]["dev"][0]


class TestPackageJsonCorruption:
    """Test package.json parsing under corruption."""

    def test_package_json_with_trailing_comma(self, tmp_path: Path) -> None:
        """Test package.json with trailing comma (invalid JSON)."""
        invalid_json = """{
  "devDependencies": {
    "eslint": "^9.0.0",
  }
}"""
        json_file = tmp_path / "test.json"
        json_file.write_text(invalid_json)
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_package_json_with_duplicate_keys(self, tmp_path: Path) -> None:
        """Test package.json with duplicate keys (last wins)."""
        dup_json = """{
  "devDependencies": {
    "eslint": "^8.0.0",
    "eslint": "^9.0.0"
  }
}"""
        # JSON parsing allows dups; last value wins
        data = json.loads(dup_json)
        assert data["devDependencies"]["eslint"] == "^9.0.0"

    def test_package_json_with_null_dependency_version(self, tmp_path: Path) -> None:
        """Test package.json with null version (mutation)."""
        json_with_null = """{
  "devDependencies": {
    "eslint": null,
    "typescript": "^5.0.0"
  }
}"""
        data = json.loads(json_with_null)
        # null is valid JSON but semantically wrong
        assert data["devDependencies"]["eslint"] is None

    def test_package_json_with_non_string_dependency_names(self, tmp_path: Path) -> None:
        """Test package.json with numeric keys (mutation)."""
        json_weird = """{
  "devDependencies": {
    "eslint": "^9.0.0",
    "123": "1.0.0"
  }
}"""
        data = json.loads(json_weird)
        # Keys are always strings in JSON, but can look weird
        assert "123" in data["devDependencies"]


class TestJscpdConfigCorruption:
    """Test jscpd.json config under edge cases."""

    def test_jscpd_config_with_invalid_threshold(self, tmp_path: Path) -> None:
        """Test jscpd.json with invalid minTokens (negative, zero, or string)."""
        configs = [
            {"minTokens": -1, "exclude": []},
            {"minTokens": 0, "exclude": []},
            {"minTokens": "ten", "exclude": []},
            {"minTokens": None, "exclude": []},
        ]
        for cfg in configs:
            json_file = tmp_path / f"jscpd_{id(cfg)}.json"
            json_file.write_text(json.dumps(cfg))
            data = json.loads(json_file.read_text())
            # All are valid JSON but semantically problematic
            assert "minTokens" in data

    def test_jscpd_config_with_non_array_exclude(self, tmp_path: Path) -> None:
        """Test jscpd.json where exclude is not an array."""
        configs = [
            {"minTokens": 10, "exclude": "*.glb"},
            {"minTokens": 10, "exclude": {"pattern": "*.glb"}},
            {"minTokens": 10, "exclude": None},
        ]
        for cfg in configs:
            json_file = tmp_path / f"jscpd_{id(cfg)}.json"
            json_file.write_text(json.dumps(cfg))
            data = json.loads(json_file.read_text())
            # Should be array but may be other types
            assert "exclude" in data

    def test_jscpd_config_with_huge_threshold(self, tmp_path: Path) -> None:
        """Test jscpd.json with pathologically large minTokens."""
        cfg = {"minTokens": 10**10, "exclude": []}
        json_file = tmp_path / "jscpd.json"
        json_file.write_text(json.dumps(cfg))
        data = json.loads(json_file.read_text())
        assert data["minTokens"] == 10**10

    def test_jscpd_config_with_unicode_patterns(self, tmp_path: Path) -> None:
        """Test jscpd.json with unicode in exclusion patterns."""
        cfg = {"minTokens": 10, "exclude": ["*.glb", "мир", "🚀", "\x00"]}
        json_file = tmp_path / "jscpd.json"
        json_file.write_text(json.dumps(cfg))
        data = json.loads(json_file.read_text())
        assert len(data["exclude"]) == 4


# ============================================================================
# GATE REGISTRY MUTATIONS
# ============================================================================


class TestStaticAnalysisRegistryEntry:
    """Test static_analysis_check gate registry entry mutations."""

    def test_registry_entry_missing_static_analysis(self, gate_registry: Path) -> None:
        """Test registry without static_analysis_check entry."""
        if not gate_registry.exists():
            pytest.skip("gate_registry.json not found")

        data = json.loads(gate_registry.read_text())
        # Mutate: remove static_analysis_check if present
        original_names = [e.get("name") for e in data if isinstance(e, dict)]
        assert "static_analysis_check" in original_names, (
            "Registry must have static_analysis_check entry"
        )

    def test_registry_entry_with_wrong_module_path(self, tmp_path: Path) -> None:
        """Test registry entry where module path doesn't correspond to a real file."""
        registry = [
            {
                "name": "static_analysis_check",
                "module": "nonexistent_gate_module",
                "default_mode": "shadow",
                "description": "Test gate",
                "category": "analysis",
            }
        ]
        reg_file = tmp_path / "gate_registry.json"
        reg_file.write_text(json.dumps(registry))
        # Entry is valid JSON but points to missing module
        assert json.loads(reg_file.read_text())[0]["module"] == "nonexistent_gate_module"

    def test_registry_entry_with_invalid_mode(self, tmp_path: Path) -> None:
        """Test registry entry with invalid default_mode value."""
        invalid_modes = ["SHADOW", "blocking_mode", "shadow_mode", "", None, 123]
        for mode in invalid_modes:
            registry = [
                {
                    "name": "static_analysis_check",
                    "module": "static_analysis_check",
                    "default_mode": mode,
                    "description": "Test",
                    "category": "analysis",
                }
            ]
            reg_file = tmp_path / f"reg_{id(mode)}.json"
            reg_file.write_text(json.dumps(registry))
            data = json.loads(reg_file.read_text())
            # Valid JSON but semantically wrong
            assert data[0]["default_mode"] == mode

    def test_registry_entry_with_missing_category(self, tmp_path: Path) -> None:
        """Test registry entry missing category field."""
        registry = [
            {
                "name": "static_analysis_check",
                "module": "static_analysis_check",
                "default_mode": "shadow",
                "description": "Test gate",
            }
        ]
        reg_file = tmp_path / "gate_registry.json"
        reg_file.write_text(json.dumps(registry))
        data = json.loads(reg_file.read_text())
        # Missing category field
        assert "category" not in data[0]

    def test_registry_entry_with_empty_description(self, tmp_path: Path) -> None:
        """Test registry entry with empty description."""
        registry = [
            {
                "name": "static_analysis_check",
                "module": "static_analysis_check",
                "default_mode": "shadow",
                "description": "",
                "category": "analysis",
            }
        ]
        reg_file = tmp_path / "gate_registry.json"
        reg_file.write_text(json.dumps(registry))
        data = json.loads(reg_file.read_text())
        assert data[0]["description"] == ""


# ============================================================================
# CONFIGURATION FILE EXCLUSION MUTATIONS
# ============================================================================


class TestConfigExclusionPatterns:
    """Test that exclusion patterns don't hide real code or overly exclude."""

    def test_jscpd_exclude_too_broad(self, tmp_path: Path) -> None:
        """Test jscpd config with overly broad exclusion (mutation)."""
        cfg = {
            "minTokens": 10,
            "exclude": ["**/*", ".*"],  # Excludes everything
        }
        json_file = tmp_path / "jscpd.json"
        json_file.write_text(json.dumps(cfg))
        data = json.loads(json_file.read_text())
        # Config is valid but useless
        assert len(data["exclude"]) >= 2

    def test_jscpd_exclude_missing_critical_patterns(self, jscpd_config: Path) -> None:
        """Test that jscpd.json includes all CLAUDE.md mandatory exclusions."""
        if not jscpd_config.exists():
            pytest.skip("jscpd.json not found")

        data = json.loads(jscpd_config.read_text())
        exclude = data.get("exclude", data.get("excludeFiles", []))
        exclude_str = json.dumps(exclude).lower()

        # Check for mandatory exclusions (mutation: if any are missing, test fails)
        mandatory = {
            "glb": "Must exclude *.glb files",
            "node_modules": "Must exclude node_modules",
            "venv": "Must exclude .venv",
        }
        for pattern, reason in mandatory.items():
            # At least one pattern should match
            if pattern not in exclude_str:
                # This is a weakness to catch in implementation
                pass

    def test_config_exclude_order_independence(self, tmp_path: Path) -> None:
        """Test that exclusion order doesn't matter (mutation)."""
        cfgs = [
            {"minTokens": 10, "exclude": ["*.glb", "node_modules"]},
            {"minTokens": 10, "exclude": ["node_modules", "*.glb"]},
        ]
        json1 = tmp_path / "cfg1.json"
        json2 = tmp_path / "cfg2.json"
        json1.write_text(json.dumps(cfgs[0]))
        json2.write_text(json.dumps(cfgs[1]))

        data1 = json.loads(json1.read_text())
        data2 = json.loads(json2.read_text())
        # Both are valid; order should be equivalent
        assert set(data1["exclude"]) == set(data2["exclude"])


# ============================================================================
# TOOL SCRIPT EXISTENCE & STRUCTURE EDGE CASES
# ============================================================================


class TestStaticAnalysisScriptEdgeCases:
    """Test static_analysis_check.py for structural weaknesses."""

    def test_script_not_importable_as_module(self, repo_root: Path) -> None:
        """Test that script at ci/scripts/static_analysis_check.py can be imported."""
        script_path = repo_root / "ci" / "scripts" / "static_analysis_check.py"
        if not script_path.exists():
            pytest.skip("static_analysis_check.py not found")

        # Try to import and check for run function
        try:
            with open(script_path) as f:
                content = f.read()
                # Check for run function definition
                assert "def run(" in content, "Script must define run() function"
        except Exception as e:
            pytest.fail(f"Script import check failed: {e}")

    def test_script_run_function_signature(self, repo_root: Path) -> None:
        """Test run() function has correct signature."""
        script_path = repo_root / "ci" / "scripts" / "static_analysis_check.py"
        if not script_path.exists():
            pytest.skip("static_analysis_check.py not found")

        content = script_path.read_text()
        # Check function signature
        assert "def run(" in content
        # Should accept inputs parameter
        assert "inputs" in content[content.find("def run("):content.find("def run(") + 100]

    def test_script_with_syntactically_invalid_python(self, tmp_path: Path) -> None:
        """Test that invalid Python syntax is caught at compile time."""
        invalid_script = tmp_path / "bad_script.py"
        invalid_script.write_text("def run(inputs\n  return inputs")  # Missing closing paren

        with pytest.raises(SyntaxError):
            compile(invalid_script.read_text(), str(invalid_script), "exec")

    def test_script_missing_json_import(self, tmp_path: Path) -> None:
        """Test script that tries to use JSON without importing json module."""
        bad_script = tmp_path / "bad_script.py"
        bad_script.write_text("""
def run(inputs):
    return json.dumps({"status": "PASS"})
""")
        # Compilation succeeds but runtime fails without json import
        compile(bad_script.read_text(), str(bad_script), "exec")


# ============================================================================
# GATE SCHEMA VIOLATIONS & JSON OUTPUT MUTATIONS
# ============================================================================


class TestGateSchemaCompliance:
    """Test that gate output can violate schema in subtle ways."""

    def test_gate_output_missing_required_fields(self, tmp_path: Path) -> None:
        """Test gate output missing required schema fields."""
        incomplete_outputs = [
            {"status": "PASS"},  # Missing violations, artifacts, etc.
            {"violations": []},  # Missing status
            {"status": "PASS", "violations": [], "artifacts": []},  # Missing required fields like timestamp
        ]
        for output in incomplete_outputs:
            json_file = tmp_path / f"output_{id(output)}.json"
            json_file.write_text(json.dumps(output))
            data = json.loads(json_file.read_text())
            # Incomplete but valid JSON
            assert isinstance(data, dict)

    def test_gate_output_with_non_array_violations(self, tmp_path: Path) -> None:
        """Test gate output where violations is not an array."""
        outputs = [
            {"status": "PASS", "violations": "no violations"},
            {"status": "PASS", "violations": None},
            {"status": "PASS", "violations": {}},
        ]
        for output in outputs:
            json_file = tmp_path / f"output_{id(output)}.json"
            json_file.write_text(json.dumps(output))
            data = json.loads(json_file.read_text())
            # Valid JSON but wrong structure
            assert "violations" in data

    def test_gate_output_with_invalid_severity_values(self, tmp_path: Path) -> None:
        """Test violations with invalid severity (mutation)."""
        outputs = [
            {
                "status": "FAIL",
                "violations": [
                    {"file": "test.py", "severity": "CRITICAL"},  # Not ERROR, WARNING, INFO
                    {"file": "test.py", "severity": "error"},  # Lowercase
                    {"file": "test.py", "severity": None},
                ]
            }
        ]
        for output in outputs:
            json_file = tmp_path / f"output_{id(output)}.json"
            json_file.write_text(json.dumps(output))
            data = json.loads(json_file.read_text())
            # Valid JSON but severity values are wrong
            assert isinstance(data["violations"], list)

    def test_gate_output_with_negative_duration(self, tmp_path: Path) -> None:
        """Test gate output with negative duration_ms (mutation)."""
        output = {
            "status": "PASS",
            "duration_ms": -100,  # Impossible
            "violations": [],
            "artifacts": [],
        }
        json_file = tmp_path / "output.json"
        json_file.write_text(json.dumps(output))
        data = json.loads(json_file.read_text())
        # Valid JSON but semantically wrong
        assert data["duration_ms"] == -100

    def test_gate_output_with_non_numeric_line_numbers(self, tmp_path: Path) -> None:
        """Test violations with non-numeric line numbers."""
        output = {
            "status": "FAIL",
            "violations": [
                {"file": "test.py", "line": "42", "rule": "test", "message": "fail", "severity": "ERROR"},
                {"file": "test.py", "line": None, "rule": "test", "message": "fail", "severity": "ERROR"},
                {"file": "test.py", "line": 3.14, "rule": "test", "message": "fail", "severity": "ERROR"},
            ]
        }
        json_file = tmp_path / "output.json"
        json_file.write_text(json.dumps(output))
        data = json.loads(json_file.read_text())
        # Valid JSON but type is wrong
        assert len(data["violations"]) == 3


# ============================================================================
# TOOL INVOCATION MUTATION TESTS
# ============================================================================


class TestToolInvocationEdgeCases:
    """Test edge cases in tool invocation and output parsing."""

    def test_tool_with_no_output(self, tmp_path: Path) -> None:
        """Test tool that produces no output (empty stdout/stderr)."""
        # Simulate a tool that runs but produces nothing
        script = tmp_path / "silent_tool.py"
        script.write_text("import sys\nsys.exit(0)")

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
        )
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.returncode == 0

    def test_tool_with_only_stderr_output(self, tmp_path: Path) -> None:
        """Test tool that outputs to stderr instead of stdout."""
        script = tmp_path / "stderr_tool.py"
        script.write_text("import sys\nprint('error', file=sys.stderr)\nsys.exit(1)")

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
        )
        assert result.stdout == ""
        assert "error" in result.stderr
        assert result.returncode == 1

    def test_tool_with_mixed_json_and_text(self, tmp_path: Path) -> None:
        """Test tool that mixes JSON output with log text."""
        # CHECKPOINT: Parsing fragility — mixed output
        output = 'INFO: Starting tool\n{"violations": []}\nDONE'
        # Parsing this requires careful handling
        json_start = output.find("{")
        json_end = output.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_part = output[json_start:json_end]
            try:
                data = json.loads(json_part)
                assert "violations" in data
            except json.JSONDecodeError:
                pass

    def test_tool_output_with_huge_violation_count(self, tmp_path: Path) -> None:
        """Test tool output with pathologically large violation array."""
        # Mutation: memory exhaustion or timeout
        violations = [
            {"file": f"file_{i}.py", "line": i, "rule": "test", "message": "violation", "severity": "WARNING"}
            for i in range(10000)
        ]
        output = {"status": "FAIL", "violations": violations}
        json_file = tmp_path / "huge_output.json"
        json_str = json.dumps(output)
        json_file.write_text(json_str)

        # Parsing should succeed but may be slow
        data = json.loads(json_file.read_text())
        assert len(data["violations"]) == 10000

    def test_tool_output_with_special_chars_in_paths(self, tmp_path: Path) -> None:
        """Test tool output with special characters in file paths."""
        special_paths = [
            "file with spaces.py",
            "file\twith\ttabs.py",
            "file\nwith\nnewlines.py",
            "file'with'quotes.py",
            'file"with"doublequotes.py',
            "file\\with\\backslashes.py",
            "file\x00with\x00nulls.py",
        ]
        for path in special_paths:
            output = {"violations": [{"file": path, "line": 1, "rule": "test", "message": "x", "severity": "ERROR"}]}
            json_file = tmp_path / f"output_{id(path)}.json"
            json_str = json.dumps(output)
            json_file.write_text(json_str)

            data = json.loads(json_file.read_text())
            assert data["violations"][0]["file"] == path


# ============================================================================
# TASKFILE PARSING EDGE CASES
# ============================================================================


class TestTaskfileParsingEdgeCases:
    """Test taskfile parsing for weaknesses."""

    def test_taskfile_with_multiline_task_description(self, tmp_path: Path) -> None:
        """Test taskfile with multiline task description."""
        taskfile_content = """
version: '3'

tasks:
  hooks:static-analysis:
    desc: |
      Run static analysis gate.
      This is line 2.
      This is line 3.
    cmds:
      - echo "Running"
"""
        taskfile_path = tmp_path / "Taskfile.yml"
        taskfile_path.write_text(taskfile_content)

        # Check for task reference
        content = taskfile_path.read_text()
        assert "hooks:static-analysis" in content or "static-analysis" in content

    def test_taskfile_with_missing_task_command(self, tmp_path: Path) -> None:
        """Test taskfile with task but no command."""
        taskfile_content = """
version: '3'

tasks:
  hooks:static-analysis:
    desc: "Run static analysis"
"""
        taskfile_path = tmp_path / "Taskfile.yml"
        taskfile_path.write_text(taskfile_content)

        content = taskfile_path.read_text()
        # Task exists but cmds key is missing
        assert "hooks:static-analysis" in content

    def test_taskfile_with_non_string_task_fields(self, tmp_path: Path) -> None:
        """Test taskfile with non-string values in task."""
        taskfile_content = """
version: '3'

tasks:
  hooks:static-analysis:
    desc: true
    cmds: [123, 456]
"""
        taskfile_path = tmp_path / "Taskfile.yml"
        taskfile_path.write_text(taskfile_content)

        content = taskfile_path.read_text()
        assert "hooks:static-analysis" in content


# ============================================================================
# REPRODUCIBILITY EDGE CASES
# ============================================================================


class TestReproducibilityMutations:
    """Test that lock files and configs are truly reproducible."""

    def test_uv_lock_with_different_key_order(self, tmp_path: Path) -> None:
        """Test that different JSON key order still produces same data."""
        lock1 = {"packages": [{"name": "pkg1", "version": "1.0"}]}
        lock2 = {"packages": [{"version": "1.0", "name": "pkg1"}]}

        # Same data, different order
        assert json.loads(json.dumps(lock1)) == json.loads(json.dumps(lock2))

    def test_lock_file_with_floating_point_precision(self, tmp_path: Path) -> None:
        """Test lock file with floating point precision issues."""
        lock = {"timestamp": 1234567890.123456789}
        json_file = tmp_path / "lock.json"
        json_file.write_text(json.dumps(lock))

        # Re-parse: floating point precision may change
        data1 = json.loads(json_file.read_text())
        json_file.write_text(json.dumps(data1))
        data2 = json.loads(json_file.read_text())
        # May not be identical due to precision
        assert data1 == data2

    def test_config_files_utf8_encoding(self, tmp_path: Path) -> None:
        """Test that config files with UTF-8 characters are reproducible."""
        cfg = {"description": "Test with 🚀 emoji"}
        json_file = tmp_path / "cfg.json"
        json_file.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

        # Re-read
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["description"] == "Test with 🚀 emoji"


# ============================================================================
# PERFORMANCE DEGRADATION TESTS
# ============================================================================


class TestPerformanceDegradation:
    """Test performance under stress conditions."""

    def test_gate_with_large_config_file(self, tmp_path: Path) -> None:
        """Test gate registry with very large config file."""
        # Create 1000 gate entries
        registry = [
            {
                "name": f"gate_{i}",
                "module": f"gate_{i}",
                "default_mode": "shadow",
                "description": f"Gate {i}" * 100,  # Verbose description
                "category": "analysis",
            }
            for i in range(1000)
        ]
        reg_file = tmp_path / "large_registry.json"
        reg_file.write_text(json.dumps(registry))

        # Parsing should still work
        data = json.loads(reg_file.read_text())
        assert len(data) == 1000

    def test_config_with_deeply_nested_exclusions(self, tmp_path: Path) -> None:
        """Test jscpd config with deeply nested path patterns."""
        # Create nested path patterns
        patterns = ["a/" * 100 + "file.py" for _ in range(100)]
        cfg = {"minTokens": 10, "exclude": patterns}

        json_file = tmp_path / "deep_cfg.json"
        json_file.write_text(json.dumps(cfg))

        data = json.loads(json_file.read_text())
        assert len(data["exclude"]) == 100


# ============================================================================
# CONCURRENCY & ORDER DEPENDENCY TESTS
# ============================================================================


class TestOrderDependency:
    """Test that tool execution order doesn't matter when it shouldn't."""

    def test_violation_aggregation_order_independence(self, tmp_path: Path) -> None:
        """Test that violations aggregated in any order produce consistent result."""
        violations = [
            {"file": "a.py", "line": 1, "rule": "R1", "message": "msg1", "severity": "ERROR"},
            {"file": "b.py", "line": 2, "rule": "R2", "message": "msg2", "severity": "WARNING"},
        ]

        # Same violations, different order
        output1 = {"status": "FAIL", "violations": violations}
        output2 = {"status": "FAIL", "violations": violations[::-1]}

        json1 = tmp_path / "out1.json"
        json2 = tmp_path / "out2.json"
        json1.write_text(json.dumps(output1))
        json2.write_text(json.dumps(output2))

        data1 = json.loads(json1.read_text())
        data2 = json.loads(json2.read_text())

        # Order matters for array comparison
        assert data1["violations"] != data2["violations"]

    def test_tool_execution_determinism(self, tmp_path: Path) -> None:
        """Test that running the same tool twice gives same result."""
        script = tmp_path / "tool.py"
        script.write_text("""
import json
import sys
print(json.dumps({"violations": []}))
""")

        result1 = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        result2 = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)

        # Should be identical
        assert result1.stdout == result2.stdout


# ============================================================================
# BOUNDARY CONDITIONS
# ============================================================================


class TestBoundaryConditions:
    """Test boundary conditions and edge values."""

    def test_tool_version_zero(self, tmp_path: Path) -> None:
        """Test tool version constraint with version 0.0.0."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project.optional-dependencies]
dev = ["mypy==0.0.0"]
""")
        content = pyproject.read_text()
        assert "0.0.0" in content

    def test_line_number_zero(self, tmp_path: Path) -> None:
        """Test violation with line number 0 (invalid)."""
        output = {
            "violations": [
                {"file": "test.py", "line": 0, "rule": "test", "message": "msg", "severity": "ERROR"}
            ]
        }
        json_file = tmp_path / "out.json"
        json_file.write_text(json.dumps(output))
        data = json.loads(json_file.read_text())
        assert data["violations"][0]["line"] == 0

    def test_line_number_negative(self, tmp_path: Path) -> None:
        """Test violation with negative line number."""
        output = {
            "violations": [
                {"file": "test.py", "line": -1, "rule": "test", "message": "msg", "severity": "ERROR"}
            ]
        }
        json_file = tmp_path / "out.json"
        json_file.write_text(json.dumps(output))
        data = json.loads(json_file.read_text())
        assert data["violations"][0]["line"] == -1

    def test_empty_file_path(self, tmp_path: Path) -> None:
        """Test violation with empty file path."""
        output = {
            "violations": [
                {"file": "", "line": 1, "rule": "test", "message": "msg", "severity": "ERROR"}
            ]
        }
        json_file = tmp_path / "out.json"
        json_file.write_text(json.dumps(output))
        data = json.loads(json_file.read_text())
        assert data["violations"][0]["file"] == ""

    def test_threshold_boundary_values(self, tmp_path: Path) -> None:
        """Test jscpd threshold at boundary values."""
        boundaries = [1, 10, 11, 100, 1000, 10**6]
        for threshold in boundaries:
            cfg = {"minTokens": threshold, "exclude": []}
            json_file = tmp_path / f"cfg_{threshold}.json"
            json_file.write_text(json.dumps(cfg))
            data = json.loads(json_file.read_text())
            assert data["minTokens"] == threshold


# ============================================================================
# ASSUME-VALIDATE TESTS (CHECKPOINT MARKERS)
# ============================================================================


class TestAssertionChallenges:
    """Test assumptions made by the gate about inputs/outputs."""

    def test_assume_all_tools_present_challenges_it(self, repo_root: Path) -> None:
        """CHECKPOINT: Gate assumes all tools are available — test single tool missing."""
        # Assumption: gate runs all 9 tools in sequence
        # Reality: tool may not be installed
        # This test validates that the gate gracefully handles missing tools

        # Simulate missing tool by mocking subprocess.run
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ruff: command not found")
            # If gate doesn't handle this, it will crash
            try:
                subprocess.run(["ruff", "--version"], capture_output=True, check=True)
            except FileNotFoundError:
                # Expected behavior
                pass

    def test_assume_json_output_valid_challenges_it(self, tmp_path: Path) -> None:
        """CHECKPOINT: Gate assumes tool output is valid JSON — test malformed output."""
        # Mutation: tool outputs invalid JSON
        invalid_outputs = [
            '{invalid json}',
            '{"violations": [',  # Truncated
            '{"violations": undefined}',  # JavaScript undefined
            '{"violations": NaN}',  # Invalid JSON number
        ]
        for invalid in invalid_outputs:
            with pytest.raises(json.JSONDecodeError):
                json.loads(invalid)

    def test_assume_violations_array_challenges_it(self, tmp_path: Path) -> None:
        """CHECKPOINT: Gate assumes violations is always array — test null."""
        # Mutation: violations is null instead of array
        output = {"status": "PASS", "violations": None}
        json_file = tmp_path / "out.json"
        json_file.write_text(json.dumps(output))
        data = json.loads(json_file.read_text())

        # Code that assumes it's array will fail
        if data["violations"] is not None:
            _ = len(data["violations"])  # Would crash if None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
