"""Contract tests for ``/api/assets/*`` JSON + binary (M902-26 Req 07)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract, assert_error_detail


@pytest.mark.asyncio
async def test_assets_list_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/assets")
    body = contract.validate(response, method="GET", path="/api/assets", expected_status=200)
    assert "assets" in body


@pytest.mark.asyncio
async def test_assets_list_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.delete("/api/assets")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_assets_textures_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/assets/textures")
    body = contract.validate(response, method="GET", path="/api/assets/textures", expected_status=200)
    assert "textures" in body


@pytest.mark.asyncio
async def test_assets_textures_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.put("/api/assets/textures")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_assets_texture_file_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/assets/textures/file/missing.png")
    assert response.status_code == 404
    assert_error_detail(response.json())


@pytest.mark.asyncio
async def test_assets_texture_file_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/assets/textures/file/../../../etc/passwd")
    assert response.status_code in {403, 404}
    if response.headers.get("content-type", "").startswith("application/json"):
        assert_error_detail(response.json())


@pytest.mark.asyncio
async def test_assets_serve_glb_happy_contract(
    async_client: AsyncClient,
    export_glb: str,
):
    response = await async_client.get(f"/api/assets/{export_glb}")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "octet-stream" in content_type or "gltf" in content_type
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_assets_serve_glb_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/assets/exports/missing.glb")
    assert response.status_code == 404
    if response.headers.get("content-type", "").startswith("application/json"):
        contract.validate(
            response,
            method="GET",
            path="/api/assets/{asset_path}",
            expected_status=404,
        )


@pytest.mark.asyncio
async def test_assets_serve_glb_forbidden_path_error_contract(async_client: AsyncClient):
    response = await async_client.get("/api/assets/../../../etc/passwd")
    assert response.status_code in {400, 403, 404}
    if response.headers.get("content-type", "").startswith("application/json"):
        assert_error_detail(response.json())
