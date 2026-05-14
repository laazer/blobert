"""Adversarial tests for gate registry (gate_registry.json).

Tests registry corruption, boundary conditions, and type mutations that
could cause the gate runner to fail or behave incorrectly.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestRegistryCorruption:
    """Test how the runner handles corrupted registry data."""

    def test_registry_with_extra_unknown_fields(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: registry entries with unexpected extra fields should not crash
        registry = [
            {
                "name": "spec_completeness_check",
                "module": "spec_completeness",
                "required_inputs": ["spec_file"],
                "default_mode": "shadow",
                "description": "Test gate",
                "category": "workflow",
                "extra_field": "should be ignored",
                "another_extra": {"nested": True},
            }
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with KeyError or AttributeError
        assert "KeyError" not in result.stderr
        assert "AttributeError" not in result.stderr

    def test_registry_with_duplicate_names(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: duplicate gate names should cause deterministic behavior
        registry = [
            {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Dup 1", "category": "workflow"},
            {"name": "spec_completeness_check", "module": "spec_completeness2",
             "required_inputs": [], "default_mode": "blocking",
             "description": "Dup 2", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash; should handle duplicates deterministically
        assert "KeyError" not in result.stderr

    def test_registry_with_missing_module_field(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: missing module field should not cause AttributeError
        registry = [
            {"name": "spec_completeness_check",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Test gate", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "AttributeError" not in result.stderr

    def test_registry_with_non_string_required_inputs(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: non-string items in required_inputs should be handled
        registry = [
            {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [123, None, True], "default_mode": "shadow",
             "description": "Test gate", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash
        assert "TypeError" not in result.stderr

    def test_registry_with_invalid_category(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: unknown category should not crash
        registry = [
            {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Test gate", "category": "unknown_category_xyz"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "KeyError" not in result.stderr

    def test_registry_with_empty_array(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: empty registry array should not crash
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text("[]")
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should fail gracefully (gate not found) not crash
        assert "JSONDecodeError" not in result.stderr
        assert "KeyError" not in result.stderr

    def test_registry_with_non_array_top_level(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: non-array top-level should fail gracefully
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text('{"gates": []}')
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "JSONDecodeError" not in result.stderr

    def test_registry_with_null_entries(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: null entries in array should not crash
        registry = [None, {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Test gate", "category": "workflow"}, None]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "TypeError" not in result.stderr

    def test_registry_with_malformed_json(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: malformed JSON should fail gracefully
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text('{"name": "spec_completeness_check", "module": "spec_completeness"')
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with unexpected exception
        assert "UnicodeDecodeError" not in result.stderr

    def test_registry_with_very_long_entry_names(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: extremely long gate/module names should not cause issues
        long_name = "a" * 10000
        registry = [
            {"name": long_name, "module": long_name,
             "required_inputs": [], "default_mode": "shadow",
             "description": "Long name test", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), long_name,
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        # Should not crash with MemoryError or RecursionError
        assert "MemoryError" not in result.stderr
        assert "RecursionError" not in result.stderr


class TestRegistryBoundaryConditions:
    """Boundary condition tests for registry."""

    def test_registry_with_zero_entries(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: zero entries → gate not found
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text("[]")
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode != 0

    def test_registry_with_whitespace_only(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: whitespace-only file should fail gracefully
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text("   \n\t\n  ")
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "JSONDecodeError" not in result.stderr

    def test_registry_with_emoji_in_description(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: emoji in description should not cause encoding issues
        registry = [
            {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Gate with emoji \U0001f680\U0001f527", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry, ensure_ascii=False))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_registry_with_unicode_gate_name(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: Unicode gate name should be handled
        registry = [
            {"name": "gate_\u00e9\u00e8\u00ea", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Unicode name", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry, ensure_ascii=False))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "gate_\u00e9\u00e8\u00ea",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_registry_with_default_mode_other_than_shadow_blocking(self, tmp_path: Path, gate_runner: Path) -> None:
        # Mutation: invalid default_mode should not crash
        registry = [
            {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "unknown_mode",
             "description": "Test gate", "category": "workflow"},
        ]
        reg_path = tmp_path / "gate_registry.json"
        reg_path.write_text(json.dumps(registry))
        env = {**__import__("os").environ, "GATE_REGISTRY_PATH": str(reg_path)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01"],
            capture_output=True, text=True, env=env,
        )
        assert "AttributeError" not in result.stderr
