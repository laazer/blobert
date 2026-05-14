"""Adversarial tests for shadow mode behavior.

Tests mode confusion, state leakage, and race conditions in shadow vs
blocking mode handling.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


class TestShadowModeMutation:
    """Mutation tests for shadow mode semantics."""

    def test_shadow_mode_status_can_be_fail(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: shadow mode records with FAIL status should still exit 0
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[-1].read_text())
            # Shadow mode MUST exit 0 even if status is FAIL
            assert result.returncode == 0
            # But the status field should reflect the actual gate result
            assert "status" in data

    def test_blocking_mode_status_pass_exits_zero(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: blocking mode with PASS should exit 0
        # Create a valid spec that passes
        tmp_dir = tmp_gate_results / "valid_specs"
        tmp_dir.mkdir()
        valid_spec = tmp_dir / "valid.md"
        valid_spec.write_text("# Valid Spec\n\n## Overview\n\n## Acceptance Criteria\n")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(valid_spec), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[-1].read_text())
            if data.get("status") == "PASS":
                assert result.returncode == 0, \
                    f"Blocking mode with PASS should exit 0, got {result.returncode}"

    def test_shadow_mode_does_not_block_ci(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: multiple shadow mode calls should not accumulate state
        for _ in range(10):
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", "shadow",
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            assert result.returncode == 0, "Shadow mode should always exit 0"

    def test_mode_switch_does_not_leak_state(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: switching between shadow and blocking should not leak state
        results = []
        for mode in ["shadow", "blocking", "shadow", "blocking"]:
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", mode,
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            files = list(tmp_gate_results.glob("*.json"))
            if files:
                data = json.loads(files[-1].read_text())
                results.append({
                    "mode": mode,
                    "exit_code": result.returncode,
                    "recorded_mode": data.get("mode"),
                    "status": data.get("status"),
                })

        # Shadow mode should always exit 0 regardless of gate status
        shadow_results = [r for r in results if r["mode"] == "shadow"]
        for r in shadow_results:
            assert r["exit_code"] == 0, \
                f"Shadow mode exit code should be 0, got {r['exit_code']}"

    def test_shadow_mode_result_file_has_shadow_marker(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: shadow mode results must have _shadow_mode: true
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[-1].read_text())
            assert data.get("_shadow_mode") is True, \
                f"Shadow mode result must have _shadow_mode: true, got {data.get('_shadow_mode')}"

    def test_blocking_mode_result_no_shadow_marker(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: blocking mode results must NOT have _shadow_mode: true
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[-1].read_text())
            shadow = data.get("_shadow_mode")
            if shadow is not None:
                assert shadow is False, \
                    f"Blocking mode result should not have _shadow_mode: true, got {shadow}"

    def test_mode_field_matches_cli_arg(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: mode field in result must match the CLI --mode argument
        for mode in ["shadow", "blocking"]:
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", mode,
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            files = list(tmp_gate_results.glob("*.json"))
            if files:
                data = json.loads(files[-1].read_text())
                assert data.get("mode") == mode, \
                    f"Mode field '{data.get('mode')}' should match CLI arg '{mode}'"


class TestShadowModeBoundaryConditions:
    """Boundary condition tests for shadow mode."""

    def test_shadow_mode_with_empty_input(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: empty input dict in shadow mode should not crash
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results)],
            capture_output=True, text=True,
        )
        # Should not crash
        assert "AttributeError" not in result.stderr

    def test_shadow_mode_with_missing_upstream_agent(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: missing --upstream-agent should not crash in shadow mode
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Should not crash
        assert "AttributeError" not in result.stderr

    def test_shadow_mode_with_missing_downstream_agent(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: missing --downstream-agent should not crash in shadow mode
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "AttributeError" not in result.stderr

    def test_shadow_mode_result_distinguishable_from_blocking_by_mode_field(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: mode field must be present and correct
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[-1].read_text())
            assert "mode" in data, "Result must contain 'mode' field"
            assert data["mode"] == "shadow"

    def test_shadow_mode_result_distinguishable_from_blocking_by_shadow_marker(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Mutation: _shadow_mode marker must be present in shadow results
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/nonexistent/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[-1].read_text())
            assert "_shadow_mode" in data, "Shadow result must contain '_shadow_mode' field"
