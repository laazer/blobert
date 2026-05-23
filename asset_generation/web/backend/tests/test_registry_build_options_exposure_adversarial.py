"""
Adversarial HTTP exposure: missing snapshots, player parity, open without registry field.

Spec: R2, R6, R8.
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
async def test_get_registry_model_player_version_includes_build_options(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    snap = coerce_validate_enemy_build_options(
        "player_slime",
        options_for_enemy("player_slime", {"eye_count": 4}),
    )
    path = "player_exports/player_get_adv.glb"
    payload = {
        "schema_version": 1,
        "enemies": {},
        "player": {
            "versions": [
                {
                    "id": "player_get_adv",
                    "path": path,
                    "draft": False,
                    "in_use": True,
                    "build_options": snap,
                },
            ],
            "slots": [],
        },
    }
    (python_root / "player_exports").mkdir(parents=True, exist_ok=True)
    (python_root / path).write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / "model_registry.json").write_text(json.dumps(payload), encoding="utf-8")

    res = await client.get("/api/registry/model")
    assert res.status_code == 200
    row = res.json()["player"]["versions"][0]
    assert row["build_options"]["eye_count"] == 4


@pytest.mark.asyncio
async def test_load_existing_open_path_kind_without_registry_row_omits_build_options(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    glb_path = "animated_exports/orphan_animated_00.glb"
    (python_root / "animated_exports").mkdir(parents=True, exist_ok=True)
    (python_root / glb_path).write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / "model_registry.json").write_text(
        json.dumps({"schema_version": 1, "enemies": {}, "player": {"versions": [], "slots": []}}),
        encoding="utf-8",
    )

    res = await client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "path", "path": glb_path},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["path"] == glb_path
    assert "build_options" not in body
