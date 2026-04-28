"""Tests for texture manifest path resolution and optional PIL loading."""

from __future__ import annotations

from src.utils import texture_asset_loader as tal


def test_get_texture_asset_filepath_resolves_known_id() -> None:
    p = tal.get_texture_asset_filepath("demo_textures3")
    assert p.name == "demo textures3.png"
    assert p.parent == tal.get_texture_assets_dir()


def test_load_texture_image_returns_pillow_image() -> None:
    """Executes lazy PIL import in load_texture_image (see texture_asset_loader)."""
    im = tal.load_texture_image("demo_textures3")
    assert im.size[0] > 0 and im.size[1] > 0
