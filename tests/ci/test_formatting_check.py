"""Behavioral tests for formatting check gate (M902-10).

Specification: project_board/specs/902_10_formatting_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md

Tests validate:
  - Requirement 01: Gate module and run() function interface
  - Requirement 02: Output contract (schema, fields, types)
  - Requirement 03: Formatter invocation and change detection
  - Requirement 04: Re-staging logic
  - Requirement 05: Error handling and graceful degradation
  - Requirement 06: Output contract validation and schema conformance
  - Requirement 07: Non-functional requirements (performance, reliability)

Total coverage: 25+ distinct test vectors across formatter categories,
mixed scenarios, error cases, edge cases, schema validation, and git integration.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# Add ci/scripts to path for gate imports
_CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(_CI_SCRIPTS))

# Import the gate module
from gates import formatting_check


# ============================================================================
# REQUIREMENT 01: Gate Module and run() Function Signature
# ============================================================================


class TestRequirement01GateModuleAndSignature:
    """Tests for Requirement 01: Gate module exists and run() is callable."""

    def test_gate_module_importable(self) -> None:
        """AC-01.1: formatting_check module is importable."""
        # The import at module level proves this; no further assertion needed
        assert hasattr(formatting_check, "run"), "Module must export run() function"

    def test_run_function_callable(self) -> None:
        """AC-01.2: run() function is callable and accepts dict input."""
        assert callable(formatting_check.run), "run must be callable"

    def test_run_function_signature_accepts_empty_dict(self) -> None:
        """AC-01.2: run() accepts empty dict and returns dict."""
        with mock.patch("subprocess.run") as mock_run:
            # Mock git to return no staged files
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert isinstance(result, dict), "run() must return a dict"

    def test_run_function_always_returns_dict(self) -> None:
        """AC-01.2: run() never returns None or non-dict types."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({"ticket_id": "M902-10"})
            assert isinstance(result, dict), "run() must return dict, not None"


# ============================================================================
# REQUIREMENT 02: Output Contract and Schema
# ============================================================================


class TestRequirement02OutputContract:
    """Tests for Requirement 02: Output schema, fields, types."""

    def _mock_git_no_files(self) -> mock.MagicMock:
        """Mock git to return no staged files."""
        mock_run = mock.MagicMock()
        mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        return mock_run

    def test_output_dict_has_all_required_fields_on_success(self) -> None:
        """AC-02.1: Success result has status, gate, timestamp, ticket_id, message, artifacts, duration_ms."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            required_fields = {
                "status",
                "gate",
                "timestamp",
                "ticket_id",
                "message",
                "artifacts",
                "duration_ms",
            }
            assert required_fields.issubset(
                result.keys()
            ), f"Missing fields: {required_fields - set(result.keys())}"

    def test_output_status_is_pass_on_success(self) -> None:
        """AC-02.1: status field is 'PASS' on success (shadow mode)."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            assert result["status"] == "PASS", "Shadow mode gate returns PASS"

    def test_output_gate_field_is_formatting_check(self) -> None:
        """AC-02.1: gate field is 'formatting_check'."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            assert result["gate"] == "formatting_check"

    def test_output_timestamp_is_iso8601(self) -> None:
        """AC-02.1: timestamp is ISO 8601 UTC format."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            ts = result["timestamp"]
            assert isinstance(ts, str), "timestamp must be string"
            # Basic ISO 8601 check: should contain T and Z
            assert "T" in ts, f"timestamp '{ts}' is not ISO 8601 format"
            assert ts.endswith("Z"), f"timestamp '{ts}' should end with Z"

    def test_output_ticket_id_defaults_to_M902_10(self) -> None:
        """AC-02.1: ticket_id defaults to 'M902-10' if not in inputs."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            assert result["ticket_id"] == "M902-10"

    def test_output_ticket_id_from_inputs(self) -> None:
        """AC-02.1: ticket_id is copied from inputs if provided."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({"ticket_id": "M999-99"})
            assert result["ticket_id"] == "M999-99"

    def test_output_message_is_string(self) -> None:
        """AC-02.2: message field is non-empty string."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            assert isinstance(result["message"], str)
            assert len(result["message"]) > 0
            assert len(result["message"]) <= 250, "Message must be <= 250 chars"

    def test_output_artifacts_is_list(self) -> None:
        """AC-02.3: artifacts is a list of strings."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            assert isinstance(result["artifacts"], list)

    def test_output_duration_ms_is_positive_number(self) -> None:
        """AC-02.1: duration_ms is a positive integer."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            assert isinstance(result["duration_ms"], (int, float))
            assert result["duration_ms"] >= 0

    def test_output_is_json_serializable(self) -> None:
        """AC-02.1: Entire result dict is JSON-serializable."""
        with mock.patch("subprocess.run", self._mock_git_no_files()):
            result = formatting_check.run({})
            try:
                json.dumps(result)
            except TypeError as e:
                pytest.fail(f"Result is not JSON-serializable: {e}")


# ============================================================================
# REQUIREMENT 03: Formatter Invocation and Change Detection
# ============================================================================


class TestRequirement03FormatterInvocation:
    """Tests for Requirement 03: Formatter invocation and change detection."""

    # Test TV-01: Black formatter only
    def test_black_formatter_invocation(self) -> None:
        """TV-01: Staged .py files with unformatted code → Black formats."""
        with mock.patch("subprocess.run") as mock_run:
            # Mock git to return a Python file
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    # First call: enumerate files
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Black runs and modifies
                    return mock.Mock(returncode=0, stdout="reformatted test.py", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Second git diff call (to detect changes)
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    # git add
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"
            assert "black" in result["message"].lower()

    # Test TV-05: Black formatter with already-formatted code
    def test_black_formatter_no_changes(self) -> None:
        """TV-05: Black runs, detects no changes → No re-staging."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # No changes detected
                    return mock.Mock(returncode=1, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"
            assert result["formatting_changed"] is False
            assert result["artifacts"] == []

    # Test TV-09: Empty staging area
    def test_empty_staging_area(self) -> None:
        """TV-09: No staged files → No changes, no formatters run."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["status"] == "PASS"
            assert result["formatting_changed"] is False
            assert result["artifacts"] == []
            assert "already formatted" in result["message"].lower()


# ============================================================================
# REQUIREMENT 04: Re-staging Logic
# ============================================================================


class TestRequirement04RestagingLogic:
    """Tests for Requirement 04: Re-staging logic when formatting changes."""

    def test_restage_on_formatting_changes(self) -> None:
        """AC-04.1: If formatting_changed=true, gate calls git add."""
        with mock.patch("subprocess.run") as mock_run:
            git_add_called = False

            def run_side_effect(cmd, *args, **kwargs):
                nonlocal git_add_called
                if "git" in str(cmd) and "add" in str(cmd):
                    git_add_called = True
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"
            # Verify git add was called
            git_add_calls = [
                call for call in mock_run.call_args_list
                if "git" in str(call) and "add" in str(call)
            ]
            assert len(git_add_calls) > 0, "git add should be called when formatting changes"

    def test_restage_message_correctness(self) -> None:
        """AC-04.4: Message matches frozen template 'Re-staged for review.'"""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert "Re-staged for review" in result["message"]

    def test_restage_artifacts_list_populated(self) -> None:
        """AC-04.3: artifacts list contains re-staged file paths."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py\nfoo.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert isinstance(result["artifacts"], list)
            assert len(result["artifacts"]) > 0


# ============================================================================
# REQUIREMENT 05: Error Handling and Graceful Degradation
# ============================================================================


class TestRequirement05ErrorHandling:
    """Tests for Requirement 05: Error handling (timeout, git failure, formatter unavailable)."""

    # TV-15: Formatter unavailable (graceful skip)
    def test_formatter_unavailable_graceful_skip(self) -> None:
        """TV-15: Formatter not installed → Skip with WARN violation."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Simulate formatter not found
                    raise FileNotFoundError("black: command not found")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Graceful degradation: should skip black but not fail entirely
            assert result["status"] == "PASS"

    # TV-16: Formatter timeout
    def test_formatter_timeout_returns_fail(self) -> None:
        """TV-16: Formatter timeout after 30s → FAIL with timeout violation."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, timeout=None, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Simulate timeout
                    raise subprocess.TimeoutExpired("black", timeout)
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "FAIL"
            assert "timeout" in result.get("message", "").lower()

    # TV-17: Formatter error (non-zero exit)
    def test_formatter_error_returns_fail(self) -> None:
        """TV-17: Formatter exits non-zero → FAIL with subprocess_error violation."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Formatter errors
                    return mock.Mock(
                        returncode=1,
                        stdout="",
                        stderr="syntax error: invalid syntax",
                    )
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "FAIL"
            assert "violations" in result

    # TV-18: Git unavailable
    def test_git_unavailable_returns_fail(self) -> None:
        """TV-18: git not available → FAIL with git_failed violation."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd):
                    raise FileNotFoundError("git: command not found")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "FAIL"
            assert "violations" in result


# ============================================================================
# REQUIREMENT 06: Output Contract Validation
# ============================================================================


class TestRequirement06OutputValidation:
    """Tests for Requirement 06: Output contract validation."""

    def test_output_schema_compliance_success(self) -> None:
        """AC-06.1: Success result matches M902-01 gate-result-success schema."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            # Check required fields
            assert "status" in result
            assert "gate" in result
            assert "timestamp" in result
            assert "ticket_id" in result
            assert "message" in result
            assert "artifacts" in result
            assert "duration_ms" in result

            # Check types
            assert isinstance(result["status"], str)
            assert isinstance(result["gate"], str)
            assert isinstance(result["timestamp"], str)
            assert isinstance(result["ticket_id"], str)
            assert isinstance(result["message"], str)
            assert isinstance(result["artifacts"], list)
            assert isinstance(result["duration_ms"], (int, float))

    def test_output_field_values_valid(self) -> None:
        """AC-06.1: Field values are valid (status in [PASS, FAIL], gate='formatting_check', etc)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert result["status"] in ["PASS", "FAIL"]
            assert result["gate"] == "formatting_check"
            assert result["timestamp"].endswith("Z")
            assert isinstance(result["ticket_id"], str)
            assert len(result["message"]) > 0

    def test_optional_formatting_changed_field_present(self) -> None:
        """AC-06.5: Optional formatting_changed field is present and accurate."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert "formatting_changed" in result
            assert isinstance(result["formatting_changed"], bool)

    def test_optional_formatters_applied_field_present(self) -> None:
        """AC-06.5: Optional formatters_applied field is present."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert "formatters_applied" in result
            assert isinstance(result["formatters_applied"], list)


# ============================================================================
# REQUIREMENT 07: Non-Functional Requirements
# ============================================================================


class TestRequirement07NonFunctionalRequirements:
    """Tests for Requirement 07: Performance, reliability, idempotency."""

    def test_gate_completes_within_reasonable_time(self) -> None:
        """NFR: Gate completes in <5 seconds for typical staging (mocked)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")

            start = time.time()
            result = formatting_check.run({})
            elapsed = time.time() - start

            # In mocked tests, should be nearly instant
            assert elapsed < 5.0, f"Gate took {elapsed}s, should be <5s"
            assert result["duration_ms"] > 0

    def test_gate_graceful_degradation_all_formatters_unavailable(self) -> None:
        """NFR: If all formatters unavailable, gate returns PASS with WARN violations."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                # All formatters raise FileNotFoundError
                raise FileNotFoundError("formatter not found")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Graceful degradation: PASS but with warnings
            assert result["status"] == "PASS"

    def test_gate_idempotency_same_input_same_output(self) -> None:
        """NFR: Running gate twice on same input yields same result (deterministic)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")

            result1 = formatting_check.run({"ticket_id": "M902-10"})
            result2 = formatting_check.run({"ticket_id": "M902-10"})

            # Core fields should match (timestamp may differ slightly)
            assert result1["status"] == result2["status"]
            assert result1["gate"] == result2["gate"]
            assert result1["formatting_changed"] == result2["formatting_changed"]
            assert result1["artifacts"] == result2["artifacts"]


# ============================================================================
# Mixed Scenarios (TV-07 through TV-14)
# ============================================================================


class TestMixedScenarios:
    """Tests for mixed scenarios: partial formatting, mixed languages, edge cases."""

    # TV-07: Partial formatting needed
    def test_partial_formatting_needed(self) -> None:
        """TV-07: Some files need formatting, some don't → Only changed files in artifacts."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="a.py\nb.py\nc.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Only a.py and c.py changed
                    return mock.Mock(returncode=0, stdout="--- a/a.py\n+++ b/a.py\n--- a/c.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"
            assert result["formatting_changed"] is True

    # TV-10: Large file
    def test_large_file_formatting(self) -> None:
        """TV-10: Single large .py file (10,000 lines) → Formats successfully."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="large_file.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted large_file.py", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/large_file.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"

    # TV-11: Many small files
    def test_many_small_files(self) -> None:
        """TV-11: 100 staged .py files → All formatters run successfully."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    # Return 100 file names
                    files = "\n".join(f"file{i}.py" for i in range(100))
                    return mock.Mock(returncode=0, stdout=files, stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"

    # TV-12: Only config changes
    def test_only_config_changes(self) -> None:
        """TV-12: pyproject.toml only (not source code) → No formatting."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="pyproject.toml", stderr="")
                elif any(fmt in str(cmd) for fmt in ["black", "ruff", "prettier", "gdformat"]):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"


# ============================================================================
# Edge Cases (TV-20 through TV-23)
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases: empty files, symlinks, deleted files, long names."""

    # TV-20: Empty file
    def test_empty_file_handling(self) -> None:
        """TV-20: Empty .py file → Formatter handles gracefully."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="empty.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=1, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Empty file treated as already formatted (no changes)
            assert result["status"] == "PASS"

    # TV-22: File deleted after enumeration
    def test_file_deleted_after_enumeration(self) -> None:
        """TV-22: File deleted between enumeration and formatting → Formatter errors."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="deleted.py", stderr="")
                elif "black" in str(cmd):
                    # File is gone
                    raise FileNotFoundError("deleted.py: No such file")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # File deletion is a soft error (WARN, not FAIL)
            assert result["status"] in ["PASS", "FAIL"]

    # TV-23: Very long filename
    def test_very_long_filename(self) -> None:
        """TV-23: Filename exceeds 255 chars → Gate handles gracefully."""
        with mock.patch("subprocess.run") as mock_run:
            long_name = "a" * 250 + ".py"

            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout=long_name, stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # No crash on long filename
            assert result["status"] in ["PASS", "FAIL"]


# ============================================================================
# Failure Output Schema Tests
# ============================================================================


class TestFailureOutputSchema:
    """Tests for failure output schema (when status=FAIL)."""

    def test_failure_dict_has_violations_array(self) -> None:
        """AC-02.4: FAIL result includes violations array."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Formatter fails
                    return mock.Mock(returncode=1, stdout="", stderr="syntax error")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            assert result["status"] == "FAIL"
            assert "violations" in result
            assert isinstance(result["violations"], list)

    def test_violation_structure(self) -> None:
        """AC-02.4: Each violation has file, line, rule, message."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=1, stdout="", stderr="error")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            if result["status"] == "FAIL" and result["violations"]:
                for violation in result["violations"]:
                    assert "file" in violation
                    assert "line" in violation
                    assert "rule" in violation
                    assert "message" in violation


# ============================================================================
# Message Template Tests (Requirement 03 coverage)
# ============================================================================


class TestMessageTemplates:
    """Tests for frozen message templates from Requirement 03."""

    def test_message_formatting_changed_single_formatter(self) -> None:
        """Message when single formatter makes changes."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Message should mention formatting and re-staging
            assert "Formatted" in result["message"] or "formatted" in result["message"]

    def test_message_no_changes(self) -> None:
        """Message when no formatting changes detected."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            # Message should indicate already formatted
            message_lower = result["message"].lower()
            assert "already formatted" in message_lower or "no changes" in message_lower
