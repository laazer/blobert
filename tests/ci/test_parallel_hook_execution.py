"""Behavioral CI contract tests for M902-28 parallel Lefthook hook scheduling.

Validates executable scheduling and artifact-isolation contracts from
``project_board/specs/902_28_parallel_hook_execution_spec.md`` (Requirement 10).
Does not assert ticket/spec markdown prose.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LEFTHOOK_YML = REPO_ROOT / "lefthook.yml"
GODOT_HOOK_SCRIPT = REPO_ROOT / ".lefthook" / "scripts" / "godot-tests.sh"
PY_HOOK_SCRIPT = REPO_ROOT / ".lefthook" / "scripts" / "py-tests.sh"
RUN_TESTS_SH = REPO_ROOT / "ci" / "scripts" / "run_tests.sh"
VERIFY_TSGR_SH = REPO_ROOT / "ci" / "scripts" / "verify_tsgr_runner_contract.sh"

GODOT_GLOB = "**/*.{gd,tscn,tres,gdshader}"
PYTHON_GLOB = "asset_generation/python/**/*.py"
GODOT_RUN = "task hooks:godot"
PYTHON_RUN = "task hooks:python"

# Write-like shell patterns under asset_generation/python (Godot hook must avoid).
_GODOT_FORBIDDEN_WRITE_PATTERNS = (
    re.compile(r">\s*['\"]?.*asset_generation/python"),
    re.compile(r"asset_generation/python/coverage\.xml"),
    re.compile(r"\bcoverage\.xml\b.*asset_generation/python"),
)


def _load_lefthook_config() -> dict:
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed; cannot parse lefthook.yml")
    data = yaml.safe_load(LEFTHOOK_YML.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "lefthook.yml must parse to a mapping"
    return data


def _normalize_run(value: object) -> str:
    assert isinstance(value, str), "command run must be a string"
    return " ".join(value.split())


@pytest.fixture()
def lefthook_config() -> dict:
    assert LEFTHOOK_YML.is_file(), f"missing {LEFTHOOK_YML}"
    return _load_lefthook_config()


@pytest.fixture()
def pre_push(lefthook_config: dict) -> dict:
    block = lefthook_config.get("pre-push")
    assert isinstance(block, dict), "pre-push must be a mapping"
    return block


@pytest.fixture()
def pre_commit(lefthook_config: dict) -> dict:
    block = lefthook_config.get("pre-commit")
    assert isinstance(block, dict), "pre-commit must be a mapping"
    return block


@pytest.fixture()
def pre_push_commands(pre_push: dict) -> dict:
    commands = pre_push.get("commands")
    assert isinstance(commands, dict), "pre-push.commands must be a mapping"
    return commands


# ---------------------------------------------------------------------------
# T1–T3: Lefthook parallel scheduling contract (Requirement 03, AC-03.x)
# ---------------------------------------------------------------------------


class TestLefthookParallelSchedulingContract:
    """T1–T3: YAML parallel flags, delegation, and globs."""

    def test_t1_pre_push_parallel_is_true(self, pre_push: dict) -> None:
        """T1: post-implementation pre-push.parallel must be true (AC-03.1)."""
        assert pre_push.get("parallel") is True

    def test_t2_pre_commit_parallel_is_true(self, pre_commit: dict) -> None:
        """T2: pre-commit.parallel remains true (AC-03.1, AC-06.3)."""
        assert pre_commit.get("parallel") is True

    def test_t3_godot_tests_delegates_to_task_hooks_godot(self, pre_push_commands: dict) -> None:
        """T3a: godot-tests.run delegates via Taskfile (AC-03.2)."""
        cmd = pre_push_commands.get("godot-tests")
        assert isinstance(cmd, dict), "godot-tests command must exist"
        assert _normalize_run(cmd.get("run")) == GODOT_RUN

    def test_t3_py_tests_delegates_to_task_hooks_python(self, pre_push_commands: dict) -> None:
        """T3b: py-tests.run delegates via Taskfile (AC-03.2)."""
        cmd = pre_push_commands.get("py-tests")
        assert isinstance(cmd, dict), "py-tests command must exist"
        assert _normalize_run(cmd.get("run")) == PYTHON_RUN

    def test_t3_pre_push_globs_match_contract(self, pre_push_commands: dict) -> None:
        """T3c: pre-push globs unchanged (AC-03.3)."""
        godot = pre_push_commands["godot-tests"]
        py_tests = pre_push_commands["py-tests"]
        assert godot.get("glob") == GODOT_GLOB
        assert py_tests.get("glob") == PYTHON_GLOB


# ---------------------------------------------------------------------------
# T4–T5: Hook script artifact isolation (Requirement 01, AC-01.3)
# ---------------------------------------------------------------------------


class TestHookScriptArtifactIsolation:
    """T4–T5: disjoint write paths for Godot vs Python pre-push hooks."""

    def test_t4_godot_hook_script_does_not_write_under_asset_generation_python(
        self,
    ) -> None:
        """T4: godot-tests.sh must not write under asset_generation/python/."""
        assert GODOT_HOOK_SCRIPT.is_file(), f"missing {GODOT_HOOK_SCRIPT}"
        text = GODOT_HOOK_SCRIPT.read_text(encoding="utf-8")
        assert "asset_generation/python" not in text, (
            "godot-tests.sh must not reference asset_generation/python write paths"
        )
        for pattern in _GODOT_FORBIDDEN_WRITE_PATTERNS:
            assert not pattern.search(text), (
                f"godot-tests.sh matches forbidden write pattern: {pattern.pattern}"
            )

    def test_t5_py_hook_coverage_xml_under_py_root_only(self) -> None:
        """T5: py-tests.sh keeps coverage.xml under PY_ROOT (AC-01.3)."""
        assert PY_HOOK_SCRIPT.is_file(), f"missing {PY_HOOK_SCRIPT}"
        text = PY_HOOK_SCRIPT.read_text(encoding="utf-8")
        assert 'PY_ROOT="$ROOT/asset_generation/python"' in text
        assert "$PY_ROOT/coverage.xml" in text or 'cov_xml="$PY_ROOT/coverage.xml"' in text
        # coverage.xml must be anchored to PY_ROOT, not repo-root ad hoc paths.
        assert re.search(r'coverage\.xml', text) is not None
        assert "asset_generation/python" in text
        bare_root_cov = re.search(
            r'(?<!PY_ROOT/)(?<!PY_ROOT)(?<!\$)coverage\.xml',
            text,
        )
        if bare_root_cov:
            # Allow only when part of PY_ROOT/coverage.xml binding.
            for match in re.finditer(r"coverage\.xml", text):
                start = max(0, match.start() - 40)
                window = text[start : match.end() + 10]
                assert "PY_ROOT" in window, (
                    f"coverage.xml reference must be under PY_ROOT: {window!r}"
                )


# ---------------------------------------------------------------------------
# T6: CI canonical suite + TSGR contract path (Requirement 07)
# ---------------------------------------------------------------------------


class TestCICanonicalSuiteAndTsgrContract:
    """T6: TSGR verifier exists; run_tests.sh stays Godot-then-Python sequential."""

    def test_t6_verify_tsgr_runner_contract_script_exists(self) -> None:
        """T6a: verify_tsgr_runner_contract.sh is present (AC-07.2)."""
        assert VERIFY_TSGR_SH.is_file(), f"missing {VERIFY_TSGR_SH}"
        assert VERIFY_TSGR_SH.stat().st_mode & 0o111, "TSGR contract script should be executable"

    def test_t6_run_tests_sh_sequences_godot_before_python(self) -> None:
        """T6b: canonical CI runs Godot import/tests before py-tests.sh (AC-07.1)."""
        assert RUN_TESTS_SH.is_file(), f"missing {RUN_TESTS_SH}"
        text = RUN_TESTS_SH.read_text(encoding="utf-8")
        godot_import = text.find("godot --headless --import")
        godot_tests = text.find("godot --headless -s tests/run_tests.gd")
        py_hook = text.find(".lefthook/scripts/py-tests.sh")
        assert godot_import >= 0, "run_tests.sh must run bounded Godot import"
        assert godot_tests >= 0, "run_tests.sh must run Godot test runner"
        assert py_hook >= 0, "run_tests.sh must delegate Python suite to py-tests.sh"
        assert godot_import < py_hook
        assert godot_tests < py_hook
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            # Background job operator (&), not logical && in shell tests.
            if re.search(r"(?<![&])&(?![&])", stripped):
                pytest.fail(
                    f"run_tests.sh must not background suites: {stripped!r}"
                )

    def test_t6_verify_tsgr_contract_exits_zero_from_repo_root(self) -> None:
        """T6c: TSGR static contract script passes on current tree (AC-07.2)."""
        if not VERIFY_TSGR_SH.is_file():
            pytest.skip("verify_tsgr_runner_contract.sh missing")
        proc = subprocess.run(
            ["bash", str(VERIFY_TSGR_SH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, (
            "verify_tsgr_runner_contract.sh failed\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


# ---------------------------------------------------------------------------
# Guard: no markdown prose as expected output (workflow test realism)
# ---------------------------------------------------------------------------


class TestNoMarkdownProseContract:
    """Ensure tests never read project_board markdown as golden output."""

    def test_module_does_not_open_project_board_markdown(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        assert "project_board/" not in source or "read_text" not in source.split(
            "project_board/"
        )[0], (
            "tests must not load project_board markdown bodies as assertions"
        )
        assert ".md" not in re.findall(
            r'read_text\([^)]*["\'][^"\']*\.md',
            source,
        ), "no read_text on .md paths in this module"
