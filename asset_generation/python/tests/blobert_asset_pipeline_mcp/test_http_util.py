"""Tests for blobert_asset_pipeline_mcp HTTP helpers."""

from __future__ import annotations

import httpx
import pytest

from blobert_asset_pipeline_mcp.http_util import (
    api_base,
    api_headers,
    encode_path_segments,
    format_http_response,
)


def test_encode_path_segments_preserves_slashes() -> None:
    assert encode_path_segments("enemies/spider.py") == "enemies/spider.py"


def test_encode_path_segments_encodes_spaces() -> None:
    assert "%20" in encode_path_segments("a b/c")


def test_format_http_response_json_object() -> None:
    r = httpx.Response(200, json={"status": "ok"})
    out = format_http_response(r)
    assert out["status_code"] == 200
    assert out["data"] == {"status": "ok"}


def test_format_http_response_binary_glb() -> None:
    r = httpx.Response(
        200,
        content=b"\x00\x01\x02",
        headers={"content-type": "model/gltf-binary"},
    )
    out = format_http_response(r)
    assert out["status_code"] == 200
    assert "content_base64" in out["data"]


def test_api_base_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOBERT_ASSET_API_BASE", "http://example:9999/")
    assert api_base() == "http://example:9999"


def test_api_headers_optional_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BLOBERT_ASSET_API_TOKEN", raising=False)
    assert api_headers() == {}
    monkeypatch.setenv("BLOBERT_ASSET_API_TOKEN", "tok")
    assert api_headers() == {"X-Blobert-Asset-Token": "tok"}
