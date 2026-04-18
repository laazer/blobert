"""Unit tests for PNG encoder function in material_system."""

from __future__ import annotations

import struct
import zlib

from .gradient_glb_utils import png_histogram


def _crc32(data: bytes) -> int:
    """Compute CRC-32 for PNG chunks."""
    crc = 0xffffffff
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xedb88320 if crc & 1 else crc >> 1
    return crc ^ 0xffffffff


def _create_png(width: int, height: int, pixels: list[float]) -> bytes:
    """Create a minimal PNG from float pixels (0.0-1.0)."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_chunk = b"IHDR" + ihdr_data
    ihdr_crc = _crc32(ihdr_chunk)

    scanlines = b""
    for y in range(height):
        scanlines += b"\x00"
        for x in range(width):
            idx = (y * width + x) * 4
            r = max(0, min(255, int(pixels[idx] * 255)))
            g = max(0, min(255, int(pixels[idx + 1] * 255)))
            b = max(0, min(255, int(pixels[idx + 2] * 255)))
            a = max(0, min(255, int(pixels[idx + 3] * 255)))
            scanlines += bytes([r, g, b, a])

    idat_data = zlib.compress(scanlines, 9)
    idat_chunk = b"IDAT" + idat_data
    idat_crc = _crc32(idat_chunk)

    iend_crc = _crc32(b"IEND")

    ihdr = struct.pack(">I", 13) + ihdr_chunk + struct.pack(">I", ihdr_crc)
    idat = struct.pack(">I", len(idat_data)) + idat_chunk + struct.pack(">I", idat_crc)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return signature + ihdr + idat + iend


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
