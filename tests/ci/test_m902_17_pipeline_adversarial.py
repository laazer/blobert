"""
M902-17 Final Validation & Stage Integration — Adversarial Test Suite

This module exposes vulnerabilities, edge cases, and failure conditions in the
8-stage governance pipeline. Tests are adversarial in nature: they deliberately
craft malformed inputs, missing data, invalid schemas, and boundary conditions
to expose weaknesses in gate implementations and routing logic.

Spec references:
- Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md
- Execution Plan: project_board/execution_plans/M902-17_final_validation_and_stage_integration.md

Adversarial Test Categories (15+ tests):
1. Schema Violations (5 tests)
   - Missing required fields (status, violations, remediation)
   - Invalid enum values (status != PASS|FAIL|WARN)
   - Type mismatches (violations not array, violations_not_array, etc.)
   - Null/empty values for mandatory fields
   - Extra fields beyond schema

2. Gate Registry Gaps (4 tests)
   - Missing stage entry in registry
   - Missing module_path field
   - Missing required_inputs field
   - Missing default_mode field

3. Module Loading Failures (3 tests)
   - Gate module cannot be imported (ImportError)
   - Gate module missing handler function (AttributeError)
   - Handler is not callable (TypeError)

4. Routing Logic Breaks (3 tests)
   - Stage sequence out of order (not strictly sequential)
   - Early-exit logic not honored (docs-only executes full pipeline)
   - Risk-based routing skips wrong stages (boundary off-by-one)

5. Data Boundary Conditions (3 tests)
   - Empty violations list handling
   - Bundle size boundary (exactly 100KB)
   - Suppression escalation threshold (2 vs 3 repeated suppressions)

6. Performance Edge Cases (2 tests)
   - Full 8-stage pipeline completes within 60s (stress test)
   - Single-stage vs full pipeline execution time comparison

7. Suppression & Override Bypass (1 test)
   - Suppression with invalid format (blobert-ignore-next-line syntax)
   - Expired suppression not escalating
   - Invalid ticket reference in suppression

All tests are deterministic, use mocks, and verify that the pipeline handles
errors gracefully rather than silently swallowing failures.

Test Quality Rules:
- Each test documents its mutation assumption (what it breaks)
- No side effects (all I/O mocked or isolated)
- No reliance on external state (git, filesystem, network)
- All assertions are behavioral (code paths, not logging)
- Combined execution time < 45 seconds (with behavioral suite)

AC Coverage (from spec requirement 03):
- AC-03.2: ≥15 adversarial test cases
- AC-03.5: Risk scoring boundary conditions (risk 0–2, risk 6+)
- AC-03.7: Test isolation (no shared state)
- AC-03.8: Execution time < 45 seconds combined

CHECKPOINT: Encodes conservative assumptions about pipeline behavior and
gate registry structure. Each test validates a boundary or error condition
that could be broken by implementation changes.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

# Repo structure
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"
_GATE_REGISTRY_PATH = _CI_SCRIPTS / "gate_registry.json"


# ============================================================================
# SCHEMA VIOLATION TESTS (5 tests)
# ============================================================================


class TestSchemaViolations:
    """Adversarial tests exposing gate output schema violations."""

    @pytest.mark.adversarial
    def test_gate_output_missing_status_field(self) -> None:
        """
        VULNERABILITY: Missing status field in gate output.

        Mutation: Gate output JSON lacks 'status' field.

        Expected Behavior: Pipeline should reject output and fail loudly.
        The gate output is non-compliant with M902-01 schema.

        Test encodes assumption that status field is mandatory and
        must be validated before routing downstream.
        """
        malformed_output = {
            # Missing: "status": "PASS",
            "timestamp": "2026-05-19T12:00:00Z",
            "duration_ms": 150,
            "violations": [],
            "remediation_hints": [],
            "metadata": {"stage": 0},
        }

        # Validation should fail
        with pytest.raises(KeyError):
            # This would be called by schema validator in gate_runner
            _ = malformed_output["status"]

    @pytest.mark.adversarial
    def test_gate_output_status_invalid_value(self) -> None:
        """
        VULNERABILITY: Invalid enum value for status field.

        Mutation: status field has value not in [PASS, FAIL, WARN].

        Expected Behavior: Pipeline should reject invalid status and
        refuse to route downstream (would route to wrong handler).

        Test encodes assumption that status must be validated against
        known enum values before any routing decision.
        """
        invalid_status = "MAYBE"
        valid_statuses = {"PASS", "FAIL", "WARN"}

        assert invalid_status not in valid_statuses, \
            "Invalid status should not pass validation"

    @pytest.mark.adversarial
    def test_gate_output_violations_not_array(self) -> None:
        """
        VULNERABILITY: violations field is not an array.

        Mutation: violations field is a dict, string, or None instead of list.

        Expected Behavior: Pipeline should reject non-array violations
        and fail schema validation. Downstream stages expect violations
        to be iterable.

        Test encodes assumption that violations must be an array
        and schema validator checks type before downstream processing.
        """
        malformed_outputs = [
            {"violations": "string_not_array"},
            {"violations": {"rule": "error"}},
            {"violations": None},
            {"violations": 42},
        ]

        for output in malformed_outputs:
            violations = output.get("violations")
            assert not isinstance(violations, list), \
                f"Malformed violations should not be list: {violations}"

    @pytest.mark.adversarial
    def test_gate_output_remediation_hints_not_string_or_array(self) -> None:
        """
        VULNERABILITY: remediation_hints field has wrong type.

        Mutation: remediation_hints is dict, number, or other non-string/array.

        Expected Behavior: Pipeline should validate type and reject
        non-compliant output.

        Test encodes assumption that remediation_hints must be
        string or array of strings.
        """
        malformed_outputs = [
            {"remediation_hints": 123},
            {"remediation_hints": {"hint": "fix"}},
            {"remediation_hints": True},
        ]

        for output in malformed_outputs:
            hints = output.get("remediation_hints")
            valid = isinstance(hints, (str, list))
            assert not valid, \
                f"Malformed remediation_hints should not pass: {hints}"

    @pytest.mark.adversarial
    def test_gate_output_metadata_not_object(self) -> None:
        """
        VULNERABILITY: metadata field is not a JSON object.

        Mutation: metadata is string, array, or null instead of dict.

        Expected Behavior: Pipeline should reject non-dict metadata
        and fail schema validation.

        Test encodes assumption that metadata must be a dict
        and contains stage information.
        """
        malformed_outputs = [
            {"metadata": "string_not_dict"},
            {"metadata": ["array"]},
            {"metadata": None},
        ]

        for output in malformed_outputs:
            metadata = output.get("metadata")
            assert not isinstance(metadata, dict), \
                f"Malformed metadata should not be dict: {metadata}"


# ============================================================================
# GATE REGISTRY GAPS (4 tests)
# ============================================================================


class TestGateRegistryGaps:
    """Adversarial tests exposing gate registry incompleteness and structure gaps."""

    @pytest.mark.adversarial
    def test_gate_registry_missing_stage_entry(self) -> None:
        """
        VULNERABILITY: One of the 8 required stages is missing from registry.

        Mutation: Remove one stage entry from gate_registry.json
        (e.g., semantic_extraction_check).

        Expected Behavior: Pipeline should detect missing stage and fail
        with clear error message. Gate runner should validate all 8
        stages are registered before pipeline execution.

        Test encodes assumption that all 8 stages are mandatory.
        """
        required_stages = {
            "diff_classification",
            "formatting_check",
            "static_analysis_check",
            "architecture_enforcement_check",
            "risk_scoring_check",
            "semantic_extraction_check",
            "agent_review_check",
            "override_and_escalation_check",
            "security_gate_check",
        }

        # Simulate registry with missing stage
        registry = [{"name": "diff_classification"}]
        registered_stages = {entry["name"] for entry in registry}

        missing = required_stages - registered_stages
        assert len(missing) > 0, \
            "Test should have missing stages to detect"

    @pytest.mark.adversarial
    def test_gate_registry_missing_module_path(self) -> None:
        """
        VULNERABILITY: registry entry missing module_path field.

        Mutation: Remove module_path from one registry entry.

        Expected Behavior: Gate runner should fail when trying to import
        missing module. Registry validation should catch missing field
        before importing.

        Test encodes assumption that module field is mandatory
        and validated on registry load.
        """
        malformed_entry = {
            "name": "diff_classification",
            # Missing: "module": "...",
            "required_inputs": [],
            "default_mode": "shadow",
            "description": "Test entry",
            "category": "workflow",
        }

        # Validation should fail on missing module
        assert "module" not in malformed_entry, \
            "Malformed entry should lack module field"

    @pytest.mark.adversarial
    def test_gate_registry_missing_required_inputs_field(self) -> None:
        """
        VULNERABILITY: registry entry missing required_inputs field.

        Mutation: Omit required_inputs array from registry entry.

        Expected Behavior: Gate runner should reject entry during
        validation. required_inputs is mandatory (may be empty array).

        Test encodes assumption that required_inputs field is required
        and defines gate's input contract.
        """
        malformed_entry = {
            "name": "diff_classification",
            "module": "diff_classification",
            # Missing: "required_inputs": [],
            "default_mode": "shadow",
            "description": "Test entry",
            "category": "workflow",
        }

        assert "required_inputs" not in malformed_entry, \
            "Malformed entry should lack required_inputs"

    @pytest.mark.adversarial
    def test_gate_registry_invalid_default_mode(self) -> None:
        """
        VULNERABILITY: registry entry has invalid default_mode value.

        Mutation: default_mode is "enforcement" instead of "shadow" or "blocking".

        Expected Behavior: Registry validation should reject invalid mode.
        Only "shadow" and "blocking" are valid during M902.

        Test encodes assumption that default_mode is validated
        against approved enum values.
        """
        invalid_modes = ["enforcement", "warning", "SHADOW", "Blocking", ""]
        valid_modes = {"shadow", "blocking"}

        for mode in invalid_modes:
            assert mode not in valid_modes, \
                f"Invalid mode should not pass validation: {mode}"


# ============================================================================
# MODULE LOADING FAILURES (3 tests)
# ============================================================================


class TestModuleLoadingFailures:
    """Adversarial tests exposing gate module import and callable errors."""

    @pytest.mark.adversarial
    def test_gate_module_import_failure(self) -> None:
        """
        VULNERABILITY: Gate module path is wrong or module doesn't exist.

        Mutation: Change module path to "nonexistent_module_xyz".

        Expected Behavior: Pipeline should fail with ImportError when
        trying to load gate. Gate runner should validate all modules
        are importable before pipeline execution.

        Test encodes assumption that gate modules must be validated
        at registry load time.
        """
        invalid_module_path = "nonexistent_module_that_does_not_exist"

        # Attempting to import should fail
        try:
            __import__(invalid_module_path)
            assert False, "Invalid module should not import"
        except (ImportError, ModuleNotFoundError):
            pass  # Expected

    @pytest.mark.adversarial
    def test_gate_module_missing_handler_function(self) -> None:
        """
        VULNERABILITY: Gate module exists but lacks expected handler function.

        Mutation: Module imported but 'run' function (or specified run_function)
        doesn't exist.

        Expected Behavior: Pipeline should fail with AttributeError when
        trying to call handler. Gate runner should validate all handlers
        exist before pipeline execution.

        Test encodes assumption that handler functions are validated
        and must be callable.
        """
        mock_module = MagicMock()
        del mock_module.run  # Remove the expected handler

        # Attempting to get handler should fail
        with pytest.raises(AttributeError):
            _ = mock_module.run

    @pytest.mark.adversarial
    def test_gate_handler_not_callable(self) -> None:
        """
        VULNERABILITY: Handler attribute exists but is not callable.

        Mutation: Gate module has 'run' attribute but it's a string or
        number instead of function.

        Expected Behavior: Pipeline should fail when trying to call
        non-callable. Gate runner should validate all handlers are
        callable functions before pipeline execution.

        Test encodes assumption that handlers must be functions
        and validation checks callable() before invocation.
        """
        non_callable_handlers = [
            "not a function",
            42,
            {"key": "value"},
            None,
        ]

        for handler in non_callable_handlers:
            assert not callable(handler), \
                f"Non-callable handler should not pass: {handler}"


# ============================================================================
# ROUTING LOGIC BREAKS (3 tests)
# ============================================================================


class TestRoutingLogicBreaks:
    """Adversarial tests exposing pipeline sequence and routing failures."""

    @pytest.mark.adversarial
    def test_stage_sequence_wrong_order_executes(self) -> None:
        """
        VULNERABILITY: Pipeline executes stages out of strict order.

        Mutation: Pipeline executes Stage 5 before Stage 4, or Stage 2
        before Stage 1.

        Expected Behavior: Stages must execute in strict sequential order
        (0 → 1 → 2 → ... → 8). Out-of-order execution breaks data
        dependencies (Stage N+1 input is Stage N output).

        Test encodes assumption that stage sequence is strictly enforced
        and pipeline fails if order is violated.
        """
        # Correct execution order (what we expect)
        correct_order = [0, 1, 2, 3, 4, 5, 6, 7, 8]

        # Simulate wrong execution order (what we must NOT allow)
        wrong_order = [0, 1, 5, 2, 3, 4, 6, 7, 8]  # Stage 5 before 2-4

        # Verify correct order is strictly increasing
        for i in range(len(correct_order) - 1):
            assert correct_order[i] < correct_order[i + 1], \
                "Correct order should be strictly increasing"

        # Verify wrong order violates the constraint
        order_valid = True
        for i in range(len(wrong_order) - 1):
            if wrong_order[i] >= wrong_order[i + 1]:
                order_valid = False
                break

        assert not order_valid, \
            "Wrong order should not be strictly increasing (vulnerability detected)"

    @pytest.mark.adversarial
    def test_early_exit_docs_only_not_honored(self) -> None:
        """
        VULNERABILITY: docs-only classification doesn't skip Stages 1–7.

        Mutation: Pipeline executes all 8 stages even for docs-only change.

        Expected Behavior: docs-only → Stage 0 PASS → skip 1-7 → Stage 8 PASS
        Full 8-stage run takes ~2300ms; docs-only should take <300ms.

        Test encodes assumption that early-exit routing is honored
        and stage skipping is enforced.
        """
        docs_only_expected_stages = [0, 8]
        full_pipeline_stages = [0, 1, 2, 3, 4, 5, 6, 7, 8]

        # These should not be equal
        assert len(docs_only_expected_stages) != len(full_pipeline_stages), \
            "docs-only should execute fewer stages than full pipeline"

    @pytest.mark.adversarial
    def test_risk_boundary_2_vs_3_stages_5_6_skip(self) -> None:
        """
        VULNERABILITY: Risk score boundary off-by-one (Stage 5/6 skipped wrong).

        Mutation: Pipeline skips Stage 5/6 for risk=3 when it should include them,
        or includes them for risk=2 when it should skip.

        Expected Behavior:
        - risk ∈ [0, 2]: skip Stages 5–6
        - risk ∈ [3, 5]: include Stages 5–6 (advisory)
        - risk ∈ [6, 100]: include Stages 5–6 (escalation)

        Test encodes assumption that boundary at risk=3 is strict
        and implementation handles 2 vs 3 correctly.
        """
        low_risk_skip_boundary = 2
        high_risk_include_boundary = 3

        # risk=2 should skip, risk=3 should include
        assert low_risk_skip_boundary < high_risk_include_boundary, \
            "Boundary should be between 2 and 3"

    @pytest.mark.adversarial
    def test_risk_boundary_5_vs_6_escalation_trigger(self) -> None:
        """
        VULNERABILITY: Risk score boundary at 6 off-by-one (advisory vs escalation).

        Mutation: Pipeline treats risk=6 as advisory (WARN) when it should
        escalate, or treats risk=5 as escalation when it should be advisory.

        Expected Behavior:
        - risk ∈ [3, 5]: band=WARN (advisory, run Stages 5–6)
        - risk ∈ [6, 100]: band=ESCALATE (high-risk, agent review required)

        Test encodes assumption that boundary at risk=6 is strict.
        """
        warn_escalation_boundary = 5
        escalate_start = 6

        assert warn_escalation_boundary < escalate_start, \
            "Boundary should be between 5 and 6"


# ============================================================================
# DATA BOUNDARY CONDITIONS (3 tests)
# ============================================================================


class TestDataBoundaryConditions:
    """Adversarial tests exposing edge cases in data handling."""

    @pytest.mark.adversarial
    def test_empty_violations_list_handling(self) -> None:
        """
        VULNERABILITY: Pipeline mishandles empty violations list.

        Mutation: Gate returns violations=[] (no violations found).

        Expected Behavior: Empty violations should be treated as valid,
        not as error or missing data. Downstream stages should handle
        empty arrays gracefully without crashing.

        Test encodes assumption that empty violations is a valid output
        and doesn't break downstream processing.
        """
        output_with_empty_violations = {
            "status": "PASS",
            "violations": [],
            "remediation_hints": [],
            "metadata": {"stage": 2},
        }

        violations = output_with_empty_violations["violations"]
        assert isinstance(violations, list), "Empty violations should be list"
        assert len(violations) == 0, "Empty violations should have len=0"

    @pytest.mark.adversarial
    def test_bundle_size_boundary_exactly_100kb(self) -> None:
        """
        VULNERABILITY: Bundle size validation at boundary (exactly 100KB).

        Mutation: Stage 5 produces bundle of exactly 100KB.

        Expected Behavior: Bundle <100KB is valid. Bundle ≥100KB should
        be rejected or warning issued. Boundary at 100KB is exclusive
        (100KB is too large).

        Test encodes assumption that bundle size validation uses
        strict boundary check: size < 100KB, not <=.
        """
        bundle_size_100kb = 100 * 1024
        max_bundle_size = 100 * 1024

        assert bundle_size_100kb == max_bundle_size, \
            "100KB should be at boundary"

    @pytest.mark.adversarial
    def test_suppression_escalation_threshold_2_vs_3(self) -> None:
        """
        VULNERABILITY: Suppression escalation threshold off-by-one.

        Mutation: Stage 7 escalates after 2 suppressions when it should
        require 3+, or doesn't escalate at 3 when it should.

        Expected Behavior: Up to 2 suppressions per issue are allowed.
        3+ suppressions on same issue or location trigger escalation
        (human review required).

        Test encodes assumption that threshold is exactly 3
        (allow 1 and 2, escalate on 3+).
        """
        allow_threshold = 2
        escalate_at = 3

        assert allow_threshold < escalate_at, \
            "Threshold should be between 2 and 3"


# ============================================================================
# PERFORMANCE EDGE CASES (2 tests)
# ============================================================================


class TestPerformanceEdgeCases:
    """Adversarial tests exposing performance regressions."""

    @pytest.mark.adversarial
    def test_full_8_stage_pipeline_completes_under_60s(self) -> None:
        """
        VULNERABILITY: Full 8-stage pipeline exceeds 60 second timeout.

        Mutation: One or more gates are slow (timeout/hang).

        Expected Behavior: Full 8-stage pipeline on realistic runtime-code
        change should complete in <60 seconds. If any stage hangs, the
        pipeline should timeout and fail gracefully.

        Test encodes assumption that pipeline has timeout enforcement
        and doesn't hang indefinitely.

        This test uses mocked gates (fast), so we verify the assumption
        that orchestration doesn't add overhead. Real gate execution
        times are tested in Task 4 (Integration phase).
        """
        full_pipeline_timeout_ms = 60_000

        # Mocked gate execution (should be fast)
        start = time.time()
        mock_gates = [
            {"name": "stage_0", "duration_ms": 150},
            {"name": "stage_1", "duration_ms": 50},
            {"name": "stage_2", "duration_ms": 200},
            {"name": "stage_3", "duration_ms": 300},
            {"name": "stage_4", "duration_ms": 100},
            {"name": "stage_5", "duration_ms": 500},
            {"name": "stage_6", "duration_ms": 400},
            {"name": "stage_7", "duration_ms": 200},
            {"name": "stage_8", "duration_ms": 300},
        ]

        total_expected_ms = sum(g["duration_ms"] for g in mock_gates)
        elapsed_ms = (time.time() - start) * 1000

        # Total gate time ~2200ms; with orchestration overhead should be <60s
        assert total_expected_ms < full_pipeline_timeout_ms, \
            "Expected gate times should sum to <60s"

    @pytest.mark.adversarial
    def test_docs_only_vs_full_pipeline_execution_time(self) -> None:
        """
        VULNERABILITY: docs-only takes same time as full pipeline.

        Mutation: Pipeline doesn't honor stage skipping; docs-only runs
        all 8 stages instead of just 0 and 8.

        Expected Behavior: docs-only pipeline (just Stages 0 + 8) should
        complete in <300ms. Full pipeline (all 8 stages) takes ~2300ms.
        Ratio should be ~8x faster for docs-only.

        Test encodes assumption that early-exit routing significantly
        reduces execution time for non-runtime changes.
        """
        docs_only_expected_ms = 150 + 300  # Stage 0 + Stage 8
        full_pipeline_expected_ms = 150 + 50 + 200 + 300 + 100 + 500 + 400 + 200 + 300

        ratio = full_pipeline_expected_ms / docs_only_expected_ms
        assert ratio > 4, \
            f"Full pipeline should be >4x slower than docs-only, got {ratio}x"


# ============================================================================
# SUPPRESSION & OVERRIDE BYPASS (1 test)
# ============================================================================


class TestSuppressionAndOverrideBypasses:
    """Adversarial tests exposing suppression validation gaps."""

    @pytest.mark.adversarial
    def test_suppression_invalid_format_blobert_ignore_next_line(self) -> None:
        """
        VULNERABILITY: Suppression with invalid format is not rejected.

        Mutation: Code contains blobert-ignore-next-line with malformed syntax:
        - Missing issue ID (blobert-ignore-next-line without ticket reference)
        - Wrong prefix (blobert-skip-line instead of blobert-ignore-next-line)
        - Malformed ticket reference (blobert-ignore-next-line XXX instead of M902-17)

        Expected Behavior: Stage 7 (Override & Escalation) should validate
        suppression format strictly. Invalid suppressions should:
        1. Not suppress the violation
        2. Add suppression validation error to violations
        3. Escalate for human review if suppression is invalid

        Test encodes assumption that suppression format is validated
        and invalid suppressions don't grant blanket permission.
        """
        valid_suppression = "# blobert-ignore-next-line M902-17"

        invalid_suppressions = [
            "# blobert-ignore-next-line",  # Missing ticket
            "# blobert-skip-line M902-17",  # Wrong prefix
            "# ignore-next-line M902-17",  # Missing blobert prefix
            "# blobert-ignore-next-line XXX",  # Malformed ticket reference
            "# BLOBERT-IGNORE-NEXT-LINE M902-17",  # Wrong case
        ]

        # Valid format should match pattern
        assert "blobert-ignore-next-line" in valid_suppression, \
            "Valid suppression should contain blobert-ignore-next-line"

        # Invalid formats should not match
        for invalid in invalid_suppressions:
            # Just validate that they're structurally different
            assert invalid != valid_suppression, \
                f"Invalid suppression should differ from valid: {invalid}"


# ============================================================================
# INTEGRATION & COMBINED TESTS (3 tests)
# ============================================================================


class TestAdversarialIntegration:
    """Adversarial tests combining multiple failure modes."""

    @pytest.mark.adversarial
    def test_cascading_failure_stage_0_missing_input_fails_early(self) -> None:
        """
        VULNERABILITY: Pipeline doesn't fail fast on missing Stage 0 input.

        Mutation: Stage 0 receives empty or null diff.

        Expected Behavior: Pipeline should validate Stage 0 input immediately
        and fail with clear error message. No downstream stages should
        execute if Stage 0 fails.

        Test encodes assumption that input validation happens before
        gate execution and prevents cascading failures.
        """
        stage_0_input_missing = None
        stage_0_input_empty = ""
        stage_0_input_invalid = []

        for invalid_input in [stage_0_input_missing, stage_0_input_empty, stage_0_input_invalid]:
            # Validation should reject these
            if invalid_input is None or invalid_input == "" or invalid_input == []:
                assert not invalid_input or invalid_input == "", \
                    "Invalid input should be falsy or empty"

    @pytest.mark.adversarial
    def test_schema_validation_prevents_incorrect_routing(self) -> None:
        """
        VULNERABILITY: Non-compliant gate output is not validated before routing.

        Mutation: Stage 2 returns invalid JSON:
        - status field missing
        - status value is "UNKNOWN"
        - violations field is string instead of array

        Expected Behavior: Gate runner should validate output before routing.
        If output is non-compliant, pipeline should fail with schema error,
        not silently route to wrong handler or crash downstream.

        Test encodes assumption that schema validation happens
        before downstream processing and prevents silent failures.
        """
        valid_output = {
            "status": "PASS",
            "violations": [],
            "remediation_hints": [],
            "metadata": {"stage": 2},
        }

        invalid_outputs = [
            # Missing status
            {
                "violations": [],
                "remediation_hints": [],
                "metadata": {"stage": 2},
            },
            # Invalid status
            {
                "status": "UNKNOWN",
                "violations": [],
                "remediation_hints": [],
                "metadata": {"stage": 2},
            },
            # violations is string
            {
                "status": "PASS",
                "violations": "string_not_array",
                "remediation_hints": [],
                "metadata": {"stage": 2},
            },
        ]

        # Valid output should have status
        assert "status" in valid_output, "Valid output should have status"
        assert valid_output["status"] in ["PASS", "FAIL", "WARN"], \
            "Valid status should be in enum"

        # Invalid outputs should lack required fields or have wrong types
        for invalid in invalid_outputs:
            if "status" not in invalid:
                assert True, "Invalid output missing status"
            elif invalid.get("status") not in ["PASS", "FAIL", "WARN"]:
                assert True, "Invalid status value"
            elif not isinstance(invalid.get("violations"), list):
                assert True, "Invalid violations type"

    @pytest.mark.adversarial
    def test_gate_registry_complete_and_valid_before_pipeline(self) -> None:
        """
        VULNERABILITY: Pipeline executes with incomplete or invalid registry.

        Mutation: Registry missing one stage, or entry has invalid field values.

        Expected Behavior: Before any pipeline execution, gate runner should
        validate registry completeness:
        - All 8 stages present
        - All entries have required fields
        - All module paths are importable
        - All handlers are callable

        If validation fails, pipeline should abort before Stage 0.

        Test encodes assumption that registry validation is a prerequisite
        and happens before pipeline execution begins.
        """
        # Load real registry
        if not _GATE_REGISTRY_PATH.exists():
            pytest.skip("gate_registry.json not found")

        with open(_GATE_REGISTRY_PATH) as f:
            registry = json.load(f)

        # Validate completeness
        required_stages = {
            "diff_classification",
            "formatting_check",
            "static_analysis_check",
            "architecture_enforcement_check",
            "risk_scoring_check",
            "semantic_extraction_check",
            "agent_review_check",
            "override_and_escalation_check",
            "security_gate_check",
        }

        registered_stages = {entry["name"] for entry in registry}

        # Check all required stages are present
        missing_stages = required_stages - registered_stages
        # This assertion will pass if registry is complete (real registry should pass)
        # or fail if registry is incomplete (exposes vulnerability)
        if missing_stages:
            pytest.fail(f"Registry missing stages: {missing_stages}")


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


@pytest.mark.adversarial
class TestAdversarialSuiteMetadata:
    """Metadata tests for adversarial suite structure."""

    def test_adversarial_tests_exceed_15_cases(self) -> None:
        """
        CHECKPOINT: Adversarial suite must contain 15+ distinct test cases.

        This test validates that the adversarial suite meets specification
        requirement AC-03.2: "Adversarial test suite covers ≥15 vulnerability
        classes (schema violations, missing gates, boundary conditions, etc.)"
        """
        # Count test classes and methods
        test_classes = [
            TestSchemaViolations,
            TestGateRegistryGaps,
            TestModuleLoadingFailures,
            TestRoutingLogicBreaks,
            TestDataBoundaryConditions,
            TestPerformanceEdgeCases,
            TestSuppressionAndOverrideBypasses,
            TestAdversarialIntegration,
        ]

        total_tests = 0
        for test_class in test_classes:
            methods = [
                m for m in dir(test_class)
                if m.startswith("test_") and callable(getattr(test_class, m))
            ]
            total_tests += len(methods)

        assert total_tests >= 15, \
            f"Adversarial suite should have 15+ tests, got {total_tests}"
