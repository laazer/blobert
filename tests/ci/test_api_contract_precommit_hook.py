"""Behavioral contract tests for api-contract-check pre-commit hook (M902-27).

Spec: project_board/specs/902_27_api_contract_precommit_spec.md
Scenarios H1–H8: hook exit codes, stderr banners, cache fallback warning,
lefthook.yml registration. Mocks npx/uv via PATH stubs; Step 1 uses
sync-api-types.sh with BLOBERT_SYNC_SKIP_FETCH or cache fixtures (no live :8000).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

_SPEC_PATH = "project_board/specs/902_27_api_contract_precommit_spec.md"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEFTHOOK_YML = _REPO_ROOT / "lefthook.yml"
_HOOK_SCRIPT = _REPO_ROOT / ".lefthook/scripts/api-contract-check.sh"
_SYNC_SCRIPT = _REPO_ROOT / "asset_generation/web/frontend/scripts/sync-api-types.sh"
_FRONTEND_ROOT = _REPO_ROOT / "asset_generation/web/frontend"
_PYTHON_ROOT = _REPO_ROOT / "asset_generation/python"

_CMD_ID = "api-contract-check"
_BACKEND_GLOB = "asset_generation/web/backend/**/*.py"
_RUN_LINE = "bash .lefthook/scripts/api-contract-check.sh"
_STAGE_COMMIT = "commit"

_OPENING_BANNER = "Running API contract check..."
_STEP1_START = "[1/3] Regenerating TypeScript types from OpenAPI spec..."
_STEP1_SUCCESS = "  ✓ Generated: asset_generation/web/frontend/src/api.types.ts"
_STEP1_FAIL_PREFIX = "  ✗ ERROR: OpenAPI type sync failed (exit"
_STEP2_START = "[2/3] Type-checking frontend..."
_STEP2_FAIL = "  ✗ ERROR: TypeScript check failed"
_STEP3_START = "[3/3] Running contract tests..."
_STEP3_SUCCESS_PREFIX = "  ✓ All contract tests passed"
_STEP3_FAIL = "  ✗ ERROR: Contract tests failed"
_STEP3_HINT = (
    "Hint: Run `cd asset_generation/python && uv run pytest "
    "tests/api/test_*_contract.py -v` to debug"
)
_SUCCESS_FOOTER = "✅ API contract check passed"
_BLOCKED_SYNC = "❌ Commit blocked: OpenAPI type sync failed. Fix and retry."
_BLOCKED_TSC = "❌ Commit blocked: Type errors found. Fix and retry."
_BLOCKED_PYTEST = "❌ Commit blocked: Contract tests failed. Fix and retry."
_CACHE_WARNING = "Backend not reachable; using cached OpenAPI spec"
_FORBIDDEN_START = ("uvicorn", "task editor", "start.sh")


def load_lefthook_config(path: Path | None = None) -> dict[str, Any]:
    target = path or _LEFTHOOK_YML
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"lefthook config root must be mapping, got {type(data)!r}")
    return data


def pre_commit_command(cfg: dict[str, Any], command_id: str) -> dict[str, Any]:
    block = cfg.get("pre-commit")
    if not isinstance(block, dict):
        return {}
    commands = block.get("commands")
    if not isinstance(commands, dict):
        return {}
    entry = commands.get(command_id)
    return entry if isinstance(entry, dict) else {}


def _minimal_openapi() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Blobert Asset Editor API", "version": "0.1.0"},
        "paths": {
            "/api/health": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"status": {"type": "string"}},
                                        "required": ["status"],
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
    }


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _stub_toolchain_bin(tmp_path: Path, *, tsc_exit: int = 0, pytest_exit: int = 0) -> Path:
    """PATH stubs for npx tsc and uv run pytest (spec Req 06 — no live backend)."""
    bindir = tmp_path / "stub-bin"
    bindir.mkdir()
    npx_lines = [
        "#!/usr/bin/env bash",
        'if [[ "$1" == "tsc" && "$2" == "--noEmit" ]]; then',
    ]
    if tsc_exit != 0:
        npx_lines.append(
            '  echo "src/api.ts(42,5): error TS2339: Property \'new_field\' does not exist." >&2'
        )
    npx_lines.append(f"  exit {tsc_exit}")
    npx_lines.append("fi")
    npx_lines.append("exit 127")
    _write_executable(bindir / "npx", "\n".join(npx_lines) + "\n")
    uv_lines = [
        "#!/usr/bin/env bash",
        'if [[ "$1" == "run" && "$2" == "pytest" ]]; then',
    ]
    if pytest_exit != 0:
        uv_lines.append('  echo "FAILED tests/api/test_health_contract.py::test_shape" >&2')
        uv_lines.append(f"  exit {pytest_exit}")
    else:
        uv_lines.append(
            '  echo "======================== 12 passed in 0.01s ========================"'
        )
        uv_lines.append("  exit 0")
    uv_lines.append("fi")
    uv_lines.append('if [[ "$1" == "--version" ]]; then')
    uv_lines.append('  echo "uv-stub"')
    uv_lines.append("  exit 0")
    uv_lines.append("fi")
    uv_lines.append("exit 127")
    _write_executable(bindir / "uv", "\n".join(uv_lines) + "\n")
    return bindir


def _require_hook_script() -> Path:
    assert _HOOK_SCRIPT.is_file(), f"Hook script missing (implementation pending): {_HOOK_SCRIPT}"
    assert os.access(_HOOK_SCRIPT, os.X_OK), f"Hook script not executable: {_HOOK_SCRIPT}"
    return _HOOK_SCRIPT


def _run_hook(
    *,
    extra_env: dict[str, str] | None = None,
    stub_bin: Path | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    script = _require_hook_script()
    env = {**os.environ}
    if extra_env:
        env.update(extra_env)
    if stub_bin is not None:
        env["PATH"] = f"{stub_bin}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(script)],
        cwd=str(_REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _sync_env_for_skip_fetch(tmp_path: Path) -> dict[str, str]:
    cache = tmp_path / "openapi.cached.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(_minimal_openapi()), encoding="utf-8")
    output = tmp_path / "api.types.ts"
    return {
        "BLOBERT_SYNC_SKIP_FETCH": "1",
        "BLOBERT_OPENAPI_CACHE": str(cache),
        "BLOBERT_OPENAPI_OUTPUT": str(output),
    }


@pytest.fixture()
def lefthook_cfg() -> dict[str, Any]:
    return load_lefthook_config()


@pytest.fixture()
def frontend_has_node_modules() -> None:
    node_modules = _FRONTEND_ROOT / "node_modules"
    if not node_modules.is_dir():
        pytest.skip("frontend node_modules missing; run npm ci in asset_generation/web/frontend")


class TestRequirement01LefthookRegistration:
    """Req 01 / H6: api-contract-check frozen in lefthook.yml."""

    def test_h6_command_id_present(self, lefthook_cfg: dict[str, Any]) -> None:
        entry = pre_commit_command(lefthook_cfg, _CMD_ID)
        assert entry, f"pre-commit.commands must define {_CMD_ID!r}"

    def test_h6_glob_matches_backend_py_tree(self, lefthook_cfg: dict[str, Any]) -> None:
        entry = pre_commit_command(lefthook_cfg, _CMD_ID)
        assert entry.get("glob") == _BACKEND_GLOB

    def test_h6_run_invokes_hook_script(self, lefthook_cfg: dict[str, Any]) -> None:
        entry = pre_commit_command(lefthook_cfg, _CMD_ID)
        assert entry.get("run") == _RUN_LINE

    def test_h6_stage_commit_for_generated_types(self, lefthook_cfg: dict[str, Any]) -> None:
        entry = pre_commit_command(lefthook_cfg, _CMD_ID)
        assert entry.get("stage") == _STAGE_COMMIT


class TestRequirement04ParallelSafety:
    """Req 04 / AC-04.1: pre-commit stays parallel; no serial override."""

    def test_pre_commit_parallel_still_true(self, lefthook_cfg: dict[str, Any]) -> None:
        block = lefthook_cfg.get("pre-commit")
        assert isinstance(block, dict)
        assert block.get("parallel") is True


class TestRequirement02HookScriptStructure:
    """Req 02 / AC-02.1, H7: script shell options and no backend auto-start."""

    def test_hook_script_exists_with_strict_mode(self) -> None:
        assert _HOOK_SCRIPT.is_file(), f"Missing {_HOOK_SCRIPT}"
        text = _HOOK_SCRIPT.read_text(encoding="utf-8")
        assert "set -euo pipefail" in text

    def test_h7_script_forbids_backend_auto_start(self) -> None:
        assert _HOOK_SCRIPT.is_file(), f"Missing {_HOOK_SCRIPT}"
        text = _HOOK_SCRIPT.read_text(encoding="utf-8")
        for token in _FORBIDDEN_START:
            assert token not in text, f"Hook must not invoke {token!r}"


class TestRequirement03HookPipelineBehavior:
    """Req 02–03 / H1–H5, H8: exit codes and frozen stderr templates."""

    def test_h1_all_steps_success_exit_zero(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        stub_bin = _stub_toolchain_bin(tmp_path, tsc_exit=0, pytest_exit=0)
        proc = _run_hook(
            extra_env=_sync_env_for_skip_fetch(tmp_path),
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _OPENING_BANNER in combined
        assert _STEP1_START in combined
        assert _STEP2_START in combined
        assert _STEP3_START in combined
        assert _STEP1_SUCCESS in combined
        assert _STEP3_SUCCESS_PREFIX in combined
        assert _SUCCESS_FOOTER in combined

    def test_h2_sync_failure_exit_one_and_step_one_template(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        stub_bin = _stub_toolchain_bin(tmp_path)
        missing_cache = tmp_path / "no-cache.json"
        proc = _run_hook(
            extra_env={
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
                "BLOBERT_OPENAPI_CACHE": str(missing_cache),
                "BLOBERT_OPENAPI_OUTPUT": str(tmp_path / "out.ts"),
            },
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _STEP1_FAIL_PREFIX in combined
        assert _BLOCKED_SYNC in combined
        assert _STEP2_START not in combined

    def test_h3_tsc_failure_exit_one_type_mismatch_banner(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        stub_bin = _stub_toolchain_bin(tmp_path, tsc_exit=1, pytest_exit=0)
        proc = _run_hook(
            extra_env=_sync_env_for_skip_fetch(tmp_path),
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _STEP2_FAIL in combined
        assert "Property 'new_field'" in combined
        assert _BLOCKED_TSC in combined
        assert _STEP3_START not in combined

    def test_h4_pytest_failure_exit_one_hint_line(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        stub_bin = _stub_toolchain_bin(tmp_path, tsc_exit=0, pytest_exit=1)
        proc = _run_hook(
            extra_env=_sync_env_for_skip_fetch(tmp_path),
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _STEP3_FAIL in combined
        assert _STEP3_HINT in combined
        assert _BLOCKED_PYTEST in combined

    def test_h5_cache_fallback_warning_line_on_success(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        if not _SYNC_SCRIPT.is_file():
            pytest.fail(f"Missing sync script: {_SYNC_SCRIPT}")
        cache = tmp_path / "openapi.cached.json"
        cache.write_text(json.dumps(_minimal_openapi()), encoding="utf-8")
        output = tmp_path / "api.types.ts"
        stub_bin = _stub_toolchain_bin(tmp_path)
        proc = _run_hook(
            extra_env={
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
                "BLOBERT_OPENAPI_CACHE": str(cache),
                "BLOBERT_OPENAPI_OUTPUT": str(output),
            },
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "using cached OpenAPI spec" in combined
        assert _CACHE_WARNING in combined
        assert combined.index(_CACHE_WARNING) < combined.index(_STEP2_START)

    def test_h8_skip_fetch_deterministic_step_one(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        stub_bin = _stub_toolchain_bin(tmp_path)
        proc = _run_hook(
            extra_env={
                **_sync_env_for_skip_fetch(tmp_path),
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
            },
            stub_bin=stub_bin,
        )
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _CACHE_WARNING not in (proc.stdout + proc.stderr)

