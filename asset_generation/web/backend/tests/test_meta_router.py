"""
GET /api/meta/enemies — build controls must load outside Blender (stubs + registry introspection).

Run from asset_generation/web/backend/:
    python -m pytest tests/test_meta_router.py -v
"""

from __future__ import annotations

import pathlib
from unittest.mock import patch

import core.config as config_module
import pytest
from httpx import ASGITransport, AsyncClient
from main import app


def _repo_python_root() -> pathlib.Path:
    """asset_generation/python (four levels up from tests/test_meta_router.py)."""
    return pathlib.Path(__file__).resolve().parent.parent.parent.parent / "python"


@pytest.mark.asyncio
async def test_meta_enemies_returns_full_build_controls_for_spider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/meta/enemies")

    assert res.status_code == 200
    data = res.json()
    assert data.get("meta_backend") == "ok"
    assert "meta_error" not in data or data.get("meta_error") is None
    spider = data["animated_build_controls"].get("spider")
    assert spider is not None
    assert len(spider) >= 1
    keys = {c["key"] for c in spider}
    assert "eye_count" in keys
    eye = next(c for c in spider if c["key"] == "eye_count")
    assert eye["type"] == "select"
    assert len(eye["options"]) >= 1

    slug = data["animated_build_controls"].get("slug")
    assert slug is not None
    place_top = next((c for c in slug if c["key"] == "extra_zone_body_place_top"), None)
    assert place_top is not None
    assert place_top["type"] == "bool"
    assert place_top["default"] is True


@pytest.mark.asyncio
async def test_meta_enemies_fallback_on_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ImportError during stub/build pipeline returns 200 with meta_backend=fallback (not silent empty ok)."""
    monkeypatch.setattr(config_module.settings, "python_root", _repo_python_root())

    def _raise_import() -> None:
        raise ImportError("simulated missing dependency")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("utils.blender_stubs.ensure_blender_stubs", side_effect=_raise_import):
            res = await client.get("/api/meta/enemies")

    assert res.status_code == 200
    data = res.json()
    assert data.get("meta_backend") == "fallback"
    assert "meta_error" in data
    assert "simulated" in data["meta_error"]
    assert data.get("animated_build_controls") == {}
    assert len(data.get("enemies", [])) >= 1
