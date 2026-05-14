"""Shadow mode semantics tests.

Covers REQ-05 (shadow mode): AC-05.1 through AC-05.6.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_json


class TestShadowMode:
    """Tests for shadow mode behavior in gate_runner.py."""

    def test_shadow_mode_result_has_mode_field(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.1
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        data = load_json(files[0])
        assert data.get("mode") == "shadow"

    def test_shadow_mode_result_has_shadow_mode_flag(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.1
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        data = load_json(files[0])
        assert data.get("_shadow_mode") is True

    def test_shadow_mode_exits_zero_on_fail(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.2: shadow mode exits 0 even on FAIL gate
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_blocking_mode_exits_nonzero_on_fail(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.3: blocking mode exits non-zero on FAIL
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

    def test_default_mode_is_shadow(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.4
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        files = list(tmp_gate_results.glob("*.json"))
        if files:
            data = load_json(files[0])
            assert data.get("mode") == "shadow"

    def test_shadow_and_blocking_write_to_same_dir(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.5
        subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        shadow_files = [f for f in tmp_gate_results.glob("*.json") if load_json(f).get("mode") == "shadow"]
        blocking_files = [f for f in tmp_gate_results.glob("*.json") if load_json(f).get("mode") == "blocking"]
        assert len(shadow_files) >= 1
        assert len(blocking_files) >= 1

    def test_shadow_mode_result_distinguishable_from_blocking(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.1 + AC-05.5
        subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(Path("/nonexistent/spec.md")), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        data = load_json(files[0])
        assert data.get("_shadow_mode") is True
        assert data.get("mode") == "shadow"
