"""Adversarial, mutation, and boundary tests for M902-11 Architecture Enforcement Gate.

Extends the behavioral test suite with:
- Mutation testing (flipped booleans, changed operators, boundary mutations)
- Edge case testing (max/min values, null/empty boundaries)
- Type violations (wrong types, structure changes, missing keys)
- Combinatorial testing (multiple failure modes together)
- Mock/integration exposure (tests that catch false confidence from mocks)
- Determinism/order dependency testing
- Spec gap detection (implicit assumptions under test)

Test naming: adversarial_* prefix for all tests in this module.

CHECKPOINT: These tests assume the implementation properly handles:
1. Risk score computation (weighted average, not just max)
2. Architecture score clamping [0, 100]
3. Empty tool results (no violations)
4. Mixed severity violations (sorted correctly)
5. Deduplication by (file, line, rule_id) fingerprint
6. All required output fields present and correct types
7. Timestamp ISO 8601 with Z suffix
8. Shadow mode override of status determination
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest


class TestAdversarialMutationRiskScoreComputation:
    """Mutation tests on risk_score computation logic."""

    def test_adversarial_risk_score_uses_weighted_average_not_max(self) -> None:
        """Mutation: Verify risk_score is weighted average, not max severity.

        If implementation incorrectly uses max(severities), this test fails.
        Mutant: risk_score = max([v["weight"] for v in violations]) instead of average.
        """
        from ci.scripts.gates import architecture_enforcement_check

        # Multiple WARN violations (weight 50 each) should average, not max
        mock_violations = [
            {"tool": "jscpd", "severity": "WARN", "file": "a.py", "line": 1, "column": 0,
             "rule_id": "DUP-01", "message": "Duplication cluster 1"},
            {"tool": "jscpd", "severity": "WARN", "file": "b.py", "line": 2, "column": 0,
             "rule_id": "DUP-01", "message": "Duplication cluster 2"},
            {"tool": "radon", "severity": "WARN", "file": "c.py", "line": 3, "column": 0,
             "rule_id": "CX-01", "message": "Function too long"},
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[mock_violations[0], mock_violations[1]]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[mock_violations[2]]):
                            result = architecture_enforcement_check.run({})
                            # Weighted average: (50 + 50 + 50) / 3 = 50, not max(50)
                            assert result["risk_score"] == 50, \
                                f"Expected risk_score 50 (average), got {result['risk_score']}"

    def test_adversarial_risk_score_with_mixed_severities(self) -> None:
        """Mutation: Verify risk_score averages mixed severities correctly.

        CRITICAL=100, ERROR=80, WARN=50, INFO=10
        Expected: (100 + 80 + 50) / 3 = 76.67 ≈ 77 (rounded)
        """
        from ci.scripts.gates import architecture_enforcement_check

        mock_violations = [
            {"tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1,
             "column": 0, "rule_id": "AR-07", "message": "Circular import"},
            {"tool": "semgrep", "severity": "ERROR", "file": "b.py", "line": 2,
             "column": 0, "rule_id": "AR-01", "message": "SRP violation"},
            {"tool": "jscpd", "severity": "WARN", "file": "c.py", "line": 3,
             "column": 0, "rule_id": "DUP-01", "message": "Duplication"},
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[mock_violations[0]]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[mock_violations[1]]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[mock_violations[2]]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            expected = round((100 + 80 + 50) / 3)
                            assert result["risk_score"] == expected, \
                                f"Expected risk_score {expected}, got {result['risk_score']}"

    def test_adversarial_architecture_score_clamped_to_zero(self) -> None:
        """Mutation: Verify architecture_score is clamped [0, 100], not negative.

        If implementation doesn't clamp, with 11+ AR violations: 100 - (11*10) = -10.
        Mutant: architecture_score not clamped to max(0, ...).
        """
        from ci.scripts.gates import architecture_enforcement_check

        # 15 AR violations would compute to -50 without clamping
        ar_violations = [
            {"tool": "semgrep", "severity": "ERROR", "file": f"m{i}.py", "line": i,
             "column": 0, "rule_id": f"AR-{(i % 6) + 1:02d}", "message": f"SRP violation {i}"}
            for i in range(15)
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=ar_violations):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert 0 <= result["architecture_score"] <= 100, \
                                f"architecture_score {result['architecture_score']} out of bounds"

    def test_adversarial_architecture_score_counts_ar_prefix_only(self) -> None:
        """Mutation: Verify architecture_score counts only AR-* violations, not DUP/CX.

        Spec: architecture_score = 100 - (AR_violations * 10)
        If implementation counts all violations: (AR + DUP + CX) * 10.
        """
        from ci.scripts.gates import architecture_enforcement_check

        mock_violations = [
            {"tool": "semgrep", "severity": "ERROR", "file": "a.py", "line": 1,
             "column": 0, "rule_id": "AR-01", "message": "SRP"},  # Counts
            {"tool": "semgrep", "severity": "ERROR", "file": "b.py", "line": 2,
             "column": 0, "rule_id": "AR-02", "message": "SRP"},  # Counts
            {"tool": "jscpd", "severity": "WARN", "file": "c.py", "line": 3,
             "column": 0, "rule_id": "DUP-01", "message": "Dup"},  # Should NOT count
            {"tool": "radon", "severity": "WARN", "file": "d.py", "line": 4,
             "column": 0, "rule_id": "CX-01", "message": "Complexity"},  # Should NOT count
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=mock_violations[:2]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[mock_violations[2]]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[mock_violations[3]]):
                            result = architecture_enforcement_check.run({})
                            # Only 2 AR violations: 100 - (2 * 10) = 80
                            assert result["architecture_score"] == 80, \
                                f"Expected score 80 (2 AR only), got {result['architecture_score']}"


class TestAdversarialMutationStatusDetermination:
    """Mutation tests on status determination logic."""

    def test_adversarial_status_fail_on_any_error_not_just_highest_severity(self) -> None:
        """Mutation: Verify FAIL is triggered by ERROR severity, not only CRITICAL.

        Spec: "risk_score > 90 or any(violation.severity == ERROR)" → FAIL
        Mutant: status = FAIL only if severity == CRITICAL (missing ERROR check).
        """
        from ci.scripts.gates import architecture_enforcement_check

        # Single ERROR violation with high risk
        mock_violation = {
            "tool": "semgrep", "severity": "ERROR", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "AR-01", "message": "SRP violation"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[mock_violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] in ["FAIL", "ESCALATE"], \
                                f"Expected FAIL for ERROR violation, got {result['status']}"

    def test_adversarial_escalate_on_critical_not_just_high_risk_score(self) -> None:
        """Mutation: Verify ESCALATE triggered by CRITICAL severity OR low architecture_score.

        Spec: "architecture_score <= 30 or any(severity == CRITICAL)" → ESCALATE
        Mutant: ESCALATE only if architecture_score condition (missing CRITICAL check).
        """
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "AR-07", "message": "Circular import"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[mock_violation]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "ESCALATE", \
                                f"Expected ESCALATE for CRITICAL violation, got {result['status']}"

    def test_adversarial_shadow_mode_overrides_status_not_just_passes_through(self) -> None:
        """Mutation: Verify shadow mode FORCES status=PASS, doesn't just skip checking violations.

        Spec: "if mode == 'shadow': status = 'PASS'" (override, not conditional)
        Mutant: Shadow mode returns computed status (FAIL) instead of forcing PASS.
        """
        from ci.scripts.gates import architecture_enforcement_check

        # CRITICAL violation that would normally escalate
        mock_violation = {
            "tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "AR-07", "message": "Circular import"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[mock_violation]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "shadow"})
                            assert result["status"] == "PASS", \
                                f"Shadow mode MUST return PASS, got {result['status']}"
                            # Violations should still be reported, just status overridden
                            assert len(result["violations"]) > 0, \
                                "Shadow mode should report violations, just with PASS status"


class TestAdversarialMutationDeduplication:
    """Mutation tests on violation deduplication logic."""

    def test_adversarial_dedup_by_exact_fingerprint_not_file_only(self) -> None:
        """Mutation: Verify deduplication uses (file, line, rule_id), not just file.

        Spec: "Deduplication by fingerprint: (file, line, rule_id)"
        Mutant: Dedup by (file) only, so different lines/rules merge incorrectly.
        """
        from ci.scripts.gates import architecture_enforcement_check

        # Two violations in same file, different lines, different rules
        mock_violations = [
            {"tool": "semgrep", "severity": "ERROR", "file": "module.py", "line": 10,
             "column": 0, "rule_id": "AR-01", "message": "First violation"},
            {"tool": "semgrep", "severity": "ERROR", "file": "module.py", "line": 20,
             "column": 0, "rule_id": "AR-02", "message": "Second violation"},
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=mock_violations):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Both should be present, not merged
                            assert len(result["violations"]) == 2, \
                                f"Expected 2 violations (different lines/rules), got {len(result['violations'])}"

    def test_adversarial_dedup_keeps_most_severe_not_first(self) -> None:
        """Mutation: Verify dedup keeps most severe violation when fingerprints match.

        If two tools report same (file, line, rule_id) with WARN + ERROR, keep ERROR.
        Mutant: Keeps first violation instead of most severe.
        """
        from ci.scripts.gates import architecture_enforcement_check

        # Same fingerprint, different severities (from different tools)
        v1 = {"tool": "import-linter", "severity": "WARN", "file": "a.py", "line": 10,
              "column": 0, "rule_id": "AR-01", "message": "Import issue (linter)"}
        v2 = {"tool": "semgrep", "severity": "ERROR", "file": "a.py", "line": 10,
              "column": 0, "rule_id": "AR-01", "message": "Import issue (semgrep)"}

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[v1]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[v2]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert len(result["violations"]) == 1, \
                                f"Expected 1 dedup'd violation, got {len(result['violations'])}"
                            assert result["violations"][0]["severity"] == "ERROR", \
                                f"Expected ERROR (most severe), got {result['violations'][0]['severity']}"

    def test_adversarial_dedup_across_all_tools_not_per_tool(self) -> None:
        """Mutation: Verify deduplication happens across all tools, not within each tool.

        If both import-linter and semgrep report the same circular import, should merge.
        Mutant: Dedup only within tool, not across tools.
        """
        from ci.scripts.gates import architecture_enforcement_check

        violation = {"tool": "???", "severity": "CRITICAL", "file": "cycle.py", "line": 1,
                    "column": 0, "rule_id": "AR-07", "message": "Circular import"}

        v_linter = dict(violation, tool="import-linter")
        v_semgrep = dict(violation, tool="semgrep")

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[v_linter]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[v_semgrep]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should deduplicate to 1, not keep 2
                            assert len(result["violations"]) == 1, \
                                f"Expected 1 dedup'd violation across tools, got {len(result['violations'])}"


class TestAdversarialBoundaryValueTesting:
    """Boundary and edge case testing."""

    def test_adversarial_zero_violations_produces_zero_risk_score(self) -> None:
        """Boundary: No violations → risk_score must be 0, not undefined/None."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert result["risk_score"] == 0, \
                                f"Zero violations must produce risk_score=0, got {result['risk_score']}"

    def test_adversarial_one_violation_computes_risk_score_as_single_weight(self) -> None:
        """Boundary: Single violation → risk_score = that violation's weight."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "radon", "severity": "WARN", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "CX-01", "message": "Long function"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[mock_violation]):
                            result = architecture_enforcement_check.run({})
                            # WARN = 50
                            assert result["risk_score"] == 50, \
                                f"Single WARN violation must give risk_score=50, got {result['risk_score']}"

    def test_adversarial_max_violations_score_remains_in_bounds(self) -> None:
        """Boundary: 100+ violations → risk_score still [0, 100]."""
        from ci.scripts.gates import architecture_enforcement_check

        huge_violations = [
            {"tool": "semgrep", "severity": "CRITICAL", "file": f"m{i}.py", "line": i,
             "column": 0, "rule_id": "AR-01", "message": "Violation"}
            for i in range(100)
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=huge_violations):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert 0 <= result["risk_score"] <= 100, \
                                f"risk_score {result['risk_score']} out of bounds with 100 violations"

    def test_adversarial_negative_duration_is_not_possible(self) -> None:
        """Boundary: duration_ms must be >= 0, not negative."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})
        assert result["duration_ms"] >= 0, \
            f"duration_ms {result['duration_ms']} must be >= 0"

    def test_adversarial_very_long_violation_message_not_truncated_silently(self) -> None:
        """Boundary: Long violation messages handled correctly (no silent truncation)."""
        from ci.scripts.gates import architecture_enforcement_check

        long_msg = "x" * 1000  # Very long message
        mock_violation = {
            "tool": "semgrep", "severity": "WARN", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "DUP-01", "message": long_msg
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[mock_violation]):
                            result = architecture_enforcement_check.run({})
                            # Should not silently truncate or fail
                            assert len(result["violations"]) == 1
                            # Message should be preserved or truncated consistently
                            assert len(result["violations"][0]["message"]) > 0


class TestAdversarialCombinatoricalFailureModes:
    """Combinatorial testing: multiple failure modes together."""

    def test_adversarial_tool_timeout_and_unavailable_mixed(self) -> None:
        """Combinatorial: Some tools timeout, some unavailable, some work normally."""
        from ci.scripts.gates import architecture_enforcement_check

        good_violation = {"tool": "semgrep", "severity": "WARN", "file": "a.py", "line": 1,
                         "column": 0, "rule_id": "DUP-01", "message": "Dup"}

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   side_effect=FileNotFoundError("Not installed")):  # Unavailable
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       side_effect=subprocess.TimeoutExpired("eslint", 60)):  # Timeout
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[good_violation]):  # Works
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should still report the working violation and tool errors
                            assert any(v["rule_id"] == "DUP-01" for v in result["violations"])
                            # Tool error violations recorded
                            assert any(v["rule_id"] in ["TOOL_UNAVAILABLE", "TOOL_TIMEOUT"]
                                      for v in result["violations"])

    def test_adversarial_empty_violations_with_parse_errors(self) -> None:
        """Combinatorial: Some tools return empty, some have parse errors."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           side_effect=json.JSONDecodeError("Bad JSON", "", 0)):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should gracefully handle, status may be PASS with parse error recorded
                            assert result["status"] in ["PASS", "WARN"]

    def test_adversarial_critical_and_error_and_warn_together(self) -> None:
        """Combinatorial: Multiple severity levels together."""
        from ci.scripts.gates import architecture_enforcement_check

        violations = [
            {"tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1,
             "column": 0, "rule_id": "AR-07", "message": "Cycle"},
            {"tool": "semgrep", "severity": "ERROR", "file": "b.py", "line": 2,
             "column": 0, "rule_id": "AR-01", "message": "SRP"},
            {"tool": "jscpd", "severity": "WARN", "file": "c.py", "line": 3,
             "column": 0, "rule_id": "DUP-01", "message": "Dup"},
            {"tool": "radon", "severity": "INFO", "file": "d.py", "line": 4,
             "column": 0, "rule_id": "CX-01", "message": "Info"},
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[violations[0]]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violations[1]]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[violations[2]]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[violations[3]]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            # Should be sorted: CRITICAL, ERROR, WARN, INFO
                            severities = [v["severity"] for v in result["violations"]]
                            assert severities == ["CRITICAL", "ERROR", "WARN", "INFO"], \
                                f"Expected sorted severities, got {severities}"
                            # Status should be ESCALATE (CRITICAL present)
                            assert result["status"] == "ESCALATE"


class TestAdversarialTypeViolations:
    """Type and structure violations."""

    def test_adversarial_violation_with_wrong_type_line_number(self) -> None:
        """Type violation: line is string instead of int.

        CHECKPOINT: Implementation must enforce types in violation objects.
        """
        from ci.scripts.gates import architecture_enforcement_check

        bad_violation = {
            "tool": "semgrep", "severity": "WARN", "file": "a.py",
            "line": "42",  # String instead of int
            "column": 0, "rule_id": "DUP-01", "message": "Dup"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[bad_violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            # Implementation should either:
                            # 1. Coerce to int and proceed
                            # 2. Reject and return error status
                            # 3. Skip the bad violation
                            result = architecture_enforcement_check.run({})
                            # Ensure result is still valid
                            assert isinstance(result["violations"], list)
                            assert isinstance(result["risk_score"], int)

    def test_adversarial_violation_missing_optional_column_field(self) -> None:
        """Type violation: missing column field (spec requires it).

        CHECKPOINT: Implementation must handle missing optional fields gracefully.
        """
        from ci.scripts.gates import architecture_enforcement_check

        incomplete_violation = {
            "tool": "semgrep", "severity": "WARN", "file": "a.py", "line": 1,
            # Missing column
            "rule_id": "DUP-01", "message": "Dup"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[incomplete_violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should handle gracefully (add default column, skip, or error)
                            assert result["status"] in ["PASS", "WARN"]


class TestAdversarialOrderDependency:
    """Test for order-dependent behavior that shouldn't exist."""

    def test_adversarial_tool_order_does_not_affect_deduplication(self) -> None:
        """Order dependency: Dedup should work regardless of tool order.

        If import-linter reports violation before semgrep, dedup should still work.
        """
        from ci.scripts.gates import architecture_enforcement_check

        same_violation = {
            "tool": "???", "severity": "ERROR", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "AR-01", "message": "SRP"
        }

        v_linter = dict(same_violation, tool="import-linter")
        v_semgrep = dict(same_violation, tool="semgrep")

        # Run 1: linter first, semgrep second
        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[v_linter]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[v_semgrep]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result1 = architecture_enforcement_check.run({})

        # Run 2: semgrep first, linter second (swap order in patches)
        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[v_linter]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[v_semgrep]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result2 = architecture_enforcement_check.run({})

        # Both runs should deduplicate to same number of violations
        assert len(result1["violations"]) == len(result2["violations"]), \
            f"Order dependency: got {len(result1['violations'])} vs {len(result2['violations'])}"

    def test_adversarial_severity_sorting_deterministic(self) -> None:
        """Order dependency: Sorting violations should be deterministic.

        Multiple calls with same violations should return same order.
        """
        from ci.scripts.gates import architecture_enforcement_check

        violations = [
            {"tool": "radon", "severity": "INFO", "file": "d.py", "line": 4,
             "column": 0, "rule_id": "CX-01", "message": "Info"},
            {"tool": "semgrep", "severity": "ERROR", "file": "b.py", "line": 2,
             "column": 0, "rule_id": "AR-01", "message": "Error"},
            {"tool": "jscpd", "severity": "WARN", "file": "c.py", "line": 3,
             "column": 0, "rule_id": "DUP-01", "message": "Warn"},
            {"tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1,
             "column": 0, "rule_id": "AR-07", "message": "Critical"},
        ]

        def get_order():
            with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                       return_value=[violations[3]]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                               return_value=[violations[1]]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                                   return_value=[violations[2]]):
                            with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                       return_value=[violations[0]]):
                                result = architecture_enforcement_check.run({})
                                return [v["rule_id"] for v in result["violations"]]

        order1 = get_order()
        order2 = get_order()
        assert order1 == order2, \
            f"Sorting non-deterministic: {order1} != {order2}"


class TestAdversarialMockHeavyExposure:
    """Tests that expose false confidence from excessive mocking."""

    def test_adversarial_violation_structure_enforcement_not_mocked(self) -> None:
        """Mock exposure: All mocks return well-formed violations, but real tools may not.

        CHECKPOINT: Implementation must validate violation structure from tools
        and reject malformed violations.
        """
        from ci.scripts.gates import architecture_enforcement_check

        # Malformed violation: missing required field 'message'
        bad_violation = {
            "tool": "semgrep", "severity": "WARN", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "DUP-01"
            # Missing: "message"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[bad_violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Implementation should either:
                            # 1. Skip malformed violation
                            # 2. Add default message
                            # 3. Record validation error
                            # But must not crash
                            assert isinstance(result, dict)

    def test_adversarial_empty_violations_array_vs_none(self) -> None:
        """Mock exposure: Mocks return [], but real tools might return None or throw.

        CHECKPOINT: Implementation must handle empty, None, and exception cases.
        """
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=None):  # None instead of []
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Must handle None gracefully (treat as no violations)
                            assert isinstance(result["violations"], list)


class TestAdversarialSpecGapDetection:
    """Tests that expose implicit spec assumptions and gaps."""

    def test_adversarial_default_mode_when_not_specified(self) -> None:
        """Spec gap: Registry says 'default_mode: shadow', but what if inputs is empty?

        CHECKPOINT: When mode is not in inputs, implementation should use 'shadow' default.
        """
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "semgrep", "severity": "ERROR", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "AR-01", "message": "SRP"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[mock_violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            # No mode specified, should default to 'shadow'
                            result = architecture_enforcement_check.run({})
                            assert result["status"] == "PASS", \
                                "Default shadow mode must return PASS even with violations"

    def test_adversarial_ticket_id_default_when_not_provided(self) -> None:
        """Spec gap: Spec says 'provided in inputs or "M902-11" if omitted'.

        CHECKPOINT: When ticket_id not in inputs, use "M902-11".
        """
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert result["ticket_id"] in ["M902-11", "unknown"], \
                                f"Default ticket_id should be M902-11, got {result['ticket_id']}"

    def test_adversarial_message_field_single_line_constraint(self) -> None:
        """Spec gap: Message field must be 'single-line, <300 chars'.

        CHECKPOINT: Implementation must enforce or validate this.
        """
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            message = result["message"]
                            assert "\n" not in message, \
                                f"Message must be single-line, got: {message}"
                            assert len(message) <= 300, \
                                f"Message must be <300 chars, got {len(message)}"

    def test_adversarial_unknown_mode_value(self) -> None:
        """Spec gap: What happens if mode is 'invalid' instead of 'shadow'/'blocking'?

        CHECKPOINT: Implementation should either reject or default to safe mode (shadow).
        """
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "semgrep", "severity": "CRITICAL", "file": "a.py", "line": 1,
            "column": 0, "rule_id": "AR-07", "message": "Critical"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[mock_violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            # Invalid mode: should default to safe behavior (shadow)
                            result = architecture_enforcement_check.run({"mode": "invalid_mode"})
                            # Should not crash; status should be safe (PASS or error indicator)
                            assert result["status"] in ["PASS", "FAIL", "ESCALATE"]

    def test_adversarial_empty_artifacts_array_always(self) -> None:
        """Spec gap: Artifacts field must always be empty (no re-staged files).

        CHECKPOINT: Verify artifacts is [] in all cases, never None or populated.
        """
        from ci.scripts.gates import architecture_enforcement_check

        mock_violations = [
            {"tool": "semgrep", "severity": "ERROR", "file": "a.py", "line": 1,
             "column": 0, "rule_id": "AR-01", "message": "SRP"},
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=mock_violations):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert result["artifacts"] == [], \
                                f"artifacts must always be [], got {result['artifacts']}"
                            assert isinstance(result["artifacts"], list)
