"""
Adversarial contract tests for M902-26 (Tier A strictness, cache drift, transport edges).

Exposes harness blind spots: extra top-level keys, live vs cached OpenAPI path sets,
malformed JSON bodies, unicode path segments, and SSE parsing/event-shape edges.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import jsonschema
import pytest
from httpx import AsyncClient

from tests.api.openapi_contract import (
    TIER_A_OPERATIONS,
    OpenAPIContract,
    assert_error_detail,
    load_cached_spec,
    load_live_spec,
    validate_response,
)
from tests.api.test_run_contract import _parse_sse_payloads

_UNICODE_DIR = "módulo_ñoño"
_UNICODE_FILE = "café_sample.py"


def _openapi_path_keys(spec: dict[str, Any]) -> set[str]:
    return set(spec.get("paths", {}).keys())


@pytest.fixture()
def unicode_src_file(src_tree: object, python_root: object) -> str:
    """Relative path under src/ using non-ASCII directory + filename."""
    rel_dir = _UNICODE_DIR
    module_dir = python_root / "src" / rel_dir  # type: ignore[operator]
    module_dir.mkdir(parents=True, exist_ok=True)
    rel_path = f"{rel_dir}/{_UNICODE_FILE}"
    (module_dir / _UNICODE_FILE).write_text("# unicode path contract fixture\n", encoding="utf-8")
    return rel_path


def test_tier_a_extra_top_level_key_rejected_by_harness(live_spec: dict[str, Any]) -> None:
    """Mutation: Tier A body with undeclared key must fail closed (Req 02 AC-02.4)."""
    polluted = {"status": "ok", "contract_probe": True}
    with pytest.raises(jsonschema.ValidationError) as exc_info:
        validate_response(
            live_spec,
            method="GET",
            path="/api/health",
            status_code=200,
            body=polluted,
        )
    message = str(exc_info.value)
    assert "contract_probe" in message
    assert (
        "unexpected top-level keys" in message
        or "Additional properties are not allowed" in message
    )


@pytest.mark.parametrize("method,path", sorted(TIER_A_OPERATIONS))
def test_tier_a_operations_documented_in_live_openapi(
    live_spec: dict[str, Any],
    method: str,
    path: str,
) -> None:
    """Assumption check: freeze table paths exist before response strictness runs."""
    assert path in live_spec.get("paths", {}), f"{method} {path} missing from live OpenAPI"
    assert method.lower() in live_spec["paths"][path]


def test_live_openapi_path_keys_are_subset_of_cached() -> None:
    """
    Drift detector: every live path must appear in committed openapi.cached.json.

    # CHECKPOINT: cache may document stale schemas (A3) but must not drop path keys;
    regen via ``npm run sync-api-types`` when this fails.
    """
    live_paths = _openapi_path_keys(load_live_spec())
    cached_paths = _openapi_path_keys(load_cached_spec())
    missing = live_paths - cached_paths
    assert not missing, (
        f"live OpenAPI paths missing from cache ({len(missing)}): "
        f"{sorted(missing)[:8]}{'...' if len(missing) > 8 else ''}"
    )


def test_cached_openapi_has_no_unknown_path_templates_vs_live() -> None:
    """
    Adversarial: cache-only path templates imply stale committed artifact.

    # CHECKPOINT: allow extra cache paths only when live is strict subset; fail on cache-only keys.
    """
    live_paths = _openapi_path_keys(load_live_spec())
    cached_paths = _openapi_path_keys(load_cached_spec())
    cache_only = cached_paths - live_paths
    assert not cache_only, (
        f"openapi.cached.json documents paths absent from live app: {sorted(cache_only)[:8]}"
    )


@pytest.mark.asyncio
async def test_health_live_response_has_no_extra_tier_a_keys(
    async_client: AsyncClient,
    contract: OpenAPIContract,
) -> None:
    response = await async_client.get("/api/health")
    contract.validate(response, method="GET", path="/api/health", expected_status=200)


@pytest.mark.asyncio
async def test_registry_model_live_response_has_no_extra_tier_a_keys(
    async_client: AsyncClient,
    contract: OpenAPIContract,
) -> None:
    response = await async_client.get("/api/registry/model")
    body = contract.validate(response, method="GET", path="/api/registry/model", expected_status=200)
    assert body["schema_version"] >= 1


@pytest.mark.asyncio
async def test_meta_enemies_live_response_has_no_extra_tier_a_keys(
    async_client: AsyncClient,
    contract: OpenAPIContract,
) -> None:
    response = await async_client.get("/api/meta/enemies")
    contract.validate(response, method="GET", path="/api/meta/enemies", expected_status=200)


@pytest.mark.asyncio
async def test_files_write_malformed_json_body_returns_422(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    src_tree: object,
) -> None:
    response = await async_client.put(
        "/api/files/module_a/sample.py",
        content=b"not-json{",
        headers={"Content-Type": "application/json"},
    )
    contract.validate(
        response,
        method="PUT",
        path="/api/files/{file_path}",
        expected_status=422,
    )


@pytest.mark.asyncio
async def test_registry_load_existing_open_malformed_json_returns_422(
    async_client: AsyncClient,
    contract: OpenAPIContract,
) -> None:
    response = await async_client.post(
        "/api/registry/model/load_existing/open",
        content=b"{kind: ",
        headers={"Content-Type": "application/json"},
    )
    contract.validate(
        response,
        method="POST",
        path="/api/registry/model/load_existing/open",
        expected_status=422,
    )


@pytest.mark.asyncio
async def test_files_read_unicode_path_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    unicode_src_file: str,
) -> None:
    # CHECKPOINT: URL-encode path segments; httpx encodes non-ASCII in request path.
    from urllib.parse import quote

    encoded = quote(unicode_src_file, safe="/")
    response = await async_client.get(f"/api/files/{encoded}")
    body = contract.validate(
        response,
        method="GET",
        path="/api/files/{file_path}",
        expected_status=200,
    )
    assert body["path"] == unicode_src_file
    assert "unicode path contract fixture" in body["content"]


@pytest.mark.asyncio
async def test_files_write_unicode_path_happy_contract(
    async_client: AsyncClient,
    contract: OpenAPIContract,
    unicode_src_file: str,
) -> None:
    from urllib.parse import quote

    encoded = quote(unicode_src_file, safe="/")
    response = await async_client.put(
        f"/api/files/{encoded}",
        json={"content": "# updated unicode path\n"},
    )
    body = contract.validate(
        response,
        method="PUT",
        path="/api/files/{file_path}",
        expected_status=200,
    )
    assert body.get("saved") is True


@pytest.mark.asyncio
async def test_assets_texture_unicode_path_returns_json_error_not_500(
    async_client: AsyncClient,
) -> None:
    from urllib.parse import quote

    segment = quote("textures/café_missing.png", safe="/")
    response = await async_client.get(f"/api/assets/textures/file/{segment}")
    assert response.status_code in {403, 404}
    if response.headers.get("content-type", "").startswith("application/json"):
        assert_error_detail(response.json())


@pytest.mark.asyncio
async def test_assets_glb_unicode_export_path_happy_or_404(
    async_client: AsyncClient,
    python_root: object,
) -> None:
    """Unicode GLB relative path under exports/ must not 500."""
    from urllib.parse import quote

    rel = "exports/café_demo.glb"
    export_dir = python_root / "exports"  # type: ignore[operator]
    export_dir.mkdir(parents=True, exist_ok=True)
    (python_root / rel).write_bytes(b"glTF\x00\x00\x00\x00")  # type: ignore[operator]
    encoded = quote(rel, safe="/")
    response = await async_client.get(f"/api/assets/{encoded}")
    assert response.status_code in {200, 403, 404}
    if response.status_code == 200:
        assert len(response.content) > 0


def test_parse_sse_malformed_data_line_raises_json_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        _parse_sse_payloads("event: log\ndata: {not valid json}\n\n")


def test_parse_sse_empty_body_yields_no_events() -> None:
    assert _parse_sse_payloads("") == []


def test_parse_sse_done_event_requires_exit_code_int() -> None:
    events = _parse_sse_payloads('event: done\ndata: {"exit_code": 0}\n\n')
    data = events[0]["data"]
    assert isinstance(data.get("exit_code"), int)


def test_parse_sse_log_event_requires_line_and_run_id_strings() -> None:
    events = _parse_sse_payloads('event: log\ndata: {"line": "x", "run_id": "r1"}\n\n')
    data = events[0]["data"]
    assert isinstance(data.get("line"), str)
    assert isinstance(data.get("run_id"), str)


@pytest.mark.asyncio
async def test_run_stream_log_event_contract(patched_process_manager: object) -> None:
    """Log SSE payload shape via ``_run_stream`` (avoids httpx/sse-starlette AppStatus loop bleed)."""
    from routers.run import _run_stream

    async def _one_line():
        yield "line-1\n"

    patched_process_manager.is_running = False  # type: ignore[attr-defined]
    patched_process_manager.stream_output = _one_line  # type: ignore[attr-defined]
    with patch("routers.run.process_manager", patched_process_manager):
        chunks: list[dict[str, str]] = []
        async for chunk in _run_stream(
            "animated",
            "imp",
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            None,
        ):
            chunks.append(chunk)
    log_chunks = [c for c in chunks if c.get("event") == "log"]
    assert log_chunks
    data = json.loads(log_chunks[0]["data"])
    assert isinstance(data.get("line"), str)
    assert isinstance(data.get("run_id"), str)


@pytest.mark.asyncio
async def test_run_stream_already_running_error_event_contract(
    running_process_manager: object,
) -> None:
    """
    SSE error when process busy — generator contract without ASGI/sse-starlette loop coupling.

    # CHECKPOINT: httpx+EventSourceResponse can raise event-loop errors under nested patches;
    assert ``_run_stream`` payload shape directly.
    """
    from routers.run import _run_stream

    with patch("routers.run.process_manager", running_process_manager):
        chunks: list[dict[str, str]] = []
        async for chunk in _run_stream(
            "animated",
            "imp",
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            None,
        ):
            chunks.append(chunk)
    assert chunks
    assert chunks[0]["event"] == "error"
    data = json.loads(chunks[0]["data"])
    assert isinstance(data.get("exit_code"), int)
    assert isinstance(data.get("message"), str) and data["message"]


@pytest.mark.asyncio
async def test_run_stream_done_event_via_mocked_manager(
    patched_process_manager: object,
) -> None:
    """Done SSE payload shape when mocked process exits 0 (Req 08 AC-08.3)."""
    from routers.run import _run_stream

    async def _empty():
        if False:  # pragma: no cover
            yield ""

    patched_process_manager.is_running = False  # type: ignore[attr-defined]
    patched_process_manager.stream_output = _empty  # type: ignore[attr-defined]
    patched_process_manager.exit_code.return_value = 0  # type: ignore[attr-defined]
    with patch("routers.run.process_manager", patched_process_manager):
        chunks: list[dict[str, str]] = []
        async for chunk in _run_stream(
            "animated",
            "imp",
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            None,
        ):
            chunks.append(chunk)
    done_chunks = [c for c in chunks if c.get("event") == "done"]
    assert done_chunks
    data = json.loads(done_chunks[0]["data"])
    assert isinstance(data.get("exit_code"), int)
