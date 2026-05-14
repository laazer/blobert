"""Spec → test_design handoff wiring tests.

Covers REQ-06 (handoff wiring): AC-06.1 through AC-06.8.
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


class TestHandoffWiring:
    """Tests for spec → test_design handoff wiring (REQ-06)."""

    def test_gate_wrapper_module_exists(self, gates_pkg: Path) -> None:
        # AC-06.1
        wrapper = gates_pkg / "spec_completeness.py"
        assert wrapper.exists(), "Gate wrapper module must exist at ci/scripts/gates/spec_completeness.py"

    def test_gate_wrapper_is_valid_python(self, gates_pkg: Path) -> None:
        # AC-06.1
        wrapper = gates_pkg / "spec_completeness.py"
        code = wrapper.read_text()
        compile(code, str(wrapper), "exec")

    def test_gate_wrapper_runnable_via_runner(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-06.2
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
        assert data.get("gate") == "spec_completeness_check"

    def test_gate_wrapper_produces_pass_on_valid_spec(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-06.3: passing spec → PASS record
        # Use the actual spec file which should pass
        spec_path = Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")
        if not spec_path.exists():
            pytest.skip("Spec file not found for pass test")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(spec_path), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        data = load_json(files[0])
        assert data.get("status") == "PASS"

    def test_gate_wrapper_produces_fail_on_missing_sections(self, gate_runner: Path, tmp_gate_results: Path, tmp_path: Path) -> None:
        # AC-06.4: failing spec → FAIL record with violations
        # Create a minimal spec that will fail the completeness check
        bad_spec = tmp_path / "bad_spec.md"
        bad_spec.write_text("# Bad Spec\n\nJust a title with no required sections.\n")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(bad_spec), "ticket_type": "api"})],
            capture_output=True, text=True,
        )
        files = list(tmp_gate_results.glob("*.json"))
        assert len(files) >= 1
        data = load_json(files[0])
        assert data.get("status") == "FAIL"
        assert "violations" in data
        violations = data.get("violations", [])
        assert len(violations) > 0

    def test_gate_registered_with_shadow_default(self, gate_registry: Path) -> None:
        # AC-06.5
        data = load_json(gate_registry)
        for entry in data:
            if entry["name"] == "spec_completeness_check":
                assert entry["default_mode"] == "shadow", \
                    "spec_completeness_check must default to shadow mode"
                break
        else:
            pytest.fail("spec_completeness_check not found in registry")

    def test_spec_completeness_check_still_works_standalone(self) -> None:
        # AC-06.6: existing script must still work standalone
        spec_path = Path("/Users/jacobbrandt/workspace/blobert/project_board/specs/902_01_gate_runner_spec.md")
        if not spec_path.exists():
            pytest.skip("Spec file not found for standalone test")
        result = subprocess.run(
            [sys.executable, "/Users/jacobbrandt/workspace/blobert/ci/scripts/spec_completeness_check.py",
             str(spec_path), "--type", "generic"],
            capture_output=True, text=True,
        )
        # Should exit 0 (pass) or 1 (fail) but not 2 (usage error)
        assert result.returncode in (0, 1), \
            f"Standalone script failed with exit code {result.returncode}: {result.stderr}"

    def test_milestone_readme_has_gate_runner_section(self, repo_root: Path) -> None:
        # AC-06.8
        readme = repo_root / "project_board" / "902_milestone_902_agent_predictabilitiy_improvements" / "README.md"
        content = readme.read_text()
        assert "Gate Runner" in content or "gate_runner" in content.lower(), \
            "Milestone README must contain a Gate Runner section"

    def test_gate_wrapper_has_run_function(self, gates_pkg: Path) -> None:
        # AC-06.1: gate module must implement run(inputs) -> dict
        wrapper = gates_pkg / "spec_completeness.py"
        code = wrapper.read_text()
        assert "def run(" in code, "Gate wrapper must define a run(inputs) function"

    def test_gate_result_includes_mode_field(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # AC-05.1: result file must include "mode" field
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
        assert "mode" in data

    def test_gate_result_includes_upstream_downstream_agents(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Result should include agent metadata
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
        if files:
            data = load_json(files[0])
            assert data.get("upstream_agent") == "Spec"
            assert data.get("downstream_agent") == "TestDesigner"

    def test_gate_result_includes_ticket_id(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Result should include ticket_id
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
        if files:
            data = load_json(files[0])
            assert data.get("ticket_id") == "M902-01"
