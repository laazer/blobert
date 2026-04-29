"""
Typed models for material feature/texture options.
"""

import math
from dataclasses import dataclass
from typing import Any, Mapping

import bpy

from src.utils.texture_asset_loader import infer_texture_asset_id_from_preview

RGBA = tuple[float, float, float, float]
FeatureMap = Mapping[str, Any]


@dataclass(frozen=True)
class ColorImageOptions:
    mode: str
    asset_id: str
    preview: str


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
            color_image = ColorImageOptions(
                mode=str(color_image_raw.get("mode", "") or "").strip().lower(),
                asset_id=str(color_image_raw.get("id", "") or "").strip(),
                preview=str(color_image_raw.get("preview", "") or ""),
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


def _pattern_normalize_hex6(raw: object) -> str:
    return _sanitize_hex_input(raw)[:6]


def _pattern_blend_hex(a_raw: object, b_raw: object) -> str:
    a = _pattern_normalize_hex6(a_raw)
    b = _pattern_normalize_hex6(b_raw)
    if not a and not b:
        return ""
    if not a:
        return b
    if not b:
        return a
    ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
    br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    return f"{(ar + br) // 2:02x}{(ag + bg) // 2:02x}{(ab + bb) // 2:02x}"


def _pattern_image_average_hex(asset_id: str) -> str:
    if not asset_id:
        return ""
    try:
        from ..utils.texture_asset_loader import get_texture_asset_filepath

        asset_path = get_texture_asset_filepath(asset_id)
        image = bpy.data.images.load(str(asset_path))
        try:
            px = image.pixels
        except AttributeError:
            px = None
        if px is None or len(px) < 4:
            return ""
        pixel_count = len(px) // 4
        step = max(1, pixel_count // 2048)
        s_r = s_g = s_b = 0.0
        count = 0
        i = 0
        while i < pixel_count:
            base = i * 4
            s_r += float(px[base])
            s_g += float(px[base + 1])
            s_b += float(px[base + 2])
            count += 1
            i += step
        if count == 0:
            return ""
        return f"{int((s_r / count) * 255):02x}{int((s_g / count) * 255):02x}{int((s_b / count) * 255):02x}"
    except Exception:
        return ""


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


@dataclass(frozen=True)
class PatternChannelOptions:
    mode: str
    hex_value: str
    gradient_a: str
    gradient_b: str
    image_id: str
    image_preview: str
    legacy_hex: str

    @classmethod
    def from_build_options(
        cls,
        *,
        zone: str,
        field: str,
        build_options: Mapping[str, Any],
    ) -> "PatternChannelOptions":
        prefix = f"feat_{zone}_texture_{field}"
        return cls(
            mode=str(build_options.get(f"{prefix}_mode", "single") or "single").strip().lower(),
            hex_value=str(build_options.get(f"{prefix}_hex", "") or ""),
            gradient_a=str(build_options.get(f"{prefix}_a", "") or ""),
            gradient_b=str(build_options.get(f"{prefix}_b", "") or ""),
            image_id=str(build_options.get(f"{prefix}_image_id", "") or "").strip(),
            image_preview=str(build_options.get(f"{prefix}_image_preview", "") or ""),
            legacy_hex=str(build_options.get(prefix, "") or ""),
        )

    def resolved_image_id(self) -> str:
        if self.image_id:
            return self.image_id
        return infer_texture_asset_id_from_preview(self.image_preview) or ""

    def resolved_hex(self) -> str:
        if self.mode == "single":
            return _pattern_normalize_hex6(self.hex_value) or _pattern_normalize_hex6(self.legacy_hex)
        if self.mode == "gradient":
            return _pattern_blend_hex(self.gradient_a, self.gradient_b) or _pattern_normalize_hex6(self.legacy_hex)
        if self.mode == "image":
            return (
                _pattern_image_average_hex(self.resolved_image_id())
                or _pattern_normalize_hex6(self.hex_value)
                or _pattern_normalize_hex6(self.legacy_hex)
            )
        return _pattern_normalize_hex6(self.legacy_hex)


@dataclass(frozen=True)
class ZoneTextureOptions:
    zone: str
    mode: str
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
    spot_color: PatternChannelOptions
    spot_bg_color: PatternChannelOptions
    stripe_color: PatternChannelOptions
    stripe_bg_color: PatternChannelOptions

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
            spot_color=PatternChannelOptions.from_build_options(zone=zone, field="spot_color", build_options=build_options),
            spot_bg_color=PatternChannelOptions.from_build_options(zone=zone, field="spot_bg_color", build_options=build_options),
            stripe_color=PatternChannelOptions.from_build_options(zone=zone, field="stripe_color", build_options=build_options),
            stripe_bg_color=PatternChannelOptions.from_build_options(zone=zone, field="stripe_bg_color", build_options=build_options),
        )

    def pattern_image_asset_id(self, fields: tuple[str, ...]) -> str:
        field_map = {
            "spot_color": self.spot_color,
            "spot_bg_color": self.spot_bg_color,
            "stripe_color": self.stripe_color,
            "stripe_bg_color": self.stripe_bg_color,
        }
        for field in fields:
            channel = field_map.get(field)
            if channel is None or channel.mode != "image":
                continue
            asset_id = channel.resolved_image_id()
            if asset_id:
                return asset_id
        return ""
