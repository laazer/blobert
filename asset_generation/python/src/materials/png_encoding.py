"""PNG encoding helpers for material texture generators."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def crc32(data: bytes) -> int:
    """Compute CRC-32 for PNG chunks."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xEDB88320 if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def create_png(width: int, height: int, pixels: list[float]) -> bytes:
    """Create a minimal PNG from float pixels (0.0-1.0)."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_chunk = b"IHDR" + ihdr_data
    ihdr_crc = crc32(ihdr_chunk)

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
    idat_crc = crc32(idat_chunk)

    iend_crc = crc32(b"IEND")

    ihdr = struct.pack(">I", 13) + ihdr_chunk + struct.pack(">I", ihdr_crc)
    idat = struct.pack(">I", len(idat_data)) + idat_chunk + struct.pack(">I", idat_crc)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return signature + ihdr + idat + iend


def write_rgba_float_png_top_first(path: Path, width: int, height: int, pixels: list[float]) -> None:
    """Write a PNG from RGBA floats (0-1) in top-first row-major order."""
    path.write_bytes(create_png(width, height, pixels))
