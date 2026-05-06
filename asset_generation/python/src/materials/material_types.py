"""
Typed models for material feature/texture options.
"""

import math
from dataclasses import dataclass
from typing import Any, Literal, Mapping

from src.materials.spot_plate_mask import DEFAULT_DARK_THRESHOLD
from src.materials.uv_atlas import (
    parse_uv_rect,
)
from src.utils.texture_asset_loader import infer_texture_asset_id_from_preview

RGBA = tuple[float, float, float, float]
FeatureMap = Mapping[str, Any]


@dataclass(frozen=True)
class ColorImageOptions:
    mode: str
    asset_id: str
    preview: str
    #: Normalized atlas rectangle ``(u0, v0, u1, v1)`` (Blender UV: origin bottom-left).
    uv_rect: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class PartOverrideOptions:
    finish: str
    hex_value: str


@dataclass(frozen=True)
class FeatureZoneOptions:
    finish: str
    hex_value: str
    color_image: ColorImageOptions | None
    parts: Mapping[str, PartOverrideOptions]

    @classmethod
    def from_mapping(cls, raw: object) -> "FeatureZoneOptions | None":
        if not isinstance(raw, dict):
            return None
        color_image_raw = raw.get("color_image")
        color_image: ColorImageOptions | None = None
        if isinstance(color_image_raw, dict):
            uv_rect = parse_uv_rect(color_image_raw.get("uv_rect"))
            color_image = ColorImageOptions(
                mode=str(color_image_raw.get("mode", "") or "").strip().lower(),
                asset_id=str(color_image_raw.get("id", "") or "").strip(),
                preview=str(color_image_raw.get("preview", "") or ""),
                uv_rect=uv_rect,
            )
        parts_raw = raw.get("parts")
        parts: dict[str, PartOverrideOptions] = {}
        if isinstance(parts_raw, dict):
            for part_id, value in parts_raw.items():
                if not isinstance(part_id, str) or not isinstance(value, dict):
                    continue
                parts[part_id] = PartOverrideOptions(
                    finish=str(value.get("finish", "default") or "default"),
                    hex_value=str(value.get("hex", "") or ""),
                )
        return cls(
            finish=str(raw.get("finish", "default") or "default"),
            hex_value=str(raw.get("hex", "") or ""),
            color_image=color_image,
            parts=parts,
        )


def feature_zone_map(features: FeatureMap | None) -> dict[str, FeatureZoneOptions]:
    if not features:
        return {}
    out: dict[str, FeatureZoneOptions] = {}
    for zone, value in features.items():
        if not isinstance(zone, str):
            continue
        parsed = FeatureZoneOptions.from_mapping(value)
        if parsed is not None:
            out[zone] = parsed
    return out


def _sanitize_hex_input(raw: object) -> str:
    s = "".join(c for c in str(raw or "").strip().lower() if c in "0123456789abcdef")
    return s[:6]


def pattern_normalize_hex6(raw: object) -> str:
    return _sanitize_hex_input(raw)[:6]


def _safe_rotation_degrees(raw: object) -> float:
    try:
        v = float(raw or 0.0)
    except (TypeError, ValueError):
        v = 0.0
    if math.isnan(v) or math.isinf(v):
        v = 0.0
    return max(-360.0, min(360.0, v))


def _normalized_stripe_preset(raw: object) -> str:
    preset = str(raw or "beachball").strip().lower()
    if preset in ("vertical", "x"):
        return "beachball"
    if preset in ("horizontal", "y"):
        return "doplar"
    if preset == "z":
        return "swirl"
    return preset if preset in ("beachball", "doplar", "swirl") else "beachball"


def _safe_bool(raw: object, *, default: bool) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        if isinstance(raw, float) and (math.isnan(raw) or math.isinf(raw)):
            return default
        return raw != 0
    s = str(raw).strip().lower()
    if s in ("false", "no", "off", "0"):
        return False
    if s in ("true", "yes", "on", "1"):
        return True
    return default


def _safe_float(
    raw: object,
    *,
    default: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    try:
        value = float(raw if raw is not None else default)
    except (TypeError, ValueError):
        value = default
    if math.isnan(value) or math.isinf(value):
        value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


# ============================================================================
# FillMaterial Types: Unified representation for pattern and background fills
# ============================================================================


@dataclass(frozen=True)
class SolidFill:
    """Single flat color fill."""
    hex_value: str

    @classmethod
    def from_build_options(
        cls,
        *,
        zone: str,
        field: str,
        build_options: Mapping[str, Any],
    ) -> "SolidFill":
        """Construct SolidFill from build_options flat dict."""
        prefix = f"feat_{zone}_texture_{field}"
        hex_val = str(build_options.get(f"{prefix}_hex", "") or "")
        return cls(hex_value=hex_val)


@dataclass(frozen=True)
class GradientFill:
    """Linear gradient fill with two endpoints and direction."""
    hex_a: str
    hex_b: str
    direction: str

    @classmethod
    def from_build_options(
        cls,
        *,
        zone: str,
        field: str,
        build_options: Mapping[str, Any],
    ) -> "GradientFill":
        """Construct GradientFill from build_options flat dict."""
        prefix = f"feat_{zone}_texture_{field}"
        # Canonical keys are *_grad_*; keep *_a/*_b/*_direction fallback for legacy payloads.
        hex_a = str(
            build_options.get(f"{prefix}_grad_a", build_options.get(f"{prefix}_a", "")) or ""
        )
        hex_b = str(
            build_options.get(f"{prefix}_grad_b", build_options.get(f"{prefix}_b", "")) or ""
        )
        direction = str(
            build_options.get(
                f"{prefix}_grad_direction",
                build_options.get(f"{prefix}_direction", "horizontal"),
            )
            or "horizontal"
        )
        return cls(hex_a=hex_a, hex_b=hex_b, direction=direction)


@dataclass(frozen=True)
class ImageFill:
    """Image asset fill with optional atlas bounds."""
    asset_id: str
    uv_rect: tuple[float, float, float, float] | None

    @classmethod
    def from_build_options(
        cls,
        *,
        zone: str,
        field: str,
        build_options: Mapping[str, Any],
    ) -> "ImageFill":
        """Construct ImageFill from build_options flat dict."""
        prefix = f"feat_{zone}_texture_{field}"
        image_id = str(build_options.get(f"{prefix}_image_id", "") or "").strip()
        image_preview = str(build_options.get(f"{prefix}_image_preview", "") or "")
        image_uv_rect_raw = str(build_options.get(f"{prefix}_image_uv_rect", "") or "")

        # Resolve asset_id from image_id or infer from preview
        asset_id = image_id or infer_texture_asset_id_from_preview(image_preview) or ""

        # Parse UV rect if present
        uv_rect = parse_uv_rect(image_uv_rect_raw)

        return cls(asset_id=asset_id, uv_rect=uv_rect)


FillMaterial = SolidFill | GradientFill | ImageFill


def fill_material_from_build_options(
    *,
    zone: str,
    field: str,
    build_options: Mapping[str, Any],
) -> FillMaterial:
    """Dispatch to appropriate FillMaterial class based on mode.

    Each class handles its own construction via from_build_options().
    """
    prefix = f"feat_{zone}_texture_{field}"
    mode = str(build_options.get(f"{prefix}_mode", "single") or "single").strip().lower()

    if mode == "single":
        return SolidFill.from_build_options(zone=zone, field=field, build_options=build_options)
    elif mode == "gradient":
        return GradientFill.from_build_options(zone=zone, field=field, build_options=build_options)
    elif mode == "image":
        return ImageFill.from_build_options(zone=zone, field=field, build_options=build_options)
    else:
        # Invalid mode: default to empty solid
        return SolidFill(hex_value="")


@dataclass(frozen=True)
class ZoneTextureOptions:
    zone: str
    #: Texture pattern mode: gradient, spots, stripes, checkerboard, or assets
    mode: Literal["gradient", "spots", "stripes", "checkerboard", "assets"]
    finish: str
    zone_hex: str
    tile_repeat: float
    gradient_a_hex: str
    gradient_b_hex: str
    gradient_direction: str
    asset_id: str
    spot_density: float
    stripe_width: float
    stripe_preset: str
    stripe_yaw: float
    stripe_pitch: float
    pattern_fill: FillMaterial
    background_fill: FillMaterial
    #: ``white_holes`` | ``dark_spots`` | ``auto`` — see ``spot_plate_mask.py``
    spot_plate_mask_mode: str
    #: Linear RGB; used when effective mode is ``dark_spots`` (max channel >= threshold ⇒ show base).
    spot_plate_dark_threshold: float
    #: When False, compositing uses a hard mask (no feathered smoothstep, no mask blur).
    spot_plate_mask_soft_edges: bool

    @classmethod
    def from_build_options(
        cls,
        *,
        zone: str,
        zone_features: Mapping[str, FeatureZoneOptions],
        build_options: Mapping[str, Any],
    ) -> "ZoneTextureOptions":
        zf = zone_features.get(zone)
        finish = zf.finish if zf is not None else "default"
        zone_hex = zf.hex_value.strip() if zf is not None else ""
        yaw = _safe_rotation_degrees(build_options.get(f"feat_{zone}_texture_stripe_rot_yaw", 0.0))
        pitch = _safe_rotation_degrees(build_options.get(f"feat_{zone}_texture_stripe_rot_pitch", 0.0))
        if f"feat_{zone}_texture_stripe_rot_pitch" not in build_options and f"feat_{zone}_texture_stripe_rot_x" in build_options:
            pitch = _safe_rotation_degrees(build_options.get(f"feat_{zone}_texture_stripe_rot_x", 0.0))
        if f"feat_{zone}_texture_stripe_rot_yaw" not in build_options and f"feat_{zone}_texture_stripe_rot_y" in build_options:
            yaw = _safe_rotation_degrees(build_options.get(f"feat_{zone}_texture_stripe_rot_y", 0.0))
        return cls(
            zone=zone,
            mode=str(build_options.get(f"feat_{zone}_texture_mode", "none") or "none").strip().lower(),
            finish=finish,
            zone_hex=zone_hex,
            tile_repeat=_safe_float(
                build_options.get(f"feat_{zone}_texture_asset_tile_repeat", 1.0),
                default=1.0,
            ),
            gradient_a_hex=str(build_options.get(f"feat_{zone}_texture_grad_color_a", "") or ""),
            gradient_b_hex=str(build_options.get(f"feat_{zone}_texture_grad_color_b", "") or ""),
            gradient_direction=str(build_options.get(f"feat_{zone}_texture_grad_direction", "horizontal") or "horizontal"),
            asset_id=str(build_options.get(f"feat_{zone}_texture_asset_id", "") or "").strip(),
            spot_density=_safe_float(
                build_options.get(f"feat_{zone}_texture_spot_density", 1.0),
                default=1.0,
                min_value=0.1,
                max_value=5.0,
            ),
            stripe_width=_safe_float(
                build_options.get(f"feat_{zone}_texture_stripe_width", 0.2),
                default=0.2,
                min_value=0.05,
                max_value=1.0,
            ),
            stripe_preset=_normalized_stripe_preset(build_options.get(f"feat_{zone}_texture_stripe_direction", "beachball")),
            stripe_yaw=yaw,
            stripe_pitch=pitch,
            pattern_fill=fill_material_from_build_options(zone=zone, field="pattern", build_options=build_options),
            background_fill=fill_material_from_build_options(zone=zone, field="background", build_options=build_options),
            spot_plate_mask_mode=str(
                build_options.get(f"feat_{zone}_texture_spot_plate_mask_mode", "auto") or "auto",
            ).strip().lower(),
            spot_plate_dark_threshold=_safe_float(
                build_options.get(
                    f"feat_{zone}_texture_spot_plate_dark_threshold",
                    DEFAULT_DARK_THRESHOLD,
                ),
                default=DEFAULT_DARK_THRESHOLD,
                min_value=0.05,
                max_value=0.95,
            ),
            spot_plate_mask_soft_edges=_safe_bool(
                build_options.get(f"feat_{zone}_texture_spot_plate_mask_soft_edges", True),
                default=True,
            ),
        )

    def spot_pattern_image_asset_id(self) -> str:
        """Asset id for a user-authored spot plate image.

        Returns the asset_id from ``pattern_fill`` if it's an ``ImageFill``, else empty.
        """
        if isinstance(self.pattern_fill, ImageFill):
            return self.pattern_fill.asset_id
        return ""
