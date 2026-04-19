"""
Gradient texture generation for animated enemies
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

import bpy


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


def _gradient_image_pixel_buffer(
    w: int,
    h: int,
    color_a: tuple[float, float, float, float],
    color_b: tuple[float, float, float, float],
    direction: str,
) -> list[float]:
    """RGBA for ``Image.pixels`` — bottom row first (Blender layout)."""
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


def _sanitize_image_label(label: str) -> str:
    import re
    raw = re.sub(r"[^a-zA-Z0-9_]+", "_", str(label or "gradient").strip())
    return (raw[:48] or "gradient").lstrip("_") or "gradient"


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


def create_gradient_png_and_load(
    width: int,
    height: int,
    pixels: list[float],
    img_name: str,
) -> bpy.types.Image:
    """Create PNG from pixel buffer, save to disk, and load into Blender."""
    png_data = _create_png(width, height, pixels)
    gradient_dir = Path(__file__).parent.parent.parent / "animated_exports" / "gradients"
    gradient_dir.mkdir(parents=True, exist_ok=True)
    tmp_png = gradient_dir / f"{img_name}.png"
    tmp_png.write_bytes(png_data)

    img_path = str(tmp_png.absolute())
    img = bpy.data.images.load(filepath=img_path)
    img.name = img_name

    try:
        img.colorspace_settings.name = "sRGB"
    except (TypeError, AttributeError):  # pragma: no cover
        pass

    try:
        img.pack()
    except Exception:  # pragma: no cover
        pass

    return img
