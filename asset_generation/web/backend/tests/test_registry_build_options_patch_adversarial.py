"""
Adversarial PATCH: clients must not mutate ``build_options`` via version patch (R7).

HTTP must reject or ignore client snapshots; on-disk registry snapshot unchanged.
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


def _seed_imp_with_snapshot(python_root: pathlib.Path) -> dict[str, object]:
    canonical = coerce_validate_enemy_build_options("imp", options_for_enemy("imp", {"eye_count": 7}))
    attacker = coerce_validate_enemy_build_options("imp", options_for_enemy("imp", {"eye_count": 66}))
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
                        "build_options": canonical,
                    },
                ],
            },
        },
        "player": {"versions": [], "slots": []},
        "_attacker_snapshot": attacker,
    }
    (python_root / "animated_exports").mkdir(parents=True, exist_ok=True)
    (python_root / "animated_exports" / "imp_animated_00.glb").write_bytes(b"glTF\x00\x00\x00\x00")
    on_disk = {k: v for k, v in payload.items() if not k.startswith("_")}
    (python_root / "model_registry.json").write_text(json.dumps(on_disk), encoding="utf-8")
    return {"canonical": canonical, "attacker": payload["_attacker_snapshot"]}


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
async def test_patch_body_with_only_build_options_rejected(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    snaps = _seed_imp_with_snapshot(python_root)

    res = await client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={"build_options": snaps["attacker"]},
    )
    assert res.status_code in (400, 422)

    disk = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
    row = disk["enemies"]["imp"]["versions"][0]
    assert row.get("build_options", {}).get("eye_count") == 7


@pytest.mark.asyncio
async def test_patch_mixed_draft_and_build_options_preserves_canonical_snapshot(
    client: AsyncClient,
    python_root: pathlib.Path,
) -> None:
    snaps = _seed_imp_with_snapshot(python_root)

    res = await client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={"draft": True, "build_options": snaps["attacker"]},
    )
    assert res.status_code == 200

    disk = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
    row = disk["enemies"]["imp"]["versions"][0]
    assert row["draft"] is True
    assert row["build_options"]["eye_count"] == 7
