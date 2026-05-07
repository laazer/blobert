"""Procedural non-gradient texture generators (stripes, spots, checkerboard)."""

from __future__ import annotations

import math
from pathlib import Path

import bpy  # type: ignore[import-not-found]

from .color_utils import hex_to_rgba
from .png_encoding import create_png


def _normalize_stripe_preset(raw: str) -> str:
    """Map API / legacy values to ``beachball`` / ``doplar`` / ``swirl``."""
    alias = str(raw or "beachball").strip().lower()
    if alias in ("x", "beachball", "vertical"):
        return "beachball"
    if alias in ("y", "doplar", "horizontal"):
        return "doplar"
    if alias in ("z", "swirl"):
        return "swirl"
    if alias in ("beachball", "doplar", "swirl"):
        return alias
    return "beachball"


def _stripe_uv_coord_for_preset(
    u: float,
    v: float,
    preset: str,
    rot_y_deg: float = 0.0,
    rot_x_deg: float = 0.0,
    rot_z_deg: float = 0.0,
    phase_offset: float = 0.0,
) -> float:
    """Phase coordinate for stripe bands via directional UV projection."""
    normalized_preset = _normalize_stripe_preset(preset)

    if normalized_preset == "beachball":
        base_angle_deg = 0.0
    elif normalized_preset == "doplar":
        base_angle_deg = 90.0
    else:  # swirl
        base_angle_deg = 60.0

    final_angle_rad = math.radians(base_angle_deg + float(rot_y_deg))
    dir_x = math.cos(final_angle_rad)
    dir_y = math.sin(final_angle_rad)

    u_center = u - 0.5
    v_center = v - 0.5

    pitch_scale = math.cos(math.radians(float(rot_x_deg)))
    v_center *= pitch_scale

    coord = (u_center * dir_x) + (v_center * dir_y)
    roll_phase = float(rot_z_deg) / 360.0
    return coord + phase_offset + roll_phase


def stripes_texture_generator(
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
    """Generate PNG with stripe pattern (half period stripe, half gap)."""
    if not isinstance(width, int) or isinstance(width, bool):
        raise TypeError("width must be an integer")
    if not isinstance(height, int) or isinstance(height, bool):
        raise TypeError("height must be an integer")
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if not isinstance(stripe_width, (int, float)) or isinstance(stripe_width, bool):
        raise TypeError("stripe_width must be numeric")
    if not isinstance(stripe_color_hex, str):
        raise TypeError("stripe_color_hex must be a string")
    if not isinstance(bg_color_hex, str):
        raise TypeError("bg_color_hex must be a string")

    stripe_rgba = hex_to_rgba(stripe_color_hex, (0.0, 0.0, 0.0, 1.0), allow_invalid=False)
    bg_rgba = hex_to_rgba(bg_color_hex, (1.0, 1.0, 1.0, 1.0), allow_invalid=True)

    period = max(0.05, min(1.0, float(stripe_width)))
    preset = _normalize_stripe_preset(stripe_preset)

    buf = [0.0] * (width * height * 4)

    for y in range(height):
        for x in range(width):
            u = (x + 0.5) / width if width > 0 else 0.5
            v = (y + 0.5) / height if height > 0 else 0.5
            coord = _stripe_uv_coord_for_preset(
                u,
                v,
                preset,
                rot_y_deg=rot_y_deg,
                rot_x_deg=rot_x_deg,
                rot_z_deg=rot_z_deg,
                phase_offset=0.0,
            )
            edge = coord * (1.0 / period)
            t = edge - math.floor(edge)
            rgba = stripe_rgba if t < 0.5 else bg_rgba
            idx = (y * width + x) * 4
            buf[idx] = rgba[0]
            buf[idx + 1] = rgba[1]
            buf[idx + 2] = rgba[2]
            buf[idx + 3] = rgba[3]

    return create_png(width, height, buf)


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
    png_data = stripes_texture_generator(
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


def _spots_grid_pixel_buffer(
    width: int,
    height: int,
    density_f: float,
    spot_pattern: str,
    spot_rgba: tuple[float, float, float, float],
    bg_rgba: tuple[float, float, float, float],
) -> list[float]:
    """RGBA for spots grid/hex pattern."""
    buf = [0.0] * (width * height * 4)
    grid_scale = max(0.1, density_f)
    spot_radius = 0.35
    pattern = str(spot_pattern or "grid").strip().lower()
    if pattern not in ("grid", "hex"):
        pattern = "grid"

    for y in range(height):
        for x in range(width):
            u = (x + 0.5) / width if width > 0 else 0.5
            v = (y + 0.5) / height if height > 0 else 0.5
            v_scaled = v * grid_scale
            row = math.floor(v_scaled)
            if pattern == "hex":
                u_scaled = u * grid_scale + (row % 2) * 0.5
                u_fract = u_scaled - math.floor(u_scaled)
                v_fract = v_scaled - row
            else:
                u_scaled = u * grid_scale
                u_fract = u_scaled - math.floor(u_scaled)
                v_fract = v_scaled - math.floor(v_scaled)

            du = u_fract - 0.5
            dv = v_fract - 0.5
            distance = math.sqrt(du * du + dv * dv)
            rgba = spot_rgba if distance < spot_radius else bg_rgba
            idx = (y * width + x) * 4
            buf[idx] = rgba[0]
            buf[idx + 1] = rgba[1]
            buf[idx + 2] = rgba[2]
            buf[idx + 3] = rgba[3]
    return buf


def spots_texture_generator(
    width: int,
    height: int,
    spot_color_hex: str,
    bg_color_hex: str,
    density: float,
    spot_pattern: str = "grid",
) -> bytes:
    """Generate PNG with procedural spot pattern."""
    if not isinstance(width, int) or isinstance(width, bool):
        raise TypeError("width must be an integer")
    if not isinstance(height, int) or isinstance(height, bool):
        raise TypeError("height must be an integer")
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if not isinstance(density, (int, float)) or isinstance(density, bool):
        raise TypeError("density must be numeric")
    density_f = float(density)
    if density_f <= 0.0:
        raise ValueError("density must be greater than 0")
    if not isinstance(spot_color_hex, str):
        raise TypeError("spot_color_hex must be a string")
    if not isinstance(bg_color_hex, str):
        raise TypeError("bg_color_hex must be a string")

    spot_rgba = hex_to_rgba(spot_color_hex, (0.0, 0.0, 0.0, 1.0), allow_invalid=False)
    bg_rgba = hex_to_rgba(bg_color_hex, (1.0, 1.0, 1.0, 1.0), allow_invalid=True)
    buf = _spots_grid_pixel_buffer(width, height, density_f, spot_pattern, spot_rgba, bg_rgba)
    return create_png(width, height, buf)


def create_spots_png_and_load(
    width: int,
    height: int,
    spot_color_hex: str,
    bg_color_hex: str,
    density: float,
    img_name: str,
    spot_pattern: str = "grid",
) -> bpy.types.Image:
    """Create spots PNG texture, save to disk, and load into Blender."""
    png_data = spots_texture_generator(
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


def checkerboard_texture_generator(
    width: int,
    height: int,
    color_a_hex: str,
    color_b_hex: str,
    density: float,
) -> bytes:
    """Generate PNG with procedural checkerboard pattern."""
    if not isinstance(width, int) or isinstance(width, bool):
        raise TypeError("width must be an integer")
    if not isinstance(height, int) or isinstance(height, bool):
        raise TypeError("height must be an integer")
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if not isinstance(density, (int, float)) or isinstance(density, bool):
        raise TypeError("density must be numeric")
    density_f = float(density)
    if density_f <= 0.0:
        raise ValueError("density must be greater than 0")
    if not isinstance(color_a_hex, str):
        raise TypeError("color_a_hex must be a string")
    if not isinstance(color_b_hex, str):
        raise TypeError("color_b_hex must be a string")

    color_a = hex_to_rgba(color_a_hex, (0.0, 0.0, 0.0, 1.0), allow_invalid=False)
    color_b = hex_to_rgba(color_b_hex, (1.0, 1.0, 1.0, 1.0), allow_invalid=True)

    grid_scale = max(0.1, density_f)
    buf = [0.0] * (width * height * 4)
    for y in range(height):
        for x in range(width):
            u = (x + 0.5) / width if width > 0 else 0.5
            v = (y + 0.5) / height if height > 0 else 0.5
            cell_x = int(math.floor(u * grid_scale))
            cell_y = int(math.floor(v * grid_scale))
            rgba = color_a if (cell_x + cell_y) % 2 == 0 else color_b
            idx = (y * width + x) * 4
            buf[idx] = rgba[0]
            buf[idx + 1] = rgba[1]
            buf[idx + 2] = rgba[2]
            buf[idx + 3] = rgba[3]

    return create_png(width, height, buf)


def create_checkerboard_png_and_load(
    width: int,
    height: int,
    color_a_hex: str,
    color_b_hex: str,
    density: float,
    img_name: str,
) -> bpy.types.Image:
    """Create checkerboard PNG texture, save to disk, and load into Blender."""
    png_data = checkerboard_texture_generator(
        width,
        height,
        color_a_hex,
        color_b_hex,
        density,
    )
    checker_dir = Path(__file__).parent.parent.parent / "animated_exports" / "checkerboards"
    checker_dir.mkdir(parents=True, exist_ok=True)
    tmp_png = checker_dir / f"{img_name}.png"
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
