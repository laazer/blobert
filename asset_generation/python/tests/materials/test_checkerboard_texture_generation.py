"""Unit tests for checkerboard texture generation."""

from __future__ import annotations

import struct

import pytest

from src.materials.gradient_generator import checkerboard_texture_generator


def test_checkerboard_texture_generator_returns_valid_png() -> None:
    png_data = checkerboard_texture_generator(
        width=32,
        height=32,
        color_a_hex="000000",
        color_b_hex="ffffff",
        density=2.0,
    )
    assert isinstance(png_data, bytes)
    assert png_data[:8] == b"\x89PNG\r\n\x1a\n"


def test_checkerboard_texture_generator_dimensions_match_inputs() -> None:
    png_data = checkerboard_texture_generator(
        width=64,
        height=16,
        color_a_hex="000000",
        color_b_hex="ffffff",
        density=1.0,
    )
    ihdr_width = struct.unpack(">I", png_data[16:20])[0]
    ihdr_height = struct.unpack(">I", png_data[20:24])[0]
    assert ihdr_width == 64
    assert ihdr_height == 16


def test_checkerboard_density_changes_output() -> None:
    low = checkerboard_texture_generator(
        width=64,
        height=64,
        color_a_hex="ff0000",
        color_b_hex="00ff00",
        density=1.0,
    )
    high = checkerboard_texture_generator(
        width=64,
        height=64,
        color_a_hex="ff0000",
        color_b_hex="00ff00",
        density=4.0,
    )
    assert low != high


def test_checkerboard_rejects_non_positive_density() -> None:
    with pytest.raises(ValueError, match="density must be greater than 0"):
        checkerboard_texture_generator(
            width=16,
            height=16,
            color_a_hex="000000",
            color_b_hex="ffffff",
            density=0.0,
        )
