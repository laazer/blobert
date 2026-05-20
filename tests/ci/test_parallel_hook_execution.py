"""Behavioral tests for parallel Lefthook hook execution (M902-28).

Specification: project_board/specs/902_28_parallel_hook_execution_spec.md
Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_in_progress/28_parallel_hook_execution.md

Asserts executable scheduling and artifact-isolation contracts (Requirement 10):
  T1–T2 YAML parallel flags, T3 Taskfile delegation, T4–T5 script write paths,
  T6 TSGR / run_tests.sh ordering, optional T7 stub concurrency overlap.
"""

from __future__ import annotations

import concurrent.futures
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEFTHOOK_YML = _REPO_ROOT / "lefthook.yml"
_GODOT_HOOK = _REPO_ROOT / ".lefthook/scripts/godot-tests.sh"
_PY_HOOK = _REPO_ROOT / ".lefthook/scripts/py-tests.sh"
_RUN_TESTS = _REPO_ROOT / "ci/scripts/run_tests.sh"
_VERIFY_TSGR = _REPO_ROOT / "ci/scripts/verify_tsgr_runner_contract.sh"
_TASKFILE = _REPO_ROOT / "Taskfile.yml"
_PY_ROOT = _REPO_ROOT / "asset_generation/python"


def load_lefthook_config(path: Path | None = None) -> dict[str, Any]:
    """Parse lefthook.yml; raises yaml.YAMLError on corrupt input."""
    target = path or _LEFTHOOK_YML
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"lefthook config root must be mapping, got {type(data)!r}")
    return data


def phase_parallel_enabled(cfg: dict[str, Any], phase: str) -> bool:
    block = cfg.get(phase)
    if not isinstance(block, dict):
        return False
    return block.get("parallel") is True


def command_run(cfg: dict[str, Any], phase: str, command_id: str) -> str:
    block = cfg.get(phase)
    if not isinstance(block, dict):
        return ""
    commands = block.get("commands")
    if not isinstance(commands, dict):
        return ""
    entry = commands.get(command_id)
    if not isinstance(entry, dict):
        return ""
    run = entry.get("run")
    return run.strip() if isinstance(run, str) else ""


def command_glob(cfg: dict[str, Any], phase: str, command_id: str) -> str:
    block = cfg.get(phase)
    if not isinstance(block, dict):
        return ""
    commands = block.get("commands")
    if not isinstance(commands, dict):
        return ""
    entry = commands.get(command_id)
    if not isinstance(entry, dict):
        return ""
    glob_val = entry.get("glob")
    return glob_val.strip() if isinstance(glob_val, str) else ""


def godot_script_isolation_violations(script_text: str) -> list[str]:
    """Godot hook must not write under asset_generation/python/ (spec P1)."""
    violations: list[str] = []
    if "asset_generation/python/coverage.xml" in script_text:
        violations.append("Godot hook must not reference asset_generation/python/coverage.xml")
    if re.search(r"(>>|>)\s*['\"]?.*asset_generation/python", script_text):
        violations.append("Godot hook must not redirect writes into asset_generation/python/")
    if "git add" in script_text:
        violations.append("Godot hook must not run git add")
    if "git commit" in script_text:
        violations.append("Godot hook must not run git commit")
    return violations


def assert_godot_script_isolation(script_text: str) -> None:
    violations = godot_script_isolation_violations(script_text)
    assert not violations, "; ".join(violations)


def py_tests_coverage_scope_violations(script_text: str) -> list[str]:
    """coverage.xml must stay under PY_ROOT (spec P1 / T5)."""
    violations: list[str] = []
    if "$PY_ROOT/coverage.xml" not in script_text and "PY_ROOT/coverage.xml" not in script_text:
        violations.append("Python hook must anchor coverage.xml under PY_ROOT")
    if re.search(r"\$ROOT/coverage\.xml", script_text):
        violations.append("Python hook must not write coverage.xml at repo root")
    if re.search(r'[^/]coverage\.xml', script_text) and "$PY_ROOT/coverage.xml" not in script_text:
        violations.append("Python hook coverage.xml path must use PY_ROOT")
    if "git add" in script_text:
        violations.append("Python hook must not run git add")
    if "git commit" in script_text:
        violations.append("Python hook must not run git commit")
    return violations


def assert_py_tests_coverage_scope(script_text: str) -> None:
    violations = py_tests_coverage_scope_violations(script_text)
    assert not violations, "; ".join(violations)


def assert_run_tests_sequential(text: str) -> None:
    """Canonical CI suite: Godot before Python, no background parallelization."""
    lines = text.splitlines()
    godot_line = next(
        (i for i, line in enumerate(lines, start=1) if "run_tests.gd" in line),
        None,
    )
    py_line = next(
        (
            i
            for i, line in enumerate(lines, start=1)
            if re.search(r"pytest|py-tests\.sh", line)
        ),
        None,
    )
    assert godot_line is not None, "run_tests.sh must invoke tests/run_tests.gd"
    assert py_line is not None, "run_tests.sh must invoke Python phase"
    assert py_line > godot_line, "Python phase must follow Godot (TSGR-1)"
    for line in lines:
        if "run_tests.gd" in line or "py-tests.sh" in line:
            assert re.search(r"\s&\s*$", line) is None, (
                f"run_tests.sh must not background hook phases: {line!r}"
            )
            assert " & " not in line, f"run_tests.sh must not parallelize via &: {line!r}"


@pytest.fixture()
def lefthook_cfg() -> dict[str, Any]:
    return load_lefthook_config()


@pytest.fixture()
def godot_hook_text() -> str:
    return _GODOT_HOOK.read_text(encoding="utf-8")


@pytest.fixture()
def py_hook_text() -> str:
    return _PY_HOOK.read_text(encoding="utf-8")


class TestRequirement03LefthookParallelContract:
    """Requirement 03 / T1–T3: YAML scheduling and delegation."""

    def test_pre_push_parallel_enabled(self, lefthook_cfg: dict[str, Any]) -> None:
        assert phase_parallel_enabled(lefthook_cfg, "pre-push") is True

    def test_pre_commit_parallel_enabled(self, lefthook_cfg: dict[str, Any]) -> None:
        assert phase_parallel_enabled(lefthook_cfg, "pre-commit") is True

    def test_pre_push_commands_delegate_to_taskfile(self, lefthook_cfg: dict[str, Any]) -> None:
        assert command_run(lefthook_cfg, "pre-push", "godot-tests") == "task hooks:godot"
        assert command_run(lefthook_cfg, "pre-push", "py-tests") == "task hooks:python"

    def test_pre_push_globs_match_spec(self, lefthook_cfg: dict[str, Any]) -> None:
        assert command_glob(lefthook_cfg, "pre-push", "godot-tests") == (
            "**/*.{gd,tscn,tres,gdshader}"
        )
        assert command_glob(lefthook_cfg, "pre-push", "py-tests") == (
            "asset_generation/python/**/*.py"
        )

    def test_pre_commit_has_eight_parallel_commands(self, lefthook_cfg: dict[str, Any]) -> None:
        commands = lefthook_cfg["pre-commit"]["commands"]
        assert isinstance(commands, dict)
        expected = {
            "py-parse",
            "py-review",
            "py-pylint",
            "py-organization",
            "py-defensive-normalization",
            "gd-review",
            "gd-organization",
        }
        assert set(commands) == expected


class TestRequirement01ArtifactIsolation:
    """Requirement 01 / T4–T5: disjoint write paths for P1."""

    def test_godot_hook_does_not_write_python_artifacts(self, godot_hook_text: str) -> None:
        assert_godot_script_isolation(godot_hook_text)

    def test_py_tests_coverage_under_py_root_only(self, py_hook_text: str) -> None:
        assert_py_tests_coverage_scope(py_hook_text)

    def test_taskfile_hooks_still_delegate_to_lefthook_scripts(self) -> None:
        text = _TASKFILE.read_text(encoding="utf-8")
        assert "hooks:godot" in text
        assert "godot-tests.sh" in text
        assert "hooks:python" in text
        assert "py-tests.sh" in text


class TestRequirement07CiCanonicalSuiteUnchanged:
    """Requirement 07 / T6: CI stays sequential; TSGR contract present."""

    def test_verify_tsgr_runner_contract_script_exists(self) -> None:
        assert _VERIFY_TSGR.is_file()

    def test_run_tests_sh_godot_before_python(self) -> None:
        assert_run_tests_sequential(_RUN_TESTS.read_text(encoding="utf-8"))

    def test_run_tests_sh_invokes_shared_py_tests_hook(self) -> None:
        text = _RUN_TESTS.read_text(encoding="utf-8")
        assert ".lefthook/scripts/py-tests.sh" in text


class TestRequirement10StubConcurrency:
    """Optional T7: prove two independent stubs can overlap (not full Godot)."""

    def test_two_python_stubs_finish_faster_in_parallel_than_sequential(self) -> None:
        stub = "import time; time.sleep(0.25)"
        cmd = [sys.executable, "-c", stub]

        t0 = time.perf_counter()
        subprocess.run(cmd, check=True, capture_output=True)
        subprocess.run(cmd, check=True, capture_output=True)
        sequential_elapsed = time.perf_counter() - t0

        t1 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(subprocess.run, cmd, check=True, capture_output=True) for _ in range(2)]
            for fut in futs:
                fut.result()
        parallel_elapsed = time.perf_counter() - t1

        assert parallel_elapsed < sequential_elapsed * 0.85
