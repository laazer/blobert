"""Tests for texture manifest path resolution and optional PIL loading."""

from __future__ import annotations

from unittest.mock import patch

from src.utils import texture_asset_loader as tal


def test_get_texture_asset_filepath_resolves_known_id() -> None:
    p = tal.get_texture_asset_filepath("demo_textures3")
    assert p.name == "demo textures3.png"
    assert p.parent == tal.get_texture_assets_dir()


def test_load_texture_image_returns_pillow_image() -> None:
    """Executes lazy PIL import in load_texture_image (see texture_asset_loader)."""
    im = tal.load_texture_image("demo_textures3")
    assert im.size[0] > 0 and im.size[1] > 0


def test_infer_texture_asset_id_from_preview_path() -> None:
    got = tal.infer_texture_asset_id_from_preview("/api/assets/textures/file/demo%20textures3.png")
    assert got == "demo_textures3"


def test_infer_texture_asset_id_from_preview_url() -> None:
    got = tal.infer_texture_asset_id_from_preview(
        "http://localhost:8000/api/assets/textures/file/f4f1cb2269ba444797c0bf3af83f17490c4dfb1039246d1d001803075e82fb40.png"
    )
    assert got == "hash_texture"


def test_infer_texture_asset_id_from_preview_none_or_blank() -> None:
    assert tal.infer_texture_asset_id_from_preview(None) is None
    assert tal.infer_texture_asset_id_from_preview("") is None
    assert tal.infer_texture_asset_id_from_preview("   ") is None


def test_infer_texture_asset_id_from_preview_bare_filename() -> None:
    got = tal.infer_texture_asset_id_from_preview("demo%20textures3.png")
    assert got == "demo_textures3"


def test_infer_texture_asset_id_skips_non_dict_manifest_entries() -> None:
    bad_manifest = {
        "demo_textures3": {"filename": "demo textures3.png"},
        "bad": "nope",
    }
    with patch.object(tal, "load_texture_manifest", return_value=bad_manifest):
        got = tal.infer_texture_asset_id_from_preview(
            "/api/assets/textures/file/demo%20textures3.png"
        )
    assert got == "demo_textures3"
