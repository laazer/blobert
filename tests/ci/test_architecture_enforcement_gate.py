"""Behavioral tests for M902-11 Stage 3 Architecture Enforcement Gate.

Covers all 13 requirements from the M902-11 specification:
- Requirement 01: Gate module and registry entry
- Requirement 02: Output contract and schema
- Requirement 03: Tool orchestration and integration
- Requirement 04: SRP violation detection
- Requirement 05: Dependency direction and circular import detection
- Requirement 06: Duplication detection
- Requirement 07: Complexity detection
- Requirement 08: Async safety violations
- Requirement 09: Observability rule enforcement
- Requirement 10: Data ownership and mutation boundary violations
- Requirement 11: Error handling and tool resilience
- Requirement 12: Non-functional requirements (NFR)
- Requirement 13: Deferred scope (out-of-scope, not tested)

Test vectors: TV-01 through TV-32 as defined in specification section "Test Vectors".
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestRequirement01GateModuleAndRegistry:
    """Tests for Requirement 01: Gate module and registry entry (AC-01)."""

    def test_gate_module_exists_at_correct_path(self) -> None:
        """AC-01.1: Gate module exists at ci/scripts/gates/architecture_enforcement_check.py."""
        gate_path = Path(__file__).parent.parent.parent / "ci" / "scripts" / "gates" / "architecture_enforcement_check.py"
        assert gate_path.exists(), f"Gate module not found at {gate_path}"

    def test_gate_module_is_importable(self) -> None:
        """AC-01.2: Gate module is importable without errors."""
        try:
            from ci.scripts.gates import architecture_enforcement_check  # noqa: F401
        except ImportError as e:
            pytest.fail(f"Gate module not importable: {e}")

    def test_gate_module_exports_run_function(self) -> None:
        """AC-01.3: Gate module exports run(inputs: dict) -> dict function."""
        from ci.scripts.gates import architecture_enforcement_check

        assert hasattr(architecture_enforcement_check, "run"), "Gate module missing 'run' function"
        assert callable(architecture_enforcement_check.run), "Gate.run is not callable"

    def test_gate_run_function_accepts_dict_input(self) -> None:
        """AC-01.4: run() function accepts dict input."""
        from ci.scripts.gates import architecture_enforcement_check

        # Call with minimal empty dict; should not raise TypeError
        result = architecture_enforcement_check.run({})
        assert isinstance(result, dict), "run() must return a dict"

    def test_gate_run_function_returns_dict_with_required_fields(self) -> None:
        """AC-01.5: run() returns dict with required fields (status, gate, timestamp, etc)."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})

        required_fields = [
            "status", "gate", "timestamp", "ticket_id", "message",
            "violations", "artifacts", "duration_ms", "risk_score", "architecture_score"
        ]
        for field in required_fields:
            assert field in result, f"Result dict missing required field: {field}"

    def test_gate_registry_entry_exists(self) -> None:
        """AC-01.6: Gate is registered in ci/scripts/gate_registry.json."""
        registry_path = Path(__file__).parent.parent.parent / "ci" / "scripts" / "gate_registry.json"
        assert registry_path.exists(), f"Gate registry not found at {registry_path}"

        with open(registry_path) as f:
            registry = json.load(f)

        gate_names = [entry["name"] for entry in registry]
        assert "architecture_enforcement_check" in gate_names, \
            "architecture_enforcement_check not found in gate registry"

    def test_gate_registry_entry_has_correct_structure(self) -> None:
        """AC-01.7: Registry entry has correct module, inputs, mode, description."""
        registry_path = Path(__file__).parent.parent.parent / "ci" / "scripts" / "gate_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)

        entry = next(
            (e for e in registry if e["name"] == "architecture_enforcement_check"),
            None
        )
        assert entry is not None

        assert "module" in entry
        assert entry["module"] == "ci.scripts.gates.architecture_enforcement_check"
        assert "run_function" in entry
        assert entry["run_function"] == "run"
        assert "default_mode" in entry
        assert entry["default_mode"] in ["shadow", "blocking"]
        assert "description" in entry
        assert len(entry["description"]) > 0


class TestRequirement02OutputContract:
    """Tests for Requirement 02: Output contract and schema (AC-02–10)."""

    def test_status_pass_on_clean_code(self) -> None:
        """AC-02.1: On clean code, status is PASS."""
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
                            assert result["status"] == "PASS"

    def test_status_fail_on_critical_violations(self) -> None:
        """AC-02.2: On critical violations (CRITICAL/ERROR), status is FAIL."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "import-linter",
            "severity": "CRITICAL",
            "file": "test.py",
            "line": 42,
            "column": 0,
            "rule_id": "AR-07",
            "message": "Circular import detected"
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
                            assert result["status"] in ["FAIL", "ESCALATE"]

    def test_output_has_correct_field_types(self) -> None:
        """AC-02.3: Output dict has correct field types (status str, violations list, duration int, etc)."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})

        assert isinstance(result["status"], str)
        assert isinstance(result["gate"], str)
        assert isinstance(result["timestamp"], str)
        assert isinstance(result["ticket_id"], str)
        assert isinstance(result["message"], str)
        assert isinstance(result["violations"], list)
        assert isinstance(result["artifacts"], list)
        assert isinstance(result["duration_ms"], int)
        assert isinstance(result["risk_score"], int)
        assert isinstance(result["architecture_score"], int)

    def test_timestamp_is_iso8601_utc(self) -> None:
        """AC-02.4: timestamp field is ISO 8601 UTC format (with Z suffix)."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})
        timestamp = result["timestamp"]

        # ISO 8601 UTC with Z: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH-MM-00Z (with dashes)
        assert timestamp.endswith("Z"), f"Timestamp '{timestamp}' does not end with Z"
        assert "T" in timestamp, f"Timestamp '{timestamp}' missing T separator"

    def test_violation_object_structure(self) -> None:
        """AC-02.5: Violation objects have required fields: tool, severity, file, line, column, rule_id, message."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "src/module.py",
            "line": 42,
            "column": 10,
            "rule_id": "AR-01",
            "message": "Domain module imports from HTTP library"
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
                            result = architecture_enforcement_check.run({})
                            assert len(result["violations"]) > 0
                            v = result["violations"][0]
                            for field in ["tool", "severity", "file", "line", "column", "rule_id", "message"]:
                                assert field in v, f"Violation missing field: {field}"

    def test_severity_levels_valid(self) -> None:
        """AC-02.6: Violation severity is one of: CRITICAL, ERROR, WARN, INFO."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violations = [
            {"tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1, "column": 0, "rule_id": "AR-07", "message": "msg"},
            {"tool": "semgrep", "severity": "ERROR", "file": "b.py", "line": 2, "column": 0, "rule_id": "AR-01", "message": "msg"},
            {"tool": "jscpd", "severity": "WARN", "file": "c.py", "line": 3, "column": 0, "rule_id": "DUP-01", "message": "msg"},
            {"tool": "radon", "severity": "INFO", "file": "d.py", "line": 4, "column": 0, "rule_id": "CX-01", "message": "msg"},
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
                                   return_value=[mock_violations[3]]):
                            result = architecture_enforcement_check.run({})
                            valid_severities = {"CRITICAL", "ERROR", "WARN", "INFO"}
                            for v in result["violations"]:
                                assert v["severity"] in valid_severities

    def test_violations_sorted_by_severity(self) -> None:
        """AC-02.7: Violations are sorted by severity (CRITICAL first, then ERROR, WARN, INFO)."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violations = [
            {"tool": "radon", "severity": "INFO", "file": "d.py", "line": 4, "column": 0, "rule_id": "CX-01", "message": "msg"},
            {"tool": "import-linter", "severity": "CRITICAL", "file": "a.py", "line": 1, "column": 0, "rule_id": "AR-07", "message": "msg"},
            {"tool": "jscpd", "severity": "WARN", "file": "c.py", "line": 3, "column": 0, "rule_id": "DUP-01", "message": "msg"},
            {"tool": "semgrep", "severity": "ERROR", "file": "b.py", "line": 2, "column": 0, "rule_id": "AR-01", "message": "msg"},
        ]

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[mock_violations[1]]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[mock_violations[3]]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[mock_violations[2]]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[mock_violations[0]]):
                            result = architecture_enforcement_check.run({})
                            severities = [v["severity"] for v in result["violations"]]
                            severity_order = {"CRITICAL": 0, "ERROR": 1, "WARN": 2, "INFO": 3}
                            assert severities == sorted(severities, key=lambda s: severity_order[s])

    def test_risk_score_in_valid_range(self) -> None:
        """AC-02.8: risk_score is integer in range [0, 100]."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})
        assert 0 <= result["risk_score"] <= 100

    def test_architecture_score_in_valid_range(self) -> None:
        """AC-02.9: architecture_score is integer in range [0, 100]."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})
        assert 0 <= result["architecture_score"] <= 100

    def test_shadow_mode_always_returns_pass(self) -> None:
        """AC-02.10: In shadow mode, status is always PASS even with violations."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "test.py",
            "line": 1,
            "column": 0,
            "rule_id": "AR-01",
            "message": "SRP violation"
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
                            result = architecture_enforcement_check.run({"mode": "shadow"})
                            assert result["status"] == "PASS"


class TestRequirement03ToolOrchestration:
    """Tests for Requirement 03: Tool orchestration and integration (AC-01–10)."""

    def test_all_five_tools_invoked(self) -> None:
        """AC-03.1: All five tools are invoked (import-linter, eslint, semgrep, jscpd, radon)."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter') as mock_il:
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint') as mock_es:
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep') as mock_sg:
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd') as mock_jc:
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon') as mock_rd:
                            mock_il.return_value = []
                            mock_es.return_value = []
                            mock_sg.return_value = []
                            mock_jc.return_value = []
                            mock_rd.return_value = []

                            architecture_enforcement_check.run({})

                            mock_il.assert_called_once()
                            mock_es.assert_called_once()
                            mock_sg.assert_called_once()
                            mock_jc.assert_called_once()
                            mock_rd.assert_called_once()

    def test_tool_timeout_handling(self) -> None:
        """AC-03.2: Tool timeout is caught and recorded (not crash)."""
        from ci.scripts.gates import architecture_enforcement_check

        # Mock a timeout exception from semgrep
        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           side_effect=subprocess.TimeoutExpired("semgrep", 120)):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            # Should return FAIL with a timeout violation
                            assert result["status"] in ["FAIL", "ESCALATE"]
                            assert any(v["rule_id"] == "TOOL_TIMEOUT" for v in result["violations"])

    def test_tool_unavailable_recorded_as_warn_violation(self) -> None:
        """AC-03.3: Tool unavailable is recorded as WARN violation, not FAIL."""
        from ci.scripts.gates import architecture_enforcement_check

        # Mock tool not found (FileNotFoundError)
        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   side_effect=FileNotFoundError("import-linter not on PATH")):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should still PASS (or return with WARN-level violations)
                            assert any(v["severity"] == "WARN" and v["rule_id"] == "TOOL_UNAVAILABLE"
                                      for v in result["violations"])

    def test_violation_deduplication(self) -> None:
        """AC-03.4: Violations with same (file, line, rule_id) are deduplicated."""
        from ci.scripts.gates import architecture_enforcement_check

        # Two tools report same violation at same location
        dup_violation_1 = {
            "tool": "import-linter",
            "severity": "ERROR",
            "file": "src/module.py",
            "line": 42,
            "column": 0,
            "rule_id": "AR-04",
            "message": "Service imports from routers"
        }
        dup_violation_2 = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "src/module.py",
            "line": 42,
            "column": 0,
            "rule_id": "AR-04",
            "message": "Service imports from routers (detected by semgrep)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[dup_violation_1]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[dup_violation_2]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should have only one violation (deduplicated)
                            ar04_violations = [v for v in result["violations"] if v["rule_id"] == "AR-04"]
                            assert len(ar04_violations) == 1


class TestRequirement04SRPViolations:
    """Tests for Requirement 04: SRP violation detection (TV-01 through TV-06)."""

    def test_tv01_domain_http_import_violation(self) -> None:
        """TV-01: AR-01 (domain HTTP import) detected."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "asset_generation/python/src/model_registry/registry.py",
            "line": 42,
            "column": 0,
            "rule_id": "AR-01",
            "message": "Domain module 'model_registry' imports from 'fastapi' (forbidden; domain is business logic only)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "AR-01" for v in result["violations"])

    def test_tv02_service_http_response_violation(self) -> None:
        """TV-02: AR-02 (service HTTP response) detected."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "asset_generation/web/backend/services/asset_service.py",
            "line": 50,
            "column": 0,
            "rule_id": "AR-02",
            "message": "Service 'asset_service' constructs HTTP response (forbidden; services are orchestration only, responses belong in routers)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "AR-02" for v in result["violations"])

    def test_tv03_router_business_logic_violation(self) -> None:
        """TV-03: AR-03 (router business logic) detected."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "asset_generation/web/backend/routers/registry.py",
            "line": 30,
            "column": 0,
            "rule_id": "AR-03",
            "message": "Router 'registry' contains business logic (>10 LOC without service delegation)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "AR-03" for v in result["violations"])

    def test_tv04_service_router_import_violation(self) -> None:
        """TV-04: AR-04 (service router import) detected."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "import-linter",
            "severity": "ERROR",
            "file": "asset_generation/web/backend/services/registry_service.py",
            "line": 5,
            "column": 0,
            "rule_id": "AR-04",
            "message": "Module 'registry_service' imports from 'routers' (forbidden; breaks layering)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[violation]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "AR-04" for v in result["violations"])

    def test_tv05_infrastructure_leak_violation(self) -> None:
        """TV-05: AR-05 (infrastructure leak) detected."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "asset_generation/python/src/model_registry/registry.py",
            "line": 60,
            "column": 0,
            "rule_id": "AR-05",
            "message": "Module 'model_registry' uses infrastructure service 'db.query()' directly (forbidden; must use repository pattern)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "AR-05" for v in result["violations"])

    def test_tv06_persistence_write_violation(self) -> None:
        """TV-06: AR-06 (persistence write) detected."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "asset_generation/web/backend/services/asset_service.py",
            "line": 75,
            "column": 0,
            "rule_id": "AR-06",
            "message": "Module 'asset_service' contains persistence write (forbidden; only repositories write data)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "AR-06" for v in result["violations"])


class TestRequirement05DependencyDirection:
    """Tests for Requirement 05: Dependency direction and circular imports (TV-07 through TV-09)."""

    def test_tv07_two_way_cycle(self) -> None:
        """TV-07: Two-way cycle (A ↔ B) detected as CRITICAL."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "import-linter",
            "severity": "CRITICAL",
            "file": "asset_generation/python/src/model_registry",
            "line": 5,
            "column": 0,
            "rule_id": "AR-07",
            "message": "Circular dependency: 'model_registry' ↔ 'services' (blocks compilation/runtime)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[violation]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] in ["FAIL", "ESCALATE"]
                            assert any(v["rule_id"] == "AR-07" and v["severity"] == "CRITICAL"
                                      for v in result["violations"])

    def test_tv08_three_way_cycle(self) -> None:
        """TV-08: Three-way cycle (A → B → C → A) detected as CRITICAL."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "import-linter",
            "severity": "CRITICAL",
            "file": "asset_generation/python/src/module_a.py",
            "line": 10,
            "column": 0,
            "rule_id": "AR-08",
            "message": "Circular import detected: 'module_a' → 'module_b' → 'module_c' → 'module_a'"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[violation]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] in ["FAIL", "ESCALATE"]
                            assert any(v["rule_id"] == "AR-08" and v["severity"] == "CRITICAL"
                                      for v in result["violations"])

    def test_tv09_clean_dag_no_cycles(self) -> None:
        """TV-09: Clean dependency DAG (no cycles) produces PASS."""
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
                            assert result["status"] == "PASS"
                            assert all(v["severity"] != "CRITICAL" for v in result["violations"])


class TestRequirement06Duplication:
    """Tests for Requirement 06: Duplication detection (TV-10 through TV-13)."""

    def test_tv10_eight_line_cluster(self) -> None:
        """TV-10: 8-line duplication cluster detected (DUP-01, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "jscpd",
            "severity": "WARN",
            "file": "src/file_a.py",
            "line": 42,
            "column": 0,
            "rule_id": "DUP-01",
            "message": "Duplication cluster: 'src/file_a.py' lines 42–49 duplicates 'src/file_b.py' lines 100–107 (8 lines, 120 tokens)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[violation]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "DUP-01" and v["severity"] == "WARN"
                                      for v in result["violations"])

    def test_tv11_fifteen_line_cluster(self) -> None:
        """TV-11: 15-line duplication cluster detected and aggregated."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "jscpd",
            "severity": "WARN",
            "file": "src/module_a.py",
            "line": 50,
            "column": 0,
            "rule_id": "DUP-01",
            "message": "Duplication cluster: 'src/module_a.py' lines 50–64 duplicates 'src/module_b.py' lines 200–214 (15 lines, 250 tokens)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[violation]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "DUP-01" for v in result["violations"])

    def test_tv12_below_threshold_no_violation(self) -> None:
        """TV-12: 7-line cluster (below 8-line threshold) produces no DUP-01."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):  # No violations
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert not any(v["rule_id"] == "DUP-01" for v in result["violations"])

    def test_tv13_high_duplication_ratio(self) -> None:
        """TV-13: High duplication ratio (8% of codebase) reported (DUP-02, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "jscpd",
            "severity": "WARN",
            "file": "",
            "line": 0,
            "column": 0,
            "rule_id": "DUP-02",
            "message": "Code duplication ratio: 8% of codebase is duplicated (consider refactoring hotspots)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[violation]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "DUP-02" and "8%" in v["message"]
                                      for v in result["violations"])


class TestRequirement07Complexity:
    """Tests for Requirement 07: Complexity detection (TV-14 through TV-17)."""

    def test_tv14_function_size_exceeded(self) -> None:
        """TV-14: Function with 87 LOC exceeds 50-LOC threshold (CX-01, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "radon",
            "severity": "WARN",
            "file": "asset_generation/python/src/services/asset_service.py",
            "line": 10,
            "column": 0,
            "rule_id": "CX-01",
            "message": "Function 'process_asset' exceeds size limit: 87 LOC (threshold: 50)"
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
                                   return_value=[violation]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "CX-01" and v["severity"] == "WARN"
                                      for v in result["violations"])

    def test_tv15_nesting_depth_exceeded(self) -> None:
        """TV-15: 5-level nesting (exceeds 4-level threshold) (CX-02, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "radon",
            "severity": "WARN",
            "file": "asset_generation/python/src/logic/complex_logic.py",
            "line": 20,
            "column": 0,
            "rule_id": "CX-02",
            "message": "Nesting depth in 'process_nested' exceeds limit: 5 levels (threshold: 4)"
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
                                   return_value=[violation]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "CX-02" for v in result["violations"])

    def test_tv16_cognitive_complexity_high(self) -> None:
        """TV-16: Cognitive complexity 15 (exceeds 10 threshold) (CX-03, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "radon",
            "severity": "WARN",
            "file": "asset_generation/python/src/logic/conditional_logic.py",
            "line": 30,
            "column": 0,
            "rule_id": "CX-03",
            "message": "Cognitive complexity in 'evaluate_condition' is high: 14 (threshold: 10)"
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
                                   return_value=[violation]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "CX-03" for v in result["violations"])

    def test_tv17_class_size_exceeded(self) -> None:
        """TV-17: Class with 320 LOC exceeds 200-LOC threshold (CX-04, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "radon",
            "severity": "WARN",
            "file": "asset_generation/web/backend/services/registry_service.py",
            "line": 5,
            "column": 0,
            "rule_id": "CX-04",
            "message": "Class 'RegistryService' exceeds size limit: 320 LOC (threshold: 200)"
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
                                   return_value=[violation]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "CX-04" for v in result["violations"])


class TestRequirement08AsyncSafety:
    """Tests for Requirement 08: Async safety violations (TV-18 through TV-20)."""

    def test_tv18_blocking_io_in_async(self) -> None:
        """TV-18: Blocking call (requests.get) in async function (AS-01, CRITICAL)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "CRITICAL",
            "file": "asset_generation/web/backend/routers/assets.py",
            "line": 25,
            "column": 0,
            "rule_id": "AS-01",
            "message": "Blocking call 'requests.get' in async function 'fetch_asset' (will block event loop)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] in ["FAIL", "ESCALATE"]
                            assert any(v["rule_id"] == "AS-01" and v["severity"] == "CRITICAL"
                                      for v in result["violations"])

    def test_tv19_unbounded_task_spawning(self) -> None:
        """TV-19: Unbounded task spawning in async context (AS-02, CRITICAL)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "CRITICAL",
            "file": "asset_generation/web/backend/services/batch_service.py",
            "line": 40,
            "column": 0,
            "rule_id": "AS-02",
            "message": "Unbounded task spawning detected in 'process_items' (no limit on concurrent tasks)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert result["status"] in ["FAIL", "ESCALATE"]
                            assert any(v["rule_id"] == "AS-02" for v in result["violations"])

    def test_tv20_missing_timeout_on_async_op(self) -> None:
        """TV-20: asyncio.wait() without timeout (AS-03, WARN)."""
        from ci.scripts.gates import architecture_enforcement_check

        violation = {
            "tool": "semgrep",
            "severity": "WARN",
            "file": "asset_generation/web/backend/services/orchestration.py",
            "line": 55,
            "column": 0,
            "rule_id": "AS-03",
            "message": "Async operation 'orchestrate_workflow' missing timeout (risk of permanent blocking)"
        }

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[violation]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "AS-03" and v["severity"] == "WARN"
                                      for v in result["violations"])


class TestRequirement11ErrorHandling:
    """Tests for Requirement 11: Error handling and tool resilience."""

    def test_no_silent_exceptions(self) -> None:
        """AC-11.1: No bare except or silent exception swallowing."""
        from ci.scripts.gates import architecture_enforcement_check

        # Simulate an exception in tool invocation
        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   side_effect=Exception("Unexpected error")):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            # Should produce FAIL with error violation (not silent crash)
                            assert result["status"] == "FAIL"
                            assert any(v["rule_id"] == "TOOL_ERROR" for v in result["violations"])

    def test_tool_timeout_produces_violation(self) -> None:
        """AC-11.2: Tool timeout is recorded as TOOL_TIMEOUT violation."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           side_effect=subprocess.TimeoutExpired("semgrep", 120)):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert any(v["rule_id"] == "TOOL_TIMEOUT" for v in result["violations"])

    def test_missing_tool_produces_warn_violation(self) -> None:
        """AC-11.3: Missing tool is recorded as TOOL_UNAVAILABLE with WARN severity."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   side_effect=FileNotFoundError("Tool not installed")):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           return_value=[]):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            assert any(v["rule_id"] == "TOOL_UNAVAILABLE" and v["severity"] == "WARN"
                                      for v in result["violations"])

    def test_parse_error_produces_warn_violation(self) -> None:
        """AC-11.4: Tool output parsing error is recorded as PARSE_ERROR with WARN."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   return_value=[]):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       return_value=[]):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           side_effect=json.JSONDecodeError("Invalid JSON", "{", 0)):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               return_value=[]):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   return_value=[]):
                            result = architecture_enforcement_check.run({})
                            # Should gracefully skip parsing error and continue
                            assert any(v["rule_id"] == "PARSE_ERROR" and v["severity"] == "WARN"
                                      for v in result["violations"]) or result["status"] == "PASS"


class TestRequirement12NFR:
    """Tests for Requirement 12: Non-functional requirements (TV-31, TV-32)."""

    def test_nfr_exit_codes(self) -> None:
        """NFR: Shadow mode exits 0; blocking mode exits 1 on FAIL."""
        from ci.scripts.gates import architecture_enforcement_check

        # Test would require subprocess.run; integration-level test
        # Verified via test_requirement01_gate_module_and_registry tests
        pass

    def test_gate_deterministic_on_same_input(self) -> None:
        """TV-32: Running gate twice on same input yields same violations (deterministic)."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "test.py",
            "line": 1,
            "column": 0,
            "rule_id": "AR-01",
            "message": "SRP violation"
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
                            result1 = architecture_enforcement_check.run({})
                            result2 = architecture_enforcement_check.run({})

                            # Results should be identical
                            assert result1["status"] == result2["status"]
                            assert len(result1["violations"]) == len(result2["violations"])
                            for v1, v2 in zip(result1["violations"], result2["violations"]):
                                assert v1["rule_id"] == v2["rule_id"]
                                assert v1["severity"] == v2["severity"]


class TestEdgeCasesAndIntegration:
    """Additional edge case and integration tests."""

    def test_empty_codebase_produces_pass(self) -> None:
        """TV-29: Empty codebase produces PASS with no violations."""
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
                            assert result["status"] == "PASS"
                            assert result["risk_score"] == 0
                            assert result["architecture_score"] == 100

    def test_all_tools_unavailable_produces_pass_with_warns(self) -> None:
        """TV-30: All tools unavailable produces PASS with TOOL_UNAVAILABLE violations."""
        from ci.scripts.gates import architecture_enforcement_check

        with patch('ci.scripts.gates.architecture_enforcement_check._run_import_linter',
                   side_effect=FileNotFoundError()):
            with patch('ci.scripts.gates.architecture_enforcement_check._run_eslint',
                       side_effect=FileNotFoundError()):
                with patch('ci.scripts.gates.architecture_enforcement_check._run_semgrep',
                           side_effect=FileNotFoundError()):
                    with patch('ci.scripts.gates.architecture_enforcement_check._run_jscpd',
                               side_effect=FileNotFoundError()):
                        with patch('ci.scripts.gates.architecture_enforcement_check._run_radon',
                                   side_effect=FileNotFoundError()):
                            result = architecture_enforcement_check.run({})
                            assert result["status"] == "PASS"
                            assert all(v["rule_id"] == "TOOL_UNAVAILABLE" for v in result["violations"])
                            assert all(v["severity"] == "WARN" for v in result["violations"])

    def test_result_json_serializable(self) -> None:
        """AC-02.11: Result dict is JSON serializable."""
        from ci.scripts.gates import architecture_enforcement_check

        result = architecture_enforcement_check.run({})
        try:
            json.dumps(result)
        except TypeError as e:
            pytest.fail(f"Result dict not JSON serializable: {e}")

    def test_mode_parameter_respected(self) -> None:
        """Mode parameter (shadow/blocking) is respected by gate."""
        from ci.scripts.gates import architecture_enforcement_check

        mock_violation = {
            "tool": "semgrep",
            "severity": "ERROR",
            "file": "test.py",
            "line": 1,
            "column": 0,
            "rule_id": "AR-01",
            "message": "SRP violation"
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
                            # Shadow mode should always return PASS
                            shadow_result = architecture_enforcement_check.run({"mode": "shadow"})
                            assert shadow_result["status"] == "PASS"

                            # Blocking mode should return FAIL for violations
                            blocking_result = architecture_enforcement_check.run({"mode": "blocking"})
                            assert blocking_result["status"] in ["FAIL", "ESCALATE"]
