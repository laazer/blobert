"""Tests for atlas UV rectangle parsing and PIL crop box."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from src.materials.uv_atlas import (
    parse_uv_rect,
    read_png_ihdr_dimensions,
    texture_sample_pixel_dimensions,
    uv_rect_to_pil_crop_box,
)


def test_parse_uv_rect_json_string() -> None:
    r = parse_uv_rect('{"u0":0,"v0":0,"u1":0.5,"v1":1}')
    assert r is not None
    assert r == (0.0, 0.0, 0.5, 1.0)


def test_parse_uv_rect_swapped_corners_normalized() -> None:
    r = parse_uv_rect('{"u0":0.8,"v0":0.9,"u1":0.1,"v1":0.1}')
    assert r is not None
    assert r[0] <= r[2]
    assert r[1] <= r[3]


def test_uv_rect_to_pil_crop_box_vertical_flip() -> None:
    # Full-height stripe at bottom in UV (v0=0, v1=0.25) → bottom quarter of image.
    left, upper, right, lower = uv_rect_to_pil_crop_box(100, 40, (0.0, 0.0, 1.0, 0.25))
    assert left == 0
    assert right == 100
    assert upper == 30
    assert lower == 40


@pytest.mark.skipif(
    importlib.util.find_spec("PIL") is None,
    reason="PIL/Pillow required",
)
def test_texture_sample_pixel_dimensions_full_and_partial(tmp_path: Path) -> None:
    from PIL import Image

    path = tmp_path / "atlas.png"
    Image.new("RGBA", (240, 160), (10, 20, 30, 255)).save(path)
    assert texture_sample_pixel_dimensions(path, None) == (240, 160)
    # Center quarter in UV → 120×80 crop (matches uv_rect_to_pil_crop_box rounding)
    w, h = texture_sample_pixel_dimensions(path, (0.25, 0.25, 0.75, 0.75))
    left, upper, right, lower = uv_rect_to_pil_crop_box(240, 160, (0.25, 0.25, 0.75, 0.75))
    assert (w, h) == (right - left, lower - upper)


@pytest.mark.skipif(
    importlib.util.find_spec("PIL") is None,
    reason="PIL/Pillow required",
)
def test_texture_sample_pixel_dimensions_fallback_logs_missing_file(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Missing asset path must fall back to 128×128 and emit a WARNING (debuggability)."""
    missing = tmp_path / "does_not_exist.png"
    caplog.set_level(logging.WARNING, logger="src.materials.uv_atlas")
    assert texture_sample_pixel_dimensions(missing, None) == (128, 128)
    assert any("falling back to 128×128" in r.message for r in caplog.records)


def test_read_png_ihdr_dimensions_matches_pil(tmp_path: Path) -> None:
    from PIL import Image

    path = tmp_path / "x.png"
    Image.new("RGBA", (1536, 1024), (0, 0, 0, 255)).save(path)
    assert read_png_ihdr_dimensions(path) == (1536, 1024)


@pytest.mark.skipif(
    importlib.util.find_spec("PIL") is None,
    reason="PIL/Pillow required",
)
def test_texture_sample_pixel_dimensions_png_ihdr_fallback_when_pil_open_fails(tmp_path: Path) -> None:
    """Blender often has no Pillow; IHDR path must match PIL when Pillow breaks mid-read."""
    from PIL import Image

    path = tmp_path / "atlas.png"
    Image.new("RGBA", (240, 160), (10, 20, 30, 255)).save(path)
    with patch("PIL.Image.open", side_effect=OSError("simulate unreadable")):
        assert texture_sample_pixel_dimensions(path, None) == (240, 160)
        w, h = texture_sample_pixel_dimensions(path, (0.25, 0.25, 0.75, 0.75))
        left, upper, right, lower = uv_rect_to_pil_crop_box(240, 160, (0.25, 0.25, 0.75, 0.75))
        assert (w, h) == (right - left, lower - upper)


@pytest.mark.skipif(
    importlib.util.find_spec("PIL") is None,
    reason="PIL/Pillow required",
)
def test_texture_sample_pixel_dimensions_invariant_to_rect_position(tmp_path: Path) -> None:
    """Same UV span at different atlas positions → same raster size (rect-local canvas)."""
    from PIL import Image

    path = tmp_path / "atlas.png"
    Image.new("RGBA", (400, 200), (0, 0, 0, 255)).save(path)
    a = texture_sample_pixel_dimensions(path, (0.0, 0.0, 0.5, 0.5))
    b = texture_sample_pixel_dimensions(path, (0.5, 0.5, 1.0, 1.0))
    assert a == b

