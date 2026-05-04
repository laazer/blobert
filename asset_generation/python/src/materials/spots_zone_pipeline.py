"""Single pipeline for spot-zone materials.

Steps (same for all ``PatternChannelOptions`` modes — colors resolve via ``resolved_hex()`` upstream):

1. Resolve optional image plate id (user-authored mask / tones) vs procedural dots.
2. Resolve underlay asset id or synthesized PNG path (zone image / spot_bg / gradient fill).
3. Pick spot / gap hex for procedural generation (neutral gap when compositing onto a file underlay).
4. Build base material — load image plate **or** procedural ``BlobertTexSpot_*`` raster.
5. If an underlay exists, composite pattern over base (shared overlay implementation).

Call sites: ``material_system.apply_zone_texture_pattern_overrides`` and
``feature_zones.apply_zone_texture_pattern_overrides`` only differ in density validation
(see ``spot_density_payload_usable``).
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
    """Apply spots texture mode: one code path for procedural plate vs image plate + underlay."""
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
