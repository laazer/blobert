"""Tests for atlas UV rectangle parsing and PIL crop box."""

from __future__ import annotations

from src.materials.uv_atlas import (
    parse_uv_rect,
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

