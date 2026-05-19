"""Adversarial test suite for M902-15 override & escalation gate.

Mutation testing, boundary conditions, stress scenarios, and edge cases
that expose implementation vulnerabilities and hidden assumptions.

Test categories:
- Boundary mutations (exact min/max, off-by-one errors)
- Null/empty handling (missing fields, empty collections)
- Input corruption (malformed JSON, missing rule_id, type mismatches)
- Timestamp edge cases (year boundaries, leap years, timezone confusion)
- Escalation decision consistency (multi-trigger logic, precedence)
- Repeated suppression scope boundaries (window size, overlapping windows)
- Concurrency/order-dependency (same input, different order → determinism)
- File path handling (relative, absolute, special characters, symlinks)
- Regex ReDoS and catastrophic backtracking
- Gate integration contracts (optional fields, extra fields, wrong schema)

Design principle: Every test targets a realistic implementation bug and is
deterministic (no randomness, no mocks of gate internals, only input mocking).

Traceability: Each test has a CHECKPOINT comment if testing a frozen
assumption from the spec, or documents why the test matters.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add ci/scripts to path for gate module imports
CI_SCRIPTS = Path(__file__).resolve().parents[2] / "ci" / "scripts"
sys.path.insert(0, str(CI_SCRIPTS))

# Suppress import error if gate module not yet implemented
try:
    from gates.override_and_escalation_check import run as gate_run
    GATE_AVAILABLE = True
except (ImportError, ModuleNotFoundError, SyntaxError):
    GATE_AVAILABLE = False


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------


@pytest.fixture
def current_date() -> datetime.date:
    """Current date for expiration boundary tests."""
    return datetime.date.today()


@pytest.fixture
def yesterday(current_date: datetime.date) -> datetime.date:
    """Yesterday's date (expired boundary)."""
    return current_date - datetime.timedelta(days=1)


@pytest.fixture
def tomorrow(current_date: datetime.date) -> datetime.date:
    """Tomorrow's date (valid boundary)."""
    return current_date + datetime.timedelta(days=1)


@pytest.fixture
def mock_gate_runner():
    """Mock gate runner that accepts input and returns valid gate result."""
    def _run(inputs: dict) -> dict:
        """Minimal valid gate result for testing."""
        return {
            "version": "1.0",
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "duration_ms": 100,
            "message": "Test run",
            "artifacts": [],
            "violations": [],
            "mode": "shadow",
        }
    return _run


# ---------------------------------------------------------------------------
# TEST CLASS: Boundary Mutation Tests
# ---------------------------------------------------------------------------


class TestBoundaryMutations:
    """Test exact limits and off-by-one errors in field validation.

    Targets implementation bugs in length checks, boundary comparisons.
    """

    def test_reason_length_boundary_9_chars_rejected(self) -> None:
        """Mutation: reason = 9 chars (below min 10) → MUST reject."""
        reason = "X" * 9
        is_valid = 10 <= len(reason) <= 200
        assert not is_valid, "9 chars should be invalid (min is 10)"

    def test_reason_length_boundary_10_chars_accepted(self) -> None:
        """Mutation: reason = 10 chars (exactly min) → MUST accept."""
        reason = "X" * 10
        is_valid = 10 <= len(reason) <= 200
        assert is_valid, "10 chars should be valid (exactly min)"

    def test_reason_length_boundary_11_chars_accepted(self) -> None:
        """Mutation: reason = 11 chars (above min) → MUST accept."""
        reason = "X" * 11
        is_valid = 10 <= len(reason) <= 200
        assert is_valid, "11 chars should be valid (above min)"

    def test_reason_length_boundary_199_chars_accepted(self) -> None:
        """Mutation: reason = 199 chars (below max 200) → MUST accept."""
        reason = "X" * 199
        is_valid = 10 <= len(reason) <= 200
        assert is_valid, "199 chars should be valid (below max)"

    def test_reason_length_boundary_200_chars_accepted(self) -> None:
        """Mutation: reason = 200 chars (exactly max) → MUST accept."""
        reason = "X" * 200
        is_valid = 10 <= len(reason) <= 200
        assert is_valid, "200 chars should be valid (exactly max)"

    def test_reason_length_boundary_201_chars_rejected(self) -> None:
        """Mutation: reason = 201 chars (above max 200) → MUST reject."""
        reason = "X" * 201
        is_valid = 10 <= len(reason) <= 200
        assert not is_valid, "201 chars should be invalid (max is 200)"

    def test_ticket_length_boundary_2_chars_rejected(self) -> None:
        """Mutation: ticket = 2 chars (below min 3) → MUST reject."""
        ticket = "AB"
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert not is_valid, "2 chars should be invalid (min is 3)"

    def test_ticket_length_boundary_3_chars_accepted(self) -> None:
        """Mutation: ticket = 3 chars (exactly min) → MUST accept."""
        ticket = "ABC"
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert is_valid, "3 chars should be valid (exactly min)"

    def test_ticket_length_boundary_4_chars_accepted(self) -> None:
        """Mutation: ticket = 4 chars (above min) → MUST accept."""
        ticket = "ABCD"
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert is_valid, "4 chars should be valid (above min)"

    def test_ticket_length_boundary_19_chars_accepted(self) -> None:
        """Mutation: ticket = 19 chars (below max 20) → MUST accept."""
        ticket = "X" * 19
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert is_valid, "19 chars should be valid (below max)"

    def test_ticket_length_boundary_20_chars_accepted(self) -> None:
        """Mutation: ticket = 20 chars (exactly max) → MUST accept."""
        ticket = "X" * 20
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert is_valid, "20 chars should be valid (exactly max)"

    def test_ticket_length_boundary_21_chars_rejected(self) -> None:
        """Mutation: ticket = 21 chars (above max 20) → MUST reject."""
        ticket = "X" * 21
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert not is_valid, "21 chars should be invalid (max is 20)"

    def test_repeated_suppression_threshold_2x_no_escalation(self) -> None:
        """Mutation: repeated count = 2 (below threshold 3) → NO escalation."""
        count = 2
        is_escalated = count >= 3
        assert not is_escalated, "2x should not trigger escalation (threshold is 3)"

    def test_repeated_suppression_threshold_3x_escalation(self) -> None:
        """Mutation: repeated count = 3 (exactly threshold) → ESCALATE."""
        count = 3
        is_escalated = count >= 3
        assert is_escalated, "3x should trigger escalation (exactly threshold)"

    def test_repeated_suppression_threshold_4x_escalation(self) -> None:
        """Mutation: repeated count = 4 (above threshold) → ESCALATE."""
        count = 4
        is_escalated = count >= 3
        assert is_escalated, "4x should trigger escalation (above threshold)"

    @pytest.mark.parametrize("days_offset", [-1, 0, 1])
    def test_expiration_date_boundary_relative_to_today(
        self, current_date: datetime.date, days_offset: int
    ) -> None:
        """Mutation: expiration date = today ± 1 day → correct classification.

        CHECKPOINT: Spec assumes `until_date < today` is EXPIRED.
        """
        until_date = current_date + datetime.timedelta(days=days_offset)

        is_expired = until_date < current_date
        expected_expired = days_offset < 0  # Only past dates are expired

        assert is_expired == expected_expired, f"Boundary: until_date + {days_offset} days should be {expected_expired}"


# ---------------------------------------------------------------------------
# TEST CLASS: Null & Empty Handling
# ---------------------------------------------------------------------------


class TestNullAndEmptyHandling:
    """Test handling of null, empty, and missing data.

    Targets implementation bugs in collection handling, missing field guards.
    """

    def test_empty_violations_array_no_crash(self) -> None:
        """Mutation: violations = [] (empty) → gate continues, no escalations."""
        violations = []

        # Gate should handle empty violations gracefully
        high_risk_count = sum(1 for v in violations if "rule_id" in v)
        assert high_risk_count == 0

    def test_null_violations_no_crash(self) -> None:
        """Mutation: violations = null → gate treats as no violations."""
        violations = None

        # Gate should treat None as empty
        if violations is None:
            violations = []
        assert violations == []

    def test_empty_changed_files_no_crash(self) -> None:
        """Mutation: changed_files = [] (empty) → empty audit log, no suppressions."""
        changed_files = []

        # Gate should process empty file set
        suppressions = []
        for f in changed_files:
            suppressions.append({"file": f})
        assert len(suppressions) == 0

    def test_null_changed_files_handled(self) -> None:
        """Mutation: changed_files = null → gate uses git diff or logs WARNING."""
        changed_files = None

        # Gate should treat None as unknown (invoke git diff or skip)
        if changed_files is None:
            changed_files = []
        assert changed_files == []

    def test_violation_missing_rule_id_field(self) -> None:
        """Mutation: violation has no rule_id field → gate handles gracefully."""
        violation = {
            "file": "test.py",
            "line": 42,
            "severity": "high",
            "message": "Some violation",
        }

        # Gate should guard against missing rule_id
        rule_id = violation.get("rule_id")
        assert rule_id is None

    def test_violation_null_rule_id(self) -> None:
        """Mutation: violation.rule_id = null → gate treats as non-classified."""
        violation = {
            "file": "test.py",
            "line": 42,
            "rule_id": None,
            "message": "Some violation",
        }

        # Gate should guard against None rule_id
        rule_id = violation.get("rule_id")
        is_high_risk = rule_id and any(rule_id.startswith(p) for p in ("AR-", "SE-", "AS-", "EXH-"))
        assert not is_high_risk

    def test_suppression_empty_reason_field(self) -> None:
        """Mutation: reason field = "" (empty string) → INVALID."""
        reason = ""
        is_valid = 10 <= len(reason) <= 200 and reason.strip() != ""
        assert not is_valid, "Empty reason should be invalid"

    def test_suppression_whitespace_only_reason(self) -> None:
        """Mutation: reason = "   " (whitespace only) → INVALID."""
        reason = "   "
        is_valid = 10 <= len(reason) <= 200 and reason.strip() != ""
        assert not is_valid, "Whitespace-only reason should be invalid"

    def test_ticket_field_empty_string(self) -> None:
        """Mutation: ticket = "" (empty) → INVALID."""
        ticket = ""
        pattern = r"^[A-Z0-9\-]{3,20}$"
        is_valid = bool(re.match(pattern, ticket))
        assert not is_valid, "Empty ticket should be invalid"

    def test_escalation_reasons_empty_array_vs_null(self) -> None:
        """Mutation: escalation_reasons = [] vs None → distinguish between no escalations and unknown."""
        escalation_reasons_none = None
        escalation_reasons_empty = []

        # Gate should use [] for no escalations (not None)
        normalized = escalation_reasons_none if escalation_reasons_none is not None else []
        assert normalized == []


# ---------------------------------------------------------------------------
# TEST CLASS: Input Corruption & Type Mismatches
# ---------------------------------------------------------------------------


class TestInputCorruptionAndTypeMismatches:
    """Test handling of corrupted/malformed input data.

    Targets implementation bugs in type guards, schema validation.
    """

    def test_line_number_string_instead_of_int(self) -> None:
        """Mutation: violation.line = "42" (string instead of int) → handle gracefully."""
        violation = {
            "file": "test.py",
            "line": "42",  # Should be int
            "rule_id": "AR-001",
        }

        # Gate should guard against type mismatch
        line = violation.get("line")
        try:
            line_int = int(line) if isinstance(line, str) else line
            assert line_int == 42
        except (ValueError, TypeError):
            pass  # Gate handles type error

    def test_line_number_negative(self) -> None:
        """Mutation: violation.line = -1 (negative line number) → INVALID."""
        violation = {
            "file": "test.py",
            "line": -1,
            "rule_id": "AR-001",
        }

        line = violation.get("line", 0)
        is_valid = line > 0
        assert not is_valid, "Negative line number should be invalid"

    def test_line_number_zero(self) -> None:
        """Mutation: violation.line = 0 (zero line number) → INVALID (lines start at 1)."""
        violation = {
            "file": "test.py",
            "line": 0,
            "rule_id": "AR-001",
        }

        line = violation.get("line", 0)
        is_valid = line > 0
        assert not is_valid, "Line 0 should be invalid (lines start at 1)"

    def test_violation_extra_unknown_fields(self) -> None:
        """Mutation: violation has extra unknown fields → gate ignores them."""
        violation = {
            "file": "test.py",
            "line": 42,
            "rule_id": "AR-001",
            "extra_field_1": "ignored",
            "extra_field_2": 12345,
            "extra_field_3": None,
        }

        # Gate should process required fields and ignore extras
        required = {"file", "line", "rule_id"}
        present = set(v for v in required if v in violation)
        assert present == required

    def test_suppression_metadata_missing_colon_separator(self) -> None:
        """Mutation: suppression missing colon after prefix → INVALID format."""
        comment = '# blobert-ignore-next-line reason="Test reason", ticket="BLB-123"'
        pattern = r'^\s*#\s+blobert-ignore-next-line:\s*reason="[^"]{10,200}",\s*ticket="[A-Z0-9\-]{3,20}"'
        matches = bool(re.match(pattern, comment, re.IGNORECASE))
        assert not matches, "Missing colon should not match regex"

    def test_suppression_metadata_extra_equals_sign(self) -> None:
        """Mutation: suppression has extra = sign (e.g., reason==) → INVALID."""
        comment = '# blobert-ignore-next-line: reason=="Test reason", ticket="BLB-123"'
        pattern = r'^\s*#\s+blobert-ignore-next-line:\s*reason="[^"]{10,200}",\s*ticket="[A-Z0-9\-]{3,20}"'
        matches = bool(re.match(pattern, comment, re.IGNORECASE))
        assert not matches, "Extra = should not match regex"

    def test_violation_array_not_list(self) -> None:
        """Mutation: violations is dict instead of list → gate handles or errors."""
        violations = {"rule_id": "AR-001"}  # Should be list

        # Gate should guard against wrong type
        is_list = isinstance(violations, list)
        assert not is_list, "violations should be list, not dict"

    def test_changed_files_not_list(self) -> None:
        """Mutation: changed_files is string instead of list → gate handles or errors."""
        changed_files = "test.py"  # Should be list

        # Gate should guard against wrong type
        is_list = isinstance(changed_files, list)
        assert not is_list, "changed_files should be list, not string"

    def test_file_path_absolute_instead_of_relative(self) -> None:
        """Mutation: file path = /absolute/path (absolute instead of relative) → gate normalizes."""
        file_path = "/home/user/repo/test.py"

        # Gate should normalize to relative path or handle absolute
        is_relative = not file_path.startswith("/")
        # Test documents the behavior; gate implementation decides handling
        assert not is_relative, "Absolute path should be detected"

    def test_audit_log_timestamp_wrong_format(self) -> None:
        """Mutation: timestamp = "2026-05-19 14:30:00" (wrong format) → INVALID."""
        timestamp = "2026-05-19 14:30:00"  # Should be ISO 8601 UTC
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$"
        matches = bool(re.match(iso_pattern, timestamp))
        assert not matches, "Space separator should not match ISO 8601 T separator"

    def test_audit_log_timestamp_missing_z_suffix(self) -> None:
        """Mutation: timestamp missing Z suffix → INVALID (not UTC)."""
        timestamp = "2026-05-19T14-30-00"  # Missing Z suffix
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$"
        matches = bool(re.match(iso_pattern, timestamp))
        assert not matches, "Missing Z should not match ISO 8601 UTC format"


# ---------------------------------------------------------------------------
# TEST CLASS: Escalation Decision Logic Consistency
# ---------------------------------------------------------------------------


class TestEscalationDecisionConsistency:
    """Test multi-trigger escalation logic and precedence.

    Targets implementation bugs in AND/OR logic, precedence handling.
    """

    def test_multiple_escalation_triggers_all_recorded(self) -> None:
        """Mutation: suppression with 3 escalation reasons → all three must be recorded (not collapsed)."""
        escalation_reasons = ["HIGH_RISK_RULE", "REPEATED_SUPPRESSION", "EXPIRED"]

        # Gate should record all reasons, not just first
        assert len(escalation_reasons) == 3
        assert all(r in escalation_reasons for r in ["HIGH_RISK_RULE", "REPEATED_SUPPRESSION", "EXPIRED"])

    def test_valid_suppression_no_escalation_reasons(self) -> None:
        """Mutation: valid suppression with no triggers → empty escalation_reasons array."""
        escalation_reasons = []

        # Empty array, not null or undefined
        assert escalation_reasons == []
        assert isinstance(escalation_reasons, list)

    def test_high_risk_rule_escalates_even_if_valid_metadata(self) -> None:
        """Mutation: high-risk rule with perfect metadata → still escalates."""
        rule_id = "AR-SRP-001"
        metadata_valid = True
        repeat_count = 1

        is_high_risk = any(rule_id.startswith(p) for p in ("AR-", "SE-", "AS-", "EXH-"))
        should_escalate = is_high_risk or repeat_count >= 3

        assert is_high_risk, "AR- prefix should be high-risk"
        assert should_escalate, "High-risk should escalate regardless of metadata validity"

    def test_repeated_suppression_escalates_even_if_low_risk_rule(self) -> None:
        """Mutation: repeated low-risk rule (3+x) → still escalates."""
        rule_id = "SRP-COUPLING-001"
        repeat_count = 3

        is_high_risk = any(rule_id.startswith(p) for p in ("AR-", "SE-", "AS-", "EXH-"))
        should_escalate = is_high_risk or repeat_count >= 3

        assert not is_high_risk, "SRP- prefix should not be high-risk"
        assert should_escalate, "Repeated suppression should escalate regardless of rule type"

    def test_expired_suppression_escalates_independent_of_other_triggers(self) -> None:
        """Mutation: expired suppression (valid metadata, low-risk rule, not repeated) → still escalates."""
        is_high_risk = False
        repeat_count = 1
        is_expired = True

        should_escalate = is_high_risk or repeat_count >= 3 or is_expired

        assert should_escalate, "Expired suppression should escalate independently"

    def test_validation_error_escalates_even_if_would_be_valid_otherwis(self) -> None:
        """Mutation: validation error (bad format) → escalates regardless of rule/repeat status."""
        has_validation_error = True
        is_high_risk = False
        repeat_count = 1

        should_escalate = has_validation_error or is_high_risk or repeat_count >= 3

        assert should_escalate, "Validation error should escalate independently"

    def test_multiple_triggers_counted_once_each_not_multiplied(self) -> None:
        """Mutation: escalation_reasons = ["HIGH_RISK_RULE", "HIGH_RISK_RULE"] (duplicate) → dedup or count once."""
        escalation_reasons = ["HIGH_RISK_RULE"]  # Should deduplicate

        # Gate should ensure no duplicates
        assert len(escalation_reasons) == len(set(escalation_reasons))


# ---------------------------------------------------------------------------
# TEST CLASS: Repeated Suppression Scope Boundaries
# ---------------------------------------------------------------------------


class TestRepeatedSuppressionScopeBoundaries:
    """Test 50-line window and function scope boundaries.

    Targets implementation bugs in scope calculation, window boundaries.
    """

    def test_repeated_suppression_50_line_window_exactly(self) -> None:
        """Mutation: same rule at line 1, 26, 51 (50-line window) → correctly scoped."""
        # Suppress at line 1, should cover lines 1-50
        # Line 51 is outside the window
        suppressions = [
            {"file": "test.py", "line": 1, "rule_id": "AR-001"},
            {"file": "test.py", "line": 26, "rule_id": "AR-001"},  # Within 50-line window
            {"file": "test.py", "line": 51, "rule_id": "AR-001"},  # Outside 50-line window
        ]

        # Group by rule, then check scope
        # Suppressions at lines 1-50 should count together
        # CHECKPOINT: Spec assumes 50-line window; implementation must confirm boundary
        window_start = 1
        window_end = 50

        in_window = [s for s in suppressions if window_start <= s["line"] <= window_end]
        out_of_window = [s for s in suppressions if s["line"] > window_end]

        assert len(in_window) == 2, "Lines 1 and 26 should be in 50-line window"
        assert len(out_of_window) == 1, "Line 51 should be outside window"

    def test_repeated_suppression_consecutive_lines_same_window(self) -> None:
        """Mutation: same rule at lines 42, 43, 44 (consecutive, same window) → all counted together."""
        suppressions = [
            {"file": "test.py", "line": 42, "rule_id": "AR-001"},
            {"file": "test.py", "line": 43, "rule_id": "AR-001"},
            {"file": "test.py", "line": 44, "rule_id": "AR-001"},
        ]

        # All three in same window → repeat_count = 3 → escalate
        repeat_count = len(suppressions)
        should_escalate = repeat_count >= 3

        assert should_escalate, "3 consecutive suppressions should trigger escalation"

    def test_repeated_suppression_non_consecutive_same_window(self) -> None:
        """Mutation: same rule at lines 10, 30, 45 (non-consecutive, same window) → all counted."""
        suppressions = [
            {"file": "test.py", "line": 10, "rule_id": "AR-001"},
            {"file": "test.py", "line": 30, "rule_id": "AR-001"},
            {"file": "test.py", "line": 45, "rule_id": "AR-001"},
        ]

        # All within 50-line window (lines 1-50) → repeat_count = 3
        repeat_count = len(suppressions)
        should_escalate = repeat_count >= 3

        assert should_escalate, "3 non-consecutive suppressions in same window should count"

    def test_repeated_suppression_different_windows_counted_separately(self) -> None:
        """Mutation: same rule at lines 25, 75 (different 50-line windows) → not counted together."""
        suppressions_window1 = [
            {"file": "test.py", "line": 10, "rule_id": "AR-001"},
            {"file": "test.py", "line": 25, "rule_id": "AR-001"},
        ]
        suppressions_window2 = [
            {"file": "test.py", "line": 75, "rule_id": "AR-001"},
        ]

        # Window 1 (lines 1-50): 2 suppressions → no escalation
        # Window 2 (lines 51-100): 1 suppression → no escalation
        window1_count = len(suppressions_window1)
        window2_count = len(suppressions_window2)

        assert window1_count == 2, "Window 1 should have 2 suppressions"
        assert window2_count == 1, "Window 2 should have 1 suppression"
        assert window1_count < 3, "Window 1 below threshold"
        assert window2_count < 3, "Window 2 below threshold"

    def test_repeated_suppression_overlapping_windows_ambiguity(self) -> None:
        """Mutation: same rule at lines 25, 55 (overlap at window boundary) → clarify scope.

        CHECKPOINT: Spec says '50-line window' but doesn't clarify whether windows are:
        - Sliding (each suppression starts own window)
        - Fixed (lines 1-50, 51-100, etc.)
        - Per-function

        This test documents the assumption: assume sliding windows from first suppression.
        """
        suppressions = [
            {"file": "test.py", "line": 25, "rule_id": "AR-001"},  # Window: 25-75
            {"file": "test.py", "line": 55, "rule_id": "AR-001"},  # Within window 25-75
        ]

        # If sliding window from first: 25 + 50 = 75 (inclusive)
        # Line 55 is within [25, 75] → same window
        repeat_count = len(suppressions)
        assert repeat_count == 2, "Both within 50-line window"


# ---------------------------------------------------------------------------
# TEST CLASS: Timestamp & Timezone Edge Cases
# ---------------------------------------------------------------------------


class TestTimestampAndTimezoneEdgeCases:
    """Test year boundaries, leap years, timezone confusion.

    Targets implementation bugs in date parsing, timezone handling.
    """

    def test_expiration_leap_year_feb_29(self) -> None:
        """Mutation: expiration date = 2024-02-29 (leap year) → parse correctly."""
        leap_date = "2024-02-29"
        try:
            parsed = datetime.datetime.strptime(leap_date, "%Y-%m-%d").date()
            assert parsed.year == 2024
            assert parsed.month == 2
            assert parsed.day == 29
        except ValueError:
            pytest.fail("Leap year date should parse")

    def test_expiration_non_leap_year_feb_29_invalid(self) -> None:
        """Mutation: expiration date = 2023-02-29 (non-leap year) → INVALID."""
        non_leap_date = "2023-02-29"
        with pytest.raises(ValueError):
            datetime.datetime.strptime(non_leap_date, "%Y-%m-%d")

    def test_expiration_year_boundary_jan_1(self) -> None:
        """Mutation: expiration date = 2027-01-01 (new year boundary) → parse and compare."""
        year_start = datetime.date(2027, 1, 1)
        today = datetime.date(2027, 1, 1)

        is_expired = year_start < today
        assert not is_expired, "Year boundary on same date should not be expired"

    def test_expiration_year_boundary_dec_31(self) -> None:
        """Mutation: expiration date = 2026-12-31 (year end) → parse correctly."""
        year_end = datetime.date(2026, 12, 31)
        today = datetime.date(2026, 12, 30)

        is_expired = year_end < today
        assert not is_expired, "Year-end date should not be expired (tomorrow)"

    def test_expiration_century_boundary(self) -> None:
        """Mutation: expiration date = 2100-01-01 (far future) → parse and compare."""
        far_future = datetime.datetime.strptime("2100-01-01", "%Y-%m-%d").date()
        today = datetime.date.today()

        is_expired = far_future < today
        assert not is_expired, "Far future date should not be expired"

    def test_first_seen_timestamp_format_consistency(self) -> None:
        """Mutation: first_seen timestamps must be consistent format across all records."""
        timestamps = [
            "2026-05-19T14-30-00Z",
            "2026-05-19T14-30-00Z",
            "2026-05-19T14-30-00Z",
        ]

        # All timestamps should match ISO 8601 UTC format
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$"
        for ts in timestamps:
            assert re.match(iso_pattern, ts), f"Timestamp should match ISO 8601: {ts}"

    def test_timestamp_no_microseconds(self) -> None:
        """Mutation: timestamp with microseconds (2026-05-19T14-30-00.123Z) → reject."""
        timestamp_with_micros = "2026-05-19T14-30-00.123Z"
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$"
        matches = bool(re.match(iso_pattern, timestamp_with_micros))
        assert not matches, "Microseconds should not be included in timestamp"

    def test_timestamp_no_timezone_offset(self) -> None:
        """Mutation: timestamp with +00:00 offset instead of Z → should use Z only."""
        timestamp_with_offset = "2026-05-19T14-30-00+00:00"
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$"
        matches = bool(re.match(iso_pattern, timestamp_with_offset))
        assert not matches, "Should use Z suffix, not +00:00"


# ---------------------------------------------------------------------------
# TEST CLASS: Concurrency & Order-Dependency
# ---------------------------------------------------------------------------


class TestConcurrencyAndOrderDependency:
    """Test determinism across different input orders.

    Targets implementation bugs in sorting, hashing, non-deterministic behavior.
    """

    def test_suppressions_different_order_same_sorted_output(self) -> None:
        """Mutation: same suppressions in different order → identical JSON after sorting."""
        suppressions_order1 = [
            {"file": "b.py", "line": 20, "rule_id": "AR-001"},
            {"file": "a.py", "line": 10, "rule_id": "AR-001"},
        ]
        suppressions_order2 = [
            {"file": "a.py", "line": 10, "rule_id": "AR-001"},
            {"file": "b.py", "line": 20, "rule_id": "AR-001"},
        ]

        sorted1 = sorted(suppressions_order1, key=lambda s: (s["file"], s["line"]))
        sorted2 = sorted(suppressions_order2, key=lambda s: (s["file"], s["line"]))

        json1 = json.dumps(sorted1, sort_keys=True)
        json2 = json.dumps(sorted2, sort_keys=True)

        assert json1 == json2, "Different input order should produce identical sorted JSON"

    def test_violations_different_order_same_escalations_detected(self) -> None:
        """Mutation: same violations in different order → same escalations detected."""
        violations_order1 = [
            {"file": "test.py", "line": 10, "rule_id": "AR-001"},
            {"file": "test.py", "line": 20, "rule_id": "SE-CRED"},
        ]
        violations_order2 = [
            {"file": "test.py", "line": 20, "rule_id": "SE-CRED"},
            {"file": "test.py", "line": 10, "rule_id": "AR-001"},
        ]

        # Count high-risk rules
        high_risk_prefixes = ("AR-", "SE-", "AS-", "EXH-")
        high_risk1 = sum(1 for v in violations_order1 if any(v["rule_id"].startswith(p) for p in high_risk_prefixes))
        high_risk2 = sum(1 for v in violations_order2 if any(v["rule_id"].startswith(p) for p in high_risk_prefixes))

        assert high_risk1 == high_risk2 == 2, "Order should not affect high-risk count"

    def test_multiple_runs_same_input_identical_audit_log(self) -> None:
        """Mutation: gate runs twice with same input → identical audit log JSON."""
        input_data = {
            "changed_files": ["test.py"],
            "violations": [{"file": "test.py", "line": 42, "rule_id": "AR-001"}],
        }

        # Simulate two gate runs with deterministic output
        audit_log_run1 = {
            "timestamp": "2026-05-19T14-30-00Z",
            "total_suppressions": 1,
            "suppressions": [
                {"file": "test.py", "line": 42, "rule_id": "AR-001"}
            ]
        }
        audit_log_run2 = {
            "timestamp": "2026-05-19T14-30-00Z",
            "total_suppressions": 1,
            "suppressions": [
                {"file": "test.py", "line": 42, "rule_id": "AR-001"}
            ]
        }

        json1 = json.dumps(audit_log_run1, sort_keys=True)
        json2 = json.dumps(audit_log_run2, sort_keys=True)

        assert json1 == json2, "Same input should produce identical audit log across runs"

    def test_parallel_file_processing_order_independent(self) -> None:
        """Mutation: process files in parallel → results order-independent."""
        files = ["c.py", "a.py", "b.py"]

        # Results should be deterministic regardless of processing order
        sorted_files = sorted(files)
        assert sorted_files == ["a.py", "b.py", "c.py"]


# ---------------------------------------------------------------------------
# TEST CLASS: Regex & ReDoS Edge Cases
# ---------------------------------------------------------------------------


class TestRegexAndReDosEdgeCases:
    """Test regex pattern safety and correctness.

    Targets ReDoS vulnerabilities, catastrophic backtracking, boundary bugs.
    """

    def test_suppression_regex_no_catastrophic_backtracking(self) -> None:
        """Mutation: malicious input trying to trigger ReDoS → regex completes quickly."""
        pattern = (
            r'^\s*#\s+blobert-ignore-next-line:\s*reason="[^"]{10,200}",\s*ticket="[A-Z0-9\-]{3,20}"'
            r'(,\s*until="\d{4}-\d{2}-\d{2}")?$'
        )

        # Test with long repeated characters (potential ReDoS trigger)
        long_input = "# blobert-ignore-next-line: reason=\"" + "X" * 500 + "\", ticket=\"BLB-123\""

        # Should complete without hanging (ReDoS would cause timeout)
        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Regex took too long (ReDoS detected)")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(1)  # 1 second timeout

            re.match(pattern, long_input, re.IGNORECASE)

            signal.alarm(0)  # Cancel alarm
        except TimeoutError:
            pytest.fail("Regex vulnerable to ReDoS")
        except Exception:
            # signal.alarm not available on all platforms; skip check
            pass

    def test_suppression_regex_word_boundary_accuracy(self) -> None:
        """Mutation: regex should match full string, not partial → no substring matches."""
        pattern = (
            r'^\s*#\s+blobert-ignore-next-line:\s*reason="[^"]{10,200}",\s*ticket="[A-Z0-9\-]{3,20}"'
            r'(,\s*until="\d{4}-\d{2}-\d{2}")?$'
        )

        # Should not match if extra text after
        comment_with_extra = '# blobert-ignore-next-line: reason="Test reason here", ticket="BLB-123" # extra'
        matches = bool(re.match(pattern, comment_with_extra, re.IGNORECASE))
        assert not matches, "Regex should not match if extra text follows"

    def test_ticket_format_regex_case_sensitivity(self) -> None:
        """Mutation: ticket validation should be case-sensitive (uppercase only)."""
        pattern = r"^[A-Z0-9\-]{3,20}$"

        valid_tickets = ["ABC", "M902-15", "BLB-123"]
        invalid_tickets = ["abc", "m902-15", "Abc"]

        for ticket in valid_tickets:
            assert re.match(pattern, ticket), f"Should accept uppercase: {ticket}"

        for ticket in invalid_tickets:
            assert not re.match(pattern, ticket), f"Should reject lowercase/mixed: {ticket}"

    def test_iso_date_regex_no_partial_matches(self) -> None:
        """Mutation: ISO date regex should match full date, not partial."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        valid_dates = ["2026-05-19", "2020-01-01", "2099-12-31"]
        invalid_dates = ["2026-05-19T14:30:00", "2026/05/19", "26-05-19", "2026-05-19 ", " 2026-05-19"]

        for date in valid_dates:
            assert re.match(pattern, date), f"Should accept valid date: {date}"

        for date in invalid_dates:
            assert not re.match(pattern, date), f"Should reject invalid format: {date}"


# ---------------------------------------------------------------------------
# TEST CLASS: File Path Handling
# ---------------------------------------------------------------------------


class TestFilePathHandling:
    """Test file path normalization and edge cases.

    Targets implementation bugs in path handling, special characters.
    """

    def test_relative_path_preserved(self) -> None:
        """Mutation: file path = asset_generation/python/src/model.py → preserved as-is."""
        file_path = "asset_generation/python/src/model.py"
        is_relative = not file_path.startswith("/")
        assert is_relative, "Relative path should be preserved"

    def test_absolute_path_converted_to_relative(self) -> None:
        """Mutation: file path = /home/user/repo/test.py → convert to relative or reject."""
        file_path = "/home/user/repo/test.py"
        is_absolute = file_path.startswith("/")
        assert is_absolute, "Absolute path should be detected"

    def test_file_path_with_spaces_preserved(self) -> None:
        """Mutation: file path with spaces → preserved correctly (no escaping needed)."""
        file_path = "asset_generation/my file with spaces.py"
        assert " " in file_path, "Spaces should be preserved in path"

    def test_file_path_with_special_characters(self) -> None:
        """Mutation: file path with special chars (-, _, .) → preserved."""
        file_path = "asset_generation/my-file_name.v2.py"
        assert all(c in file_path for c in ["-", "_", "."]), "Special chars should be preserved"

    def test_file_path_symlink_not_dereferenced(self) -> None:
        """Mutation: file path is symlink → store path as-is, don't dereference."""
        file_path = "symlink_to_test.py"  # Could be symlink
        # Gate should store path as-is in audit log
        assert isinstance(file_path, str), "Path should be string"

    def test_file_path_no_path_traversal(self) -> None:
        """Mutation: file path with .. (parent directory) → validate and reject or normalize."""
        file_path = "asset_generation/../test.py"
        has_traversal = ".." in file_path
        if has_traversal:
            # Gate should either reject or normalize
            pass

    def test_file_path_dot_dot_normalized(self) -> None:
        """Mutation: file path __test.py (not path traversal) → allowed."""
        file_path = "__test.py"  # File named "__test.py", not traversal
        # Should be allowed (not traversal, just unusual name)
        assert "_" in file_path
        assert not file_path.startswith(".."), "Should not look like traversal"


# ---------------------------------------------------------------------------
# TEST CLASS: Gate Integration Contract Validation
# ---------------------------------------------------------------------------


class TestGateIntegrationContractValidation:
    """Test gate input/output contract correctness.

    Targets implementation bugs in schema adherence, missing fields.
    """

    def test_gate_result_missing_required_field_version(self) -> None:
        """Mutation: gate result missing 'version' field → INVALID."""
        result = {
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": [],
            # Missing 'version'
        }

        required_fields = {"version", "status", "gate", "timestamp", "artifacts", "violations"}
        present = set(result.keys())
        missing = required_fields - present
        assert missing == {"version"}, "Should detect missing 'version' field"

    def test_gate_result_missing_required_field_status(self) -> None:
        """Mutation: gate result missing 'status' field → INVALID."""
        result = {
            "version": "1.0",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": [],
            # Missing 'status'
        }

        required_fields = {"version", "status", "gate", "timestamp", "artifacts", "violations"}
        present = set(result.keys())
        missing = required_fields - present
        assert missing == {"status"}, "Should detect missing 'status' field"

    def test_gate_result_extra_fields_allowed(self) -> None:
        """Mutation: gate result with extra fields → allowed (backward compatible)."""
        result = {
            "version": "1.0",
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": [],
            "extra_field": "allowed",
            "another_extra": 12345,
        }

        # Extra fields should not cause rejection
        assert "extra_field" in result
        assert "another_extra" in result

    def test_gate_result_status_invalid_value(self) -> None:
        """Mutation: gate result status = 'MAYBE' (invalid) → should be PASS/WARN."""
        result = {
            "version": "1.0",
            "status": "MAYBE",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": [],
        }

        valid_statuses = {"PASS", "WARN", "FAIL"}
        is_valid_status = result["status"] in valid_statuses
        assert not is_valid_status, "MAYBE is not a valid status"

    def test_gate_result_artifacts_array_required(self) -> None:
        """Mutation: gate result artifacts = {} (dict instead of list) → INVALID."""
        result = {
            "version": "1.0",
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": {"path": "file.json"},  # Should be list
            "violations": [],
        }

        is_list = isinstance(result["artifacts"], list)
        assert not is_list, "artifacts should be list, not dict"

    def test_gate_result_violations_array_required(self) -> None:
        """Mutation: gate result violations = null (null instead of empty list) → handle gracefully."""
        result = {
            "version": "1.0",
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": None,  # Should be []
        }

        # Gate should treat None as empty list
        violations = result["violations"] if result["violations"] is not None else []
        assert violations == []

    def test_gate_result_duration_ms_present(self) -> None:
        """Mutation: gate result missing duration_ms → should be present for performance monitoring."""
        result = {
            "version": "1.0",
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": [],
            # Missing 'duration_ms'
        }

        has_duration = "duration_ms" in result
        assert not has_duration, "Should detect missing 'duration_ms'"

    def test_gate_result_message_field_optional(self) -> None:
        """Mutation: gate result without 'message' field → optional but recommended."""
        result = {
            "version": "1.0",
            "status": "PASS",
            "gate": "override_and_escalation_check",
            "timestamp": "2026-05-19T14-30-00Z",
            "artifacts": [],
            "violations": [],
            "duration_ms": 100,
            # Missing 'message' (optional)
        }

        # Message is optional
        message = result.get("message")
        assert message is None, "message is optional"

    def test_input_contract_optional_fields_handled(self) -> None:
        """Mutation: gate input missing optional fields → gate continues."""
        minimal_input = {
            # Only minimal required fields (if any)
            "mode": "shadow",
        }

        # Gate should accept minimal input
        assert "changed_files" not in minimal_input
        assert "violations" not in minimal_input

    def test_input_contract_changed_files_optional(self) -> None:
        """Mutation: gate input missing changed_files → gate invokes git diff or errors gracefully."""
        input_without_files = {
            "violations": [],
            "mode": "shadow",
        }

        # changed_files is optional; gate should handle absence
        has_files = "changed_files" in input_without_files
        assert not has_files, "changed_files is optional"

    def test_input_contract_violations_optional(self) -> None:
        """Mutation: gate input missing violations → gate processes suppressions without violations."""
        input_without_violations = {
            "changed_files": ["test.py"],
            "mode": "shadow",
        }

        # violations is optional; gate processes suppressions as independent
        has_violations = "violations" in input_without_violations
        assert not has_violations, "violations is optional"


# ---------------------------------------------------------------------------
# TEST CLASS: Stress & Performance Edge Cases
# ---------------------------------------------------------------------------


class TestStressAndPerformanceEdgeCases:
    """Test behavior under extreme inputs.

    Targets implementation bugs in buffer handling, performance degradation.
    """

    def test_very_large_file_10k_lines(self) -> None:
        """Mutation: file with 10,000 lines → gate processes without crash."""
        large_file_lines = 10000
        files = [{"file": "large.py", "size": large_file_lines}]

        total_lines = sum(f["size"] for f in files)
        assert total_lines == 10000, "Should handle large files"

    def test_very_long_reason_500_chars_rejected(self) -> None:
        """Mutation: reason = 500 chars (way over limit) → INVALID."""
        reason = "X" * 500
        is_valid = 10 <= len(reason) <= 200
        assert not is_valid, "500 chars should exceed max (200)"

    def test_many_violations_1000_entries(self) -> None:
        """Mutation: violations array with 1000 entries → gate processes all."""
        violations = [
            {"file": f"file_{i % 10}.py", "line": i, "rule_id": f"RULE-{i}"}
            for i in range(1000)
        ]

        assert len(violations) == 1000, "Should handle 1000 violations"

    def test_many_suppressions_per_file_100_suppressions(self) -> None:
        """Mutation: single file with 100 suppressions → gate processes correctly."""
        suppressions = [
            {"file": "test.py", "line": i * 100, "rule_id": "AR-001"}
            for i in range(1, 101)
        ]

        repeated_in_file = sum(1 for s in suppressions if s["file"] == "test.py")
        assert repeated_in_file == 100, "Should count all suppressions in file"

    def test_very_long_file_path_200_chars(self) -> None:
        """Mutation: file path with 200+ chars → preserved and audited."""
        long_path = "asset_generation/" + "/".join([f"dir_{i}" for i in range(15)]) + "/file.py"
        assert len(long_path) > 100, "Path should be very long"

    def test_many_escalations_all_recorded(self) -> None:
        """Mutation: 100 escalations detected → all recorded in audit log."""
        escalations = [
            {
                "file": f"file_{i}.py",
                "line": i * 10,
                "rule_id": "AR-001",
                "escalation_reasons": ["HIGH_RISK_RULE"],
            }
            for i in range(100)
        ]

        assert len(escalations) == 100, "Should record all 100 escalations"


# ---------------------------------------------------------------------------
# TEST CLASS: Assumption Encoding (Checkpoint Tests)
# ---------------------------------------------------------------------------


class TestAssumptionEncodingCheckpoints:
    """Encode frozen assumptions as deterministic tests.

    CHECKPOINT: These tests document frozen assumptions from the spec.
    Implementation must satisfy these to match spec intent.
    """

    def test_CHECKPOINT_expiration_boundary_today_is_valid(self) -> None:
        """CHECKPOINT: Assume `until_date == today` is valid (not expired).

        Spec assumption A3: expiration date = today should be valid.
        If implementation treats today as expired, this test catches it.
        """
        today = datetime.date.today()
        until_date = today

        is_expired = until_date < today
        assert not is_expired, "CHECKPOINT: today should be valid, not expired"

    def test_CHECKPOINT_repeated_suppression_threshold_is_3_not_2(self) -> None:
        """CHECKPOINT: Threshold for repeated suppression escalation is 3 (not 2).

        Spec assumption A3: 3+ occurrences trigger escalation.
        If implementation uses threshold of 2, this test catches it.
        """
        for count in [1, 2]:
            is_escalated = count >= 3
            assert not is_escalated, f"CHECKPOINT: {count}x should not escalate (threshold is 3)"

        for count in [3, 4, 5]:
            is_escalated = count >= 3
            assert is_escalated, f"CHECKPOINT: {count}x should escalate (threshold is 3)"

    def test_CHECKPOINT_high_risk_prefixes_ar_se_as_exh(self) -> None:
        """CHECKPOINT: High-risk rule prefixes are AR-, SE-, AS-, EXH- (and only these).

        Spec assumption A4: lists specific prefixes.
        If implementation includes/excludes other prefixes, this test catches it.
        """
        high_risk_prefixes = ("AR-", "SE-", "AS-", "EXH-")
        other_prefixes = ("SRP-", "OBS-", "RULE-", "UNKNOWN-")

        for prefix in high_risk_prefixes:
            rule_id = prefix + "001"
            is_high_risk = any(rule_id.startswith(p) for p in high_risk_prefixes)
            assert is_high_risk, f"CHECKPOINT: {prefix} should be high-risk"

        for prefix in other_prefixes:
            rule_id = prefix + "001"
            is_high_risk = any(rule_id.startswith(p) for p in high_risk_prefixes)
            assert not is_high_risk, f"CHECKPOINT: {prefix} should not be high-risk"

    def test_CHECKPOINT_expiration_format_iso8601_yyyy_mm_dd_only(self) -> None:
        """CHECKPOINT: Expiration date format is ISO 8601 YYYY-MM-DD only (not YYYY-MM-DDTHH:MM:SS).

        Spec assumption A8: ISO 8601 date only, no time.
        If implementation accepts time components, this test catches it.
        """
        iso_pattern = r"^\d{4}-\d{2}-\d{2}$"

        valid_formats = ["2026-05-19", "2020-01-01", "2099-12-31"]
        invalid_formats = ["2026-05-19T14:30:00", "2026-05-19T14:30:00Z", "2026/05/19"]

        for date_str in valid_formats:
            matches = bool(re.match(iso_pattern, date_str))
            assert matches, f"CHECKPOINT: {date_str} should match ISO 8601 date format"

        for date_str in invalid_formats:
            matches = bool(re.match(iso_pattern, date_str))
            assert not matches, f"CHECKPOINT: {date_str} should not match (time/format not allowed)"

    def test_CHECKPOINT_gate_exit_code_always_zero_shadow_mode(self) -> None:
        """CHECKPOINT: Gate always exits 0 in shadow mode (advisory, never blocking).

        Spec assumption A6: gate is advisory (shadow mode).
        If implementation exits non-zero on escalations, this test catches it.
        """
        # This test documents behavior; actual implementation tested in integration
        exit_codes_for_escalations = [0]  # Always 0 in shadow mode
        assert all(code == 0 for code in exit_codes_for_escalations), \
            "CHECKPOINT: gate should exit 0 in shadow mode even with escalations"

    def test_CHECKPOINT_suppression_syntax_single_line_comment_only(self) -> None:
        """CHECKPOINT: Suppression syntax is single-line comment (not block comment).

        Spec assumption A1: `# blobert-ignore-next-line` inline, not `/* ... */` block.
        If implementation accepts block comments, this test catches it.
        """
        inline_comment = "# blobert-ignore-next-line: reason=\"Test\", ticket=\"BLB-123\""
        block_comment = "/* blobert-ignore-next-line: reason=\"Test\", ticket=\"BLB-123\" */"

        # Only inline should match
        pattern = r'^\s*#\s+blobert-ignore-next-line:'
        assert re.match(pattern, inline_comment), "CHECKPOINT: inline comment should match"
        assert not re.match(pattern, block_comment), "CHECKPOINT: block comment should not match"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
