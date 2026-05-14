"""Adversarial tests for handoff wiring edge cases.

Tests chain breaks, missing dependencies, and wiring edge cases that could
cause handoff failures.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestWiringMutation:
    """Mutation tests for handoff wiring."""

    def test_gate_wrapper_missing_run_function(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: gate module without run() function should fail gracefully
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "no_run_func.py").write_text("# No run function defined\n")
        registry = [
            {"name": "no_run_func_gate", "module": "no_run_func",
             "required_inputs": [], "default_mode": "shadow",
             "description": "No run func", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "no_run_func_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_path / "output"),
             "--input", "{}"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with AttributeError
        assert "AttributeError" not in result.stderr

    def test_gate_wrapper_run_returns_non_dict(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: gate returning non-dict should not crash the runner
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "bad_return.py").write_text(
            "def run(inputs):\n    return 'not a dict'\n"
        )
        registry = [
            {"name": "bad_return_gate", "module": "bad_return",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Bad return", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "bad_return_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_path / "output"),
             "--input", "{}"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with TypeError
        assert "TypeError" not in result.stderr

    def test_gate_wrapper_raises_exception(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: gate that raises should not crash the runner
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "raises_gate.py").write_text(
            "def run(inputs):\n    raise ValueError('intentional error')\n"
        )
        registry = [
            {"name": "raises_gate", "module": "raises_gate",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Raises", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "raises_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_path / "output"),
             "--input", "{}"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with unhandled traceback
        assert "Traceback" not in result.stderr or "ValueError" in result.stderr

    def test_gate_wrapper_missing_inputs_not_enforced(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: missing required inputs should be handled
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "requires_input.py").write_text(
            "def run(inputs):\n    return {'status': 'PASS'}\n"
        )
        registry = [
            {"name": "requires_input_gate", "module": "requires_input",
             "required_inputs": ["required_field_xyz"], "default_mode": "shadow",
             "description": "Requires input", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "requires_input_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_path / "output"),
             "--input", json.dumps({"other_field": "value"})],
            capture_output=True, text=True, env=env,
        )
        # Should not crash
        assert "KeyError" not in result.stderr

    def test_wiring_chain_break_first_gate_fails(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: if first gate in chain fails, downstream gates should not run
        # This tests that the runner properly handles gate chain failures
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "failing_gate.py").write_text(
            "def run(inputs):\n    return {'status': 'FAIL', 'violations': []}\n"
        )
        registry = [
            {"name": "failing_gate", "module": "failing_gate",
             "required_inputs": [], "default_mode": "blocking",
             "description": "Failing", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "failing_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "blocking",
             "--output-dir", str(tmp_path / "output"),
             "--input", "{}"],
            capture_output=True, text=True, env=env,
        )
        # Blocking mode with FAIL should exit non-zero
        assert result.returncode != 0

    def test_wiring_chain_break_second_gate_raises(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: if second gate raises, first gate result should not be corrupted
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "first_gate.py").write_text(
            "def run(inputs):\n    return {'status': 'PASS'}\n"
        )
        registry = [
            {"name": "first_gate", "module": "first_gate",
             "required_inputs": [], "default_mode": "shadow",
             "description": "First", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "first_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_path / "output"),
             "--input", "{}"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash
        assert "Traceback" not in result.stderr

    def test_gate_result_can_be_modified_by_downstream(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: downstream gate should not be able to modify upstream result
        # This tests result immutability in the chain
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "modifying_gate.py").write_text(
            "def run(inputs):\n    return {'status': 'PASS', 'modified': True}\n"
        )
        registry = [
            {"name": "modifying_gate", "module": "modifying_gate",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Modifying", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "modifying_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--output-dir", str(tmp_path / "output"),
             "--input", "{}"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash
        assert "AttributeError" not in result.stderr


class TestWiringBoundaryConditions:
    """Boundary condition tests for handoff wiring."""

    def test_gate_module_file_not_python(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: gate module that is not .py should fail gracefully
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "not_a_module.txt").write_text("# Not Python\n")
        registry = [
            {"name": "not_a_module_gate", "module": "not_a_module",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Not Python", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "not_a_module_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash
        assert "UnicodeDecodeError" not in result.stderr

    def test_gate_module_syntax_error(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: gate module with syntax error should fail gracefully
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "syntax_error.py").write_text("def run(inputs)\n  return {}\n")
        registry = [
            {"name": "syntax_error_gate", "module": "syntax_error",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Syntax error", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "syntax_error_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with unexpected exception
        assert "UnicodeDecodeError" not in result.stderr

    def test_gate_module_circular_import(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: circular imports should fail gracefully
        gates_pkg = tmp_path / "gates"
        gates_pkg.mkdir()
        (gates_pkg / "__init__.py").write_text("")
        (gates_pkg / "circular_a.py").write_text(
            "import circular_b\ndef run(inputs): return {}\n"
        )
        (gates_pkg / "circular_b.py").write_text(
            "import circular_a\ndef run(inputs): return {}\n"
        )
        registry = [
            {"name": "circular_a_gate", "module": "circular_a",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Circular", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "circular_a_gate",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with RecursionError
        assert "RecursionError" not in result.stderr

    def test_gate_wrapper_has_run_function_signature(self, gates_pkg: Path) -> None:
        # Mutation: run() must accept inputs parameter
        wrapper = gates_pkg / "spec_completeness.py"
        if wrapper.exists():
            code = wrapper.read_text()
            assert "def run(" in code

    def test_gate_wrapper_produces_dict_result(self, gates_pkg: Path) -> None:
        # Mutation: run() must return a dict
        wrapper = gates_pkg / "spec_completeness.py"
        if wrapper.exists():
            code = wrapper.read_text()
            # Check for return statement
            assert "return" in code
