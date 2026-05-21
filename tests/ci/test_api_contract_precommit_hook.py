"""Behavioral contract tests for api-contract-check pre-commit hook (M902-27).

Spec: project_board/specs/902_27_api_contract_precommit_spec.md
Scenarios H1–H8: hook exit codes, stderr banners, cache fallback warning,
lefthook.yml registration. Adversarial class (execution plan Task 3): F1–F10
setup/sync failures, invalid cache, missing tooling, wrong cwd, determinism,
and step-order isolation. Mocks npx/uv via PATH stubs; Step 1 uses
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
_BLOCKED_SETUP = "❌ Commit blocked: Setup error. Fix and retry."
_CACHE_WARNING = "Backend not reachable; using cached OpenAPI spec"
_UV_SETUP_MSG = "api-contract-check: uv not found"
_NODE_MODULES_SETUP_MSG = "api-contract-check: run npm ci in asset_generation/web/frontend"
_SYNC_SCRIPT_REL = "asset_generation/web/frontend/scripts/sync-api-types.sh"
_FORBIDDEN_START = ("uvicorn", "task editor", "start.sh")
_FORBIDDEN_TYPEGEN = ("openapi-typescript",)


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


def _stub_toolchain_bin(
    tmp_path: Path,
    *,
    tsc_exit: int = 0,
    pytest_exit: int = 0,
    uv_marker: Path | None = None,
    include_uv: bool = True,
) -> Path:
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
    npx_lines.append('exec "$(command -v npx)" "$@"')
    _write_executable(bindir / "npx", "\n".join(npx_lines) + "\n")
    if include_uv:
        uv_lines = [
            "#!/usr/bin/env bash",
            'if [[ "$1" == "run" && "$2" == "pytest" ]]; then',
        ]
        if uv_marker is not None:
            uv_lines.append(f'  echo "invoked" >> "{uv_marker}"')
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


def _fake_npx_openapi_typescript_fail(tmp_path: Path) -> Path:
    """Prepends npx shim that fails openapi-typescript only (sync exit 5 / F4)."""
    bindir = tmp_path / "fake-npx-bin"
    bindir.mkdir()
    npx = bindir / "npx"
    npx.write_text(
        """#!/usr/bin/env bash
for arg in "$@"; do
  case "$arg" in
    *openapi-typescript*)
      echo "generation failed (adversarial mock)" >&2
      exit 1
      ;;
  esac
done
exec "$(command -v npx)" "$@"
""",
        encoding="utf-8",
    )
    npx.chmod(0o755)
    return bindir


def _path_without_command(command: str) -> str:
    """Drop PATH entries that expose a given executable (missing-tooling tests)."""
    kept: list[str] = []
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        candidate = Path(entry) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            continue
        kept.append(entry)
    return os.pathsep.join(kept)


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
        """AC-02.6: no backend start invocations; frozen Fix text may mention task editor."""
        assert _HOOK_SCRIPT.is_file(), f"Missing {_HOOK_SCRIPT}"
        text = _HOOK_SCRIPT.read_text(encoding="utf-8")
        assert "uvicorn" not in text
        assert "start.sh" not in text
        for line in text.splitlines():
            if "task editor" not in line:
                continue
            stripped = line.strip()
            assert stripped.startswith("echo "), (
                "task editor must appear only in user-facing echo text, not as a command: "
                f"{line!r}"
            )


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
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "using cached OpenAPI spec" in proc.stderr
        assert _CACHE_WARNING in proc.stderr
        assert _STEP2_START in proc.stdout
        script = _HOOK_SCRIPT.read_text(encoding="utf-8")
        warn_idx = script.index("Backend not reachable; using cached OpenAPI spec")
        step2_idx = script.index("[2/3] Type-checking frontend...")
        assert warn_idx < step2_idx, "hook must emit cache warning before Step 2 banner"

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


class TestApiContractPrecommitHookAdversarial:
    """M902-27 execution plan Task 3: adversarial F1–F10 and ordering traps."""

    def test_a1_empty_cache_file_fetch_fail_blocks_before_step_two(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """F2 OPENAPI_UNAVAILABLE: zero-byte cache + dead URL must not reach tsc."""
        cache = tmp_path / "empty.cache.json"
        cache.write_text("", encoding="utf-8")
        stub_bin = _stub_toolchain_bin(tmp_path)
        proc = _run_hook(
            extra_env={
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
                "BLOBERT_OPENAPI_CACHE": str(cache),
                "BLOBERT_OPENAPI_OUTPUT": str(tmp_path / "out.ts"),
            },
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _STEP1_FAIL_PREFIX in combined
        assert _BLOCKED_SYNC in combined
        assert _STEP2_START not in combined

    def test_a2_invalid_cache_skip_fetch_exit_one(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """F3/F4: corrupt cache with BLOBERT_SYNC_SKIP_FETCH must fail Step 1 (sync exit 4)."""
        cache = tmp_path / "bad.cache.json"
        cache.write_text("{not-valid-json", encoding="utf-8")
        stub_bin = _stub_toolchain_bin(tmp_path)
        proc = _run_hook(
            extra_env={
                "BLOBERT_SYNC_SKIP_FETCH": "1",
                "BLOBERT_OPENAPI_CACHE": str(cache),
                "BLOBERT_OPENAPI_OUTPUT": str(tmp_path / "out.ts"),
            },
            stub_bin=stub_bin,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _STEP1_FAIL_PREFIX in combined
        assert _STEP2_START not in combined

    def test_a3_missing_uv_setup_error_before_pipeline(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """F9 SETUP: hook must fail when uv is absent from PATH (no pytest stub reached)."""
        stub_bin = _stub_toolchain_bin(tmp_path, include_uv=False)
        uv_marker = tmp_path / "uv.marker"
        proc = _run_hook(
            extra_env={
                **_sync_env_for_skip_fetch(tmp_path),
                "PATH": f"{stub_bin}{os.pathsep}{_path_without_command('uv')}",
            },
            stub_bin=None,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _UV_SETUP_MSG in combined
        assert _BLOCKED_SETUP in combined
        assert _STEP1_START not in combined
        assert not uv_marker.exists()

    def test_a4_wrong_cwd_repo_root_resolution_still_succeeds(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """Order/cwd trap: hook invoked from frontend/ must still resolve repo ROOT."""
        stub_bin = _stub_toolchain_bin(tmp_path)
        script = _require_hook_script()
        env = {**os.environ, **_sync_env_for_skip_fetch(tmp_path)}
        env["PATH"] = f"{stub_bin}{os.pathsep}{env.get('PATH', '')}"
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(_FRONTEND_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _SUCCESS_FOOTER in combined

    def test_a5_three_consecutive_runs_identical_exit_and_footer(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """Determinism: three identical env runs must share exit code and success footer."""
        stub_bin = _stub_toolchain_bin(tmp_path)
        env = _sync_env_for_skip_fetch(tmp_path)
        codes: list[int] = []
        footers: list[bool] = []
        for _ in range(3):
            proc = _run_hook(extra_env=env, stub_bin=stub_bin)
            codes.append(proc.returncode)
            footers.append(_SUCCESS_FOOTER in proc.stdout + proc.stderr)
        assert codes == [0, 0, 0], codes
        assert footers == [True, True, True]

    def test_a6_hook_script_delegates_sync_not_raw_openapi_typescript(self) -> None:
        """A1 anti-pattern: hook must not invoke openapi-typescript directly (comments OK)."""
        assert _HOOK_SCRIPT.is_file(), f"Missing {_HOOK_SCRIPT}"
        text = _HOOK_SCRIPT.read_text(encoding="utf-8")
        assert _SYNC_SCRIPT.name in text
        assert str(_SYNC_SCRIPT_REL) in text or "sync-api-types.sh" in text
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for token in _FORBIDDEN_TYPEGEN:
                assert token not in line, (
                    f"Hook must delegate typegen to sync script, not {token!r} in: {line!r}"
                )

    def test_a7_step_three_uses_contract_test_glob(self) -> None:
        """A3: Step 3 must target tests/api/test_*_contract.py under asset_generation/python."""
        assert _HOOK_SCRIPT.is_file(), f"Missing {_HOOK_SCRIPT}"
        text = _HOOK_SCRIPT.read_text(encoding="utf-8")
        assert "tests/api/test_*_contract.py" in text
        assert "asset_generation/python" in text

    def test_a8_sync_typegen_failure_blocks_with_step_one_template(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """F4 TYPEGEN_FAILED: openapi-typescript failure surfaces as Step 1 hook failure."""
        cache = tmp_path / "openapi.cached.json"
        cache.write_text(json.dumps(_minimal_openapi()), encoding="utf-8")
        fake_npx = _fake_npx_openapi_typescript_fail(tmp_path)
        stub_bin = _stub_toolchain_bin(tmp_path)
        proc = _run_hook(
            extra_env={
                "BLOBERT_SYNC_SKIP_FETCH": "1",
                "BLOBERT_OPENAPI_CACHE": str(cache),
                "BLOBERT_OPENAPI_OUTPUT": str(tmp_path / "out.ts"),
                "PATH": f"{fake_npx}{os.pathsep}{stub_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            },
            stub_bin=None,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert _STEP1_FAIL_PREFIX in combined
        assert _STEP2_START not in combined

    def test_a9_sync_failure_does_not_invoke_pytest_stub(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """Step-order: Step 1 failure must not call uv run pytest (marker file stays empty)."""
        uv_marker = tmp_path / "uv.invoked"
        stub_bin = _stub_toolchain_bin(tmp_path, uv_marker=uv_marker)
        proc = _run_hook(
            extra_env={
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
                "BLOBERT_OPENAPI_CACHE": str(tmp_path / "missing.cache.json"),
                "BLOBERT_OPENAPI_OUTPUT": str(tmp_path / "out.ts"),
            },
            stub_bin=stub_bin,
        )
        assert proc.returncode == 1
        assert not uv_marker.exists()

    def test_a10_node_modules_prerequisite_documented_in_script(self) -> None:
        """F7 SETUP: script must check frontend node_modules before pipeline (grep contract)."""
        assert _HOOK_SCRIPT.is_file(), f"Missing {_HOOK_SCRIPT}"
        text = _HOOK_SCRIPT.read_text(encoding="utf-8")
        assert "node_modules" in text
        assert "npm ci" in text or _NODE_MODULES_SETUP_MSG in text

    def test_a11_backend_glob_includes_core_not_routers_only(
        self,
        lefthook_cfg: dict[str, Any],
    ) -> None:
        """R4: glob must cover core/ config, not ticket's narrower routers/** example."""
        entry = pre_commit_command(lefthook_cfg, _CMD_ID)
        glob_val = entry.get("glob", "")
        assert glob_val == _BACKEND_GLOB
        assert "core" in glob_val or "backend/**/*.py" in glob_val
        assert "routers/**/*.py" != glob_val

    def test_a12_h6_registration_yaml_byte_drift_guards(
        self,
        lefthook_cfg: dict[str, Any],
    ) -> None:
        """YAML drift: name/stage/run must stay frozen (mutation of any field breaks commit)."""
        entry = pre_commit_command(lefthook_cfg, _CMD_ID)
        assert entry.get("name"), "api-contract-check must have human-readable name"
        assert "API contract" in str(entry.get("name"))
        assert entry.get("stage") == _STAGE_COMMIT
        assert entry.get("run") == _RUN_LINE

    def test_a13_npx_stub_must_delegate_openapi_typescript_to_real_npx(
        self,
        tmp_path: Path,
        frontend_has_node_modules: None,
    ) -> None:
        """Mock trap: PATH stub that only handles tsc must not break sync Step 1 typegen."""
        stub_bin = _stub_toolchain_bin(tmp_path)
        proc = _run_hook(extra_env=_sync_env_for_skip_fetch(tmp_path), stub_bin=stub_bin)
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "openapi-typescript exited non-zero" not in combined

