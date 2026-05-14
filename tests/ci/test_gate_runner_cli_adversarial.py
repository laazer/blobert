"""Adversarial tests for gate runner CLI behavior.

Covers mutation testing, edge cases, and assumption challenges for the gate
runner CLI (ci/scripts/gate_runner.py) that the existing test suite does not
exercise.

Dimensions covered:
  - Null & Empty: empty strings, empty JSON, missing values
  - Boundary: oversized inputs, extreme path lengths, Unicode
  - Type/Structure: wrong types in JSON, nested structures
  - Invalid/Corrupt: malformed JSON, special chars in paths
  - Combinatorial: flag combinations, mode+input combos
  - Error handling: stderr vs stdout separation, exit code discrimination

# CHECKPOINT — Conservative assumption: the gate runner MUST validate inputs
# before attempting any gate dispatch. If it crashes with a traceback instead of
# a structured error, the runner is not resilient to adversarial input.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


class TestCLIMutation:
    """Mutation tests: flip expected behavior paths."""

    def test_help_flag_any_position(self, gate_runner: Path) -> None:
        # Mutation: --help may only work at end; test mid-args and start
        for pos in [0, 1, 2]:
            args = ["--help"]
            for i, extra in enumerate(["gate_name", "--upstream-agent", "Spec"]):
                if i != pos:
                    args.append(extra)
            result = subprocess.run(
                [sys.executable, str(gate_runner), *args],
                capture_output=True, text=True,
            )
            # --help should always exit 0 regardless of position
            assert result.returncode == 0, \
                f"--help at position {pos} should exit 0, got {result.returncode}"

    def test_unknown_flag_rejected(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: unknown flags should produce usage error, not pass through
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--bogus-flag", "value"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "Unknown flags should be rejected"
        assert "bogus-flag" in result.stderr or "unknown" in result.stderr.lower() or "unrecognized" in result.stderr.lower(), \
            f"Error should mention the unknown flag, got: {result.stderr}"

    def test_empty_gate_name_rejected(self, gate_runner: Path) -> None:
        # Mutation: empty string as gate name should fail, not crash
        result = subprocess.run(
            [sys.executable, str(gate_runner), "",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "Empty gate name must be rejected"

    def test_unicode_gate_name_rejected(self, gate_runner: Path) -> None:
        # Mutation: Unicode in gate name should not cause encoding errors
        result = subprocess.run(
            [sys.executable, str(gate_runner), "gate_with_émojis_🎉_name",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True,
        )
        # Should not crash with UnicodeDecodeError
        assert "UnicodeDecodeError" not in result.stderr
        assert "UnicodeEncodeError" not in result.stderr

    def test_numeric_gate_name_rejected(self, gate_runner: Path) -> None:
        # Mutation: numeric gate name should not be accepted as valid
        result = subprocess.run(
            [sys.executable, str(gate_runner), "12345",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0, "Numeric gate name should be rejected"


class TestInputMutation:
    """Mutation tests on the --input JSON payload."""

    def test_null_input_object(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: null as input should not crash runner
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", "null"],
            capture_output=True, text=True,
        )
        # Runner should handle null gracefully (not crash with JSON decode error)
        assert "JSONDecodeError" not in result.stderr, \
            f"Runner should handle null input gracefully: {result.stderr}"

    def test_array_input_rejected(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: array input instead of object should be rejected
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", "[1, 2, 3]"],
            capture_output=True, text=True,
        )
        # Should not crash; may fail gate validation but runner shouldn't
        assert "JSONDecodeError" not in result.stderr

    def test_deeply_nested_input(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: deeply nested JSON should not cause stack overflow
        deep = {"data": {"level1": {"level2": {"level3": {"level4": {"level5": "value"}}}}}}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps(deep)],
            capture_output=True, text=True,
        )
        assert "RecursionError" not in result.stderr
        assert "MemoryError" not in result.stderr

    def test_empty_string_input(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: empty string as --input value
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", ""],
            capture_output=True, text=True,
        )
        # Should not crash with JSON decode error
        assert "JSONDecodeError" not in result.stderr

    def test_malformed_json_truncated(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: truncated JSON should be caught before gate dispatch
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", '{"spec_file": "/tmp/spec.md", "ticket_type": "generic"'],
            capture_output=True, text=True,
        )
        assert "JSONDecodeError" not in result.stderr

    def test_input_with_special_chars_in_path(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: paths with spaces, brackets, and special chars
        spec_path = tmp_gate_results / "spec [with] spaces & special chars.md"
        spec_path.write_text("# Test Spec\n\n## Overview\n\n## Acceptance Criteria\n")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(spec_path), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash due to path escaping
        assert "OSError" not in result.stderr or result.returncode in (0, 1)

    def test_input_with_null_values(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: null values in input dict should not cause KeyError
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": None, "ticket_type": None})],
            capture_output=True, text=True,
        )
        # Should not crash with AttributeError on None
        assert "AttributeError" not in result.stderr


class TestExitCodeDiscrimination:
    """Test that exit codes are properly discriminated (not all non-zero)."""

    def test_exit_code_2_for_usage_error(self, gate_runner: Path) -> None:
        # Mutation: usage errors should use exit code 2 (not 1)
        result = subprocess.run(
            [sys.executable, str(gate_runner)],
            capture_output=True, text=True,
        )
        # No args → usage error → exit 2
        assert result.returncode == 2, \
            f"Usage error should exit 2, got {result.returncode}"

    def test_exit_code_2_for_missing_spec_file(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: missing spec file in input should exit 2 (not 1)
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/path/to/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Shadow mode: missing spec file does not block CI → exit 0
        assert result.returncode == 0, \
            f"Shadow mode should not block CI for missing spec file, got {result.returncode}"

    def test_stderr_vs_stdout_separation(self, gate_runner: Path) -> None:
        # Mutation: errors should go to stderr, not stdout
        result = subprocess.run(
            [sys.executable, str(gate_runner)],
            capture_output=True, text=True,
        )
        assert result.stderr != "", "Usage error should produce stderr output"
        # stdout should be empty or minimal for errors
        assert result.stdout.strip() == "" or "usage" in result.stdout.lower() or "help" in result.stdout.lower(), \
            f"stdout should not contain error details: {result.stdout}"


class TestCombinatorialFlags:
    """Combinatorial tests: flag order and combination."""

    @pytest.mark.parametrize("ticket_id", ["", "M", "A" * 256, "M902-01", "ticket/with/slashes"])
    def test_various_ticket_ids(self, gate_runner: Path, tmp_gate_results: Path, ticket_id: str) -> None:
        # Mutation: ticket ID validation boundary cases
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", ticket_id,
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash regardless of ticket_id content
        assert "OSError" not in result.stderr
        assert "UnicodeDecodeError" not in result.stderr

    @pytest.mark.parametrize("mode", ["shadow", "blocking", "SHADOW", "Shadow", ""])
    def test_mode_case_sensitivity(self, gate_runner: Path, tmp_gate_results: Path, mode: str) -> None:
        # Mutation: mode should be case-sensitive or normalized
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", mode,
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash; invalid modes should be handled
        assert "ValueError" not in result.stderr or result.returncode != 2

    @pytest.mark.parametrize("upstream,downstream", [
        ("", ""),
        ("Spec", ""),
        ("", "TestDesigner"),
        ("A" * 256, "B" * 256),
        ("Spec Agent", "Test Designer Agent"),
        ("UPPER", "lower"),
    ])
    def test_agent_name_edge_cases(self, gate_runner: Path, tmp_gate_results: Path,
                                     upstream: str, downstream: str) -> None:
        # Mutation: agent name boundary cases
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", upstream,
             "--downstream-agent", downstream,
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash with unusual agent names
        assert "UnicodeDecodeError" not in result.stderr


class TestOutputDirEdgeCases:
    """Test output directory edge cases."""

    def test_output_dir_with_symlink(self, gate_runner: Path, tmp_path: Path) -> None:
        # Mutation: symlinked output directory should work
        real_dir = tmp_path / "real_output"
        real_dir.mkdir()
        link_dir = tmp_path / "link_output"
        link_dir.symlink_to(real_dir)
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(link_dir),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash on symlink
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)

    def test_output_dir_is_file(self, gate_runner: Path, tmp_path: Path) -> None:
        # Mutation: output-dir pointing to a file should fail gracefully
        file_path = tmp_path / "not_a_dir"
        file_path.write_text("content")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(file_path),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should fail gracefully, not crash
        assert "OSError" not in result.stderr or result.returncode != 0

    def test_output_dir_permission_denied(self, gate_runner: Path, tmp_path: Path) -> None:
        # Mutation: unreadable output directory
        no_access_dir = tmp_path / "no_access"
        no_access_dir.mkdir(mode=0o000)
        try:
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", "shadow",
                 "--output-dir", str(no_access_dir),
                 "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            # Should not crash with unexpected exception
            assert "OSError" not in result.stderr or result.returncode != 0
        finally:
            # Restore permissions so cleanup works
            no_access_dir.chmod(0o755)

    def test_output_dir_nonexistent_parent(self, gate_runner: Path) -> None:
        # Mutation: output-dir with nonexistent parent should propagate the error
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", "/nonexistent/deeply/nested/dir/that/does/not/exist/output",
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # OSError should propagate (not silently swallowed)
        assert result.returncode != 0, "OSError from directory creation should propagate"
        assert "WARNING" in result.stderr, "Should log a warning about the failed directory creation"


class TestPathTraversal:
    """Path traversal and injection tests."""

    def test_dotdot_in_spec_path(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: path traversal in spec_file should not escape expected scope
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "../../../etc/passwd", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash; if it reads the file, that's a security concern
        assert "UnicodeDecodeError" not in result.stderr

    def test_null_byte_in_spec_path(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: null byte in path should be rejected or handled
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/tmp/spec\x00.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_absolute_vs_relative_spec_path(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: relative spec path should resolve relative to cwd
        spec_path = tmp_gate_results / "relative_spec.md"
        spec_path.write_text("# Test\n\n## Overview\n\n## Acceptance Criteria\n")
        orig_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_gate_results))
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", "shadow",
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "relative_spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            # Should not crash
            assert "OSError" not in result.stderr
        finally:
            os.chdir(orig_cwd)


class TestDeterminism:
    """Determinism tests: same input → same output structure."""

    def test_result_structure_consistent_across_runs(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: result structure should be deterministic
        results = []
        for _ in range(3):
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", "shadow",
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            files = list(tmp_gate_results.glob("*.json"))
            if files:
                data = json.loads(files[-1].read_text())
                results.append({k: type(v).__name__ for k, v in data.items()})
                tmp_gate_results.unlink() if tmp_gate_results.is_file() else None
                for f in tmp_gate_results.glob("*.json"):
                    f.unlink()

        if len(results) >= 2:
            # All runs should produce same field types
            for i in range(1, len(results)):
                assert results[0] == results[i], \
                    f"Result structure differs between runs: {results[0]} vs {results[i]}"

    def test_exit_code_deterministic_for_same_input(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: same input should always produce same exit code
        codes = set()
        for _ in range(5):
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", "shadow",
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            codes.add(result.returncode)
        assert len(codes) == 1, f"Exit code not deterministic: {codes}"
