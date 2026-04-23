from __future__ import annotations

import logging
import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app


@pytest_asyncio.fixture()
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client


@pytest.mark.asyncio
async def test_registry_model_import_error_maps_to_503_with_unavailable_detail(client: AsyncClient) -> None:
    with patch("routers.registry._load_service", side_effect=ImportError("bridge offline")):
        response = await client.get("/api/registry/model")

    assert response.status_code == 503
    payload = response.json()
    assert isinstance(payload.get("detail"), str)
    assert payload["detail"].startswith("registry unavailable:")
    assert "bridge offline" in payload["detail"]


@pytest.mark.asyncio
async def test_registry_delete_forbidden_target_path_maps_to_403(client: AsyncClient) -> None:
    with patch(
        "routers.registry._load_service",
        side_effect=ValueError("forbidden target path class: absolute-path"),
    ):
        response = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_00",
            json={"confirm": True, "delete_files": False},
        )

    assert response.status_code == 403
    assert response.json() == {"detail": "forbidden target path class: absolute-path"}


@pytest.mark.asyncio
async def test_assets_textures_runtime_failure_maps_to_500_with_detail_shape(client: AsyncClient) -> None:
    with patch("routers.assets.import_asset_module", side_effect=RuntimeError("loader failure")):
        response = await client.get("/api/assets/textures")

    assert response.status_code == 500
    payload = response.json()
    assert isinstance(payload.get("detail"), str)
    assert payload["detail"].startswith("Failed to load texture assets:")


@pytest.mark.asyncio
async def test_unknown_failures_use_safe_generic_detail_consistently_across_routers(client: AsyncClient) -> None:
    secret_token = "SECRET_INTERNAL_TOKEN_42"
    with (
        patch("routers.registry._load_service", side_effect=RuntimeError(secret_token)),
        patch("routers.assets.import_asset_module", side_effect=RuntimeError(secret_token)),
    ):
        registry_response = await client.get("/api/registry/model")
        assets_response = await client.get("/api/assets/textures")

    assert registry_response.status_code == 500
    assert assets_response.status_code == 500

    registry_detail = registry_response.json().get("detail")
    assets_detail = assets_response.json().get("detail")

    assert isinstance(registry_detail, str)
    assert isinstance(assets_detail, str)
    assert "internal" in registry_detail.lower()
    assert "internal" in assets_detail.lower()
    assert secret_token not in registry_detail
    assert secret_token not in assets_detail
    assert registry_detail == assets_detail


@pytest.mark.asyncio
async def test_unknown_failure_logs_structured_context_for_assets_fallback(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR)
    with patch("routers.assets.import_asset_module", side_effect=RuntimeError("boom")):
        response = await client.get("/api/assets/textures")

    assert response.status_code == 500
    assert any(
        record.__dict__.get("route") == "/api/assets/textures"
        and record.__dict__.get("exception_type") == "RuntimeError"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_unknown_failure_logs_structured_context_for_registry_fallback(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR)
    with patch("routers.registry._load_service", side_effect=RuntimeError("boom")):
        response = await client.get("/api/registry/model")

    assert response.status_code == 500
    assert any(
        record.__dict__.get("route") == "/api/registry/model"
        and record.__dict__.get("exception_type") == "RuntimeError"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_unknown_failure_logs_structured_context_for_run_fallback(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR)
    with patch("routers.run.process_manager.start", side_effect=RuntimeError("boom")):
        response = await client.get("/api/run/complete?cmd=test")

    assert response.status_code == 500
    assert any(
        record.__dict__.get("route") == "/api/run/complete"
        and record.__dict__.get("exception_type") == "RuntimeError"
        for record in caplog.records
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_error", "expected_status"),
    [
        ("forbidden target path class: absolute-path", 403),
        ("FORBIDDEN target path class: absolute-path", 400),
        ("prefix forbidden target path class: absolute-path", 400),
    ],
)
async def test_registry_delete_value_error_precedence_is_prefix_exact(
    client: AsyncClient,
    service_error: str,
    expected_status: int,
) -> None:
    # CHECKPOINT: preserve conservative precedence: only the exact forbidden prefix
    # is promoted to 403; broader substring/case-insensitive matching stays 400.
    with patch("routers.registry._load_service", side_effect=ValueError(service_error)):
        response = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_00",
            json={"confirm": True, "delete_files": False},
        )

    assert response.status_code == expected_status
    assert response.json() == {"detail": service_error}


@pytest.mark.asyncio
async def test_unknown_failures_remain_redaction_safe_under_concurrent_burst(client: AsyncClient) -> None:
    secret_token = "SECRET_BURST_TOKEN_314159"

    with (
        patch("routers.registry._load_service", side_effect=RuntimeError(secret_token)),
        patch("routers.assets.import_asset_module", side_effect=RuntimeError(secret_token)),
    ):
        async def _request_pair() -> tuple[str, str]:
            reg = await client.get("/api/registry/model")
            tex = await client.get("/api/assets/textures")
            assert reg.status_code == 500
            assert tex.status_code == 500
            return reg.json().get("detail", ""), tex.json().get("detail", "")

        pairs = await asyncio.gather(*[_request_pair() for _ in range(20)])

    registry_details = [pair[0] for pair in pairs]
    assets_details = [pair[1] for pair in pairs]

    assert len(set(registry_details)) == 1
    assert len(set(assets_details)) == 1
    assert set(registry_details) == set(assets_details)
    assert all(secret_token not in detail for detail in registry_details)
    assert all(secret_token not in detail for detail in assets_details)


@pytest.mark.asyncio
async def test_run_complete_unknown_start_failure_uses_safe_fallback_contract(client: AsyncClient) -> None:
    secret_token = "SECRET_RUN_START_FAILURE_99"
    with patch("routers.run.process_manager.start", side_effect=RuntimeError(secret_token)):
        response = await client.get("/api/run/complete?cmd=test")

    # CHECKPOINT: conservative cross-router fallback should avoid exposing raw
    # subprocess-start failures to clients.
    assert response.status_code == 500
    detail = response.json().get("detail")
    assert isinstance(detail, str)
    assert "internal" in detail.lower()
    assert secret_token not in detail
