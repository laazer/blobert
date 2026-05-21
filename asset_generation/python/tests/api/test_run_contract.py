"""Contract tests for ``/api/run/*`` JSON + SSE (M902-26 Req 06, 08)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import OpenAPIContract, assert_error_detail


def _parse_sse_payloads(text: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    current_event: str | None = None
    for line in text.splitlines():
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            raw = line.split(":", 1)[1].strip()
            payload = json.loads(raw)
            events.append({"event": current_event, "data": payload})
    return events


@pytest.mark.asyncio
async def test_run_status_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    patched_process_manager: object,
):
    response = await async_client.get("/api/run/status")
    body = contract.validate(response, method="GET", path="/api/run/status", expected_status=200)
    assert "is_running" in body


@pytest.mark.asyncio
async def test_run_status_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.post("/api/run/status")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_run_kill_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    patched_process_manager: object,
):
    response = await async_client.post("/api/run/kill")
    body = contract.validate(response, method="POST", path="/api/run/kill", expected_status=200)
    assert "killed" in body


@pytest.mark.asyncio
async def test_run_kill_error_contract(async_client: AsyncClient, contract: OpenAPIContract):
    response = await async_client.get("/api/run/kill")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_run_complete_invalid_cmd_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    patched_process_manager: object,
):
    response = await async_client.get("/api/run/complete", params={"cmd": "not_a_command"})
    contract.validate(response, method="GET", path="/api/run/complete", expected_status=400)


@pytest.mark.asyncio
async def test_run_complete_conflict_error_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    running_process_manager: object,
):
    with patch("routers.run.process_manager", running_process_manager):
        response = await async_client.get("/api/run/complete", params={"cmd": "animated", "enemy": "imp"})
    contract.validate(response, method="GET", path="/api/run/complete", expected_status=409)


@pytest.mark.asyncio
async def test_run_complete_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    patched_process_manager: object,
):
    async def _one_line():
        yield "line-1\n"

    patched_process_manager.stream_output = _one_line  # type: ignore[attr-defined]
    response = await async_client.get(
        "/api/run/complete",
        params={"cmd": "animated", "enemy": "imp", "max_wait_ms": 5000},
    )
    contract.validate(response, method="GET", path="/api/run/complete", expected_status=200)


@pytest.mark.asyncio
async def test_run_stream_invalid_cmd_error_contract(
    async_client: AsyncClient,
    patched_process_manager: object,
):
    response = await async_client.get("/api/run/stream", params={"cmd": "invalid_cmd"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    events = _parse_sse_payloads(response.text)
    assert events
    error_events = [e for e in events if e.get("event") == "error"]
    assert error_events
    data = error_events[0]["data"]
    assert isinstance(data, dict)
    assert "exit_code" in data
    assert isinstance(data.get("message"), str)
    assert data["message"]


def test_run_stream_done_event_happy_contract():
    """Happy SSE data shape (Req 08) without ASGI/sse-starlette event-loop coupling."""
    events = _parse_sse_payloads('event: done\ndata: {"exit_code": 0, "output_file": "exports/x.glb"}\n\n')
    done = next(e for e in events if e.get("event") == "done")
    data = done["data"]
    assert isinstance(data.get("exit_code"), int)


@pytest.mark.asyncio
async def test_run_stream_malformed_query_error_contract(async_client: AsyncClient):
    response = await async_client.get("/api/run/stream")
    assert response.status_code == 422
    assert_error_detail(response.json())
