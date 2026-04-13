"""Coverage for server._request, _run_query_params, tools, and __main__."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

import blobert_asset_pipeline_mcp.server as server


@pytest.mark.asyncio
async def test_request_success_returns_formatted_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class _OkClient:
        async def request(self, *_a: Any, **_k: Any) -> httpx.Response:
            return httpx.Response(200, json={"ok": True})

        async def __aenter__(self) -> _OkClient:
            return self

        async def __aexit__(self, *_a: Any) -> None:
            return None

    @asynccontextmanager
    async def _fake_client(**_kw: Any) -> AsyncIterator[_OkClient]:
        yield _OkClient()

    monkeypatch.setattr(server, "http_client", _fake_client)
    out = await server._request("GET", "/api/health")
    assert out["status_code"] == 200
    assert out["data"] == {"ok": True}


@pytest.mark.asyncio
async def test_request_maps_httpx_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BadClient:
        async def request(self, *_a: Any, **_k: Any) -> httpx.Response:
            raise httpx.RequestError("simulated", request=httpx.Request("GET", "http://127.0.0.1:8000/x"))

        async def __aenter__(self) -> _BadClient:
            return self

        async def __aexit__(self, *_a: Any) -> None:
            return None

    @asynccontextmanager
    async def _fake_client(**_kw: Any) -> AsyncIterator[_BadClient]:
        yield _BadClient()

    monkeypatch.setattr(server, "http_client", _fake_client)
    out = await server._request("GET", "/api/health")
    assert out["status_code"] is None
    assert out["data"] is None
    assert "simulated" in out["error"]


def test_run_query_params_includes_all_optionals() -> None:
    p = server._run_query_params(
        cmd="animated",
        enemy="spider",
        count=2,
        description="d",
        difficulty="easy",
        finish="matte",
        hex_color="#fff",
        build_options=' {"k":1} ',
        output_draft=True,
        max_wait_ms=5000,
    )
    assert p["cmd"] == "animated"
    assert p["enemy"] == "spider"
    assert p["count"] == 2
    assert p["description"] == "d"
    assert p["difficulty"] == "easy"
    assert p["finish"] == "matte"
    assert p["hex_color"] == "#fff"
    assert p["build_options"] == '{"k":1}'
    assert p["output_draft"] is True
    assert p["max_wait_ms"] == 5000


def test_run_query_params_omits_blank_build_options() -> None:
    p = server._run_query_params(
        cmd="stats",
        enemy=None,
        count=None,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options="   ",
        output_draft=False,
        max_wait_ms=None,
    )
    assert "build_options" not in p
    assert "max_wait_ms" not in p


@pytest.mark.asyncio
async def test_run_complete_uses_read_timeout_from_max_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _spy(
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        read_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        captured["read_timeout_seconds"] = read_timeout_seconds
        captured["params"] = params
        return {"status_code": 200, "data": {}}

    monkeypatch.setattr(server, "_request", _spy)
    await server.blobert_asset_pipeline_run_complete("stats", max_wait_ms=10_000)
    assert captured["params"] is not None
    assert captured["params"]["max_wait_ms"] == 10_000
    # max(wait_s + 120, 300) — 10s wait still below 300s floor
    assert captured["read_timeout_seconds"] == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_all_tools_call_request(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_req = AsyncMock(return_value={"status_code": 200, "data": {}})
    monkeypatch.setattr(server, "_request", mock_req)

    await server.blobert_asset_pipeline_health()
    await server.blobert_asset_pipeline_run_complete("stats")
    await server.blobert_asset_pipeline_run_status()
    await server.blobert_asset_pipeline_run_kill()
    await server.blobert_asset_pipeline_registry_get()
    await server.blobert_asset_pipeline_registry_patch_enemy_version("spider", "v1", {"x": 1})
    await server.blobert_asset_pipeline_registry_patch_player_active({"y": 2})
    await server.blobert_asset_pipeline_registry_load_existing_candidates()
    await server.blobert_asset_pipeline_registry_load_existing_open({"kind": "enemy"})
    await server.blobert_asset_pipeline_registry_put_enemy_slots("spider", {"slots": []})
    await server.blobert_asset_pipeline_registry_put_player_slots({"slots": []})
    await server.blobert_asset_pipeline_registry_sync_animated_exports("spider")
    await server.blobert_asset_pipeline_registry_sync_player_exports()
    await server.blobert_asset_pipeline_registry_spawn_eligible("spider")
    await server.blobert_asset_pipeline_registry_delete_enemy_version("spider", "v1", {"confirm": True})
    await server.blobert_asset_pipeline_registry_delete_player_active({"confirm": True})
    await server.blobert_asset_pipeline_files_list()
    await server.blobert_asset_pipeline_files_read("enemies/x.py")
    await server.blobert_asset_pipeline_files_write("enemies/x.py", "print(1)")
    await server.blobert_asset_pipeline_assets_list()
    await server.blobert_asset_pipeline_assets_get("draft/foo.glb")
    await server.blobert_asset_pipeline_meta_enemies()

    assert mock_req.await_count == 22


def test_server_main_runs_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[bool] = []
    monkeypatch.setattr(server.mcp, "run", lambda: called.append(True))
    server.main()
    assert called == [True]


def test___main___executes_when_run_as_script(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    called: list[bool] = []
    monkeypatch.setattr(server, "main", lambda: called.append(True))
    main_py = Path(__file__).resolve().parents[2] / "src/blobert_asset_pipeline_mcp/__main__.py"
    runpy.run_path(str(main_py), run_name="__main__")
    assert called == [True]
