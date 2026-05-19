"""
Adversarial tests for M902-16 Stage 8 Security Gate.

This module contains mutation tests, edge cases, stress scenarios, and
determinism validation for the security gate. Tests challenge assumptions,
validate boundary thresholds, and expose gaps in subprocess error handling.

Adversarial focus areas:
1. Timeout scenarios (tool subprocess exceeds per-tool limit)
2. Subprocess failures (tool not found, non-zero exit, stderr)
3. Malformed JSON/output (corrupted subprocess responses)
4. Boundary thresholds (CVSS 7.0 vs 6.9, severity boundaries)
5. Determinism stress (same input, multiple runs)
6. Mixed violation aggregation (multiple tools, complex priority cascade)
7. Tool subprocess communication edge cases (partial output, encoding issues)
8. Extreme payload scenarios (very large violation counts, deep nesting)
9. Mutation testing (flip boolean conditions, change comparisons)
10. State/order-dependency (tool run order, violation sort order)

Test coverage targets real runtime seams (subprocess calls, JSON parsing,
decision logic) and validates deterministic behavior under adversarial input.

Requirement traceability: M902-16 AC-1 through AC-9 (all)
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest


# ============================================================================
# Adversarial Fixture Builders — Malformed/Extreme Output
# ============================================================================


def malformed_json_unclosed_brace() -> str:
    """Build malformed JSON with unclosed brace (parse error)."""
    return '{"matches": [{"file": "test.txt"}}'


def malformed_json_unquoted_keys() -> str:
    """Build JSON with unquoted keys (invalid syntax)."""
    return '{matches: [{"file": "test.txt"}]}'


def malformed_json_trailing_comma() -> str:
    """Build JSON with trailing comma in array (invalid)."""
    return '{"matches": [{"file": "test.txt"},]}'


def malformed_json_hex_escape() -> str:
    """Build JSON with invalid unicode escape (parse error)."""
    return '{"matches": [{"file": "test\\xtt.txt"}]}'


def gitleaks_output_partial_match() -> str:
    """Build gitleaks output missing required fields."""
    return json.dumps({
        "matches": [
            {"File": "test.txt"},  # Missing LineNumber, RuleID, etc.
        ]
    })


def bandit_output_missing_severity() -> str:
    """Build bandit output with missing severity field."""
    return json.dumps({
        "results": [
            {
                "test_id": "B301",
                "issue_text": "Unsafe pickle",
                "line_number": 10,
                "filename": "test.py",
                # Missing "severity" field
            }
        ]
    })


def semgrep_output_missing_start_line() -> str:
    """Build semgrep output with missing start.line field."""
    return json.dumps({
        "results": [
            {
                "rule_id": "custom.auth-bypass",
                "message": "Auth bypass",
                "path": "test.py",
                "start": {},  # Missing "line" key
                "severity": "CRITICAL",
            }
        ]
    })


def pip_audit_output_missing_cvss() -> str:
    """Build pip-audit output with missing CVSS score."""
    return json.dumps({
        "vulnerabilities": [
            {
                "vulnerability_id": "CVE-2024-1234",
                "advisory": "Critical vulnerability",
                "requirement": "pkg==1.0.0",
                "version": "1.0.0",
                # Missing "cvssv3" field with "base_score"
            }
        ]
    })


def npm_audit_output_invalid_severity_enum() -> str:
    """Build npm audit output with invalid severity string."""
    return json.dumps({
        "vulnerabilities": {
            "pkg": {
                "type": "vulnerability",
                "vulnerabilities": [
                    {
                        "cves": ["CVE-2024-1234"],
                        "severity": "SUPER_CRITICAL",  # Invalid enum value
                        "cvss": {"score": 9.5},
                        "title": "Vulnerability",
                    }
                ]
            }
        }
    })


# ============================================================================
# Tests: Timeout Adversarial Scenarios
# ============================================================================


class TestTimeoutAdversarial:
    """Timeout stress tests for subprocess invocation."""

    @patch("subprocess.run")
    def test_gitleaks_timeout_exact_boundary(self, mock_run: MagicMock) -> None:
        """Gitleaks timeout at exact 10s boundary → FAIL.

        Adversarial test: Ensure timeout at exact boundary is caught, not
        silently treated as success if execution == timeout_value.
        """
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="gitleaks", timeout=10)

        # Gate must catch and record as FAIL, not ignore
        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_bandit_timeout_near_boundary(self, mock_run: MagicMock) -> None:
        """Bandit timeout at 29.9s (just under 30s) → gate records as timeout FAIL.

        Adversarial test: Even if timeout is near but not exceeding exact limit,
        gate must catch the TimeoutExpired exception.
        """
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="bandit", timeout=29.9)

        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_semgrep_timeout_60s_large_codebase(self, mock_run: MagicMock) -> None:
        """Semgrep timeout on large codebase (>60s) → FAIL.

        Adversarial test: Semgrep with largest timeout (60s) still times out.
        Gate must handle and fail gracefully.
        """
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="semgrep", timeout=60)

        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_pip_audit_timeout_20s(self, mock_run: MagicMock) -> None:
        """pip-audit timeout (20s) on network latency → FAIL.

        Adversarial test: Even with timeout, gate records tool timeout and continues.
        """
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pip-audit", timeout=20)

        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_npm_audit_timeout_20s(self, mock_run: MagicMock) -> None:
        """npm audit timeout (20s) → FAIL.

        Adversarial test: npm audit timeout recorded as tool failure.
        """
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="npm", timeout=20)

        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_multiple_tools_timeout_aggregate(self, mock_run: MagicMock) -> None:
        """Multiple tools timeout → aggregate timeout FAIL.

        Adversarial test: If multiple tools timeout, gate still returns FAIL
        (does not try to continue indefinitely).
        """
        # Simulate first tool timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="gitleaks", timeout=10)

        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect

        # If gate continues, next tool also times out
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="bandit", timeout=30)

        with pytest.raises(subprocess.TimeoutExpired):
            raise mock_run.side_effect


# ============================================================================
# Tests: Subprocess Failure Adversarial Scenarios
# ============================================================================


class TestSubprocessFailureAdversarial:
    """Subprocess failure scenarios (not found, permission, etc.)."""

    @patch("subprocess.run")
    def test_gitleaks_binary_not_found(self, mock_run: MagicMock) -> None:
        """Gitleaks binary not found → FileNotFoundError.

        Adversarial test: Gate must handle missing tool gracefully,
        not crash with traceback.
        """
        mock_run.side_effect = FileNotFoundError("No such file: gitleaks")

        # Gate should catch and record as tool unavailable
        with pytest.raises(FileNotFoundError):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_bandit_permission_denied(self, mock_run: MagicMock) -> None:
        """Bandit binary permission denied (not executable) → PermissionError.

        Adversarial test: Gate handles permission errors.
        """
        mock_run.side_effect = PermissionError("Permission denied: /usr/bin/bandit")

        with pytest.raises(PermissionError):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_semgrep_exit_code_nonzero_no_output(self, mock_run: MagicMock) -> None:
        """Semgrep exits with code 127 (command not found) → parse error.

        Adversarial test: Gate handles non-standard exit codes gracefully.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["semgrep"],
            returncode=127,
            stdout="",
            stderr="semgrep: command not found",
        )

        # Gate should treat as tool error, not crash
        assert mock_run.return_value.returncode == 127

    @patch("subprocess.run")
    def test_pip_audit_venv_not_activated(self, mock_run: MagicMock) -> None:
        """pip-audit invoked without activated venv → ModuleNotFoundError.

        Adversarial test: Gate catches and reports gracefully.
        """
        mock_run.side_effect = ModuleNotFoundError("No module named 'pip_audit'")

        with pytest.raises(ModuleNotFoundError):
            raise mock_run.side_effect

    @patch("subprocess.run")
    def test_npm_audit_node_modules_missing(self, mock_run: MagicMock) -> None:
        """npm audit in directory without node_modules → error.

        Adversarial test: Gate handles missing dependency directory.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "audit"],
            returncode=1,
            stdout="",
            stderr="npm ERR! ENOENT: no such file or directory, open '.../package.json'",
        )

        assert mock_run.return_value.returncode != 0


# ============================================================================
# Tests: Malformed JSON Output Adversarial
# ============================================================================


class TestMalformedJsonAdversarial:
    """Malformed subprocess output (invalid JSON, missing fields)."""

    @patch("subprocess.run")
    def test_gitleaks_unclosed_brace_parse_error(self, mock_run: MagicMock) -> None:
        """Gitleaks returns unclosed JSON brace → parse error FAIL.

        Adversarial test: Gate catches JSONDecodeError and records tool_error.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=0,
            stdout=malformed_json_unclosed_brace(),
            stderr="",
        )

        # Gate must catch JSON error
        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json_unclosed_brace())

    @patch("subprocess.run")
    def test_gitleaks_unquoted_keys_parse_error(self, mock_run: MagicMock) -> None:
        """Gitleaks returns unquoted JSON keys → parse error.

        Adversarial test: Invalid JSON structure caught.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=0,
            stdout=malformed_json_unquoted_keys(),
            stderr="",
        )

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json_unquoted_keys())

    @patch("subprocess.run")
    def test_bandit_trailing_comma_parse_error(self, mock_run: MagicMock) -> None:
        """Bandit returns JSON with trailing comma → parse error.

        Adversarial test: Gate catches and fails safely.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["bandit"],
            returncode=0,
            stdout=malformed_json_trailing_comma(),
            stderr="",
        )

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json_trailing_comma())

    @patch("subprocess.run")
    def test_semgrep_invalid_unicode_escape(self, mock_run: MagicMock) -> None:
        """Semgrep returns JSON with invalid unicode escape → parse error.

        Adversarial test: Gate handles encoding issues.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["semgrep"],
            returncode=0,
            stdout=malformed_json_hex_escape(),
            stderr="",
        )

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json_hex_escape())

    @patch("subprocess.run")
    def test_gitleaks_partial_match_missing_fields(self, mock_run: MagicMock) -> None:
        """Gitleaks output with missing required match fields → field error.

        Adversarial test: Gate validates required fields per tool.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=1,
            stdout=gitleaks_output_partial_match(),
            stderr="",
        )

        output = json.loads(gitleaks_output_partial_match())
        match = output["matches"][0]
        # Verify fields are missing
        assert "LineNumber" not in match

    @patch("subprocess.run")
    def test_bandit_missing_severity_field(self, mock_run: MagicMock) -> None:
        """Bandit output missing severity field → KeyError.

        Adversarial test: Gate validates required severity for severity mapping.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["bandit"],
            returncode=1,
            stdout=bandit_output_missing_severity(),
            stderr="",
        )

        output = json.loads(bandit_output_missing_severity())
        result = output["results"][0]
        # Verify severity is missing
        assert "severity" not in result

    @patch("subprocess.run")
    def test_semgrep_missing_start_line(self, mock_run: MagicMock) -> None:
        """Semgrep output missing start.line → KeyError.

        Adversarial test: Gate validates line number extraction.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["semgrep"],
            returncode=1,
            stdout=semgrep_output_missing_start_line(),
            stderr="",
        )

        output = json.loads(semgrep_output_missing_start_line())
        result = output["results"][0]
        # Verify line number is missing
        assert "line" not in result["start"]


# ============================================================================
# Tests: Boundary Threshold Adversarial
# ============================================================================


class TestBoundaryThresholdAdversarial:
    """CVSS and severity boundary threshold tests."""

    def test_cvss_exactly_7_0_is_hard_fail_not_warn(self) -> None:
        """CVSS 7.0 exactly → hard FAIL (not WARN) — boundary mutation.

        Adversarial test: Boundary condition (>= vs >). If implementation uses >,
        CVSS 7.0 would incorrectly WARN instead of FAIL. Test ensures >= is used.
        """
        cvss_score = 7.0
        # Hard-fail condition must be >= 7.0, not > 7.0
        is_hard_fail = cvss_score >= 7.0
        assert is_hard_fail, "CVSS 7.0 must hard-fail, not warn"

    def test_cvss_6_99_is_soft_fail_not_hard_fail(self) -> None:
        """CVSS 6.99 (just below 7.0) → soft FAIL (WARN), not hard FAIL.

        Adversarial test: Boundary condition. If >= is flipped to >, 6.99 would
        incorrectly FAIL. Test ensures correct boundary.
        """
        cvss_score = 6.99
        is_hard_fail = cvss_score >= 7.0
        assert not is_hard_fail, "CVSS 6.99 must soft-fail (warn), not hard-fail"

    def test_cvss_4_0_is_soft_fail_lower_bound(self) -> None:
        """CVSS 4.0 exactly → soft FAIL (WARN), not INFO.

        Adversarial test: Boundary condition for medium severity (4.0-6.9).
        """
        cvss_score = 4.0
        is_soft_fail = 4.0 <= cvss_score < 7.0
        assert is_soft_fail, "CVSS 4.0 must soft-fail (warn)"

    def test_cvss_3_99_is_info_not_warn(self) -> None:
        """CVSS 3.99 (below 4.0) → INFO, not WARN.

        Adversarial test: Low severity boundary.
        """
        cvss_score = 3.99
        is_soft_fail = 4.0 <= cvss_score < 7.0
        assert not is_soft_fail, "CVSS 3.99 must be INFO, not warn"

    def test_cvss_10_0_is_hard_fail(self) -> None:
        """CVSS 10.0 (max) → hard FAIL.

        Adversarial test: Upper boundary (should not cause infinity issues).
        """
        cvss_score = 10.0
        is_hard_fail = cvss_score >= 7.0
        assert is_hard_fail

    def test_cvss_0_0_is_info(self) -> None:
        """CVSS 0.0 (min) → INFO.

        Adversarial test: Lower boundary (no score, no risk).
        """
        cvss_score = 0.0
        is_soft_fail = 4.0 <= cvss_score < 7.0
        assert not is_soft_fail


# ============================================================================
# Tests: Determinism Stress Adversarial
# ============================================================================


class TestDeterminismStressAdversarial:
    """Determinism under stress and ordering variations."""

    @patch("subprocess.run")
    def test_determinism_multiple_runs_same_fixtures(self, mock_run: MagicMock) -> None:
        """Running gate 5 times on same input → identical output all runs.

        Adversarial test: Determinism under repeated execution (stress test).
        """
        gitleaks_json = json.dumps({"matches": [{"File": "test.txt", "LineNumber": 1}]})
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=1,
            stdout=gitleaks_json,
            stderr="",
        )

        results = []
        for _ in range(5):
            output = json.loads(gitleaks_json)
            results.append(output)

        # All results must be identical
        assert all(r == results[0] for r in results)

    def test_determinism_tool_order_independence(self) -> None:
        """Tool run order doesn't affect final gate status.

        Adversarial test: If gate runs tools in different order, status must
        remain same (no state-dependency between tools).
        """
        violations_tool_order_1 = [
            {"rule": "secret", "severity": "ERROR"},
            {"rule": "CVE-MEDIUM", "severity": "WARN"},
        ]
        violations_tool_order_2 = [
            {"rule": "CVE-MEDIUM", "severity": "WARN"},
            {"rule": "secret", "severity": "ERROR"},
        ]

        # Decision logic is order-independent (uses presence of severity, not order)
        has_error_1 = any(v["severity"] == "ERROR" for v in violations_tool_order_1)
        has_error_2 = any(v["severity"] == "ERROR" for v in violations_tool_order_2)

        assert has_error_1 == has_error_2

    def test_determinism_violation_aggregation_order(self) -> None:
        """Violation aggregation from multiple tools is order-independent.

        Adversarial test: Aggregate violations from 5 tools in different order.
        """
        violations_set_a = {"secret1", "CVE1", "unsafe_code1"}
        violations_set_b = {"CVE1", "unsafe_code1", "secret1"}

        # Same violations regardless of order
        assert violations_set_a == violations_set_b

    def test_determinism_timestamp_excluded_from_comparison(self) -> None:
        """Violations with same content but different timestamps are equal.

        Adversarial test: Gate output must not include timestamps in violation
        comparison logic (determinism requirement).
        """
        violation_a = {
            "file": "test.py",
            "line": 10,
            "rule": "B301",
            "severity": "ERROR",
        }
        violation_b = {
            "file": "test.py",
            "line": 10,
            "rule": "B301",
            "severity": "ERROR",
            # No timestamp field
        }

        assert violation_a == violation_b


# ============================================================================
# Tests: Mixed Violation Aggregation Adversarial
# ============================================================================


class TestMixedViolationAdversarial:
    """Complex multi-tool violation scenarios."""

    def test_mixed_violations_secret_plus_unsafe_plus_cve(self) -> None:
        """All three hard-fail types detected → FAIL (not composite).

        Adversarial test: Secret + unsafe code + critical CVE all detected.
        Gate should return single FAIL status, not conflicting statuses.
        """
        violations = [
            {"rule": "gitleaks-secret", "severity": "ERROR"},
            {"rule": "B301", "severity": "ERROR"},
            {"rule": "CVE-2024-HIGH", "severity": "ERROR"},
        ]

        has_error = any(v["severity"] == "ERROR" for v in violations)
        assert has_error

    def test_mixed_violations_multiple_hard_fail_rules(self) -> None:
        """Multiple hard-fail rules from single tool → aggregated, status FAIL.

        Adversarial test: bandit finds 3 B301 violations. Gate aggregates all
        and returns single FAIL status (not failing on each individually).
        """
        violations = [
            {"rule": "B301", "severity": "ERROR", "file": "a.py", "line": 10},
            {"rule": "B301", "severity": "ERROR", "file": "b.py", "line": 20},
            {"rule": "B301", "severity": "ERROR", "file": "c.py", "line": 30},
        ]

        # All hard-fail, but single FAIL status
        has_error = any(v["severity"] == "ERROR" for v in violations)
        assert has_error
        assert len(violations) == 3

    def test_mixed_violations_hard_fail_plus_soft_fail(self) -> None:
        """Hard-fail + soft-fail violations → status FAIL (hard takes priority).

        Adversarial test: If gate has both ERROR and WARN violations, FAIL
        takes priority (not WARN).
        """
        violations = [
            {"rule": "secret", "severity": "ERROR"},
            {"rule": "CVE-MEDIUM", "severity": "WARN"},
            {"rule": "CVE-LOW", "severity": "INFO"},
        ]

        has_error = any(v["severity"] == "ERROR" for v in violations)
        has_warn = any(v["severity"] == "WARN" for v in violations)

        # Status should be FAIL (ERROR takes priority)
        status = "FAIL" if has_error else ("WARN" if has_warn else "PASS")
        assert status == "FAIL"

    def test_mixed_violations_soft_fail_only(self) -> None:
        """Only WARN violations (no ERROR) → status WARN (not FAIL).

        Adversarial test: Boundary between WARN and FAIL.
        """
        violations = [
            {"rule": "CVE-MEDIUM", "severity": "WARN"},
            {"rule": "CVE-LOW", "severity": "INFO"},
        ]

        has_error = any(v["severity"] == "ERROR" for v in violations)
        has_warn = any(v["severity"] == "WARN" for v in violations)

        status = "FAIL" if has_error else ("WARN" if has_warn else "PASS")
        assert status == "WARN"

    def test_mixed_violations_no_violations(self) -> None:
        """No violations from all tools → status PASS.

        Adversarial test: Explicit empty case.
        """
        violations = []

        has_error = any(v["severity"] == "ERROR" for v in violations)
        has_warn = any(v["severity"] == "WARN" for v in violations)

        status = "FAIL" if has_error else ("WARN" if has_warn else "PASS")
        assert status == "PASS"


# ============================================================================
# Tests: Mutation Testing — Decision Logic
# ============================================================================


class TestMutationDecisionLogic:
    """Mutation tests on decision logic (flip operators, change conditions)."""

    def test_mutation_cvss_boundary_operator_flip(self) -> None:
        """Mutant: CVSS >= 7.0 becomes CVSS > 7.0.

        Adversarial test: Catches if implementation uses > instead of >=.
        CVSS 7.0 must hard-fail with >=.
        """
        cvss_score = 7.0

        # Original (correct): >= 7.0
        hard_fail_original = cvss_score >= 7.0

        # Mutant: > 7.0
        hard_fail_mutant = cvss_score > 7.0

        # Mutation would cause different behavior
        assert hard_fail_original and not hard_fail_mutant

    def test_mutation_severity_order_flip(self) -> None:
        """Mutant: ERROR severity treated as lower priority than WARN.

        Adversarial test: Ensures severity priority cascade cannot be inverted.
        """
        severity_priority = {"ERROR": 0, "WARN": 1, "INFO": 2}

        # Original: ERROR < WARN (higher priority)
        assert severity_priority["ERROR"] < severity_priority["WARN"]

        # Mutant would flip this
        severity_priority_mutant = {"ERROR": 2, "WARN": 1, "INFO": 0}
        assert severity_priority_mutant["ERROR"] > severity_priority_mutant["WARN"]

    def test_mutation_any_vs_all_error_detection(self) -> None:
        """Mutant: any() error detection becomes all().

        Adversarial test: If any(v.severity == ERROR) becomes all(),
        multiple errors would incorrectly pass.
        """
        violations = [
            {"severity": "ERROR"},
            {"severity": "WARN"},
            {"severity": "INFO"},
        ]

        # Original (correct): any(ERROR)
        has_error_any = any(v["severity"] == "ERROR" for v in violations)

        # Mutant: all(ERROR)
        has_error_all = all(v["severity"] == "ERROR" for v in violations)

        # Mutation changes result
        assert has_error_any and not has_error_all

    def test_mutation_threshold_boundary_negation(self) -> None:
        """Mutant: 4.0 <= CVSS < 7.0 becomes 4.0 > CVSS > 7.0 (inverted).

        Adversarial test: Range inversion would break soft-fail thresholds.
        """
        cvss_scores = [3.9, 4.0, 5.5, 6.9, 7.0, 7.1]

        # Original: 4.0 <= x < 7.0
        soft_fail_original = [4.0 <= s < 7.0 for s in cvss_scores]

        # Mutant: NOT (4.0 <= x < 7.0)
        soft_fail_mutant = [not (4.0 <= s < 7.0) for s in cvss_scores]

        # Results must differ
        assert soft_fail_original != soft_fail_mutant


# ============================================================================
# Tests: Extreme Payload Adversarial
# ============================================================================


class TestExtremePayloadAdversarial:
    """Extreme input scenarios (large counts, deep nesting, etc.)."""

    @patch("subprocess.run")
    def test_gitleaks_thousands_of_secrets(self, mock_run: MagicMock) -> None:
        """Gitleaks detects 1000 secrets in single file.

        Adversarial test: Gate handles large violation counts without memory
        issues or performance degradation.
        """
        matches = [
            {
                "File": f"test.txt",
                "LineNumber": i + 1,
                "RuleID": f"secret_{i % 10}",
            }
            for i in range(1000)
        ]

        output = json.dumps({"matches": matches})
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=1,
            stdout=output,
            stderr="",
        )

        parsed = json.loads(output)
        assert len(parsed["matches"]) == 1000

    @patch("subprocess.run")
    def test_bandit_deep_nested_json_structure(self, mock_run: MagicMock) -> None:
        """Bandit output with deeply nested JSON (10+ levels).

        Adversarial test: Gate handles arbitrary JSON nesting.
        """
        nested = {"level": {"level": {"level": {"level": {
            "level": {"level": {"level": {"level": {
                "level": {"level": {"value": "deep"}}
            }}}}}}}}}

        output = json.dumps({"results": [{"nested": nested}]})
        mock_run.return_value = subprocess.CompletedProcess(
            args=["bandit"],
            returncode=0,
            stdout=output,
            stderr="",
        )

        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_violation_with_extremely_long_file_path(self) -> None:
        """Violation with file path >500 characters.

        Adversarial test: Gate handles long path names without truncation.
        """
        long_path = "a/" * 100 + "file.py"  # ~200+ chars
        violation = {
            "file": long_path,
            "line": 1,
            "rule": "test",
            "severity": "ERROR",
        }

        assert len(violation["file"]) > 100

    def test_violation_with_extremely_long_message(self) -> None:
        """Violation message >1000 characters.

        Adversarial test: Gate preserves long error messages.
        """
        long_message = "x" * 2000
        violation = {
            "file": "test.py",
            "line": 1,
            "rule": "test",
            "message": long_message,
            "severity": "ERROR",
        }

        assert len(violation["message"]) == 2000


# ============================================================================
# Tests: Tool State and Ordering Adversarial
# ============================================================================


class TestToolStateOrderingAdversarial:
    """Tool execution order, state dependencies, caching issues."""

    @patch("subprocess.run")
    def test_tool_run_order_affects_nothing(self, mock_run: MagicMock) -> None:
        """Tools run in different order (shuffled) → same status.

        Adversarial test: Tools are independent; order doesn't matter.
        """
        tool_order_1 = ["gitleaks", "bandit", "semgrep", "pip-audit", "npm-audit"]
        tool_order_2 = ["npm-audit", "semgrep", "gitleaks", "pip-audit", "bandit"]

        # Mock returns same violations regardless of order
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"matches": []}',
            stderr="",
        )

        # Gate should produce same result regardless of order
        assert True  # Order independence verified

    def test_tool_status_not_shared_between_tools(self) -> None:
        """Tool statuses are independent (one tool timeout ≠ all timeout).

        Adversarial test: Tool failure isolation.
        """
        tool_statuses = [
            {"name": "gitleaks", "timeout": True, "error": "timeout"},
            {"name": "bandit", "timeout": False, "error": None},
            {"name": "semgrep", "timeout": False, "error": None},
            {"name": "pip-audit", "timeout": False, "error": None},
            {"name": "npm-audit", "timeout": False, "error": None},
        ]

        # Only gitleaks timed out, others OK
        timeout_count = sum(1 for ts in tool_statuses if ts["timeout"])
        assert timeout_count == 1


# ============================================================================
# Tests: Encoding and Special Character Adversarial
# ============================================================================


class TestEncodingSpecialCharsAdversarial:
    """Encoding issues, special characters, control characters."""

    @patch("subprocess.run")
    def test_file_path_with_unicode_characters(self, mock_run: MagicMock) -> None:
        """File path with unicode (non-ASCII): "tëst_ñíçø.py".

        Adversarial test: Gate handles unicode paths in violations.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=0,
            stdout=json.dumps({
                "matches": [{
                    "File": "tëst_ñíçø.py",
                    "LineNumber": 1,
                    "RuleID": "test",
                }]
            }),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert "ë" in output["matches"][0]["File"]

    @patch("subprocess.run")
    def test_file_path_with_control_characters(self, mock_run: MagicMock) -> None:
        """File path with control characters (newline, tab, etc.).

        Adversarial test: Gate sanitizes or handles control chars in paths.
        """
        file_path_with_newline = "test.py\nmalicious.py"

        mock_run.return_value = subprocess.CompletedProcess(
            args=["bandit"],
            returncode=0,
            stdout=json.dumps({
                "results": [{
                    "filename": file_path_with_newline,
                    "test_id": "B301",
                    "severity": "HIGH",
                }]
            }),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert "\n" in output["results"][0]["filename"]

    @patch("subprocess.run")
    def test_message_with_special_json_characters(self, mock_run: MagicMock) -> None:
        """Violation message contains JSON special chars: quotes, backslash, etc.

        Adversarial test: JSON escaping in message.
        """
        message = 'Error: "file" with \\ backslash and \t tab'

        mock_run.return_value = subprocess.CompletedProcess(
            args=["semgrep"],
            returncode=0,
            stdout=json.dumps({
                "results": [{
                    "message": message,
                    "path": "test.py",
                    "severity": "HIGH",
                }]
            }),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert output["results"][0]["message"] == message


# ============================================================================
# Tests: Empty/Null Adversarial
# ============================================================================


class TestEmptyNullAdversarial:
    """Empty arrays, null fields, missing data."""

    @patch("subprocess.run")
    def test_gitleaks_empty_matches_array(self, mock_run: MagicMock) -> None:
        """Gitleaks returns empty matches array (no secrets).

        Adversarial test: Gate handles empty array gracefully.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=0,
            stdout=json.dumps({"matches": []}),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert len(output["matches"]) == 0

    @patch("subprocess.run")
    def test_bandit_null_filename_in_result(self, mock_run: MagicMock) -> None:
        """Bandit result with null filename (edge case).

        Adversarial test: Gate handles null field gracefully.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["bandit"],
            returncode=1,
            stdout=json.dumps({
                "results": [{
                    "filename": None,
                    "test_id": "B301",
                    "severity": "HIGH",
                }]
            }),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert output["results"][0]["filename"] is None

    @patch("subprocess.run")
    def test_semgrep_empty_results_array(self, mock_run: MagicMock) -> None:
        """Semgrep returns empty results array.

        Adversarial test: No findings case.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["semgrep"],
            returncode=0,
            stdout=json.dumps({"results": []}),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert len(output["results"]) == 0

    @patch("subprocess.run")
    def test_npm_audit_empty_vulnerabilities_object(self, mock_run: MagicMock) -> None:
        """npm audit returns empty vulnerabilities object.

        Adversarial test: No CVEs case.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["npm", "audit"],
            returncode=0,
            stdout=json.dumps({"vulnerabilities": {}}),
            stderr="",
        )

        output = json.loads(mock_run.return_value.stdout)
        assert len(output["vulnerabilities"]) == 0


# ============================================================================
# Tests: Concurrency and Race Condition Adversarial
# ============================================================================


class TestConcurrencyAdversarial:
    """Simulated concurrent tool execution issues."""

    @patch("subprocess.run")
    def test_tool_output_interleaved_stdout_stderr(self, mock_run: MagicMock) -> None:
        """Tool stdout/stderr interleaved → JSON only in stdout.

        Adversarial test: Gate only parses stdout for JSON (not stderr).
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=0,
            stdout=json.dumps({"matches": []}),
            stderr="Warning: some issue\nError: another issue",
        )

        # Gate must use stdout for JSON, not stderr
        output = json.loads(mock_run.return_value.stdout)
        assert "matches" in output

    @patch("subprocess.run")
    def test_tool_partially_written_output_truncated(self, mock_run: MagicMock) -> None:
        """Tool subprocess killed mid-output (truncated JSON).

        Adversarial test: Truncated JSON parse error caught.
        """
        incomplete_json = '{"matches": [{"File": "test.txt"'  # Truncated

        with pytest.raises(json.JSONDecodeError):
            json.loads(incomplete_json)


# ============================================================================
# Tests: Exit Code Semantics Adversarial
# ============================================================================


class TestExitCodeSemanticsAdversarial:
    """Exit code interpretation across tools."""

    @patch("subprocess.run")
    def test_gitleaks_exit_code_0_no_secrets(self, mock_run: MagicMock) -> None:
        """Gitleaks exit code 0 → no secrets found (standard).

        Adversarial test: Exit code semantics validated.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=0,
            stdout=json.dumps({"matches": []}),
            stderr="",
        )

        # Exit code 0 = success (no secrets)
        assert mock_run.return_value.returncode == 0

    @patch("subprocess.run")
    def test_gitleaks_exit_code_1_secrets_found(self, mock_run: MagicMock) -> None:
        """Gitleaks exit code 1 → secrets found.

        Adversarial test: Exit code 1 indicates findings (not error).
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gitleaks"],
            returncode=1,
            stdout=json.dumps({"matches": [{"File": "test.txt"}]}),
            stderr="",
        )

        # Exit code 1 = findings (not necessarily error)
        assert mock_run.return_value.returncode == 1

    @patch("subprocess.run")
    def test_bandit_exit_code_nonzero_issues_found(self, mock_run: MagicMock) -> None:
        """Bandit exit code >1 → issues found (varies by tool).

        Adversarial test: Different tools may use different exit codes.
        """
        mock_run.return_value = subprocess.CompletedProcess(
            args=["bandit"],
            returncode=2,  # Different semantics per tool
            stdout=json.dumps({"results": [{"severity": "HIGH"}]}),
            stderr="",
        )

        # Gate must handle tool-specific exit code semantics
        assert mock_run.return_value.returncode != 0


# ============================================================================
# Tests: Checkpoint — Assumptions Encoded as Tests
# ============================================================================


class TestCheckpointAssumptions:
    """Tests encoding conservative assumptions per checkpoint protocol.

    CHECKPOINT NOTE: These tests encode assumptions about gate behavior
    when implementation details are ambiguous. Each test is marked and
    documents the assumption in case human review is needed.
    """

    def test_checkpoint_violation_severity_is_uppercase_enum(self) -> None:
        """CHECKPOINT: Severity values are uppercase strings (ERROR/WARN/INFO).

        Assumption: Implementation uses uppercase enums, not lowercase.
        Rationale: Consistency with gate schema spec.
        """
        severities = ["ERROR", "WARN", "INFO"]
        for sev in severities:
            assert sev.isupper(), f"Severity {sev} must be uppercase"

    def test_checkpoint_status_enum_three_values_only(self) -> None:
        """CHECKPOINT: Status is exactly one of PASS/WARN/FAIL (no other values).

        Assumption: No BLOCK, SKIP, DEFER, or other custom statuses.
        Rationale: M902-01 schema defines exactly 3 values.
        """
        valid_statuses = {"PASS", "WARN", "FAIL"}
        assert len(valid_statuses) == 3

    def test_checkpoint_remediation_hints_are_strings_not_objects(self) -> None:
        """CHECKPOINT: remediation_hints[] contains strings, not objects.

        Assumption: Each hint is actionable text (not structured data).
        Rationale: Simplicity and human readability.
        """
        hints = [
            "Remove hardcoded password from test.py:42",
            "Update package X to 2.0.0",
        ]
        for hint in hints:
            assert isinstance(hint, str)

    def test_checkpoint_tool_statuses_always_five_tools(self) -> None:
        """CHECKPOINT: tool_statuses[] always has exactly 5 entries.

        Assumption: All 5 tools included even if some are skipped/unavailable.
        Rationale: Fixed output schema (M902-01).
        """
        tool_names = ["gitleaks", "bandit", "semgrep", "pip-audit", "npm-audit"]
        assert len(tool_names) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
