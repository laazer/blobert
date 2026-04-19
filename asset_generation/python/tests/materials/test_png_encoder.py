"""Unit tests for PNG encoder function in material_system."""

from __future__ import annotations

from src.materials.gradient_generator import _create_png

from .gradient_glb_utils import png_histogram


def test_png_encoder_creates_valid_png() -> None:
    """PNG encoder should produce valid PNG files."""
    pixels = [1.0, 0.0, 0.0, 1.0] * 4
    png_data = _create_png(2, 2, pixels)

    assert png_data[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature should be correct"
    assert len(png_data) > 50, "PNG should have content"


def test_png_encoder_preserves_gradient_colors() -> None:
    """PNG encoder should produce non-black gradients."""
    width, height = 256, 4
    pixels = []
    for y in range(height):
        for x in range(width):
            t = x / (width - 1)
            r = (1.0 - t) + t * 0.0
            g = (1.0 - t) * 0.0 + t * 0.0
            b = (1.0 - t) * 0.0 + t * 1.0
            a = 1.0
            pixels.extend([r, g, b, a])

    png_data = _create_png(width, height, pixels)
    max_r, max_g, max_b = png_histogram(png_data)

    assert max_r > 200, f"Red channel should be bright in red-to-blue gradient, got {max_r}"
    assert max_b > 200, f"Blue channel should be bright in red-to-blue gradient, got {max_b}"


def test_png_encoder_black_gradient_is_black() -> None:
    """PNG encoder should produce black pixels for zero values."""
    pixels = [0.0, 0.0, 0.0, 1.0] * 4
    png_data = _create_png(2, 2, pixels)
    max_r, max_g, max_b = png_histogram(png_data)

    assert max(max_r, max_g, max_b) <= 2, "All-zero gradient should be black"
