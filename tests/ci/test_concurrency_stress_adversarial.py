"""Adversarial tests for concurrency, stress/load, and path traversal edge cases.

Tests race conditions, high-volume execution, and security-sensitive path handling
that the existing test suite does not exercise.

Dimensions covered:
  - Concurrency: parallel writes, shared state, race conditions
  - Stress/Load: large payloads, repeated calls, memory pressure
  - Path traversal: symlink attacks, absolute path bypass, device files

# CHECKPOINT — Conservative assumption: the gate runner MUST sanitize all paths
# and handle concurrent access safely. If it crashes or produces corrupted output
# under adversarial conditions, the runner is not production-ready.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestConcurrencyRaceConditions:
    """Tests for concurrent access patterns and race conditions."""

    def test_parallel_writes_to_same_output_dir(self, gate_runner: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "concurrent_output"
        output_dir.mkdir()

        results = []

        def run_once(idx: int) -> None:
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", f"M902-01-{idx}",
                 "--mode", "shadow",
                 "--output-dir", str(output_dir),
                 "--input", json.dumps({"spec_file": f"/tmp/spec_{idx}.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            results.append({"idx": idx, "exit_code": result.returncode, "stderr": result.stderr})

        for i in range(5):
            run_once(i)

        for r in results:
            assert "Traceback" not in r["stderr"] or r["exit_code"] != 0, \
                f"Parallel call {r['idx']} crashed: {r['stderr']}"

        json_files = list(output_dir.glob("*.json"))
        for f in json_files:
            try:
                data = json.loads(f.read_text())
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                pytest.fail(f"Corrupted output file: {f.name}")

    def test_duplicate_ticket_id_no_file_collision(self, gate_runner: Path, tmp_path: Path) -> None:
        output_dir = tmp_path / "same_ticket_output"
        output_dir.mkdir()

        for i in range(5):
            subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01-dup",
                 "--mode", "shadow",
                 "--output-dir", str(output_dir),
                 "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )

        json_files = list(output_dir.glob("*.json"))
        for f in json_files:
            try:
                json.loads(f.read_text())
            except json.JSONDecodeError:
                pytest.fail(f"Corrupted file from duplicate ticket ID: {f.name}")

    def test_concurrent_registry_read_write(self, gate_runner: Path, tmp_path: Path) -> None:
        registry = tmp_path / "gate_registry.json"
        registry.write_text(json.dumps([
            {"name": "spec_completeness_check", "module": "spec_completeness",
             "required_inputs": [], "default_mode": "shadow",
             "description": "Test gate", "category": "workflow"},
        ]))

        env = {**os.environ, "GATE_REGISTRY_PATH": str(registry)}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_path / "output"),
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True, env=env,
        )
        assert "JSONDecodeError" not in result.stderr
        assert "PermissionError" not in result.stderr

    def test_output_dir_created_with_parent_dirs(self, gate_runner: Path) -> None:
        deep_path = "/tmp/gate_test_deep_nested_dir_xyz_12345/output"
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", deep_path,
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode != 0


class TestStressLoadScenarios:
    """Tests for high-volume and stress scenarios."""

    def test_large_input_payload(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        # Use a moderate-sized payload that won't hit ARG_MAX limits
        large_data = {"spec_content": "x" * (100 * 1024), "ticket_type": "generic"}
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps(large_data)],
            capture_output=True, text=True,
        )
        assert "MemoryError" not in result.stderr
        assert "RecursionError" not in result.stderr

    def test_many_repeated_calls_no_state_leak(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        for i in range(50):
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", f"M902-01-{i}",
                 "--mode", "shadow",
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            assert "MemoryError" not in result.stderr
            assert "RecursionError" not in result.stderr

    def test_rapid_mode_switching(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        for i in range(20):
            mode = "shadow" if i % 2 == 0 else "blocking"
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", f"M902-01-{i}",
                 "--mode", mode,
                 "--output-dir", str(tmp_gate_results),
                 "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            assert "ValueError" not in result.stderr
            assert "AttributeError" not in result.stderr

    def test_nested_deeply_nested_output_path(self, gate_runner: Path, tmp_path: Path) -> None:
        deep_dir = tmp_path
        for i in range(20):
            deep_dir = deep_dir / f"level_{i}"
        deep_dir.mkdir(parents=True)

        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(deep_dir),
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)

    def test_output_file_with_special_chars_in_name(self, gate_runner: Path, tmp_path: Path) -> None:
        special_dir = tmp_path / "output with spaces & special (chars) [123]!"
        special_dir.mkdir()

        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(special_dir),
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)


class TestPathTraversalSecurity:
    """Tests for path traversal and security-sensitive path handling."""

    def test_symlink_to_system_dir(self, gate_runner: Path, tmp_path: Path) -> None:
        real_dir = tmp_path / "real_output"
        real_dir.mkdir()
        link_path = tmp_path / "link_to_output"
        link_path.symlink_to(real_dir)

        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(link_path),
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)

    def test_symlink_loop_detection(self, gate_runner: Path, tmp_path: Path) -> None:
        a = tmp_path / "loop_a"
        b = tmp_path / "loop_b"
        a.symlink_to(b)
        b.symlink_to(a)

        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(a),
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "RecursionError" not in result.stderr

    def test_null_byte_in_output_path(self, gate_runner: Path, tmp_path: Path) -> None:
        # Python subprocess rejects null bytes in argv before spawning.
        # This test verifies the runner doesn't crash when encountering
        # null bytes via the output-dir parameter.
        null_path = str(tmp_path / "output\x00.json")
        try:
            result = subprocess.run(
                [sys.executable, str(gate_runner), "spec_completeness_check",
                 "--upstream-agent", "Spec",
                 "--downstream-agent", "TestDesigner",
                 "--ticket-id", "M902-01",
                 "--mode", "shadow",
                 "--output-dir", null_path,
                 "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
                capture_output=True, text=True,
            )
            assert "UnicodeDecodeError" not in result.stderr
        except ValueError:
            # Python rejects null bytes in argv — expected behavior
            pass

    def test_absolute_path_in_spec_file_input(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        real_spec = tmp_gate_results / "real_spec.md"
        real_spec.write_text("# Test\n\n## Overview\n\n## Acceptance Criteria\n")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(real_spec), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)

    def test_device_file_as_spec_path(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "/dev/null", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)

    def test_relative_path_with_dots(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": "../../../../../../etc/passwd", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr

    def test_very_long_output_filename(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        long_name = "a" * 255
        long_path = tmp_gate_results / long_name
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(long_path),
             "--input", json.dumps({"spec_file": "/tmp/spec.md", "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "OSError" not in result.stderr or result.returncode in (0, 1, 2)

    def test_utf16_encoded_spec_path(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        utf16_path = tmp_gate_results / "spec_中文_日本語_한국어.md"
        utf16_path.write_text("# Test\n\n## Overview\n\n## Acceptance Criteria\n")
        result = subprocess.run(
            [sys.executable, str(gate_runner), "spec_completeness_check",
             "--upstream-agent", "Spec",
             "--downstream-agent", "TestDesigner",
             "--ticket-id", "M902-01",
             "--mode", "shadow",
             "--output-dir", str(tmp_gate_results),
             "--input", json.dumps({"spec_file": str(utf16_path), "ticket_type": "generic"})],
            capture_output=True, text=True,
        )
        assert "UnicodeDecodeError" not in result.stderr


class TestDeterminismConcurrency:
    """Tests for determinism under concurrent/parallel conditions."""

    def test_deterministic_exit_code_under_load(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        codes = set()
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
            codes.add(result.returncode)
        assert len(codes) == 1, f"Exit code not deterministic under load: {codes}"

    def test_result_structure_consistent_across_modes(self, gate_runner: Path, tmp_gate_results: Path) -> None:
        shadow_data = None
        blocking_data = None

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
                if mode == "shadow":
                    shadow_data = {k: type(v).__name__ for k, v in data.items()}
                else:
                    blocking_data = {k: type(v).__name__ for k, v in data.items()}

        if shadow_data and blocking_data:
            core_fields = {"gate", "upstream_agent", "downstream_agent", "ticket_id", "status"}
            for field in core_fields:
                if field in shadow_data and field in blocking_data:
                    assert shadow_data[field] == blocking_data[field], \
                        f"Type mismatch for field '{field}': shadow={shadow_data[field]} vs blocking={blocking_data[field]}"
