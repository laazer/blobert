"""Adversarial tests for sync-api-types.sh (M902-24).

Spec: project_board/specs/902_24_openapi_typescript_gen_spec.md (Req 02, Failure Taxonomy).
Exposes exit 5 generation failures, empty/whitespace cache, read-only output dirs,
BLOBERT_SYNC_SKIP_FETCH strictness, and concurrent output writes.

Traceability: M902-24 execution plan Task 3; complements
tests/web_frontend/test_sync_api_types_script.py.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

_SPEC_PATH = "project_board/specs/902_24_openapi_typescript_gen_spec.md"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_ROOT = _REPO_ROOT / "asset_generation" / "web" / "frontend"
_SCRIPT = _FRONTEND_ROOT / "scripts" / "sync-api-types.sh"


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
            },
        },
    }


@pytest.fixture()
def frontend_root() -> Path:
    assert (_FRONTEND_ROOT / "package.json").is_file()
    return _FRONTEND_ROOT


@pytest.fixture()
def sync_script() -> Path:
    return _SCRIPT


def _run_sync(
    *,
    frontend_root: Path,
    sync_script: Path,
    cache_path: Path,
    output_path: Path,
    extra_env: dict[str, str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "BLOBERT_OPENAPI_CACHE": str(cache_path),
        "BLOBERT_OPENAPI_OUTPUT": str(output_path),
    }
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(sync_script)],
        cwd=str(frontend_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _write_cache(path: Path, payload: dict[str, Any] | str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    elif isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")


def _fake_npx_bindir(tmp_path: Path) -> Path:
    """Prepends a shim that fails only for openapi-typescript invocations (exit 5 path)."""
    bindir = tmp_path / "fake_bin"
    bindir.mkdir()
    npx = bindir / "npx"
    npx.write_text(
        """#!/bin/sh
for arg in "$@"; do
  case "$arg" in
    *openapi-typescript*) echo "generation failed (adversarial mock)" >&2; exit 1 ;;
  esac
done
exec "$(command -v npx)" "$@"
""",
        encoding="utf-8",
    )
    npx.chmod(0o755)
    return bindir


class TestGenerationFailureExit5:
    """Failure Taxonomy exit 5: openapi-typescript or non-empty output failure."""

    def test_exit_5_when_openapi_typescript_fails(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, _minimal_openapi())
        bindir = _fake_npx_bindir(tmp_path)

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={
                "BLOBERT_SYNC_SKIP_FETCH": "1",
                "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
            },
        )

        assert proc.returncode == 5, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "generation failed" in proc.stderr.lower()
        assert not output.exists() or output.stat().st_size == 0

    def test_exit_5_when_output_parent_not_writable(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        if sys.platform == "win32":
            pytest.skip("read-only directory semantics are Unix-oriented")

        cache = tmp_path / "openapi.cached.json"
        out_dir = tmp_path / "readonly_out"
        out_dir.mkdir()
        output = out_dir / "api.types.ts"
        _write_cache(cache, _minimal_openapi())
        os.chmod(out_dir, stat.S_IREAD | stat.S_IEXEC)

        try:
            proc = _run_sync(
                frontend_root=frontend_root,
                sync_script=sync_script,
                cache_path=cache,
                output_path=output,
                extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
            )
        finally:
            os.chmod(out_dir, stat.S_IRWXU)

        assert proc.returncode == 5, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "generation failed" in proc.stderr.lower()

    def test_exit_5_when_existing_output_file_read_only(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        if sys.platform == "win32":
            pytest.skip("read-only file semantics are Unix-oriented")

        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, _minimal_openapi())
        output.write_text("// stale\n", encoding="utf-8")
        os.chmod(output, stat.S_IREAD)

        try:
            proc = _run_sync(
                frontend_root=frontend_root,
                sync_script=sync_script,
                cache_path=cache,
                output_path=output,
                extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
            )
        finally:
            os.chmod(output, stat.S_IRWXU)

        assert proc.returncode == 5, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "generation failed" in proc.stderr.lower()


class TestEmptyCacheAdversarial:
    """Null/empty/corrupt cache bodies before generation (exit 4, not silent success)."""

    def test_zero_byte_cache_file_exits_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(b"")

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 4, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "invalid cache" in proc.stderr
        assert not output.exists()

    def test_empty_json_object_cache_exits_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, {})

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 4, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "invalid cache" in proc.stderr

    def test_whitespace_only_cache_exits_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, "   \n\t  ")

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 4, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "invalid cache" in proc.stderr


class TestBlobertSyncSkipFetchEdgeCases:
    """BLOBERT_SYNC_SKIP_FETCH must be strict; cache-only path when set to 1."""

    def test_skip_fetch_without_cache_exits_3_not_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "missing.json"
        output = tmp_path / "api.types.ts"

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 3, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "no cache" in proc.stderr

    def test_skip_fetch_with_empty_cache_exits_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        cache.touch()

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 4, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "invalid cache" in proc.stderr

    def test_skip_fetch_one_does_not_attempt_live_fetch(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, _minimal_openapi())

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={
                "BLOBERT_SYNC_SKIP_FETCH": "1",
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
            },
        )

        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "fetch failed" not in proc.stderr.lower()
        assert "using cached OpenAPI" not in proc.stderr
        assert output.is_file() and output.stat().st_size > 0

    def test_skip_fetch_truthy_string_not_one_attempts_fetch_then_cache_fallback(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, _minimal_openapi())

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={
                "BLOBERT_SYNC_SKIP_FETCH": "true",
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
            },
        )

        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "using cached OpenAPI" in proc.stderr

    def test_skip_fetch_zero_attempts_fetch_without_cache_exits_3(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "missing.json"
        output = tmp_path / "api.types.ts"

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={
                "BLOBERT_SYNC_SKIP_FETCH": "0",
                "BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json",
            },
        )

        assert proc.returncode == 3, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "fetch failed" in proc.stderr


class TestConcurrentOutputWrites:
    """Concurrency: parallel runs must not leave corrupt partial api.types.ts."""

    def test_two_parallel_runs_same_output_both_succeed_with_identical_output(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, _minimal_openapi())
        results: list[subprocess.CompletedProcess[str]] = []
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                results.append(
                    _run_sync(
                        frontend_root=frontend_root,
                        sync_script=sync_script,
                        cache_path=cache,
                        output_path=output,
                        extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
                    )
                )
            except BaseException as exc:  # noqa: BLE001 — collect thread failures
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=120)

        assert not errors, f"thread errors: {errors}"
        assert len(results) == 2
        assert all(proc.returncode == 0 for proc in results), [
            (proc.returncode, proc.stderr) for proc in results
        ]
        assert output.is_file() and output.stat().st_size > 0
        text = output.read_text(encoding="utf-8")
        assert '"/api/health"' in text
        assert text.count("export") >= 1
