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

from pathlib import Path
from typing import Any, Mapping

import bpy

from src.materials.material_types import FeatureZoneOptions, ZoneTextureOptions
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
        overlay_base_image_on_zone_material,
        resolve_spots_composite_underlay,
        resolve_zone_color_image_asset_id,
        resolve_zone_color_image_uv_rect,
    )
    from src.materials.uv_atlas import resolved_asset_path_for_image_sampling
    from src.utils.texture_asset_loader import get_texture_asset_filepath

    spot_pattern_id = settings.spot_pattern_image_asset_id()
    under_asset, under_path = resolve_spots_composite_underlay(
        zone=zone,
        build_options=build_options,
        zone_feature=zone_feature,
        settings=settings,
        spot_pattern_id=spot_pattern_id,
    )
    has_file_underlay = bool(under_asset or under_path)
    spots_bg_hex = "ffffff" if has_file_underlay else settings.spot_bg_color.resolved_hex()
    spot_hex = settings.spot_color.resolved_hex()
    if not spot_hex and has_file_underlay and not spot_pattern_id:
        spot_hex = "000000"

    instance_suffix = f"{zone}_tex_spot"

    if spot_pattern_id:
        _under = under_asset or (str(under_path) if under_path else "") or "(none; full plate on UV only)"
        log_spots_composite(
            f"apply_spots_zone_pattern zone={zone}: IMAGE spot plate asset_id={spot_pattern_id!r}; "
            f"composite_underlay={_under!r}",
        )
        spots_mat = material_for_spots_zone_from_image_asset(
            base_palette_name=base_palette_name,
            finish=settings.finish,
            asset_id=spot_pattern_id,
            zone_hex_fallback=settings.zone_hex,
            instance_suffix=instance_suffix,
            spot_plate_mask_mode=settings.spot_plate_mask_mode,
            spot_plate_dark_threshold=settings.spot_plate_dark_threshold,
            spot_plate_mask_soft_edges=settings.spot_plate_mask_soft_edges,
            uv_rect=settings.spot_pattern_image_uv_rect(),
        )
    else:
        _under = under_asset or (str(under_path) if under_path else "(none)")
        log_spots_composite(
            f"apply_spots_zone_pattern zone={zone}: procedural spots spot_hex={spot_hex!r} "
            f"bg_hex={spots_bg_hex!r}; composite_underlay={_under!r}",
        )
        spots_mat = material_for_spots_zone(
            base_palette_name=base_palette_name,
            finish=settings.finish,
            spot_hex=spot_hex,
            bg_hex=spots_bg_hex,
            density=settings.spot_density,
            zone_hex_fallback=settings.zone_hex,
            instance_suffix=instance_suffix,
        )

    if under_asset:
        # Determine which UV rect to use based on where the underlay came from.
        # If underlay is from spot_bg_color image, use its UV rect.
        # If underlay is zone color image, use zone's UV rect.
        zone_id = resolve_zone_color_image_asset_id(zone, build_options, zone_feature)

        if under_asset != zone_id and settings.spot_bg_color.mode == "image":
            # Underlay is from spot_bg_color image → use its UV rect
            u_uv = settings.spot_bg_color.parsed_image_uv_rect()
        else:
            # Underlay is zone color image (or synthesized) → use zone's UV rect
            u_uv = resolve_zone_color_image_uv_rect(zone, build_options, zone_feature)

        try:
            base_ap = Path(get_texture_asset_filepath(under_asset))
            resolved_u = resolved_asset_path_for_image_sampling(base_ap, u_uv)
            if resolved_u != base_ap:
                return overlay_base_image_on_zone_material(spots_mat, base_path=resolved_u)
        except (ValueError, OSError, TypeError):
            pass
        return overlay_base_image_on_zone_material(
            spots_mat,
            asset_id=under_asset,
            underlay_uv_rect=u_uv,
        )
    if under_path is not None:
        return overlay_base_image_on_zone_material(spots_mat, base_path=under_path)
    return spots_mat
