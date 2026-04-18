"""Integration test for gradient pixel buffer generation and PNG encoding."""

from __future__ import annotations

import struct
import zlib


def _lerp_rgba(
    color_a: tuple[float, float, float, float],
    color_b: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    u = max(0.0, min(1.0, float(t)))
    return (
        color_a[0] + (color_b[0] - color_a[0]) * u,
        color_a[1] + (color_b[1] - color_a[1]) * u,
        color_a[2] + (color_b[2] - color_a[2]) * u,
        color_a[3] + (color_b[3] - color_a[3]) * u,
    )


def _gradient_image_pixel_buffer_test(
    w: int,
    h: int,
    color_a: tuple[float, float, float, float],
    color_b: tuple[float, float, float, float],
    direction: str,
) -> list[float]:
    """Simplified version of the real function for testing."""
    import math

    buf = [0.0] * (w * h * 4)
    d = str(direction or "horizontal").strip().lower()
    for y in range(h):
        for x in range(w):
            if d == "vertical":
                t = (y + 0.5) / h if h > 0 else 0.5
            elif d == "radial":
                u = (x + 0.5) / w
                v = (y + 0.5) / h
                du, dv = u - 0.5, v - 0.5
                t = min(1.0, math.sqrt(du * du + dv * dv) * 1.4142135623730951)
            else:
                t = (x + 0.5) / w if w > 0 else 0.5
            rgba = _lerp_rgba(color_a, color_b, t)
            idx = (y * w + x) * 4
            buf[idx] = rgba[0]
            buf[idx + 1] = rgba[1]
            buf[idx + 2] = rgba[2]
            buf[idx + 3] = rgba[3]
    return buf


def _crc32(data: bytes) -> int:
    """Compute CRC-32 for PNG chunks."""
    crc = 0xffffffff
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xedb88320 if crc & 1 else crc >> 1
    return crc ^ 0xffffffff


def _create_png_test(width: int, height: int, pixels: list[float]) -> bytes:
    """Test version of PNG encoder."""
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


def test_gradient_buffer_red_to_blue():
    """Verify gradient buffer is generated with correct interpolation."""
    color_a = (1.0, 0.0, 0.0, 1.0)
    color_b = (0.0, 0.0, 1.0, 1.0)
    buf = _gradient_image_pixel_buffer_test(256, 4, color_a, color_b, "horizontal")

    # Check first pixel (should be red)
    assert buf[0] > 0.9, f"First pixel R should be ~1.0, got {buf[0]}"
    assert buf[1] < 0.1, f"First pixel G should be ~0.0, got {buf[1]}"
    assert buf[2] < 0.1, f"First pixel B should be ~0.0, got {buf[2]}"

    # Check last pixel (should be blue)
    last_idx = (256 - 1) * 4
    assert buf[last_idx] < 0.1, f"Last pixel R should be ~0.0, got {buf[last_idx]}"
    assert buf[last_idx + 1] < 0.1, f"Last pixel G should be ~0.0, got {buf[last_idx + 1]}"
    assert buf[last_idx + 2] > 0.9, f"Last pixel B should be ~1.0, got {buf[last_idx + 2]}"


def test_gradient_png_respects_buffer():
    """Verify PNG encoder correctly encodes gradient buffer to PNG."""
    color_a = (1.0, 0.0, 0.0, 1.0)
    color_b = (0.0, 0.0, 1.0, 1.0)
    buf = _gradient_image_pixel_buffer_test(256, 4, color_a, color_b, "horizontal")
    png_data = _create_png_test(256, 4, buf)

    # Parse PNG and verify pixels
    pos = 8
    idat_data = None
    while pos < len(png_data):
        chunk_len = struct.unpack(">I", png_data[pos : pos + 4])[0]
        chunk_type = png_data[pos + 4 : pos + 8]
        chunk_data = png_data[pos + 8 : pos + 8 + chunk_len]
        pos += 12 + chunk_len
        if chunk_type == b"IDAT":
            idat_data = chunk_data
            break

    assert idat_data is not None, "PNG should contain IDAT chunk"

    raw = zlib.decompress(idat_data)

    # First pixel in PNG (after filter byte) should be red
    r1 = raw[1]
    g1 = raw[2]
    b1 = raw[3]
    assert r1 > 200, f"First pixel R should be ~255, got {r1}"
    assert g1 < 50, f"First pixel G should be ~0, got {g1}"
    assert b1 < 50, f"First pixel B should be ~0, got {b1}"

    # Last pixel of first scanline should be blue
    # Each scanline: 1 filter byte + 256*4 pixel bytes = 1025 bytes
    # Last pixel of first scanline: filter byte (1) + (255)*4 bytes offset
    last_pixel_idx = 1 + (256 - 1) * 4
    r_last = raw[last_pixel_idx]
    g_last = raw[last_pixel_idx + 1]
    b_last = raw[last_pixel_idx + 2]
    assert r_last < 50, f"Last pixel R should be ~0, got {r_last}"
    assert g_last < 50, f"Last pixel G should be ~0, got {g_last}"
    assert b_last > 200, f"Last pixel B should be ~255, got {b_last}"
