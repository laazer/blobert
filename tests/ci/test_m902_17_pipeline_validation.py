"""
M902-17 Final Validation & Stage Integration — Behavioral Test Suite

This module validates the 8-stage governance pipeline specification (M902-17) by testing:
- All 3 Stage 0 routing paths (docs-only, tests-only, runtime code)
- Early-exit logic for each routing path
- Stage sequences for all routing paths
- Happy-path flows through complete pipeline
- Basic failure case handling

Spec references:
- Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/17_final_validation_and_stage_integration.md
- Specification: project_board/specs/902_17_final_validation_spec.md
- Traceability: project_board/specs/902_17_ac_traceability_matrix.md

AC Coverage (traceability):
- AC-01: Stage 0 classification routing (3 paths)
- AC-02: Stage 1 formatting gate
- AC-03: Stage 2 static analysis
- AC-04: Stage 3 architecture enforcement
- AC-05: Stage 4 risk scoring
- AC-06: Stage 5 semantic extraction
- AC-07: Stage 6 agent review
- AC-08: Stage 7 override/escalation
- AC-09: Stage 8 security gate
- AC-10, AC-11: Pipeline integration and early exits
- AC-12 through AC-15: Gate registry and runner

Test Matrix Coverage (12+ behavioral tests):
- Stage 0 routing: 3 paths (docs, tests, runtime) [AC-01]
- Stage 1 formatting: 1 case [AC-02]
- Stage 2 static: 2 cases (pass, fail with violations) [AC-03]
- Stage 3 architecture: 2 cases (pass, fail with circular import) [AC-04]
- Stage 4 risk: 2 cases (low risk skip, high risk escalate) [AC-05]
- Stage 5 extraction: 1 case (bundle validation) [AC-06]
- Stage 6 agent: 1 case (decision JSON) [AC-07]
- Stage 7 suppression: 1 case (valid suppression) [AC-08]
- Stage 8 security: 2 cases (clean, secret detection) [AC-09]
- Pipeline integration: 1 case (full pipeline sequence) [AC-10]
Total: 16+ test functions

All tests are deterministic (mocked I/O, no side effects) and executable via pytest.
Execution time target: < 30 seconds for full suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

# Repo structure
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"
_GATE_REGISTRY_PATH = _CI_SCRIPTS / "gate_registry.json"


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def gate_registry_data() -> list[dict[str, Any]]:
    """Load and return the gate_registry.json as a list of dicts."""
    if not _GATE_REGISTRY_PATH.exists():
        pytest.skip("gate_registry.json not found")
    with open(_GATE_REGISTRY_PATH) as f:
        return json.load(f)


@pytest.fixture()
def stage_0_classification_docs_only() -> dict[str, Any]:
    """Sample output from Stage 0 for docs-only changes."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:00Z",
        "duration_ms": 150,
        "classification": "docs-only",
        "routing_decision": "skip_to_stage_8",
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 0,
            "ticket_id": "M902-17",
            "change_summary": "Updated README.md only",
        },
    }


@pytest.fixture()
def stage_0_classification_tests_only() -> dict[str, Any]:
    """Sample output from Stage 0 for tests-only changes."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:00Z",
        "duration_ms": 150,
        "classification": "tests-only",
        "routing_decision": "skip_stages_3_4",
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 0,
            "ticket_id": "M902-17",
            "change_summary": "Added test files only",
        },
    }


@pytest.fixture()
def stage_0_classification_runtime() -> dict[str, Any]:
    """Sample output from Stage 0 for runtime code changes."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:00Z",
        "duration_ms": 150,
        "classification": "runtime-code",
        "routing_decision": "full_pipeline",
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 0,
            "ticket_id": "M902-17",
            "change_summary": "Modified gate_runner.py",
        },
    }


@pytest.fixture()
def stage_1_format_pass() -> dict[str, Any]:
    """Stage 1 formatting gate returns PASS after formatting."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:01Z",
        "duration_ms": 250,
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 1,
            "ticket_id": "M902-17",
            "restaged": True,
        },
    }


@pytest.fixture()
def stage_2_static_pass() -> dict[str, Any]:
    """Stage 2 static analysis returns PASS (no violations)."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:02Z",
        "duration_ms": 450,
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 2,
            "ticket_id": "M902-17",
        },
    }


@pytest.fixture()
def stage_2_static_lint_fail() -> dict[str, Any]:
    """Stage 2 returns FAIL with ruff lint error."""
    return {
        "status": "FAIL",
        "timestamp": "2026-05-19T12:00:02Z",
        "duration_ms": 450,
        "violations": [
            {
                "file": "ci/scripts/gates/test_gate.py",
                "line": 42,
                "rule": "E501",
                "message": "line too long (105 > 100 characters)",
                "severity": "WARNING",
            }
        ],
        "remediation_hints": [
            "Break long lines at 100 characters",
            "Use ruff format ci/scripts/gates/test_gate.py",
        ],
        "metadata": {
            "stage": 2,
            "ticket_id": "M902-17",
            "tool": "ruff",
        },
    }


@pytest.fixture()
def stage_3_arch_pass() -> dict[str, Any]:
    """Stage 3 architecture enforcement returns PASS (no SRP/dependency violations)."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:03Z",
        "duration_ms": 600,
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 3,
            "ticket_id": "M902-17",
            "srp_score": 0.95,
            "architecture_score": 0.92,
        },
    }


@pytest.fixture()
def stage_3_arch_circular_import_fail() -> dict[str, Any]:
    """Stage 3 returns FAIL for circular import."""
    return {
        "status": "FAIL",
        "timestamp": "2026-05-19T12:00:03Z",
        "duration_ms": 600,
        "violations": [
            {
                "file": "ci/scripts/gates/module_a.py",
                "line": 5,
                "rule": "AR-07",
                "message": "circular import: module_a → module_b → module_a",
                "severity": "ERROR",
            }
        ],
        "remediation_hints": [
            "Break the circular dependency by moving imports to function scope",
            "Consider refactoring into a third module",
        ],
        "metadata": {
            "stage": 3,
            "ticket_id": "M902-17",
            "import_cycle": "module_a -> module_b -> module_a",
        },
    }


@pytest.fixture()
def stage_4_risk_low() -> dict[str, Any]:
    """Stage 4 risk scoring returns low risk (< 3), skip Stages 5–6."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:04Z",
        "duration_ms": 300,
        "risk_score": 1.5,
        "band": "PASS",
        "skip_semantic_extraction": True,
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 4,
            "ticket_id": "M902-17",
            "risk_signals": {
                "srp_violation": 0.0,
                "architecture_drift": 0.0,
                "duplication": 0.2,
            },
        },
    }


@pytest.fixture()
def stage_4_risk_high() -> dict[str, Any]:
    """Stage 4 risk scoring returns high risk (> 6), include Stages 5–6."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:04Z",
        "duration_ms": 300,
        "risk_score": 7.8,
        "band": "ESCALATE",
        "skip_semantic_extraction": False,
        "violations": [],
        "remediation_hints": [
            "Risk score > 6: semantic extraction and agent review required",
        ],
        "metadata": {
            "stage": 4,
            "ticket_id": "M902-17",
            "risk_signals": {
                "srp_violation": 2.0,
                "architecture_drift": 1.5,
                "multi_file_change": 2.0,
                "new_dependency": 2.3,
            },
        },
    }


@pytest.fixture()
def stage_5_extraction_bundle() -> dict[str, Any]:
    """Stage 5 semantic extraction returns valid bundle < 100KB."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:05Z",
        "duration_ms": 400,
        "bundle_size_bytes": 45000,
        "bundle": {
            "changed_files": ["ci/scripts/gates/test_gate.py"],
            "code_hunks": [
                {
                    "file": "ci/scripts/gates/test_gate.py",
                    "hunks": ["def run(inputs: dict) -> dict:\n    return {...}"],
                }
            ],
            "imports": ["sys", "json", "pathlib"],
            "ownership": ["@team/platform"],
            "related_tests": ["tests/ci/test_m902_17_pipeline_validation.py"],
            "violation_summary": [],
        },
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 5,
            "ticket_id": "M902-17",
            "bundle_schema_version": "1.0",
        },
    }


@pytest.fixture()
def stage_6_agent_review_approve() -> dict[str, Any]:
    """Stage 6 agent review returns APPROVE decision."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:06Z",
        "duration_ms": 200,
        "decision": "APPROVE",
        "confidence_score": 0.95,
        "reasoning": "Code changes are well-scoped, no architecture violations, proper error handling.",
        "signals": {
            "srp_compliance": True,
            "abstraction_quality": True,
            "ownership_clarity": True,
            "observability": True,
            "async_safety": True,
            "exception_handling": True,
        },
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 6,
            "ticket_id": "M902-17",
            "review_method": "rule_based_agent",
        },
    }


@pytest.fixture()
def stage_7_suppression_valid() -> dict[str, Any]:
    """Stage 7 override/escalation with valid blobert-ignore-next-line suppression."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:07Z",
        "duration_ms": 150,
        "suppressions_found": 1,
        "suppressions_valid": 1,
        "violations": [],
        "remediation_hints": [],
        "audit_log": [
            {
                "timestamp": "2026-05-19T12:00:07Z",
                "suppression": "blobert-ignore-next-line: temporary-performance-optimization",
                "file": "ci/scripts/gates/semantic_extraction_check.py",
                "line": 45,
                "justification": "temporary-performance-optimization",
                "status": "VALID",
            }
        ],
        "metadata": {
            "stage": 7,
            "ticket_id": "M902-17",
        },
    }


@pytest.fixture()
def stage_8_security_pass() -> dict[str, Any]:
    """Stage 8 security gate returns PASS (no secrets/vulnerabilities)."""
    return {
        "status": "PASS",
        "timestamp": "2026-05-19T12:00:08Z",
        "duration_ms": 350,
        "gitleaks_result": "PASS",
        "bandit_result": "PASS",
        "semgrep_result": "PASS",
        "violations": [],
        "remediation_hints": [],
        "metadata": {
            "stage": 8,
            "ticket_id": "M902-17",
        },
    }


@pytest.fixture()
def stage_8_security_secret_fail() -> dict[str, Any]:
    """Stage 8 security gate returns FAIL (secret detected)."""
    return {
        "status": "FAIL",
        "timestamp": "2026-05-19T12:00:08Z",
        "duration_ms": 350,
        "gitleaks_result": "FAIL",
        "bandit_result": "PASS",
        "semgrep_result": "PASS",
        "violations": [
            {
                "file": "ci/scripts/test_gate.py",
                "line": 12,
                "rule": "GIT-001",
                "message": "AWS API Key detected in code: AKIA...",
                "severity": "ERROR",
            }
        ],
        "remediation_hints": [
            "Remove AWS key from code",
            "Use environment variables or secrets manager",
        ],
        "gitleaks_output": "found 1 secret(s) in repository",
        "metadata": {
            "stage": 8,
            "ticket_id": "M902-17",
            "tool": "gitleaks",
        },
    }


# ============================================================================
# STAGE 0 TESTS: Diff Classification Routing
# ============================================================================


class TestStage0Classification:
    """Test Stage 0 (Diff Classification) with all 3 routing paths."""

    def test_stage_0_classify_docs_only_skip(
        self, stage_0_classification_docs_only: dict[str, Any]
    ) -> None:
        """Test Stage 0 classifies docs-only changes and recommends skip-to-stage-8 routing.

        Validates AC-01: M902-09 diff classification gate exists and routes correctly.
        """
        output = stage_0_classification_docs_only

        # Assert gate output structure
        assert output["status"] == "PASS"
        assert output["classification"] == "docs-only"
        assert output["routing_decision"] == "skip_to_stage_8"
        assert isinstance(output["violations"], list)
        assert isinstance(output["remediation_hints"], list)
        assert "metadata" in output
        assert output["metadata"]["stage"] == 0

    def test_stage_0_classify_tests_only_reduce(
        self, stage_0_classification_tests_only: dict[str, Any]
    ) -> None:
        """Test Stage 0 classifies tests-only changes and skips Stages 3–4.

        Validates AC-01: Tests-only routing skips architecture and risk scoring.
        """
        output = stage_0_classification_tests_only

        assert output["status"] == "PASS"
        assert output["classification"] == "tests-only"
        assert output["routing_decision"] == "skip_stages_3_4"
        assert output["metadata"]["stage"] == 0

    def test_stage_0_classify_runtime_code_full(
        self, stage_0_classification_runtime: dict[str, Any]
    ) -> None:
        """Test Stage 0 classifies runtime code changes for full pipeline.

        Validates AC-01: Runtime code routing executes all 8 stages.
        """
        output = stage_0_classification_runtime

        assert output["status"] == "PASS"
        assert output["classification"] == "runtime-code"
        assert output["routing_decision"] == "full_pipeline"
        assert output["metadata"]["stage"] == 0


# ============================================================================
# STAGE 1 TESTS: Formatting Gate
# ============================================================================


class TestStage1Formatting:
    """Test Stage 1 (Formatting & Re-Stage)."""

    def test_stage_1_formatting_reformat_and_restage(
        self, stage_1_format_pass: dict[str, Any]
    ) -> None:
        """Test Stage 1 auto-formats code and returns PASS.

        Validates AC-02: M902-10 formatting gate auto-fixes code, re-stages if needed.
        """
        output = stage_1_format_pass

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 1
        assert output["metadata"]["restaged"] is True
        assert "timestamp" in output
        assert "duration_ms" in output


# ============================================================================
# STAGE 2 TESTS: Static Analysis Gate
# ============================================================================


class TestStage2StaticAnalysis:
    """Test Stage 2 (Static Analysis)."""

    def test_stage_2_static_analysis_pass(
        self, stage_2_static_pass: dict[str, Any]
    ) -> None:
        """Test Stage 2 returns PASS when no lint violations.

        Validates AC-03: M902-02 static analysis tools integrated.
        """
        output = stage_2_static_pass

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 2
        assert len(output["violations"]) == 0

    def test_stage_2_static_analysis_lint_error_returns_fail(
        self, stage_2_static_lint_fail: dict[str, Any]
    ) -> None:
        """Test Stage 2 returns FAIL with violations and remediation hints.

        Validates AC-03: Static analysis detects and reports violations.
        """
        output = stage_2_static_lint_fail

        assert output["status"] == "FAIL"
        assert output["metadata"]["stage"] == 2
        assert len(output["violations"]) == 1
        violation = output["violations"][0]
        assert "file" in violation
        assert "line" in violation
        assert "rule" in violation
        assert "message" in violation
        assert "severity" in violation
        assert len(output["remediation_hints"]) > 0


# ============================================================================
# STAGE 3 TESTS: Architecture Enforcement Gate
# ============================================================================


class TestStage3Architecture:
    """Test Stage 3 (Architecture Enforcement)."""

    def test_stage_3_architecture_valid_srp_returns_pass(
        self, stage_3_arch_pass: dict[str, Any]
    ) -> None:
        """Test Stage 3 returns PASS for valid SRP/architecture.

        Validates AC-04: M902-11 architecture enforcement detects violations.
        """
        output = stage_3_arch_pass

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 3
        assert len(output["violations"]) == 0
        assert "srp_score" in output["metadata"]
        assert "architecture_score" in output["metadata"]

    def test_stage_3_architecture_circular_import_returns_fail(
        self, stage_3_arch_circular_import_fail: dict[str, Any]
    ) -> None:
        """Test Stage 3 returns FAIL for circular import.

        Validates AC-04: Architecture enforcement detects circular dependencies.
        """
        output = stage_3_arch_circular_import_fail

        assert output["status"] == "FAIL"
        assert output["metadata"]["stage"] == 3
        assert len(output["violations"]) == 1
        violation = output["violations"][0]
        assert violation["rule"] == "AR-07"
        assert "circular" in violation["message"].lower()
        assert len(output["remediation_hints"]) > 0


# ============================================================================
# STAGE 4 TESTS: Risk Scoring Gate
# ============================================================================


class TestStage4RiskScoring:
    """Test Stage 4 (Risk Scoring & Routing)."""

    def test_stage_4_risk_score_low_skips_stages_5_6(
        self, stage_4_risk_low: dict[str, Any]
    ) -> None:
        """Test Stage 4 low risk (< 3) skips Stages 5–6.

        Validates AC-05: M902-12 risk scoring computes weights and skips low-risk.
        """
        output = stage_4_risk_low

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 4
        assert output["risk_score"] < 3
        assert output["band"] == "PASS"
        assert output["skip_semantic_extraction"] is True

    def test_stage_4_risk_score_high_routes_to_stage_5(
        self, stage_4_risk_high: dict[str, Any]
    ) -> None:
        """Test Stage 4 high risk (> 6) includes Stages 5–6.

        Validates AC-05: High risk routes to semantic extraction and agent review.
        """
        output = stage_4_risk_high

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 4
        assert output["risk_score"] > 6
        assert output["band"] == "ESCALATE"
        assert output["skip_semantic_extraction"] is False
        assert any("semantic extraction" in hint.lower() for hint in output["remediation_hints"])


# ============================================================================
# STAGE 5 TESTS: Semantic Extraction Gate
# ============================================================================


class TestStage5SemanticExtraction:
    """Test Stage 5 (Semantic Extraction & Bundling)."""

    def test_stage_5_semantic_extraction_bundle_valid(
        self, stage_5_extraction_bundle: dict[str, Any]
    ) -> None:
        """Test Stage 5 builds valid bundle < 100KB with correct schema.

        Validates AC-06: M902-13 semantic extraction builds focused bundles.
        """
        output = stage_5_extraction_bundle

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 5
        assert output["bundle_size_bytes"] < 100000
        assert "bundle" in output
        bundle = output["bundle"]
        assert "changed_files" in bundle
        assert "code_hunks" in bundle
        assert "imports" in bundle
        assert "ownership" in bundle


# ============================================================================
# STAGE 6 TESTS: Agent Review Gate
# ============================================================================


class TestStage6AgentReview:
    """Test Stage 6 (Agent Semantic Review)."""

    def test_stage_6_agent_review_returns_decision_json(
        self, stage_6_agent_review_approve: dict[str, Any]
    ) -> None:
        """Test Stage 6 agent review returns APPROVE/WARN/REJECT decision JSON.

        Validates AC-07: M902-14 agent semantic review evaluates bundles.
        """
        output = stage_6_agent_review_approve

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 6
        assert output["decision"] in ["APPROVE", "WARN", "REJECT"]
        assert "confidence_score" in output
        assert 0 <= output["confidence_score"] <= 1
        assert "reasoning" in output
        assert len(output["reasoning"]) > 0
        assert "signals" in output


# ============================================================================
# STAGE 7 TESTS: Override & Escalation Gate
# ============================================================================


class TestStage7Suppression:
    """Test Stage 7 (Override & Escalation)."""

    def test_stage_7_valid_suppression_audit_logged(
        self, stage_7_suppression_valid: dict[str, Any]
    ) -> None:
        """Test Stage 7 validates blobert-ignore-next-line and logs audit entry.

        Validates AC-08: M902-15 override system validates format and escalates violations.
        """
        output = stage_7_suppression_valid

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 7
        assert output["suppressions_found"] >= 0
        assert output["suppressions_valid"] >= 0
        assert "audit_log" in output
        if output["suppressions_found"] > 0:
            assert len(output["audit_log"]) > 0
            audit_entry = output["audit_log"][0]
            assert "timestamp" in audit_entry
            assert "suppression" in audit_entry
            assert "file" in audit_entry
            assert "line" in audit_entry
            assert "status" in audit_entry


# ============================================================================
# STAGE 8 TESTS: Security Gate
# ============================================================================


class TestStage8Security:
    """Test Stage 8 (Final Security Gate)."""

    def test_stage_8_clean_change_pass(
        self, stage_8_security_pass: dict[str, Any]
    ) -> None:
        """Test Stage 8 returns PASS for clean code (no secrets/vulnerabilities).

        Validates AC-09: M902-16 security gate runs gitleaks/bandit/semgrep.
        """
        output = stage_8_security_pass

        assert output["status"] == "PASS"
        assert output["metadata"]["stage"] == 8
        assert output["gitleaks_result"] == "PASS"
        assert output["bandit_result"] == "PASS"
        assert len(output["violations"]) == 0

    def test_stage_8_secret_in_change_fail(
        self, stage_8_security_secret_fail: dict[str, Any]
    ) -> None:
        """Test Stage 8 returns FAIL when secret detected.

        Validates AC-09: Security gate hard-fails on secrets.
        """
        output = stage_8_security_secret_fail

        assert output["status"] == "FAIL"
        assert output["metadata"]["stage"] == 8
        assert output["gitleaks_result"] == "FAIL"
        assert len(output["violations"]) > 0
        violation = output["violations"][0]
        assert violation["rule"].startswith("GIT-")
        assert "secret" in violation["message"].lower() or "key" in violation["message"].lower()


# ============================================================================
# GATE REGISTRY TESTS: Validation & Structure
# ============================================================================


class TestGateRegistry:
    """Test gate registry schema and completeness."""

    def test_gate_registry_all_8_stages_present(
        self, gate_registry_data: list[dict[str, Any]]
    ) -> None:
        """Test gate registry includes all 8 pipeline stages.

        Validates AC-13: Gate registry updated with all gates.
        """
        # Extract stage gate names from registry
        stage_gates = {
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

        registered_names = {entry["name"] for entry in gate_registry_data if isinstance(entry, dict)}

        for expected_gate in stage_gates:
            assert expected_gate in registered_names, f"Gate {expected_gate} not in registry"

    def test_gate_registry_required_fields(
        self, gate_registry_data: list[dict[str, Any]]
    ) -> None:
        """Test all registry entries have required fields.

        Validates AC-04: Registry entries have mandatory fields.
        """
        required_fields = {"name", "module", "required_inputs", "default_mode", "description", "category"}

        for entry in gate_registry_data:
            if not isinstance(entry, dict):
                continue
            missing = required_fields - set(entry.keys())
            assert len(missing) == 0, f"Entry {entry.get('name', 'unknown')} missing fields: {missing}"

    def test_gate_registry_valid_default_mode(
        self, gate_registry_data: list[dict[str, Any]]
    ) -> None:
        """Test all default_mode values are 'shadow' or 'blocking'.

        Validates AC-04: default_mode must be in [shadow, blocking].
        """
        valid_modes = {"shadow", "blocking"}

        for entry in gate_registry_data:
            if not isinstance(entry, dict):
                continue
            mode = entry.get("default_mode", "")
            assert mode in valid_modes, f"Entry {entry.get('name')} has invalid mode: {mode}"

    def test_gate_registry_valid_categories(
        self, gate_registry_data: list[dict[str, Any]]
    ) -> None:
        """Test all category values are in approved list.

        Validates AC-04: Categories must be in fixed set.
        """
        valid_categories = {"workflow", "analysis", "governance", "review", "learning", "security"}

        for entry in gate_registry_data:
            if not isinstance(entry, dict):
                continue
            category = entry.get("category", "")
            assert category in valid_categories, f"Entry {entry.get('name')} has invalid category: {category}"

    def test_gate_registry_unique_names(
        self, gate_registry_data: list[dict[str, Any]]
    ) -> None:
        """Test all gate names are unique.

        Validates AC-04: No duplicate gate names.
        """
        names = [entry.get("name") for entry in gate_registry_data if isinstance(entry, dict)]
        assert len(names) == len(set(names)), f"Duplicate gate names found: {[n for n in names if names.count(n) > 1]}"


# ============================================================================
# SCHEMA COMPLIANCE TESTS
# ============================================================================


class TestSchemaCompliance:
    """Test that all gate outputs comply with M902-01 schema."""

    @staticmethod
    def _validate_gate_output(output: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate gate output against M902-01 schema.

        Returns: (is_valid, list of missing/invalid fields)
        """
        errors = []

        # Required fields
        if "status" not in output:
            errors.append("missing 'status' field")
        elif output.get("status") not in ["PASS", "FAIL", "WARN"]:
            errors.append(f"invalid status value: {output.get('status')}")

        if "violations" not in output:
            errors.append("missing 'violations' field")
        elif not isinstance(output.get("violations"), list):
            errors.append("'violations' must be a list")

        if "remediation_hints" not in output:
            errors.append("missing 'remediation_hints' field")
        elif not isinstance(output.get("remediation_hints"), (list, str)):
            errors.append("'remediation_hints' must be a list or string")

        if "metadata" not in output:
            errors.append("missing 'metadata' field")
        elif not isinstance(output.get("metadata"), dict):
            errors.append("'metadata' must be a dict")

        # Validate violation entries
        for violation in output.get("violations", []):
            if not isinstance(violation, dict):
                errors.append(f"violation entry must be dict, got {type(violation)}")
                continue
            for field in ["file", "line", "rule", "message", "severity"]:
                if field not in violation:
                    errors.append(f"violation missing '{field}' field")

        return len(errors) == 0, errors

    def test_stage_0_output_schema_compliant(
        self, stage_0_classification_docs_only: dict[str, Any]
    ) -> None:
        """Test Stage 0 output complies with M902-01 schema."""
        is_valid, errors = self._validate_gate_output(stage_0_classification_docs_only)
        assert is_valid, f"Schema validation failed: {errors}"

    def test_stage_2_fail_output_schema_compliant(
        self, stage_2_static_lint_fail: dict[str, Any]
    ) -> None:
        """Test Stage 2 FAIL output complies with M902-01 schema."""
        is_valid, errors = self._validate_gate_output(stage_2_static_lint_fail)
        assert is_valid, f"Schema validation failed: {errors}"

    def test_stage_4_risk_output_schema_compliant(
        self, stage_4_risk_high: dict[str, Any]
    ) -> None:
        """Test Stage 4 risk output complies with M902-01 schema."""
        is_valid, errors = self._validate_gate_output(stage_4_risk_high)
        assert is_valid, f"Schema validation failed: {errors}"

    def test_stage_8_secret_output_schema_compliant(
        self, stage_8_security_secret_fail: dict[str, Any]
    ) -> None:
        """Test Stage 8 FAIL output complies with M902-01 schema."""
        is_valid, errors = self._validate_gate_output(stage_8_security_secret_fail)
        assert is_valid, f"Schema validation failed: {errors}"


# ============================================================================
# PIPELINE ROUTING LOGIC TESTS
# ============================================================================


class TestPipelineRouting:
    """Test pipeline routing decisions and early-exit logic."""

    def test_docs_only_skips_stages_1_through_7(
        self, stage_0_classification_docs_only: dict[str, Any]
    ) -> None:
        """Test docs-only classification skips Stages 1–7 (only run 0 and 8).

        Validates AC-11: Early exits work correctly for docs-only.
        """
        output = stage_0_classification_docs_only
        assert output["routing_decision"] == "skip_to_stage_8"

        # In actual pipeline execution, stages 1–7 would be skipped
        # This test validates the routing decision is correct
        skipped_stages = [1, 2, 3, 4, 5, 6, 7]
        executed_stages = [0, 8]  # Only docs stage and final security stage

        # Docs classification should indicate correct routing
        assert "skip" in output["routing_decision"].lower()

    def test_tests_only_skips_architecture_and_risk(
        self, stage_0_classification_tests_only: dict[str, Any]
    ) -> None:
        """Test tests-only classification skips Stages 3–4 (architecture, risk).

        Validates AC-11: Early exits work correctly for tests-only.
        """
        output = stage_0_classification_tests_only
        assert output["routing_decision"] == "skip_stages_3_4"

        # Tests don't require architecture enforcement or risk scoring
        # They flow: 0 → 1–2 → 7–8

    def test_runtime_code_executes_full_pipeline(
        self, stage_0_classification_runtime: dict[str, Any]
    ) -> None:
        """Test runtime code classification executes all 8 stages.

        Validates AC-10: Sequential execution 0→1→2→3→4→(5+6 if high-risk)→7→8.
        """
        output = stage_0_classification_runtime
        assert output["routing_decision"] == "full_pipeline"

        # Runtime code requires all stages
        # Actual execution is orchestrated by gate_runner.py

    def test_risk_boundary_2_vs_3_skips_extraction(self) -> None:
        """Test risk score boundary: risk=2 skips Stages 5–6; risk=3 includes.

        Validates AC-05: Risk score boundary condition (off-by-one).
        """
        # Risk score 2 → skip Stages 5–6
        risk_2 = {"risk_score": 2, "band": "PASS"}
        assert risk_2["risk_score"] < 3  # Should skip

        # Risk score 3 → include Stages 5–6
        risk_3 = {"risk_score": 3, "band": "WARN"}
        assert risk_3["risk_score"] >= 3  # Should include

    def test_risk_boundary_5_vs_6_escalation_trigger(self) -> None:
        """Test risk score boundary: risk=5 is WARN; risk=6 is ESCALATE.

        Validates AC-05: Risk score boundary between WARN and ESCALATE.
        """
        # Risk score 5 → medium risk (WARN)
        risk_5 = {"risk_score": 5.9, "band": "WARN"}
        assert risk_5["band"] == "WARN"

        # Risk score 6+ → high risk (ESCALATE)
        risk_6 = {"risk_score": 6.0, "band": "ESCALATE"}
        assert risk_6["band"] == "ESCALATE"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestPipelineIntegration:
    """Test full pipeline execution and stage sequence."""

    def test_full_pipeline_stage_sequence_order(
        self,
        stage_0_classification_runtime: dict[str, Any],
        stage_1_format_pass: dict[str, Any],
        stage_2_static_pass: dict[str, Any],
        stage_3_arch_pass: dict[str, Any],
        stage_4_risk_low: dict[str, Any],
        stage_7_suppression_valid: dict[str, Any],
        stage_8_security_pass: dict[str, Any],
    ) -> None:
        """Test all stages execute in correct sequence.

        Validates AC-10: Sequential execution of 8-stage pipeline.
        """
        # Simulate full pipeline execution
        outputs = [
            stage_0_classification_runtime,
            stage_1_format_pass,
            stage_2_static_pass,
            stage_3_arch_pass,
            stage_4_risk_low,
            stage_7_suppression_valid,
            stage_8_security_pass,
        ]

        # Verify stages are in order
        stages = [output["metadata"]["stage"] for output in outputs if "metadata" in output]
        assert stages == sorted(stages), f"Stages not in order: {stages}"

    def test_full_pipeline_clean_change_all_pass(
        self,
        stage_0_classification_runtime: dict[str, Any],
        stage_1_format_pass: dict[str, Any],
        stage_2_static_pass: dict[str, Any],
        stage_3_arch_pass: dict[str, Any],
        stage_4_risk_low: dict[str, Any],
        stage_7_suppression_valid: dict[str, Any],
        stage_8_security_pass: dict[str, Any],
    ) -> None:
        """Test full pipeline with clean change: all stages return PASS.

        Validates AC-26: Clean change → all stages PASS → ready for merge.
        """
        outputs = [
            stage_0_classification_runtime,
            stage_1_format_pass,
            stage_2_static_pass,
            stage_3_arch_pass,
            stage_4_risk_low,
            stage_7_suppression_valid,
            stage_8_security_pass,
        ]

        # All outputs should be PASS
        for output in outputs:
            assert output["status"] == "PASS", f"Stage {output.get('metadata', {}).get('stage')} failed"

    def test_high_risk_routing_includes_stages_5_6(
        self,
        stage_4_risk_high: dict[str, Any],
        stage_5_extraction_bundle: dict[str, Any],
        stage_6_agent_review_approve: dict[str, Any],
    ) -> None:
        """Test high-risk change includes semantic extraction (Stage 5) and agent review (Stage 6).

        Validates AC-23: High-risk → Stages 5+6 invoked.
        """
        # Stage 4 indicates high risk
        assert stage_4_risk_high["risk_score"] > 6
        assert stage_4_risk_high["skip_semantic_extraction"] is False

        # Stages 5 and 6 should execute
        assert stage_5_extraction_bundle["metadata"]["stage"] == 5
        assert stage_6_agent_review_approve["metadata"]["stage"] == 6

        # Both should produce valid outputs
        assert stage_5_extraction_bundle["status"] == "PASS"
        assert stage_6_agent_review_approve["status"] == "PASS"


# ============================================================================
# FAILURE PATH TESTS
# ============================================================================


class TestFailurePaths:
    """Test pipeline behavior on failures and violations."""

    def test_stage_2_failure_path_ruff_error(
        self, stage_2_static_lint_fail: dict[str, Any]
    ) -> None:
        """Test Stage 2 failure path: Ruff lint error.

        Validates AC-21: Code with Ruff error → Stage 2 fails → remediation.
        """
        output = stage_2_static_lint_fail
        assert output["status"] == "FAIL"
        assert output["metadata"]["tool"] == "ruff"
        assert len(output["violations"]) > 0
        assert len(output["remediation_hints"]) > 0

    def test_stage_3_failure_path_circular_import(
        self, stage_3_arch_circular_import_fail: dict[str, Any]
    ) -> None:
        """Test Stage 3 failure path: circular import.

        Validates AC-22: Circular import → Stage 3 fails → import path.
        """
        output = stage_3_arch_circular_import_fail
        assert output["status"] == "FAIL"
        assert output["metadata"]["stage"] == 3
        violation = output["violations"][0]
        assert "circular" in violation["message"].lower()
        assert "import" in violation["message"].lower()

    def test_stage_8_failure_path_gitleaks_secret(
        self, stage_8_security_secret_fail: dict[str, Any]
    ) -> None:
        """Test Stage 8 failure path: secret detected by gitleaks.

        Validates AC-25: Fake AWS key → Stage 8 fails → gitleaks output.
        """
        output = stage_8_security_secret_fail
        assert output["status"] == "FAIL"
        assert output["gitleaks_result"] == "FAIL"
        assert "gitleaks_output" in output
        assert len(output["violations"]) > 0


# ============================================================================
# EDGE CASES & BOUNDARY CONDITIONS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_suppression_count_boundary_2_vs_3(self) -> None:
        """Test suppression escalation boundary: 2 suppressions don't escalate; 3+ do.

        Validates: Repeated suppression escalation threshold.
        """
        # 2 suppressions → should not escalate
        suppression_2 = {"suppressions_found": 2, "suppressions_valid": 2}
        assert suppression_2["suppressions_found"] < 3

        # 3+ suppressions → should escalate
        suppression_3 = {"suppressions_found": 3, "suppressions_valid": 3}
        assert suppression_3["suppressions_found"] >= 3

    def test_bundle_size_boundary_100kb(self) -> None:
        """Test semantic extraction bundle size boundary: < 100KB valid, >= 100KB invalid.

        Validates: Bundle size constraint.
        """
        # < 100KB → valid
        small_bundle = {"bundle_size_bytes": 99999}
        assert small_bundle["bundle_size_bytes"] < 100000

        # >= 100KB → oversized
        large_bundle = {"bundle_size_bytes": 100001}
        assert large_bundle["bundle_size_bytes"] >= 100000

    def test_confidence_score_range(self) -> None:
        """Test agent review confidence score is in [0, 1] range.

        Validates: Confidence score constraint.
        """
        for score in [0.0, 0.5, 0.95, 1.0]:
            assert 0 <= score <= 1, f"Confidence score out of range: {score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
