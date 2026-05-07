"""Test gradient generator parameter validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.materials.pattern_texture_generators import checkerboard_texture_generator
from src.materials.png_encoding import write_rgba_float_png_top_first
from src.materials.uv_atlas import read_png_ihdr_dimensions


def test_write_rgba_float_png_top_first_writes_png_with_matching_ihdr(tmp_path: Path) -> None:
    w, h = 17, 11
    pixels = [0.5, 0.5, 0.5, 1.0] * (w * h)
    out = tmp_path / "rgba_top_first.png"
    write_rgba_float_png_top_first(out, w, h, pixels)
    assert read_png_ihdr_dimensions(out) == (w, h)


@pytest.mark.parametrize(
    "width,height,color_a,color_b,density,expected_error",
    [
        ("not_int", 512, "ff0000", "00ff00", 1.0, TypeError),
        (512, "not_int", "ff0000", "00ff00", 1.0, TypeError),
        (True, 512, "ff0000", "00ff00", 1.0, TypeError),
        (512, True, "ff0000", "00ff00", 1.0, TypeError),
        (-1, 512, "ff0000", "00ff00", 1.0, ValueError),
        (512, -1, "ff0000", "00ff00", 1.0, ValueError),
        (512, 512, "ff0000", "00ff00", "not_numeric", TypeError),
        (512, 512, "ff0000", "00ff00", True, TypeError),
        (512, 512, "ff0000", "00ff00", -1.0, ValueError),
        (512, 512, 123, "00ff00", 1.0, TypeError),
        (512, 512, "ff0000", 456, 1.0, TypeError),
    ],
)
def test_checkerboard_texture_generator_validates_parameters(
    width, height, color_a, color_b, density, expected_error
) -> None:
    with pytest.raises(expected_error):
        checkerboard_texture_generator(width, height, color_a, color_b, density)
