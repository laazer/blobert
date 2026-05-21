"""Gate registry validation tests.

Covers REQ-04 (gate_registry.json): AC-04.1 through AC-04.7.
"""

import json
from pathlib import Path

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_json


class TestGateRegistry:
    """Tests for ci/scripts/gate_registry.json."""

    def test_registry_file_exists(self, gate_registry: Path) -> None:
        # AC-04.1
        assert gate_registry.exists(), "gate_registry.json must exist"

    def test_registry_valid_json(self, gate_registry: Path) -> None:
        # AC-04.1
        data = load_json(gate_registry)
        assert isinstance(data, list), "Registry must be a top-level array"

    def test_registry_entries_have_required_fields(self, gate_registry: Path) -> None:
        # AC-04.2
        data = load_json(gate_registry)
        required = {"name", "module", "required_inputs", "default_mode", "description", "category"}
        for entry in data:
            assert required.issubset(entry.keys()), f"Entry missing fields: {required - set(entry.keys())}"

    def test_registry_names_unique(self, gate_registry: Path) -> None:
        # AC-04.3
        data = load_json(gate_registry)
        names = [e["name"] for e in data]
        assert len(names) == len(set(names)), f"Duplicate gate names: {[n for n in names if names.count(n) > 1]}"

    def test_registry_modules_exist_as_files(self, gate_registry: Path, gates_pkg: Path) -> None:
        # AC-04.4
        data = load_json(gate_registry)
        for entry in data:
            module_name = entry["module"]
            if "." in module_name:
                module_name = module_name.rsplit(".", 1)[-1]
            module_file = gates_pkg / f"{module_name}.py"
            assert module_file.exists(), f"Module file not found: {module_file}"

    def test_registry_categories_valid(self, gate_registry: Path) -> None:
        # AC-04.5
        data = load_json(gate_registry)
        allowed = {
            "workflow",
            "static_analysis",
            "analysis",
            "governance",
            "per_stage",
            "review",
            "learning",
            "security",
        }
        for entry in data:
            assert entry["category"] in allowed, f"Invalid category: {entry['category']}"

    def test_spec_completeness_check_registered(self, gate_registry: Path) -> None:
        # AC-04.6
        data = load_json(gate_registry)
        names = {e["name"] for e in data}
        assert "spec_completeness_check" in names, "spec_completeness_check gate must be registered"

    def test_registry_max_50_entries(self, gate_registry: Path) -> None:
        # NFR-03: registry must be <= 50 entries
        data = load_json(gate_registry)
        assert len(data) <= 50, f"Registry has {len(data)} entries, max is 50"

    def test_registry_default_mode_values_valid(self, gate_registry: Path) -> None:
        # AC-04.2: default_mode must be "shadow" or "blocking"
        data = load_json(gate_registry)
        for entry in data:
            assert entry["default_mode"] in ("shadow", "blocking"), \
                f"Invalid default_mode: {entry['default_mode']}"

    def test_registry_required_inputs_is_list(self, gate_registry: Path) -> None:
        # AC-04.2: required_inputs must be an array of strings
        data = load_json(gate_registry)
        for entry in data:
            ri = entry["required_inputs"]
            assert isinstance(ri, list), f"required_inputs must be a list, got {type(ri)}"
            for item in ri:
                assert isinstance(item, str), f"required_inputs items must be strings"
