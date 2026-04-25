"""Test gradient generator parameter validation."""

from __future__ import annotations

import pytest

from src.materials.gradient_generator import checkerboard_texture_generator


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
