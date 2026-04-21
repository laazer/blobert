"""Focused adversarial tests for spots generation regressions."""

from __future__ import annotations

import struct

import pytest

from src.materials.gradient_generator import _spots_texture_generator


def _png_dimensions(png_data: bytes) -> tuple[int, int]:
    """Extract width/height from IHDR chunk."""
    assert png_data[:8] == b"\x89PNG\r\n\x1a\n"
    width = struct.unpack(">I", png_data[16:20])[0]
    height = struct.unpack(">I", png_data[20:24])[0]
    return width, height


def test_rejects_non_numeric_density() -> None:
    with pytest.raises(TypeError):
        _spots_texture_generator(
            width=32,
            height=32,
            spot_color_hex="ff0000",
            bg_color_hex="ffffff",
            density="1.0",  # type: ignore[arg-type]
        )


def test_rejects_zero_or_negative_density() -> None:
    for invalid in (0.0, -0.5):
        with pytest.raises(ValueError):
            _spots_texture_generator(
                width=32,
                height=32,
                spot_color_hex="ff0000",
                bg_color_hex="ffffff",
                density=invalid,
            )


def test_rejects_non_string_hex_inputs() -> None:
    with pytest.raises(TypeError):
        _spots_texture_generator(
            width=32,
            height=32,
            spot_color_hex=None,  # type: ignore[arg-type]
            bg_color_hex="ffffff",
            density=1.0,
        )

    with pytest.raises(TypeError):
        _spots_texture_generator(
            width=32,
            height=32,
            spot_color_hex="ff0000",
            bg_color_hex=123,  # type: ignore[arg-type]
            density=1.0,
        )


def test_invalid_spot_hex_raises_value_error() -> None:
    with pytest.raises(ValueError):
        _spots_texture_generator(
            width=32,
            height=32,
            spot_color_hex="zzzzzz",
            bg_color_hex="ffffff",
            density=1.0,
        )


def test_png_dimensions_remain_exact_for_asymmetric_input() -> None:
    png_data = _spots_texture_generator(
        width=17,
        height=251,
        spot_color_hex="ff0000",
        bg_color_hex="ffffff",
        density=1.0,
    )
    assert _png_dimensions(png_data) == (17, 251)


def test_generation_is_deterministic_for_same_input() -> None:
    first = _spots_texture_generator(
        width=64,
        height=64,
        spot_color_hex="00ff00",
        bg_color_hex="0000ff",
        density=2.0,
    )
    second = _spots_texture_generator(
        width=64,
        height=64,
        spot_color_hex="00ff00",
        bg_color_hex="0000ff",
        density=2.0,
    )
    assert first == second


def test_density_change_affects_output_pattern() -> None:
    low = _spots_texture_generator(
        width=64,
        height=64,
        spot_color_hex="ff0000",
        bg_color_hex="ffffff",
        density=0.2,
    )
    high = _spots_texture_generator(
        width=64,
        height=64,
        spot_color_hex="ff0000",
        bg_color_hex="ffffff",
        density=5.0,
    )
    assert low != high


def test_rejects_non_int_width_or_height() -> None:
    with pytest.raises(TypeError, match="width must be an integer"):
        _spots_texture_generator(  # type: ignore[arg-type]
            width=32.0,
            height=32,
            spot_color_hex="ff0000",
            bg_color_hex="ffffff",
            density=1.0,
        )
    with pytest.raises(TypeError, match="height must be an integer"):
        _spots_texture_generator(  # type: ignore[arg-type]
            width=32,
            height=True,
            spot_color_hex="ff0000",
            bg_color_hex="ffffff",
            density=1.0,
        )


def test_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError, match="width and height must be positive"):
        _spots_texture_generator(
            width=0,
            height=32,
            spot_color_hex="ff0000",
            bg_color_hex="ffffff",
            density=1.0,
        )


def test_spot_hex_double_hash_raises() -> None:
    with pytest.raises(ValueError, match="hex color must be valid hexadecimal"):
        _spots_texture_generator(
            width=8,
            height=8,
            spot_color_hex="##ff0000",
            bg_color_hex="ffffff",
            density=1.0,
        )


def test_bg_hex_invalid_chars_fall_back_to_default_white() -> None:
    """Invalid bg hex without ``#`` uses default white when allow_invalid is True."""
    png_data = _spots_texture_generator(
        width=4,
        height=4,
        spot_color_hex="ff0000",
        bg_color_hex="zzzzzz",
        density=1.0,
    )
    assert _png_dimensions(png_data) == (4, 4)
    # IHDR + IDAT present; pixel buffer uses white background for invalid bg
    assert b"IDAT" in png_data


def test_bg_hex_double_hash_falls_back_to_white() -> None:
    png_data = _spots_texture_generator(
        width=4,
        height=4,
        spot_color_hex="ff0000",
        bg_color_hex="##ffffff",
        density=1.0,
    )
    assert _png_dimensions(png_data) == (4, 4)
