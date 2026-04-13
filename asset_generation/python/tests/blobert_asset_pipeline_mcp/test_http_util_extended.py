"""Additional coverage for blobert_asset_pipeline_mcp.http_util."""

from __future__ import annotations

import httpx
import pytest

from blobert_asset_pipeline_mcp.http_util import format_http_response, http_client


def test_format_http_response_204() -> None:
    r = httpx.Response(204, content=b"")
    out = format_http_response(r)
    assert out["status_code"] == 204
    assert out["data"] is None


def test_format_http_response_empty_body_200() -> None:
    r = httpx.Response(200, content=b"")
    out = format_http_response(r)
    assert out["data"] is None


def test_format_http_response_json_decode_error_with_json_ct() -> None:
    r = httpx.Response(
        200,
        content=b"not json",
        headers={"content-type": "application/json"},
    )
    out = format_http_response(r)
    assert out["status_code"] == 200
    assert out["data"] == {"text": "not json"}


def test_format_http_response_brace_prefix_invalid_json() -> None:
    r = httpx.Response(200, content=b"{not valid", headers={"content-type": "text/plain"})
    out = format_http_response(r)
    assert out["data"] == {"text": "{not valid"}


def test_format_http_response_brace_prefix_valid_json_without_json_ct() -> None:
    r = httpx.Response(200, content=b'{"x":1}', headers={"content-type": "text/plain"})
    out = format_http_response(r)
    assert out["data"] == {"x": 1}


def test_format_http_response_octet_stream_base64() -> None:
    r = httpx.Response(
        200,
        content=b"\xff\x00",
        headers={"content-type": "application/octet-stream"},
    )
    out = format_http_response(r)
    assert out["data"]["content_base64"] == "/wA="


def test_format_http_response_gltf_binary_ct() -> None:
    r = httpx.Response(
        200,
        content=b"glb",
        headers={"content-type": "model/gltf-binary"},
    )
    out = format_http_response(r)
    assert "content_base64" in out["data"]


@pytest.mark.asyncio
async def test_http_client_context_yields_async_client() -> None:
    async with http_client(read_timeout_seconds=30.0) as client:
        assert isinstance(client, httpx.AsyncClient)
        assert str(client.base_url).rstrip("/").endswith("8000")
