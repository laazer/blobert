"""Normalized UV rectangles (0–1) for sampling a sub-region of a texture atlas."""

from __future__ import annotations

import json
import logging
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)

# Minimum span so degenerate rects fall back to full image.
_MIN_UV_SPAN = 1e-4


def parse_uv_rect(raw: object) -> tuple[float, float, float, float] | None:
    """Parse ``uv_rect`` from schema (JSON string, dict, or list)."""
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            return None
        return _parse_uv_rect_mapping(data)
    if isinstance(raw, Mapping):
        return _parse_uv_rect_mapping(dict(raw))
    if isinstance(raw, (list, tuple)) and len(raw) >= 4:
        try:
            u0 = float(raw[0])
            v0 = float(raw[1])
            u1 = float(raw[2])
            v1 = float(raw[3])
        except (TypeError, ValueError):
            return None
        return _normalize_rect(u0, v0, u1, v1)
    return None


def _parse_uv_rect_mapping(data: dict[str, Any]) -> tuple[float, float, float, float] | None:
    # Support u0/v0/u1/v1 and legacy alias names
    try:
        u0 = float(data.get("u0", data.get("u_min", 0.0)))
        v0 = float(data.get("v0", data.get("v_min", 0.0)))
        u1 = float(data.get("u1", data.get("u_max", 1.0)))
        v1 = float(data.get("v1", data.get("v_max", 1.0)))
    except (TypeError, ValueError):
        return None
    return _normalize_rect(u0, v0, u1, v1)


def _normalize_rect(u0: float, v0: float, u1: float, v1: float) -> tuple[float, float, float, float] | None:
    if any(math.isnan(x) or math.isinf(x) for x in (u0, v0, u1, v1)):
        return None
    lo_u = max(0.0, min(1.0, min(u0, u1)))
    hi_u = max(0.0, min(1.0, max(u0, u1)))
    lo_v = max(0.0, min(1.0, min(v0, v1)))
    hi_v = max(0.0, min(1.0, max(v0, v1)))
    if hi_u - lo_u < _MIN_UV_SPAN or hi_v - lo_v < _MIN_UV_SPAN:
        return None
    return (lo_u, lo_v, hi_u, hi_v)


def is_full_uv_rect(uv: tuple[float, float, float, float] | None) -> bool:
    if uv is None:
        return True
    u0, v0, u1, v1 = uv
    return (
        abs(u0) < _MIN_UV_SPAN
        and abs(v0) < _MIN_UV_SPAN
        and abs(u1 - 1.0) < _MIN_UV_SPAN
        and abs(v1 - 1.0) < _MIN_UV_SPAN
    )


def mapping_scale_location_for_uv_rect(
    uv_rect: tuple[float, float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Blender Mapping node: ``output = location + scale * uv`` (rotation default)."""
    u0, v0, u1, v1 = uv_rect
    sx = max(u1 - u0, _MIN_UV_SPAN)
    sy = max(v1 - v0, _MIN_UV_SPAN)
    return (sx, sy, 1.0), (u0, v0, 0.0)


def read_png_ihdr_dimensions(path: Path) -> tuple[int, int]:
    """Return width, height from a PNG without Pillow (IHDR chunk only).

    Used when Blender's bundled Python has no Pillow but pipeline textures are PNG.
    """
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    if data[12:16] != b"IHDR":
        raise ValueError(f"missing IHDR: {path}")
    w = int.from_bytes(data[16:20], "big")
    h = int.from_bytes(data[20:24], "big")
    if w <= 0 or h <= 0:
        raise ValueError(f"invalid PNG dimensions: {path}")
    return w, h


def uv_rect_to_pil_crop_box(
    width: int,
    height: int,
    uv_rect: tuple[float, float, float, float],
) -> tuple[int, int, int, int]:
    """PIL crop box (left, upper, right, lower); UV origin bottom-left for v."""
    u0, v0, u1, v1 = uv_rect
    left = int(max(0, min(width, round(u0 * width))))
    right = int(max(0, min(width, round(u1 * width))))
    # v increases upward in UV; image y increases downward from top.
    upper = int(max(0, min(height, round((1.0 - v1) * height))))
    lower = int(max(0, min(height, round((1.0 - v0) * height))))
    if right <= left:
        right = min(width, left + 1)
    if lower <= upper:
        lower = min(height, upper + 1)
    return left, upper, right, lower


def _texture_full_image_pixel_size(asset_path: Path) -> tuple[int, int]:
    """Resolve full-atlas width×height; Pillow when available, else PNG IHDR (Blender-friendly)."""
    try:
        from PIL import Image

        with Image.open(asset_path) as im:
            return im.size
    except ModuleNotFoundError:
        if asset_path.suffix.lower() == ".png":
            return read_png_ihdr_dimensions(asset_path)
        raise
    except (OSError, ValueError, TypeError):
        if asset_path.suffix.lower() == ".png":
            return read_png_ihdr_dimensions(asset_path)
        raise


def texture_sample_pixel_dimensions(
    asset_path: Path,
    uv_rect: tuple[float, float, float, float] | None,
) -> tuple[int, int]:
    """Pixel size (width, height) of the atlas region selected by ``uv_rect``.

    Matches the crop used by ``crop_texture_asset_to_temp_png`` / ``resolved_asset_path_for_image_sampling``.
    For ``None`` or a full-image rect, returns the image's dimensions.

    Uses Pillow when importable; if Pillow is missing or fails to open the file but the asset is
    ``.png``, reads dimensions from the IHDR chunk so Blender's Python (often without Pillow) still
    gets correct crop sizes. On unrecoverable errors, returns ``(128, 128)`` as procedural fallback.
    """
    try:
        w, h = _texture_full_image_pixel_size(asset_path)
    except (ModuleNotFoundError, OSError, ValueError, TypeError) as exc:
        logger.warning(
            "texture_sample_pixel_dimensions: falling back to 128×128 for %s uv_rect=%r (%s: %s)",
            asset_path,
            uv_rect,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return (128, 128)
    if uv_rect is None or is_full_uv_rect(uv_rect):
        return (max(1, w), max(1, h))
    left, upper, right, lower = uv_rect_to_pil_crop_box(w, h, uv_rect)
    cw = max(1, right - left)
    ch = max(1, lower - upper)
    return (cw, ch)


def _crop_texture_asset_to_temp_png_blender(
    asset_path: Path,
    uv_rect: tuple[float, float, float, float],
) -> Path | None:
    """Crop using Blender's image API when Pillow is unavailable (Blender's bundled Python)."""
    try:
        import bpy  # type: ignore[import-not-found]

        from src.materials.gradient_generator import write_rgba_float_png_top_first
    except ImportError as exc:
        logger.warning(
            "crop_texture_asset_to_temp_png: Blender crop unavailable (%s); "
            "install Pillow in the project venv or use Blender with bpy + gradient_generator",
            exc,
        )
        return None

    try:
        img = bpy.data.images.load(filepath=str(asset_path.resolve()), check_existing=False)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        logger.warning(
            "crop_texture_asset_to_temp_png: bpy failed to load %s (%s: %s)",
            asset_path,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return None

    try:
        w, h = int(img.size[0]), int(img.size[1])
        box = uv_rect_to_pil_crop_box(w, h, uv_rect)
        left, upper, right, lower = box
        if right <= left or lower <= upper:
            logger.warning(
                "crop_texture_asset_to_temp_png (Blender): degenerate crop box for %s uv_rect=%r "
                "(left=%s upper=%s right=%s lower=%s)",
                asset_path,
                uv_rect,
                left,
                upper,
                right,
                lower,
            )
            return None

        cw, ch = right - left, lower - upper
        px = list(img.pixels)
        buf = [0.0] * (cw * ch * 4)
        for cy in range(ch):
            py = upper + cy
            by = h - 1 - py
            row_src_base = (by * w) * 4
            row_dst_base = (cy * cw) * 4
            for cx in range(cw):
                x = left + cx
                si = row_src_base + x * 4
                di = row_dst_base + cx * 4
                buf[di : di + 4] = px[si : si + 4]

        fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="blobert_atlas_bpy_")
        os.close(fd)
        out_path = Path(tmp_path)
        write_rgba_float_png_top_first(out_path, cw, ch, buf)
        return out_path
    finally:
        try:
            bpy.data.images.remove(img)
        except (RuntimeError, ReferenceError, TypeError):
            pass


def crop_texture_asset_to_temp_png(
    asset_path: Path,
    uv_rect: tuple[float, float, float, float],
) -> Path | None:
    """Write a cropped PNG to a temp file; return path or None if crop invalid."""
    try:
        from PIL import Image
    except ModuleNotFoundError:
        out = _crop_texture_asset_to_temp_png_blender(asset_path, uv_rect)
        if out is not None:
            return out
        logger.warning(
            "crop_texture_asset_to_temp_png: Pillow not installed and Blender crop failed for %s "
            "(uv_rect=%r); callers may fall back to the uncropped asset path",
            asset_path,
            uv_rect,
        )
        return None
    try:
        with Image.open(asset_path) as im:
            im = im.convert("RGBA")
            w, h = im.size
            box = uv_rect_to_pil_crop_box(w, h, uv_rect)
            left, upper, right, lower = box
            if right <= left or lower <= upper:
                logger.warning(
                    "crop_texture_asset_to_temp_png: degenerate crop box for %s uv_rect=%r "
                    "(left=%s upper=%s right=%s lower=%s)",
                    asset_path,
                    uv_rect,
                    left,
                    upper,
                    right,
                    lower,
                )
                return None
            cropped = im.crop((left, upper, right, lower))
            fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="blobert_atlas_")
            try:
                cropped.save(tmp_path, format="PNG")
            finally:
                os.close(fd)
            return Path(tmp_path)
    except (OSError, ValueError, TypeError) as exc:
        logger.warning(
            "crop_texture_asset_to_temp_png: failed for %s uv_rect=%r (%s: %s)",
            asset_path,
            uv_rect,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        return None


def resolved_asset_path_for_image_sampling(
    asset_path: Path,
    uv_rect: tuple[float, float, float, float] | None,
) -> Path:
    """Disk path to sample: original or a temp cropped PNG when ``uv_rect`` is set."""
    if uv_rect is None or is_full_uv_rect(uv_rect):
        return asset_path
    cropped = crop_texture_asset_to_temp_png(asset_path, uv_rect)
    return cropped if cropped is not None else asset_path
