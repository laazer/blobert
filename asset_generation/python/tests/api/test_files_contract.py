"""Contract tests for ``/api/files/*`` (M902-26 Req 05)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract


@pytest.mark.asyncio
async def test_files_list_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    src_tree: object,
):
    response = await async_client.get("/api/files")
    body = contract.validate(response, method="GET", path="/api/files", expected_status=200)
    assert isinstance(body.get("tree"), list)


@pytest.mark.asyncio
async def test_files_list_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    python_root: object,
):
    response = await async_client.get("/api/files")
    contract.validate(response, method="GET", path="/api/files", expected_status=404)


@pytest.mark.asyncio
async def test_files_read_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    src_tree: object,
):
    response = await async_client.get("/api/files/module_a/sample.py")
    body = contract.validate(
        response,
        method="GET",
        path="/api/files/{file_path}",
        expected_status=200,
    )
    assert body["path"] == "module_a/sample.py"
    assert isinstance(body["content"], str)


@pytest.mark.asyncio
async def test_files_read_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    src_tree: object,
):
    response = await async_client.get("/api/files/does_not_exist.py")
    contract.validate(
        response,
        method="GET",
        path="/api/files/{file_path}",
        expected_status=404,
    )


@pytest.mark.asyncio
async def test_files_write_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    src_tree: object,
):
    response = await async_client.put(
        "/api/files/module_a/sample.py",
        json={"content": "# updated by contract test\n"},
    )
    body = contract.validate(
        response,
        method="PUT",
        path="/api/files/{file_path}",
        expected_status=200,
    )
    assert body.get("saved") is True


@pytest.mark.asyncio
async def test_files_write_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    src_tree: object,
):
    response = await async_client.put("/api/files/module_a/sample.py", json={})
    contract.validate(
        response,
        method="PUT",
        path="/api/files/{file_path}",
        expected_status=422,
    )
