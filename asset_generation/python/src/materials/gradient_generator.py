"""
Gradient texture generation for animated enemies
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import cast

import bpy  # type: ignore[import-not-found]

from . import png_encoding as _png_encoding


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


def gradient_image_pixel_buffer(
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


def sanitize_image_label(label: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9_]+", "_", str(label or "gradient").strip())
    return (raw[:48] or "gradient").lstrip("_") or "gradient"


def _create_png(width: int, height: int, pixels: list[float]) -> bytes:
    """Compatibility shim for callers importing from this module."""
    return cast(bytes, _png_encoding.create_png(width, height, pixels))


def write_rgba_buffer_to_gradients_png(
    width: int,
    height: int,
    pixels: list[float],
    img_name: str,
) -> Path:
    """Write RGBA float buffer (Blender ``Image.pixels`` layout) to ``animated_exports/gradients``."""
    png_data = _create_png(width, height, pixels)
    gradient_dir = Path(__file__).parent.parent.parent / "animated_exports" / "gradients"
    gradient_dir.mkdir(parents=True, exist_ok=True)
    safe = sanitize_image_label(img_name)
    path = gradient_dir / f"{safe}.png"
    path.write_bytes(png_data)
    return path


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
    img = bpy.data.images.load(filepath=img_path, check_existing=False)
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

