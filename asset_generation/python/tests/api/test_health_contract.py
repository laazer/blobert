"""Contract tests for ``GET /api/health`` (M902-26 Req 09)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract


@pytest.mark.asyncio
async def test_health_happy_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/health")
    body = contract.validate(response, method="GET", path="/api/health", expected_status=200)
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_health_error_contract_method_not_allowed(
    async_client: AsyncClient,
    contract: OpenAPIContract,
):
    response = await async_client.post("/api/health", json={})
    assert response.status_code == 405
    if response.headers.get("content-type", "").startswith("application/json"):
        contract.validate(response, method="POST", path="/api/health", expected_status=405)
