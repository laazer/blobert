"""Unit tests for stripes texture generation."""

from __future__ import annotations

import struct

import pytest

from src.materials.gradient_generator import _crc32, _stripes_texture_generator


class TestStripesTextureGenerator:
    def test_returns_valid_png_bytes(self) -> None:
        png_data = _stripes_texture_generator(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.5,
        )
        assert isinstance(png_data, bytes)
        assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_output_dimensions_match_input(self) -> None:
        for width, height in [(32, 32), (64, 128), (1, 1)]:
            png_data = _stripes_texture_generator(
                width=width,
                height=height,
                stripe_color_hex="ff0000",
                bg_color_hex="ffffff",
                stripe_width=0.5,
            )
            ihdr_width = struct.unpack(">I", png_data[16:20])[0]
            ihdr_height = struct.unpack(">I", png_data[20:24])[0]
            assert ihdr_width == width
            assert ihdr_height == height

    def test_invalid_hex_raises(self) -> None:
        with pytest.raises(ValueError):
            _stripes_texture_generator(
                width=8,
                height=8,
                stripe_color_hex="zzzzzz",
                bg_color_hex="ffffff",
                stripe_width=0.5,
            )

    def test_two_periods_produce_different_output(self) -> None:
        a = _stripes_texture_generator(
            64, 8, "ff0000", "ffffff", 0.2
        )
        b = _stripes_texture_generator(
            64, 8, "ff0000", "ffffff", 0.9
        )
        assert a != b

    def test_crc32_ihdr_valid(self) -> None:
        png_data = _stripes_texture_generator(
            32, 32, "ff0000", "ffffff", 0.5
        )
        ihdr_data = png_data[16:29]
        ihdr_chunk = b"IHDR" + ihdr_data
        stored_crc = struct.unpack(">I", png_data[29:33])[0]
        assert stored_crc == _crc32(ihdr_chunk)

    def test_crc32_idat_valid(self) -> None:
        png_data = _stripes_texture_generator(
            32, 32, "ff0000", "ffffff", 0.5
        )
        pos = 33
        while pos < len(png_data):
            length = struct.unpack(">I", png_data[pos : pos + 4])[0]
            chunk_type = png_data[pos + 4 : pos + 8]
            if chunk_type == b"IDAT":
                idat_data = png_data[pos + 8 : pos + 8 + length]
                idat_chunk = b"IDAT" + idat_data
                stored_crc = struct.unpack(">I", png_data[pos + 8 + length : pos + 12 + length])[0]
                assert stored_crc == _crc32(idat_chunk)
                return
            pos += 12 + length
        pytest.fail("IDAT chunk not found")


def test_create_stripes_png_and_load_exists() -> None:
    from src.materials import gradient_generator as gg

    assert hasattr(gg, "create_stripes_png_and_load")
