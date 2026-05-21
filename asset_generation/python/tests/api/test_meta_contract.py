"""Contract tests for ``/api/meta/*`` (M902-26 Req 09)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract, assert_error_detail


@pytest.mark.asyncio
async def test_meta_enemies_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/meta/enemies")
    body = contract.validate(response, method="GET", path="/api/meta/enemies", expected_status=200)
    assert "meta_backend" in body
    assert isinstance(body.get("enemies"), list)


@pytest.mark.asyncio
async def test_meta_enemies_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.post("/api/meta/enemies")
    assert response.status_code == 405
    if response.headers.get("content-type", "").startswith("application/json"):
        assert_error_detail(response.json())


@pytest.mark.asyncio
async def test_meta_animations_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/meta/animations")
    body = contract.validate(response, method="GET", path="/api/meta/animations", expected_status=200)
    assert isinstance(body, dict)
    assert len(body) > 0


@pytest.mark.asyncio
async def test_meta_animations_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.delete("/api/meta/animations")
    assert response.status_code == 405
