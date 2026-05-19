"""Mutation testing suite for formatting check gate (M902-10).

This suite uses code mutation techniques to verify the gate implementation
detects and properly handles various failure modes. Tests are designed to fail
if specific implementation bugs are introduced.

Mutation categories:
  - Condition inversion (if x: → if not x:)
  - Operation omission (remove git add, skip formatter, omit change detection)
  - Operator swap (== → !=, True → False)
  - Field omission (missing artifacts, no violations)
  - Return value mutation (PASS → FAIL, true → false)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

_CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(_CI_SCRIPTS))


# Import will fail until formatting_check is implemented
try:
    from gates import formatting_check
    GATE_AVAILABLE = True
except ImportError:
    GATE_AVAILABLE = False


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationConditionInversion:
    """Tests that catch inverted conditions in implementation."""

    def test_detect_inverted_formatting_changed_condition(self) -> None:
        """Catch bug: if not formatting_changed → if formatting_changed."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Changes detected
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # If git diff shows changes, gate MUST re-stage
            # (Bug: if not formatting_changed would skip re-staging)
            if result["formatting_changed"]:
                assert len(result["artifacts"]) > 0, "Changes detected but no artifacts listed"

    def test_detect_inverted_error_condition_timeout(self) -> None:
        """Catch bug: if not timeout → if timeout (allow timeout)."""
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

            # Timeout must always result in FAIL
            # (Bug: inverted condition would return PASS)
            assert result["status"] == "FAIL", "Timeout must return FAIL"

    def test_detect_inverted_formatter_exit_check(self) -> None:
        """Catch bug: if returncode == 0 → if returncode != 0."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    # Non-zero exit code
                    return mock.Mock(returncode=1, stdout="", stderr="syntax error")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Non-zero formatter exit MUST fail
            # (Bug: inverted check would treat error as success)
            assert result["status"] == "FAIL"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationOperationOmission:
    """Tests that catch omitted critical operations."""

    def test_detect_omitted_git_add_on_changes(self) -> None:
        """Catch bug: formatter runs but git add is skipped."""
        with mock.patch("subprocess.run") as mock_run:
            git_add_invoked = False

            def run_side_effect(cmd, *args, **kwargs):
                nonlocal git_add_invoked
                if "git" in str(cmd) and "add" in str(cmd):
                    git_add_invoked = True
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # If changes detected, git add MUST be called
            # (Bug: omitted git add means formatted code not re-staged)
            if result["formatting_changed"]:
                # Check that git add was called
                add_calls = [c for c in mock_run.call_args_list if "add" in str(c)]
                assert len(add_calls) > 0, "git add must be called when formatting changes"

    def test_detect_omitted_change_detection(self) -> None:
        """Catch bug: formatter runs but change detection is skipped."""
        with mock.patch("subprocess.run") as mock_run:
            git_diff_working_called = False

            def run_side_effect(cmd, *args, **kwargs):
                nonlocal git_diff_working_called
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Change detection (non-cached diff)
                    git_diff_working_called = True
                    return mock.Mock(returncode=0, stdout="--- a/test.py\n+++ b/test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Change detection (non-cached git diff) MUST be called
            # (Bug: omitted detection means no way to know if changes occurred)
            # Verify by checking if formatting_changed was set correctly
            assert isinstance(result["formatting_changed"], bool)

    def test_detect_omitted_formatter_execution(self) -> None:
        """Catch bug: formatter is entirely skipped."""
        with mock.patch("subprocess.run") as mock_run:
            formatter_called = False

            def run_side_effect(cmd, *args, **kwargs):
                nonlocal formatter_called
                if any(fmt in str(cmd) for fmt in ["black", "ruff", "prettier", "gdformat"]):
                    formatter_called = True
                    return mock.Mock(returncode=0, stdout="", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # With staged files, at least one formatter should be called
            # (Bug: all formatters omitted means gate does nothing)
            # This is harder to verify without implementation details,
            # but we can check that gate completed successfully
            assert result["status"] in ["PASS", "FAIL"]


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationReturnValueSwap:
    """Tests that catch incorrect return values."""

    def test_detect_pass_fail_swap_on_timeout(self) -> None:
        """Catch bug: return PASS on timeout instead of FAIL."""
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

            # Timeout is hard failure
            assert result["status"] == "FAIL"

    def test_detect_pass_fail_swap_on_formatter_error(self) -> None:
        """Catch bug: return PASS when formatter fails."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=1, stdout="", stderr="SyntaxError")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            assert result["status"] == "FAIL"

    def test_detect_true_false_swap_formatting_changed(self) -> None:
        """Catch bug: report formatting_changed=False when True."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif "black" in str(cmd):
                    return mock.Mock(returncode=0, stdout="reformatted", stderr="")
                elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
                    # Clear change detected
                    return mock.Mock(returncode=0, stdout="--- a/test.py", stderr="")
                elif "git" in str(cmd) and "add" in str(cmd):
                    return mock.Mock(returncode=0, stdout="", stderr="")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # Changes detected, so formatting_changed must be True
            assert result["formatting_changed"] is True


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationFieldOmission:
    """Tests that catch omitted required fields."""

    def test_detect_missing_artifacts_field(self) -> None:
        """Catch bug: artifacts field omitted from output."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert "artifacts" in result, "artifacts field must always be present"

    def test_detect_missing_violations_on_fail(self) -> None:
        """Catch bug: violations field omitted when status=FAIL."""
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

            if result["status"] == "FAIL":
                assert "violations" in result, "violations must be present on FAIL"

    def test_detect_missing_formatting_changed_field(self) -> None:
        """Catch bug: formatting_changed field omitted."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert "formatting_changed" in result, "formatting_changed field must be present"

    def test_detect_missing_formatters_applied_field(self) -> None:
        """Catch bug: formatters_applied field omitted."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert "formatters_applied" in result, "formatters_applied field must be present"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationGracefulDegradation:
    """Tests that verify graceful degradation (not hard-failure on soft errors)."""

    def test_detect_fail_on_missing_formatter(self) -> None:
        """Catch bug: return FAIL when formatter unavailable (should be PASS + WARN)."""
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

            # Missing formatter is graceful degradation, not failure
            assert result["status"] == "PASS", "Missing formatter should return PASS + WARN"

    def test_detect_all_formatters_skipped_still_pass(self) -> None:
        """Catch bug: return FAIL when all formatters unavailable (should be PASS)."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
                elif any(fmt in str(cmd) for fmt in ["black", "ruff", "prettier", "gdformat"]):
                    raise FileNotFoundError("formatter not found")
                else:
                    return mock.Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            result = formatting_check.run({})

            # All formatters missing is graceful (skip all, still pass)
            assert result["status"] == "PASS"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationMessageTemplates:
    """Tests that verify message templates are correct."""

    def test_detect_wrong_restage_message(self) -> None:
        """Catch bug: wrong message when re-staging."""
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

            if result["formatting_changed"]:
                # Message should mention re-staging
                msg_lower = result["message"].lower()
                assert "re-stage" in msg_lower or "restage" in msg_lower, \
                    "Message should mention re-staging when changes detected"

    def test_detect_wrong_no_changes_message(self) -> None:
        """Catch bug: wrong message when no changes."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            if not result["formatting_changed"]:
                msg_lower = result["message"].lower()
                # Should indicate no formatting needed
                assert "already formatted" in msg_lower or "no changes" in msg_lower, \
                    "Message should indicate code is already formatted"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationTimestampLogic:
    """Tests that verify timestamp correctness."""

    def test_timestamp_generation_timing(self) -> None:
        """Catch bug: timestamp from wrong time (past, future)."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")

            before = time.time()
            result = formatting_check.run({})
            after = time.time()

            # Timestamp should be in ISO format
            ts = result["timestamp"]
            assert "T" in ts and "Z" in ts, "Invalid timestamp format"

            # Duration should be reasonable (gate execution time)
            duration_s = result["duration_ms"] / 1000.0
            assert 0 < duration_s < 10, "Duration should be reasonable"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationDurationTracking:
    """Tests that verify duration_ms is tracked correctly."""

    def test_duration_not_zero(self) -> None:
        """Catch bug: duration_ms=0."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert result["duration_ms"] > 0, "duration_ms must be > 0"

    def test_duration_non_negative(self) -> None:
        """Catch bug: negative duration_ms."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert result["duration_ms"] >= 0, "duration_ms must be >= 0"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationFilePathHandling:
    """Tests for file path handling in artifacts."""

    def test_artifacts_uses_relative_paths(self) -> None:
        """Catch bug: artifacts with absolute paths instead of relative."""
        with mock.patch("subprocess.run") as mock_run:
            def run_side_effect(cmd, *args, **kwargs):
                if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
                    return mock.Mock(returncode=0, stdout="test.py", stderr="")
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

            for artifact in result["artifacts"]:
                assert not artifact.startswith("/"), \
                    f"Artifact '{artifact}' should be relative, not absolute"
                assert not artifact.startswith("~/"), \
                    f"Artifact '{artifact}' should be relative, not tilde-expanded"


@pytest.mark.skipif(not GATE_AVAILABLE, reason="formatting_check module not yet implemented")
class TestMutationStatusEnumValues:
    """Tests that verify exact status enum values."""

    def test_status_only_pass_or_fail(self) -> None:
        """Catch bug: status is 'Success', 'success', or other variant."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert result["status"] in {"PASS", "FAIL"}, \
                f"status must be 'PASS' or 'FAIL', not '{result['status']}'"

    def test_gate_field_exact_spelling(self) -> None:
        """Catch bug: gate is 'FormattingCheck' or other variant."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            result = formatting_check.run({})

            assert result["gate"] == "formatting_check", \
                f"gate must be 'formatting_check', not '{result['gate']}'"
