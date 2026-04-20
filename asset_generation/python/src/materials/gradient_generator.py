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


def _normalize_stripe_preset(raw: str) -> str:
    """Map API / legacy values to ``beachball`` / ``doplar`` / ``swirl``."""
    a = str(raw or "beachball").strip().lower()
    if a in ("x", "beachball", "vertical"):
        return "beachball"
    if a in ("y", "doplar", "horizontal"):
        return "doplar"
    if a in ("z", "swirl"):
        return "swirl"
    if a in ("beachball", "doplar", "swirl"):
        return a
    return "beachball"


def _euler_rotate_uv_xy(
    u: float, v: float, rot_x_deg: float, rot_y_deg: float, rot_z_deg: float
) -> tuple[float, float]:
    """Apply ``Rz * Ry * Rx`` to centered UV (third component 0), return new UV in [0,1]²."""
    px = u - 0.5
    py = v - 0.5
    pz = 0.0
    rx = math.radians(float(rot_x_deg))
    ry = math.radians(float(rot_y_deg))
    rz = math.radians(float(rot_z_deg))
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    x1, y1, z1 = px, py * cx - pz * sx, py * sx + pz * cx
    x2, y2 = x1 * cy + z1 * sy, y1
    x3, y3 = x2 * cz - y2 * sz, x2 * sz + y2 * cz
    return x3 + 0.5, y3 + 0.5


def _stripe_uv_coord_for_preset(u: float, v: float, preset: str) -> float:
    """Phase coordinate for stripe bands: beachball / doplar / swirl base angles in UV."""
    p = _normalize_stripe_preset(preset)
    if p == "beachball":
        theta = 0.0
    elif p == "doplar":
        theta = math.pi / 2.0
    else:
        theta = math.pi / 4.0
    return u * math.cos(theta) + v * math.sin(theta)


def _stripes_texture_generator(
    width: int,
    height: int,
    stripe_color_hex: str,
    bg_color_hex: str,
    stripe_width: float,
    stripe_preset: str = "beachball",
    rot_x_deg: float = 0.0,
    rot_y_deg: float = 0.0,
    rot_z_deg: float = 0.0,
) -> bytes:
    """Generate PNG with stripe pattern (half period stripe, half gap).

    ``stripe_width`` is the period in normalized UV space (0.05–1.0). ``stripe_preset``
    picks beachball / doplar / swirl phase axes; Euler rotations (degrees) tilt UV first.
    """
    def _hex_to_rgba(
        hex_str: str,
        default_rgba: tuple[float, float, float, float],
        allow_invalid: bool = False,
    ) -> tuple[float, float, float, float]:
        h = (hex_str or "").strip().lstrip("#").lower()
        if not h:
            return default_rgba
        if len(h) != 6:
            if allow_invalid:
                return default_rgba
            raise ValueError(f"hex color must be 6 characters (RRGGBB), got {h!r}")
        try:
            r = int(h[0:2], 16) / 255.0
            g = int(h[2:4], 16) / 255.0
            b = int(h[4:6], 16) / 255.0
            return (r, g, b, 1.0)
        except ValueError as e:
            if allow_invalid:
                return default_rgba
            raise ValueError("hex color must be valid hexadecimal") from e

    stripe_rgba = _hex_to_rgba(stripe_color_hex, (0.0, 0.0, 0.0, 1.0), allow_invalid=False)
    bg_rgba = _hex_to_rgba(bg_color_hex, (1.0, 1.0, 1.0, 1.0), allow_invalid=True)

    period = max(0.05, min(1.0, float(stripe_width)))
    preset = _normalize_stripe_preset(stripe_preset)

    buf = [0.0] * (width * height * 4)
    for y in range(height):
        for x in range(width):
            u = (x + 0.5) / width if width > 0 else 0.5
            v = (y + 0.5) / height if height > 0 else 0.5
            u2, v2 = _euler_rotate_uv_xy(u, v, rot_x_deg, rot_y_deg, rot_z_deg)
            coord = _stripe_uv_coord_for_preset(u2, v2, preset)
            edge = coord * (1.0 / period)
            t = edge - math.floor(edge)
            rgba = stripe_rgba if t < 0.5 else bg_rgba
            idx = (y * width + x) * 4
            buf[idx] = rgba[0]
            buf[idx + 1] = rgba[1]
            buf[idx + 2] = rgba[2]
            buf[idx + 3] = rgba[3]

    return _create_png(width, height, buf)


def create_stripes_png_and_load(
    width: int,
    height: int,
    stripe_color_hex: str,
    bg_color_hex: str,
    stripe_width: float,
    img_name: str,
    stripe_preset: str = "beachball",
    rot_x_deg: float = 0.0,
    rot_y_deg: float = 0.0,
    rot_z_deg: float = 0.0,
) -> bpy.types.Image:
    """Create stripes PNG texture, save to disk, and load into Blender."""
    png_data = _stripes_texture_generator(
        width,
        height,
        stripe_color_hex,
        bg_color_hex,
        stripe_width,
        stripe_preset=stripe_preset,
        rot_x_deg=rot_x_deg,
        rot_y_deg=rot_y_deg,
        rot_z_deg=rot_z_deg,
    )
    stripes_dir = Path(__file__).parent.parent.parent / "animated_exports" / "stripes"
    stripes_dir.mkdir(parents=True, exist_ok=True)
    tmp_png = stripes_dir / f"{img_name}.png"
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


def _spots_texture_generator(
    width: int,
    height: int,
    spot_color_hex: str,
    bg_color_hex: str,
    density: float,
    spot_pattern: str = "grid",
) -> bytes:
    """Generate PNG with procedural spot pattern.

    Args:
        width: PNG width in pixels
        height: PNG height in pixels
        spot_color_hex: Hex color string for spots (e.g., "ff0000"). Empty defaults to black.
        bg_color_hex: Hex color string for background (e.g., "ffffff"). Empty defaults to white.
        density: Frequency of spots, range 0.1–5.0. Higher = more spots, smaller size.

    Returns:
        PNG-encoded bytes with correct CRC-32 checksums.

    Raises:
        ValueError: If spot_color_hex is non-empty and invalid.
    """
    def _hex_to_rgba(hex_str: str, default_rgba: tuple[float, float, float, float], allow_invalid: bool = False) -> tuple[float, float, float, float]:
        """Parse 6-char hex string to RGBA or return default.

        Args:
            hex_str: Hex color string
            default_rgba: Fallback color if string is empty
            allow_invalid: If False, raise ValueError for invalid non-empty strings

        Returns:
            RGBA tuple
        """
        h = (hex_str or "").strip().lstrip("#").lower()
        if not h:
            return default_rgba
        if len(h) != 6:
            if allow_invalid:
                return default_rgba
            raise ValueError(f"hex color must be 6 characters (RRGGBB), got {h!r}")
        try:
            r = int(h[0:2], 16) / 255.0
            g = int(h[2:4], 16) / 255.0
            b = int(h[4:6], 16) / 255.0
            return (r, g, b, 1.0)
        except ValueError as e:
            if allow_invalid:
                return default_rgba
            raise ValueError("hex color must be valid hexadecimal") from e

    # Parse colors - spot color can raise ValueError if non-empty and invalid
    spot_rgba = _hex_to_rgba(spot_color_hex, (0.0, 0.0, 0.0, 1.0), allow_invalid=False)
    # Background color defaults to white if invalid
    bg_rgba = _hex_to_rgba(bg_color_hex, (1.0, 1.0, 1.0, 1.0), allow_invalid=True)

    # Build pixel buffer (bottom-row-first, Blender convention)
    buf = [0.0] * (width * height * 4)

    # Linear grid scaling: density controls number of spot grid divisions per unit
    # density=0.1: 0.1 divisions (1 huge spot)
    # density=1.0: 1 division (1 baseline spot)
    # density=5.0: 5 divisions (5x5 = 25 spots)
    # For fractional densities < 1, we still get sparse spots by making them bigger
    grid_scale = max(0.1, float(density))  # Allow fractional divisions
    spot_radius = 0.35  # In normalized UV space per grid cell
    pat = str(spot_pattern or "grid").strip().lower()
    if pat not in ("grid", "hex"):
        pat = "grid"

    for y in range(height):
        for x in range(width):
            # Normalized UV coordinates
            u = (x + 0.5) / width if width > 0 else 0.5
            v = (y + 0.5) / height if height > 0 else 0.5

            # Scale by density; optional brick offset for hex-like staggered rows
            v_scaled = v * grid_scale
            row = math.floor(v_scaled)
            if pat == "hex":
                u_scaled = u * grid_scale + (row % 2) * 0.5
                u_fract = u_scaled - math.floor(u_scaled)
                v_fract = v_scaled - row
            else:
                u_scaled = u * grid_scale
                u_fract = u_scaled - math.floor(u_scaled)
                v_fract = v_scaled - math.floor(v_scaled)

            # Distance from cell center (0.5, 0.5)
            du = u_fract - 0.5
            dv = v_fract - 0.5
            distance = math.sqrt(du * du + dv * dv)

            # Choose spot or background color
            if distance < spot_radius:
                rgba = spot_rgba
            else:
                rgba = bg_rgba

            # Store in buffer
            idx = (y * width + x) * 4
            buf[idx] = rgba[0]
            buf[idx + 1] = rgba[1]
            buf[idx + 2] = rgba[2]
            buf[idx + 3] = rgba[3]

    return _create_png(width, height, buf)


def create_spots_png_and_load(
    width: int,
    height: int,
    spot_color_hex: str,
    bg_color_hex: str,
    density: float,
    img_name: str,
    spot_pattern: str = "grid",
) -> bpy.types.Image:
    """Create spots PNG texture, save to disk, and load into Blender.

    Args:
        width: PNG width
        height: PNG height
        spot_color_hex: Hex color for spots
        bg_color_hex: Hex color for background
        density: Spot frequency (0.1–5.0)
        img_name: Image name (will be sanitized and prefixed)

    Returns:
        Loaded Blender Image object.
    """
    png_data = _spots_texture_generator(
        width, height, spot_color_hex, bg_color_hex, density, spot_pattern=spot_pattern
    )
    spots_dir = Path(__file__).parent.parent.parent / "animated_exports" / "spots"
    spots_dir.mkdir(parents=True, exist_ok=True)
    tmp_png = spots_dir / f"{img_name}.png"
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
