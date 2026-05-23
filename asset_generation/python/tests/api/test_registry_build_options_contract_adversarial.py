"""
Adversarial OpenAPI contracts for registry ``build_options`` (oversized manifest, player open).

Spec: R1, R6, R8, R7.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract

from src.utils.build_options import coerce_validate_enemy_build_options, options_for_enemy

_BUILD_OPTIONS_MAX_BYTES = 262_144


def _write_oversized_imp_manifest(python_root: pathlib.Path) -> None:
    snap = coerce_validate_enemy_build_options("imp", options_for_enemy("imp", {}))
    snap["feat_body_hex"] = "z" * (_BUILD_OPTIONS_MAX_BYTES + 64)
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
                        "build_options": snap,
                    },
                ],
            },
        },
        "player": {"versions": [], "slots": []},
    }
    (python_root / "animated_exports").mkdir(parents=True, exist_ok=True)
    (python_root / "animated_exports" / "imp_animated_00.glb").write_bytes(b"glTF\x00\x00\x00\x00")
    (python_root / "model_registry.json").write_text(json.dumps(payload), encoding="utf-8")


def _seed_player_open_fixture(python_root: pathlib.Path) -> None:
    snap = coerce_validate_enemy_build_options(
        "player_slime",
        options_for_enemy("player_slime", {"eye_count": 3}),
    )
    path = "player_exports/player_open_adv.glb"
    payload = {
        "schema_version": 1,
        "enemies": {},
        "player": {
            "versions": [
                {
                    "id": "player_open_adv",
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


@pytest.mark.asyncio
async def test_registry_model_contract_rejects_oversized_build_options_on_disk(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    python_root: pathlib.Path,
) -> None:
    _write_oversized_imp_manifest(python_root)

    response = await async_client.get("/api/registry/model")
    assert response.status_code == 500
    detail = response.json().get("detail", "")
    assert "build_options" in detail.lower() or "unexpected" in detail.lower() or "validation" in detail.lower()


@pytest.mark.asyncio
async def test_registry_load_existing_open_player_contract_includes_build_options(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    python_root: pathlib.Path,
) -> None:
    _seed_player_open_fixture(python_root)

    response = await async_client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "player", "version_id": "player_open_adv"},
    )
    body = contract.validate(
        response,
        method="POST",
        path="/api/registry/model/load_existing/open",
        expected_status=200,
    )
    assert body["build_options"]["eye_count"] == 3
