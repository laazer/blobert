"""Adversarial tests for parallel Lefthook hook execution (M902-28).

Exposes YAML regression vectors, YAML type confusion, policy drift, artifact
contention, CI sequencing mutations, and collection stability beyond
`tests/ci/test_parallel_hook_execution.py`.

Traceability: M902-28 / project_board/specs/902_28_parallel_hook_execution_spec.md
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_CONTRACT_PATH = Path(__file__).resolve().parent / "test_parallel_hook_execution.py"
_CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "parallel_hook_contract",
    _CONTRACT_PATH,
)
assert _CONTRACT_SPEC and _CONTRACT_SPEC.loader
_contract = importlib.util.module_from_spec(_CONTRACT_SPEC)
_CONTRACT_SPEC.loader.exec_module(_contract)

_GODOT_HOOK = _contract._GODOT_HOOK
_LEFTHOOK_YML = _contract._LEFTHOOK_YML
_PY_HOOK = _contract._PY_HOOK
_REPO_ROOT = _contract._REPO_ROOT
_RUN_TESTS = _contract._RUN_TESTS
_VERIFY_TSGR = _contract._VERIFY_TSGR
assert_godot_script_isolation = _contract.assert_godot_script_isolation
assert_py_tests_coverage_scope = _contract.assert_py_tests_coverage_scope
godot_script_isolation_violations = _contract.godot_script_isolation_violations
py_tests_coverage_scope_violations = _contract.py_tests_coverage_scope_violations
assert_run_tests_sequential = _contract.assert_run_tests_sequential
command_glob = _contract.command_glob
command_run = _contract.command_run
load_lefthook_config = _contract.load_lefthook_config
phase_parallel_enabled = _contract.phase_parallel_enabled

yaml = pytest.importorskip("yaml")

_SPEC_FORBIDDEN_ENV = "BLOBERT_HOOKS_PARALLEL"
_GOVERNANCE_MONITORED = frozenset(
    {
        "CLAUDE.md",
        "Taskfile.yml",
        "lefthook.yml",
        "project_board/CHECKPOINTS.md",
        ".gitignore",
    }
)


def _scheduling_contract(cfg: dict[str, Any]) -> list[str]:
    """Return human-readable contract violations (empty == pass)."""
    violations: list[str] = []
    if not phase_parallel_enabled(cfg, "pre-push"):
        violations.append("pre-push.parallel must be true")
    if not phase_parallel_enabled(cfg, "pre-commit"):
        violations.append("pre-commit.parallel must be true")
    if command_run(cfg, "pre-push", "godot-tests") != "task hooks:godot":
        violations.append("godot-tests.run must delegate to task hooks:godot")
    if command_run(cfg, "pre-push", "py-tests") != "task hooks:python":
        violations.append("py-tests.run must delegate to task hooks:python")
    return violations


class TestYamlParallelRegression:
    """Mutation: parallel flag removed, false, or wrong YAML type."""

    def test_parallel_false_string_is_not_enabled(self, tmp_path: Path) -> None:
        """VULNERABILITY: parallel: 'false' is a non-empty string → truthy in YAML bool coercion."""
        mutated = _LEFTHOOK_YML.read_text(encoding="utf-8").replace(
            "pre-push:\n  parallel: false",
            "pre-push:\n  parallel: 'false'",
            1,
        )
        path = tmp_path / "lefthook.yml"
        path.write_text(mutated, encoding="utf-8")
        cfg = load_lefthook_config(path)
        assert phase_parallel_enabled(cfg, "pre-push") is False

    def test_missing_pre_push_parallel_key_fails_contract(self, tmp_path: Path) -> None:
        mutated = re.sub(
            r"(?m)^pre-push:\n  parallel: (true|false)\n",
            "pre-push:\n",
            _LEFTHOOK_YML.read_text(encoding="utf-8"),
            count=1,
        )
        path = tmp_path / "lefthook.yml"
        path.write_text(mutated, encoding="utf-8")
        cfg = load_lefthook_config(path)
        assert "pre-push.parallel must be true" in _scheduling_contract(cfg)

    def test_pre_commit_parallel_false_regression_detected(self, tmp_path: Path) -> None:
        mutated = _LEFTHOOK_YML.read_text(encoding="utf-8").replace(
            "pre-commit:\n  parallel: true",
            "pre-commit:\n  parallel: false",
            1,
        )
        path = tmp_path / "lefthook.yml"
        path.write_text(mutated, encoding="utf-8")
        cfg = load_lefthook_config(path)
        assert "pre-commit.parallel must be true" in _scheduling_contract(cfg)

    def test_duplicate_parallel_key_last_value_wins(self, tmp_path: Path) -> None:
        """YAML duplicate keys: last wins — false after true must disable parallelism."""
        block = (
            "pre-push:\n"
            "  parallel: true\n"
            "  parallel: false\n"
            "  commands:\n"
            "    godot-tests:\n"
            "      run: task hooks:godot\n"
        )
        path = tmp_path / "lefthook_dup.yml"
        path.write_text(block, encoding="utf-8")
        cfg = load_lefthook_config(path)
        assert phase_parallel_enabled(cfg, "pre-push") is False


class TestPolicyDriftMutations:
    """Mutation: command paths, globs, or env kill-switch drift."""

    def test_direct_bash_godot_script_instead_of_task_fails_contract(self, tmp_path: Path) -> None:
        cfg = load_lefthook_config()
        cfg["pre-push"] = dict(cfg["pre-push"])
        cfg["pre-push"]["commands"] = dict(cfg["pre-push"]["commands"])
        cfg["pre-push"]["commands"]["godot-tests"] = dict(
            cfg["pre-push"]["commands"]["godot-tests"]
        )
        cfg["pre-push"]["commands"]["godot-tests"]["run"] = (
            "bash .lefthook/scripts/godot-tests.sh"
        )
        path = tmp_path / "lefthook.yml"
        path.write_text(yaml.dump(cfg), encoding="utf-8")
        loaded = load_lefthook_config(path)
        violations = _scheduling_contract(loaded)
        assert any("godot-tests.run" in v for v in violations)

    def test_narrowed_godot_glob_excludes_gd_files(self) -> None:
        cfg = load_lefthook_config()
        cfg["pre-push"] = dict(cfg["pre-push"])
        cfg["pre-push"]["commands"] = dict(cfg["pre-push"]["commands"])
        cfg["pre-push"]["commands"]["godot-tests"] = dict(
            cfg["pre-push"]["commands"]["godot-tests"]
        )
        cfg["pre-push"]["commands"]["godot-tests"]["glob"] = "**/*.tscn"
        assert command_glob(cfg, "pre-push", "godot-tests") != "**/*.{gd,tscn,tres,gdshader}"

    def test_blobert_hooks_parallel_env_not_introduced_in_implementation_tree(self) -> None:
        """Spec Req 05: do not add unsupported BLOBERT_HOOKS_PARALLEL to hook/config surfaces."""
        scan_roots = [
            _REPO_ROOT / "lefthook.yml",
            _REPO_ROOT / "Taskfile.yml",
            _REPO_ROOT / "CLAUDE.md",
            _REPO_ROOT / ".lefthook",
            _REPO_ROOT / "ci",
        ]
        hits: list[str] = []
        for root in scan_roots:
            paths = [root] if root.is_file() else list(root.rglob("*"))
            for path in paths:
                if not path.is_file():
                    continue
                if path.suffix in {".png", ".glb", ".jpg", ".webp", ".pyc"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if _SPEC_FORBIDDEN_ENV in text:
                    hits.append(str(path.relative_to(_REPO_ROOT)))
        assert hits == [], f"Forbidden env in implementation paths: {hits}"


class TestScriptIsolationMutations:
    """Mutation: shared coverage.xml or cross-root writes (P1 UNSAFE)."""

    def test_godot_hook_writing_coverage_xml_fails_isolation(self) -> None:
        mutated = (
            _GODOT_HOOK.read_text(encoding="utf-8")
            + '\necho "x" >> asset_generation/python/coverage.xml\n'
        )
        violations = godot_script_isolation_violations(mutated)
        assert any("coverage.xml" in v for v in violations)

    def test_py_hook_root_level_coverage_path_fails_scope(self) -> None:
        mutated = re.sub(
            r"\$PY_ROOT/coverage\.xml",
            "$ROOT/coverage.xml",
            _PY_HOOK.read_text(encoding="utf-8"),
        )
        violations = py_tests_coverage_scope_violations(mutated)
        assert violations, f"expected scope violations, got none: {mutated[:200]}"

    def test_concurrent_writes_same_coverage_xml_corrupt_or_race(
        self, tmp_path: Path
    ) -> None:
        """Combinatorial: parallel writers to one coverage.xml (simulated P1 contention)."""
        cov = tmp_path / "coverage.xml"
        cov.write_text("<coverage></coverage>", encoding="utf-8")
        errors: list[str] = []

        def writer(tag: str) -> None:
            try:
                for _ in range(50):
                    cov.write_text(f"<coverage agent='{tag}'/>", encoding="utf-8")
            except OSError as exc:
                errors.append(str(exc))

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futs = [pool.submit(writer, f"w{i}") for i in range(4)]
            for fut in futs:
                fut.result()
        assert not errors
        final = cov.read_text(encoding="utf-8")
        assert final.startswith("<coverage agent='w")


class TestCiSequencingMutations:
    """Mutation: run_tests.sh parallelized or TSGR contract removed."""

    def test_run_tests_background_ampersand_fails_sequential_guard(self) -> None:
        mutated = _RUN_TESTS.read_text(encoding="utf-8").replace(
            "timeout 300 godot",
            "timeout 300 godot &",
            1,
        )
        with pytest.raises(AssertionError):
            assert_run_tests_sequential(mutated)

    def test_run_tests_python_before_godot_fails_ordering(self) -> None:
        mutated = (
            "#!/usr/bin/env bash\n"
            "set -e\n"
            "bash .lefthook/scripts/py-tests.sh\n"
            "timeout 300 godot --headless -s tests/run_tests.gd\n"
        )
        with pytest.raises(AssertionError, match="Python phase must follow"):
            assert_run_tests_sequential(mutated)

    def test_verify_tsgr_still_checks_godot_hook_script(self) -> None:
        text = _VERIFY_TSGR.read_text(encoding="utf-8")
        assert "godot-tests.sh" in text
        assert "_check_godot_hook" in text


class TestGovernanceAndCollectionStability:
    """Handoff metadata + determinism under repeated collection."""

    def test_lefthook_yml_remains_governance_monitored_file(self) -> None:
        ci_scripts = str(_REPO_ROOT / "ci" / "scripts")
        if ci_scripts not in sys.path:
            sys.path.insert(0, ci_scripts)
        from escalation_detectors import _MONITORED_FILES

        assert "lefthook.yml" in _MONITORED_FILES
        assert _GOVERNANCE_MONITORED == _MONITORED_FILES


_COLLECT_BASELINE: int | None = None


@pytest.mark.parametrize("run_idx", range(4))
def test_pytest_collection_node_count_stable_across_four_runs(run_idx: int) -> None:
    """Stress: 4× collect-only must return identical item counts (no import flake)."""
    global _COLLECT_BASELINE
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/ci/test_parallel_hook_execution.py",
        "tests/ci/test_parallel_hook_execution_adversarial.py",
        "--collect-only",
        "-q",
    ]
    result = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match is not None, result.stdout
    count = int(match.group(1))
    if run_idx == 0:
        _COLLECT_BASELINE = count
    else:
        assert _COLLECT_BASELINE is not None
        assert count == _COLLECT_BASELINE
