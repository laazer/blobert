"""Single pipeline for spot-zone materials.

Dispatches to one of two factories based on ``pattern_fill`` type:

1. **Image plate** (``ImageFill``): loads the user-authored mask image directly,
   applies UV rect for atlas sub-region selection.
2. **Procedural** (``SolidFill`` / ``GradientFill``): generates a ``BlobertTexSpot_*``
   raster with pattern and background colors.

Call sites: ``material_system._apply_spots_pattern`` and
``feature_zones.apply_zone_texture_pattern_overrides`` both delegate here.
``feature_zones`` guards with ``spot_density_payload_usable`` first.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

import bpy

logger = logging.getLogger(__name__)

from src.materials.material_types import (
    FeatureZoneOptions,
    ImageFill,
    ZoneTextureOptions,
)
from src.materials.spots_composite_debug import log_spots_composite
from src.materials.uv_atlas import parse_uv_rect, texture_sample_pixel_dimensions
from src.utils.texture_asset_loader import get_texture_asset_filepath


def spot_density_payload_usable(build_options: Mapping[str, Any], zone: str) -> bool:
    """Return False when raw ``feat_<zone>_texture_spot_density`` is unparseable.

    ``feature_zones`` historically skips that zone (no texture override) in that case.
    ``material_system`` uses ``ZoneTextureOptions`` coercion instead and never hits this.
    """
    try:
        float(build_options.get(f"feat_{zone}_texture_spot_density", 1.0) or 1.0)
        return True
    except (TypeError, ValueError):
        return False


def apply_spots_zone_pattern(
    *,
    base_palette_name: str,
    settings: ZoneTextureOptions,
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
) -> bpy.types.Material:
    """Apply spots texture mode: image plate (with UV rect) or procedural dots."""
    from src.materials.material_system import (
        material_for_spots_zone,
        material_for_spots_zone_from_image_asset,
        overlay_base_image_on_zone_material,
        resolve_texture_pattern_overlay_uv_rect,
        resolve_zone_color_image_asset_id,
    )

    # Check if pattern_fill is an image (that's the spot pattern)
    spot_pattern_id = settings.pattern_fill.asset_id if isinstance(settings.pattern_fill, ImageFill) else ""
    pattern_uv_rect = settings.pattern_fill.uv_rect if isinstance(settings.pattern_fill, ImageFill) else None

    instance_suffix = f"{zone}_tex_spot"

    if spot_pattern_id:
        # Image-based spots: load image directly, apply UV rect
        log_spots_composite(
            f"apply_spots_zone_pattern zone={zone}: IMAGE spot plate asset_id={spot_pattern_id!r}",
        )
        return material_for_spots_zone_from_image_asset(
            base_palette_name=base_palette_name,
            finish=settings.finish,
            asset_id=spot_pattern_id,
            zone_hex_fallback=settings.zone_hex,
            instance_suffix=instance_suffix,
            spot_plate_mask_mode=settings.spot_plate_mask_mode,
            spot_plate_dark_threshold=settings.spot_plate_dark_threshold,
            spot_plate_mask_soft_edges=settings.spot_plate_mask_soft_edges,
            uv_rect=pattern_uv_rect,
        )

    # Image background: resolve atlas UV first (same rect the underlay will use), then generate
    # procedural spots on that region's pixel canvas — crop-then-spots, not spots-then-UV-map.
    bg_fill = settings.background_fill
    spot_w, spot_h = 128, 128
    underlay_uv_for_dims: tuple[float, float, float, float] | None = None
    if isinstance(bg_fill, ImageFill) and bg_fill.asset_id:
        bg_uv_rect = bg_fill.uv_rect
        if bg_uv_rect is None:
            bg_uv_rect = parse_uv_rect(
                build_options.get(f"feat_{zone}_texture_background_image_uv_rect")
            )
        zone_image_asset_id = resolve_zone_color_image_asset_id(zone, build_options, zone_feature)
        underlay_uv_for_dims = resolve_texture_pattern_overlay_uv_rect(
            zone=zone,
            build_options=build_options,
            zone_feature=zone_feature,
            pattern_asset_id=bg_fill.asset_id,
            zone_image_asset_id=zone_image_asset_id,
            channel_uv_rect=bg_uv_rect,
        )
        try:
            apath = Path(get_texture_asset_filepath(bg_fill.asset_id))
            spot_w, spot_h = texture_sample_pixel_dimensions(apath, underlay_uv_for_dims)
        except (ValueError, OSError, TypeError) as exc:
            logger.warning(
                "apply_spots_zone_pattern: failed to resolve background texture path or sample "
                "dimensions (zone=%s bg_asset_id=%r underlay_uv=%r): %s: %s",
                zone,
                bg_fill.asset_id,
                underlay_uv_for_dims,
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            spot_w, spot_h = 128, 128

    # Procedural spots: with image BG, spot_w×spot_h == atlas sample size; else default 128×128.
    log_spots_composite(
        f"apply_spots_zone_pattern zone={zone}: procedural spots raster={spot_w}x{spot_h}",
    )
    if isinstance(bg_fill, ImageFill) and bg_fill.asset_id:
        # Always visible in Blender export logs (editor terminal / run SSE). Preview GLB only
        # updates after a full animated export — restarting the API server alone does not.
        print(
            f"[blobert:spots-pipeline] zone={zone} "
            f"raster={spot_w}x{spot_h} underlay_uv={underlay_uv_for_dims!r} "
            f"bg_asset_id={bg_fill.asset_id!r}",
            flush=True,
        )
    spots_mat = material_for_spots_zone(
        base_palette_name=base_palette_name,
        finish=settings.finish,
        pattern_fill=settings.pattern_fill,
        background_fill=settings.background_fill,
        density=settings.spot_density,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=instance_suffix,
        spot_texture_width=spot_w,
        spot_texture_height=spot_h,
    )

    if isinstance(bg_fill, ImageFill) and bg_fill.asset_id:
        spots_mat["blobert_spot_plate_mask_mode"] = "white_holes"
        spots_mat["blobert_spot_plate_mask_soft_edges"] = 0
        return overlay_base_image_on_zone_material(
            spots_mat,
            asset_id=bg_fill.asset_id,
            underlay_uv_rect=underlay_uv_for_dims,
        )

    return spots_mat
