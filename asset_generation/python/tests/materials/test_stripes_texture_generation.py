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

    def test_presets_beachball_doplar_swirl_produce_distinct_output(self) -> None:
        base = dict(
            width=48,
            height=48,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.25,
        )
        pb = _stripes_texture_generator(**base, stripe_preset="beachball")
        pd = _stripes_texture_generator(**base, stripe_preset="doplar")
        ps = _stripes_texture_generator(**base, stripe_preset="swirl")
        assert pb != pd
        assert pb != ps
        assert pd != ps

    def test_discrete_yaw_rotations_produce_different_textures(self) -> None:
        """Different 90° multiple rotations (0°, 90°, 180°, 270°) should produce different textures."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            stripe_preset="beachball",
        )
        tex_0 = _stripes_texture_generator(**base, rot_y_deg=0.0)
        tex_90 = _stripes_texture_generator(**base, rot_y_deg=90.0)
        tex_180 = _stripes_texture_generator(**base, rot_y_deg=180.0)
        tex_270 = _stripes_texture_generator(**base, rot_y_deg=270.0)

        # Each 90° multiple rotation should produce a different texture
        assert tex_0 != tex_90, "0° and 90° should be different"
        assert tex_90 != tex_180, "90° and 180° should be different"
        assert tex_180 != tex_270, "180° and 270° should be different"
        assert tex_270 != tex_0, "270° and 0° should be different"

    def test_non_discrete_angles_round_to_nearest_90_multiple(self) -> None:
        """Non-discrete angles should round to nearest 90° multiple."""
        base = dict(
            width=32,
            height=32,
            stripe_color_hex="ff0000",
            bg_color_hex="ffffff",
            stripe_width=0.4,
            stripe_preset="beachball",
        )
        # 30° and 45° should both round to 0°
        tex_30 = _stripes_texture_generator(**base, rot_y_deg=30.0)
        tex_45 = _stripes_texture_generator(**base, rot_y_deg=45.0)
        # 50° and 60° should both round to 90°
        tex_50 = _stripes_texture_generator(**base, rot_y_deg=50.0)
        tex_60 = _stripes_texture_generator(**base, rot_y_deg=60.0)
        tex_0 = _stripes_texture_generator(**base, rot_y_deg=0.0)
        tex_90 = _stripes_texture_generator(**base, rot_y_deg=90.0)

        assert tex_30 == tex_45 == tex_0, "30° and 45° should both round to 0°"
        assert tex_50 == tex_60 == tex_90, "50° and 60° should both round to 90°"

    def test_legacy_horizontal_vertical_map_to_presets(self) -> None:
        a = _stripes_texture_generator(
            32, 32, "ff0000", "ffffff", 0.4, stripe_preset="horizontal"
        )
        b = _stripes_texture_generator(32, 32, "ff0000", "ffffff", 0.4, stripe_preset="doplar")
        assert a == b
        c = _stripes_texture_generator(
            32, 32, "ff0000", "ffffff", 0.4, stripe_preset="vertical"
        )
        d = _stripes_texture_generator(32, 32, "ff0000", "ffffff", 0.4, stripe_preset="beachball")
        assert c == d

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
