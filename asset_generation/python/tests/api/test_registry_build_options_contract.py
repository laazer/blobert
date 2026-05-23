"""
OpenAPI contract: registry ``build_options`` on GET model and load_existing/open (FEAT-20260522).

Spec: R1, R8.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from httpx import AsyncClient

from src.utils.build_options import (
    coerce_validate_enemy_build_options,
    options_for_enemy,
)
from tests.api.openapi_contract import OpenAPIContract


def _seed_spider_row_with_snapshot(python_root: pathlib.Path) -> None:
    snap = coerce_validate_enemy_build_options("spider", options_for_enemy("spider", {"eye_count": 8}))
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
    (python_root / "model_registry.json").write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.asyncio
async def test_registry_model_contract_includes_build_options_on_version_row(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    python_root: pathlib.Path,
) -> None:
    _seed_spider_row_with_snapshot(python_root)

    response = await async_client.get("/api/registry/model")
    body = contract.validate(response, method="GET", path="/api/registry/model", expected_status=200)
    row = body["enemies"]["spider"]["versions"][0]
    assert isinstance(row.get("build_options"), dict)
    assert row["build_options"]["eye_count"] == 8


@pytest.mark.asyncio
async def test_registry_load_existing_open_contract_includes_build_options(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    python_root: pathlib.Path,
) -> None:
    _seed_spider_row_with_snapshot(python_root)

    response = await async_client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "enemy", "family": "spider", "version_id": "spider_animated_00"},
    )
    body = contract.validate(
        response,
        method="POST",
        path="/api/registry/model/load_existing/open",
        expected_status=200,
    )
    assert body["build_options"]["eye_count"] == 8
