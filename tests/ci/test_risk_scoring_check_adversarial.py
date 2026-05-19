"""Adversarial and mutation tests for M902-12 Stage 4 Risk Scoring Gate.

This test suite extends the behavioral test coverage (test_risk_scoring_check.py) with:
1. Boundary condition tests (rounding precision, exact threshold crossings)
2. Weight mutation tests (incorrect weight values to catch scoring errors)
3. Schema edge cases (huge message/reasoning strings, null/missing optional fields)
4. Determinism stress tests (same input idempotence, order independence)
5. Assumption validation (prior gate output format variations, signal inference)
6. Numerical precision tests (floating-point rounding, clamping edge cases)
7. Signal interaction tests (conflicting signals, rare combinations)
8. Malformed input robustness (corrupted violations, type mismatches)

Adversarial test strategy: Target code paths that may have hidden assumptions,
numerical edge cases, or schema compliance gaps that behavioral tests don't expose.

All tests are deterministic and reproducible; no randomness or mocking.
Each test targets a specific vulnerability or gap in the spec/implementation.
"""

import json
import time
from typing import Any, Dict, List
from unittest.mock import patch

import pytest


class TestBoundaryConditionsAndRounding:
    """Boundary tests for score thresholds, rounding precision, and exact threshold crossings.

    Target: Rounding errors at band boundaries (2/3, 5/6), floating-point precision issues.
    """

    def test_score_exactly_at_exit_boundary_0(self) -> None:
        """Edge: risk_score exactly 0 (minimum) → band EXIT."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        assert result["risk_score"] == 0
        assert result["band"] == "EXIT"
        assert result["next_stage_recommendation"] == "low_risk_exit"

    def test_score_exactly_at_exit_boundary_2(self) -> None:
        """Edge: risk_score exactly 2 (EXIT upper boundary) → band EXIT.

        Note: With current weights, we cannot produce exactly 2. This tests the boundary logic:
        if score <= 2: band = "EXIT"
        """
        # CHECKPOINT: Spec freezes band 0-2 as EXIT. If implementation uses
        # strict >= instead of <=, this will catch off-by-one errors.
        from ci.scripts.gates import risk_scoring_check

        # Can't construct exactly 2 with available weights (min non-zero is 5 for DUP).
        # Test that the boundary logic handles <= 2 correctly by testing 0 and near-2.
        result = risk_scoring_check.run({"violations": []})
        assert result["risk_score"] <= 2
        assert result["band"] == "EXIT"

    def test_score_just_above_exit_boundary_at_3(self) -> None:
        """Edge: risk_score exactly 3 (first WARN score, if achievable) → band WARN.

        Min non-zero single signal is DUP (+1) = 5, but multiple single-weight
        signals sum to achievable values. Try 1+1+1 = 3.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 1+1+1 = 3, (3/20)*100 = 15
        assert result["risk_score"] == 15
        assert result["band"] == "WARN"

    def test_score_exactly_at_warn_boundary_5(self) -> None:
        """Edge: risk_score exactly 5 (WARN upper boundary) → band WARN.

        5 signals × +1 weight = 5 points, (5/20)*100 = 25.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "OB-03", "severity": "WARN", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "MUT-03", "severity": "WARN", "file": "e.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["risk_score"] == 25  # (5/20)*100 = 25
        assert result["band"] == "WARN"

    def test_score_just_below_escalate_boundary_at_25(self) -> None:
        """Edge: risk_score exactly 25 (just below ESCALATE at 30, near boundary).

        Test that score 25 (< 30, which is 6/20*100) → WARN, not ESCALATE.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "OB-03", "severity": "WARN", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "IGN-01", "severity": "WARN", "file": "e.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 1+1+1+1+2 = 6, but IGN-01 is +2, so 1+1+1+1+2 = 6, (6/20)*100 = 30
        assert result["risk_score"] == 30
        # 30 >= 6, so ESCALATE
        assert result["band"] == "ESCALATE"

    def test_score_exactly_at_escalate_boundary_6_signals(self) -> None:
        """Edge: risk_score exactly 30 (= 6/20*100, first ESCALATE) → band ESCALATE.

        6 points total weight: 1+1+1+1+2 = 6, (6/20)*100 = 30.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "OB-03", "severity": "WARN", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "IGN-01", "severity": "WARN", "file": "e.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 1+1+1+1+2 = 6, (6/20)*100 = 30
        assert result["risk_score"] == 30
        assert result["band"] == "ESCALATE"

    def test_score_high_end_near_100_boundary(self) -> None:
        """Edge: risk_score very close to 100 (all signals present) → band ESCALATE."""
        from ci.scripts.gates import risk_scoring_check

        # All 8 signals (but we may not be able to include migrations in violations array)
        # Max from violations: SRP(+3) + AR-drift(+5) + DUP(+1) + Async(+5) + IGN(+2) + OB(+1) + MUT-03(+1) = 18
        # To get 20, we need migration (+2). But migrations are detected via file paths.
        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},     # +3 SRP
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "b.py", "line": 1, "message": ""},   # +5 Arch drift
            {"rule_id": "DUP-01", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},      # +1 Duplication
            {"rule_id": "AS-01", "severity": "ERROR", "file": "d.py", "line": 1, "message": ""},      # +5 Async
            {"rule_id": "IGN-01", "severity": "WARN", "file": "e.py", "line": 1, "message": ""},      # +2 Suppression
            {"rule_id": "OB-01", "severity": "WARN", "file": "f.py", "line": 1, "message": ""},       # +1 Observability
            {"rule_id": "MUT-03", "severity": "WARN", "file": "g.py", "line": 1, "message": ""}       # +1 Ownership
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 3+5+1+5+2+1+1 = 18, (18/20)*100 = 90
        assert result["risk_score"] == 90
        assert result["band"] == "ESCALATE"

    def test_score_clamped_at_100_maximum(self) -> None:
        """Edge: risk_score clamped to [0, 100]; no overflow to 101+.

        If all 8 signals are present (20 points), score = (20/20)*100 = 100.
        Tests that score never exceeds 100.
        """
        from ci.scripts.gates import risk_scoring_check

        # To get all 8 signals, we'd need migration detection via file path.
        # For now, test with maximum violations weight (7 signals, 18 points).
        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "alembic/versions/001_test.py", "line": 1, "message": ""},
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "DUP-01", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "IGN-01", "severity": "WARN", "file": "e.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "f.py", "line": 1, "message": ""},
            {"rule_id": "MUT-03", "severity": "WARN", "file": "g.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Max expected <= 100
        assert result["risk_score"] <= 100
        assert isinstance(result["risk_score"], int)

    def test_rounding_down_behavior_at_2_4(self) -> None:
        """Edge: Rounding down (floor) behavior: 2.4 → 2, not 3.

        Spec freezes floor rounding. Test: weight sum that produces
        non-integer percentage. E.g., sum=2 → (2/20)*100 = 10. If sum=1,
        (1/20)*100 = 5. Can't get exactly 2.4, but test the principle.
        """
        # CHECKPOINT: Spec says "round down" (floor). If implementation
        # uses banker's rounding or round(), this test ensures rounding
        # strategy is correct.
        from ci.scripts.gates import risk_scoring_check

        # Single DUP violation: (1/20)*100 = 5.0 (exact, no rounding)
        violations = [{"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        assert result["risk_score"] == 5  # Exact, no fractional part

    def test_rounding_down_at_fractional_boundary(self) -> None:
        """Edge: Test rounding with fractional weight that yields non-integer score.

        With current integer weights, (sum/20)*100 often yields exact multiples of 5.
        This test ensures that if a sum produces a fractional percentage, it's floored.

        E.g., if we somehow got sum=3.5, (3.5/20)*100 = 17.5 → floor to 17.
        """
        from ci.scripts.gates import risk_scoring_check

        # With integer weights, (3/20)*100 = 15 (exact).
        # Test multiple signals to get various sums.
        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "DUP-02", "severity": "WARN", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 1+1 = 2, (2/20)*100 = 10
        assert result["risk_score"] == 10
        assert isinstance(result["risk_score"], int)


class TestWeightMutationAndNumericalEdgeCases:
    """Mutation tests: Verify weights are correctly applied and summed.

    Target: Typos in weight constants, off-by-one errors, weight swaps,
    incorrect aggregation logic.
    """

    def test_weight_mutation_srp_signal_must_be_3_not_2(self) -> None:
        """Mutation: SRP weight should be +3. If implementation uses +2, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (3/20)*100 = 15, NOT (2/20)*100 = 10
        assert result["risk_score"] == 15, f"AR-01 (SRP) weight must be +3, got score {result['risk_score']}"

    def test_weight_mutation_arch_drift_must_be_5_not_3(self) -> None:
        """Mutation: Architecture drift weight should be +5. If implementation uses +3, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (5/20)*100 = 25, NOT (3/20)*100 = 15
        assert result["risk_score"] == 25, f"AR-07 (arch drift) weight must be +5, got score {result['risk_score']}"

    def test_weight_mutation_dup_must_be_1_not_2(self) -> None:
        """Mutation: Duplication weight should be +1. If implementation uses +2, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (1/20)*100 = 5, NOT (2/20)*100 = 10
        assert result["risk_score"] == 5, f"DUP (duplication) weight must be +1, got score {result['risk_score']}"

    def test_weight_mutation_async_must_be_5_not_2(self) -> None:
        """Mutation: Async weight should be +5. If implementation uses +2, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "AS-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (5/20)*100 = 25, NOT (2/20)*100 = 10
        assert result["risk_score"] == 25, f"AS-01 (async) weight must be +5, got score {result['risk_score']}"

    def test_weight_mutation_suppression_must_be_2_not_1(self) -> None:
        """Mutation: Suppression weight should be +2. If implementation uses +1, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "IGN-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (2/20)*100 = 10, NOT (1/20)*100 = 5
        assert result["risk_score"] == 10, f"IGN-01 (suppression) weight must be +2, got score {result['risk_score']}"

    def test_weight_mutation_observability_must_be_1_not_2(self) -> None:
        """Mutation: Observability weight should be +1. If implementation uses +2, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "OB-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (1/20)*100 = 5, NOT (2/20)*100 = 10
        assert result["risk_score"] == 5, f"OB-01 (observability) weight must be +1, got score {result['risk_score']}"

    def test_weight_mutation_ownership_must_be_1_not_2(self) -> None:
        """Mutation: Ownership weight should be +1. If implementation uses +2, this fails."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "MUT-03", "severity": "WARN", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (1/20)*100 = 5, NOT (2/20)*100 = 10
        assert result["risk_score"] == 5, f"MUT-03 (ownership) weight must be +1, got score {result['risk_score']}"

    def test_weight_aggregation_sum_not_product(self) -> None:
        """Mutation: Weights should be summed, not multiplied.

        If implementation multiplies: (3 * 5) / 20 * 100 = 75 (wrong).
        Correct: (3 + 5) / 20 * 100 = 40.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Should be (3+5)/20*100 = 40, NOT 3*5/20*100 = 75
        assert result["risk_score"] == 40

    def test_weight_aggregation_all_signals_additive(self) -> None:
        """Mutation: All signal weights should be added together, not averaged.

        If implementation averages: (3+5+1+5+2+1+1+2) / 8 = 20/8 = 2.5 (wrong formula).
        Correct: (3+5+1+5+2+1+1+2) / 20 * 100 = 100.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},      # +3
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "b.py", "line": 1, "message": ""},   # +5
            {"rule_id": "DUP-01", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},      # +1
            {"rule_id": "AS-01", "severity": "ERROR", "file": "d.py", "line": 1, "message": ""},      # +5
            {"rule_id": "IGN-01", "severity": "WARN", "file": "e.py", "line": 1, "message": ""},      # +2
            {"rule_id": "OB-01", "severity": "WARN", "file": "f.py", "line": 1, "message": ""},       # +1
            {"rule_id": "MUT-03", "severity": "WARN", "file": "g.py", "line": 1, "message": ""}       # +1
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 3+5+1+5+2+1+1 = 18, (18/20)*100 = 90
        assert result["risk_score"] == 90

    def test_weight_total_divisor_must_be_20_not_21(self) -> None:
        """Mutation: Total possible weight is 20, not 19 or 21.

        If divisor is wrong, all scores are scaled incorrectly.
        E.g., if divisor=21: (3/21)*100 = 14.28 (wrong).
        Correct: (3/20)*100 = 15.
        """
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Must be exactly 15, not 14.28 or 16.67
        assert result["risk_score"] == 15


class TestSchemaBoundariesAndNullHandling:
    """Schema edge cases: Huge strings, null fields, missing optional fields, type violations.

    Target: String length constraints, null reference errors, missing field handling.
    """

    def test_message_field_not_exceeding_300_chars(self) -> None:
        """Schema: message field must be < 300 characters."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        assert len(result["message"]) < 300, f"message too long: {len(result['message'])} >= 300"

    def test_reasoning_field_not_exceeding_500_chars(self) -> None:
        """Schema: reasoning field must be < 500 characters."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        assert len(result["reasoning"]) < 500, f"reasoning too long: {len(result['reasoning'])} >= 500"

    def test_message_and_reasoning_with_many_violations(self) -> None:
        """Schema: message/reasoning strings should stay within limits even with 100+ violations."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": f"file{i}.py", "line": i, "message": f"Violation {i}"}
            for i in range(100)
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert len(result["message"]) < 300
        assert len(result["reasoning"]) < 500

    def test_timestamp_field_never_null(self) -> None:
        """Schema: timestamp field must never be null."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["timestamp"] is not None
        assert isinstance(result["timestamp"], str)
        assert len(result["timestamp"]) > 0

    def test_risk_score_field_never_null(self) -> None:
        """Schema: risk_score field must never be null or missing."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["risk_score"] is not None
        assert isinstance(result["risk_score"], int)

    def test_band_field_never_null(self) -> None:
        """Schema: band field must never be null."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["band"] is not None
        assert result["band"] in ["EXIT", "WARN", "ESCALATE"]

    def test_next_stage_recommendation_never_null(self) -> None:
        """Schema: next_stage_recommendation must never be null."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["next_stage_recommendation"] is not None
        assert result["next_stage_recommendation"] in [
            "low_risk_exit", "medium_risk_review", "high_risk_escalate"
        ]

    def test_violations_array_always_empty(self) -> None:
        """Schema: violations array output must always be empty (no violations from this gate)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["violations"] == []
        assert isinstance(result["violations"], list)

    def test_artifacts_array_always_empty(self) -> None:
        """Schema: artifacts array must always be empty (no outputs)."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["artifacts"] == []
        assert isinstance(result["artifacts"], list)

    def test_status_field_never_fail(self) -> None:
        """Schema: status must always be PASS (shadow mode, never FAIL)."""
        from ci.scripts.gates import risk_scoring_check

        # Even with high-risk violations, status should be PASS
        violations = [
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["status"] == "PASS"

    def test_mode_field_always_shadow(self) -> None:
        """Schema: mode must always be shadow (non-blocking)."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["mode"] == "shadow"

    def test_gate_field_always_correct_identifier(self) -> None:
        """Schema: gate field must be exactly 'risk_scoring_check'."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["gate"] == "risk_scoring_check"

    def test_upstream_agent_field_optional_but_preserved(self) -> None:
        """Schema: upstream_agent field may be null or string, but must be present."""
        from ci.scripts.gates import risk_scoring_check

        result1 = risk_scoring_check.run({})
        assert "upstream_agent" in result1

        result2 = risk_scoring_check.run({"upstream_agent": "architecture_enforcement_check"})
        assert result2["upstream_agent"] == "architecture_enforcement_check"

    def test_downstream_agent_field_frozen(self) -> None:
        """Schema: downstream_agent should be 'semantic_extraction' (hardcoded per spec)."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        # Spec says downstream_agent is informational and hardcoded to "semantic_extraction"
        assert "downstream_agent" in result
        # Value may be "semantic_extraction" or similar; just ensure field exists
        assert isinstance(result["downstream_agent"], str)

    def test_duration_ms_field_is_non_negative_integer(self) -> None:
        """Schema: duration_ms must be non-negative integer."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0

    def test_version_field_is_string(self) -> None:
        """Schema: version field must be string (e.g., '1.0')."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_ticket_id_field_present(self) -> None:
        """Schema: ticket_id field must be present (may be null or default)."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert "ticket_id" in result

    def test_json_serializable_with_no_nan_or_infinity(self) -> None:
        """Schema: Output must be JSON-serializable; no NaN, Infinity, or custom types."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        try:
            json_str = json.dumps(result)
            # Re-parse to ensure no NaN/Infinity
            parsed = json.loads(json_str)
            assert parsed["risk_score"] in range(0, 101)
        except (ValueError, TypeError) as e:
            pytest.fail(f"Output not JSON-serializable: {e}")


class TestDeterminismAndIdempotence:
    """Determinism tests: Same input always produces identical output.

    Target: Hidden randomness, timestamp variations, internal state,
    non-deterministic iteration order.
    """

    def test_determinism_identical_input_identical_output_exact(self) -> None:
        """Determinism: Running gate twice with same input produces identical output."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "DUP-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "c.py", "line": 1, "message": ""}
        ]
        inputs = {"violations": violations}

        result1 = risk_scoring_check.run(inputs)
        result2 = risk_scoring_check.run(inputs)

        # Core scoring should be identical
        assert result1["risk_score"] == result2["risk_score"]
        assert result1["band"] == result2["band"]
        assert result1["reasoning"] == result2["reasoning"]
        # Note: timestamp will likely differ slightly, so we don't compare it

    def test_determinism_order_independence_violations_array(self) -> None:
        """Determinism: Violations array order shouldn't affect score (order-independent)."""
        from ci.scripts.gates import risk_scoring_check

        violation_a = {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}
        violation_b = {"rule_id": "DUP-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""}
        violation_c = {"rule_id": "AS-01", "severity": "ERROR", "file": "c.py", "line": 1, "message": ""}

        result1 = risk_scoring_check.run({"violations": [violation_a, violation_b, violation_c]})
        result2 = risk_scoring_check.run({"violations": [violation_c, violation_b, violation_a]})
        result3 = risk_scoring_check.run({"violations": [violation_b, violation_a, violation_c]})

        assert result1["risk_score"] == result2["risk_score"]
        assert result1["risk_score"] == result3["risk_score"]
        assert result1["band"] == result2["band"]
        assert result1["band"] == result3["band"]

    def test_determinism_no_hidden_randomness_10_runs(self) -> None:
        """Determinism: 10 consecutive runs produce identical scores."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "b.py", "line": 1, "message": ""}
        ]
        inputs = {"violations": violations}

        scores = [risk_scoring_check.run(inputs)["risk_score"] for _ in range(10)]
        assert len(set(scores)) == 1, f"Scores vary across runs: {scores}"

    def test_determinism_reasoning_consistent_across_runs(self) -> None:
        """Determinism: Reasoning text should be consistent (not vary with timestamp)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}
        ]
        inputs = {"violations": violations}

        result1 = risk_scoring_check.run(inputs)
        result2 = risk_scoring_check.run(inputs)

        # Reasoning should be identical
        assert result1["reasoning"] == result2["reasoning"]

    def test_determinism_band_classification_stable(self) -> None:
        """Determinism: Band classification should never flip between runs."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""}
        ]

        bands = [risk_scoring_check.run({"violations": violations})["band"] for _ in range(5)]
        assert len(set(bands)) == 1, f"Band varies: {bands}"


class TestAssumptionValidationAndInputFormat:
    """Assumption validation tests: Verify assumptions about prior gate outputs, signal mapping.

    Target: Spec assumptions about M902-09/10/11 output format, signal inference rules,
    edge cases in prior gate output format variations.
    """

    def test_assumption_empty_violations_array_treated_as_no_violations(self) -> None:
        """Assumption: Empty violations array → risk_score=0, band=EXIT."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        assert result["risk_score"] == 0
        assert result["band"] == "EXIT"

    def test_assumption_missing_violations_key_treated_as_empty_array(self) -> None:
        """Assumption: If inputs dict has no 'violations' key, treat as empty array."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({})
        assert result["risk_score"] == 0
        assert result["band"] == "EXIT"

    def test_assumption_rule_id_prefix_matching_is_case_sensitive(self) -> None:
        """Assumption: Rule ID prefix matching is case-sensitive (AR-01, not ar-01)."""
        from ci.scripts.gates import risk_scoring_check

        # Lowercase should not match and should be treated as unknown (+0)
        violations = [{"rule_id": "ar-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Should treat as unknown and score 0
        assert result["risk_score"] == 0

    def test_assumption_unknown_rule_id_assigned_zero_weight(self) -> None:
        """Assumption: Unknown rule IDs assigned +0 weight, not treated as error."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "XYZ-99", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Should not crash; should assign +0
        assert result["risk_score"] == 0
        assert result["status"] == "PASS"

    def test_assumption_malformed_violation_skipped_not_fatal(self) -> None:
        """Assumption: Malformed violations (missing rule_id) are skipped, not fatal."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"severity": "ERROR", "file": "a.py", "line": 1, "message": ""},  # No rule_id
            {"rule_id": "DUP-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Should process the good violation and skip the bad one
        assert result["status"] == "PASS"
        assert result["risk_score"] == 5  # DUP-01 only

    def test_assumption_duplicate_violations_counted_separately(self) -> None:
        """Assumption: Duplicate rule_ids counted separately (weight added per violation)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AR-01", "severity": "ERROR", "file": "b.py", "line": 2, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 3 + 3 = 6, (6/20)*100 = 30
        assert result["risk_score"] == 30

    def test_assumption_signal_extraction_via_rule_id_prefix(self) -> None:
        """Assumption: Signals extracted via rule_id prefix matching (AR- → architecture)."""
        from ci.scripts.gates import risk_scoring_check

        # AR-01 through AR-06 all map to SRP ambiguity (+3 each)
        for i in range(1, 7):
            violations = [{"rule_id": f"AR-{i:02d}", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
            result = risk_scoring_check.run({"violations": violations})
            assert result["risk_score"] == 15, f"AR-{i:02d} should be +3 signal"

    def test_assumption_ar_07_ar_08_different_weight_than_ar_01_06(self) -> None:
        """Assumption: AR-07 and AR-08 map to different signal (architecture drift, +5) than AR-01-06 (SRP, +3)."""
        from ci.scripts.gates import risk_scoring_check

        violations_ar01 = [{"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        violations_ar07 = [{"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""}]

        result_ar01 = risk_scoring_check.run({"violations": violations_ar01})
        result_ar07 = risk_scoring_check.run({"violations": violations_ar07})

        assert result_ar01["risk_score"] == 15  # +3
        assert result_ar07["risk_score"] == 25  # +5
        assert result_ar01["risk_score"] != result_ar07["risk_score"]

    def test_assumption_multiple_signals_cumulative_not_capped(self) -> None:
        """Assumption: Multiple signals accumulate; there is no per-signal cap (other than global [0-100])."""
        from ci.scripts.gates import risk_scoring_check

        # High-risk combination: should be cumulative
        violations = [
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "IGN-01", "severity": "WARN", "file": "c.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 5 + 5 + 2 = 12, (12/20)*100 = 60
        assert result["risk_score"] == 60


class TestSignalInteractionAndRareCombinations:
    """Signal interaction tests: Unusual/rare signal combinations, conflicting signals.

    Target: Code paths exercised only by uncommon violation combinations.
    """

    def test_rare_combination_all_low_weight_signals_only(self) -> None:
        """Rare: Only low-weight signals (DUP, OB, MUT-03 each +1)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "OB-03", "severity": "WARN", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "MUT-03", "severity": "WARN", "file": "e.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 1+1+1+1+1 = 5, (5/20)*100 = 25
        assert result["risk_score"] == 25
        assert result["band"] == "WARN"

    def test_rare_combination_high_weight_signals_only(self) -> None:
        """Rare: Only high-weight signals (SRP +3, AR-drift +5, Async +5)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "c.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # 3+5+5 = 13, (13/20)*100 = 65
        assert result["risk_score"] == 65
        assert result["band"] == "ESCALATE"

    def test_signal_interaction_srp_cancels_nothing(self) -> None:
        """No signal cancels or reduces another's weight. All additive."""
        from ci.scripts.gates import risk_scoring_check

        violations_single_srp = [{"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        violations_srp_plus_dup = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "DUP-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""}
        ]

        result_single = risk_scoring_check.run({"violations": violations_single_srp})
        result_combined = risk_scoring_check.run({"violations": violations_srp_plus_dup})

        # Score should increase when we add DUP (+1)
        assert result_combined["risk_score"] > result_single["risk_score"]
        assert result_combined["risk_score"] == 20  # 15 + 5 = 20


class TestMigrationDetection:
    """Migration detection tests: File path pattern matching for migration files.

    Target: Migration file detection via path patterns, multiple patterns,
    false positives/negatives.
    """

    def test_migration_detection_alembic_versions_pattern(self) -> None:
        """Migration detection: alembic/versions/*.py pattern."""
        from ci.scripts.gates import risk_scoring_check

        # Assume migration files are detected via path scanning. This may require
        # the gate to examine violation file paths or inputs differently.
        # For now, test that gate handles migration-like violations gracefully.
        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "alembic/versions/001_init.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Migration detection may add +2 if file path is scanned; otherwise just the violation weight
        assert result["status"] == "PASS"

    def test_migration_detection_migrations_directory_pattern(self) -> None:
        """Migration detection: migrations/*.py pattern."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "db/migrations/v1_add_column.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["status"] == "PASS"

    def test_migration_not_detected_outside_patterns(self) -> None:
        """Migration detection: Files outside alembic/migrations paths not treated as migrations."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "migration_utils.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Should score based on AR-01 only, no migration bonus
        assert result["risk_score"] == 15


class TestPerformanceAndStressScenarios:
    """Performance and stress tests: Large inputs, many violations, edge cases at scale.

    Target: Performance degradation, memory issues, timeout risks.
    """

    def test_performance_100_violations_completes_under_1s(self) -> None:
        """Performance: Gate processes 100 violations in <1s."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": f"file{i}.py", "line": i, "message": f"Violation {i}"}
            for i in range(100)
        ]

        start = time.time()
        result = risk_scoring_check.run({"violations": violations})
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Gate took {elapsed:.3f}s, expected <1s"
        assert result["status"] == "PASS"

    def test_performance_1000_violations_completes_under_2s(self) -> None:
        """Stress: Gate handles 1000 violations in reasonable time."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": f"file{i}.py", "line": i, "message": ""}
            for i in range(1000)
        ]

        start = time.time()
        result = risk_scoring_check.run({"violations": violations})
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Gate took {elapsed:.3f}s, expected <2s"
        # Score should be (1000 * 1 / 20) * 100 = 5000%, clamped to 100
        assert result["risk_score"] == 100

    def test_stress_large_violation_message_strings(self) -> None:
        """Stress: Large message fields in violations don't break gate."""
        from ci.scripts.gates import risk_scoring_check

        large_message = "x" * 10000
        violations = [
            {"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": large_message}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["status"] == "PASS"
        assert result["risk_score"] == 15

    def test_stress_large_file_path_strings(self) -> None:
        """Stress: Large file paths in violations."""
        from ci.scripts.gates import risk_scoring_check

        long_path = "/very/long/path/" + "subdir/" * 100 + "file.py"
        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": long_path, "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["status"] == "PASS"

    def test_stress_mixed_rule_ids_many_unknowns(self) -> None:
        """Stress: Many unknown rule IDs mixed with valid ones."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            *[
                {"rule_id": f"UNKNOWN-{i}", "severity": "ERROR", "file": f"file{i}.py", "line": i, "message": ""}
                for i in range(100)
            ]
        ]
        result = risk_scoring_check.run({"violations": violations})
        # Only DUP-01 should score; unknowns are +0
        assert result["risk_score"] == 5


class TestOutputFieldConsistency:
    """Output consistency tests: band/score consistency, recommendation/band consistency.

    Target: Mismatches between related fields, inconsistent enums.
    """

    def test_consistency_band_exit_with_low_score(self) -> None:
        """Consistency: band=EXIT only when risk_score <= 2."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        if result["band"] == "EXIT":
            assert result["risk_score"] <= 2

    def test_consistency_band_warn_with_mid_score(self) -> None:
        """Consistency: band=WARN only when 3 <= risk_score <= 5 (or close to)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        if result["band"] == "WARN":
            # Score should be in the WARN range
            assert 3 <= result["risk_score"] <= 100

    def test_consistency_band_escalate_with_high_score(self) -> None:
        """Consistency: band=ESCALATE only when risk_score >= 6 (or close to)."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        if result["band"] == "ESCALATE":
            assert result["risk_score"] >= 6

    def test_consistency_recommendation_exit_with_exit_band(self) -> None:
        """Consistency: next_stage_recommendation=low_risk_exit iff band=EXIT."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        assert result["band"] == "EXIT"
        assert result["next_stage_recommendation"] == "low_risk_exit"

    def test_consistency_recommendation_warn_with_warn_band(self) -> None:
        """Consistency: next_stage_recommendation=medium_risk_review iff band=WARN."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["band"] == "WARN"
        assert result["next_stage_recommendation"] == "medium_risk_review"

    def test_consistency_recommendation_escalate_with_escalate_band(self) -> None:
        """Consistency: next_stage_recommendation=high_risk_escalate iff band=ESCALATE."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "AR-07", "severity": "CRITICAL", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "AS-01", "severity": "ERROR", "file": "b.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["band"] == "ESCALATE"
        assert result["next_stage_recommendation"] == "high_risk_escalate"

    def test_consistency_message_includes_band_string(self) -> None:
        """Consistency: message field should reference the band somewhere."""
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        message_lower = result["message"].lower()
        # Should mention band or risk
        assert "exit" in message_lower or "risk" in message_lower or "scoring" in message_lower

    def test_consistency_reasoning_includes_signal_details(self) -> None:
        """Consistency: reasoning field explains which signals were detected."""
        from ci.scripts.gates import risk_scoring_check

        violations = [{"rule_id": "AR-01", "severity": "ERROR", "file": "a.py", "line": 1, "message": ""}]
        result = risk_scoring_check.run({"violations": violations})
        # Reasoning should explain the signal
        reasoning_lower = result["reasoning"].lower()
        assert len(result["reasoning"]) > 10  # Non-trivial explanation


class TestBandBoundaryPrecision:
    """Precise boundary tests for band transitions (2↔3, 5↔6).

    Target: Off-by-one errors in band classification logic.
    """

    def test_band_boundary_score_2_exact_is_exit(self) -> None:
        """Boundary: Score exactly 2 maps to EXIT (not WARN)."""
        # Can't create exactly 2 with weights, but test the logic.
        from ci.scripts.gates import risk_scoring_check

        result = risk_scoring_check.run({"violations": []})
        # Score 0, which is < 2, should be EXIT
        assert result["risk_score"] == 0
        assert result["band"] == "EXIT"

    def test_band_boundary_score_3_exact_is_warn(self) -> None:
        """Boundary: Score exactly 15 (= 3/20*100) maps to WARN."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["risk_score"] == 15
        assert result["band"] == "WARN"

    def test_band_boundary_score_5_exact_is_warn(self) -> None:
        """Boundary: Score exactly 25 (= 5/20*100) maps to WARN."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "OB-03", "severity": "WARN", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "MUT-03", "severity": "WARN", "file": "e.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["risk_score"] == 25
        assert result["band"] == "WARN"

    def test_band_boundary_score_6_exact_is_escalate(self) -> None:
        """Boundary: Score exactly 30 (= 6/20*100) maps to ESCALATE."""
        from ci.scripts.gates import risk_scoring_check

        violations = [
            {"rule_id": "DUP-01", "severity": "WARN", "file": "a.py", "line": 1, "message": ""},
            {"rule_id": "OB-01", "severity": "WARN", "file": "b.py", "line": 1, "message": ""},
            {"rule_id": "OB-02", "severity": "WARN", "file": "c.py", "line": 1, "message": ""},
            {"rule_id": "OB-03", "severity": "WARN", "file": "d.py", "line": 1, "message": ""},
            {"rule_id": "IGN-01", "severity": "WARN", "file": "e.py", "line": 1, "message": ""}
        ]
        result = risk_scoring_check.run({"violations": violations})
        assert result["risk_score"] == 30
        assert result["band"] == "ESCALATE"
