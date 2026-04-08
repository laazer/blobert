"""
HTTP contract tests for ``/api/registry/*`` (FastAPI app under ``asset_generation/web/backend``).

Loads ``main.app`` via ``sys.path`` so ``uv run pytest`` from ``asset_generation/python`` covers MRVC editor API.
"""
# ruff: noqa: I001 — backend imports follow a deliberate ``sys.path`` bootstrap.

from __future__ import annotations

import json
import pathlib
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2].parent / "web" / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import core.config as config_module  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def python_root(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    root = tmp_path / "python"
    root.mkdir(parents=True)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_get_model_registry_returns_default_when_missing(client: AsyncClient):
    res = await client.get("/api/registry/model")
    assert res.status_code == 200
    data = res.json()
    assert data["schema_version"] == 1
    assert "spider" in data["enemies"]
    assert data["enemies"]["spider"]["versions"][0]["draft"] is False


@pytest.mark.asyncio
async def test_patch_enemy_promote_and_spawn_eligible(client: AsyncClient, python_root: pathlib.Path):
    r0 = await client.get("/api/registry/model/spawn_eligible/imp")
    assert r0.status_code == 200
    assert r0.json()["paths"]

    r1 = await client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={"draft": True, "in_use": False},
    )
    assert r1.status_code == 200
    body = r1.json()
    assert body["enemies"]["imp"]["versions"][0]["draft"] is True

    reg_file = python_root / "model_registry.json"
    assert reg_file.is_file()
    disk = json.loads(reg_file.read_text(encoding="utf-8"))
    assert disk["enemies"]["imp"]["versions"][0]["draft"] is True

    r2 = await client.get("/api/registry/model/spawn_eligible/imp")
    assert r2.status_code == 200
    assert r2.json()["paths"] == []

    r3 = await client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={"draft": False, "in_use": True},
    )
    assert r3.status_code == 200
    r4 = await client.get("/api/registry/model/spawn_eligible/imp")
    assert r4.json()["paths"]


@pytest.mark.asyncio
async def test_patch_unknown_version_404(client: AsyncClient):
    res = await client.patch(
        "/api/registry/model/enemies/imp/versions/not_a_real_id",
        json={"draft": True},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_patch_requires_body_field(client: AsyncClient):
    res = await client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={},
    )
    assert res.status_code == 400
