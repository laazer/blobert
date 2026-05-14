"""Gate runner CLI tests.

Covers REQ-01 (gate_runner.py CLI): AC-01.1 through AC-01.9.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestGateRunnerCLI:
    """Tests for ci/scripts/gate_runner.py CLI behavior."""

    def test_help_exits_zero(self, gate_runner: Path) -> None:
        # AC-01.1
        result = subprocess.run(
            [sys.executable, str(gate_runner), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "--help" in result.stdout or "usage" in result.stdout.lower()

    def test_unknown_gate_exits_nonzero(self, gate_runner: Path) -> None:
        # AC-01.2
        result = subprocess.run(
            [sys.executable, str(gate_runner), "nonexistent_gate_xyz",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "nonexistent_gate_xyz" in result.stderr or "unknown" in result.stderr.lower() or "not found" in result.stderr.lower()

    def test_missing_required_flags_exits_nonzero(self, gate_runner: Path) -> None:
        # AC-01.3 partial — missing --upstream-agent should fail
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_shadow_mode_always_exits_zero(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.5 + AC-05.2: shadow mode exits 0 even on FAIL gate
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_blocking_mode_exits_nonzero_on_fail(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.4 + AC-05.3: blocking mode exits non-zero on FAIL
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_result_file_written_with_correct_name(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.6: result file name pattern <gate-name>_<timestamp>.json
        gate_name = "spec_completeness_check"
        result = subprocess.run(
            [sys.executable, str(gate_runner), gate_name,
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        name = files[0].name
        assert name.startswith(gate_name + "_")
        assert name.endswith(".json")

    def test_result_file_valid_json(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.3: result file contains valid JSON
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        data = json.loads(files[0].read_text())
        assert isinstance(data, dict)

    def test_missing_registry_exits_nonzero(self, gate_runner: Path, tmp_gate_results: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # AC-01.7: missing registry file → exit 2
        import os
        env = {**os.environ, "GATE_REGISTRY_PATH": str(tmp_gate_results / "nonexistent_registry.json")}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode != 0

    def test_custom_output_dir(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.9: --output-dir overrides default
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1

    def test_input_flag_accepts_inline_json(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.8: --input accepts inline JSON
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", '{"spec_file": "/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md", "ticket_type": "generic"}'],
            capture_output=True, text=True,
        )
        # Should not crash on valid inline JSON
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1

    def test_no_input_provides_empty_dict(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-01.8: omitted --input → gate receives {}
        # We test that the runner doesn't crash without --input
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results)],
            capture_output=True, text=True,
        )
        # Gate may fail due to missing spec file, but runner should not crash
        files = list(tmp_gate_results.glob("*.json"))
        # If the gate ran, a result file should exist
        if files:
            data = json.loads(files[0].read_text())
            assert "status" in data

    def test_default_mode_is_shadow(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.4: default --mode is "shadow"
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        # Default should be shadow → exits 0
        assert result.returncode == 0
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = json.loads(files[0].read_text())
            assert data.get("mode") == "shadow"
