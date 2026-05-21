"""Behavioral contract tests for sync-api-types.sh (M902-24).

Spec: project_board/specs/902_24_openapi_typescript_gen_spec.md
Requirement 07 scenarios T1–T4, T6; executable exit codes and cache semantics only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
            "/api/registry/model": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"},
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


def _write_cache(path: Path, payload: dict[str, Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")


class _OpenApiHandler(BaseHTTPRequestHandler):
    body: bytes = b"{}"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/openapi.json":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.body)


@pytest.fixture()
def openapi_http_server() -> str:
    payload = json.dumps(_minimal_openapi()).encode("utf-8")
    _OpenApiHandler.body = payload
    server = HTTPServer(("127.0.0.1", 0), _OpenApiHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/openapi.json"
    finally:
        server.shutdown()
        thread.join(timeout=5)


class TestSyncApiTypesScriptContract:
    """Requirement 02 / 07: sync-api-types.sh exit codes and cache behavior."""

    def test_script_exists_and_is_executable(self, sync_script: Path) -> None:
        assert sync_script.is_file(), f"missing sync script at {sync_script}"
        assert os.access(sync_script, os.X_OK), f"sync script not executable: {sync_script}"

    def test_t1_valid_cache_skip_fetch_exits_0_and_writes_types(
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
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert output.is_file() and output.stat().st_size > 0
        text = output.read_text(encoding="utf-8")
        assert "paths" in text
        assert '"/api/health"' in text

    def test_t1_cache_fallback_stderr_when_fetch_fails(
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
            extra_env={"BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json"},
        )

        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "using cached OpenAPI" in proc.stderr
        assert output.is_file()

    def test_t2_no_cache_fetch_fails_exits_3(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "missing-cache.json"
        output = tmp_path / "api.types.ts"

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_OPENAPI_URL": "http://127.0.0.1:1/openapi.json"},
        )

        assert proc.returncode == 3, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "fetch failed" in proc.stderr
        assert "no cache" in proc.stderr
        assert not output.exists()

    def test_t3_live_fetch_updates_cache_and_exits_0(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
        openapi_http_server: str,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_OPENAPI_URL": openapi_http_server},
        )

        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert cache.is_file()
        cached = json.loads(cache.read_text(encoding="utf-8"))
        assert cached.get("openapi", "").startswith("3.")
        assert output.is_file()

    def test_t4_invalid_cache_exits_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, "{not-valid-json")

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

    def test_t4_openapi_2_cache_exits_4(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        cache = tmp_path / "openapi.cached.json"
        output = tmp_path / "api.types.ts"
        _write_cache(cache, {"openapi": "2.0", "info": {"title": "x", "version": "1"}, "paths": {}})

        proc = _run_sync(
            frontend_root=frontend_root,
            sync_script=sync_script,
            cache_path=cache,
            output_path=output,
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )

        assert proc.returncode == 4, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        assert "invalid cache" in proc.stderr

    def test_t6_generated_paths_include_health_and_registry_smoke_keys(
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
            extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
        )
        assert proc.returncode == 0, proc.stderr

        text = output.read_text(encoding="utf-8")
        assert '"/api/health"' in text
        assert '"/api/registry/model"' in text

    def test_t5_tsc_no_emit_passes_after_generation(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        """Requirement 07 T5: generated types compile under project tsconfig."""
        cache = tmp_path / "openapi.cached.json"
        output = frontend_root / "src" / "api.types.ts"
        prior_types = output.read_text(encoding="utf-8") if output.exists() else None
        _write_cache(cache, _minimal_openapi())

        try:
            proc = _run_sync(
                frontend_root=frontend_root,
                sync_script=sync_script,
                cache_path=cache,
                output_path=output,
                extra_env={"BLOBERT_SYNC_SKIP_FETCH": "1"},
            )
            assert proc.returncode == 0, proc.stderr
            assert output.is_file()

            health_module = frontend_root / "src" / "api" / "healthCheck.ts"
            assert health_module.is_file(), "healthCheck.ts required for tsc contract (Req 05)"

            tsc = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=str(frontend_root),
                capture_output=True,
                text=True,
                timeout=180,
            )
            assert tsc.returncode == 0, f"tsc stdout:\n{tsc.stdout}\ntsc stderr:\n{tsc.stderr}"
        finally:
            if prior_types is None:
                output.unlink(missing_ok=True)
            else:
                output.write_text(prior_types, encoding="utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="curl PATH isolation is Unix-oriented")
class TestSyncApiTypesEnvironmentPrechecks:
    def test_exit_2_when_curl_missing(
        self,
        frontend_root: Path,
        sync_script: Path,
        tmp_path: Path,
    ) -> None:
        if not sync_script.is_file():
            pytest.skip("sync script not implemented yet")
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
                "PATH": "/usr/bin:/bin",
            },
        )
        if (proc.returncode, "curl" in proc.stderr) == (0, False):
            pytest.skip("curl still resolved on PATH; environment isolation inconclusive")
        assert proc.returncode == 2
        assert "curl" in proc.stderr.lower()
