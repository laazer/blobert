"""Shared httpx helpers for MCP tools (no FastAPI imports)."""

from __future__ import annotations

import base64
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

import httpx

_DEFAULT_BASE = "http://127.0.0.1:8000"


def api_base() -> str:
    return os.environ.get("BLOBERT_ASSET_API_BASE", _DEFAULT_BASE).rstrip("/")


def api_headers() -> dict[str, str]:
    tok = os.environ.get("BLOBERT_ASSET_API_TOKEN")
    if tok:
        return {"X-Blobert-Asset-Token": tok}
    return {}


def encode_path_segments(rel: str) -> str:
    """Encode each path segment for use in a URL path (preserve slashes)."""
    return "/".join(quote(part, safe="") for part in rel.split("/") if part != "")


def format_http_response(response: httpx.Response) -> dict[str, Any]:
    """Normalize httpx response into a JSON-serializable dict for MCP tools."""
    out: dict[str, Any] = {"status_code": response.status_code}
    if response.status_code == 204 or not response.content:
        out["data"] = None
        return out
    ct = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
    if "application/json" in ct:
        try:
            out["data"] = response.json()
            return out
        except json.JSONDecodeError:
            pass
    if response.content[:1] in (b"{", b"["):
        try:
            out["data"] = response.json()
            return out
        except json.JSONDecodeError:
            pass
    if "octet-stream" in ct or "gltf-binary" in ct:
        out["data"] = {
            "content_base64": base64.b64encode(response.content).decode("ascii"),
        }
        return out
    out["data"] = {"text": response.text}
    return out


@asynccontextmanager
async def http_client(*, read_timeout_seconds: float | None = None) -> AsyncIterator[httpx.AsyncClient]:
    read = read_timeout_seconds if read_timeout_seconds is not None else 3600.0
    timeout = httpx.Timeout(connect=30.0, read=read, write=60.0, pool=30.0)
    async with httpx.AsyncClient(
        base_url=api_base(),
        headers=api_headers(),
        timeout=timeout,
    ) as client:
        yield client
