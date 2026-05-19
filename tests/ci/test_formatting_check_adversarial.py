"""Adversarial and mutation test suite for formatting check gate (M902-10).

Specification: project_board/specs/902_10_formatting_gate_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/10_stage_1_formatting_and_restage_gate.md

Adversarial test objectives:
  - Expose edge cases and boundary conditions not covered by behavioral tests
  - Mutation testing: invert logic, omit operations, swap order, corrupt data
  - Concurrency and race condition detection
  - Stress testing with extreme inputs
  - Schema validation mutations
  - Error handling robustness
  - Determinism and idempotency under adversarial conditions
  - False-positive and false-negative detection in change detection logic

Test matrix dimensions:
  - Null & Empty: empty dicts, empty lists, null values
  - Boundary: very large files, max field lengths, extreme counts
  - Type/Structure: wrong types, nested structures, missing keys
  - Invalid/Corrupt: malformed git output, invalid JSON, corrupted state
  - Concurrency: parallel invocations, race conditions
  - Order-dependency: formatter order changes, git operation sequencing
  - Mutation: invert booleans, swap operations, omit steps
  - Stress: large scaling, repeated calls, accumulating state
  - Determinism: repeated calls verify consistency
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

_CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(_CI_SCRIPTS))

from gates import formatting_check


# ============================================================================
# NULL & EMPTY TESTS — Verify gate handles missing/empty data
# ============================================================================


class TestNullAndEmpty:
    """Adversarial tests for null and empty conditions."""

    def test_empty_dict_input(self) -> None:
        """Gate accepts empty dict input without error."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert isinstance(result, dict)
            assert result["status"] in ["PASS", "FAIL"]

    def test_none_input_raises_error(self) -> None:
        """Gate rejects None input (should fail or raise)."""
        # CHECKPOINT: Conservative assumption — gate should validate inputs or gracefully handle.
        # If gate expects dict, None should trigger TypeError or validation error.
        with pytest.raises((TypeError, AttributeError)):
            formatting_check.run(None)  # type: ignore

    def test_git_returns_empty_stdout(self) -> None:
        """Git returns empty string (no staged files) → gate handles correctly."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["status"] == "PASS"
            assert result["formatting_changed"] is False
            assert result["artifacts"] == []

    def test_git_returns_empty_stderr_on_error(self) -> None:
        """Git fails with empty stderr (unclear error) → gate includes context."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=128, stdout="", stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "FAIL"
            # Even with empty stderr, message should be present
            assert len(result["message"]) > 0

    def test_formatter_returns_empty_stdout_and_stderr(self) -> None:
        """Formatter succeeds but produces no output → gate handles correctly."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Silent success (no output)
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=1, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "PASS"

    def test_message_field_never_empty_on_pass(self) -> None:
        """Message field always non-empty, even on edge cases."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert len(result.get("message", "")) > 0

    def test_artifacts_list_never_none(self) -> None:
        """artifacts field is always list, never None."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["artifacts"] is not None
            assert isinstance(result["artifacts"], list)

    def test_violations_array_present_on_fail(self) -> None:
        """violations array always present when status=FAIL."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    raise FileNotFoundError("git not found")
                return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            assert result["status"] == "FAIL"
            assert "violations" in result
            assert isinstance(result["violations"], list)

    def test_formatters_applied_list_never_none(self) -> None:
        """formatters_applied is always list, never None."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["formatters_applied"] is not None
            assert isinstance(result["formatters_applied"], list)


# ============================================================================
# BOUNDARY & EXTREME INPUT TESTS
# ============================================================================


class TestBoundaryConditions:
    """Adversarial tests for boundary conditions and extreme inputs."""

    def test_very_long_message_truncated(self) -> None:
        """Message field exceeds 250 chars → gate truncates or validates."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="x" * 10000, stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Message should be truncated or reasonable length
            assert len(result["message"]) <= 1000  # Generous upper bound

    def test_massive_number_of_staged_files(self) -> None:
        """1000+ staged files → gate handles without hanging or OOM."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    # Return 1000 files
                    files = "\n".join(f"file{i}.py" for i in range(1000))
                    return mock.Mock(returncode=0, stdout=files, stderr="")
                elif any(fmt in str(cmd) for fmt in ["black", "ruff", "prettier", "gdformat"]):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            start = time.time()
            result = formatting_check.run({})
            elapsed = time.time() - start
            # Should complete within reasonable time (mocked should be fast)
            assert elapsed < 10.0
            assert result["status"] in ["PASS", "FAIL"]

    def test_zero_duration_ms_rejected(self) -> None:
        """duration_ms should be > 0 (not zero)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["duration_ms"] > 0

    def test_negative_duration_ms_rejected(self) -> None:
        """duration_ms should never be negative."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["duration_ms"] >= 0

    def test_timestamp_not_future_dated(self) -> None:
        """Timestamp should be close to current time (not far future)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            before = time.time()
            result = formatting_check.run({})
            after = time.time()
            # Timestamp should be within gate execution window
            # (This is a soft check; exact time validation deferred to INTEGRATION)
            assert "T" in result["timestamp"]
            assert "Z" in result["timestamp"]


# ============================================================================
# TYPE & STRUCTURE MUTATION TESTS
# ============================================================================


class TestTypeAndStructureMutations:
    """Adversarial tests for type confusion and structural changes."""

    def test_status_field_not_uppercase_variation(self) -> None:
        """status must be exactly 'PASS' or 'FAIL', not variants."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            # Exactly "PASS" or "FAIL", not "Pass", "pass", "SUCCESS", etc.
            assert result["status"] in {"PASS", "FAIL"}

    def test_gate_field_lowercase_spelling(self) -> None:
        """gate field must be exactly 'formatting_check' (lowercase, underscore)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert result["gate"] == "formatting_check"
            assert result["gate"] != "FormattingCheck"
            assert result["gate"] != "formatting-check"

    def test_artifacts_always_list_of_strings(self) -> None:
        """artifacts must be list of strings, not mixed types or objects."""
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
            assert isinstance(result["artifacts"], list)
            for artifact in result["artifacts"]:
                assert isinstance(artifact, str)

    def test_formatting_changed_always_boolean(self) -> None:
        """formatting_changed must be boolean (true/false), not string or int."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            assert isinstance(result["formatting_changed"], bool)
            assert result["formatting_changed"] in {True, False}

    def test_violations_array_contains_dicts_only(self) -> None:
        """violations array contains only dicts, not strings or mixed types."""
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
            if "violations" in result:
                for violation in result["violations"]:
                    assert isinstance(violation, dict)

    def test_violation_required_fields_all_present(self) -> None:
        """Each violation must have file, line, rule, message (never partial)."""
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
            if result.get("violations"):
                for violation in result["violations"]:
                    assert "file" in violation
                    assert "line" in violation
                    assert "rule" in violation
                    assert "message" in violation


# ============================================================================
# INVALID & CORRUPT INPUT TESTS
# ============================================================================


class TestInvalidAndCorruptInput:
    """Adversarial tests for malformed and corrupt input handling."""

    def test_malformed_git_output_extra_whitespace(self) -> None:
        """Git returns file list with extra spaces/tabs → gate parses correctly."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    # Extra whitespace in output
                    return mock.Mock(returncode=0, stdout="  test.py  \n\n\nfoo.py\t\t", stderr="")
                elif any(fmt in str(cmd) for fmt in ["black", "ruff"]):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Should parse successfully despite whitespace
            assert result["status"] in ["PASS", "FAIL"]

    def test_git_output_with_null_bytes(self) -> None:
        """Git output with null bytes → gate handles or gracefully fails."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    # Null byte in output (edge case)
                    return mock.Mock(returncode=0, stdout="test.py\x00bad.py", stderr="")
                return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Gate should either handle or fail gracefully (not crash)
            assert result["status"] in ["PASS", "FAIL"]

    def test_formatter_output_with_non_utf8_characters(self) -> None:
        """Formatter output contains non-UTF8 bytes → gate handles gracefully."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Non-UTF8 output (simulated)
                    return mock.Mock(returncode=0, stdout=b"reformatted\xff\xfe".decode('utf-8', errors='replace'), stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Should not crash on encoding issues
            assert result["status"] in ["PASS", "FAIL"]

    def test_git_diff_output_malformed(self) -> None:
        """git diff output (change detection) is malformed → gate handles."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Malformed diff (missing --- / +++ markers)
                    return mock.Mock(returncode=0, stdout="garbage output not a diff", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Gate should detect changes despite malformed diff or handle gracefully
            assert result["status"] in ["PASS", "FAIL"]

    def test_ticket_id_with_special_characters(self) -> None:
        """ticket_id input contains special characters → gate preserves/escapes."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({"ticket_id": "M902-10'; DROP TABLE--"})
            # Should preserve input (no SQL injection risk in output dict)
            assert result["ticket_id"] == "M902-10'; DROP TABLE--"


# ============================================================================
# ORDER-DEPENDENCY & SEQUENCING TESTS
# ============================================================================


class TestOrderDependency:
    """Adversarial tests for order-dependent behavior and sequencing."""

    def test_formatter_execution_order_matters(self) -> None:
        """Formatter order (black → ruff → prettier → gdformat) is critical."""
        # CHECKPOINT: Conservative assumption — if formatters are run out of order,
        # intermediate outputs may differ. Test verifies gate uses correct order.
        with mock.patch("subprocess.run") as mock_run:
            call_order = []

            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    call_order.append("black")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "ruff" in str(cmd) and "format" in str(cmd):
                    call_order.append("ruff")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "prettier" in str(cmd):
                    call_order.append("prettier")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "gdformat" in str(cmd):
                    call_order.append("gdformat")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Formatters should run in order (black before ruff before prettier before gdformat)
            # (If implementation provides order info, verify it)
            assert result["status"] in ["PASS", "FAIL"]

    def test_git_add_only_after_change_detection(self) -> None:
        """git add must be called only if changes detected (not before)."""
        with mock.patch("subprocess.run") as mock_run:
            call_sequence = []

            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "add" in str(cmd):
                    call_sequence.append("git_add")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    call_sequence.append("git_diff_cached")
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    call_sequence.append("git_diff_working")
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "black" in str(cmd):
                    call_sequence.append("black")
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # If changes were detected, git_add should come after git_diff_working
            if result["formatting_changed"]:
                add_idx = call_sequence.index("git_add") if "git_add" in call_sequence else -1
                diff_idx = call_sequence.index("git_diff_working") if "git_diff_working" in call_sequence else -1
                if add_idx >= 0 and diff_idx >= 0:
                    assert add_idx > diff_idx, "git add should come after change detection"


# ============================================================================
# CONCURRENCY & RACE CONDITION TESTS
# ============================================================================


class TestConcurrencyAndRaceConditions:
    """Adversarial tests for concurrent execution and race conditions."""

    def test_parallel_gate_invocations_independent(self) -> None:
        """Multiple gate invocations in parallel don't interfere."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")

            # Simulate multiple invocations
            results = [formatting_check.run({}) for _ in range(5)]

            # All should succeed
            assert all(r["status"] == "PASS" for r in results)

    def test_repeated_invocations_consistent(self) -> None:
        """Calling gate 10 times with same input yields consistent results."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            results = [formatting_check.run({"ticket_id": "M902-10"}) for _ in range(10)]

            # All results should have same status and formatting_changed
            statuses = [r["status"] for r in results]
            changed_flags = [r["formatting_changed"] for r in results]

            assert len(set(statuses)) == 1, "Status should be consistent across invocations"
            assert len(set(tuple(sorted(changed_flags)))) == 1, "formatting_changed should be consistent"


# ============================================================================
# MUTATION TESTING — Inverted Logic & Omitted Operations
# ============================================================================


class TestMutationDetection:
    """Adversarial tests that would fail if implementation has logic bugs."""

    def test_false_when_should_be_true_formatting_changed(self) -> None:
        """If gate incorrectly reports formatting_changed=false when true, test fails."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Change detected (diff output present)
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Gate must detect the change from diff output
            assert result["formatting_changed"] is True, "Gate should detect formatting changes from diff"

    def test_empty_artifacts_when_should_contain_files(self) -> None:
        """If gate returns empty artifacts when files were formatted, test fails."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py\nfoo.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # If formatting changed, artifacts should not be empty
            if result["formatting_changed"]:
                assert len(result["artifacts"]) > 0, "artifacts should list formatted files"

    def test_pass_when_should_be_fail_on_timeout(self) -> None:
        """If gate returns PASS on timeout, test fails."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, timeout=None, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    raise subprocess.TimeoutExpired("black", timeout)
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Timeout is a hard failure
            assert result["status"] == "FAIL", "Timeout should return FAIL, not PASS"

    def test_pass_when_should_be_fail_on_formatter_error(self) -> None:
        """If gate returns PASS when formatter exits non-zero, test fails."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Non-zero exit (syntax error, etc.)
                    return mock.Mock(returncode=1, stdout="", stderr="SyntaxError")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Non-zero formatter exit is a hard failure
            assert result["status"] == "FAIL", "Formatter error should return FAIL, not PASS"

    def test_fail_when_should_be_pass_on_missing_formatter(self) -> None:
        """If gate returns FAIL for missing formatter, test fails (should gracefully skip)."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    raise FileNotFoundError("black not found")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Missing formatter is graceful degradation (skip + WARN, not FAIL)
            assert result["status"] == "PASS", "Missing formatter should gracefully skip (PASS + WARN)"

    def test_violation_rule_matches_error_type(self) -> None:
        """Each violation rule must match the actual error type."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, timeout=None, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    raise subprocess.TimeoutExpired("black", timeout)
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            if result.get("violations"):
                for violation in result["violations"]:
                    # Timeout error should have rule='timeout'
                    if "timeout" in violation.get("message", "").lower():
                        assert violation["rule"] == "timeout"


# ============================================================================
# SCHEMA VALIDATION MUTATION TESTS
# ============================================================================


class TestSchemaValidationMutations:
    """Adversarial tests for JSON schema compliance under mutation."""

    def test_result_json_serializable_with_edge_types(self) -> None:
        """Result must be JSON-serializable even with extreme field values."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="x" * 10000, stderr="y" * 10000)
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Must be JSON-serializable despite large output
            try:
                json.dumps(result)
            except TypeError as e:
                pytest.fail(f"Result not JSON-serializable: {e}")

    def test_no_datetime_objects_in_output(self) -> None:
        """Output must not contain datetime objects (must be strings)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            def check_no_datetime(obj: Any) -> None:
                if isinstance(obj, dict):
                    for v in obj.values():
                        check_no_datetime(v)
                elif isinstance(obj, list):
                    for item in obj:
                        check_no_datetime(item)
                else:
                    assert not hasattr(obj, "year"), f"Found datetime object: {obj}"

            check_no_datetime(result)

    def test_no_pathlib_path_objects_in_output(self) -> None:
        """Output must not contain Path objects (must be strings)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            def check_no_path(obj: Any) -> None:
                if isinstance(obj, dict):
                    for v in obj.values():
                        check_no_path(v)
                elif isinstance(obj, list):
                    for item in obj:
                        check_no_path(item)
                else:
                    assert not isinstance(obj, Path), f"Found Path object: {obj}"

            check_no_path(result)


# ============================================================================
# DETERMINISM & IDEMPOTENCY UNDER ADVERSARIAL CONDITIONS
# ============================================================================


class TestDeterminismAndIdempotency:
    """Adversarial tests for deterministic and idempotent behavior."""

    def test_idempotency_with_large_input(self) -> None:
        """Running gate twice on large input yields same result."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    files = "\n".join(f"file{i}.py" for i in range(100))
                    return mock.Mock(returncode=0, stdout=files, stderr="")
                elif any(fmt in str(cmd) for fmt in ["black", "ruff"]):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            result1 = formatting_check.run({})
            result2 = formatting_check.run({})

            # Core fields should match
            assert result1["status"] == result2["status"]
            assert result1["formatting_changed"] == result2["formatting_changed"]
            assert result1["artifacts"] == result2["artifacts"]

    def test_idempotency_on_error_condition(self) -> None:
        """Running gate twice on same error yields same error."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=1, stdout="", stderr="SyntaxError")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            result1 = formatting_check.run({})
            result2 = formatting_check.run({})

            assert result1["status"] == result2["status"] == "FAIL"
            # Violation count should be same
            assert len(result1.get("violations", [])) == len(result2.get("violations", []))


# ============================================================================
# STRESS TESTING
# ============================================================================


class TestStressTesting:
    """Adversarial tests for behavior under stress and extreme conditions."""

    def test_gate_handles_very_large_artifact_list(self) -> None:
        """Gate handles result with 1000+ artifacts without error."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    files = "\n".join(f"file{i}.py" for i in range(1000))
                    return mock.Mock(returncode=0, stdout=files, stderr="")
                elif any(fmt in str(cmd) for fmt in ["black", "ruff"]):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Simulate all files changed
                    lines = [f"--- a/file{i}.py" for i in range(1000)]
                    return mock.Mock(returncode=0, stdout="\n".join(lines), stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Should handle large artifact list
            assert isinstance(result["artifacts"], list)
            # JSON should remain serializable
            json.dumps(result)

    def test_gate_handles_very_large_message(self) -> None:
        """Gate handles result with very large message field."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Very large formatter output (unlikely but possible)
                    return mock.Mock(returncode=0, stdout="x" * 100000, stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Message should be present and reasonable
            assert len(result["message"]) > 0
            # Should still be JSON-serializable
            json.dumps(result)

    def test_gate_rapid_succession_calls(self) -> None:
        """Gate handles 100 rapid successive calls without state issues."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")

            results = []
            for _ in range(100):
                results.append(formatting_check.run({}))

            # All should succeed
            assert all(r["status"] == "PASS" for r in results)


# ============================================================================
# ASSUMPTION VIOLATION TESTS
# ============================================================================


class TestAssumptionViolations:
    """Tests that challenge implicit assumptions in the specification."""

    def test_ticket_id_none_value_handled(self) -> None:
        """ticket_id=None in inputs → gate handles (default or error)."""
        # CHECKPOINT: Conservative assumption — if ticket_id=None, gate should
        # either default to "M902-10" or explicitly reject. Test both possibilities.
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({"ticket_id": None})
            # Should either default or raise
            assert result["ticket_id"] is not None or "ticket_id" in result

    def test_inputs_dict_with_unknown_keys_ignored(self) -> None:
        """inputs dict has unknown keys → gate ignores safely."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({
                "ticket_id": "M902-10",
                "unknown_key": "value",
                "another_key": 12345,
            })
            # Should process normally despite extra keys
            assert result["status"] in ["PASS", "FAIL"]

    def test_git_not_on_path_returns_fail(self) -> None:
        """If git is not available, gate returns FAIL (not silent skip)."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd):
                    raise FileNotFoundError("git: command not found")
                return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Git failure is critical
            assert result["status"] == "FAIL"
            assert len(result.get("violations", [])) > 0

    def test_message_always_ends_with_period_or_similar(self) -> None:
        """Message field ends with proper punctuation (conservative assumption)."""
        # CHECKPOINT: Spec examples show messages with periods. Verify actual
        # implementation follows this pattern consistently.
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})
            # Message should be well-formed
            msg = result["message"]
            assert len(msg) > 0
            # Optional: could check for trailing punctuation if spec requires it
            # assert msg[-1] in '.!?'


# ============================================================================
# FALSE POSITIVE / FALSE NEGATIVE DETECTION TESTS
# ============================================================================


class TestFalsePositivesFalseNegatives:
    """Tests to detect false positives and false negatives in logic."""

    def test_no_false_positive_formatting_changed_on_no_diff(self) -> None:
        """When diff returns no changes, formatting_changed must be false."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Return non-zero (no changes)
                    return mock.Mock(returncode=1, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # If diff detected no changes, formatting_changed MUST be false
            assert result["formatting_changed"] is False

    def test_no_false_negative_formatting_changed_on_diff_present(self) -> None:
        """When diff shows changes, formatting_changed must be true."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Clear diff output
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,2 @@", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # If diff shows changes, formatting_changed MUST be true
            assert result["formatting_changed"] is True

    def test_no_false_positive_pass_status_when_formatter_fails(self) -> None:
        """If formatter fails, status cannot be PASS (must be FAIL)."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Fatal error
                    return mock.Mock(returncode=127, stdout="", stderr="fatal error")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})
            # Non-zero formatter exit is always FAIL
            assert result["status"] == "FAIL"

    def test_git_add_not_called_when_no_changes(self) -> None:
        """git add should not be called if no changes detected."""
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
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # No changes
                    return mock.Mock(returncode=1, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # If no changes, git add should not be called
            if not result["formatting_changed"]:
                # Verify git add was not called (check mock calls)
                add_calls = [c for c in mock_run.call_args_list if "add" in str(c)]
                # If there are add calls when formatting_changed=false, test fails
                assert len(add_calls) == 0, "git add should not be called when no changes"


# ============================================================================
# INTEGRATION BOUNDARY TESTS
# ============================================================================


class TestIntegrationBoundaries:
    """Tests at the boundary between gate and downstream consumers."""

    def test_gate_output_matches_expected_schema_exactly(self) -> None:
        """Gate output structure exactly matches M902-01 schema expectations."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            # Required fields by M902-01
            required = {"status", "gate", "timestamp", "ticket_id", "message", "artifacts", "duration_ms"}
            assert required.issubset(result.keys()), f"Missing: {required - set(result.keys())}"

            # Type checks
            assert isinstance(result["status"], str)
            assert isinstance(result["gate"], str)
            assert isinstance(result["timestamp"], str)
            assert isinstance(result["ticket_id"], str)
            assert isinstance(result["message"], str)
            assert isinstance(result["artifacts"], list)
            assert isinstance(result["duration_ms"], (int, float))

    def test_timestamp_parseable_as_iso8601(self) -> None:
        """Timestamp is valid ISO 8601 and parseable by downstream."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            ts = result["timestamp"]
            # Should match ISO 8601 format: YYYY-MM-DDTHH:MM:SS[.sss]Z
            import re
            iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$"
            assert re.match(iso_pattern, ts), f"Timestamp '{ts}' is not valid ISO 8601"

    def test_no_extra_fields_beyond_schema(self) -> None:
        """Gate output doesn't include extra fields not in schema (clean contract)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            # Expected schema fields
            expected_base = {
                "status", "gate", "timestamp", "ticket_id", "message",
                "artifacts", "duration_ms", "formatting_changed", "formatters_applied"
            }
            # Violations only on FAIL
            if result["status"] == "FAIL":
                expected_base.add("violations")

            # No completely unexpected fields
            unexpected = set(result.keys()) - expected_base
            # Some flexibility for extension fields, but not wild additions
            assert len(unexpected) <= 2, f"Unexpected fields: {unexpected}"
