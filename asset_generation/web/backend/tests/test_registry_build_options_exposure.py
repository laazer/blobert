"""
Registry HTTP exposure of ``versions[].build_options`` (FEAT-20260522).

Spec: R1, R8 — GET ``/api/registry/model`` and POST ``load_existing/open``.
"""

from __future__ import annotations

import json
import pathlib

import core.config as config_module
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app

from src.utils.build_options import coerce_validate_enemy_build_options, options_for_enemy


def _spider_snapshot(**overrides: object) -> dict[str, object]:
    return coerce_validate_enemy_build_options("spider", options_for_enemy("spider", dict(overrides)))


def _seed_manifest_with_build_options(python_root: pathlib.Path) -> dict[str, object]:
    snap = _spider_snapshot(eye_count=12, feat_body_hex="aabbcc")
    payload = {
        "schema_version": 1,
        "enemies": {
            "spider": {
                "versions": [
                    {
                        "id": "spider_animated_00",
                        "path": "animated_exports/spider_animated_00.glb",
                        "draft": False,
                        "in_use": True,
                        "build_options": snap,
                    },
                ],
            },
        },
        "player": {"versions": [], "slots": []},
    }
    (python_root / "animated_exports").mkdir(parents=True, exist_ok=True)
    (python_root / "animated_exports" / "spider_animated_00.glb").write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / "model_registry.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return snap


@pytest.fixture()
def python_root(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    root = tmp_path / "python"
    root.mkdir(parents=True)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_registry_model_includes_build_options_on_version_row(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    expected = _seed_manifest_with_build_options(python_root)

    res = await client.get("/api/registry/model")
    assert res.status_code == 200
    body = res.json()
    row = body["enemies"]["spider"]["versions"][0]
    assert row["build_options"]["eye_count"] == expected["eye_count"]
    assert row["build_options"]["features"]["body"]["hex"] == "aabbcc"


@pytest.mark.asyncio
async def test_load_existing_open_includes_build_options_from_registry_row(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    expected = _seed_manifest_with_build_options(python_root)

    res = await client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "enemy", "family": "spider", "version_id": "spider_animated_00"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["path"] == "animated_exports/spider_animated_00.glb"
    assert body["build_options"]["eye_count"] == expected["eye_count"]
    assert body["build_options"]["features"]["body"]["hex"] == "aabbcc"


@pytest.mark.asyncio
async def test_load_existing_open_omits_build_options_when_row_has_none(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    payload = {
        "schema_version": 1,
        "enemies": {
            "imp": {
                "versions": [
                    {
                        "id": "imp_animated_00",
                        "path": "animated_exports/imp_animated_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                ],
            },
        },
        "player": {"versions": [], "slots": []},
    }
    (python_root / "animated_exports").mkdir(parents=True, exist_ok=True)
    (python_root / "animated_exports" / "imp_animated_00.glb").write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / "model_registry.json").write_text(json.dumps(payload), encoding="utf-8")

    res = await client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "enemy", "family": "imp", "version_id": "imp_animated_00"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "build_options" not in body
