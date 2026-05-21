"""Contract tests for ``/api/registry/*`` (M902-26 Req 04)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract


@pytest.mark.asyncio
async def test_registry_load_existing_candidates_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.get("/api/registry/model/load_existing/candidates")
    body = contract.validate(
        response,
        method="GET",
        path="/api/registry/model/load_existing/candidates",
        expected_status=200,
    )
    assert "candidates" in body


@pytest.mark.asyncio
async def test_registry_load_existing_candidates_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post("/api/registry/model/load_existing/candidates")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_registry_load_existing_open_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "enemy", "family": "imp", "version_id": "imp_animated_00"},
    )
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/load_existing/open",
        expected_status=404,
    )


@pytest.mark.asyncio
async def test_registry_load_existing_open_mixed_identity_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post(
        "/api/registry/model/load_existing/open",
        json={"kind": "enemy", "family": "imp", "version_id": "x", "path": "exports/x.glb"},
    )
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/load_existing/open",
        expected_status=400,
    )


@pytest.mark.asyncio
async def test_registry_load_existing_open_missing_kind_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post(
        "/api/registry/model/load_existing/open",
        json={"family": "imp"},
    )
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/load_existing/open",
        expected_status=422,
    )


@pytest.mark.asyncio
async def test_registry_model_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/registry/model")
    body = contract.validate(response, method="GET", path="/api/registry/model", expected_status=200)
    assert body["schema_version"] >= 1
    assert "enemies" in body


@pytest.mark.asyncio
async def test_registry_model_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.delete("/api/registry/model")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_registry_patch_enemy_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={"draft": True},
    )
    contract.validate(
        response,
        method="PATCH",
        path="/api/registry/model/enemies/{family}/versions/{version_id}",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_patch_enemy_empty_body_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.patch(
        "/api/registry/model/enemies/imp/versions/imp_animated_00",
        json={},
    )
    contract.validate(
        response,
        method="PATCH",
        path="/api/registry/model/enemies/{family}/versions/{version_id}",
        expected_status=400,
    )


@pytest.mark.asyncio
async def test_registry_patch_player_active_visual_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    registry_with_player_version: object,
):
    response = await async_client.patch(
        "/api/registry/model/player_active_visual",
        json={"draft": False, "path": "player_exports/player_test_00.glb"},
    )
    contract.validate(
        response,
        method="PATCH",
        path="/api/registry/model/player_active_visual",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_patch_player_active_visual_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.patch(
        "/api/registry/model/player_active_visual",
        json={},
    )
    contract.validate(
        response,
        method="PATCH",
        path="/api/registry/model/player_active_visual",
        expected_status=400,
    )


@pytest.mark.asyncio
async def test_registry_enemy_slots_get_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.get("/api/registry/model/enemies/imp/slots")
    contract.validate(
        response,
        method="GET",
        path="/api/registry/model/enemies/{family}/slots",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_enemy_slots_get_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.get("/api/registry/model/enemies/unknown_family/slots")
    contract.validate(
        response,
        method="GET",
        path="/api/registry/model/enemies/{family}/slots",
        expected_status=404,
    )


@pytest.mark.asyncio
async def test_registry_sync_animated_exports_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post("/api/registry/model/enemies/imp/sync_animated_exports")
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/enemies/{family}/sync_animated_exports",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_sync_animated_exports_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post("/api/registry/model/enemies/nope/sync_animated_exports")
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/enemies/{family}/sync_animated_exports",
        expected_status=404,
    )


@pytest.mark.asyncio
async def test_registry_enemy_slots_put_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.put(
        "/api/registry/model/enemies/imp/slots",
        json={"version_ids": ["imp_animated_00"]},
    )
    contract.validate(
        response,
        method="PUT",
        path="/api/registry/model/enemies/{family}/slots",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_enemy_slots_put_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.put(
        "/api/registry/model/enemies/imp/slots",
        json={"version_ids": "not-an-array"},
    )
    contract.validate(
        response,
        method="PUT",
        path="/api/registry/model/enemies/{family}/slots",
        expected_status=422,
    )


@pytest.mark.asyncio
async def test_registry_player_slots_get_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.get("/api/registry/model/player/slots")
    contract.validate(
        response,
        method="GET",
        path="/api/registry/model/player/slots",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_player_slots_get_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post("/api/registry/model/player/slots")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_registry_player_slots_put_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    registry_with_player_version: object,
):
    response = await async_client.put(
        "/api/registry/model/player/slots",
        json={"version_ids": ["player_test_00"]},
    )
    contract.validate(
        response,
        method="PUT",
        path="/api/registry/model/player/slots",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_player_slots_put_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.put(
        "/api/registry/model/player/slots",
        json={"version_ids": 1},
    )
    contract.validate(
        response,
        method="PUT",
        path="/api/registry/model/player/slots",
        expected_status=422,
    )


@pytest.mark.asyncio
async def test_registry_sync_player_exports_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post("/api/registry/model/player/sync_player_exports")
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/player/sync_player_exports",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_sync_player_exports_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.get("/api/registry/model/player/sync_player_exports")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_registry_spawn_eligible_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.get("/api/registry/model/spawn_eligible/imp")
    body = contract.validate(
        response,
        method="GET",
        path="/api/registry/model/spawn_eligible/{family}",
        expected_status=200,
    )
    assert body["family"] == "imp"
    assert "paths" in body


@pytest.mark.asyncio
async def test_registry_spawn_eligible_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.patch(
        "/api/registry/model/enemies/not_a_family/versions/missing_id",
        json={"draft": True},
    )
    contract.validate(
        response,
        method="PATCH",
        path="/api/registry/model/enemies/{family}/versions/{version_id}",
        expected_status=404,
    )


@pytest.mark.asyncio
async def test_registry_delete_enemy_version_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    family = "imp"
    version_id = "imp_animated_00"
    await async_client.patch(
        f"/api/registry/model/enemies/{family}/versions/{version_id}",
        json={"draft": True, "in_use": False},
    )
    response = await async_client.request(
        "DELETE",
        f"/api/registry/model/enemies/{family}/versions/{version_id}",
        json={
            "confirm": True,
            "confirm_text": f"delete draft {family} {version_id}",
        },
    )
    contract.validate(
        response,
        method="DELETE",
        path="/api/registry/model/enemies/{family}/versions/{version_id}",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_delete_enemy_version_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.request(
        "DELETE",
        "/api/registry/model/enemies/nope/versions/missing",
        json={"confirm": True},
    )
    contract.validate(
        response,
        method="DELETE",
        path="/api/registry/model/enemies/{family}/versions/{version_id}",
        expected_status=404,
    )


@pytest.mark.asyncio
async def test_registry_delete_player_active_visual_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    registry_with_player_version: object,
):
    await async_client.patch(
        "/api/registry/model/player_active_visual",
        json={"draft": True, "path": "player_exports/player_test_00.glb"},
    )
    response = await async_client.request(
        "DELETE",
        "/api/registry/model/player_active_visual",
        json={"confirm": True},
    )
    contract.validate(
        response,
        method="DELETE",
        path="/api/registry/model/player_active_visual",
        expected_status=200,
    )


@pytest.mark.asyncio
async def test_registry_delete_player_active_visual_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.request(
        "DELETE",
        "/api/registry/model/player_active_visual",
        json={},
    )
    contract.validate(
        response,
        method="DELETE",
        path="/api/registry/model/player_active_visual",
        expected_status=400,
    )
