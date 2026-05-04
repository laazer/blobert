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

from typing import Any, Mapping

import bpy

from src.materials.material_types import (
    FeatureZoneOptions,
    ImageFill,
    ZoneTextureOptions,
)
from src.materials.spots_composite_debug import log_spots_composite


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

    # Procedural spots: generate dot texture with pattern/background colors
    log_spots_composite(
        f"apply_spots_zone_pattern zone={zone}: procedural spots",
    )
    return material_for_spots_zone(
        base_palette_name=base_palette_name,
        finish=settings.finish,
        pattern_fill=settings.pattern_fill,
        background_fill=settings.background_fill,
        density=settings.spot_density,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=instance_suffix,
    )
